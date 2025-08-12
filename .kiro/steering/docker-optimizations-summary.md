---
inclusion: fileMatch
fileMatchPattern: ['**/Dockerfile', '**/docker-compose*.yml', '**/.dockerignore', 'scripts/docker-*.ps1', 'scripts/test-*.ps1']
---

# Docker & Container Standards

## Required Dockerfile Patterns

### Multi-Stage Build Structure
All services must use multi-stage builds for optimal image size and security:

```dockerfile
# Stage 1: Builder
FROM python:3.11-slim as builder
RUN apt-get update && apt-get install -y build-essential gcc
COPY requirements.txt .
RUN pip wheel --no-cache-dir --wheel-dir /wheels -r requirements.txt

# Stage 2: Runtime
FROM python:3.11-slim as runtime
RUN groupadd -r appuser && useradd -r -g appuser appuser
WORKDIR /app
COPY --from=builder /wheels /wheels
COPY --from=builder /build/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir --no-index --find-links /wheels -r /tmp/requirements.txt && \
    rm -rf /wheels /tmp/requirements.txt
COPY --chown=appuser:appuser . /app/
USER appuser
```

### Mandatory Health Check Pattern
Use Python-native health checks with exec form to avoid shell issues:

```dockerfile
# Copy health check script
COPY scripts/healthcheck.py /usr/local/bin/healthcheck.py
RUN chmod +x /usr/local/bin/healthcheck.py

# Health check with dedicated script
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD ["python3", "/usr/local/bin/healthcheck.py"]
```

## Service Configuration Standards

### Worker Allocation
- **Auth Service**: 2 workers (authentication load)
- **Creator Hub**: 2 workers (file uploads/processing)
- **AI Engine**: 1 worker (resource-intensive AI operations)
- **Channel Service**: 1 worker (WebSocket connections)

### Port Assignments
- Auth Service: 8001
- Creator Hub: 8002  
- AI Engine: 8003
- Channel Service: 8004

## Docker Compose Requirements

### Service Dependencies
Use `wait-for-services.py` script for robust dependency management:
- Configure appropriate timeouts per service
- Implement retry logic with exponential backoff
- Log dependency status clearly

### Environment Configuration
- Use `.env` files for environment-specific variables
- Never hardcode URLs, ports, or credentials
- Support multiple environments (dev, staging, prod)

## .dockerignore Optimization

### Required Exclusions
```
.git/
.vscode/
*.md
__pycache__/
*.pyc
.pytest_cache/
.env*
venv/
.venv/
*.log
tmp/
*.tmp
```

### Service-Specific Ignores
Each service should have its own `.dockerignore` excluding irrelevant services and files.

## Testing & Verification Commands

### Build Verification
```powershell
# Optimized parallel build
.\scripts\docker-build-optimized.ps1 -Parallel

# Health monitoring
.\scripts\docker-health-monitor.ps1 -Continuous

# API Gateway testing
.\scripts\test-api-gateway.ps1 -BaseUrl "http://localhost" -TimeoutSec 10
```

### Image Analysis
```bash
# Check image sizes
docker images | grep mvp

# Inspect layers
docker history <image-name>

# Security scanning
docker scout cves <image-name>
```

## Performance Targets

### Image Optimization
- Target: <400MB per service image
- Achieve 50%+ size reduction through multi-stage builds
- Use wheel caching for 60% faster rebuilds

### Build Performance
- Optimize Docker context with proper .dockerignore
- Leverage BuildKit features for parallel builds
- Implement layer caching strategies

## Security Requirements

### Container Security
- Run as non-root user in all containers
- Remove build tools from final images
- Minimize attack surface with slim base images
- Implement proper file ownership with `COPY --chown`

### Network Security
- Use internal Docker networks for service communication
- Expose only necessary ports
- Implement proper health check endpoints

## Anti-Patterns to Avoid

- Using shell form in health checks (causes quoting issues)
- Including build tools in final runtime images
- Hardcoding localhost URLs in scripts
- Missing or inadequate health check start periods
- Ignoring Docker layer caching optimization
- Running containers as root user