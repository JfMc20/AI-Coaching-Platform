# CLAUDE.md

This file provides comprehensive guidance to Claude Code (claude.ai/code) when working with this Multi-Channel AI Coaching Platform.

## 🚀 Project Overview

**Multi-Channel AI Coaching Platform** - Enterprise-grade microservices architecture with 4 FastAPI services, AI/ML pipeline, and multi-tenant security. Platform enables creators to build and deploy proactive coaching programs across multiple channels.

**Technology Stack:**
- **Backend**: FastAPI + SQLAlchemy + AsyncPG + Redis + JWT
- **AI/ML**: Ollama (LLM) + ChromaDB (Vector DB) + RAG Pipeline  
- **Infrastructure**: Docker + PostgreSQL + Nginx + Multi-tenant RLS
- **Testing**: Pytest + Coverage + Testcontainers + Poetry workspace

## 🎯 Current Project State (Updated 2025-01-16)

**MVP Status: PRODUCTION READY** ✅

### Production Ready Services:
- ✅ **Auth Service (8001)**: Complete JWT + RBAC + GDPR implementation
- ✅ **AI Engine Service (8003)**: Full RAG pipeline with Ollama + ChromaDB integration  
- ✅ **Infrastructure**: PostgreSQL + Redis + ChromaDB + Ollama fully operational
- ✅ **Testing Suite**: 85%+ coverage with comprehensive fixtures

### Foundation Services (Require Enhancement):
- ⚠️ **Creator Hub Service (8002)**: Basic structure, needs content management features
- ⚠️ **Channel Service (8004)**: WebSocket foundation, needs multi-channel expansion

### Key Technical Achievements:
- ✅ Multi-tenant architecture with Row Level Security (RLS) policies
- ✅ Production-grade RAG pipeline with embedding generation  
- ✅ Comprehensive test suite with 85%+ coverage (Poetry workspace)
- ✅ Docker-based development environment with health checks
- ✅ Security hardening: JWT + Argon2 + Rate limiting + Input validation
- ✅ Advanced monitoring with OpenTelemetry and privacy protection

## 🏗️ Architecture & Infrastructure

### Microservices Structure:
```
📦 Multi-Channel AI Coaching Platform
├── 🔐 auth-service (8001)          # JWT + RBAC + GDPR + Multi-tenant
├── 🎨 creator-hub-service (8002)   # Content management + Program builder
├── 🤖 ai-engine-service (8003)     # RAG pipeline + Ollama + ChromaDB  
├── 📡 channel-service (8004)       # WebSocket + Multi-channel support
├── 🌐 nginx (80/443)               # API Gateway + Load balancer
└── 📊 Infrastructure Services      # PostgreSQL + Redis + ChromaDB + Ollama
```

### Data Layer Architecture:
- **PostgreSQL 15**: Multi-tenant RLS policies, async SQLAlchemy, connection pooling
- **Redis 7**: Tenant-isolated caching (DB 0-4), sessions, rate limiting, message queues  
- **ChromaDB**: Vector storage with creator-specific collections (`creator_{creator_id}_knowledge`)
- **Async Patterns**: All I/O operations use async/await, connection pooling optimized

### AI/ML Stack:
- **Ollama**: Local LLM serving (llama2:7b-chat, llama3.2, nomic-embed-text)
- **ChromaDB**: Vector embeddings with HNSW indexing, auto-scaling collections
- **RAG Pipeline**: 1000 token chunks, 200 overlap, <5s response times, context-aware
- **Monitoring**: OpenTelemetry tracing + privacy-preserving ML metrics

## 🛠️ Essential Development Commands

### Quick Start:
```bash
# 🚀 Complete environment setup (first time)
make setup              # Initialize environment + pull AI models + health checks

# 🐳 Daily development workflow  
make up                 # Start all services
make health            # Check service health status
make down              # Stop services when done
```

