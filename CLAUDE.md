# CLAUDE.md

Este archivo proporciona guía integral a Claude Code (claude.ai/code) para trabajar con la Multi-Channel AI Coaching Platform.

## 🚀 Project Overview

**"RESULTS AS A SERVICE" - AI Coaching Platform** - Plataforma revolucionaria que crea **digital twins de creadores** mediante RAG avanzado + síntesis de personalidad. Los creadores suben su conocimiento/metodología y la IA se convierte en su clon de coaching proactivo, entregando cambios de comportamiento medibles a través de múltiples canales.

### 🧬 Core Innovation: Creator Digital Twin
- **Personality Synthesis**: IA aprende la voz, metodología y estilo de coaching del creador
- **Proactive Engagement**: IA inicia conversaciones basándose en patrones de comportamiento del usuario
- **Program Orchestration**: Constructor visual de flujos de coaching drag-and-drop
- **Behavioral Analytics**: Mide cambios reales de comportamiento, no solo satisfacción
- **Multi-Channel Presence**: El twin de IA del creador disponible 24/7 en todas las plataformas

**Technology Stack:**
- **Backend**: FastAPI + SQLAlchemy + AsyncPG + Redis + JWT
- **AI/ML**: Ollama (LLM) + ChromaDB (Vector DB) + RAG Pipeline  
- **Infrastructure**: Docker + PostgreSQL + Nginx + Multi-tenant RLS
- **Testing**: Pytest + Coverage + Testcontainers + Poetry workspace

## 🎯 Current Project State (2025-01-17)

**MVP Status: PRODUCTION READY** ✅

### Production Ready Services:
- ✅ **Auth Service (8001)**: Complete JWT + RBAC + GDPR implementation
- ✅ **AI Engine Service (8003)**: Full RAG pipeline with Ollama + ChromaDB integration  
- ✅ **Infrastructure**: PostgreSQL + Redis + ChromaDB + Ollama fully operational
- ✅ **Testing Suite**: 85%+ coverage with comprehensive fixtures

### Foundation Services (Require Enhancement):
- ⚠️ **Creator Hub Service (8002)**: Basic structure, needs content management features
- ⚠️ **Channel Service (8004)**: WebSocket foundation, needs multi-channel expansion

**📚 For detailed documentation see**: [.docs/README.md](.docs/README.md)

## 🛠️ Essential Development Commands

### Quick Start
```bash
# 🚀 Complete environment setup (first time)
make setup              # Initialize environment + pull AI models + health checks

# 🐳 Daily development workflow  
make up                 # Start all services
make health            # Check service health status
make down              # Stop services when done
```

**📚 Complete development guide**: [.docs/development/quick-start.md](.docs/development/quick-start.md)

## 🏗️ Architecture Overview

### Microservices Structure
```
📦 Multi-Channel AI Coaching Platform
├── 🔐 auth-service (8001)          # JWT + RBAC + GDPR ✅ Production Ready
├── 🎨 creator-hub-service (8002)   # Content management ⚠️ Foundation Ready
├── 🤖 ai-engine-service (8003)     # RAG pipeline + Ollama ✅ Production Ready
├── 📡 channel-service (8004)       # WebSocket + Multi-channel ✅ Demo Ready
├── 🔧 testing-service (8005)       # Visual debugging 🚧 Future Implementation
└── 📊 Infrastructure Services      # PostgreSQL + Redis + ChromaDB ✅ Optimized
```

**📚 Detailed architecture**: 
- [Microservices](.docs/architecture/microservices.md)
- [Data Layer](.docs/architecture/data-layer.md)
- [Security](.docs/architecture/security.md)

## ⚡ Development Patterns (CRITICAL)

### 🛡️ Multi-Tenant Architecture (MANDATORY)
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
```

### 🔄 Async Patterns (MANDATORY)
```python
# ✅ All I/O operations use async/await
async def process_document(file: UploadFile, creator_id: str) -> Result:
    async with get_db_session() as session:
        result = await session.execute(select(Document))
    
    async with get_redis_client() as redis:
        await redis.set(f"cache:{creator_id}", data)
```

### 🔐 Security Implementation (ENFORCE)
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
```

**📚 Complete patterns guide**: [.docs/development/patterns.md](.docs/development/patterns.md)

## 🗃️ Database Management

### Essential Commands
```bash
# 🔍 Verificar estado de la base de datos
make db-status              # Estado completo: conexión, migraciones, tablas

# 🔄 Migraciones con validación
make db-migrate             # Ejecutar migraciones con validación automática

# 📝 Crear nueva migración
make db-create-migration    # Crear migración con auto-generación
```

**📚 Complete database guide**: [.docs/development/database-management.md](.docs/development/database-management.md)

