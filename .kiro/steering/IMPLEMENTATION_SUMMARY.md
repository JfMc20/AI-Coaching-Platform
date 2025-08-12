---
inclusion: fileMatch
fileMatchPattern: ['**/auth*', '**/security*', '**/password*', '**/models/auth.py', '**/models/database.py']
---

# Authentication System Implementation Guide

## Core Security Patterns (MANDATORY)

### Password Security Implementation
**Use existing `shared/security/password_security.py` components:**
- **PasswordHasher**: Argon2id primary, bcrypt fallback with auto-upgrade
- **PasswordValidator**: Comprehensive validation with HaveIBeenPwned integration
- **Configuration**: All parameters via environment variables

```python
# Required pattern for password operations
from shared.security.password_security import PasswordHasher, PasswordValidator

hasher = PasswordHasher()
validator = PasswordValidator()

# Hash passwords
hashed = await hasher.hash_password(password)

# Validate strength before hashing
validation = await validator.validate_password(password, user_info)
if not validation.is_valid:
    raise HTTPException(400, detail=validation.suggestions)
```

### Authentication Endpoints (Implemented)
**Follow existing patterns in `services/auth-service/app/routes/auth.py`:**
- All endpoints use Pydantic validation and proper HTTP status codes
- Rate limiting: 5-10 requests/min per endpoint
- Account lockout: 5 failed attempts = 30min lockout
- Email enumeration protection implemented

## Database Architecture (SQLAlchemy Models)

### Core Tables in `shared/models/database.py`
- **creators**: Main user table with security fields
- **refresh_tokens**: JWT refresh tokens with family tracking
- **user_sessions**: Anonymous end-user sessions
- **password_reset_tokens**: Short-lived reset tokens (15min)
- **jwt_blacklist**: Blacklisted JWT tokens (JTI tracking)
- **audit_logs**: Security event logging

### Multi-Tenant Security (MANDATORY)
**Always implement Row Level Security for tenant isolation:**

```python
# Required pattern for tenant context
async def set_tenant_context(creator_id: str, db: AsyncSession):
    await db.execute(
        text("SELECT set_config('app.current_creator_id', :creator_id, true)"),
        {"creator_id": creator_id}
    )

# Usage in dependencies
async def get_tenant_db(
    creator_id: str = Depends(get_current_creator_id),
    db: AsyncSession = Depends(get_db)
) -> AsyncSession:
    await set_tenant_context(creator_id, db)
    return db
```

## Service Architecture Patterns

### AuthService Implementation
**Follow `services/auth-service/app/services/auth_service.py` patterns:**
- Async operations for all I/O
- Proper error handling with audit logging
- Token family tracking for refresh token rotation
- Comprehensive security event logging

### FastAPI Dependencies
**Use existing auth middleware in `services/auth-service/app/dependencies/auth.py`:**
- JWT token validation with blacklist checking
- Rate limiting with account lockout
- Tenant context setting for RLS

## Required Environment Variables

```bash
# Database
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/db

# JWT Configuration
JWT_SECRET_KEY=your-secret-key
JWT_ALGORITHM=RS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=60
JWT_REFRESH_TOKEN_EXPIRE_DAYS=30

# Security Settings
MAX_FAILED_LOGIN_ATTEMPTS=5
ACCOUNT_LOCKOUT_DURATION_MINUTES=30
PASSWORD_RESET_TOKEN_EXPIRE_MINUTES=15

# Password Hashing (OWASP Recommended)
ARGON2_MEMORY_COST=65536
ARGON2_TIME_COST=3
ARGON2_PARALLELISM=4
BCRYPT_ROUNDS=12
```

## Testing Patterns

### Security Testing Requirements
**Follow patterns in `tests/test_password_security.py` and `tests/test_auth_service.py`:**
- Test password hashing and verification
- Test password strength validation
- Test authentication flows with error scenarios
- Test multi-tenant isolation
- Test rate limiting and account lockout

### Validation Script
**Use `scripts/test-auth-service.py` for integration testing:**
- Validates all endpoints
- Tests security features
- Verifies database connectivity

## File Structure Convention

```
services/auth-service/
├── app/
│   ├── main.py                 # FastAPI app
│   ├── database.py             # DB configuration
│   ├── services/auth_service.py # Business logic
│   ├── dependencies/auth.py     # Auth middleware
│   └── routes/auth.py          # API endpoints

shared/
├── models/
│   ├── auth.py                 # Pydantic models
│   └── database.py             # SQLAlchemy models
├── security/
│   ├── password_security.py    # Password system
│   └── common_passwords.txt    # Common passwords list
└── validators/common.py        # Shared validators
```

## Implementation Guidelines

### When Working with Authentication Code
1. **Always use existing security components** - Don't recreate password hashing or validation
2. **Follow multi-tenant patterns** - Set tenant context for all database operations
3. **Implement proper error handling** - Use audit logging for security events
4. **Use async patterns** - All I/O operations must be async
5. **Validate inputs** - Use Pydantic models for all request/response data
6. **Test security features** - Include tests for rate limiting, lockout, and validation

### Security Requirements
- **Password validation** before hashing (strength, common passwords, personal info)
- **Rate limiting** on all authentication endpoints
- **Audit logging** for all security events
- **Token rotation** for refresh tokens with family tracking
- **Multi-tenant isolation** with Row Level Security
- **Proper error responses** that don't leak information

### Database Migration Pattern
**Use Alembic with existing configuration in `alembic/`:**
- Follow `alembic/versions/001_initial_auth_tables.py` patterns
- Include RLS policies in migrations
- Add proper indexes and constraints
- Test migrations with existing data

This authentication system is production-ready with comprehensive security features implemented and tested.