### 🧪 Testing & Quality:
```bash
# 🏃‍♂️ Fast testing workflow
make test-unit                    # Unit tests only (fastest)
make test-auth                   # Auth service tests only
make test-ai-engine             # AI engine tests only
make test                       # Full test suite with coverage

# 🔍 Code quality
make lint                       # Flake8 linting  
make format                     # Black + isort formatting
make pre-commit                 # Run all pre-commit hooks

# 📊 Coverage analysis
make test-coverage              # Generate HTML coverage report → htmlcov/
```

### 🐛 Debugging & Logs:
```bash
# 🔍 Service-specific logs (most useful)
make ai-engine-logs             # AI engine service logs (follow mode)
make auth-logs                  # Auth service logs
make postgres-logs              # Database logs
make logs-errors               # Only error logs from all services

# 📋 Log analysis
make logs-save                  # Save all logs to timestamped files
make logs-analyze              # Analyze error patterns
```

### 💾 Database Operations:
```bash
make db-shell                   # PostgreSQL shell access
make db-migrate                 # Run Alembic migrations  
make db-reset                   # Reset database (destructive)
make redis-shell               # Redis CLI access
```

### 🚨 Troubleshooting Commands:
```bash
# 🔧 Container issues
docker-compose ps               # Check container status
docker-compose logs SERVICE     # Specific service logs
docker-compose build --no-cache SERVICE  # Rebuild service

# 🌡️ Health diagnostics  
make health                     # All service health checks
curl http://localhost:8003/ready # AI engine readiness
```

## ⚡ Development Patterns & Best Practices

### 🏛️ Multi-Tenant Architecture (CRITICAL):
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

### 🔄 Async Patterns (MANDATORY):
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

### 🔐 Security Implementation (ENFORCE):
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

### 📝 Configuration Management:
- **Environment Variables**: Use `get_env_value()` from `shared.config.env_constants`
- **Service Requirements**: Auto-generated from `pyproject.toml` Poetry workspace
- **Multi-Environment**: Development, testing, production configurations centralized

### 🧪 Testing Strategy:
- **Coverage Requirement**: 85%+ existing code, 90%+ new features
- **Fixtures**: Use comprehensive fixtures from `tests/fixtures/`
- **Multi-tenant Tests**: Always verify creator_id isolation
- **Integration Tests**: Use testcontainers for real database/Redis testing

## 📁 Key Files & Project Structure

### 🎯 Essential Configuration:
```
📁 Root Configuration
├── pyproject.toml                    # Poetry workspace + dependencies
├── docker-compose.yml               # Development orchestration  
├── Makefile                         # Development commands (68 commands!)
├── CLAUDE.md                        # This file - Claude Code guidance
└── .kiro/                          # Project specs + steering docs

📁 Shared Components (shared/)
├── config/env_constants.py          # Centralized environment variables
├── models/database.py              # Multi-tenant base models + RLS
├── security/                       # JWT + RBAC + Rate limiting
├── ai/                            # Ollama + ChromaDB managers  
├── monitoring/                     # OpenTelemetry + Privacy-preserving
└── exceptions/                     # Structured error handling

📁 Services (services/)
├── auth-service/                   # JWT + RBAC + GDPR (Production Ready)
├── ai-engine-service/             # RAG Pipeline + ML (Production Ready)  
├── creator-hub-service/           # Content management (Foundation)
└── channel-service/               # WebSocket + Multi-channel (Foundation)

📁 Testing (tests/)
├── fixtures/                      # Comprehensive test fixtures
├── unit/                         # Service-specific unit tests
├── shared/                       # Shared component tests
└── e2e/                         # End-to-end integration tests
```

### 🤖 AI/ML Integration:
- **Document Processing**: `ai-engine-service/app/document_processor.py` (PDF, DOCX, TXT)
- **Vector Storage**: `shared/ai/chromadb_manager.py` (Creator-isolated collections)
- **RAG Pipeline**: `ai-engine-service/app/rag_pipeline.py` (Context-aware responses)
- **LLM Integration**: `shared/ai/ollama_manager.py` (Local model serving)

