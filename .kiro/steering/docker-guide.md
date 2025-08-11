---
inclusion: fileMatch
fileMatchPattern: ['docker-compose*.yml', 'Dockerfile*', '**/Dockerfile*']
---

# Docker Development Guidelines

## Service Architecture

**Multi-Channel Proactive Coaching Platform** with microservices:
- **Infrastructure**: PostgreSQL, Redis, Ollama (LLM), ChromaDB (vectors), Nginx (gateway)
- **Services**: auth-service (8001), creator-hub-service (8002), ai-engine-service (8003), channel-service (8004)
- **Configuration**: `docker-compose.yml` (main), `docker-compose.vault.yml` (production secrets)

## Essential Commands

### Development Workflow
```bash
# Start all services
docker-compose up -d

# Start infrastructure first, then services
docker-compose up -d postgres redis ollama chromadb
docker-compose up -d auth-service creator-hub-service ai-engine-service channel-service

# Rebuild and restart specific service
docker-compose build auth-service
docker-compose up -d auth-service

# View logs
docker-compose logs -f auth-service
docker-compose logs --since="1h" ai-engine-service
```

### Service Management
```bash
# Check service health
curl http://localhost:8001/health  # auth-service
curl http://localhost:8002/health  # creator-hub-service
curl http://localhost:8003/health  # ai-engine-service
curl http://localhost:8004/health  # channel-service

# Debug inside containers
docker-compose exec auth-service bash
docker-compose exec postgres psql -U postgres -d mvp_coaching
```

### Maintenance
```bash
# Clean up regularly (IMPORTANT)
docker image prune -f
docker system prune -f

# Full cleanup (removes data)
docker-compose down -v
docker system prune -a -f
```

## Service Dependencies

**Startup Order**: Infrastructure services must start before application services
1. postgres, redis, ollama, chromadb
2. auth-service, creator-hub-service, ai-engine-service, channel-service

**Service Communication**:
- All services connect to shared PostgreSQL and Redis
- AI Engine connects to Ollama and ChromaDB
- Nginx routes external traffic to services

## Environment Configuration

**Required Variables** (`.env`):
```env
POSTGRES_DB=mvp_coaching
POSTGRES_USER=postgres
POSTGRES_PASSWORD=secure-password
REDIS_URL=redis://localhost:6379/0
JWT_SECRET_KEY=secure-jwt-key
OLLAMA_URL=http://localhost:11434
CHROMADB_URL=http://localhost:8000
```

## Dockerfile Patterns

**Service Structure**: Each service in `services/{service-name}/Dockerfile`
- Use Python 3.11+ base images
- Install dependencies from `requirements.txt`
- Copy service code and shared modules
- Expose appropriate ports (8001-8004)
- Use non-root user for security

## Troubleshooting

**Common Issues**:
- Port conflicts: Use `docker-compose down` then restart
- Build failures: Use `docker-compose build --no-cache`
- Connection issues: Verify service startup order
- Space issues: Run `docker system prune -f` regularly

**Health Checks**: All services expose `/health` endpoints for monitoring

## AI Assistant Guidelines

**When working with Docker**:
1. Always check service dependencies before starting
2. Use `docker-compose logs` to diagnose issues
3. Rebuild services after code changes: `docker-compose build {service}`
4. Verify health endpoints after service updates
5. Clean up images regularly to prevent disk space issues