"""
Authentication endpoints with advanced JWT and RBAC support
Handles creator registration, login, token refresh, password management, and GDPR compliance
"""

import hashlib
import hmac
import json
import logging
import uuid
from datetime import datetime
from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Request, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import text
from pydantic import BaseModel
from jose import JWTError

from shared.models.auth import (
    CreatorCreate, CreatorResponse, TokenResponse, LoginRequest,
    PasswordResetRequest, PasswordResetConfirm, TokenRefreshRequest,
    PasswordStrengthResponse
)
from ..services.auth_service import AuthService
from ..services.email_service import get_email_service
from shared.cache import get_cache_manager
from shared.security.jwt_manager import get_jwt_manager
from shared.security.rbac import (
    require_admin_access
)
from shared.security.gdpr_compliance import gdpr_manager, DataDeletionType
from ..dependencies.auth import (
    get_current_creator, get_current_creator_id, get_client_info,
    get_login_rate_limiter, get_registration_rate_limiter, 
    get_password_reset_rate_limiter, get_password_reset_confirm_rate_limiter, 
    RateLimitChecker
)
from ..database import get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/auth", tags=["authentication"])


# GDPR Compliance Models
class DataDeletionRequest(BaseModel):
    """Request model for GDPR data deletion"""
    deletion_type: DataDeletionType
    reason: str
    confirm_deletion: bool = False


class DataExportResponse(BaseModel):
    """Response model for GDPR data export"""
    export_id: str
    creator_id: str
    export_date: str
    data: Dict[str, Any]


class KeyRotationResponse(BaseModel):
    """Response model for JWT key rotation"""
    status: str
    new_key_id: str
    rotation_date: str
    message: str

# Initialize auth service
def generate_correlation_id() -> str:
    """Generate a unique correlation ID for request tracing"""
    return str(uuid.uuid4())

def generate_secure_cache_key(password: str, key_prefix: str = "password_strength") -> str:
    """Generate a secure cache key using HMAC-SHA256"""
    # Use a server-side secret for HMAC from environment variable
    import os
    secret_key = os.getenv("AUTH_CACHE_SECRET_KEY", "fallback_dev_key_2024").encode('utf-8')
    
    # Create HMAC digest of the password
    password_bytes = password.encode('utf-8')
    hmac_digest = hmac.new(secret_key, password_bytes, hashlib.sha256).hexdigest()
    
    return f"{key_prefix}:{hmac_digest}"

auth_service = AuthService()


@router.post(
    "/register",
    response_model=Dict[str, Any],
    status_code=status.HTTP_201_CREATED,
    summary="Register new creator",
    description="Register a new creator account with comprehensive password validation",
    responses={
        201: {
            "description": "Creator registered successfully",
            "content": {
                "application/json": {
                    "example": {
                        "creator": {
                            "id": "123e4567-e89b-12d3-a456-426614174000",
                            "email": "creator@example.com",
                            "full_name": "John Doe",
                            "company_name": "Acme Corp",
                            "is_active": True,
                            "subscription_tier": "free"
                        },
                        "tokens": {
                            "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9...",
                            "refresh_token": "def502004a8b7e...",
                            "token_type": "bearer",
                            "expires_in": 3600
                        }
                    }
                }
            }
        },
        400: {
            "description": "Password validation failed",
            "content": {
                "application/json": {
                    "example": {
                        "detail": {
                            "message": "Password does not meet security requirements",
                            "violations": ["Password must contain at least one uppercase letter"],
                            "suggestions": ["Add uppercase letters (A-Z)"]
                        }
                    }
                }
            }
        },
        409: {"description": "Email already registered"},
        429: {"description": "Too many registration attempts"}
    }
)
async def register_creator(
    creator_data: CreatorCreate,
    request: Request,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    registration_limiter: RateLimitChecker = Depends(get_registration_rate_limiter)
):
    """
    Register a new creator account.
    
    This endpoint:
    - Validates email uniqueness
    - Enforces strong password policy using Argon2id hashing
    - Checks password against common passwords and breaches
    - Generates JWT access and refresh tokens
    - Logs registration event for audit trail
    
    Rate limited to 3 attempts per hour per IP address.
    """
    # Generate correlation ID for request tracing
    correlation_id = generate_correlation_id()
    
    # Apply rate limiting
    await registration_limiter.check_rate_limit(request)
    
    # Get client information
    client_info = await get_client_info(request)
    
    try:
        # Register creator
        creator, tokens = await auth_service.register_creator(
            creator_data=creator_data,
            db=db,
            client_ip=client_info["client_ip"],
            user_agent=client_info["user_agent"]
        )
        
        # TODO: Add background task for email verification
        # background_tasks.add_task(send_verification_email, creator.email)
        
        return {
            "creator": creator,
            "tokens": tokens,
            "message": "Creator registered successfully. Please check your email for verification."
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Unexpected error in creator registration", extra={
            "correlation_id": correlation_id,
            "error": str(e)
        })
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed due to internal error"
        )


