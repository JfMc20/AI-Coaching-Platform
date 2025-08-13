---
inclusion: always
---

---
inclusion: always
---

# API Design Guidelines

## OpenAPI Documentation Standards

### FastAPI Configuration Requirements
- **Title & Description**: Use descriptive service names and detailed descriptions
- **Version**: Follow semantic versioning (1.0.0)
- **Tags**: Organize endpoints with descriptive tags
- **Security Schemes**: Always include BearerAuth for JWT tokens
- **Error Examples**: Provide standard error response examples

## URL Patterns & Service Ports

### Service Port Allocation
- **Auth Service**: 8001 (`/api/v1/auth/`)
- **Creator Hub**: 8002 (`/api/v1/creators/`)
- **AI Engine**: 8003 (`/api/v1/ai/`)
- **Channel Service**: 8004 (`/api/v1/channels/`)

### URL Structure Rules
- **Version**: Always use `/api/v1/` prefix
- **Resources**: Use plural nouns (`/creators/`, `/documents/`)
- **Actions**: Use HTTP verbs (GET, POST, PUT, DELETE)
- **Nested Resources**: Use hierarchical paths (`/creators/knowledge/documents/`)
- **WebSocket**: Use `/connect` suffix for WebSocket endpoints

### Endpoint Documentation Requirements
- **Summary**: Brief, descriptive endpoint purpose
- **Description**: Detailed explanation with processing steps
- **Response Model**: Use Pydantic models for type safety
- **Status Codes**: Appropriate HTTP status codes (201 for creation, etc.)
- **Error Responses**: Complete error examples with codes and details
- **Examples**: Realistic request/response examples
- **Processing Times**: Expected performance characteristics
- **File Limits**: Size and format restrictions for uploads

## Request/Response Standards

### Required Headers
- **Authorization**: `Bearer <jwt_token>` for authenticated endpoints
- **Content-Type**: `application/json` for JSON payloads
- **Accept**: `application/json` for JSON responses

### Optional Headers
- **X-Request-ID**: UUID for request tracing
- **X-Client-Version**: Client version for compatibility
- **Accept-Language**: Language preference for i18n

### Response Format Rules
- **Success**: Wrap data in `data` field with `meta` object
- **Errors**: Use `error` object with `code`, `message`, `details`
- **Pagination**: Include `pagination` object with page info
- **Timestamps**: Always include ISO 8601 timestamps
- **Request IDs**: Include request_id in all responses

## Authentication & Authorization

### JWT Token Claims
- **sub**: Creator ID (subject)
- **creator_id**: Creator identifier for multi-tenancy
- **permissions**: Array of permission strings
- **subscription_tier**: Subscription level (free, pro, enterprise)
- **tenant_id**: Same as creator_id for RLS
- **aud**: "coaching-platform"
- **iss**: "auth-service"

### Authorization Dependencies
- **get_current_creator_id**: Extract creator ID from JWT
- **require_permission**: Check specific permissions
- **HTTPBearer**: Use for token extraction
- **RS256**: Algorithm for JWT verification
- **401**: Unauthorized for invalid tokens
- **403**: Forbidden for insufficient permissions

## Input Validation & Security

### File Upload Rules
- **Max Size**: 50MB limit
- **Allowed Types**: PDF, TXT, DOCX, MD only
- **MIME Validation**: Verify content matches extension
- **Magic Number Check**: Use python-magic for content detection
- **Path Traversal**: Sanitize filenames to prevent directory traversal

### Input Sanitization Requirements
- **HTML Content**: Use bleach library with allowed tags only
- **Filenames**: Remove dangerous characters and limit length
- **Domain Names**: Validate format with regex patterns
- **SQL Injection**: Use parameterized queries only
- **XSS Prevention**: Escape all user content in responses

## Rate Limiting

### Rate Limit Configuration
- **Auth Endpoints**: 10 requests/minute
- **File Uploads**: 5 requests/minute
- **Chat Messages**: 100 requests/minute
- **Search Queries**: 50 requests/minute
- **Default**: 30 requests/minute

### Implementation Requirements
- **Redis Backend**: Use Redis sorted sets for sliding window
- **Per-User Limits**: Rate limit by creator_id when available
- **IP Fallback**: Use IP address for unauthenticated requests
- **429 Status**: Return 429 Too Many Requests when exceeded
- **Retry Headers**: Include Retry-After header in responses

## Health Check Endpoints

### Required Health Endpoints
- **GET /health**: Basic liveness check (always 200 if running)
- **GET /ready**: Readiness check with dependency validation

### Health Check Requirements
- **Response Model**: Use HealthResponse Pydantic model
- **Status Field**: "healthy", "ready", "not_ready", "unhealthy"
- **Dependencies**: Check database, Redis, external services
- **Response Times**: Include response time metrics
- **Error Details**: Include error messages for failed checks
- **Status Codes**: 200 for healthy, 503 for unhealthy/not ready