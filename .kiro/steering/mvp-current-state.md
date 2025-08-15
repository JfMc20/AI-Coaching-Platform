---
inclusion: always
---

# MVP Development Guidelines

## Platform Status: Production-Ready MVP ✅

Multi-channel proactive coaching platform with functional microservices, complete infrastructure, and operational AI capabilities. Ready for scaling and advanced feature development.

## Core Development Principles

### Architecture Standards (MANDATORY)
- **Multi-Tenant First**: ALL database operations MUST use Row Level Security (RLS)
- **Async Patterns**: Use `async/await` for ALL I/O operations (DB, Redis, HTTP)
- **Type Safety**: Mandatory type hints for all function parameters and return values
- **Pydantic Models**: Required for ALL request/response validation
- **Service Isolation**: Each service maintains independent FastAPI applications

### Code Quality Requirements (ENFORCED)
- **Test Coverage**: Minimum 85% existing, 90% new features
- **Error Handling**: Use shared exception classes from `shared.exceptions`
- **Security First**: JWT authentication, input validation, rate limiting
- **Performance**: <2s API response times, Redis caching for AI responses

## Service Implementation Patterns

### Auth Service (Port 8001) ✅ PRODUCTION READY
**Pattern**: JWT + Multi-tenant + RBAC

**REQUIRED Authentication Flow:**
```python
from shared.models.auth import CreatorCreate, TokenResponse
from shared.security.jwt_manager import JWTManager

# Multi-tenant context - MANDATORY for all operations
async def get_tenant_session(
    creator_id: str = Depends(get_current_creator_id),
    session: AsyncSession = Depends(get_db_session)
) -> AsyncSession:
    await database_manager.set_tenant_context(session, creator_id)
    return session
```

**Service Structure (FOLLOW):**
```
services/{service-name}/app/
├── routes/           # FastAPI endpoints
├── services/         # Business logic layer  
├── dependencies/     # FastAPI dependencies
├── models/          # Service-specific models
└── database.py      # DB connection management
```

**Standard Endpoints:**
- `POST /api/v1/auth/register` - Creator registration
- `POST /api/v1/auth/login` - JWT authentication  
- `POST /api/v1/auth/refresh` - Token refresh
- `GET /api/v1/auth/me` - Current user profile

### Creator Hub Service (Port 8002) ⚠️ FOUNDATION ONLY
**Pattern**: Content Management + Program Builder + Analytics

**Basic Structure (EXTEND for new features):**
```python
from fastapi import FastAPI, Depends
from shared.models.auth import get_current_creator_id
from shared.database import get_tenant_session

app = FastAPI(title="Creator Hub Service")

@app.get("/api/v1/creators/health")
async def health_check():
    return {"status": "healthy", "service": "creator-hub"}
```

**Q1 2025 Priorities:**
1. Knowledge Base Management - Document upload/processing
2. Visual Program Builder - React Flow workflows  
3. Analytics Dashboard - Creator insights
4. Content Management - Advanced organization

### AI Engine Service (Port 8003) ✅ RAG PRODUCTION READY
**Pattern**: RAG Pipeline + Multi-tenant Vector Storage + Ollama Integration

**RAG Pipeline (USE this pattern):**
```python
class RAGPipeline:
    async def process_query(self, query: str, creator_id: str, conversation_id: str) -> AIResponse:
        # 1. Retrieve conversation context
        context = await self.conversation_manager.get_context(conversation_id)
        # 2. Search relevant knowledge (ChromaDB)
        chunks = await self.retrieve_knowledge(query, creator_id)
        # 3. Generate response (Ollama)
        response = await self.ollama_client.generate_chat_completion(
            self.build_prompt(query, context, chunks)
        )
        return AIResponse(response=response, sources=chunks)
```

**Multi-tenant Collections (MANDATORY):**
```python
# ALWAYS use creator-specific collections
collection_name = f"creator_{creator_id}_knowledge"
await chroma_client.get_or_create_collection(collection_name)
```

