# Claude Code Development Guide
## Multi-Channel AI Coaching Platform

This guide provides Claude Code specific instructions for developing features in this multi-tenant AI platform.

## 🚀 Quick Start for New Features

### 1. Environment Setup
```bash
# Start development environment
make up
make health  # Ensure all services are healthy

# Install dependencies
poetry install --with dev
```

### 2. Create New Feature Workflow

#### Step 1: Planning
1. Check `.kiro/specs/mvp-foundation-platform/tasks.md` for feature requirements
2. Identify which service the feature belongs to:
   - **auth-service**: Authentication, users, RBAC
   - **ai-engine-service**: AI, RAG, document processing, embeddings
   - **creator-hub-service**: Content management, program building
   - **channel-service**: Communications, WebSocket, multi-channel

#### Step 2: Database Model (if needed)
```bash
# Navigate to appropriate service
cd services/ai-engine-service/

# Create model in shared/models/ (for shared models)
# or in service-specific location

# Create migration
poetry run alembic revision --autogenerate -m "Add new feature model"

# Review and apply migration
make db-migrate
```

#### Step 3: Create API Endpoint
Use the template at `.claude/templates/fastapi_endpoint.py`:

```python
# Copy template and modify
cp .claude/templates/fastapi_endpoint.py services/ai-engine-service/app/new_feature.py

# Key points to remember:
# 1. ALWAYS use get_current_user() for authentication
# 2. ALWAYS use get_tenant_session() for database access
# 3. ALWAYS inherit from BaseTenantModel for database models
# 4. ALWAYS validate creator_id matches current user
# 5. Use Pydantic models for request/response validation
```

#### Step 4: Write Tests
Use the template at `.claude/templates/test_template.py`:

```python
# Copy template and modify
cp .claude/templates/test_template.py tests/unit/ai-engine-service/test_new_feature.py

# Test coverage requirements:
# - Unit tests for all business logic
# - Multi-tenant isolation tests (CRITICAL)
# - Authentication/authorization tests
# - Input validation tests
# - Integration tests for complex workflows
```

#### Step 5: Test and Validate
```bash
# Run specific service tests
make test-ai-engine

# Check coverage (aim for 90%+)
make test-coverage

# Run format and lint
make format
make lint

# Test the endpoint manually
curl -X POST http://localhost:8003/api/v1/new-endpoint \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"data": "test"}'
```

## 🏗️ Architecture Patterns

### Multi-Tenant Database Access
```python
# ALWAYS use this pattern for database operations
@app.post("/api/v1/feature")
async def create_feature(
    request: FeatureRequest,
    current_user: UserContext = Depends(get_current_user),
    session: AsyncSession = Depends(get_tenant_session),  # Automatic RLS
):
    # Validate creator access
    if current_user.creator_id != request.creator_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Create with creator_id
    feature = Feature(
        name=request.name,
        creator_id=request.creator_id  # REQUIRED
    )
    
    session.add(feature)
    await session.commit()
```

### AI/ML Integration Pattern
```python
# For AI engine features
from shared.ai.ollama_manager import get_ollama_manager
from shared.ai.chromadb_manager import get_chromadb_manager

async def process_ai_request(creator_id: str, query: str):
    # Get AI managers
    ollama = get_ollama_manager()
    chromadb = get_chromadb_manager()
    
    # Generate embeddings
    embeddings = await ollama.generate_embeddings([query])
    
    # Search creator-specific collection
    collection_name = f"creator_{creator_id}_knowledge"
    results = await chromadb.query_collection(
        collection_name=collection_name,
        query_embeddings=embeddings.embeddings[0],
        n_results=5
    )
    
    return results
```

### Error Handling Pattern
```python
from shared.exceptions.base import PlatformError
from shared.exceptions.auth import AuthenticationError

try:
    # Your business logic
    result = await process_business_logic()
    return result
except AuthenticationError as e:
    raise HTTPException(status_code=401, detail=str(e))
except PlatformError as e:
    logger.error(f"Business logic error: {str(e)}")
    raise HTTPException(status_code=400, detail=str(e))
except Exception as e:
    logger.error(f"Unexpected error: {str(e)}")
    raise HTTPException(status_code=500, detail="Internal server error")
```

## 🧪 Testing Best Practices