### 🔐 Security Stack:
- **Authentication**: JWT RS256, 15min access + 30day refresh, Redis blacklisting
- **Authorization**: RBAC system in `shared/security/rbac.py`
- **Multi-Tenancy**: PostgreSQL RLS policies enforce creator_id isolation  
- **Rate Limiting**: `shared/security/rate_limiter.py` (Redis-backed, tenant-aware)
- **Password Security**: Argon2 hashing, strength validation, reset flows

## Performance Targets

- API responses: <2s (p95)
- AI responses: <5s (p95) 
- Database queries: <100ms (p95)
- Support: 1,000+ creators, 10,000+ users
- Test coverage: 85%+ required, 90%+ for new features

## 🚀 Claude Code Development Workflows

### 🔧 Common Development Tasks:

#### Adding New API Endpoints:
```bash
# 1. Create endpoint in appropriate service
cd services/ai-engine-service/app/
# Edit main.py or create new router file

# 2. Add request/response models with Pydantic
# 3. Implement multi-tenant authentication pattern
# 4. Run tests to ensure coverage
make test-ai-engine

# 5. Test endpoint manually
curl -X POST http://localhost:8003/api/v1/new-endpoint \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"data": "test"}'
```

#### Debugging Service Issues:
```bash
# 1. Check service health
make health

# 2. View specific service logs  
make ai-engine-logs      # Most common issues are here
make auth-logs          # For authentication issues
make postgres-logs      # For database issues

# 3. Check container status
docker-compose ps

# 4. Rebuild if needed (code changes)
docker-compose build --no-cache ai-engine-service
make up
```

#### Database Schema Changes:
```bash
# 1. Create migration
poetry run alembic revision --autogenerate -m "description"

# 2. Review generated migration in alembic/versions/
# 3. Apply migration
make db-migrate

# 4. Test with multi-tenant data
make test-unit tests/shared/test_database.py
```

### 🧪 Testing New Features:
```bash
# 1. Write tests first (TDD approach)
# Create test file in tests/unit/SERVICE-NAME/

# 2. Run specific tests during development
poetry run pytest tests/unit/ai-engine-service/test_new_feature.py -v

# 3. Check coverage (aim for 90%+ on new code)
make test-coverage

# 4. Run full test suite before committing
make test
```

