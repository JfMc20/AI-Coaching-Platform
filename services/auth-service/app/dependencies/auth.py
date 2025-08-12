"""
Authentication dependencies for FastAPI
Provides JWT validation, user context, and security middleware
"""

import os
import uuid
import time
import redis.asyncio as redis
import logging
import asyncio
from typing import Optional, Dict, Any
from datetime import datetime, timedelta

from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
from jose import JWTError, jwt
from jose.exceptions import ExpiredSignatureError, JWTClaimsError

from shared.models.database import Creator, JWTBlacklist
from shared.models.auth import CreatorResponse
from ..database import get_db

logger = logging.getLogger(__name__)

# Security scheme for OpenAPI documentation
security = HTTPBearer(
    scheme_name="JWT Bearer Token",
    description="JWT Bearer token for authentication"
)

# In a real application, this dependency would be defined in a central place
# (e.g., app/redis.py) and would manage a connection pool created during
# the application's startup event.
async def get_redis(request: Request) -> redis.Redis:
    """
    Provides a Redis client from a connection pool managed in the app's lifespan.
    Example: `return request.app.state.redis`
    """
    if not hasattr(request.app.state, "redis"):
        logger.error("Redis client not found in application state. Rate limiting will fail.")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Rate limiter is not available",
        )
    return request.app.state.redis

class AuthenticationError(HTTPException):
    """Custom authentication error"""
    def __init__(self, detail: str = "Authentication failed"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"}
        )


class AuthorizationError(HTTPException):
    """Custom authorization error"""
    def __init__(self, detail: str = "Access denied"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail
        )