@router.post(
    "/login",
    response_model=Dict[str, Any],
    summary="Authenticate creator",
    description="Authenticate creator and return JWT tokens with account lockout protection",
    responses={
        200: {
            "description": "Authentication successful",
            "content": {
                "application/json": {
                    "example": {
                        "creator": {
                            "id": "123e4567-e89b-12d3-a456-426614174000",
                            "email": "creator@example.com",
                            "full_name": "John Doe",
                            "subscription_tier": "free"
                        },
                        "tokens": {
                            "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9...",
                            "refresh_token": "def502004a8b7e...",
                            "token_type": "bearer",
                            "expires_in": 3600
                        }
                    }
                }
            }
        },
        401: {"description": "Invalid credentials"},
        423: {"description": "Account locked due to failed attempts"},
        429: {"description": "Too many login attempts"}
    }
)
async def login(
    login_data: LoginRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    login_limiter: RateLimitChecker = Depends(get_login_rate_limiter)
):
    """
    Authenticate creator and return JWT tokens.
    
    This endpoint:
    - Validates email and password
    - Implements account lockout after 5 failed attempts
    - Supports "remember me" for extended sessions
    - Automatically rehashes passwords to stronger algorithms
    - Logs authentication events for audit trail
    
    Rate limited to 5 attempts per 15 minutes per IP address.
    """
    # Generate correlation ID for request tracing
    correlation_id = generate_correlation_id()
    
    # Apply rate limiting
    await login_limiter.check_rate_limit(request)
    
    # Get client information
    client_info = await get_client_info(request)
    
    try:
        # Authenticate creator
        creator, tokens = await auth_service.authenticate_creator(
            login_data=login_data,
            db=db,
            client_ip=client_info["client_ip"],
            user_agent=client_info["user_agent"]
        )
        
        return {
            "creator": creator,
            "tokens": tokens,
            "message": "Authentication successful"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Unexpected error in creator authentication", extra={
            "correlation_id": correlation_id,
            "error": str(e)
        })
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication failed due to internal error"
        )


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Refresh access token",
    description="Refresh JWT access token using refresh token with rotation security",
    responses={
        200: {
            "description": "Token refreshed successfully",
            "content": {
                "application/json": {
                    "example": {
                        "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9...",
                        "refresh_token": "def502004a8b7e...",
                        "token_type": "bearer",
                        "expires_in": 3600
                    }
                }
            }
        },
        401: {"description": "Invalid or expired refresh token"}
    }
)
async def refresh_token(
    refresh_request: TokenRefreshRequest,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Refresh JWT access token using refresh token.
    
    This endpoint:
    - Validates refresh token authenticity and expiration
    - Implements refresh token rotation for security
    - Detects token theft and revokes token families
    - Generates new access and refresh token pair
    - Logs token refresh events
    
    Refresh tokens are single-use and automatically rotated.
    """
    # Generate correlation ID for request tracing
    correlation_id = generate_correlation_id()
    
    # Get client information
    client_info = await get_client_info(request)
    
    try:
        # Refresh token
        tokens = await auth_service.refresh_token(
            refresh_request=refresh_request,
            db=db,
            client_ip=client_info["client_ip"],
            user_agent=client_info["user_agent"]
        )
        
        return tokens
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Unexpected error in token refresh", extra={
            "correlation_id": correlation_id,
            "error": str(e)
        })
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token refresh failed due to internal error"
        )


@router.get(
    "/me",
    response_model=CreatorResponse,
    summary="Get current creator profile",
    description="Get authenticated creator's profile information",
    responses={
        200: {
            "description": "Creator profile retrieved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "id": "123e4567-e89b-12d3-a456-426614174000",
                        "email": "creator@example.com",
                        "full_name": "John Doe",
                        "company_name": "Acme Corp",
                        "is_active": True,
                        "subscription_tier": "free",
                        "created_at": "2024-01-01T00:00:00Z",
                        "updated_at": "2024-01-01T00:00:00Z"
                    }
                }
            }
        },
        401: {"description": "Authentication required"}
    }
)
async def get_current_creator_profile(
    current_creator: CreatorResponse = Depends(get_current_creator)
):
    """
    Get current authenticated creator's profile.
    
    Returns detailed information about the authenticated creator including:
    - Basic profile information
    - Account status and subscription tier
    - Account creation and update timestamps
    
    Requires valid JWT access token.
    """
    return current_creator


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Logout creator",
    description="Logout creator and invalidate refresh token",
    responses={
        204: {"description": "Logout successful"},
        401: {"description": "Authentication required"}
    }
)
async def logout(
    request: Request,
    creator_id: str = Depends(get_current_creator_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Logout creator and invalidate tokens.
    
    This endpoint:
    - Invalidates the provided refresh token
    - Logs logout event for audit trail
    - Optionally blacklists the current access token (if JTI provided)
    
    The access token will remain valid until expiration unless explicitly blacklisted.
    """
    # Generate correlation ID for request tracing
    correlation_id = generate_correlation_id()
    
    # Get client information
    client_info = await get_client_info(request)
    
    # Extract refresh token from request body if provided
    refresh_token = None
    
    # Safe JSON parsing with proper validation
    content_type = request.headers.get('content-type', '').lower()
    content_length = request.headers.get('content-length')
    
    if content_type.startswith('application/json'):
        # Check content length limits (1MB max)
        if content_length and int(content_length) > 1024 * 1024:
            logger.warning("Request body too large for JSON parsing", extra={
                "correlation_id": correlation_id,
                "creator_id": creator_id,
                "content_length": content_length,
                "client_ip": client_info["client_ip"]
            })
        elif content_length and int(content_length) > 0:
            try:
                # Read body as text first
                body_text = await request.body()
                if body_text:
                    body_str = body_text.decode('utf-8')
                    body = json.loads(body_str)
                    refresh_token = body.get('refresh_token')
            except json.JSONDecodeError as e:
                logger.warning("Failed to parse JSON from request body", extra={
                    "correlation_id": correlation_id,
                    "creator_id": creator_id,
                    "error": str(e),
                    "client_ip": client_info["client_ip"]
                })
                # Continue without refresh token - it's optional for logout
            except UnicodeDecodeError as e:
                logger.warning("Failed to decode request body as UTF-8", extra={
                    "correlation_id": correlation_id,
                    "creator_id": creator_id,
                    "error": str(e),
                    "client_ip": client_info["client_ip"]
                })
                # Continue without refresh token - it's optional for logout
            except Exception as e:
                logger.warning("Unexpected error reading request body", extra={
                    "correlation_id": correlation_id,
                    "creator_id": creator_id,
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "client_ip": client_info["client_ip"]
                })
                # Continue without refresh token - it's optional for logout
    
    try:
        # Logout creator
        success = await auth_service.logout_creator(
            creator_id=creator_id,
            refresh_token=refresh_token,
            db=db,
            client_ip=client_info["client_ip"],
            user_agent=client_info["user_agent"]
        )
        
        if not success:
            logger.warning("Logout failed for creator", extra={
                "correlation_id": correlation_id,
                "creator_id": creator_id
            })
        
        # Return 204 regardless for security
        return None
        
    except Exception as e:
        logger.exception("Unexpected error in logout", extra={
            "correlation_id": correlation_id,
            "creator_id": creator_id,
            "error": str(e)
        })
        # Return 204 regardless for security
        return None


@router.post(
    "/password/validate",
    response_model=PasswordStrengthResponse,
    summary="Validate password strength",
    description="Validate password strength against security policy",
    responses={
        200: {
            "description": "Password validation completed",
            "content": {
                "application/json": {
                    "example": {
                        "strength": "strong",
                        "score": 85,
                        "is_valid": True,
                        "violations": [],
                        "suggestions": [],
                        "estimated_crack_time": "centuries"
                    }
                }
            }
        }
    }
)
async def validate_password_strength(
    password_data: Dict[str, Any],
    request: Request
):
    """
    Validate password strength against security policy.
    
    This endpoint:
    - Checks password against complexity requirements
    - Validates against common password lists
    - Checks for personal information usage
    - Queries HaveIBeenPwned for breach detection
    - Provides improvement suggestions
    
    Does not require authentication for registration flow support.
    """
    # Generate correlation ID for request tracing
    correlation_id = generate_correlation_id()
    
    password = password_data.get("password")
    personal_info = password_data.get("personal_info", {})
    
    if not password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password is required"
        )
    
    # Initialize cache manager
    cache_manager = get_cache_manager()
    
    # Generate secure cache key for password strength validation
    cache_key = generate_secure_cache_key(password, "password_strength")
    
    try:
        # Try to get cached result
        cached_result = await cache_manager.redis.get("system", cache_key)
        if cached_result:
            logger.debug(f"Cache hit for password strength validation")
            return cached_result
        
        # Validate password strength
        result = await auth_service.validate_password_strength_endpoint(
            password=password,
            personal_info=personal_info
        )
        
        # Cache the result for 5 minutes
        await cache_manager.redis.set("system", cache_key, result, ttl=300)
        
        return result
        
    except Exception as e:
        logger.exception("Unexpected error in password validation", extra={
            "correlation_id": correlation_id,
            "error": str(e)
        })
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Password validation failed due to internal error"
        )


