---
inclusion: always
---

# Technology Stack & Development Guidelines

## Architecture Patterns

### Microservices Structure
- **Service Isolation**: Each service in `services/` directory is independent with its own FastAPI app
- **Shared Components**: Common code lives in `shared/` directory (models, utils, config, cache)
- **Multi-Tenancy**: Use PostgreSQL Row Level Security for tenant isolation
- **API Design**: RESTful APIs with OpenAPI documentation via FastAPI

### Code Organization
- **Service Structure**: `services/{service-name}/` contains routes, models, dependencies
- **Shared Utilities**: Use `shared/utils/` for common functions, `shared/models/` for database models
- **Configuration**: Environment-based config in `shared/config/`
- **Testing**: Service-specific tests in each service, integration tests in root `tests/`

## Technology Stack

### Core Backend
- **FastAPI** (Python 3.11+): Async web framework with automatic OpenAPI docs
- **SQLAlchemy 2.0+**: Async ORM with declarative models
- **PostgreSQL 15**: Primary database with RLS for multi-tenancy
- **Redis 7**: Caching, sessions, and pub/sub messaging
- **Alembic**: Database migrations with version control

### AI/ML Components
- **Ollama**: Local LLM serving (llama2:7b-chat model)
- **LangChain**: AI workflow orchestration and prompt management
- **ChromaDB**: Vector embeddings storage for semantic search
- **nomic-embed-text**: Text embedding model for vector operations

### Infrastructure
- **Docker Compose**: Development environment orchestration
- **Nginx**: API gateway, load balancing, and static file serving
- **JWT Authentication**: Token-based auth with python-jose and passlib[bcrypt]

## Development Standards

### Code Quality Requirements
- **Type Hints**: MANDATORY for all function parameters and return values
- **Pydantic Models**: Use for all request/response validation and serialization
- **Async Patterns**: Use `async/await` for all I/O operations (DB, Redis, HTTP)
- **Error Handling**: Implement proper HTTP status codes and exception handling
- **Line Length**: 100 characters maximum (Black formatter)

### File Naming & Structure
- **Snake Case**: Use `snake_case` for Python files and functions
- **Service Modules**: `{service}/routes/`, `{service}/models/`, `{service}/dependencies/`
- **Shared Modules**: `shared/models/`, `shared/utils/`, `shared/cache/`
- **Test Files**: Prefix with `test_` and mirror source structure

### Database Patterns
- **Async Sessions**: Always use async SQLAlchemy sessions
- **Repository Pattern**: Create repository classes for complex queries
- **Migrations**: Use Alembic for all schema changes
- **RLS Policies**: Implement Row Level Security for tenant data isolation

## Essential Commands

### Development Workflow
```bash
make setup          # Initial environment setup
make up             # Start all services
make format         # Format code (Black + isort)
make lint           # Run linting checks
make test           # Run test suite
make db-migrate     # Apply database migrations
```

### Service Management
```bash
make {service}-logs # View individual service logs
make health         # Check all service health
make db-shell       # Access PostgreSQL
make redis-shell    # Access Redis CLI
```

## Service Ports & Endpoints
- **Auth Service**: 8001 (`/auth/`)
- **Creator Hub**: 8002 (`/creator-hub/`)
- **AI Engine**: 8003 (`/ai-engine/`)
- **Channel Service**: 8004 (`/channels/`)
- **PostgreSQL**: 5432
- **Redis**: 6379
- **Ollama**: 11434
- **ChromaDB**: 8000

## AI Assistant Guidelines

### When Writing Code
1. **Check Existing**: Search for similar functionality before creating new files
2. **Use Shared**: Leverage `shared/` directory utilities and models
3. **Follow Patterns**: Match existing service structure and naming conventions
4. **Add Types**: Include comprehensive type hints and Pydantic models
5. **Handle Errors**: Implement proper exception handling with HTTP status codes

### When Modifying Services
1. **Service Isolation**: Keep service-specific logic within service boundaries
2. **Async Operations**: Use async patterns for all database and external API calls
3. **Caching Strategy**: Implement Redis caching for frequently accessed data
4. **Multi-Tenant**: Ensure all database queries respect tenant isolation

### Testing Requirements
- Unit tests for business logic
- Integration tests for API endpoints
- Multi-tenant isolation verification
- Redis caching behavior validation