**Performance Standards:**
- Response time: <5s for RAG queries
- Chunk size: 1000 tokens with 200 overlap  
- Context window: 4000 tokens maximum
- Models: llama2:7b-chat, nomic-embed-text

### Channel Service (Port 8004) ⚠️ WEBSOCKETS FOUNDATION
**Pattern**: Multi-channel Communication + Real-time Messaging

**WebSocket Pattern (USE for real-time features):**
```python
@app.websocket("/api/v1/channels/widget/{creator_id}/connect")
async def websocket_endpoint(websocket: WebSocket, creator_id: str, token: str = Query(...)):
    # 1. Authenticate connection
    auth_claims = await validate_websocket_token(token)
    # 2. Establish connection  
    await websocket_manager.connect(websocket, creator_id, session_id)
    # 3. Message handling loop
    while True:
        data = await websocket.receive_text()
        await message_processor.process_user_message(
            websocket, json.loads(data), creator_id, session_id
        )
```

**Channel Abstraction (EXTEND for new channels):**
```python
class ChannelHandler(ABC):
    @abstractmethod
    async def send_message(self, recipient: str, message: Dict) -> bool: pass
    @abstractmethod  
    async def receive_message(self, raw_message: Any) -> Optional[Dict]: pass

# Register handlers
channel_router.register_handler("widget", WebWidgetHandler())
```

**Q1 2025 Priorities:**
1. WhatsApp Business API - Official integration
2. Web Widget - Embeddable chat interface
3. Telegram Bot - Bot API integration
4. Enhanced WebSocket - Health monitoring

## Infrastructure Patterns

