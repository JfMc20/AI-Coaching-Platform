---
inclusion: fileMatch
fileMatchPattern: ['nginx/**/*', 'docker-compose*.yml', '**/routes/**/*', '**/main.py']
---

# API Gateway Development Guidelines

## Routing Architecture

### Service Endpoints
All microservices are accessible through the Nginx API Gateway at `http://localhost`:

- **Auth Service**: `/api/v1/auth/*` → `auth-service:8001`
- **Creator Hub**: `/api/v1/creators/*` → `creator-hub-service:8002`
- **AI Engine**: `/api/v1/ai/*` → `ai-engine-service:8003`
- **Channel Service**: `/api/v1/channels/*` → `channel-service:8004`

### Required Health Checks
Every service MUST implement a `/health` endpoint that returns HTTP 200 with basic status information. The API Gateway exposes these at:
- `/api/v1/{service}/health`

## Rate Limiting Rules

### Service-Specific Limits
- **Auth endpoints**: 10 req/min (burst: 20) - Protects against brute force
- **Creator Hub**: 100 req/min (burst: 100) - File uploads and content management
- **AI Engine**: 30 req/min (burst: 50) - Resource-intensive AI operations
- **Channel Service**: 100 req/min (burst: 30) - Real-time messaging

### Implementation
Rate limiting is configured in `nginx/nginx.conf` using `limit_req_zone` and `limit_req` directives.

## Timeout Configuration

### Service-Specific Timeouts
- **AI Engine**: 60s - Allows for LLM processing time
- **Creator Hub**: 300s - Supports large file uploads
- **Channel Service**: 24h - WebSocket connections
- **Auth Service**: 30s - Standard authentication operations

### WebSocket Support
Channel service supports WebSocket connections for real-time messaging.

#### Nginx WebSocket Configuration
```nginx
location /ws {
    proxy_pass http://channel_service;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    
    # WebSocket timeout settings
    proxy_read_timeout 86400s;
    proxy_send_timeout 86400s;
    
    # WebSocket connection management
    proxy_buffering off;
    proxy_cache off;
}
```

#### Resource Management
- **Connection Monitoring**: Monitor active WebSocket connections using `nginx_status` module
- **Connection Limits**: Implement per-IP connection limits to prevent abuse
- **Timeout Management**: Configure appropriate read/send timeouts (24h for persistent connections)
- **Load Balancing**: Consider dedicated WebSocket tier with sticky sessions for horizontal scaling
- **Health Monitoring**: Implement WebSocket-specific health checks to detect connection issues

#### Best Practices
- Use connection pooling and cleanup for abandoned connections
- Implement heartbeat/ping-pong mechanisms to detect dead connections
- Monitor memory usage as WebSocket connections consume more resources than HTTP
- Consider using Redis pub/sub for multi-instance WebSocket message distribution

## Security Headers

### Required Headers
All responses include security headers:
- `X-Frame-Options: DENY`
- `X-Content-Type-Options: nosniff`
- `Content-Security-Policy: default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; connect-src 'self' ws: wss:;`
- `Strict-Transport-Security: max-age=31536000; includeSubDomains` (HTTPS only)

**Note**: Use `add_header` directives with the `always` parameter to ensure headers are sent even on error responses.

### CORS Configuration
CORS is configured for preflight requests. Update `nginx/nginx.conf` when adding new frontend origins.

## Development Guidelines

### Adding New Endpoints
1. Implement endpoint in the appropriate service
2. Add routing rule in `nginx/nginx.conf`
3. Configure appropriate rate limiting
4. Set service-specific timeout if needed
5. Test through API Gateway using `scripts/test-api-gateway.ps1`

### Service Integration
- Always route through API Gateway in development
- Use service names (e.g., `auth-service:8001`) for internal communication
- External clients should only access `localhost` (API Gateway)

### Error Handling
- 502 Bad Gateway: Service is down or unreachable
- 504 Gateway Timeout: Service exceeded timeout limits
- 429 Too Many Requests: Rate limit exceeded

## Testing Requirements

### Gateway Health Verification
Use `scripts/test-api-gateway.ps1` to verify:
- All service health checks respond
- Rate limiting is working
- Security headers are present
- Routing is correct

### Manual Testing
```bash
# Test health checks
curl http://localhost/api/v1/auth/health
curl http://localhost/api/v1/creators/health
curl http://localhost/api/v1/ai/health
curl http://localhost/api/v1/channels/health

# Test rate limiting (should return 429 after limit)
for i in {1..15}; do curl http://localhost/api/v1/auth/health; done
```

## Configuration Files

### Primary Configuration
- `nginx/nginx.conf` - Main gateway configuration
- `docker-compose.yml` - Service orchestration and networking

### Key Configuration Sections
- `upstream` blocks - Service backend definitions
- `location` blocks - Route matching and proxying
- `limit_req_zone` - Rate limiting zones
- `proxy_set_header` - Header forwarding rules