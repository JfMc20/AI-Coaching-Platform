---
inclusion: always
---

# Multi-Channel AI Coaching Platform - Development Guidelines

## Platform Status: Production-Ready MVP ✅

Multi-channel proactive coaching platform with functional microservices, complete infrastructure, and operational AI capabilities. Ready for scaling and advanced feature development.

## Core Architecture Principles

### Multi-Tenancy First (MANDATORY)
- **Row Level Security**: ALL database operations MUST use RLS policies with creator_id isolation
- **Tenant Context**: Set `app.current_creator_id` for ALL database sessions
- **ChromaDB Collections**: Use pattern `creator_{creator_id}_knowledge` for vector storage
- **Redis Keys**: Prefix ALL keys with creator isolation: `{key_type}:creator_{creator_id}:{identifier}`

### Service Communication (ESTABLISHED)
- **Auth Service** (8001): JWT + Multi-tenant + RBAC - PRODUCTION READY
- **Creator Hub** (8002): Content management - BASIC STRUCTURE
- **AI Engine** (8003): RAG + Ollama + ChromaDB - FULLY FUNCTIONAL  
- **Channel Service** (8004): WebSockets + Multi-channel - FOUNDATION READY

## Development Standards (ENFORCED)

### Code Quality Requirements
- **Type Hints**: MANDATORY for all function parameters and return values
- **Async Patterns**: Use `async/await` for ALL I/O operations (DB, Redis, HTTP)
- **Pydantic Models**: REQUIRED for ALL request/response validation
- **Error Handling**: Use shared exception classes from `shared.exceptions`
- **Test Coverage**: Minimum 90% for new features, 85% overall

### Multi-Tenant Implementation Pattern
```python
# MANDATORY pattern for all database operations
async def get_tenant_session(
    creator_id: str = Depends(get_current_creator_id),
    session: AsyncSession = Depends(get_db_session)
) -> AsyncSession:
    await session.execute(
        text("SET app.current_creator_id = :creator_id"),
        {"creator_id": creator_id}
    )
    return session
```

### Service Structure (FOLLOW)
```
services/{service-name}/
├── routes/           # FastAPI endpoints
├── services/         # Business logic layer
├── dependencies/     # FastAPI dependencies  
├── models/          # Service-specific models
└── database.py      # DB connection management
```

## Service Implementation Status

### Auth Service (8001) ✅ PRODUCTION READY
- JWT Authentication with refresh tokens
- Multi-tenant isolation with RLS policies
- RBAC and Argon2 password security
- Rate limiting and GDPR compliance
- Complete API endpoints with documentation

### Creator Hub Service (8002) ⚠️ FOUNDATION ONLY
- Service foundation with health checks
- Auth integration functional
- **NEEDED**: Knowledge base management system
- **NEEDED**: Visual program builder (React Flow)
- **NEEDED**: Analytics dashboard

### AI Engine Service (8003) ✅ FULLY FUNCTIONAL
- RAG pipeline operational with <5s response times
- Ollama integration with multiple models (llama2, mistral)
- ChromaDB vector storage with multi-tenant isolation
- Document processing (PDF, DOCX, TXT)
- Conversation context management with Redis

### Channel Service (8004) ⚠️ WEBSOCKETS ONLY
- WebSocket connections functional
- Real-time messaging infrastructure
- Redis-backed connection management
- **NEEDED**: WhatsApp Business API integration
- **NEEDED**: Telegram Bot API support
- **NEEDED**: Embeddable web widget

## Development Priorities (Q1 2025)

### 1. Creator Hub Enhancement (CRITICAL)
- Knowledge Base Management System with document organization
- Visual Program Builder using React Flow for coaching workflows
- Analytics & Insights Dashboard with creator metrics
- User Management Interface for audience management

### 2. Multi-Channel Expansion (HIGH)
- WhatsApp Business API Integration with webhook handling
- Embeddable Web Widget with customizable themes
- Telegram Bot Support with Bot API integration
- Enhanced AI Conversation Engine with proactive triggers

### 3. Mobile Experience (MEDIUM)
- React Native "Compañero" App for end users
- Gamification System with points and achievements
- Push Notifications for coaching reminders
- Habit Tracking Features with progress visualization