### 🐛 Troubleshooting Multi-Tenant Issues:
```python
# Common issue: Data leaking between creators
# Always verify creator_id isolation in tests:

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

## 🎯 Q1 2025 Development Priorities

### 1. Creator Hub Enhancement (CRITICAL) 🔴
**Files to focus on**: `services/creator-hub-service/app/main.py`
- **Knowledge Base Management**: Document upload, processing, organization
- **Visual Program Builder**: React Flow-based coaching program creation  
- **Analytics Dashboard**: Creator insights and performance metrics
- **Status**: Foundation exists, core features needed

### 2. Multi-Channel Expansion (HIGH) 🟡  
**Files to focus on**: `services/channel-service/app/main.py`
- **WhatsApp Business Integration**: Official API integration + webhooks
- **Web Widget Implementation**: Embeddable chat widget with customization
- **Enhanced AI Conversation**: Personality consistency + proactive engagement
- **Status**: WebSocket foundation ready, channel handlers needed

### 3. Mobile Experience (MEDIUM) 🟢
**Backend APIs ready**: Focus on mobile app development
- **React Native App**: Cross-platform mobile application "Compañero"
- **Gamification System**: Points, achievements, progress tracking
- **Offline Support**: Local data storage with background sync

## Current Task Status

The platform is at a **functional MVP stage** with 4 main areas completed and 3 areas requiring enhancement:

**Completed (✅)**:
1. Infrastructure & Development Environment
2. Authentication & Authorization Service  
3. AI Engine with RAG Pipeline
4. Testing Infrastructure & Quality Assurance

**In Progress (🔄)**:
5. Creator Hub Service - Core features needed
6. Channel Service - Multi-channel expansion required
7. Web Widget Development - Foundation exists

**Pending Implementation**:
- Mobile application development
- Advanced analytics and monitoring
- Enterprise features and integrations

## 🎯 Claude Code Development Guidelines

### 🛡️ Security & Multi-Tenancy (CRITICAL):
1. **Multi-tenant First**: ALWAYS implement creator_id isolation and RLS policies
2. **Authentication**: Use `get_current_user()` dependency in ALL protected endpoints
3. **Data Isolation**: NEVER allow creator data to leak across tenants
4. **Input Validation**: Use Pydantic models for ALL request/response validation
5. **Rate Limiting**: Automatically applied, but verify limits in `shared/security/rate_limiter.py`

### 🔧 Code Quality Standards:
1. **Type Safety**: Use comprehensive type hints and Pydantic models everywhere
2. **Async Patterns**: MANDATORY async/await for all I/O operations 
3. **Error Handling**: Use structured exceptions from `shared/exceptions/`
4. **Testing**: Achieve 90%+ coverage with multi-tenant test isolation
5. **Performance**: Meet <2s API response time targets

### 📁 File and Service Structure Management:
1. **ALWAYS check existing service structure** before creating new files or directories
2. **Follow established patterns** from working services (auth-service, creator-hub-service)
3. **Keep service-specific files within service boundaries** - Never create cross-service dependencies
4. **Use shared/ directory only for truly shared components** - Not for service-specific implementations
5. **Check implementation patterns** in other services before duplicating functionality
6. **Verify file locations** in the current service before creating new structures

### 🎯 Task Completion and Testing Protocol:
1. **Complete ONE task at a time** - Never jump to next task until current is fully working
2. **Test thoroughly** - Every endpoint, every function, every integration must be verified
3. **Docker cache awareness** - Always rebuild without cache when making structural changes
4. **End-to-end verification** - Test the complete user flow, not just individual components
5. **Documentation validation** - Ensure all created endpoints are accessible and functional
6. **Error investigation** - Understand and fix ALL errors before proceeding to next task

### 📋 Before Committing Code:
```bash
# 1. Format and lint code
make format
make lint

# 2. Run relevant tests
make test-auth          # If auth changes
make test-ai-engine     # If AI engine changes  
make test              # Full suite for major changes

# 3. Check coverage
make test-coverage     # Ensure 90%+ for new code

# 4. Verify health after changes
make up
make health
```

### 🚨 Common Pitfalls to Avoid:
- ❌ **Never hardcode environment variables** - Use `get_env_value()`
- ❌ **Never expose creator data across tenants** - Always test isolation
- ❌ **Never use blocking I/O** - Use async patterns only
- ❌ **Never skip authentication** - All endpoints need `get_current_user()`
- ❌ **Never commit without tests** - TDD approach preferred
- ❌ **Never create files outside the current service context** - Always check existing structure first
- ❌ **Never jump between tasks without completing current one** - Test thoroughly before moving on
- ❌ **Never assume similar implementations exist** - Always check other services for patterns first

### 📚 Project Documentation:
- **Detailed Tasks**: `.kiro/specs/mvp-foundation-platform/tasks.md`
- **Technical Guidance**: `.kiro/steering/` directory
- **API Documentation**: Available at http://localhost:8003/docs (AI Engine)
- **Test Coverage**: `htmlcov/index.html` after running `make test-coverage`

### 🔍 When Debugging Issues:
1. **Check logs first**: `make ai-engine-logs` or `make SERVICE-logs`
2. **Verify health**: `make health` 
3. **Check environment**: Variables in `shared/config/env_constants.py`
4. **Test isolation**: Multi-tenant data separation
5. **Performance**: API response times and database query performance

### 💡 Pro Tips for Claude Code:
- Use `make` commands instead of raw docker-compose for consistent workflows
- The project uses Poetry workspace - all dependencies managed in root `pyproject.toml`
- All services share the `shared/` directory for common functionality
- Multi-tenant architecture is the foundation - always think creator_id first
- 85%+ test coverage is enforced - write tests as you develop features

## 🗃️ ROBUST DATABASE MANAGEMENT SYSTEM (UPDATED 2025-01-16)

### 🎯 **NEW: Production-Ready Migration System**

El proyecto ahora incluye un sistema robusto de migraciones que elimina los problemas comunes de base de datos en desarrollo y producción.

### ✅ **Comandos Esenciales de Base de Datos**

```bash
# 🔍 Verificar estado de la base de datos
make db-status              # Estado completo: conexión, migraciones, tablas

