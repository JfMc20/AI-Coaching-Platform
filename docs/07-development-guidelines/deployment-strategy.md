# Deployment Strategy and Infrastructure

## Overview

This document outlines the comprehensive deployment strategy for the multi-channel proactive coaching platform, covering Docker containerization, CI/CD pipelines, environment management, database migrations, monitoring, logging, backup strategies, and disaster recovery procedures.

## Containerization Strategy

### Docker Architecture
```dockerfile
# Backend Dockerfile
FROM python:3.11-slim as builder

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# Production stage
FROM python:3.11-slim

WORKDIR /app

# Copy dependencies from builder
COPY --from=builder /root/.local /root/.local

# Copy application code
COPY . .

# Create non-root user
RUN useradd --create-home --shell /bin/bash app
USER app

# Set environment variables
ENV PATH=/root/.local/bin:$PATH
ENV PYTHONPATH=/app

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```dockerfile
# Frontend Dockerfile
FROM node:18-alpine as builder

WORKDIR /app

# Copy package files
COPY package*.json ./
RUN npm ci --only=production

# Copy source code
COPY . .

# Build application
RUN npm run build

# Production stage
FROM nginx:alpine

# Copy built application
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy nginx configuration
COPY nginx.conf /etc/nginx/nginx.conf

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:80/health || exit 1

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
```

### Docker Compose Configuration
```yaml
# docker-compose.yml
version: '3.8'

services:
  # API Gateway / Load Balancer
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf
      - ./nginx/ssl:/etc/nginx/ssl
    depends_on:
      - backend
      - frontend
    networks:
      - coaching-network

  # Backend API
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    environment:
      - DATABASE_URL=postgresql://postgres:password@postgres:5432/coaching_db
      - REDIS_URL=redis://redis:6379
      - OLLAMA_URL=http://ollama:11434
      - ENVIRONMENT=production
    depends_on:
      - postgres
      - redis
      - ollama
    networks:
      - coaching-network
    deploy:
      replicas: 3
      resources:
        limits:
          memory: 1G
          cpus: '0.5'

  # Frontend Application
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    networks:
      - coaching-network

  # Database
  postgres:
    image: postgres:15
    environment:
      - POSTGRES_DB=coaching_db
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./database/init:/docker-entrypoint-initdb.d
    networks:
      - coaching-network
    deploy:
      resources:
        limits:
          memory: 2G
          cpus: '1.0'

  # Redis Cache
  redis:
    image: redis:7-alpine
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data
    networks:
      - coaching-network

  # Ollama LLM Server
  ollama:
    image: ollama/ollama:latest
    volumes:
      - ollama_data:/root/.ollama
    environment:
      - OLLAMA_HOST=0.0.0.0
    networks:
      - coaching-network
    deploy:
      resources:
        limits:
          memory: 8G
          cpus: '2.0'

  # ChromaDB Vector Database
  chromadb:
    image: chromadb/chroma:latest
    environment:
      - CHROMA_SERVER_HOST=0.0.0.0
      - CHROMA_SERVER_PORT=8000
    volumes:
      - chromadb_data:/chroma/chroma
    networks:
      - coaching-network

volumes:
  postgres_data:
  redis_data:
  ollama_data:
  chromadb_data:

networks:
  coaching-network:
    driver: bridge
```

## CI/CD Pipeline

### GitHub Actions Workflow
```yaml
# .github/workflows/deploy.yml
name: Deploy to Production

on:
  push:
    branches: [main]
  workflow_dispatch:

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: coaching-platform

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    
    - name: Run tests
      run: |
        docker-compose -f docker-compose.test.yml up --abort-on-container-exit
        docker-compose -f docker-compose.test.yml down

  build-and-push:
    needs: test
    runs-on: ubuntu-latest
    permissions:
      contents: read
      packages: write
    
    strategy:
      matrix:
        service: [backend, frontend]
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Log in to Container Registry
      uses: docker/login-action@v2
      with:
        registry: ${{ env.REGISTRY }}
        username: ${{ github.actor }}
        password: ${{ secrets.GITHUB_TOKEN }}
    
    - name: Extract metadata
      id: meta
      uses: docker/metadata-action@v4
      with:
        images: ${{ env.REGISTRY }}/${{ github.repository }}/${{ matrix.service }}
        tags: |
          type=ref,event=branch
          type=sha,prefix={{branch}}-
          type=raw,value=latest,enable={{is_default_branch}}
    
    - name: Build and push Docker image
      uses: docker/build-push-action@v4
      with:
        context: ./${{ matrix.service }}
        push: true
        tags: ${{ steps.meta.outputs.tags }}
        labels: ${{ steps.meta.outputs.labels }}

  deploy-staging:
    needs: build-and-push
    runs-on: ubuntu-latest
    environment: staging
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Deploy to staging
      run: |
        echo "Deploying to staging environment"
        # Deploy to staging server
        ./scripts/deploy.sh staging
    
    - name: Run smoke tests
      run: |
        ./scripts/smoke-tests.sh staging

  deploy-production:
    needs: deploy-staging
    runs-on: ubuntu-latest
    environment: production
    if: github.ref == 'refs/heads/main'
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Deploy to production
      run: |
        echo "Deploying to production environment"
        ./scripts/deploy.sh production
    
    - name: Run health checks
      run: |
        ./scripts/health-checks.sh production
