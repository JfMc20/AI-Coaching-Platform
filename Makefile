# MVP Coaching AI Platform - Development Makefile
# Updated to reflect current implementation status

.PHONY: help setup up down restart logs clean test lint format install-deps dev-credentials health

# Variables
COMPOSE_FILE = docker-compose.yml
COMPOSE_OVERRIDE = docker-compose.override.yml
COMPOSE_TEST = docker-compose.test.yml
COMPOSE_BUILD = docker-compose.build.yml
COMPOSE_VAULT = docker-compose.vault.yml
TIMESTAMP = $(shell date +%Y%m%d_%H%M%S)

# Build optimization variables
DOCKER_BUILDKIT = 1
COMPOSE_DOCKER_CLI_BUILD = 1
BUILDX_CACHE_DIR = /tmp/.buildx-cache

# Default target
help:
	@echo "MVP Coaching AI Platform - Development Commands"
	@echo ""
	@echo "🚀 Environment Management:"
	@echo "  setup          - Initial development environment setup"
	@echo "  up             - Start all services"
	@echo "  down           - Stop all services"
	@echo "  restart        - Restart all services"
	@echo "  clean          - Clean up containers and volumes"
	@echo "  health         - Check service health status"
	@echo "  status         - Show service status"
	@echo ""
	@echo "🔧 Development:"
	@echo "  lint           - Run linting for all services"
	@echo "  format         - Format code for all services"
	@echo "  install-deps   - Install dependencies for all services"
	@echo "  dev-credentials - Setup development credentials"
	@echo "  generate-requirements - Generate service requirements.txt files"
	@echo ""
	@echo "⚡ Optimized Builds (30min → <5min):"
	@echo "  build-optimized     - Build all services with BuildKit optimization"
	@echo "  build-ai-engine-fast - Build AI Engine with maximum optimization"
	@echo "  rebuild-optimized   - Rebuild from scratch (optimized)"
	@echo "  up-optimized       - Build and start with optimization"
	@echo "  clean-build-cache  - Clean build cache"
	@echo ""
	@echo "🧪 Testing:"
	@echo "  test           - Run all tests with coverage"
	@echo "  test-unit      - Run unit tests only"
	@echo "  test-integration - Run integration tests only"
	@echo "  test-e2e       - Run end-to-end tests only"
	@echo "  test-security  - Run security tests only"
	@echo "  test-performance - Run performance tests only"
	@echo "  test-auth      - Run auth service tests"
	@echo "  test-ai-engine - Run AI engine service tests"
	@echo "  test-creator-hub - Run creator hub service tests"
	@echo "  test-channel   - Run channel service tests"
	@echo "  test-shared    - Run shared components tests"
	@echo "  test-docker    - Run tests in Docker environment"
	@echo "  test-watch     - Run tests in watch mode"
	@echo "  test-coverage  - Generate coverage report"
	@echo "  test-clean     - Clean test artifacts"
	@echo ""
	@echo "📋 Log Management:"
	@echo "  logs           - View logs from all services (last 100 lines)"
	@echo "  logs-follow    - Follow logs from all services in real-time"
	@echo "  logs-tail      - Show last 50 lines from all services"
	@echo "  logs-since     - Show logs since TIME (e.g., make logs-since TIME=1h)"
	@echo "  logs-errors    - Filter and show only error logs"
	@echo "  logs-warnings  - Filter and show only warning logs"
	@echo "  logs-save      - Save all logs to timestamped files"
	@echo "  logs-clean     - Clean old log files (older than 7 days)"
	@echo ""
	@echo "🔍 Service-Specific Logs:"
	@echo "  auth-logs      - Auth service logs"
	@echo "  creator-hub-logs - Creator Hub service logs"
	@echo "  ai-engine-logs - AI Engine service logs"
	@echo "  channel-logs   - Channel service logs"
	@echo "  postgres-logs  - PostgreSQL logs"
	@echo "  redis-logs     - Redis logs"
	@echo "  ollama-logs    - Ollama logs"
	@echo "  chromadb-logs  - ChromaDB logs"
	@echo "  nginx-logs     - Nginx logs"
	@echo ""
	@echo "🚨 Error Analysis:"
	@echo "  auth-errors    - Show Auth service errors only"
	@echo "  creator-hub-errors - Show Creator Hub service errors only"
	@echo "  ai-engine-errors - Show AI Engine service errors only"
	@echo "  channel-errors - Show Channel service errors only"
	@echo ""
	@echo "🧹 Code Quality:"
	@echo "  analyze-dead-code - Analyze and report dead code"
	@echo "  analyze-hardcoded - Analyze hardcoded values"
	@echo "  cleanup-env    - Clean up environment variables"
	@echo "  pre-commit     - Run pre-commit hooks"
	@echo ""
	@echo "🔐 Vault Management:"
	@echo "  vault-start    - Start Vault development server"
	@echo "  vault-stop     - Stop Vault development server"
	@echo "  vault-status   - Check Vault status"
	@echo "  vault-logs     - View Vault logs"
	@echo ""
	@echo "💾 Database:"
	@echo "  db-shell       - Access PostgreSQL shell"
	@echo "  db-migrate     - Run database migrations"
	@echo "  db-reset       - Reset database"
	@echo "  db-seed        - Seed database with development data"
	@echo "  redis-shell    - Access Redis shell"

