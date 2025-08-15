---
inclusion: always
---

# MVP Architecture Guidelines - Updated Estado Funcional

## Core Architecture Principles

### Multi-Tenancy First Design ✅ IMPLEMENTED
- **Row Level Security (RLS)**: All PostgreSQL tables HAVE RLS policies implemented for creator isolation
- **Tenant Context**: Database queries include creator_id through set_config pattern
- **ChromaDB Collections**: Pattern `creator_{creator_id}_knowledge` IMPLEMENTED for vector storage isolation
- **Redis Keys**: Multi-tenant isolation IMPLEMENTED with creator-specific key prefixes

### Service Communication Patterns ✅ FUNCTIONAL
- **HTTP/JSON Communication**: Direct service-to-service communication via FastAPI
- **Redis Message Queues**: IMPLEMENTED for async processing and caching
- **WebSocket Support**: FUNCTIONAL real-time communication in Channel Service
- **Error Handling**: Consistent error responses across all services

### Data Flow Architecture ✅ IMPLEMENTED
```
Widget/Frontend → Nginx (API Gateway) → FastAPI Services → PostgreSQL/ChromaDB
                                              ↓
                                         Redis Cache → WebSocket Connections
```

## Service-Specific Guidelines - CURRENT IMPLEMENTATION STATUS

### Auth Service (Port 8001) ✅ PRODUCTION READY
- **JWT Management**: RS256 with refresh tokens IMPLEMENTED
- **Password Security**: Argon2 hashing IMPLEMENTED (upgraded from bcrypt)
- **Session Management**: Redis-based sessions FUNCTIONAL
- **Rate Limiting**: Per-IP and per-user limiting IMPLEMENTED
- **RBAC**: Role-based access control FUNCTIONAL
- **GDPR Compliance**: Data protection features IMPLEMENTED

### Creator Hub Service (Port 8002) ⚠️ BASIC STRUCTURE
- **Service Foundation**: FastAPI app with health checks IMPLEMENTED
- **Auth Integration**: JWT validation FUNCTIONAL
- **Document Processing**: PENDING - needs full implementation
- **Widget Configuration**: PENDING - basic structure only
- **Knowledge Base**: PENDING - integration with AI Engine needed

### AI Engine Service (Port 8003) ✅ RAG FUNCTIONAL
- **RAG Pipeline**: Retrieval-augmented generation IMPLEMENTED and FUNCTIONAL
- **Ollama Integration**: Local LLM serving FUNCTIONAL with multiple models
- **ChromaDB Management**: Per-tenant vector storage IMPLEMENTED
- **Document Processing**: PDF, DOCX, TXT processing FUNCTIONAL
- **Embedding Management**: Text embeddings with nomic-embed-text IMPLEMENTED
- **Context Management**: Conversation context handling IMPLEMENTED

### Channel Service (Port 8004) ⚠️ WEBSOCKETS ONLY
- **WebSocket Management**: Real-time connections IMPLEMENTED
- **Message Processing**: Basic async message handling FUNCTIONAL
- **Connection Management**: Redis-backed connection state IMPLEMENTED
- **Multi-Channel Support**: Structure ready, WhatsApp/Telegram PENDING

## Database Schema Requirements ✅ IMPLEMENTED

### Core Tables Structure ✅ FUNCTIONAL
```sql
-- All tables IMPLEMENT these fields
created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()  
creator_id UUID NOT NULL REFERENCES creators(id) ON DELETE CASCADE

-- RLS is ENABLED on all multi-tenant tables
ALTER TABLE table_name ENABLE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON table_name FOR ALL TO authenticated_user 
USING (creator_id = current_setting('app.current_tenant_id')::UUID);
```

### Current Database Status
- **Alembic Migrations**: FUNCTIONAL with version control
- **RLS Policies**: IMPLEMENTED on all relevant tables
- **Tenant Isolation**: VERIFIED and FUNCTIONAL
- **Multi-Tenant Indexes**: OPTIMIZED for performance
- **Connection Pooling**: CONFIGURED for async operations

## AI/ML Integration Patterns ✅ FULLY FUNCTIONAL

### ChromaDB Management ✅ PRODUCTION READY
- **Collection Naming**: `creator_{creator_id}_knowledge` IMPLEMENTED
- **Metadata Schema**: INCLUDES document_id, chunk_index, creator_id, source, created_at
- **Embedding Model**: `nomic-embed-text` CONSISTENTLY USED across all documents
- **Chunk Size**: 1000 tokens with 200 overlap CONFIGURED and OPTIMIZED
- **Multi-Tenant Isolation**: VERIFIED vector storage separation per creator

### Ollama Integration ✅ STABLE
- **Model Management**: Auto-pull and health checks IMPLEMENTED
- **Available Models**: llama2:7b-chat, mistral, nomic-embed-text READY
- **Error Handling**: Retry logic and fallback responses IMPLEMENTED
- **Context Management**: Conversation tracking and token limit handling FUNCTIONAL
- **Performance**: <5s response times achieved, Redis caching IMPLEMENTED

## Security Implementation ✅ PRODUCTION GRADE

### Authentication & Authorization ✅ ENTERPRISE READY
- **JWT Tokens**: INCLUDE creator_id, permissions, expiration - FUNCTIONAL
- **Refresh Tokens**: Token rotation and security IMPLEMENTED
- **Password Security**: Argon2 hashing with proper salting IMPLEMENTED
- **RBAC**: Role-based access control FUNCTIONAL
- **Rate Limiting**: Anti-brute force protection ACTIVE
- **CORS Configuration**: Secure origin restrictions CONFIGURED

### Data Protection ✅ COMPLIANCE READY
- **Multi-Tenant Isolation**: Row Level Security ENFORCED
- **Encryption in Transit**: TLS 1.3 for all communications CONFIGURED
- **PII Handling**: GDPR compliance features IMPLEMENTED
- **Audit Logging**: Security events and data access LOGGED
- **Input Validation**: Pydantic models for ALL request validation IMPLEMENTED

## Error Handling Standards

### Exception Hierarchy
```python
# Use shared exception classes
from shared.exceptions.base import APIError
from shared.exceptions.auth import AuthenticationError
from shared.exceptions.documents import DocumentProcessingError
from shared.exceptions.widgets import WidgetConfigError
```

### Error Response Format
```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human readable message",
    "details": {},
    "timestamp": "2023-01-01T00:00:00Z",
    "request_id": "uuid"
  }
}
```

### Logging Requirements
- **Structured Logging**: Use JSON format with consistent fields
- **Request Tracing**: Include request_id in all log entries
- **Security Logging**: Log authentication attempts and authorization failures
- **Performance Logging**: Log response times and resource usage

## Development Workflow

### Code Organization
- **Shared Models**: Use `shared/models/` for cross-service data structures
- **Service Isolation**: Keep service-specific logic within service boundaries
- **Configuration Management**: Use `shared/config/env_constants.py` for all config
- **Testing Structure**: Mirror source structure in test directories

### Quality Gates
- **Type Checking**: mypy must pass with no errors
- **Code Coverage**: Minimum 80% coverage for new code
- **Security Scanning**: bandit and safety checks must pass
- **Performance**: API endpoints must respond within 200ms (95th percentile)

### Deployment Requirements
- **Health Checks**: Implement `/health` and `/ready` endpoints
- **Graceful Shutdown**: Handle SIGTERM with proper cleanup
- **Resource Limits**: Set appropriate CPU and memory limits
- **Monitoring**: Expose Prometheus metrics on `/metrics`