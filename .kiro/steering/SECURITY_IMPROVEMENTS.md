---
inclusion: always
---

# Security & Reliability Implementation Patterns

## Database Integrity Requirements

### Foreign Key Constraints (MANDATORY)
All database models MUST implement proper foreign key relationships:

```python
# Required pattern for token tables
class JWTBlacklist(Base):
    creator_id: Mapped[UUID] = mapped_column(ForeignKey("creators.id", ondelete="CASCADE"))

class AuditLog(Base):
    creator_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("creators.id", ondelete="SET NULL"))

class RefreshToken(Base):
    family_id: Mapped[UUID] = mapped_column(default=uuid.uuid4)
```

### Temporal Validation Constraints
All token tables MUST include temporal validation:

```python
# Required CheckConstraint for all token tables
__table_args__ = (
    CheckConstraint('expires_at > created_at', name='valid_expiration'),
)
```

## Concurrency & Race Condition Handling

### Database Transaction Pattern (MANDATORY)
Use flush-commit pattern for race condition handling:

```python
try:
    await db.flush()  # Get ID without committing
    # ... business logic
    await db.commit()
except IntegrityError as e:
    await db.rollback()
    logger.warning(f"Integrity error: {e}")
    raise HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail="Resource already exists"
    )
```

### Thread-Safe Rate Limiting (MANDATORY)
All rate limiting implementations MUST use asyncio.Lock:

```python
class RateLimitChecker:
    def __init__(self):
        self._attempts: Dict[str, list] = {}
        self._lock = asyncio.Lock()  # REQUIRED for thread safety
    
    async def check_rate_limit(self, identifier: str):
        async with self._lock:  # REQUIRED synchronization
            # ... rate limiting logic
```

## Resource Management Patterns

### Lazy Initialization Pattern (MANDATORY)
Database managers and heavy resources MUST use lazy initialization:

```python
# Global instance (initialized lazily)
db_manager: Optional[DatabaseManager] = None

def get_db_manager() -> DatabaseManager:
    global db_manager
    if db_manager is None:
        db_manager = DatabaseManager()
    return db_manager

async def close_db():
    global db_manager
    if db_manager is not None:
        await db_manager.close()
        db_manager = None
```

## Database Migration Standards

### URL Normalization (MANDATORY)
All database URL handling MUST normalize legacy formats:

```python
def get_database_url(async_url: bool = True):
    database_url = os.getenv("DATABASE_URL")
    
    # Normalize legacy postgres:// prefix
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)
    
    # Convert to async URL if needed
    if async_url and database_url.startswith("postgresql://"):
        database_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    
    return database_url
```

### Alembic Configuration (MANDATORY)
Migration context MUST use correct configuration:

```python
context.configure(
    connection=connection,
    target_metadata=target_metadata,
    compare_type=True,
    compare_server_default=True,
    include_schemas=True,
    render_as_batch=True,  # NOT render_item=True
)
```

## Error Handling & Audit Logging

### Audit Event Logging (MANDATORY)
All security-related events MUST be logged:

```python
await self._log_audit_event(
    db, creator_id, "event_type", "service_name",
    "Event description",
    {"additional": "context"},
    client_ip, user_agent, "severity_level"
)
```

### HTTP Status Code Standards
- `409 Conflict`: For integrity constraint violations
- `429 Too Many Requests`: For rate limit exceeded
- `401 Unauthorized`: For authentication failures
- `403 Forbidden`: For authorization failures

## Testing Requirements

### Security Test Patterns
All security-critical code MUST include explicit tests:

```python
# Test unknown hash format handling
unknown_format_hash = "unknown_format_hash"
needs_rehash = hasher.needs_rehash(unknown_format_hash)
assert needs_rehash is True, f"Expected unknown format to need rehashing"

# Test race condition handling
async def test_concurrent_registration():
    # Simulate concurrent requests with same email
    # Verify only one succeeds, others get 409 Conflict
```

## Production Readiness Checklist

When implementing security features, verify:
- [ ] Foreign key constraints with appropriate cascade policies
- [ ] Temporal validation constraints on all token tables
- [ ] Thread-safe rate limiting with asyncio.Lock
- [ ] Lazy initialization for heavy resources
- [ ] Proper IntegrityError handling with rollback
- [ ] Audit logging for all security events
- [ ] Database URL normalization for legacy formats
- [ ] Explicit tests for edge cases and race conditions

## Anti-Patterns to Avoid

- Direct database access without foreign key constraints
- Rate limiting without thread synchronization
- Premature resource initialization during imports
- Generic exception handling without specific error types
- Missing audit trails for security events
- Hardcoded database URLs without normalization
- Ambiguous test assertions without descriptive messages