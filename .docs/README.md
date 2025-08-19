# Multi-Channel AI Coaching Platform - Documentation

This directory contains comprehensive documentation for Claude Code development on the Multi-Channel AI Coaching Platform.

## 📚 Documentation Structure

### 🏗️ Architecture Documentation
- **[Microservices Architecture](architecture/microservices.md)** - Service overview, ports, and responsibilities
- **[Data Layer Design](architecture/data-layer.md)** - Database design, caching, and vector storage
- **[Security Implementation](architecture/security.md)** - Authentication, authorization, and compliance

### 🛠️ Development Guides
- **[Quick Start Guide](development/quick-start.md)** - Essential commands and workflows
- **[Development Patterns](development/patterns.md)** - Multi-tenant patterns, async patterns, and best practices
- **[Database Management](development/database-management.md)** - Migration system and database operations

### 📋 Specifications
- **[Creator Personality System](specs/personality-system.md)** - Core innovation for digital twin creation
- **[Q1 2025 Priorities](specs/q1-2025-priorities.md)** - Development roadmap and priorities

### 🎯 System Implementation Guides
- **[Knowledge Service](guides/KNOWLEDGE_SERVICE_DOCS.md)** - PHASE 1: AI Engine integration and document processing
- **[Personality System](guides/PERSONALITY_SYSTEM_DOCS.md)** - PHASE 2: Creator digital twin and personality synthesis  
- **[Visual Program Builder](guides/VISUAL_PROGRAM_BUILDER_DOCS.md)** - PHASE 3: Automated coaching program creation

## 🎯 Quick Navigation

### For New Developers
1. Start with [Quick Start Guide](development/quick-start.md)
2. Review [Development Patterns](development/patterns.md)
3. Understand [Microservices Architecture](architecture/microservices.md)

### For Architecture Understanding
1. [Microservices Overview](architecture/microservices.md)
2. [Data Layer Design](architecture/data-layer.md)
3. [Security Implementation](architecture/security.md)

### For Feature Development
1. [Q1 2025 Priorities](specs/q1-2025-priorities.md)
2. [Creator Personality System](specs/personality-system.md)
3. [Development Patterns](development/patterns.md)

## 🚀 Project Status Summary

### ✅ Production Ready (85%+ coverage)
- **Auth Service (8001)**: JWT + RBAC + GDPR + Multi-tenant
- **AI Engine Service (8003)**: RAG pipeline + Ollama + ChromaDB
- **Infrastructure**: PostgreSQL + Redis + ChromaDB + Ollama

### ✅ Enhanced Production Ready  
- **Creator Hub Service (8002)**: Content management + **Visual Program Builder** + Multi-phase integration
- **Channel Service (8004)**: WebSocket + Multi-channel expansion

### 🚧 Future Implementation
- **Testing Service (8005)**: Visual debugging + AI Twin training

## 🎨 Core Innovation: Creator Digital Twin

The platform's unique value proposition lies in creating authentic digital twins of creators:

- **Personality Synthesis**: AI learns creator's voice and methodology (PHASE 2)
- **Knowledge Integration**: RAG-powered content from creator materials (PHASE 1)
- **Program Orchestration**: Visual coaching workflow builder (PHASE 3)
- **Proactive Engagement**: Behavior-triggered conversations
- **Multi-Channel Presence**: 24/7 availability across platforms

See [Creator Personality System](specs/personality-system.md) for complete specifications.

## 🔧 Development Guidelines

### Critical Requirements
1. **Multi-tenant First**: All database operations must use RLS
2. **Async Patterns**: Mandatory async/await for all I/O
3. **Security**: JWT authentication on all protected endpoints
4. **Testing**: 90%+ coverage for new features

### Common Patterns
```python
# Multi-tenant database session
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

See [Development Patterns](development/patterns.md) for complete guidelines.

## 📊 Performance Targets

- **API Responses**: <2s (p95)
- **AI Responses**: <5s (p95)
- **Database Queries**: <100ms (p95)
- **Scale**: 1,000+ creators, 10,000+ users
- **Coverage**: 85%+ existing, 90%+ new features

## 🔗 Quick Links

- **Main Configuration**: `CLAUDE.md` (project root)
- **Environment Setup**: `make setup && make up`
- **Service Health**: `make health`
- **Test Suite**: `make test`
- **Code Quality**: `make format && make lint`

---

**🚀 This documentation is optimized for Claude Code development workflows and provides comprehensive guidance for building the Multi-Channel AI Coaching Platform.**