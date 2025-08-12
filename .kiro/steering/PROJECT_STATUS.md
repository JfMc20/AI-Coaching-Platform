---
inclusion: always
---

# MVP Coaching AI Platform - Project Status & Conventions

## Architecture Overview

### Microservices Structure
- **Auth Service** (Port 8001): JWT authentication + multi-tenancy at `/api/v1/auth/`
- **Creator Hub Service** (Port 8002): Content and creator management at `/api/v1/creators/`
- **AI Engine Service** (Port 8003): Ollama + ChromaDB + embeddings at `/api/v1/ai/`
- **Channel Service** (Port 8004): WebSockets + multi-channel at `/api/v1/channels/`

### Infrastructure Stack
- **PostgreSQL 15**: Primary database with Row Level Security for tenant isolation
- **Redis 7**: Multi-tenant caching with stampede prevention
- **Ollama**: Local LLM service (llama2:7b-chat model)
- **ChromaDB**: Vector database for embeddings
- **Nginx**: API Gateway with rate limiting and CORS

## Required Implementation Patterns

### Multi-Tenant Security (MANDATORY)
All database operations MUST implement Row Level Security:

```python
# Required pattern for setting tenant context
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

### Service Health Checks (MANDATORY)
All services MUST implement `/health` endpoint:

```python
@router.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "service-name",
        "timestamp": datetime.utcnow().isoformat()
    }
```

### AI/ML Integration Patterns
- Use **Model Registry** for tracking AI model metadata and versions
- Implement **graceful degradation** when AI services fail
- Use **versioned prompt templates** with fallback strategies
- Namespace embeddings by tenant for isolation

## Development Commands

### Quick Start
```powershell
# Start infrastructure
docker-compose up -d postgres redis ollama chromadb

# Verify dependencies
.\scripts\test-service-dependencies.ps1

# Build and start services
.\scripts\docker-build-optimized.ps1 -Parallel
docker-compose up -d

# Verify API Gateway
.\scripts\test-api-gateway.ps1
```

### Health Verification
```bash
curl http://localhost/health                    # Nginx
curl http://localhost/api/v1/auth/health       # Auth Service
curl http://localhost/api/v1/creators/health   # Creator Hub
curl http://localhost/api/v1/ai/health         # AI Engine
curl http://localhost/api/v1/channels/health   # Channel Service
```

## Code Quality Standards

### Mandatory Requirements
- **Cyclomatic Complexity**: ≤ 10 per function
- **Test Coverage**: ≥ 80%
- **Type Hints**: Required for all functions
- **Async Patterns**: Use async/await for all I/O operations
- **Pydantic Models**: Required for request/response validation

### Pre-commit Tools
- **Black**: Code formatting (100 char line length)
- **isort**: Import sorting
- **Ruff**: Fast linting
- **Mypy**: Type checking
- **Bandit**: Security scanning

## File Structure Conventions

### Service Organization
```
services/{service-name}/
├── routes/          # FastAPI route handlers
├── models/          # Service-specific models
├── dependencies/    # FastAPI dependencies
└── __init__.py
```

### Shared Components
```
shared/
├── models/          # Database models (SQLAlchemy)
├── utils/           # Common utilities
├── cache/           # Redis caching utilities
├── config/          # Configuration management
└── validators/      # Pydantic validators
```

## Documentation Structure
- `docs/01-product/`: Business requirements
- `docs/02-architecture/`: Technical architecture
- `docs/03-api-specifications/`: API documentation
- `docs/07-development-guidelines/`: Development standards

## Key Implementation Notes
- Project uses **FastAPI** with **SQLAlchemy 2.0** async patterns
- All services are **containerized** with optimized Docker builds
- **Multi-tenant isolation** is enforced at the database level with RLS
- **AI services** use local Ollama deployment for privacy
- **API Gateway** handles routing, rate limiting, and CORS
- **Quality gates** are automated via pre-commit hooks and CI/CD