"""
Authentication and Authorization Module for AI Engine Service
Implements JWT validation, tenant isolation, and user context management
"""

import logging
from typing import Dict, Any, Optional
from functools import lru_cache
from contextvars import ContextVar
from dataclasses import dataclass

import httpx
from fastapi import HTTPException, Depends, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from jose.exceptions import ExpiredSignatureError, JWTClaimsError

logger = logging.getLogger(__name__)

# Context variable for user context in background tasks
user_context: ContextVar[Optional['UserContext']] = ContextVar('user_context', default=None)

@dataclass
class UserContext:
    """User context with authentication and tenant information"""
    creator_id: str
    tenant_id: str
    permissions: list[str]
    subscription_tier: str
    email: Optional[str] = None
    is_admin: bool = False
    
    def has_permission(self, permission: str) -> bool:
        """Check if user has specific permission"""
        return permission in self.permissions or self.is_admin
    
    def can_access_tenant(self, requested_tenant: str) -> bool:
        """Check if user can access requested tenant"""
        # Users can access their own tenant
        if self.tenant_id == requested_tenant:
            return True
        
        # Admins can access any tenant
        if self.is_admin:
            return True
        
        # Check for cross-tenant permissions
        return "cross_tenant_access" in self.permissions


class JWTManager:
    """Manages JWT validation and JWKS key retrieval"""
    
    def __init__(self):
        self.auth_service_url = "http://auth-service:8001"
        self.jwks_url = f"{self.auth_service_url}/.well-known/jwks.json"
        self.issuer = "auth-service"
        self.audience = "coaching-platform"
        self.algorithm = "RS256"
    
    @lru_cache(maxsize=10)
    async def get_jwks(self) -> Dict[str, Any]:
        """Get JWKS with caching and retry logic"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(self.jwks_url, timeout=5.0)
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Failed to fetch JWKS: {e}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Authentication service unavailable"
            )
    
    def get_signing_key(self, jwks: Dict[str, Any], kid: str) -> str:
        """Get signing key by key ID"""
        for key in jwks.get("keys", []):
            if key.get("kid") == kid:
                return key
        
        # Retry with fresh JWKS on cache miss
        self.get_jwks.cache_clear()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token: key not found"
        )
    
    async def verify_token(self, token: str) -> Dict[str, Any]:
        """Verify JWT token and return claims"""
        try:
            # Decode header to get key ID
            unverified_header = jwt.get_unverified_header(token)
            kid = unverified_header.get("kid")
            
            if not kid:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token: missing key ID"
                )
            
            # Get JWKS and signing key
            jwks = await self.get_jwks()
            signing_key = self.get_signing_key(jwks, kid)
            
            # Verify token
            claims = jwt.decode(
                token,
                signing_key,
                algorithms=[self.algorithm],
                audience=self.audience,
                issuer=self.issuer
            )
            
            # Validate required claims
            required_claims = ["sub", "creator_id", "tenant_id", "permissions"]
            for claim in required_claims:
                if claim not in claims:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail=f"Invalid token: missing {claim} claim"
                    )
            
            return claims
            
        except ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired"
            )
        except JWTClaimsError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid token claims: {str(e)}"
            )
        except JWTError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid token: {str(e)}"
            )


# Global JWT manager instance
jwt_manager = JWTManager()
security = HTTPBearer()


async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> UserContext:
    """
    Get current authenticated user context
    
    Args:
        request: FastAPI request object
        credentials: JWT credentials from Authorization header
        
    Returns:
        UserContext with user information
        
    Raises:
        HTTPException: If authentication fails
    """
    try:
        # Verify JWT token
        claims = await jwt_manager.verify_token(credentials.credentials)
        
        # Create user context
        user_ctx = UserContext(
            creator_id=claims["creator_id"],
            tenant_id=claims["tenant_id"],
            permissions=claims.get("permissions", []),
            subscription_tier=claims.get("subscription_tier", "free"),
            email=claims.get("email"),
            is_admin="admin" in claims.get("permissions", [])
        )
        
        # Set context for background tasks
        user_context.set(user_ctx)
        
        # Store in request state
        request.state.user = user_ctx
        
        return user_ctx
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Authentication failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed"
        )


async def get_current_creator_id(user: UserContext = Depends(get_current_user)) -> str:
    """Get current creator ID from authenticated user"""
    return user.creator_id


async def require_permission(permission: str):
    """Dependency factory for permission-based access control"""
    def permission_checker(user: UserContext = Depends(get_current_user)) -> UserContext:
        if not user.has_permission(permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions: {permission} required"
            )
        return user
    return permission_checker


async def validate_tenant_access(
    requested_tenant: str,
    user: UserContext = Depends(get_current_user)
) -> UserContext:
    """Validate user can access requested tenant"""
    if not user.can_access_tenant(requested_tenant):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: insufficient tenant permissions"
        )
    return user


def get_user_context() -> Optional[UserContext]:
    """Get user context from context variable (for background tasks)"""
    return user_context.get()