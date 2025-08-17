# Project Context for Claude Code

## Quick Project Overview
Multi-Channel AI Coaching Platform - Creates digital twins of creators through advanced RAG + personality synthesis.

## Current State
- **MVP Status**: Production Ready ✅
- **Services Ready**: Auth (8001), AI Engine (8003), Infrastructure
- **Needs Enhancement**: Creator Hub (8002), Channel Service (8004)

## Critical Development Patterns

### Multi-Tenant Database (MANDATORY)
```python
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

### Security Pattern (ENFORCE)
```python
@app.post("/api/v1/endpoint")
async def endpoint(
    request: RequestModel,
    current_user: UserContext = Depends(get_current_user),
    session: AsyncSession = Depends(get_tenant_session),
):
    # Implementation
```

## Performance Targets
- API responses: <2s (p95)
- AI responses: <5s (p95)
- Database queries: <100ms (p95)
- Test coverage: 90%+ for new features

## Q1 2025 Priorities
1. **Creator Hub Enhancement** (CRITICAL) - Content management, visual program builder
2. **Multi-Channel Expansion** (HIGH) - WhatsApp, enhanced AI conversation
3. **Visual Testing Service** (HIGH) - Creator personality trainer, debugging tools

## Key Commands
- `make setup && make up` - Environment setup
- `make health` - Check all services
- `make test-coverage` - Run tests with coverage
- `make db-migrate` - Apply database migrations

## Never Do
- ❌ Hardcode environment variables
- ❌ Use blocking I/O (no async/await)
- ❌ Skip authentication on protected endpoints
- ❌ Allow cross-tenant data leaks
- ❌ Commit without tests