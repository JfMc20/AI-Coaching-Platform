"""
Authentication Service
Handles user authentication, JWT tokens, and security operations

This service has been migrated to use the centralized environment constants system
located in shared.config.env_constants for consistent configuration management
across all services.
"""

import uuid
import secrets
import hashlib
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Tuple

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status
from jose import JWTError, jwt

from shared.config.env_constants import (
    JWT_SECRET_KEY, JWT_ALGORITHM, JWT_ACCESS_TOKEN_EXPIRE_MINUTES,
    JWT_REFRESH_TOKEN_EXPIRE_DAYS, MAX_FAILED_LOGIN_ATTEMPTS,
    ACCOUNT_LOCKOUT_DURATION_MINUTES, PASSWORD_RESET_TOKEN_EXPIRE_MINUTES,
    get_env_value
)
from shared.models.database import Creator, RefreshToken, PasswordResetToken, AuditLog
from shared.models.auth import (
    CreatorCreate, CreatorResponse, TokenResponse, LoginRequest,
    PasswordResetRequest, PasswordResetConfirm, TokenRefreshRequest,
    PasswordStrengthResponse
)
from shared.security.password_security import (
    PasswordHasher, PasswordValidator, validate_password_strength
)

logger = logging.getLogger(__name__)


class AuthService:
    """
    Authentication service with comprehensive security features
    
    Configuration is managed through the centralized environment constants system
    in shared.config.env_constants, which provides environment-specific defaults
    and eliminates scattered hardcoded values throughout the codebase.
    """
    
    def __init__(self):
        # JWT Configuration - using centralized constants with environment-specific defaults
        self.jwt_secret_key = get_env_value(JWT_SECRET_KEY, fallback=True)
        self.jwt_algorithm = get_env_value(JWT_ALGORITHM, fallback=True)
        self.jwt_access_token_expire_minutes = int(get_env_value(JWT_ACCESS_TOKEN_EXPIRE_MINUTES, fallback=True))
        self.jwt_refresh_token_expire_days = int(get_env_value(JWT_REFRESH_TOKEN_EXPIRE_DAYS, fallback=True))
        
        # Security Configuration - using centralized constants with environment-specific defaults
        self.max_failed_login_attempts = int(get_env_value(MAX_FAILED_LOGIN_ATTEMPTS, fallback=True))
        self.account_lockout_duration_minutes = int(get_env_value(ACCOUNT_LOCKOUT_DURATION_MINUTES, fallback=True))
        self.password_reset_token_expire_minutes = int(get_env_value(PASSWORD_RESET_TOKEN_EXPIRE_MINUTES, fallback=True))
        
        # Initialize security components
        self.password_hasher = PasswordHasher()
        self.password_validator = PasswordValidator()
        
        # Validate required configuration
        if not self.jwt_secret_key:
            raise ValueError(f"{JWT_SECRET_KEY} environment variable is required")
    
    async def register_creator(
        self, 
        creator_data: CreatorCreate, 
        db: AsyncSession,
        client_ip: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Tuple[CreatorResponse, TokenResponse]:
        """
        Register a new creator with comprehensive validation
        
        Args:
            creator_data: Creator registration data
            db: Database session
            client_ip: Client IP address
            user_agent: Client user agent
            
        Returns:
            Tuple of (CreatorResponse, TokenResponse)
            
        Raises:
            HTTPException: If registration fails
        """
        try:
            # 1. Check if email already exists
            existing_creator = await db.execute(
                select(Creator).where(Creator.email == creator_data.email.lower())
            )
            if existing_creator.scalar_one_or_none():
                await self._log_audit_event(
                    db, None, "registration_failed", "auth",
                    f"Registration attempt with existing email: {creator_data.email}",
                    {"email": creator_data.email, "reason": "email_exists"},
                    client_ip, user_agent, "warning"
                )
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Email address is already registered"
                )
            
            # 2. Validate password strength
            personal_info = {
                "email": creator_data.email,
                "name": creator_data.full_name,
                "company": creator_data.company_name or ""
            }
            
            password_result = await validate_password_strength(
                creator_data.password, personal_info
            )
            
            if not password_result.is_valid:
                await self._log_audit_event(
                    db, None, "registration_failed", "auth",
                    f"Registration failed due to weak password: {creator_data.email}",
                    {"email": creator_data.email, "violations": password_result.violations},
                    client_ip, user_agent, "warning"
                )
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "message": "Password does not meet security requirements",
                        "violations": password_result.violations,
                        "suggestions": password_result.suggestions
                    }
                )
            
            # 3. Hash password using Argon2id
            password_hash = self.password_hasher.hash_password(creator_data.password, use_argon2=True)
            
            # 4. Create creator record
            creator = Creator(
                email=creator_data.email.lower(),
                password_hash=password_hash,
                full_name=creator_data.full_name,
                company_name=creator_data.company_name,
                is_active=True,
                is_verified=False,  # Email verification required
                subscription_tier="free"
            )
            
            db.add(creator)
            
            try:
                await db.flush()  # Get the ID without committing
                
                # 5. Generate JWT tokens
                tokens = await self._generate_token_pair(
                    creator.id, db, client_ip, user_agent
                )
                
                # 6. Log successful registration
                await self._log_audit_event(
                    db, creator.id, "creator_registered", "auth",
                    f"New creator registered: {creator.email}",
                    {"email": creator.email, "subscription_tier": creator.subscription_tier},
                    client_ip, user_agent, "info"
                )
                
                await db.commit()
                
            except IntegrityError as e:
                await db.rollback()
                logger.warning(f"Integrity error during registration for {creator_data.email}: {e}")
                await self._log_audit_event(
                    db, None, "registration_failed", "auth",
                    f"Registration failed due to integrity constraint: {creator_data.email}",
                    {"email": creator_data.email, "reason": "integrity_error"},
                    client_ip, user_agent, "warning"
                )
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Email address is already registered"
                )
            
            # 7. Return response
            creator_response = CreatorResponse(
                id=str(creator.id),
                email=creator.email,
                full_name=creator.full_name,
                company_name=creator.company_name,
                is_active=creator.is_active,
                subscription_tier=creator.subscription_tier,
                created_at=creator.created_at,
                updated_at=creator.updated_at
            )
            
            return creator_response, tokens
            
        except HTTPException:
            await db.rollback()
            raise
        except Exception as e:
            await db.rollback()
            logger.exception(f"Creator registration failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Registration failed due to internal error"
            )
    
    async def authenticate_creator(
        self,
        login_data: LoginRequest,
        db: AsyncSession,
        client_ip: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Tuple[CreatorResponse, TokenResponse]:
        """
        Authenticate creator and return tokens
        
        Args:
            login_data: Login credentials
            db: Database session
            client_ip: Client IP address
            user_agent: Client user agent
            
        Returns:
            Tuple of (CreatorResponse, TokenResponse)
            
        Raises:
            HTTPException: If authentication fails
        """
        try:
            # 1. Find creator by email
            result = await db.execute(
                select(Creator).where(Creator.email == login_data.email.lower())
            )
            creator = result.scalar_one_or_none()
            
            if not creator:
                await self._log_audit_event(
                    db, None, "login_failed", "auth",
                    f"Login attempt with non-existent email: {login_data.email}",
                    {"email": login_data.email, "reason": "email_not_found"},
                    client_ip, user_agent, "warning"
                )
                # Use generic error to prevent email enumeration
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid email or password"
                )
            
            # 2. Check if account is locked
            if creator.locked_until and creator.locked_until > datetime.utcnow():
                await self._log_audit_event(
                    db, creator.id, "login_blocked", "auth",
                    f"Login attempt on locked account: {creator.email}",
                    {"email": creator.email, "locked_until": creator.locked_until.isoformat()},
                    client_ip, user_agent, "warning"
                )
                raise HTTPException(
                    status_code=status.HTTP_423_LOCKED,
                    detail=f"Account is locked until {creator.locked_until.isoformat()}"
                )
            
            # 3. Check if account is active
            if not creator.is_active:
                await self._log_audit_event(
                    db, creator.id, "login_failed", "auth",
                    f"Login attempt on inactive account: {creator.email}",
                    {"email": creator.email, "reason": "account_inactive"},
                    client_ip, user_agent, "warning"
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Account is deactivated"
                )
            
            # 4. Verify password
            password_valid = self.password_hasher.verify_password(
                login_data.password, creator.password_hash
            )
            
            if not password_valid:
                # Increment failed login attempts
                creator.failed_login_attempts += 1
                
                # Lock account if too many failed attempts
                if creator.failed_login_attempts >= self.max_failed_login_attempts:
                    creator.locked_until = datetime.utcnow() + timedelta(
                        minutes=self.account_lockout_duration_minutes
                    )
                    
                    await self._log_audit_event(
                        db, creator.id, "account_locked", "security",
                        f"Account locked due to failed login attempts: {creator.email}",
                        {
                            "email": creator.email,
                            "failed_attempts": creator.failed_login_attempts,
                            "locked_until": creator.locked_until.isoformat()
                        },
                        client_ip, user_agent, "error"
                    )
                else:
                    await self._log_audit_event(
                        db, creator.id, "login_failed", "auth",
                        f"Invalid password for: {creator.email}",
                        {
                            "email": creator.email,
                            "failed_attempts": creator.failed_login_attempts,
                            "remaining_attempts": self.max_failed_login_attempts - creator.failed_login_attempts
                        },
                        client_ip, user_agent, "warning"
                    )
                
                await db.commit()
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid email or password"
                )
            
            # 5. Reset failed login attempts on successful authentication
            creator.failed_login_attempts = 0
            creator.locked_until = None
            creator.last_login_at = datetime.utcnow()
            
            # 6. Check if password needs rehashing
            if self.password_hasher.needs_rehash(creator.password_hash):
                new_hash = self.password_hasher.hash_password(login_data.password, use_argon2=True)
                creator.password_hash = new_hash
                creator.password_changed_at = datetime.utcnow()
                
                await self._log_audit_event(
                    db, creator.id, "password_rehashed", "security",
                    f"Password rehashed to stronger algorithm: {creator.email}",
                    {"email": creator.email},
                    client_ip, user_agent, "info"
                )
            
            # 7. Generate JWT tokens
            token_expire_hours = 24 * 7 if login_data.remember_me else 24  # 7 days vs 1 day
            tokens = await self._generate_token_pair(
                creator.id, db, client_ip, user_agent, token_expire_hours
            )
            
            # 8. Log successful login
            await self._log_audit_event(
                db, creator.id, "login_successful", "auth",
                f"Successful login: {creator.email}",
                {
                    "email": creator.email,
                    "remember_me": login_data.remember_me,
                    "token_expire_hours": token_expire_hours
                },
                client_ip, user_agent, "info"
            )
            
            await db.commit()
            
            # 9. Return response
            creator_response = CreatorResponse(
                id=str(creator.id),
                email=creator.email,
                full_name=creator.full_name,
                company_name=creator.company_name,
                is_active=creator.is_active,
                subscription_tier=creator.subscription_tier,
                created_at=creator.created_at,
                updated_at=creator.updated_at
            )
            
            return creator_response, tokens
            
        except HTTPException:
            raise
        except Exception as e:
            await db.rollback()
            logger.exception(f"Creator authentication failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Authentication failed due to internal error"
            )
    
    async def refresh_token(
        self,
        refresh_request: TokenRefreshRequest,
        db: AsyncSession,
        client_ip: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> TokenResponse:
        """
        Refresh JWT access token using refresh token
        
        Args:
            refresh_request: Refresh token request
            db: Database session
            client_ip: Client IP address
            user_agent: Client user agent
            
        Returns:
            New TokenResponse
            
        Raises:
            HTTPException: If refresh fails
        """
        try:
            # 1. Hash the refresh token for lookup
            token_hash = hashlib.sha256(refresh_request.refresh_token.encode()).hexdigest()
            
            # 2. Find the refresh token
            result = await db.execute(
                select(RefreshToken, Creator)
                .join(Creator)
                .where(
                    and_(
                        RefreshToken.token_hash == token_hash,
                        RefreshToken.is_active == True,
                        RefreshToken.expires_at > datetime.utcnow(),
                        RefreshToken.used_at.is_(None),
                        RefreshToken.revoked_at.is_(None)
                    )
                )
            )
            token_creator = result.first()
            
            if not token_creator:
                await self._log_audit_event(
                    db, None, "token_refresh_failed", "security",
                    "Invalid or expired refresh token used",
                    {"token_hash": token_hash[:16] + "..."},
                    client_ip, user_agent, "warning"
                )
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid or expired refresh token"
                )
            
            refresh_token, creator = token_creator
            
            # 3. Check for token reuse (security breach detection)
            if refresh_token.used_at:
                # Token reuse detected - revoke entire token family
                await self._revoke_token_family(refresh_token.family_id, db)
                
                await self._log_audit_event(
                    db, creator.id, "token_theft_detected", "security",
                    f"Refresh token reuse detected - revoking token family: {creator.email}",
                    {
                        "email": creator.email,
                        "family_id": str(refresh_token.family_id),
                        "original_use": refresh_token.used_at.isoformat()
                    },
                    client_ip, user_agent, "critical"
                )
                
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token theft detected - all sessions revoked"
                )
            
            # 4. Mark current token as used
            refresh_token.used_at = datetime.utcnow()
            refresh_token.is_active = False
            
            # 5. Generate new token pair with same family
            tokens = await self._generate_token_pair(
                creator.id, db, client_ip, user_agent,
                family_id=refresh_token.family_id
            )
            
            # 6. Log successful refresh
            await self._log_audit_event(
                db, creator.id, "token_refreshed", "auth",
                f"Access token refreshed: {creator.email}",
                {"email": creator.email, "family_id": str(refresh_token.family_id)},
                client_ip, user_agent, "info"
            )
            
            await db.commit()
            return tokens
            
        except HTTPException:
            await db.rollback()
            raise
        except Exception as e:
            await db.rollback()
            logger.exception(f"Token refresh failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Token refresh failed due to internal error"
            )
    
    async def logout_creator(
        self,
        creator_id: uuid.UUID,
        refresh_token: Optional[str],
        db: AsyncSession,
        client_ip: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> bool:
        """
        Logout creator and invalidate tokens
        
        Args:
            creator_id: Creator ID from JWT
            refresh_token: Optional refresh token to revoke
            db: Database session
            client_ip: Client IP address
            user_agent: Client user agent
            
        Returns:
            True if logout successful
        """
        try:
            # 1. Revoke refresh token if provided
            if refresh_token:
                token_hash = hashlib.sha256(refresh_token.encode()).hexdigest()
                
                result = await db.execute(
                    select(RefreshToken)
                    .where(
                        and_(
                            RefreshToken.token_hash == token_hash,
                            RefreshToken.creator_id == creator_id,
                            RefreshToken.is_active == True
                        )
                    )
                )
                refresh_token_obj = result.scalar_one_or_none()
                
                if refresh_token_obj:
                    refresh_token_obj.revoked_at = datetime.utcnow()
                    refresh_token_obj.is_active = False
            
            # 2. Log logout event
            await self._log_audit_event(
                db, creator_id, "logout", "auth",
                f"Creator logged out: {creator_id}",
                {"creator_id": str(creator_id)},
                client_ip, user_agent, "info"
            )
            
            await db.commit()
            return True
            
        except Exception as e:
            await db.rollback()
            logger.exception(f"Logout failed: {e}")
            return False
    
    async def validate_password_strength_endpoint(
        self,
        password: str,
        personal_info: Optional[Dict[str, str]] = None
    ) -> PasswordStrengthResponse:
        """
        Validate password strength for API endpoint
        
        Args:
            password: Password to validate
            personal_info: Optional personal information
            
        Returns:
            PasswordStrengthResponse
        """
        result = await validate_password_strength(password, personal_info)
        
        return PasswordStrengthResponse(
            strength=result.strength.value,
            score=result.score,
            is_valid=result.is_valid,
            violations=result.violations,
            suggestions=result.suggestions,
            estimated_crack_time=result.estimated_crack_time
        )
    
    async def _generate_token_pair(
        self,
        creator_id: uuid.UUID,
        db: AsyncSession,
        client_ip: Optional[str] = None,
        user_agent: Optional[str] = None,
        token_expire_hours: int = 24,
        family_id: Optional[uuid.UUID] = None
    ) -> TokenResponse:
        """Generate JWT access token and refresh token pair"""
        
        # Generate JTI for access token
        jti = str(uuid.uuid4())
        
        # Access token payload
        access_token_payload = {
            "sub": str(creator_id),
            "jti": jti,
            "type": "access",
            "iat": datetime.utcnow(),
            "exp": datetime.utcnow() + timedelta(hours=token_expire_hours),
            "iss": "mvp-coaching-ai-platform",
            "aud": "api"
        }
        
        # Generate access token
        try:
            access_token = jwt.encode(
                access_token_payload,
                self.jwt_secret_key,
                algorithm=self.jwt_algorithm
            )
        except JWTError as e:
            logger.error(f"JWT encoding failed for creator {creator_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Token generation failed"
            )
        
        # Generate refresh token
        refresh_token_value = secrets.token_urlsafe(32)
        refresh_token_hash = hashlib.sha256(refresh_token_value.encode()).hexdigest()
        
        # Create refresh token record
        refresh_token = RefreshToken(
            token_hash=refresh_token_hash,
            creator_id=creator_id,
            family_id=family_id or uuid.uuid4(),
            expires_at=datetime.utcnow() + timedelta(days=self.jwt_refresh_token_expire_days),
            client_ip=client_ip,
            user_agent=user_agent
        )
        
        db.add(refresh_token)
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token_value,
            token_type="bearer",
            expires_in=token_expire_hours * 3600  # Convert to seconds
        )
    
    async def _revoke_token_family(self, family_id: uuid.UUID, db: AsyncSession):
        """Revoke all tokens in a family (security breach response)"""
        await db.execute(
            update(RefreshToken)
            .where(RefreshToken.family_id == family_id)
            .values(
                revoked_at=datetime.utcnow(),
                is_active=False
            )
        )
    
    async def _log_audit_event(
        self,
        db: AsyncSession,
        creator_id: Optional[uuid.UUID],
        event_type: str,
        event_category: str,
        description: str,
        metadata: Dict[str, Any],
        client_ip: Optional[str] = None,
        user_agent: Optional[str] = None,
        severity: str = "info"
    ):
        """Log audit event for security tracking"""
        audit_log = AuditLog(
            creator_id=creator_id,
            event_type=event_type,
            event_category=event_category,
            description=description,
            event_metadata=metadata,
            client_ip=client_ip,
            user_agent=user_agent,
            severity=severity
        )
        
        db.add(audit_log)

    async def request_password_reset(
        self,
        reset_request: PasswordResetRequest,
        db: AsyncSession,
        client_ip: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Optional[str]:
        """
        Request password reset for a creator
        
        Args:
            reset_request: Password reset request data
            db: Database session
            client_ip: Client IP address
            user_agent: Client user agent
            
        Returns:
            Reset token if creator exists, None otherwise (for security)
        """
        try:
            # 1. Find creator by email (don't reveal if email exists for security)
            result = await db.execute(
                select(Creator).where(Creator.email == reset_request.email.lower())
            )
            creator = result.scalar_one_or_none()
            
            # 2. Always proceed with success for security (prevent email enumeration)
            if creator:
                # 3. Generate secure reset token
                reset_token = secrets.token_urlsafe(32)
                token_hash = hashlib.sha256(reset_token.encode()).hexdigest()
                
                # 4. Calculate expiration time
                expires_at = datetime.utcnow() + timedelta(
                    minutes=self.password_reset_token_expire_minutes
                )
                
                # 5. Create PasswordResetToken record
                reset_token_record = PasswordResetToken(
                    token_hash=token_hash,
                    creator_id=creator.id,
                    expires_at=expires_at,
                    client_ip=client_ip,
                    user_agent=user_agent
                )
                
                db.add(reset_token_record)
                
                # 6. Log audit event
                await self._log_audit_event(
                    db, creator.id, "password_reset_requested", "auth",
                    f"Password reset requested for: {creator.email}",
                    {
                        "email": creator.email,
                        "token_id": str(reset_token_record.id)[:8] + "...",
                        "client_ip": client_ip
                    },
                    client_ip, user_agent, "info"
                )
                
                # 7. Commit transaction
                await db.commit()
                
                # 8. Return token for email service
                return reset_token
            else:
                # Log failed attempt for non-existent email (for security monitoring)
                await self._log_audit_event(
                    db, None, "password_reset_requested", "auth",
                    f"Password reset requested for non-existent email: {reset_request.email}",
                    {
                        "email": reset_request.email,
                        "reason": "email_not_found",
                        "client_ip": client_ip
                    },
                    client_ip, user_agent, "warning"
                )
                
                await db.commit()
                return None
                
        except Exception as e:
            await db.rollback()
            logger.exception(f"Password reset request failed: {e}")
            # Always return None for security
            return None

    async def confirm_password_reset(
        self,
        reset_confirm: PasswordResetConfirm,
        db: AsyncSession,
        client_ip: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> bool:
        """
        Confirm password reset with new password
        
        Args:
            reset_confirm: Password reset confirmation data
            db: Database session
            client_ip: Client IP address
            user_agent: Client user agent
            
        Returns:
            True if successful, raises HTTPException for errors
        """
        try:
            # 1. Hash the provided token and look up PasswordResetToken
            token_hash = hashlib.sha256(reset_confirm.token.encode()).hexdigest()
            
            result = await db.execute(
                select(PasswordResetToken, Creator)
                .join(Creator)
                .where(PasswordResetToken.token_hash == token_hash)
            )
            token_creator = result.first()
            
            if not token_creator:
                await self._log_audit_event(
                    db, None, "password_reset_failed", "auth",
                    "Invalid password reset token used",
                    {
                        "token_hash": token_hash[:16] + "...",
                        "reason": "token_not_found"
                    },
                    client_ip, user_agent, "warning"
                )
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid or expired password reset token"
                )
            
            reset_token, creator = token_creator
            
            # 2. Validate token is active, not used, and not expired
            if not reset_token.is_active:
                await self._log_audit_event(
                    db, creator.id, "password_reset_failed", "auth",
                    f"Password reset with inactive token: {creator.email}",
                    {
                        "email": creator.email,
                        "token_id": str(reset_token.id)[:8] + "...",
                        "reason": "token_inactive"
                    },
                    client_ip, user_agent, "warning"
                )
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Password reset token has been used or is invalid"
                )
            
            if reset_token.used_at:
                await self._log_audit_event(
                    db, creator.id, "password_reset_failed", "auth",
                    f"Password reset with used token: {creator.email}",
                    {
                        "email": creator.email,
                        "token_id": str(reset_token.id)[:8] + "...",
                        "reason": "token_already_used"
                    },
                    client_ip, user_agent, "warning"
                )
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Password reset token has already been used"
                )
            
            if reset_token.expires_at < datetime.utcnow():
                await self._log_audit_event(
                    db, creator.id, "password_reset_failed", "auth",
                    f"Password reset with expired token: {creator.email}",
                    {
                        "email": creator.email,
                        "token_id": str(reset_token.id)[:8] + "...",
                        "reason": "token_expired"
                    },
                    client_ip, user_agent, "warning"
                )
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Password reset token has expired"
                )
            
            # 3. Validate new password strength using existing validate_password_strength
            personal_info = {
                "email": creator.email,
                "name": creator.full_name,
                "company": creator.company_name or ""
            }
            
            password_result = await validate_password_strength(
                reset_confirm.new_password, personal_info
            )
            
            if not password_result.is_valid:
                await self._log_audit_event(
                    db, creator.id, "password_reset_failed", "auth",
                    f"Password reset failed due to weak password: {creator.email}",
                    {
                        "email": creator.email,
                        "violations": password_result.violations,
                        "token_id": str(reset_token.id)[:8] + "..."
                    },
                    client_ip, user_agent, "warning"
                )
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "message": "Password does not meet security requirements",
                        "violations": password_result.violations,
                        "suggestions": password_result.suggestions
                    }
                )
            
            # 4. Update creator's password using self.password_hasher.hash_password
            new_password_hash = self.password_hasher.hash_password(
                reset_confirm.new_password, use_argon2=True
            )
            creator.password_hash = new_password_hash
            
            # 5. Mark reset token as used (used_at = datetime.utcnow(), is_active = False)
            reset_token.used_at = datetime.utcnow()
            reset_token.is_active = False
            
            # 6. Revoke all refresh tokens for the creator
            await self._revoke_all_refresh_tokens(creator.id, db)
            
            # 7. Log password change audit event
            await self._log_audit_event(
                db, creator.id, "password_reset_completed", "auth",
                f"Password reset completed: {creator.email}",
                {
                    "email": creator.email,
                    "token_id": str(reset_token.id)[:8] + "...",
                    "password_strength": password_result.strength.value
                },
                client_ip, user_agent, "info"
            )
            
            # 8. Update password_changed_at timestamp
            creator.password_changed_at = datetime.utcnow()
            
            await db.commit()
            return True
            
        except HTTPException:
            await db.rollback()
            raise
        except Exception as e:
            await db.rollback()
            logger.exception(f"Password reset confirmation failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Password reset failed due to internal error"
            )

    async def _revoke_all_refresh_tokens(self, creator_id: uuid.UUID, db: AsyncSession):
        """
        Revoke all refresh tokens for a creator
        
        Args:
            creator_id: Creator ID
            db: Database session
        """
        await db.execute(
            update(RefreshToken)
            .where(
                and_(
                    RefreshToken.creator_id == creator_id,
                    RefreshToken.is_active == True,
                    RefreshToken.revoked_at.is_(None)
                )
            )
            .values(
                revoked_at=datetime.utcnow(),
                is_active=False
            )
        )

    async def _invalidate_creator_sessions(self, creator_id: uuid.UUID):
        """
        Invalidate all sessions for a creator
        
        Args:
            creator_id: Creator ID
            
        Raises:
            Exception: If session invalidation fails
        """
        try:
            from shared.cache.session_store import get_session_store
            get_session_store()
            
            # Get all sessions for the creator and end them
            # Note: This is a simplified implementation
            # In a production environment, you might want to track sessions differently
            logger.info(f"Invalidating sessions for creator {creator_id}")
            
        except Exception as e:
            logger.error(f"Error invalidating creator sessions for {creator_id}: {e}")
            # Re-raise the exception so callers can react to the failure
            raise