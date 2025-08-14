"""
Shared Utilities Module for the MVP Coaching AI Platform.

This package provides shared models, configurations, utilities, and other
core components used across different services.
"""
from .config.env_constants import get_env_value
from .config.settings import BaseConfig

# Expose key models for easier access
from .models.auth import TokenResponse, CreatorCreate, CreatorResponse
from .models.base import BaseEntity
from .models.database import Base, Creator

# Expose key security functions (if they exist)
try:
    from .security.jwt_manager import create_access_token, verify_token
except ImportError:
    # Security functions might not be implemented yet
    create_access_token = None
    verify_token = None

__version__ = "0.1.0"

__all__ = [
    # config
    "get_env_value",
    "BaseConfig",

    # models
    "TokenResponse",
    "CreatorCreate", 
    "CreatorResponse",
    "BaseEntity",
    "Base",
    "Creator",

    # security
    "create_access_token",
    "verify_token",
]
