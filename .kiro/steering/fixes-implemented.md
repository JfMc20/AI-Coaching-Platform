---
inclusion: always
---

# Infrastructure Fixes & Patterns

## Critical Implementation Patterns

### Docker Health Checks
**Required Pattern**: Use Python-native health checks in all Dockerfiles with exec form
```dockerfile
HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
  CMD ["python3", "-c", "import urllib.request,sys; resp=urllib.request.urlopen('http://localhost:8001/health',timeout=5); sys.exit(0 if resp.getcode()==200 else 1)"]
```
**Rationale**: Exec form avoids shell quoting issues, explicit HTTP 200 check ensures proper health validation, compatible with minimal/distroless images

### Redis Atomic Operations
**Required Pattern**: Use Lua scripts for atomic Redis operations
```python
# Use atomic updates for session management
lua_script = """
local key = KEYS[1]
local updates = cjson.decode(ARGV[1])
if redis.call('exists', key) == 1 then
    for field, value in pairs(updates) do
        redis.call('hset', key, field, value)
    end
    return 1
else
    return 0
end
"""
```
**Rationale**: Prevents race conditions in concurrent environments

### Session Management
**Required Pattern**: Always preserve TTL during session updates
- Use atomic operations for session state changes
- Maintain original expiration times
- Update last_activity timestamp atomically
- Handle concurrent access gracefully

## Service Architecture Standards

### Health Check Endpoints
All services must implement `/health` endpoint returning:
```json
{
  "status": "healthy",
  "service": "service-name",
  "timestamp": "ISO-8601-timestamp"
}
```

### Redis Connection Patterns
- Use `get_connection()` method for transactional operations
- Maintain backward compatibility with existing Redis client API
- Implement proper connection pooling and error handling

### API Gateway Integration
- All services accessible via Nginx proxy at `/api/v1/{service}/`
- Security headers automatically applied
- Rate limiting enforced at gateway level
- Health checks routed through gateway

## Testing Requirements

### Infrastructure Testing
- Verify all container health checks pass
- Test Redis connectivity and atomic operations
- Validate API Gateway routing and security headers
- Confirm multi-service communication

### Verification Commands
```bash
# Check container health
docker-compose ps

# Test direct service health
curl http://localhost:800{1-4}/health

# Test via API Gateway
curl http://localhost/api/v1/{auth|creators|ai|channels}/health

# Run comprehensive tests
.\scripts\test-fixes.ps1
```

## Performance Considerations

### Redis Optimization
- Use Lua scripts to reduce network round-trips
- Implement proper connection pooling
- Cache frequently accessed session data
- Monitor Redis memory usage and eviction policies

### Container Resource Management
- Set appropriate health check intervals (30s)
- Configure reasonable timeout values (5s)
- Implement graceful shutdown handling
- Monitor container resource consumption

## Error Handling Patterns

### Health Check Failures
- Implement exponential backoff for retries
- Log health check failures with context
- Provide meaningful error messages
- Ensure graceful degradation

### Session Store Errors
- Handle Redis connection failures gracefully
- Implement fallback mechanisms for session data
- Log atomic operation failures with full context
- Maintain data consistency during error conditions

## Deployment Readiness Checklist

- [ ] All services have Python-native health checks
- [ ] Redis operations use atomic Lua scripts
- [ ] API Gateway routes all services correctly
- [ ] Security headers configured and active
- [ ] Rate limiting properly configured
- [ ] All containers report healthy status
- [ ] Inter-service communication verified
- [ ] Test scripts execute successfully