# 🚀 Inicialización segura
make db-init                # Inicializar DB con migraciones apropiadas

# 🔄 Migraciones con validación
make db-migrate             # Ejecutar migraciones con validación automática

# ✅ Validación antes de aplicar
make db-validate            # Verificar seguridad antes de migrar

# 💾 Backup (solo desarrollo)
make db-backup              # Crear backup antes de cambios importantes

# 📝 Crear nueva migración
make db-create-migration    # Crear migración con auto-generación
```

### 🔒 **Seguridad Multi-Tenant**

**Row Level Security (RLS) Automático:**
- Todas las tablas incluyen políticas RLS
- Aislamiento automático por `creator_id`
- Validación de contexto de tenant
- Protección contra data leaks

**Tablas Implementadas:**
- ✅ `creators` - Gestión de usuarios/creadores
- ✅ `documents` - Knowledge base con metadatos
- ✅ `widget_configurations` - Configuración de widgets
- ✅ `conversations` - Historial de conversaciones
- ✅ `refresh_tokens`, `jwt_blacklist` - Seguridad JWT
- ✅ `audit_logs` - Auditoría completa

### 🛠️ **Para Desarrolladores**

**Modelos SQLAlchemy Sincronizados:**
```python
# Todos los modelos en shared/models/database.py
from shared.models.database import Document, Creator, WidgetConfiguration

# Auto-relaciones con RLS
document = Document(creator_id=creator_id, title="Test")
# RLS automáticamente filtra por creator_id
```

**Comandos de Desarrollo:**
```bash
# Estado rápido
make db-status

# Reinicio completo (cuidado!)
make db-reset               # Solo desarrollo

# Acceso directo
make db-shell               # PostgreSQL shell
make redis-shell            # Redis shell
```

### 🏭 **Para Producción**

**Validaciones Automáticas:**
- ❌ Rollbacks bloqueados en producción
- ✅ Validación de conexión antes de migrar
- ✅ Detección de migraciones pendientes
- ✅ Verificación de integridad de datos

**Script de Migración Robusto:**
```bash
# En contenedor
python /app/scripts/db-migration-manager.py status
python /app/scripts/db-migration-manager.py migrate --env production
```

### 🚨 **Resolución de Problemas Comunes**

**Error: "Multiple heads detected"**
- ✅ **Solucionado**: Sistema ahora maneja branches automáticamente

**Error: "Table already exists"**
- ✅ **Solucionado**: Auto-detección de estado actual y stamping inteligente

**Error: "Migration timeout"**
- ✅ **Solucionado**: Timeouts configurables y rollback automático

**Error: "RLS policy conflicts"**
- ✅ **Solucionado**: Políticas consistentes auto-aplicadas

### 🔄 **Flujo de Trabajo Recomendado**

```bash
# 1. Verificar estado antes de cambios
make db-status

# 2. Crear backup si es necesario
make db-backup

# 3. Aplicar migraciones
make db-migrate

# 4. Verificar resultado
make db-status

# 5. Si hay problemas, logs detallados
docker-compose logs auth-service | grep migration
```