```

### Deployment Scripts
```bash
#!/bin/bash
# scripts/deploy.sh

set -e

ENVIRONMENT=$1
if [ -z "$ENVIRONMENT" ]; then
    echo "Usage: $0 <environment>"
    exit 1
fi

echo "Deploying to $ENVIRONMENT environment..."

# Set environment-specific variables
case $ENVIRONMENT in
    "staging")
        SERVER="staging.coaching-platform.com"
        COMPOSE_FILE="docker-compose.staging.yml"
        ;;
    "production")
        SERVER="coaching-platform.com"
        COMPOSE_FILE="docker-compose.prod.yml"
        ;;
    *)
        echo "Unknown environment: $ENVIRONMENT"
        exit 1
        ;;
esac

# Deploy to server
ssh deploy@$SERVER << EOF
    cd /opt/coaching-platform
    
    # Pull latest images
    docker-compose -f $COMPOSE_FILE pull
    
    # Run database migrations
    docker-compose -f $COMPOSE_FILE run --rm backend alembic upgrade head
    
    # Deploy with zero downtime
    docker-compose -f $COMPOSE_FILE up -d --remove-orphans
    
    # Wait for services to be healthy
    sleep 30
    
    # Run health checks
    docker-compose -f $COMPOSE_FILE exec backend python -m app.health_check
    
    # Clean up old images
    docker image prune -f
EOF

echo "Deployment to $ENVIRONMENT completed successfully!"
```

## Environment Management

### Environment Configuration
```python
# app/core/config.py
from pydantic import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # Environment
    environment: str = "development"
    debug: bool = False
    
    # Database
    database_url: str
    database_pool_size: int = 20
    database_max_overflow: int = 30
    
    # Redis
    redis_url: str
    redis_max_connections: int = 100
    
    # AI Services
    ollama_url: str = "http://localhost:11434"
    chromadb_url: str = "http://localhost:8000"
    
    # Security
    secret_key: str
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 30
    
    # External APIs
    whatsapp_access_token: Optional[str] = None
    telegram_bot_token: Optional[str] = None
    stripe_secret_key: Optional[str] = None
    
    # Monitoring
    sentry_dsn: Optional[str] = None
    log_level: str = "INFO"
    
    # Performance
    max_workers: int = 4
    request_timeout: int = 30
    
    class Config:
        env_file = ".env"
        case_sensitive = False

# Environment-specific configurations
class DevelopmentSettings(Settings):
    debug: bool = True
    log_level: str = "DEBUG"

class StagingSettings(Settings):
    debug: bool = False
    log_level: str = "INFO"

class ProductionSettings(Settings):
    debug: bool = False
    log_level: str = "WARNING"
    database_pool_size: int = 50
    database_max_overflow: int = 100

def get_settings() -> Settings:
    environment = os.getenv("ENVIRONMENT", "development")
    
    if environment == "development":
        return DevelopmentSettings()
    elif environment == "staging":
        return StagingSettings()
    elif environment == "production":
        return ProductionSettings()
    else:
        return Settings()
```

### Environment Files
```bash
# .env.development
ENVIRONMENT=development
DEBUG=true
DATABASE_URL=postgresql://postgres:password@localhost:5432/coaching_dev
REDIS_URL=redis://localhost:6379
OLLAMA_URL=http://localhost:11434
SECRET_KEY=dev-secret-key
LOG_LEVEL=DEBUG

# .env.staging
ENVIRONMENT=staging
DEBUG=false
DATABASE_URL=postgresql://postgres:password@staging-db:5432/coaching_staging
REDIS_URL=redis://staging-redis:6379
OLLAMA_URL=http://staging-ollama:11434
SECRET_KEY=${STAGING_SECRET_KEY}
LOG_LEVEL=INFO
SENTRY_DSN=${STAGING_SENTRY_DSN}

