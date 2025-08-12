---
inclusion: fileMatch
fileMatchPattern: ['services/auth-service/**/*', 'shared/security/**/*', 'shared/models/auth.py', 'tests/test_auth_service.py', 'tests/test_password_security.py']
---

# Authentication Service Implementation Guide

## Architecture Overview

The Authentication Service (`services/auth-service/`) provides secure JWT-based authentication for creators with comprehensive security features including multi-tenant isolation, password security, and rate limiting.

**Base URL**: `/api/v1/auth/`
**Service Port**: 8001

## Required Implementation Patterns

### Security Components (MANDATORY)
Always use existing shared security components:

```python
# Use shared security components
from shared.security.password_security import PasswordHasher, PasswordValidator
from shared.models.auth import CreatorCreate, CreatorResponse, TokenResponse

# Required pattern for password operations
hasher = PasswordHasher()
validator = PasswordValidator()

# Validate before hashing
validation = await validator.validate_password(password, user_info)
if not validation.is_valid:
    raise HTTPException(400, detail=validation.to_dict())

# Hash with auto-upgrade capability
hashed = await hasher.hash_password(password)
```

### Multi-Tenant Database Access (MANDATORY)
All database operations must set tenant context for Row Level Security:

```python
# Required dependency pattern
async def get_tenant_db(
    creator_id: str = Depends(get_current_creator_id),
    db: AsyncSession = Depends(get_db)
) -> AsyncSession:
    await set_tenant_context(creator_id, db)
    return db

# Set tenant context for RLS
async def set_tenant_context(creator_id: str, db: AsyncSession):
    await db.execute(
        text("SELECT set_config('app.current_creator_id', :creator_id, true)"),
        {"creator_id": creator_id}
    )
```

### FastAPI Route Patterns
Follow existing patterns in `services/auth-service/app/routes/auth.py`:

```python
@router.post("/register", response_model=CreatorResponse, status_code=201)
async def register_creator(
    creator_data: CreatorCreate,
    db: AsyncSession = Depends(get_db),
    auth_service: AuthService = Depends(get_auth_service)
):
    # Use service layer for business logic
    result = await auth_service.register_creator(creator_data, db)
    return result
```

## Core Security Requirements

### Password Security (Implemented)
- **Argon2id** primary hashing with bcrypt fallback
- **Auto-upgrade** weaker hashes on login
- **Strength validation** with HaveIBeenPwned integration
- **Personal info detection** prevents using email/name in password

### Authentication Security
- **JWT tokens**: RS256 for production, access tokens expire in 1 hour
- **Refresh token rotation** with family tracking for theft detection
- **Account lockout**: 5 failed attempts = 30-minute lockout
- **Rate limiting**: 5-10 requests/minute per endpoint
- **Email enumeration protection**: Consistent responses

### Multi-Tenant Isolation
- **Row Level Security** enforced at database level
- **Tenant context** set for all authenticated operations
- **Session isolation** prevents cross-tenant data access

## API Endpoints & Responses

### Core Authentication Endpoints
- `POST /register` - Creator registration with validation
- `POST /login` - Authentication with lockout protection
- `POST /refresh` - Token refresh with rotation
- `GET /me` - Current creator profile
- `POST /logout` - Token invalidation

### Password Management
- `POST /password/validate` - Password strength validation
- `POST /password/reset/request` - Reset token generation (15min expiry)
- `POST /password/reset/confirm` - Password reset with token

### Standard Response Format
```python
# Success responses use Pydantic models
CreatorResponse(
    id=uuid,
    email=str,
    full_name=str,
    company_name=str,
    is_active=bool,
    subscription_tier=str,
    created_at=datetime,
    updated_at=datetime
)

# Error responses follow FastAPI HTTPException pattern
raise HTTPException(
    status_code=400,
    detail={"message": "Error description", "violations": [...]}
)
```

## Database Models & Tables

### Core Tables (in `shared/models/database.py`)
- **creators**: Main user table with security fields
- **refresh_tokens**: JWT refresh tokens with family tracking
- **password_reset_tokens**: Short-lived reset tokens
- **jwt_blacklist**: Blacklisted tokens (JTI tracking)
- **audit_logs**: Security event logging

### Required Indexes & Constraints
- Email uniqueness with case-insensitive collation
- Composite indexes for tenant isolation
- TTL indexes for token expiration

## Environment Configuration

### Required Variables
```bash
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

## Testing Requirements

### Security Test Coverage
- Password hashing and verification
- Password strength validation with edge cases
- Authentication flows with error scenarios
- Multi-tenant isolation verification
- Rate limiting and account lockout behavior
- Token rotation and blacklisting

### Integration Testing
Use `scripts/test-auth-service.py` for endpoint validation and `tests/test_auth_service.py` for comprehensive security testing.

## Implementation Guidelines

### When Modifying Auth Service
1. **Use existing security components** - Never recreate password hashing or validation
2. **Follow async patterns** - All I/O operations must be async
3. **Implement tenant isolation** - Set tenant context for all database operations
4. **Add audit logging** - Log all security events with proper context
5. **Validate all inputs** - Use Pydantic models for request/response validation
6. **Test security features** - Include tests for rate limiting, lockout, and validation

### Code Quality Requirements
- **Type hints** on all functions
- **Pydantic models** for all request/response data
- **Proper error handling** with structured responses
- **Async/await** for all database and external API calls
- **Multi-tenant context** set before database operations