## 🎯 Q1 2025 Development Priorities

### 1. Creator Hub Enhancement (CRITICAL) 🔴
**Files**: `services/creator-hub-service/app/main.py`
- Knowledge Base Management
- Visual Program Builder
- Analytics Dashboard

### 2. Multi-Channel Expansion (HIGH) 🟡
**Files**: `services/channel-service/app/main.py`
- WhatsApp Business Integration
- Enhanced AI Conversation
- Personality consistency

### 3. Visual Testing & Training Service (HIGH) 🔶
**New Service**: `services/testing-service/` (Port 8005)
- Creator Personality Trainer
- Proactive Engine Simulator
- Multi-Channel Orchestrator

**📚 Complete priorities**: [.docs/specs/q1-2025-priorities.md](.docs/specs/q1-2025-priorities.md)

## 🧬 Creator Personality System (CORE INNOVATION)

Sistema modular que captura, sintetiza y replica personalidades de creadores para crear digital twins auténticos.

### Key Components
- **Personality Engine**: Análisis y síntesis de personalidad
- **Dynamic Prompt Generation**: Prompts contextuales y personalizados
- **Consistency Monitoring**: Seguimiento de alineación de personalidad
- **Analytics Dashboard**: Métricas de rendimiento de personalidad

**📚 Complete personality system spec**: [.docs/specs/personality-system.md](.docs/specs/personality-system.md)

## 🔧 Claude Code Development Guidelines

### 🛡️ Security & Multi-Tenancy (CRITICAL)
1. **Multi-tenant First**: ALWAYS implement creator_id isolation and RLS policies
2. **Authentication**: Use `get_current_user()` dependency in ALL protected endpoints
3. **Data Isolation**: NEVER allow creator data to leak across tenants
4. **Input Validation**: Use Pydantic models for ALL request/response validation

### 🔧 Code Quality Standards
1. **Type Safety**: Use comprehensive type hints and Pydantic models everywhere
2. **Async Patterns**: MANDATORY async/await for all I/O operations 
3. **Error Handling**: Use structured exceptions from `shared/exceptions/`
4. **Testing**: Achieve 90%+ coverage with multi-tenant test isolation
5. **Performance**: Meet <2s API response time targets

### 📁 File Structure Management
1. **Check existing service structure** before creating new files
2. **Follow established patterns** from working services
3. **Keep service-specific files within service boundaries**
4. **Use shared/ directory only for truly shared components**

### 🎯 Task Completion Protocol
1. **Complete ONE task at a time** - Never jump until current is fully working
2. **Test thoroughly** - Every endpoint, function, integration must be verified
3. **Docker cache awareness** - Rebuild without cache for structural changes
4. **End-to-end verification** - Test complete user flow
5. **Error investigation** - Understand and fix ALL errors before proceeding

### 🚨 Common Pitfalls to Avoid
- ❌ **Never hardcode environment variables** - Use `get_env_value()`
- ❌ **Never expose creator data across tenants** - Always test isolation
- ❌ **Never use blocking I/O** - Use async patterns only
- ❌ **Never skip authentication** - All endpoints need `get_current_user()`
- ❌ **Never commit without tests** - TDD approach preferred

### 📋 Before Committing Code
```bash
# 1. Format and lint code
make format && make lint

# 2. Run relevant tests
make test-auth          # If auth changes
make test-ai-engine     # If AI engine changes  
make test              # Full suite for major changes

# 3. Check coverage
make test-coverage     # Ensure 90%+ for new code

# 4. Verify health after changes
make up && make health
```

## 📚 Documentation Structure

### Architecture Documentation
- [Microservices Architecture](.docs/architecture/microservices.md)
- [Data Layer Design](.docs/architecture/data-layer.md)
- [Security Implementation](.docs/architecture/security.md)

### Development Guides
- [Quick Start Guide](.docs/development/quick-start.md)
- [Development Patterns](.docs/development/patterns.md)
- [Database Management](.docs/development/database-management.md)

### Specifications
- [Creator Personality System](.docs/specs/personality-system.md)
- [Q1 2025 Priorities](.docs/specs/q1-2025-priorities.md)

### Key Files Reference
- **Configuration**: `shared/config/env_constants.py`
- **Database Models**: `shared/models/database.py`
- **Security**: `shared/security/`
- **AI Integration**: `shared/ai/`
- **Testing Fixtures**: `tests/fixtures/`

## Performance Targets

- API responses: <2s (p95)
- AI responses: <5s (p95) 
- Database queries: <100ms (p95)
- Support: 1,000+ creators, 10,000+ users
- Test coverage: 85%+ required, 90%+ for new features

---

**🔗 For complete documentation, architecture details, and development guides, see the [.docs/](.docs/) directory.**