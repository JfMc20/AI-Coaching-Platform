"""Security utilities for the MVP Coaching AI Platform"""

from .password_security import (
    PasswordHasher,
    PasswordValidator,
    PasswordStrengthResult,
    PasswordPolicy,
    hash_password,
    verify_password,
    validate_password_strength,
    check_password_policy
)

from .jwt_manager import (
    JWTManager,
    get_jwt_manager
)

from .rbac import (
    Role,
    Permission,
    RBACManager
)

from .rate_limiter import (
    RateLimiter,
    RateLimitType,
    RateLimitError,
    get_rate_limiter,
    check_rate_limit_dependency
)

from .gdpr_compliance import (
    GDPRComplianceManager,
    DataDeletionType
)

__all__ = [
    # Password Security
    "PasswordHasher",
    "PasswordValidator", 
    "PasswordStrengthResult",
    "PasswordPolicy",
    "hash_password",
    "verify_password",
    "validate_password_strength",
    "check_password_policy",
    
    # JWT Management
    "JWTManager",
    "get_jwt_manager",
    
    # RBAC
    "Role",
    "Permission", 
    "RBACManager",
    
    # Rate Limiting
    "RateLimiter",
    "RateLimitType",
    "RateLimitError",
    "get_rate_limiter",
    "check_rate_limit_dependency",
    
    # GDPR Compliance
    "GDPRComplianceManager",
    "DataDeletionType"
]