### Multi-Tenant Test Isolation
```python
@pytest.mark.asyncio
async def test_creator_isolation(db_session, auth_fixtures):
    # Create data for two different creators
    creator1_data = await create_test_data(creator_id="creator1")
    creator2_data = await create_test_data(creator_id="creator2")
    
    # Set RLS context for creator1
    await db_session.execute(
        text("SET app.current_creator_id = :id"), 
        {"id": "creator1"}
    )
    
    # Query should only return creator1's data
    results = await db_session.execute(select(TestModel))
    assert all(r.creator_id == "creator1" for r in results.scalars())
```

### Authentication Testing
```python
@pytest.mark.asyncio
async def test_endpoint_authentication(async_client):
    # Test without token
    response = await async_client.post("/api/v1/endpoint", json={})
    assert response.status_code == 401
    
    # Test with invalid token
    response = await async_client.post(
        "/api/v1/endpoint",
        json={},
        headers={"Authorization": "Bearer invalid"}
    )
    assert response.status_code == 401
    
    # Test with valid token
    response = await async_client.post(
        "/api/v1/endpoint",
        json=valid_data,
        headers={"Authorization": f"Bearer {valid_token}"}
    )
    assert response.status_code == 200
```

## 🐛 Debugging Guide

### Common Issues and Solutions

#### 1. Multi-Tenant Data Leakage
**Symptom**: User sees data from other creators
**Solution**: 
- Verify RLS policies are applied
- Check that `get_tenant_session()` is used
- Validate creator_id in all queries

#### 2. Authentication Failures
**Symptom**: 401 Unauthorized errors
**Solution**:
- Check JWT token format and expiration
- Verify `get_current_user()` dependency is used
- Check Redis for token blacklisting

#### 3. Environment Variable Issues
**Symptom**: `get_env_value()` returns None
**Solution**:
- Check variable is defined in `shared/config/env_constants.py`
- Verify environment-specific defaults are set
- Use `get_env_value(VARIABLE_NAME, default="fallback")`

#### 4. Database Connection Issues
**Symptom**: Database connection errors
**Solution**:
```bash
# Check PostgreSQL health
make postgres-logs

# Test database connection
make db-shell

# Reset database if needed
make db-reset
```

#### 5. AI Service Issues
**Symptom**: Ollama or ChromaDB connection failures
**Solution**:
```bash
# Check AI service logs
make ollama-logs
make chromadb-logs

# Test AI endpoints
curl http://localhost:8003/api/v1/ai/ollama/health
curl http://localhost:8003/api/v1/ai/chromadb/health
```

## 📋 Code Review Checklist

Before submitting code, ensure:

### Security & Multi-Tenancy ✅
- [ ] All endpoints use `get_current_user()` for authentication
- [ ] All database operations use `get_tenant_session()`
- [ ] Creator_id isolation is properly tested
- [ ] No hardcoded secrets or credentials
- [ ] Input validation with Pydantic models

### Code Quality ✅
- [ ] Async/await patterns used for all I/O
- [ ] Proper error handling and logging
- [ ] Type hints throughout
- [ ] Code formatted with `make format`
- [ ] No linting errors (`make lint`)

### Testing ✅
- [ ] Unit tests for all business logic
- [ ] Multi-tenant isolation tests
- [ ] Authentication/authorization tests
- [ ] 90%+ coverage for new code
- [ ] Integration tests for complex workflows

### Documentation ✅
- [ ] API endpoints documented with OpenAPI
- [ ] Complex business logic commented
- [ ] README updated if needed
- [ ] CLAUDE.md updated for significant changes

## 🔧 Useful Commands

```bash
# Development workflow
make up && make health              # Start and verify services
make ai-engine-logs                # Watch AI engine logs
make test-ai-engine                # Test specific service
make format && make lint           # Format and lint code

# Debugging
docker-compose ps                  # Check container status
docker-compose logs SERVICE        # View service logs
make logs-errors                   # Filter error logs
curl http://localhost:PORT/health   # Test service health

# Database operations
make db-shell                      # PostgreSQL shell
make redis-shell                   # Redis CLI
make db-migrate                    # Run migrations
make db-reset                      # Reset database (destructive)

# Testing
make test-coverage                 # Generate coverage report
make test-unit                     # Fast unit tests only
make test-integration             # Integration tests
make test-e2e                     # End-to-end tests
```

## 📚 Additional Resources

- **Project Documentation**: `.kiro/` directory
- **API Documentation**: http://localhost:8003/docs (AI Engine)
- **Test Coverage**: `htmlcov/index.html` after `make test-coverage`
- **Service Health**: `make health` or individual service `/health` endpoints
- **Database Schema**: Check `shared/models/` and `alembic/versions/`