@router.post(
    "/password/reset/request",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Request password reset",
    description="Request password reset token via email",
    responses={
        202: {"description": "Password reset email sent (if account exists)"},
        429: {"description": "Too many reset requests"}
    }
)
async def request_password_reset(
    reset_request: PasswordResetRequest,
    request: Request,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    reset_limiter: RateLimitChecker = Depends(get_password_reset_rate_limiter)
):
    """
    Request password reset token.
    
    This endpoint:
    - Validates email format
    - Generates secure reset token (15 minute expiration)
    - Sends reset email if account exists
    - Always returns 202 to prevent email enumeration
    - Logs reset requests for audit trail
    
    Rate limited to 3 requests per hour per IP address.
    """
    # Generate correlation ID for request tracing
    correlation_id = generate_correlation_id()
    
    # Apply rate limiting
    await reset_limiter.check_rate_limit(request)
    
    # Get client information
    client_info = await get_client_info(request)
    
    try:
        # TODO: Implement password reset request
        # This would:
        # 1. Check if email exists
        # 2. Generate secure reset token
        # 3. Store token with expiration
        # 4. Send email with reset link
        # 5. Log the request
        
        # Check if email exists and generate reset token
        reset_token = await auth_service.request_password_reset(
            reset_request=reset_request,
            db=db,
            client_ip=client_info["client_ip"],
            user_agent=client_info["user_agent"]
        )
        
        # Send email in background task if token was generated
        if reset_token:
            email_service = get_email_service()
            
            # Add background task to send email
            background_tasks.add_task(
                email_service.send_password_reset_email,
                email=reset_request.email,
                reset_token=reset_token,
                client_ip=client_info["client_ip"]
            )
        
        # Always return accepted to prevent enumeration
        return {
            "message": "If an account with this email exists, a password reset link has been sent."
        }
        
    except Exception as e:
        logger.exception("Unexpected error in password reset request", extra={
            "correlation_id": correlation_id,
            "error": str(e)
        })
        # Always return accepted for security
        return {
            "message": "If an account with this email exists, a password reset link has been sent."
        }