async def get_current_creator_id(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> str:
    """
    Extract and validate creator ID from JWT token
    
    Args:
        request: FastAPI request object
        credentials: JWT credentials from Authorization header
        db: Database session
        
    Returns:
        Creator ID as string
        
    Raises:
        AuthenticationError: If token is invalid or expired
    """
    try:
        # Get JWT configuration
        jwt_secret_key = os.getenv("JWT_SECRET_KEY")
        jwt_algorithm = os.getenv("JWT_ALGORITHM", "RS256")
        jwt_audience = os.getenv("JWT_AUDIENCE", "api")
        jwt_issuer = os.getenv("JWT_ISSUER", "mvp-coaching-ai-platform")
        
        if not jwt_secret_key:
            logger.error("JWT_SECRET_KEY not configured")
            raise AuthenticationError("Authentication service misconfigured")
        
        # Decode JWT token
        try:
            payload = jwt.decode(
                credentials.credentials,
                jwt_secret_key,
                algorithms=[jwt_algorithm],
                audience=jwt_audience,
                issuer=jwt_issuer
            )
        except ExpiredSignatureError:
            logger.warning(f"Expired JWT token from {request.client.host}")
            raise AuthenticationError("Token has expired")
        except JWTClaimsError as e:
            logger.warning(f"Invalid JWT claims from {request.client.host}: {e}")
            raise AuthenticationError("Invalid token claims")
        except JWTError as e:
            logger.warning(f"Invalid JWT token from {request.client.host}: {e}")
            raise AuthenticationError("Invalid token")
        
        # Extract claims
        creator_id = payload.get("sub")
        jti = payload.get("jti")
        token_type = payload.get("type")
        
        if not creator_id or not jti or token_type != "access":
            logger.warning(f"Missing or invalid JWT claims from {request.client.host}")
            raise AuthenticationError("Invalid token format")
        
        # Validate creator ID format
        try:
            creator_uuid = uuid.UUID(creator_id)
        except ValueError:
            logger.warning(f"Invalid creator ID format in JWT: {creator_id}")
            raise AuthenticationError("Invalid token format")
        
        # Check if token is blacklisted
        blacklist_result = await db.execute(
            select(JWTBlacklist).where(JWTBlacklist.jti == jti)
        )
        if blacklist_result.scalar_one_or_none():
            logger.warning(f"Blacklisted JWT token used: {jti[:16]}...")
            raise AuthenticationError("Token has been revoked")
        
        # Verify creator exists and is active
        creator_result = await db.execute(
            select(Creator).where(
                Creator.id == creator_uuid,
                Creator.is_active == True
            )
        )
        creator = creator_result.scalar_one_or_none()
        
        if not creator:
            logger.warning(f"JWT token for non-existent or inactive creator: {creator_id}")
            raise AuthenticationError("Invalid token")
        
        # Store request context for audit logging
        request.state.creator_id = creator_id
        request.state.jti = jti
        request.state.client_ip = request.client.host
        request.state.user_agent = request.headers.get("User-Agent")
        
        return creator_id
        
    except AuthenticationError:
        raise
    except Exception as e:
        logger.exception(f"Unexpected error in JWT validation: {e}")
        raise AuthenticationError("Authentication failed")


async def get_current_creator(
    creator_id: str = Depends(get_current_creator_id),
    db: AsyncSession = Depends(get_db)
) -> CreatorResponse:
    """
    Get current authenticated creator details
    
    Args:
        creator_id: Creator ID from JWT token
        db: Database session
        
    Returns:
        CreatorResponse with creator details
        
    Raises:
        AuthenticationError: If creator not found
    """
    try:
        creator_uuid = uuid.UUID(creator_id)
        
        result = await db.execute(
            select(Creator).where(Creator.id == creator_uuid)
        )
        creator = result.scalar_one_or_none()
        
        if not creator:
            raise AuthenticationError("Creator not found")
        
        return CreatorResponse(
            id=str(creator.id),
            email=creator.email,
            full_name=creator.full_name,
            company_name=creator.company_name,
            is_active=creator.is_active,
            subscription_tier=creator.subscription_tier,
            created_at=creator.created_at,
            updated_at=creator.updated_at
        )
        
    except ValueError:
        raise AuthenticationError("Invalid creator ID format")
    except Exception as e:
        logger.exception(f"Error getting current creator: {e}")
        raise AuthenticationError("Failed to get creator details")


async def get_tenant_db(
    creator_id: str = Depends(get_current_creator_id),
    db: AsyncSession = Depends(get_db)
) -> AsyncSession:
    """
    Get database session with tenant context set for Row Level Security
    
    Args:
        creator_id: Creator ID from JWT token
        db: Database session
        
    Returns:
        Database session with tenant context
    """
    try:
        # Set tenant context for Row Level Security
        await db.execute(
            text("SELECT set_config('app.current_creator_id', :creator_id, true)"),
            {"creator_id": creator_id}
        )
        
        return db
        
    except Exception as e:
        logger.exception(f"Error setting tenant context: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to set tenant context"
        )


def require_role(required_role: str):
    """
    Decorator factory for role-based access control
    
    Args:
        required_role: Required role for access
        
    Returns:
        Dependency function for FastAPI
    """
    async def role_checker(
        creator: CreatorResponse = Depends(get_current_creator)
    ) -> CreatorResponse:
        """Check if creator has required role"""
        
        # For MVP, we have basic role mapping based on subscription tier
        role_mapping = {
            "free": ["creator"],
            "pro": ["creator", "creator-readonly"],
            "enterprise": ["creator", "creator-readonly", "admin"]
        }
        
        creator_roles = role_mapping.get(creator.subscription_tier, ["creator"])
        
        if required_role not in creator_roles:
            logger.warning(
                f"Access denied for creator {creator.id}: "
                f"required_role={required_role}, creator_roles={creator_roles}"
            )
            raise AuthorizationError(
                f"Access denied. Required role: {required_role}"
            )
        
        return creator
    
    return role_checker


def require_resource_ownership(resource_field: str = "creator_id"):
    """
    Decorator factory for resource ownership validation
    
    Args:
        resource_field: Field name containing creator ID
        
    Returns:
        Dependency function for FastAPI
    """
    async def ownership_checker(
        request: Request,
        creator_id: str = Depends(get_current_creator_id)
    ) -> str:
        """Check if creator owns the requested resource"""
        
        # Extract resource creator ID from path parameters
        path_params = request.path_params
        resource_creator_id = path_params.get(resource_field)
        
        if not resource_creator_id:
            # If not in path params, check query params
            query_params = dict(request.query_params)
            resource_creator_id = query_params.get(resource_field)
        
        if resource_creator_id and resource_creator_id != creator_id:
            logger.warning(
                f"Resource access denied for creator {creator_id}: "
                f"attempted to access resource owned by {resource_creator_id}"
            )
            raise AuthorizationError("Access denied to resource")
        
        return creator_id
    
    return ownership_checker


class RateLimitChecker:
    """Rate limiting checker backed by Redis for distributed environments."""

    # Lua script for atomic check-and-increment using a sorted set.
    # This provides a sliding window algorithm.
    #
    # Returns:
    #   -1 if the rate limit is exceeded.
    #   The new attempt count if the request is allowed.
    LUA_SCRIPT = """
        local key = KEYS[1]
        local now = tonumber(ARGV[1])
        local window_ms = tonumber(ARGV[2]) * 1000  -- Convert seconds to milliseconds
        local max_attempts = tonumber(ARGV[3])

        -- Remove timestamps older than the window's start time
        local min_score = now - window_ms
        redis.call('ZREMRANGEBYSCORE', key, '-inf', min_score)

        -- Get the current number of attempts within the window
        local current_attempts = redis.call('ZCARD', key)

        -- Check if the limit has been reached
        if current_attempts >= max_attempts then
            return -1
        end

        -- If not, add the new attempt with a unique member and set/update the key's expiration
        -- Generate a unique member using timestamp and a counter to prevent race conditions
        local member = now .. ':' .. redis.call('INCR', key .. ':counter')
        redis.call('ZADD', key, now, member)
        redis.call('EXPIRE', key, tonumber(ARGV[2]))  -- Use original seconds for expiration
        return current_attempts + 1
    """

    def __init__(
        self,
        redis_client: redis.Redis,
        max_attempts: int,
        window_seconds: int,
        namespace: str = "default",
    ):
        self.redis = redis_client
        self.max_attempts = max_attempts
        self.window_seconds = window_seconds
        self.namespace = namespace
        # Register the Lua script with Redis. This is cached on the client.
        self._script = self.redis.register_script(self.LUA_SCRIPT)

    async def check_rate_limit(self, request: Request, identifier: str = None):
        """
        Check if a request exceeds the rate limit using Redis.

        Args:
            request: FastAPI request object.
            identifier: Custom identifier (defaults to client IP).

        Raises:
            HTTPException: If the rate limit is exceeded or Redis is unavailable.
        """
        if identifier is None:
            identifier = request.client.host

        key = f"rate_limit:{self.namespace}:{identifier}"
        now = int(time.time() * 1000)  # Use milliseconds for better precision

        try:
            # Execute the Lua script atomically
            result = await self._script(
                keys=[key],
                args=[now, self.window_seconds, self.max_attempts],
            )

            if result == -1:
                logger.warning(f"Rate limit exceeded for identifier: {identifier}")
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Too many requests. Please try again later.",
                )
        except redis.RedisError as e:
            logger.exception(f"Redis error during rate limiting check: {e}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Could not connect to rate limiting service.",
            )