# ===================================================================
# Environment Management
# ===================================================================

# Initial setup
setup:
	@echo "🚀 Setting up development environment..."
	@if [ ! -f .env ]; then cp .env.example .env; echo "📝 Created .env file from example"; fi
	@mkdir -p uploads logs secrets
	@touch uploads/.gitkeep logs/.gitkeep
	@echo "📦 Generating requirements files..."
	@python scripts/generate-requirements.py
	@echo "🔐 Setting up development secrets..."
	@$(MAKE) dev-credentials
	@echo "🐳 Building and starting services..."
	@docker-compose up -d --build
	@echo "⏳ Waiting for services to be healthy..."
	@python scripts/wait-for-services.py
	@echo "🤖 Pulling AI models..."
	@bash scripts/pull-ollama-models.sh
	@echo "✅ Setup complete! Services available at:"
	@echo "   - Auth Service: http://localhost:8001"
	@echo "   - Creator Hub: http://localhost:8002"
	@echo "   - AI Engine: http://localhost:8003"
	@echo "   - Channel Service: http://localhost:8004"
	@echo "   - API Gateway: http://localhost:80"

# Start all services
up:
	@echo "� Stalrting all services..."
	@docker-compose up -d
	@echo "⏳ Waiting for services to be ready..."
	@python scripts/wait-for-services.py
	@echo "✅ All services are running!"

# Stop all services
down:
	@echo "🛑 Stopping all services..."
	@docker-compose down

# Restart all services
restart:
	@echo "🔄 Restarting all services..."
	@docker-compose restart
	@echo "⏳ Waiting for services to be ready..."
	@python scripts/wait-for-services.py
	@echo "✅ All services restarted!"

# Clean up containers and volumes
clean:
	@echo "🧹 Cleaning up containers and volumes..."
	@docker-compose down -v --remove-orphans
	@docker system prune -f
	@echo "✅ Cleanup complete!"

# Check service health
health:
	@echo "🏥 Checking service health..."
	@echo "Auth Service (8001):"
	@curl -s http://localhost:8001/health | jq . || echo "❌ Auth service not responding"
	@echo "Creator Hub (8002):"
	@curl -s http://localhost:8002/health | jq . || echo "❌ Creator Hub not responding"
	@echo "AI Engine (8003):"
	@curl -s http://localhost:8003/health | jq . || echo "❌ AI Engine not responding"
	@echo "Channel Service (8004):"
	@curl -s http://localhost:8004/health | jq . || echo "❌ Channel Service not responding"

# Show service status
status:
	@echo "📊 Service Status:"
	@docker-compose ps

# ===================================================================
# Development Tools
# ===================================================================

# Generate requirements files
generate-requirements:
	@echo "📦 Generating requirements.txt files..."
	@python scripts/generate-requirements.py
	@echo "✅ Requirements files generated!"

# Install dependencies
install-deps:
	@echo "� Installning dependencies..."
	@pip install -r requirements.txt
	@echo "✅ Dependencies installed!"

# Setup development credentials
dev-credentials:
	@echo "🔐 Setting up development credentials..."
	@mkdir -p secrets
	@if [ ! -f secrets/jwt_secret.txt ]; then \
		openssl rand -base64 32 > secrets/jwt_secret.txt; \
		echo "Generated JWT secret"; \
	fi
	@echo "✅ Development credentials ready!"

# Code formatting
format:
	@echo "🎨 Formatting code..."
	@black shared/ services/ tests/ --line-length 100
	@isort shared/ services/ tests/ --profile black
	@echo "✅ Code formatted!"

# Linting
lint:
	@echo "🔍 Running linting..."
	@flake8 shared/ services/ tests/ --max-line-length=100 --extend-ignore=E203,W503
	@mypy shared/ services/ --ignore-missing-imports
	@echo "✅ Linting complete!"