### Docker Standards ✅ PRODUCTION OPTIMIZED
**Multi-stage builds + Health checks (FOLLOW):**
```dockerfile
FROM python:3.11-slim as builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

FROM python:3.11-slim as runtime
WORKDIR /app
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY . .
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Service Architecture (MAINTAIN):**
- auth-service (8001) - JWT + Multi-tenant
- creator-hub (8002) - Content management  
- ai-engine (8003) - RAG + Ollama + ChromaDB
- channel-service (8004) - WebSockets + Multi-channel
- postgres - PostgreSQL 15 + RLS policies
- redis - Cache + Sessions + Message queues
- chromadb - Vector storage + Multi-tenant collections
- ollama - LLM serving + Model management
- nginx - API Gateway + Load balancing

**Development Commands (USE):**
```bash
make setup          # Environment setup
make up             # Start all services
make test           # Run test suite (85%+ coverage)
make format         # Code formatting (Black + isort)
make lint           # Linting checks (mypy + flake8)
make db-migrate     # Database migrations
```

### Database Architecture ✅ MULTI-TENANT RLS ENFORCED
**Pattern**: Row Level Security + Tenant Context + Async Sessions

**Multi-tenant Pattern (MANDATORY for all queries):**
```python
# ALWAYS use tenant context
async def get_tenant_session(
    creator_id: str = Depends(get_current_creator_id),
    session: AsyncSession = Depends(get_db_session)
) -> AsyncSession:
    # Set tenant context for RLS policies
    await session.execute(
        text("SET app.cur = Depends(get_db_session)
) -> AsyncSession:
    await session.execute(
        text("SET app.current_creator_id = :creator_id"),
        {"creator_id": creator_id}
    )
    return session

# RLS automatically filters by creator_id
async def get_user_conversations(session: AsyncSession):
    result = await session.execute(select(Conversation))
    return result.scalars().all()
```

**Base Model (ALL models MUST inherit):**
```python
class BaseTenantModel(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    creator_id: UUID  # REQUIRED for multi-tenancy
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
```

**RLS Policy (APPLY to all tenant tables):**
```sql
ALTER TABLE table_name ENABLE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON table_name FOR ALL TO authenticated_user
USING (creator_id = current_setting('app.current_creator_id')::UUID);
```
### Redis & Caching ✅ MULTI-TENANT
**Pattern**: Tenant-isolated keys + Rate limiting + Message queues

**Redis Key Patterns (MANDATORY tenant isolation):**
```python
# ALWAYS use tenant isolation
def get_tenant_key(creator_id: str, key_type: str, identifier: str) -> str:
    return f"{key_type}:creator_{creator_id}:{identifier}"

# Examples
conversation_key = f"conversation:creator_{creator_id}:{conversation_id}:messages"
rate_limit_key = f"rate_limit:creator_{creator_id}:chat:{session_id}"
cache_key = f"ai_response:creator_{creator_id}:{query_hash}"
```

**Rate Limiting (USE for all endpoints):**
```python
async def check_rate_limit(creator_id: str, endpoint_type: str, session_id: str) -> Tuple[bool, Dict]:
    key = f"rate_limit:creator_{creator_id}:{endpoint_type}:{session_id}"
    allowed, info = await rate_limiter.check_rate_limit(key, limits)
    return allowed, info
```

### AI/ML Infrastructure ✅ RAG PRODUCTION PIPELINE
**Pattern**: Ollama + ChromaDB + Multi-tenant Vector Storage

**Ollama Client (STANDARD implementation):**
```python
class OllamaClient:
    async def generate_chat_completion(self, prompt: str, model: str = "llama2:7b-chat") -> str:
        for attempt in range(3):
            try:
                response = await self._make_request("/api/generate", {
                    "model": model, "prompt": prompt,
                    "options": {"temperature": 0.7, "num_predict": 1000}
                })
                return response["response"]
            except Exception as e:
                if attempt == 2: raise AIEngineError(f"LLM failed: {e}")
                await asyncio.sleep(2 ** attempt)
```

**ChromaDB Multi-tenant (MANDATORY):**
```python
# ALWAYS use creator-specific collections
collection_name = f"creator_{creator_id}_knowledge"
await chroma_client.get_or_create_collection(collection_name)
```

**Performance Standards:**
- RAG response: <5s, Document processing: <30s
- Chunk size: 1000 tokens, overlap: 200 tokens
- Models: llama2:7b-chat, nomic-embed-text

## Testing Standards ✅ 85%+ COVERAGE ENFORCED

**Test Structure (FOLLOW):**
```python
# Multi-tenant test pattern - USE for all database tests
@pytest.fixture
async def tenant_session(db_session):
    creator_id = "test-creator-123"
    await db_session.execute(text("SET app.current_creator_id = :creator_id"), {"creator_id": creator_id})
    return db_session, creator_id

@pytest.mark.asyncio
async def test_create_conversation(tenant_session):
    session, creator_id = tenant_session
    conversation = await create_conversation(session, creator_id, "test-session")
    assert conversation.creator_id == creator_id
```

**Quality Gates (MANDATORY for PRs):**
- Unit test coverage: >90% for new code
- Integration test coverage: >80% for service interactions  
- Performance tests: All endpoints <2s response time
- Multi-tenant isolation: Verify RLS policy enforcement

## Security Implementation ✅ ENTERPRISE GRADE

**Authentication Pattern (MANDATORY for all endpoints):**
```python
# JWT authentication - USE for all protected endpoints
async def get_current_creator_id(token: str = Depends(HTTPBearer())) -> str:
    try:
        payload = jwt_manager.verify_token(token.credentials)
        return payload["creator_id"]
    except Exception:
        raise HTTPException(401, "Invalid authentication")

# Input validation - MANDATORY for all user inputs
validator = InputValidator()
sanitized_content = validator.sanitize_html(user_content)
safe_filename = validator.sanitize_filename(uploaded_file.filename)

# Rate limiting - REQUIRED for all API endpoints
allowed, info = await rate_limiter.check_rate_limit(creator_id, "endpoint_type", session_id)
if not allowed:
    raise HTTPException(429, "Rate limit exceeded")
```

**Multi-Tenant Security (CRITICAL):**
- Database: RLS policies enforce creator_id filtering
- Application: JWT tokens contain creator_id for context
- API: All endpoints validate tenant access
- Storage: File uploads isolated by creator_id
- Cache: Redis keys prefixed with creator_id

## Development Standards ✅ ENFORCED

**Code Quality (MANDATORY):**
```python
# Type hints - REQUIRED for all functions
async def process_document(document: UploadFile, creator_id: str, session: AsyncSession) -> ProcessingResult:
    """Process uploaded document with proper typing."""
    pass

# Pydantic models - MANDATORY for all API endpoints
class DocumentUploadRequest(BaseModel):
    filename: str = Field(..., min_length=1, max_length=255)
    content_type: str = Field(..., regex=r'^(application|text)/')

# Error handling - STANDARD exception patterns
from shared.exceptions.base import APIError
try:
    result = await process_document(file, creator_id, session)
except Exception as e:
    logger.exception(f"Document processing failed: {e}")
    raise DocumentProcessingError(f"Processing failed: {str(e)}")
```

**Requirements (ENFORCE in PRs):**
- Type Coverage: 95%+ type hints (mypy validation)
- Code Formatting: Black + isort (automated)
- Async Patterns: async/await for ALL I/O operations
- Error Handling: Structured exceptions with proper HTTP codes

## Q1 2025 Development Priorities

### 1. Creator Hub Enhancement (Month 1-2) 🔴 CRITICAL
**Pattern**: Content Management + Visual Builder + Analytics

**Document Management:**
```python
class DocumentManager:
    async def upload_document(self, file: UploadFile, creator_id: str, metadata: Dict) -> ProcessingResult:
        # 1. Validate file, 2. Store with tenant isolation, 3. Process with AI Engine
        file_path = f"uploads/creator_{creator_id}/{safe_filename}"
        processing_result = await self.ai_engine.process_document(file_path, creator_id)
        return ProcessingResult(document_id=document.id, status="processing")
```

### 2. Multi-Channel Expansion (Month 2-3) 🔴 CRITICAL
**Pattern**: Channel abstraction + Webhook handling

**WhatsApp Integration:**
```python
class WhatsAppHandler(ChannelHandler):
    async def send_message(self, recipient: str, message: Dict) -> bool:
        response = await self.whatsapp_client.send_message(to=recipient, type="text", text={"body": message["content"]})
        return response.status_code == 200
```

### 3. Enhanced AI Capabilities (Month 3-4) 🟡 HIGH PRIORITY
**Pattern**: Proactive engagement + Context management

### 4. Mobile Application (Month 4-5) 🟡 HIGH PRIORITY  
**Pattern**: React Native + Push notifications + Offline sync

## Performance Standards & Success Metrics

**Performance Targets (ENFORCE):**
- API response: <2s (p95), AI response: <5s (p95)
- Test coverage: >90% new code, >80% integration
- Uptime: 99.9%, Concurrent users: 1000/service

**Health Check Pattern (MANDATORY for all services):**
```python
@app.get("/health")
async def health_check():
    checks = {"database": await database_manager.health_check(), "redis": await redis_client.ping()}
    all_healthy = all(checks.values())
    return JSONResponse(status_code=200 if all_healthy else 503, content={"status": "healthy" if all_healthy else "unhealthy", "checks": checks})
```

**Business Targets 2025:**
- Active creators: 1,000, Platform users: 50,000
- Monthly recurring revenue: $100K USD
- Creator retention: 85%, User retention: 70%

## Implementation Checklist

**When Adding New Features (FOLLOW):**
1. Multi-tenant First: Ensure RLS policies and creator_id isolation
2. Type Safety: Add comprehensive type hints and Pydantic models  
3. Async Patterns: Use async/await for all I/O operations
4. Error Handling: Implement structured exceptions with proper HTTP codes
5. Testing: Achieve 90%+ test coverage with multi-tenant test isolation
6. Security: Validate inputs, implement rate limiting, audit logging
7. Performance: Meet <2s API response time targets

**Architecture Principles (MAINTAIN):**
- Service Isolation: Independent FastAPI applications
- Database Multi-tenancy: All queries filtered by creator_id through RLS
- Caching Strategy: Redis with tenant-isolated keys
- AI Integration: RAG pipeline with ChromaDB multi-tenant collections
- Real-time Communication: WebSocket connections with proper authentication