## Technical Stack (OPERATIONAL)

### Backend Infrastructure
- **FastAPI** (Python 3.11+): 4 microservices with async/await patterns
- **PostgreSQL 15**: Multi-tenant database with RLS policies
- **Redis 7**: Caching, sessions, and message queues
- **Ollama + ChromaDB**: AI/ML infrastructure with vector storage
- **Docker + Nginx**: Production containers with API gateway

### Development Workflow
- **Testing**: pytest with 85%+ coverage requirement
- **Code Quality**: Black formatting + mandatory type hints
- **Database**: Alembic migrations with version control
- **Automation**: Make commands for common tasks

### Security Implementation
- **Authentication**: JWT with refresh tokens (RS256)
- **Multi-tenancy**: Row Level Security with creator_id isolation
- **Passwords**: Argon2 hashing with strength validation
- **Authorization**: RBAC with permission-based access
- **Compliance**: GDPR data protection features

## Implementation Guidelines

### When Adding New Features (MANDATORY CHECKLIST)
1. **Multi-tenant First**: Implement RLS policies and creator_id isolation
2. **Type Safety**: Add comprehensive type hints and Pydantic models
3. **Async Patterns**: Use async/await for ALL I/O operations
4. **Error Handling**: Use structured exceptions with proper HTTP codes
5. **Testing**: Achieve 90%+ test coverage with multi-tenant isolation
6. **Security**: Validate inputs, implement rate limiting, audit logging
7. **Performance**: Meet <2s API response time targets

### Database Operations Pattern
```python
# ALWAYS use this pattern for database operations
from shared.models.base import BaseTenantModel

class NewModel(BaseTenantModel):
    # All models MUST inherit from BaseTenantModel
    name: str
    # creator_id automatically included

# Repository pattern with RLS
async def create_record(session: AsyncSession, creator_id: str, data: dict):
    # RLS automatically filters by creator_id
    record = NewModel(creator_id=creator_id, **data)
    session.add(record)
    await session.commit()
    return record
```

### API Endpoint Pattern
```python
# Standard endpoint pattern with authentication and validation
@router.post("/endpoint", response_model=ResponseModel)
async def create_resource(
    data: RequestModel,
    creator_id: str = Depends(get_current_creator_id),
    session: AsyncSession = Depends(get_tenant_session)
) -> ResponseModel:
    # Implementation with automatic tenant isolation
    pass
```

## Performance Standards & Success Metrics

### Technical Requirements (ENFORCE)
- **API Response**: <2s (p95), AI Response: <5s (p95)
- **Test Coverage**: >90% for new code, >85% overall
- **Uptime**: 99.9% availability target
- **Concurrent Users**: Support 1,000+ creators, 10,000+ users

### Business Targets (2025)
- **Active Creators**: 1,000+ by Q4 2025
- **Platform Users**: 50,000+ engaged users
- **Revenue**: $100K MRR by end of 2025
- **Retention**: 85% creator, 70% user retention

## Quick Start Commands

### Development Setup
```bash
make setup          # Initial environment setup
make up             # Start all services
make test           # Run test suite (85%+ coverage)
make format         # Code formatting (Black + isort)
make lint           # Type checking and linting
make db-migrate     # Apply database migrations
```

### Service Health Checks
```bash
make health         # Check all service health
make {service}-logs # View individual service logs
make db-shell       # Access PostgreSQL
make redis-shell    # Access Redis CLI
```

## Key Architecture Documents

### Core Implementation
- **`mvp-architecture.md`**: Service architecture and patterns
- **`database-design.md`**: Multi-tenant database design with RLS
- **`tech.md`**: Technology stack and development standards

### Specialized Patterns
- **`ai-ml-integration.md`**: RAG pipeline and Ollama/ChromaDB integration
- **`security-patterns.md`**: Authentication, authorization, and data protection
- **`websocket-realtime.md`**: Real-time communication patterns
- **`shared-models.md`**: Pydantic models and data structures
- **`api-design.md`**: REST API design and documentation standards

This steering document provides essential guidance for AI assistants working with the multi-channel coaching platform codebase.