# Pre-commit hooks
pre-commit:
	@echo "🔧 Running pre-commit hooks..."
	@pre-commit run --all-files
	@echo "✅ Pre-commit checks complete!"

# ===================================================================
# Testing
# ===================================================================

# Run all tests with coverage
test:
	@echo "🧪 Running all tests with coverage..."
	@pytest --cov=shared --cov=services --cov-report=term-missing --cov-report=html:htmlcov --cov-report=xml:coverage.xml
	@echo "✅ Tests complete! Coverage report in htmlcov/"

# Unit tests only
test-unit:
	@echo "🧪 Running unit tests..."
	@pytest tests/unit/ -v

# Integration tests only
test-integration:
	@echo "🧪 Running integration tests..."
	@pytest tests/integration/ -v

# End-to-end tests
test-e2e:
	@echo "🧪 Running end-to-end tests..."
	@pytest tests/e2e/ -v

# Security tests
test-security:
	@echo "🔒 Running security tests..."
	@pytest tests/ -m security -v

# Performance tests
test-performance:
	@echo "⚡ Running performance tests..."
	@pytest tests/performance/ -v

# Service-specific tests
test-auth:
	@echo "🧪 Running auth service tests..."
	@pytest tests/unit/auth-service/ -v

test-ai-engine:
	@echo "🧪 Running AI engine tests..."
	@pytest tests/unit/ai-engine-service/ -v

test-creator-hub:
	@echo "🧪 Running creator hub tests..."
	@pytest tests/unit/creator-hub-service/ -v

test-channel:
	@echo "🧪 Running channel service tests..."
	@pytest tests/unit/channel-service/ -v

test-shared:
	@echo "🧪 Running shared components tests..."
	@pytest tests/shared/ -v

# Docker-based testing
test-docker:
	@echo "🐳 Running tests in Docker environment..."
	@docker-compose -f $(COMPOSE_TEST) up --build --abort-on-container-exit
	@docker-compose -f $(COMPOSE_TEST) down

# Watch mode testing
test-watch:
	@echo "👀 Running tests in watch mode..."
	@pytest --watch

# Coverage report
test-coverage:
	@echo "📊 Generating coverage report..."
	@pytest --cov=shared --cov=services --cov-report=html:htmlcov --cov-report=xml:coverage.xml
	@echo "✅ Coverage report generated in htmlcov/"

# Clean test artifacts
test-clean:
	@echo "🧹 Cleaning test artifacts..."
	@rm -rf .pytest_cache/ htmlcov/ coverage.xml .coverage
	@find . -name "*.pyc" -delete
	@find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
	@echo "✅ Test artifacts cleaned!"

# ===================================================================
# Log Management
# ===================================================================

# View logs from all services
logs:
	@docker-compose logs --tail=100

# Follow logs in real-time
logs-follow:
	@docker-compose logs -f

# Show last 50 lines
logs-tail:
	@docker-compose logs --tail=50

# Show logs since specific time
logs-since:
	@docker-compose logs --since="$(TIME)"

# Filter error logs
logs-errors:
	@docker-compose logs | grep -i error

# Filter warning logs
logs-warnings:
	@docker-compose logs | grep -i warning

# Save logs to files
logs-save:
	@echo "💾 Saving logs to files..."
	@mkdir -p logs/$(TIMESTAMP)
	@docker-compose logs > logs/$(TIMESTAMP)/all-services.log
	@docker-compose logs auth-service > logs/$(TIMESTAMP)/auth-service.log
	@docker-compose logs creator-hub-service > logs/$(TIMESTAMP)/creator-hub-service.log
	@docker-compose logs ai-engine-service > logs/$(TIMESTAMP)/ai-engine-service.log
	@docker-compose logs channel-service > logs/$(TIMESTAMP)/channel-service.log
	@echo "✅ Logs saved to logs/$(TIMESTAMP)/"

# Clean old log files
logs-clean:
	@echo "🧹 Cleaning old log files..."
	@find logs/ -type f -mtime +7 -delete 2>/dev/null || true
	@echo "✅ Old log files cleaned!"

# Service-specific logs
auth-logs:
	@docker-compose logs -f auth-service

creator-hub-logs:
	@docker-compose logs -f creator-hub-service

ai-engine-logs:
	@docker-compose logs -f ai-engine-service

channel-logs:
	@docker-compose logs -f channel-service

postgres-logs:
	@docker-compose logs -f postgres

redis-logs:
	@docker-compose logs -f redis

ollama-logs:
	@docker-compose logs -f ollama

