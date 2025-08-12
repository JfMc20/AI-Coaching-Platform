---
inclusion: always
---

# MVP Coaching AI Platform - Development Guide

## Architecture Overview

### Microservices (Port → Route)
- **Auth Service** (8001) → `/api/v1/auth/` - JWT authentication, multi-tenancy
- **Creator Hub** (8002) → `/api/v1/creators/` - Content management, coaching programs
- **AI Engine** (8003) → `/api/v1/ai/` - Ollama LLM, ChromaDB embeddings
- **Channel Service** (8004) → `/api/v1/channels/` - WebSockets, real-time messaging

### Core Stack
- **Backend**: FastAPI + SQLAlchemy 2.0 (async) + PostgreSQL 15 (RLS enabled)
- **Caching**: Redis 7 (multi-tenant namespacing)
- **Gateway**: Nginx (routing, security headers, rate limiting)
- **AI/ML**: Ollama (llama2:7b-chat) + ChromaDB (vector embeddings)

## Critical Implementation Patterns

### Multi-Tenant Security (MANDATORY)
Every database operation MUST set tenant context:

```python
# Required before any DB operation
async def set_tenant_context(creator_id: str, db: AsyncSession):
    await db.execute(
        text("SELECT set_config('app.current_creator_id', :creator_id, true)"),
        {"creator_id": creator_id}
    )

# Standard FastAPI dependency
async def get_tenant_db(
    creator_id: str = Depends(get_current_creator_id),
    db: AsyncSession = Depends(get_db)
) -> AsyncSession:
    await set_tenant_context(creator_id, db)
    return db
```

### Service Health Checks (MANDATORY)
```python
@router.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "service-name",
        "timestamp": datetime.utcnow().isoformat()
    }
```

### Code Quality Requirements (NON-NEGOTIABLE)
- **Type hints**: ALL functions must have parameter and return type annotations
- **Async operations**: Use `async/await` for ALL I/O (database, Redis, HTTP calls)
- **Pydantic models**: Required for request/response validation and serialization
- **Line length**: 100 characters maximum (Black formatter enforced)
- **Complexity**: Cyclomatic complexity ≤ 10 per function

## Project Structure

### Service Organization
```
services/{service-name}/
├── routes/          # FastAPI endpoint definitions
├── models/          # Service-specific Pydantic models
├── dependencies/    # FastAPI dependency injection
└── __init__.py
```

### Shared Components (Use First)
```
shared/
├── models/          # SQLAlchemy database models (multi-tenant)
├── utils/           # Common utility functions
├── cache/           # Redis operations and patterns
├── config/          # Environment configuration
└── validators/      # Reusable Pydantic validators
```

## Development Workflow

### Local Development Setup
```powershell
# Start infrastructure services
docker-compose up -d postgres redis ollama chromadb

# Build and start application services
.\scripts\docker-build-optimized.ps1 -Parallel
docker-compose up -d

# Verify all services are healthy
.\scripts\test-api-gateway.ps1
```

### Service Health Verification
- **Gateway**: `http://localhost/health`
- **Auth**: `http://localhost/api/v1/auth/health`
- **Creator Hub**: `http://localhost/api/v1/creators/health`
- **AI Engine**: `http://localhost/api/v1/ai/health`
- **Channels**: `http://localhost/api/v1/channels/health`

## AI/ML Implementation Standards

### Model Management
- **Version tracking**: Use model registry for all AI models
- **Graceful degradation**: Implement fallbacks when AI services fail
- **Tenant isolation**: Namespace all embeddings and conversations by tenant ID
- **Prompt versioning**: Use versioned templates with v1 fallback

### Integration Requirements
- **Privacy-first**: Local Ollama deployment (no external API calls)
- **Vector storage**: ChromaDB for embeddings with tenant isolation
- **Async operations**: All AI calls must be non-blocking
- **Error handling**: Proper HTTP status codes for AI service failures

## Implementation Checklist

Before writing any code:
1. **Search existing**: Check `shared/` and similar services for existing functionality
2. **Follow patterns**: Match established service structure and naming conventions
3. **Async first**: Use async/await for all I/O operations
4. **Multi-tenant**: Implement RLS context for all database operations
5. **Type safety**: Add comprehensive type hints and Pydantic models
6. **Error handling**: Use appropriate HTTP status codes and structured exceptions
7. **Environment config**: Never hardcode values, use environment variables
8. **Test isolation**: Verify multi-tenant data separation in tests