# Dependency providers for rate limiters.
# This pattern replaces module-level instances to allow for dependency injection
# of the Redis client, which is only available during a request.

def get_login_rate_limiter(
    redis_client: redis.Redis = Depends(get_redis),
) -> "RateLimitChecker":
    """Dependency for the login endpoint rate limiter."""
    return RateLimitChecker(
        redis_client=redis_client, max_attempts=5, window_seconds=15 * 60, namespace="login"
    )


def get_registration_rate_limiter(
    redis_client: redis.Redis = Depends(get_redis),
) -> "RateLimitChecker":
    """Dependency for the registration endpoint rate limiter."""
    return RateLimitChecker(
        redis_client=redis_client, max_attempts=3, window_seconds=60 * 60, namespace="registration"
    )


def get_password_reset_rate_limiter(
    redis_client: redis.Redis = Depends(get_redis),
) -> "RateLimitChecker":
    """Dependency for the password reset endpoint rate limiter."""
    return RateLimitChecker(
        redis_client=redis_client, max_attempts=3, window_seconds=60 * 60, namespace="password_reset"
    )


def get_password_reset_confirm_rate_limiter(
    redis_client: redis.Redis = Depends(get_redis),
) -> "RateLimitChecker":
    """Dependency for the password reset confirmation endpoint rate limiter."""
    return RateLimitChecker(
        redis_client=redis_client, max_attempts=5, window_seconds=15 * 60, namespace="password_reset_confirm"
    )


async def get_client_info(request: Request) -> Dict[str, Any]:
    """
    Extract client information from request
    
    Args:
        request: FastAPI request object
        
    Returns:
        Dictionary with client information
    """
    return {
        "client_ip": request.client.host if request.client else "unknown",
        "user_agent": request.headers.get("User-Agent", "unknown"),
        "forwarded_for": request.headers.get("X-Forwarded-For"),
        "real_ip": request.headers.get("X-Real-IP")
    }
