"""Authentication and authorization models"""

from pydantic import BaseModel, EmailStr, Field, validator
from datetime import datetime
from typing import Optional, Dict, Any
from .base import BaseEntity


class CreatorCreate(BaseModel):
    """Model for creator registration"""
    email: EmailStr
    password: str = Field(..., min_length=8, description="Password must be at least 8 characters")
    full_name: str = Field(..., min_length=2, max_length=100)
    company_name: Optional[str] = Field(None, max_length=100)
    
    @validator('password')
    def validate_password_strength(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
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


class UserSession(BaseModel):
    """Model for end-user sessions (anonymous users interacting with widgets)"""
    session_id: str = Field(..., description="Unique session identifier")
    creator_id: str = Field(..., description="Creator this session belongs to")
    channel: str = Field(default="web_widget", description="Channel type (web_widget, whatsapp, etc)")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_activity: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional session metadata")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }