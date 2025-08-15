---
inclusion: always
---

# API Endpoints Implementation Guide

## Service Architecture Overview

### Auth Service (Port 8001) ✅ PRODUCTION READY
**Base URL**: `http://localhost:8001`
**Pattern**: JWT + Multi-tenant + RBAC + GDPR

#### Core Endpoints (IMPLEMENTED)
- `GET /health` - Liveness probe
- `GET /ready` - Readiness probe with dependency validation
- `POST /api/v1/auth/register` - Creator registration with validation
- `POST /api/v1/auth/login` - JWT authentication with rate limiting
- `POST /api/v1/auth/refresh` - Token refresh with rotation
- `GET /api/v1/auth/me` - Current creator profile
- `POST /api/v1/auth/logout` - Session termination

#### Security Features (IMPLEMENTED)
- `POST /api/v1/auth/password/validate` - Password strength validation
- `POST /api/v1/auth/password/reset/request` - Password reset flow
- `POST /api/v1/auth/password/reset/confirm` - Password reset confirmation
- `POST /api/v1/auth/tokens/revoke` - JWT token revocation
- `POST /api/v1/auth/keys/rotate` - JWT key rotation

#### GDPR Compliance (IMPLEMENTED)
- `POST /api/v1/auth/gdpr/data-deletion` - Data deletion request
- `GET /api/v1/auth/gdpr/data-export` - User data export

---

### Creator Hub Service (Port 8002) ⚠️ FOUNDATION ONLY
**Base URL**: `http://localhost:8002`
**Pattern**: Content Management + Program Builder + Analytics

#### Health Endpoints (IMPLEMENTED)
- `GET /health` - Service health check
- `GET /ready` - Dependency validation check

#### Creator Management (� PRIORITtY Q1 2025)
- `GET /api/v1/creators/profile` - Creator profile retrieval
- `PUT /api/v1/creators/profile` - Profile updates
- `GET /api/v1/creators/dashboard/metrics` - Analytics dashboard

#### Knowledge Base Management (� CeRITICAL PRIORITY)
- `POST /api/v1/creators/knowledge/upload` - Document upload with processing
- `GET /api/v1/creators/knowledge/documents` - Document listing with pagination
- `DELETE /api/v1/creators/knowledge/documents/{doc_id}` - Document deletion
- `GET /api/v1/creators/knowledge/search` - Knowledge base search

#### Widget Configuration (🔄 HIGH PRIORITY)
- `GET /api/v1/creators/widget/config` - Widget configuration retrieval
- `PUT /api/v1/creators/widget/config` - Configuration updates
- `GET /api/v1/creators/widget/embed-code` - Embed code generation

#### Program Builder (🔄 CRITICAL PRIORITY)
- `POST /api/v1/creators/programs` - Create coaching program
- `GET /api/v1/creators/programs` - List programs
- `PUT /api/v1/creators/programs/{program_id}` - Update program
- `POST /api/v1/creators/programs/{program_id}/publish` - Publish program

---

### AI Engine Service (Port 8003) ✅ RAG PRODUCTION READY
**Base URL**: `http://localhost:8003`
**Pattern**: RAG Pipeline + Multi-tenant Vector Storage + Ollama Integration

#### Health & Monitoring (IMPLEMENTED)
- `GET /health` - Service health with dependency checks
- `GET /ready` - Readiness with AI model validation
- `GET /api/v1/ai/pipeline/performance` - RAG pipeline metrics

#### Core AI Operations (IMPLEMENTED)
- `POST /api/v1/ai/conversations` - RAG-powered conversation processing
- `GET /api/v1/ai/conversations/{conversation_id}/context` - Context retrieval
- `POST /api/v1/ai/documents/process` - Document embedding generation
- `POST /api/v1/ai/documents/search` - Semantic search in knowledge base

#### Model Management (IMPLEMENTED)
- `GET /api/v1/ai/models/status` - AI model availability status
- `POST /api/v1/ai/models/reload` - Model reloading and health check
- `GET /api/v1/ai/ollama/health` - Ollama service status
- `POST /api/v1/ai/ollama/test-embedding` - Embedding generation test
- `POST /api/v1/ai/ollama/test-chat` - Chat completion test

