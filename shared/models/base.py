"""Base models and common validators"""

from pydantic import BaseModel, Field, validator
from datetime import datetime
from typing import Optional
import uuid


class BaseEntity(BaseModel):
    """Base model for all entities with common fields"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class TenantAwareEntity(BaseEntity):
    """Base model for tenant-aware entities"""
    creator_id: str = Field(..., description="Creator/tenant ID for multi-tenancy")
    
    @validator('creator_id')
    def validate_creator_id(cls, v):
        if not v or not v.strip():
            raise ValueError('creator_id cannot be empty')
        return v.strip()