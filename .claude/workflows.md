# Development Workflows for Maximum Production

## 🚀 Quick Start Workflow
```bash
# Daily development
make setup    # First time only
make up       # Start services
make health   # Verify everything running
```

## 🧪 Testing Workflow (MANDATORY)
```bash
# Before any commit
make format && make lint      # Code quality
make test-coverage           # Run tests with coverage
make up && make health       # Verify services healthy
```

## 🔧 Service Development Pattern

### 1. Adding New Endpoint
1. **Check existing patterns** in similar services
2. **Use multi-tenant session**: `get_tenant_session`
3. **Add authentication**: `get_current_user`
4. **Write tests FIRST** (TDD approach)
5. **Test endpoint manually**
6. **Check coverage**: aim for 90%+

### 2. Database Changes
1. **Create migration**: `make db-create-migration`
2. **Review generated migration**
3. **Apply**: `make db-migrate`
4. **Test with multi-tenant data**
5. **Verify RLS policies maintained**

### 3. Multi-Channel Features
1. **Start with Channel Service** (`services/channel-service/`)
2. **Use WebSocket foundation** (already implemented)
3. **Follow channel abstraction pattern**
4. **Test across different channels**

## 🎯 Priority-Based Development

### CRITICAL: Creator Hub Enhancement
- **Focus**: `services/creator-hub-service/app/main.py`
- **Features**: Knowledge management, program builder, analytics
- **Pattern**: Use existing auth and database patterns

### HIGH: Multi-Channel Expansion  
- **Focus**: `services/channel-service/app/main.py`
- **Features**: WhatsApp integration, enhanced AI conversation
- **Pattern**: Extend existing channel handlers

### HIGH: Visual Testing Service
- **Create**: `services/testing-service/` (Port 8005)
- **Features**: Personality trainer, debugging tools
- **Pattern**: New service following existing architecture

## 🔍 Debugging Workflow
```bash
# Service-specific debugging
make ai-engine-logs     # AI engine issues
make auth-logs         # Authentication issues
make postgres-logs     # Database issues

# Container issues
docker-compose ps                    # Check status
docker-compose build --no-cache SERVICE  # Rebuild specific service
```

## 📊 Performance Monitoring
- **API Response Time**: Target <2s (p95)
- **AI Response Time**: Target <5s (p95)  
- **Database Queries**: Target <100ms (p95)
- **Test Coverage**: Require 90%+ for new features

## 🚨 Common Issues & Solutions

### Multi-Tenant Data Leak
```python
# ❌ WRONG - no tenant isolation
result = await session.execute(select(Document))

# ✅ CORRECT - tenant isolation enforced
session = await get_tenant_session(creator_id, session)
result = await session.execute(select(Document))
```

### Missing Authentication
```python
# ❌ WRONG - no authentication
@app.post("/api/v1/endpoint")
async def endpoint(request: RequestModel):

# ✅ CORRECT - authentication required
@app.post("/api/v1/endpoint")
async def endpoint(
    request: RequestModel,
    current_user: UserContext = Depends(get_current_user)
):
```

### Blocking I/O
```python
# ❌ WRONG - blocking operations
def process_file(file):
    result = requests.post("/api/endpoint")
    return result

# ✅ CORRECT - async operations
async def process_file(file):
    async with httpx.AsyncClient() as client:
        result = await client.post("/api/endpoint")
    return result
```