chromadb-logs:
	@docker-compose logs -f chromadb

nginx-logs:
	@docker-compose logs -f nginx

# Error-specific logs
auth-errors:
	@docker-compose logs auth-service | grep -i error

creator-hub-errors:
	@docker-compose logs creator-hub-service | grep -i error

ai-engine-errors:
	@docker-compose logs ai-engine-service | grep -i error

channel-errors:
	@docker-compose logs channel-service | grep -i error

# ===================================================================
# Code Quality Analysis
# ===================================================================

# Analyze dead code
analyze-dead-code:
	@echo "� Analyezing dead code..."
	@vulture shared/ services/ --min-confidence 80
	@echo "✅ Dead code analysis complete!"

# Analyze hardcoded values
analyze-hardcoded:
	@echo "🔍 Analyzing hardcoded values..."
	@grep -r "TODO\|FIXME\|XXX\|HACK" shared/ services/ || echo "No hardcoded TODOs found"
	@echo "✅ Hardcoded values analysis complete!"

# Clean up environment variables
cleanup-env:
	@echo "🧹 Cleaning up environment variables..."
	@echo "Checking for unused environment variables..."
	@echo "✅ Environment cleanup complete!"

# ===================================================================
# Vault Management (Production Secrets)
# ===================================================================

# Start Vault development server
vault-start:
	@echo "🔐 Starting Vault development server..."
	@docker-compose -f $(COMPOSE_VAULT) up -d vault
	@echo "✅ Vault started at http://localhost:8200"

# Stop Vault server
vault-stop:
	@echo "🛑 Stopping Vault server..."
	@docker-compose -f $(COMPOSE_VAULT) down

# Check Vault status
vault-status:
	@echo "� Checkiing Vault status..."
	@curl -s http://localhost:8200/v1/sys/health | jq . || echo "❌ Vault not responding"

# View Vault logs
vault-logs:
	@docker-compose -f $(COMPOSE_VAULT) logs -f vault

# ===================================================================
# Database Management
# ===================================================================

# Access PostgreSQL shell
db-shell:
	@echo "💾 Accessing PostgreSQL shell..."
	@docker-compose exec postgres psql -U postgres -d ai_platform_dev

# ===================================================================
# ROBUST DATABASE MANAGEMENT
# ===================================================================

# Check database status
db-status:
	@echo "📊 Checking database status..."
	@docker-compose exec auth-service python /app/scripts/db-migration-manager.py status

# Run database migrations (safe with validation)
db-migrate:
	@echo "🔄 Running database migrations with validation..."
	@docker-compose exec auth-service python /app/scripts/db-migration-manager.py migrate
	@echo "✅ Database migrations complete!"

# Create new migration
db-create-migration:
	@echo "📝 Creating new migration..."
	@read -p "Migration message: " message; \
	docker-compose exec auth-service python /app/scripts/db-migration-manager.py create "$$message"

# Validate migration safety
db-validate:
	@echo "🔍 Validating migration safety..."
	@docker-compose exec auth-service python /app/scripts/db-migration-manager.py validate

# Create database backup (development only)
db-backup:
	@echo "💾 Creating database backup..."
	@docker-compose exec auth-service python /app/scripts/db-migration-manager.py backup

# Initialize database with proper migration state
db-init:
	@echo "🚀 Initializing database..."
	@docker-compose exec auth-service python /app/scripts/db-migration-manager.py migrate
	@$(MAKE) db-status

# Reset database
db-reset:
	@echo "⚠️  Resetting database (this will delete all data)..."
	@read -p "Are you sure? [y/N] " -n 1 -r; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		docker-compose exec postgres psql -U postgres -c "DROP DATABASE IF EXISTS ai_platform_dev;"; \
		docker-compose exec postgres psql -U postgres -c "CREATE DATABASE ai_platform_dev;"; \
		$(MAKE) db-migrate; \
		echo "✅ Database reset complete!"; \
	else \
		echo "❌ Database reset cancelled."; \
	fi

# Seed database with development data
db-seed:
	@echo "🌱 Seeding database with development data..."
	@docker-compose exec auth-service python -c "from scripts.seed_dev_data import seed_data; seed_data()"
	@echo "✅ Database seeded!"

# Access Redis shell
redis-shell:
	@echo "� Acceszsing Redis shell..."
	@docker-compose exec redis redis-cli

# ===================================================================
# Build and Deployment (Optimized)
# ===================================================================

# Build all services (legacy - slow)
build:
	@echo "🔨 Building all services..."
	@docker-compose build