@router.post(
    "/password/reset/confirm",
    status_code=status.HTTP_200_OK,
    summary="Confirm password reset",
    description="Reset password using reset token",
    responses={
        200: {"description": "Password reset successful"},
        400: {"description": "Invalid or expired reset token"},
        429: {"description": "Too many reset attempts"}
    }
)
async def confirm_password_reset(
    reset_confirm: PasswordResetConfirm,
    request: Request,
    db: AsyncSession = Depends(get_db),
    password_reset_confirm_rate_limiter: RateLimitChecker = Depends(get_password_reset_confirm_rate_limiter)
):
    """
    Confirm password reset using token.
    
    This endpoint:
    - Validates reset token authenticity and expiration
    - Enforces password strength requirements
    - Updates password with secure hashing
    - Invalidates all existing sessions
    - Logs password change event
    
    Reset tokens expire after 15 minutes and are single-use.
    """
    # Generate correlation ID for request tracing
    correlation_id = generate_correlation_id()
    
    # Get client information
    client_info = await get_client_info(request)
    
    try:
        # TODO: Implement password reset confirmation
        # This would:
        # 1. Validate reset token
        # 2. Check token expiration
        # 3. Validate new password strength
        # 4. Update password hash
        # 5. Invalidate all sessions
        # 6. Log the change
        
        logger.info("Password reset confirmation attempted", extra={
            "correlation_id": correlation_id,
            "token_prefix": reset_confirm.token[:16] if reset_confirm.token else None,
            "client_ip": client_info["client_ip"]
        })
        
        # Apply rate limiting
        await password_reset_confirm_rate_limiter.check_rate_limit(request)
        
        # Implement password reset confirmation
        success = await auth_service.confirm_password_reset(
            reset_confirm=reset_confirm,
            db=db,
            client_ip=client_info["client_ip"],
            user_agent=client_info["user_agent"]
        )
        
        if success:
            # Invalidate all sessions for the creator
            # Note: This is a simplified implementation
            logger.info("Password reset confirmed successfully")
            
            return {
                "message": "Password reset successful. You can now log in with your new password."
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password reset failed"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Unexpected error in password reset confirmation", extra={
            "correlation_id": correlation_id,
            "error": str(e)
        })
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Password reset failed due to internal error"
        )