#### Vector Storage Management (IMPLEMENTED)
- `GET /api/v1/ai/chromadb/health` - ChromaDB connectivity status
- `GET /api/v1/ai/chromadb/stats` - Collection statistics
- `GET /api/v1/ai/embeddings/stats/{creator_id}` - Creator embedding stats

#### Cache Management (IMPLEMENTED)
- `DELETE /api/v1/ai/cache/{creator_id}/document/{document_id}` - Cache invalidation
- `POST /api/v1/ai/cache/{creator_id}/warm` - Cache warming for searches

---

### Channel Service (Port 8004) ⚠️ WEBSOCKETS FOUNDATION
**Base URL**: `http://localhost:8004`
**Pattern**: Multi-channel Communication + Real-time Messaging

#### Health & Monitoring (IMPLEMENTED)
- `GET /health` - Service health check
- `GET /ready` - WebSocket infrastructure readiness
- `GET /api/v1/channels/connections` - Active WebSocket connections

#### WebSocket Communication (IMPLEMENTED)
- `WS /api/v1/channels/widget/{creator_id}/connect` - Authenticated WebSocket connection
- **Authentication**: Token-based WebSocket auth with creator isolation
- **Message Types**: user_message, ai_response, typing_indicator, connection_status

#### Session Management (🔄 Q1 2025 PRIORITY)
- `POST /api/v1/channels/sessions` - User session creation
- `GET /api/v1/channels/sessions/{session_id}` - Session information retrieval
- `PUT /api/v1/channels/sessions/{session_id}` - Session updates

#### Multi-Channel Support (🔄 CRITICAL Q1 2025)
- `POST /api/v1/channels/whatsapp/webhook` - WhatsApp Business API webhook
- `POST /api/v1/channels/telegram/webhook` - Telegram Bot API webhook
- `GET /api/v1/channels/widget/embed/{creator_id}` - Widget embed code

---

## Implementation Status & Development Priorities

### ✅ Production Ready Services
- **Auth Service**: Complete JWT + RBAC + GDPR implementation
- **AI Engine Service**: Full RAG pipeline with Ollama + ChromaDB integration
- **Database Layer**: Multi-tenant RLS policies with async SQLAlchemy

### ⚠️ Foundation Services (Require Enhancement)
- **Creator Hub Service**: Basic structure, needs content management features
- **Channel Service**: WebSocket foundation, needs multi-channel expansion

### 🔄 Q1 2025 Development Priorities
1. **Creator Hub Enhancement** (CRITICAL): Knowledge base management, program builder
2. **Multi-Channel Expansion** (HIGH): WhatsApp, Telegram, web widget integration
3. **Advanced AI Features** (MEDIUM): Proactive engagement, personality consistency

---

## Authentication & Authorization Patterns

### JWT Token Structure (MANDATORY)
```json
{
  "sub": "creator_id",
  "creator_id": "uuid",
  "tenant_id": "uuid",
  "permissions": ["read", "write", "admin"],
  "subscription_tier": "free|pro|enterprise",
  "aud": "coaching-platform",
  "iss": "auth-service",
  "exp": 1234567890,
  "iat": 1234567890
}
```

### Required Headers (ENFORCE)
```
Authorization: Bearer <jwt_token>
Content-Type: application/json
Accept: application/json
X-Request-ID: <uuid> (optional for tracing)
```

### Multi-Tenant Context (CRITICAL)
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

### Rate Limiting (IMPLEMENTED)
- **Auth endpoints**: 10 requests/minute (brute force protection)
- **File uploads**: 5 requests/minute (resource protection)
- **Chat messages**: 100 requests/minute (conversation flow)
- **Search queries**: 50 requests/minute (AI resource management)
- **Default**: 30 requests/minute (general API protection)

---

## Core Data Models & Patterns

### Base Model Requirements (MANDATORY)
```python
# ALL models MUST inherit from BaseTenantModel
class BaseTenantModel(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    creator_id: UUID  # REQUIRED for multi-tenancy
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
```

