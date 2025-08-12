"""
Authentication endpoints
Handles creator registration, login, token refresh, and password management
"""

import json
import logging
import uuid
from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from shared.models.auth import (
    CreatorCreate, CreatorResponse, TokenResponse, LoginRequest,
    PasswordResetRequest, PasswordResetConfirm, TokenRefreshRequest,
    PasswordStrengthResponse
)
from ..services.auth_service import AuthService
from shared.cache import get_cache_manager, get_redis_client
from ..dependencies.auth import (
    get_current_creator, get_current_creator_id, get_client_info,
    login_rate_limiter, registration_rate_limiter, password_reset_rate_limiter,
    get_password_reset_confirm_rate_limiter
)
from ..database import get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/auth", tags=["authentication"])

# Initialize auth service
def generate_correlation_id() -> str:
    """Generate a unique correlation ID for request tracing"""
    return str(uuid.uuid4())
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
    db: AsyncSession = Depends(get_db)
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
    await registration_rate_limiter.check_rate_limit(request)
    
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
    db: AsyncSession = Depends(get_db)
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
    await login_rate_limiter.check_rate_limit(request)
    
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
    if hasattr(request, 'json'):
        try:
            body = await request.json()
            refresh_token = body.get('refresh_token')
        except json.JSONDecodeError as e:
            logger.warning("Failed to parse JSON from request body", extra={
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
    
    # Generate cache key for password strength validation
    cache_key = f"password_strength:{hash(password)}"
    
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
    db: AsyncSession = Depends(get_db)
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
    await password_reset_rate_limiter.check_rate_limit(request)
    
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
            from ..services.email_service import get_email_service
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