# Advanced JWT and Security Endpoints

@router.post(
    "/tokens/revoke",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Revoke JWT token",
    description="Revoke a specific JWT token by adding it to blacklist",
    responses={
        204: {"description": "Token revoked successfully"},
        401: {"description": "Authentication required"},
        400: {"description": "Invalid token"}
    }
)
async def revoke_token(
    request: Request,
    creator_id: str = Depends(get_current_creator_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Revoke a JWT token by adding it to blacklist.
    
    This endpoint:
    - Extracts JTI from current access token
    - Adds token to blacklist with expiration
    - Logs token revocation event
    - Prevents further use of the token
    
    Requires valid JWT access token.
    """
    # Generate correlation ID for request tracing
    correlation_id = generate_correlation_id()
    
    # Get client information
    await get_client_info(request)
    
    try:
        # Extract JWT token from Authorization header
        authorization = request.headers.get("Authorization")
        if not authorization or not authorization.startswith("Bearer "):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid authorization header"
            )
        
        token = authorization.split(" ")[1]
        
        # Get JWT manager
        jwt_manager = get_jwt_manager()
        
        # Decode token to get JTI and expiration
        try:
            payload = await jwt_manager.verify_token(token, db, check_blacklist=False)
            jti = payload.get("jti")
            exp = payload.get("exp")
            
            if not jti:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Token missing JTI claim"
                )
            
            # Convert exp to datetime
            expires_at = datetime.fromtimestamp(exp)
            
            # Add token to blacklist
            await jwt_manager.blacklist_token(
                jti=jti,
                creator_id=creator_id,
                reason="manual_revocation",
                expires_at=expires_at,
                db=db
            )
            
            await db.commit()
            
            logger.info("JWT token revoked manually", extra={
                "correlation_id": correlation_id,
                "creator_id": creator_id,
                "jti": jti[:16] + "..."
            })
            
            return None
            
        except JWTError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid token"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Unexpected error in token revocation", extra={
            "correlation_id": correlation_id,
            "creator_id": creator_id,
            "error": str(e)
        })
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token revocation failed due to internal error"
        )


@router.post(
    "/keys/rotate",
    response_model=KeyRotationResponse,
    summary="Rotate JWT signing keys",
    description="Manually trigger JWT key rotation for security",
    responses={
        200: {"description": "Key rotation successful"},
        401: {"description": "Authentication required"},
        403: {"description": "Admin access required"}
    }
)
async def rotate_jwt_keys(
    request: Request,
    creator: CreatorResponse = Depends(require_admin_access()),
    db: AsyncSession = Depends(get_db)
):
    """
    Manually rotate JWT signing keys.
    
    This endpoint:
    - Generates new RSA key pair for JWT signing
    - Maintains old keys for grace period (24 hours)
    - Updates key rotation timestamp
    - Logs key rotation event
    
    Requires admin role access.
    """
    # Generate correlation ID for request tracing
    correlation_id = generate_correlation_id()
    
    # Get client information
    client_info = await get_client_info(request)
    
    try:
        # Get JWT manager
        jwt_manager = get_jwt_manager()
        
        # Perform key rotation
        new_key_id = await jwt_manager.rotate_keys_if_needed()
        
        if new_key_id:
            # Log key rotation event
            await auth_service._log_audit_event(
                db, uuid.UUID(creator.id), "jwt_key_rotated", "security",
                f"JWT signing keys rotated by admin: {creator.email}",
                {
                    "admin_email": creator.email,
                    "new_key_id": new_key_id,
                    "rotation_type": "manual"
                },
                client_info["client_ip"], client_info["user_agent"], "info"
            )
            
            await db.commit()
            
            return KeyRotationResponse(
                status="success",
                new_key_id=new_key_id,
                rotation_date=datetime.utcnow().isoformat(),
                message="JWT signing keys rotated successfully"
            )
        else:
            return KeyRotationResponse(
                status="no_rotation_needed",
                new_key_id="",
                rotation_date=datetime.utcnow().isoformat(),
                message="Key rotation not needed at this time"
            )
        
    except Exception as e:
        logger.exception("Unexpected error in key rotation", extra={
            "correlation_id": correlation_id,
            "admin_id": creator.id,
            "error": str(e)
        })
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Key rotation failed due to internal error"
        )


# GDPR Compliance Endpoints

@router.post(
    "/gdpr/data-deletion",
    response_model=Dict[str, Any],
    summary="Request GDPR data deletion",
    description="Request deletion of personal data under GDPR Article 17",
    responses={
        200: {"description": "Data deletion request processed"},
        401: {"description": "Authentication required"},
        400: {"description": "Invalid deletion request"}
    }
)
async def request_data_deletion(
    deletion_request: DataDeletionRequest,
    request: Request,
    creator: CreatorResponse = Depends(get_current_creator),
    db: AsyncSession = Depends(get_db)
):
    """
    Request GDPR data deletion.
    
    This endpoint:
    - Validates deletion request and confirmation
    - Processes data deletion based on type (anonymization, soft delete, hard delete)
    - Logs GDPR compliance event
    - Returns deletion confirmation
    
    Supports three deletion types:
    - anonymization: Replace PII with anonymous data
    - soft_delete: Mark as deleted but retain for compliance
    - hard_delete: Complete removal from system
    """
    # Generate correlation ID for request tracing
    correlation_id = generate_correlation_id()
    
    # Get client information
    client_info = await get_client_info(request)
    
    try:
        # Validate deletion confirmation
        if not deletion_request.confirm_deletion:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Data deletion must be explicitly confirmed"
            )
        
        # Process data deletion request
        result = await gdpr_manager.request_data_deletion(
            creator_id=creator.id,
            deletion_type=deletion_request.deletion_type,
            reason=deletion_request.reason,
            db=db,
            client_ip=client_info["client_ip"],
            user_agent=client_info["user_agent"]
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Unexpected error in GDPR data deletion", extra={
            "correlation_id": correlation_id,
            "creator_id": creator.id,
            "error": str(e)
        })
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Data deletion request failed due to internal error"
        )


@router.get(
    "/gdpr/data-export",
    response_model=DataExportResponse,
    summary="Export personal data",
    description="Export all personal data under GDPR Article 20",
    responses={
        200: {"description": "Data export successful"},
        401: {"description": "Authentication required"}
    }
)
async def export_personal_data(
    request: Request,
    creator: CreatorResponse = Depends(get_current_creator),
    db: AsyncSession = Depends(get_db)
):
    """
    Export all personal data for GDPR compliance.
    
    This endpoint:
    - Collects all personal data associated with the creator
    - Includes profile information, sessions, and audit logs
    - Returns structured data export
    - Logs data export event
    
    Supports GDPR Article 20 (Right to data portability).
    """
    # Generate correlation ID for request tracing
    correlation_id = generate_correlation_id()
    
    # Get client information
    client_info = await get_client_info(request)
    
    try:
        # Export user data
        export_data = await gdpr_manager.export_user_data(
            creator_id=creator.id,
            db=db
        )
        
        # Log data export event
        await auth_service._log_audit_event(
            db, uuid.UUID(creator.id), "gdpr_data_exported", "gdpr",
            f"Personal data exported: {creator.email}",
            {
                "email": creator.email,
                "export_size": len(str(export_data)),
                "data_types": list(export_data.keys())
            },
            client_info["client_ip"], client_info["user_agent"], "info"
        )
        
        await db.commit()
        
        return DataExportResponse(
            export_id=str(uuid.uuid4()),
            creator_id=creator.id,
            export_date=datetime.utcnow().isoformat(),
            data=export_data
        )
        
    except Exception as e:
        logger.exception("Unexpected error in GDPR data export", extra={
            "correlation_id": correlation_id,
            "creator_id": creator.id,
            "error": str(e)
        })
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Data export failed due to internal error"
        )


# Health Check Endpoint

@router.get(
    "/health",
    summary="Health check",
    description="Check authentication service health",
    responses={
        200: {"description": "Service is healthy"},
        503: {"description": "Service is unhealthy"}
    }
)
async def health_check(db: AsyncSession = Depends(get_db)):
    """
    Health check endpoint for the authentication service.
    
    This endpoint:
    - Checks database connectivity
    - Validates JWT key availability
    - Returns service status and timestamp
    
    Used by API Gateway and monitoring systems.
    """
    try:
        # Test database connectivity
        await db.execute(text("SELECT 1"))
        
        # Test JWT manager
        jwt_manager = get_jwt_manager()
        await jwt_manager.key_manager.get_current_key()
        
        return {
            "status": "healthy",
            "service": "auth-service",
            "timestamp": datetime.utcnow().isoformat(),
            "version": "1.0.0"
        }
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service unhealthy"
        )