### Creator Model (IMPLEMENTED)
```json
{
  "id": "uuid",
  "email": "string",
  "full_name": "string",
  "company_name": "string",
  "subscription_tier": "free|pro|enterprise",
  "is_active": true,
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z"
}
```

### Conversation Model (IMPLEMENTED)
```json
{
  "id": "uuid",
  "creator_id": "uuid",
  "user_session_id": "uuid",
  "channel": "widget|whatsapp|telegram",
  "status": "active|completed|archived",
  "context": {},
  "metadata": {},
  "created_at": "2024-01-01T00:00:00Z"
}
```

### AI Response Model (IMPLEMENTED)
```json
{
  "response": "string",
  "conversation_id": "uuid",
  "confidence": 0.85,
  "processing_time_ms": 1500,
  "model_used": "llama2:7b-chat",
  "sources_count": 3,
  "sources": [
    {
      "content": "string",
      "metadata": {},
      "similarity_score": 0.92
    }
  ]
}
```

### Document Processing Result (IMPLEMENTED)
```json
{
  "document_id": "string",
  "status": "pending|processing|completed|failed",
  "total_chunks": 0,
  "processing_time_seconds": 0.0,
  "filename": "string",
  "error_message": "string",
  "metadata": {
    "file_size": 0,
    "mime_type": "string",
    "chunk_count": 0
  }
}
```

---

## HTTP Status Codes & Error Handling

### Success Responses (USE APPROPRIATELY)
- `200 OK` - Successful request with response body
- `201 Created` - Resource created successfully
- `202 Accepted` - Request accepted for async processing
- `204 No Content` - Successful operation without response body

### Client Error Responses (IMPLEMENT CONSISTENTLY)
- `400 Bad Request` - Malformed request or invalid parameters
- `401 Unauthorized` - Authentication required or invalid token
- `403 Forbidden` - Insufficient permissions for resource
- `404 Not Found` - Resource not found or not accessible
- `409 Conflict` - Resource conflict (duplicate email, etc.)
- `422 Unprocessable Entity` - Validation errors with details
- `429 Too Many Requests` - Rate limit exceeded with retry headers

### Server Error Responses (HANDLE GRACEFULLY)
- `500 Internal Server Error` - Unexpected server error
- `503 Service Unavailable` - Service temporarily unavailable

### Error Response Format (MANDATORY)
```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human readable message",
    "details": {},
    "timestamp": "2024-01-01T00:00:00Z",
    "request_id": "uuid"
  }
}
```

---

## API Documentation & Development Tools

### OpenAPI Documentation (AVAILABLE)
- Auth Service: `http://localhost:8001/docs`
- Creator Hub: `http://localhost:8002/docs`
- AI Engine: `http://localhost:8003/docs`
- Channel Service: `http://localhost:8004/docs`

### Postman Collections (MAINTAINED)
- Located in `test_endpoints/postman/`
- Environment configs in `test_endpoints/environments/`
- **Usage**: Import collections for API testing and development

---

## Monitoring & Observability Patterns

### Health Check Requirements (MANDATORY)
All services MUST implement:
- `GET /health` - Liveness probe (always 200 if running)
- `GET /ready` - Readiness probe with dependency validation

### Structured Logging (ENFORCE)
```json
{
  "timestamp": "2024-01-01T00:00:00Z",
  "level": "INFO",
  "service": "service-name",
  "request_id": "uuid",
  "creator_id": "uuid",
  "message": "Event description",
  "metadata": {}
}
```

### Performance Metrics (TRACK)
- **Response Times**: p50, p95, p99 for all endpoints
- **Request Rates**: Per endpoint and per creator
- **Error Rates**: By service and error type
- **AI Performance**: Model response times, confidence scores
- **Database Performance**: Query times, connection pool usage
- **WebSocket Metrics**: Active connections, message throughput

### Development Commands (USE)
```bash
make health         # Check all service health
make {service}-logs # View individual service logs
make test           # Run test suite with coverage
make format         # Code formatting and linting
```