"""Authentication and authorization models"""

from pydantic import BaseModel, EmailStr, Field, validator, root_validator
from datetime import datetime
from typing import Optional, Dict, Any, List
from .base import BaseEntity


class CreatorCreate(BaseModel):
    """Model for creator registration"""
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128, description="Password must be at least 8 characters")
    full_name: str = Field(..., min_length=2, max_length=100)
    company_name: Optional[str] = Field(None, max_length=100)
    
    @validator('password')
    def validate_password_strength(cls, v, values):
        """Basic password validation - detailed validation happens in service layer"""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if len(v) > 128:
            raise ValueError('Password must not exceed 128 characters')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        if not any(c in '!@#$%^&*(),.?":{}|<>' for c in v):
            raise ValueError('Password must contain at least one special character')
        return v
    
    @validator('full_name')
    def validate_full_name(cls, v):
        """Validate full name format"""
        if not v.strip():
            raise ValueError('Full name cannot be empty')
        if len(v.strip()) < 2:
            raise ValueError('Full name must be at least 2 characters')
        # Basic sanitization - remove excessive whitespace
        return ' '.join(v.split())
    
    @validator('company_name')
    def validate_company_name(cls, v):
        """Validate company name if provided"""
        if v is not None:
            if not v.strip():
                return None  # Convert empty string to None
            return ' '.join(v.split())  # Sanitize whitespace
        return v


class CreatorResponse(BaseEntity):
    """Model for creator data in responses"""
    email: str
    full_name: str
    company_name: Optional[str]
    is_active: bool = True
    subscription_tier: str = "free"
    
    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    """JWT token response model"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = Field(..., description="Token expiration time in seconds")


class LoginRequest(BaseModel):
    """Model for login requests"""
    email: EmailStr
    password: str = Field(..., min_length=1, description="User password")
    remember_me: bool = Field(default=False, description="Extended session duration")


class PasswordResetRequest(BaseModel):
    """Model for password reset requests"""
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    """Model for password reset confirmation"""
    token: str = Field(..., description="Password reset token")
    new_password: str = Field(..., min_length=8, max_length=128, description="New password")
    
    @validator('new_password')
    def validate_new_password(cls, v):
        """Basic password validation for reset"""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if len(v) > 128:
            raise ValueError('Password must not exceed 128 characters')
        return v


class TokenRefreshRequest(BaseModel):
    """Model for token refresh requests"""
    refresh_token: str = Field(..., description="Valid refresh token")


class UserSession(BaseModel):
    """Model for end-user sessions (anonymous users interacting with widgets)"""
    session_id: str = Field(..., description="Unique session identifier")
    creator_id: str = Field(..., description="Creator this session belongs to")
    channel: str = Field(default="web_widget", description="Channel type (web_widget, whatsapp, etc)")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_activity: datetime = Field(default_factory=datetime.utcnow)
    session_metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional session metadata")
    is_active: bool = Field(default=True, description="Session active status")
    expires_at: Optional[datetime] = Field(None, description="Session expiration time")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class PasswordStrengthResponse(BaseModel):
    """Response model for password strength validation"""
    strength: str = Field(..., description="Password strength level")
    score: int = Field(..., ge=0, le=100, description="Password strength score (0-100)")
    is_valid: bool = Field(..., description="Whether password meets policy requirements")
    violations: List[str] = Field(default_factory=list, description="Policy violations")
    suggestions: List[str] = Field(default_factory=list, description="Improvement suggestions")
    estimated_crack_time: str = Field(..., description="Estimated time to crack password")