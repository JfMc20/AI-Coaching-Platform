---
inclusion: always
---

# MVP Architecture Guidelines

## Core Architecture Principles

### Multi-Tenancy First Design
- **Row Level Security (RLS)**: All PostgreSQL tables MUST implement RLS policies for creator isolation
- **Tenant Context**: Every database query MUST include creator_id for proper data isolation
- **ChromaDB Collections**: Use pattern `creator_{creator_id}_knowledge` for vector storage isolation
- **Redis Keys**: Prefix all Redis keys with creator_id: `creator:{creator_id}:{key_name}`

### Service Communication Patterns
- **Async HTTP Clients**: Use `shared/clients/http_client.py` for inter-service communication
- **X-Request-ID Propagation**: Always propagate request IDs across service boundaries
- **Circuit Breaker**: Implement circuit breaker pattern for external service calls
- **Timeout Handling**: Set appropriate timeouts for all external calls (default: 30s)

### Data Flow Architecture
```
Widget/Frontend → API Gateway → Service → Database/AI
                                    ↓
                              Message Queue → Other Services
```

## Service-Specific Guidelines

### Auth Service (Port 8001)
- **JWT Management**: Use RS256 algorithm with key rotation support
- **Password Security**: bcrypt with minimum 12 rounds
- **Session Management**: Redis-based sessions with configurable TTL
- **Rate Limiting**: Implement per-IP and per-user rate limiting

### Creator Hub Service (Port 8002)
- **Document Processing**: Use `DocumentProcessor` class with async file operations
- **Widget Configuration**: Generate embed codes using Jinja2 templates
- **File Upload Security**: Validate file types, sizes, and scan for malware
- **Knowledge Base**: Integrate with AI Engine for document processing

### AI Engine Service (Port 8003)
- **RAG Pipeline**: Implement retrieval-augmented generation with context management
- **Ollama Integration**: Use `nomic-embed-text` for embeddings, `llama2:7b-chat` for generation
- **ChromaDB Management**: Per-tenant collections with proper metadata
- **Context Windows**: Manage conversation context within token limits

### Channel Service (Port 8004)
- **WebSocket Management**: Use `WebSocketManager` with Redis for scalability
- **Message Processing**: Async message handling with proper error recovery
- **Connection Cleanup**: Implement graceful shutdown and stale connection cleanup
- **Multi-Channel Support**: Abstract message handling for future channel expansion

## Database Schema Requirements

### Core Tables Structure
```sql
-- All tables MUST include these fields
created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
creator_id UUID NOT NULL REFERENCES creators(id) ON DELETE CASCADE

-- All tables MUST have RLS enabled
ALTER TABLE table_name ENABLE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON table_name FOR ALL TO authenticated_user 
USING (creator_id = current_setting('app.current_creator_id')::UUID);
```

### Required Indexes
- **Creator ID**: Index on creator_id for all multi-tenant tables
- **Timestamps**: Index on created_at and updated_at for time-based queries
- **Status Fields**: Index on status/state fields for filtering
- **Composite Indexes**: For common query patterns

## AI/ML Integration Patterns

### ChromaDB Management
- **Collection Naming**: `creator_{creator_id}_knowledge`
- **Metadata Schema**: Include document_id, chunk_index, creator_id, source, created_at
- **Embedding Model**: Use `nomic-embed-text` consistently across all documents
- **Chunk Size**: Default 1000 tokens with 200 token overlap

### Ollama Integration
- **Model Management**: Ensure models are pulled and available before service start
- **Error Handling**: Implement retry logic for model loading and generation
- **Context Management**: Track conversation context and manage token limits
- **Performance**: Monitor response times and implement caching where appropriate

## Security Implementation

### Authentication & Authorization
- **JWT Tokens**: Include creator_id, permissions, and expiration
- **API Key Management**: Support API keys for programmatic access
- **CORS Configuration**: Restrict origins based on widget configuration
- **Input Validation**: Use Pydantic models for all request validation

### Data Protection
- **Encryption at Rest**: Encrypt sensitive data in database
- **Encryption in Transit**: TLS 1.3 for all communications
- **PII Handling**: Implement data anonymization for analytics
- **Audit Logging**: Log all data access and modifications

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