# .env.production
ENVIRONMENT=production
DEBUG=false
DATABASE_URL=${PRODUCTION_DATABASE_URL}
REDIS_URL=${PRODUCTION_REDIS_URL}
OLLAMA_URL=${PRODUCTION_OLLAMA_URL}
SECRET_KEY=${PRODUCTION_SECRET_KEY}
LOG_LEVEL=WARNING
SENTRY_DSN=${PRODUCTION_SENTRY_DSN}
```

## Database Migrations

### Alembic Configuration
```python
# alembic/env.py
from alembic import context
from sqlalchemy import engine_from_config, pool
from app.core.database import Base
from app.core.config import get_settings

settings = get_settings()

# Alembic Config object
config = context.config
config.set_main_option("sqlalchemy.url", settings.database_url)

target_metadata = Base.metadata

def run_migrations_offline():
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online():
    """Run migrations in 'online' mode."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, 
            target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

### Migration Scripts
```bash
#!/bin/bash
# scripts/migrate.sh

set -e

ENVIRONMENT=${1:-development}

echo "Running database migrations for $ENVIRONMENT..."

case $ENVIRONMENT in
    "development")
        alembic upgrade head
        ;;
    "staging"|"production")
        # Backup database before migration
        ./scripts/backup-db.sh $ENVIRONMENT
        
        # Run migration
        alembic upgrade head
        
        # Verify migration
        ./scripts/verify-migration.sh $ENVIRONMENT
        ;;
esac

echo "Database migration completed successfully!"
```

## Monitoring and Logging

### Application Monitoring
```python
# app/core/monitoring.py
import logging
import time
from functools import wraps
from prometheus_client import Counter, Histogram, Gauge
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

# Prometheus metrics
REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint', 'status'])
REQUEST_DURATION = Histogram('http_request_duration_seconds', 'HTTP request duration')
ACTIVE_CONNECTIONS = Gauge('active_database_connections', 'Active database connections')
AI_RESPONSE_TIME = Histogram('ai_response_duration_seconds', 'AI response generation time')

def setup_monitoring(settings):
    """Setup monitoring and logging."""
    
    # Configure Sentry
    if settings.sentry_dsn:
        sentry_sdk.init(
            dsn=settings.sentry_dsn,
            integrations=[
                FastApiIntegration(auto_enabling_integrations=False),
                SqlalchemyIntegration(),
            ],
            traces_sample_rate=0.1,
            environment=settings.environment,
        )
    
    # Configure logging
    logging.basicConfig(
        level=getattr(logging, settings.log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('/var/log/coaching-platform/app.log')
        ]
    )

def monitor_performance(func):
    """Decorator to monitor function performance."""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = await func(*args, **kwargs)
            return result
        finally:
            duration = time.time() - start_time
            AI_RESPONSE_TIME.observe(duration)
    return wrapper
```

### Logging Configuration
```yaml
# logging.yml
version: 1
disable_existing_loggers: false

formatters:
  standard:
    format: '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
  detailed:
    format: '%(asctime)s - %(name)s - %(levelname)s - %(module)s - %(funcName)s - %(message)s'
  json:
    format: '{"timestamp": "%(asctime)s", "logger": "%(name)s", "level": "%(levelname)s", "message": "%(message)s"}'

handlers:
  console:
    class: logging.StreamHandler
    level: INFO
    formatter: standard
    stream: ext://sys.stdout
  
  file:
    class: logging.handlers.RotatingFileHandler
    level: INFO
    formatter: detailed
    filename: /var/log/coaching-platform/app.log
    maxBytes: 10485760  # 10MB
    backupCount: 5
  
  error_file:
    class: logging.handlers.RotatingFileHandler
    level: ERROR
    formatter: detailed
    filename: /var/log/coaching-platform/error.log
    maxBytes: 10485760
    backupCount: 5

loggers:
  app:
    level: INFO
    handlers: [console, file, error_file]
    propagate: false
  
  sqlalchemy:
    level: WARNING
    handlers: [file]
    propagate: false

root:
  level: INFO
  handlers: [console, file]
```

## Backup and Disaster Recovery

### Backup Strategy
```bash
#!/bin/bash
# scripts/backup.sh

set -e

ENVIRONMENT=$1
BACKUP_TYPE=${2:-full}  # full, incremental, or differential
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

echo "Starting $BACKUP_TYPE backup for $ENVIRONMENT environment..."

# Database backup
backup_database() {
    local db_url=$1
    local backup_file="db_backup_${ENVIRONMENT}_${TIMESTAMP}.sql"
    
    echo "Backing up database..."
    pg_dump $db_url > /backups/database/$backup_file
    
    # Compress backup
    gzip /backups/database/$backup_file
    
    # Upload to cloud storage
    aws s3 cp /backups/database/${backup_file}.gz s3://coaching-platform-backups/database/
    
    echo "Database backup completed: ${backup_file}.gz"
}

# File storage backup
backup_files() {
    local backup_file="files_backup_${ENVIRONMENT}_${TIMESTAMP}.tar.gz"
    
    echo "Backing up uploaded files..."
    tar -czf /backups/files/$backup_file /var/lib/coaching-platform/uploads/
    
    # Upload to cloud storage
    aws s3 cp /backups/files/$backup_file s3://coaching-platform-backups/files/
    
    echo "Files backup completed: $backup_file"
}

# Vector database backup
backup_chromadb() {
    local backup_file="chromadb_backup_${ENVIRONMENT}_${TIMESTAMP}.tar.gz"
    
    echo "Backing up ChromaDB..."
    tar -czf /backups/chromadb/$backup_file /var/lib/chromadb/
    
    # Upload to cloud storage
    aws s3 cp /backups/chromadb/$backup_file s3://coaching-platform-backups/chromadb/
    
    echo "ChromaDB backup completed: $backup_file"
}

# Configuration backup
backup_config() {
    local backup_file="config_backup_${ENVIRONMENT}_${TIMESTAMP}.tar.gz"
    
    echo "Backing up configuration..."
    tar -czf /backups/config/$backup_file /opt/coaching-platform/config/
    
    # Upload to cloud storage
    aws s3 cp /backups/config/$backup_file s3://coaching-platform-backups/config/
    
    echo "Configuration backup completed: $backup_file"
}

# Execute backups based on type
case $BACKUP_TYPE in
    "full")
        backup_database $DATABASE_URL
        backup_files
        backup_chromadb
        backup_config
        ;;
    "incremental")
        backup_database $DATABASE_URL
        backup_files
        ;;
    "differential")
        backup_database $DATABASE_URL
        ;;
esac

# Cleanup old backups (keep last 30 days)
find /backups -type f -mtime +30 -delete

echo "Backup process completed successfully!"
```

### Disaster Recovery Plan
```bash
#!/bin/bash
# scripts/disaster-recovery.sh

set -e

ENVIRONMENT=$1
RECOVERY_POINT=$2  # Backup timestamp to restore from

echo "Starting disaster recovery for $ENVIRONMENT environment..."
echo "Recovery point: $RECOVERY_POINT"

# Stop services
echo "Stopping services..."
docker-compose -f docker-compose.$ENVIRONMENT.yml down

# Restore database
restore_database() {
    local backup_file="db_backup_${ENVIRONMENT}_${RECOVERY_POINT}.sql.gz"
    
    echo "Restoring database from $backup_file..."
    
    # Download backup from cloud storage
    aws s3 cp s3://coaching-platform-backups/database/$backup_file /tmp/
    
    # Decompress and restore
    gunzip /tmp/$backup_file
    psql $DATABASE_URL < /tmp/db_backup_${ENVIRONMENT}_${RECOVERY_POINT}.sql
    
    echo "Database restoration completed"
}

# Restore files
restore_files() {
    local backup_file="files_backup_${ENVIRONMENT}_${RECOVERY_POINT}.tar.gz"
    
    echo "Restoring files from $backup_file..."
    
    # Download backup from cloud storage
    aws s3 cp s3://coaching-platform-backups/files/$backup_file /tmp/
    
    # Extract files
    tar -xzf /tmp/$backup_file -C /
    
    echo "Files restoration completed"
}

# Restore ChromaDB
restore_chromadb() {
    local backup_file="chromadb_backup_${ENVIRONMENT}_${RECOVERY_POINT}.tar.gz"
    
    echo "Restoring ChromaDB from $backup_file..."
    
    # Download backup from cloud storage
    aws s3 cp s3://coaching-platform-backups/chromadb/$backup_file /tmp/
    
    # Extract ChromaDB data
    tar -xzf /tmp/$backup_file -C /
    
    echo "ChromaDB restoration completed"
}

# Execute restoration
restore_database
restore_files
restore_chromadb

# Start services
echo "Starting services..."
docker-compose -f docker-compose.$ENVIRONMENT.yml up -d

# Wait for services to be ready
sleep 60

# Run health checks
echo "Running health checks..."
./scripts/health-checks.sh $ENVIRONMENT

echo "Disaster recovery completed successfully!"
```

This comprehensive deployment strategy ensures reliable, scalable, and maintainable infrastructure for the multi-channel proactive coaching platform with robust backup and disaster recovery capabilities.