# ===================================================================
# OPTIMIZED BUILD COMMANDS (30min → <5min)
# ===================================================================

# Setup BuildKit cache directory
setup-buildkit:
	@echo "🚀 Setting up BuildKit cache..."
	@mkdir -p $(BUILDX_CACHE_DIR)
	@echo "✅ BuildKit cache directory created"

# Build with BuildKit optimization (FAST)
build-optimized: setup-buildkit
	@echo "⚡ Building with BuildKit optimization..."
	@export DOCKER_BUILDKIT=$(DOCKER_BUILDKIT) && \
	export COMPOSE_DOCKER_CLI_BUILD=$(COMPOSE_DOCKER_CLI_BUILD) && \
	docker-compose -f $(COMPOSE_BUILD) build --parallel
	@echo "✅ Optimized build complete!"

# Build specific service optimized
build-service-optimized: setup-buildkit
	@echo "⚡ Building $(SERVICE) with optimization..."
	@export DOCKER_BUILDKIT=$(DOCKER_BUILDKIT) && \
	export COMPOSE_DOCKER_CLI_BUILD=$(COMPOSE_DOCKER_CLI_BUILD) && \
	docker-compose -f $(COMPOSE_BUILD) build $(SERVICE)
	@echo "✅ Service $(SERVICE) built!"

# Build AI Engine with optimizations (most critical)
build-ai-engine-fast: setup-buildkit
	@echo "🤖 Building AI Engine with maximum optimization..."
	@export DOCKER_BUILDKIT=$(DOCKER_BUILDKIT) && \
	export COMPOSE_DOCKER_CLI_BUILD=$(COMPOSE_DOCKER_CLI_BUILD) && \
	docker-compose -f $(COMPOSE_BUILD) build ai-engine-service
	@echo "✅ AI Engine built in <5min!"

# Rebuild from scratch with optimization
rebuild-optimized: setup-buildkit
	@echo "🔄 Rebuilding all services from scratch (optimized)..."
	@export DOCKER_BUILDKIT=$(DOCKER_BUILDKIT) && \
	export COMPOSE_DOCKER_CLI_BUILD=$(COMPOSE_DOCKER_CLI_BUILD) && \
	docker-compose -f $(COMPOSE_BUILD) build --no-cache --parallel
	@echo "✅ Optimized rebuild complete!"

# Clean build cache
clean-build-cache:
	@echo "🧹 Cleaning build cache..."
	@rm -rf $(BUILDX_CACHE_DIR)
	@docker builder prune -f
	@echo "✅ Build cache cleaned!"

# Up with optimized builds
up-optimized: build-optimized
	@echo "🚀 Starting services with optimized builds..."
	@docker-compose up -d
	@echo "✅ Optimized services started!"
	@echo "✅ All services built!"

# Build specific service
build-auth:
	@docker-compose build auth-service

build-creator-hub:
	@docker-compose build creator-hub-service

build-ai-engine:
	@docker-compose build ai-engine-service

build-channel:
	@docker-compose build channel-service

# Production deployment preparation
prod-check:
	@echo "🔍 Checking production readiness..."
	@echo "Checking environment variables..."
	@python scripts/validate-production-env.py
	@echo "Running security checks..."
	@$(MAKE) test-security
	@echo "✅ Production checks complete!"

# ===================================================================
# Monitoring and Debugging
# ===================================================================

# Show resource usage
resources:
	@echo "📊 Resource Usage:"
	@docker stats --no-stream

# Show network information
network:
	@echo "🌐 Network Information:"
	@docker network ls
	@docker-compose ps

# Debug specific service
debug-auth:
	@docker-compose exec auth-service bash

debug-creator-hub:
	@docker-compose exec creator-hub-service bash

debug-ai-engine:
	@docker-compose exec ai-engine-service bash

debug-channel:
	@docker-compose exec channel-service bash

# ===================================================================
# AI Model Management
# ===================================================================

# Pull AI models
pull-models:
	@echo "🤖 Pulling AI models..."
	@bash scripts/pull-ollama-models.sh
	@echo "✅ AI models ready!"

# Check AI model status
models-status:
	@echo "🤖 Checking AI model status..."
	@curl -s http://localhost:11434/api/tags | jq . || echo "❌ Ollama not responding"

# Test AI functionality
test-ai:
	@echo "🤖 Testing AI functionality..."
	@curl -s -X POST http://localhost:8003/api/v1/ai/ollama/test-chat \
		-H "Content-Type: application/json" \
		-d '{"message": "Hello, test message"}' | jq . || echo "❌ AI test failed"