# Development Patterns & Best Practices

## Multi-Tenant Architecture (CRITICAL)

### Required Pattern for Database Operations
```python
# ✅ ALWAYS use this pattern for database operations
async def get_tenant_session(
    creator_id: str = Depends(get_current_creator_id),
    session: AsyncSession = Depends(get_db_session)
) -> AsyncSession:
    await session.execute(
        text("SET app.current_creator_id = :creator_id"), 
        {"creator_id": creator_id}
    )
    return session

# ✅ All models MUST inherit from BaseTenantModel
class NewFeature(BaseTenantModel):
    creator_id: UUID  # REQUIRED for RLS
    name: str
    # RLS policies automatically filter by creator_id
```

## Async Patterns (MANDATORY)

### All I/O Operations
```python
# ✅ All I/O operations use async/await
async def process_document(file: UploadFile, creator_id: str) -> Result:
    # Database operations
    async with get_db_session() as session:
        result = await session.execute(select(Document))
    
    # Redis operations  
    async with get_redis_client() as redis:
        await redis.set(f"cache:{creator_id}", data)
    
    # External API calls
    async with httpx.AsyncClient() as client:
        response = await client.post("/api/endpoint")
```

## Security Implementation (ENFORCE)

### JWT Authentication Pattern
```python
# ✅ JWT Authentication Pattern
@app.post("/api/v1/endpoint")
async def endpoint(
    request: RequestModel,
    current_user: UserContext = Depends(get_current_user),  # JWT validation
    session: AsyncSession = Depends(get_tenant_session),    # Multi-tenant
):
    # Rate limiting is automatically applied
    # Input validation via Pydantic models
    # Output sanitization via response models
```

## Configuration Management

### Environment Variables
- **Use**: `get_env_value()` from `shared.config.env_constants`
- **Service Requirements**: Auto-generated from `pyproject.toml` Poetry workspace
- **Multi-Environment**: Development, testing, production configurations centralized

### Example
```python
from shared.config.env_constants import get_env_value

# ✅ Correct way to get environment variables
database_url = get_env_value("DATABASE_URL", fallback=True)
redis_url = get_env_value("REDIS_URL", fallback=True)

# ❌ Never hardcode
# database_url = "postgresql://localhost:5432/db"
```

## Testing Strategy

### Coverage Requirements
- **Existing Code**: 85%+ coverage required
- **New Features**: 90%+ coverage required
- **Multi-tenant Tests**: Always verify creator_id isolation
- **Integration Tests**: Use testcontainers for real database/Redis testing

### Test Patterns
```python
# ✅ Multi-tenant test isolation
async def test_creator_isolation(auth_fixtures, db_session):
    creator1_data = await create_test_data(creator_id="creator1")
    creator2_data = await create_test_data(creator_id="creator2")
    
    # Set RLS context for creator1
    await db_session.execute(
        text("SET app.current_creator_id = :id"), 
        {"id": "creator1"}
    )
    
    results = await db_session.execute(select(TestModel))
    # Should only see creator1's data
    assert all(r.creator_id == "creator1" for r in results.scalars())
```

### Fixtures Usage
- **Comprehensive Fixtures**: Use fixtures from `tests/fixtures/`
- **Service Integration**: Use `service_integration_fixtures.py`
- **Auth Fixtures**: Use `auth_fixtures.py` for authentication testing

## Code Quality Standards

### Security & Multi-Tenancy (CRITICAL)
1. **Multi-tenant First**: ALWAYS implement creator_id isolation and RLS policies
2. **Authentication**: Use `get_current_user()` dependency in ALL protected endpoints
3. **Data Isolation**: NEVER allow creator data to leak across tenants
4. **Input Validation**: Use Pydantic models for ALL request/response validation
5. **Rate Limiting**: Automatically applied, but verify limits in `shared/security/rate_limiter.py`

### Code Quality Standards
1. **Type Safety**: Use comprehensive type hints and Pydantic models everywhere
2. **Async Patterns**: MANDATORY async/await for all I/O operations 
3. **Error Handling**: Use structured exceptions from `shared/exceptions/`
4. **Testing**: Achieve 90%+ coverage with multi-tenant test isolation
5. **Performance**: Meet <2s API response time targets

### Common Pitfalls to Avoid
- ❌ **Never hardcode environment variables** - Use `get_env_value()`
- ❌ **Never expose creator data across tenants** - Always test isolation
- ❌ **Never use blocking I/O** - Use async patterns only
- ❌ **Never skip authentication** - All endpoints need `get_current_user()`
- ❌ **Never commit without tests** - TDD approach preferred

## File and Service Structure Management

### Before Creating New Files
1. **ALWAYS check existing service structure** before creating new files or directories
2. **Follow established patterns** from working services (auth-service, creator-hub-service)
3. **Keep service-specific files within service boundaries** - Never create cross-service dependencies
4. **Use shared/ directory only for truly shared components** - Not for service-specific implementations
5. **Check implementation patterns** in other services before duplicating functionality
6. **Verify file locations** in the current service before creating new structures

### Task Completion Protocol
1. **Complete ONE task at a time** - Never jump to next task until current is fully working
2. **Test thoroughly** - Every endpoint, every function, every integration must be verified
3. **Docker cache awareness** - Always rebuild without cache when making structural changes
4. **End-to-end verification** - Test the complete user flow, not just individual components
5. **Documentation validation** - Ensure all created endpoints are accessible and functional
6. **Error investigation** - Understand and fix ALL errors before proceeding to next task