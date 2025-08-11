# MVP Coaching AI Platform - Development Makefile

.PHONY: help setup up down logs clean test lint format install-deps dev-credentials

# Default target
help:
	@echo "MVP Coaching AI Platform - Development Commands"
	@echo ""
	@echo "🚀 Environment Management:"
	@echo "  setup          - Initial development environment setup"
	@echo "  up             - Start all services"
	@echo "  down           - Stop all services"
	@echo "  clean          - Clean up containers and volumes"
	@echo "  health         - Check service health status"
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
	@echo "🔍 Advanced Log Analysis:"
	@echo "  logs-setup     - Setup logging infrastructure and directories"
	@echo "  logs-analyze   - Analyze logs and generate summary"
	@echo "  logs-analyze-errors - Analyze error patterns in detail"
	@echo "  logs-analyze-performance - Analyze performance metrics"
	@echo "  logs-report    - Generate and save detailed analysis report"
	@echo "  logs-monitor   - Monitor logs in real-time"
	@echo "  logs-monitor-errors - Monitor only error logs in real-time"
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
	@echo "🧪 Development:"
	@echo "  test           - Run tests for all services"
	@echo "  lint           - Run linting for all services"
	@echo "  format         - Format code for all services"
	@echo "  install-deps   - Install dependencies for all services"
	@echo "  dev-credentials - Setup development credentials"
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

# Initial setup
setup:
	@echo "🚀 Setting up development environment..."
	@if [ ! -f .env ]; then cp .env.example .env; echo "📝 Created .env file"; fi
	@mkdir -p uploads logs
	@touch uploads/.gitkeep logs/.gitkeep
	@docker-compose up -d --build
	@echo "⏳ Waiting for services..."
	@sleep 30
	@docker-compose exec ollama ollama pull nomic-embed-text || true
	@docker-compose exec ollama ollama pull llama2:7b-chat || true
	@echo "✅ Setup complete!"

# Start services
up:
	@echo "🐳 Starting services..."
	@docker-compose up -d

# Stop services
down:
	@echo "🛑 Stopping services..."
	@docker-compose down

# View logs
logs:
	@echo "📋 Viewing logs from all services..."
	@docker-compose logs -f --tail=100

logs-follow:
	@echo "📋 Following logs from all services..."
	@docker-compose logs -f

logs-tail:
	@echo "📋 Showing last 50 lines from all services..."
	@docker-compose logs --tail=50

logs-since:
	@echo "📋 Showing logs since $(TIME) (e.g., make logs-since TIME=1h)..."
	@docker-compose logs --since=$(TIME)

logs-errors:
	@echo "🚨 Filtering error logs from all services..."
	@docker-compose logs | grep -i "error\|exception\|failed\|fatal" || echo "No errors found"

logs-warnings:
	@echo "⚠️  Filtering warning logs from all services..."
	@docker-compose logs | grep -i "warn\|warning" || echo "No warnings found"

logs-save:
	@echo "💾 Saving logs to files..."
	@mkdir -p logs/$(shell date +%Y-%m-%d)
	@docker-compose logs --no-color > logs/$(shell date +%Y-%m-%d)/all-services-$(shell date +%H-%M-%S).log
	@docker-compose logs --no-color postgres > logs/$(shell date +%Y-%m-%d)/postgres-$(shell date +%H-%M-%S).log
	@docker-compose logs --no-color redis > logs/$(shell date +%Y-%m-%d)/redis-$(shell date +%H-%M-%S).log
	@docker-compose logs --no-color auth-service > logs/$(shell date +%Y-%m-%d)/auth-service-$(shell date +%H-%M-%S).log
	@docker-compose logs --no-color creator-hub-service > logs/$(shell date +%Y-%m-%d)/creator-hub-service-$(shell date +%H-%M-%S).log
	@docker-compose logs --no-color ai-engine-service > logs/$(shell date +%Y-%m-%d)/ai-engine-service-$(shell date +%H-%M-%S).log
	@docker-compose logs --no-color channel-service > logs/$(shell date +%Y-%m-%d)/channel-service-$(shell date +%H-%M-%S).log
	@echo "✅ Logs saved to logs/$(shell date +%Y-%m-%d)/"

logs-clean:
	@echo "🧹 Cleaning old log files (older than 7 days)..."
	@find logs -name "*.log" -mtime +7 -delete 2>/dev/null || true
	@echo "✅ Old log files cleaned"

logs-analyze:
	@echo "🔍 Analyzing logs..."
	@chmod +x scripts/analyze-logs.sh
	@./scripts/analyze-logs.sh summary

logs-analyze-errors:
	@echo "🚨 Analyzing error patterns..."
	@chmod +x scripts/analyze-logs.sh
	@./scripts/analyze-logs.sh errors

logs-analyze-performance:
	@echo "⚡ Analyzing performance metrics..."
	@chmod +x scripts/analyze-logs.sh
	@./scripts/analyze-logs.sh performance

logs-report:
	@echo "📊 Generating detailed log report..."
	@chmod +x scripts/analyze-logs.sh
	@./scripts/analyze-logs.sh report

logs-monitor:
	@echo "👀 Monitoring logs in real-time..."
	@chmod +x scripts/analyze-logs.sh
	@./scripts/analyze-logs.sh monitor

logs-monitor-errors:
	@echo "🚨 Monitoring error logs in real-time..."
	@chmod +x scripts/analyze-logs.sh
	@./scripts/analyze-logs.sh monitor error

logs-setup:
	@echo "🔧 Setting up logging infrastructure..."
	@chmod +x scripts/setup-logging.sh
	@./scripts/setup-logging.sh

# Clean up
clean:
	@echo "🧹 Cleaning up..."
	@docker-compose down -v --remove-orphans
	@docker system prune -f

# Run tests
test:
	@echo "🧪 Running tests..."
	@cd shared && poetry run pytest || true
	@cd services/auth-service && poetry run pytest || true
	@cd services/creator-hub-service && poetry run pytest || true
	@cd services/ai-engine-service && poetry run pytest || true
	@cd services/channel-service && poetry run pytest || true

# Run linting
lint:
	@echo "🔍 Running linting..."
	@cd shared && poetry run flake8 . || true
	@cd services/auth-service && poetry run flake8 . || true
	@cd services/creator-hub-service && poetry run flake8 . || true
	@cd services/ai-engine-service && poetry run flake8 . || true
	@cd services/channel-service && poetry run flake8 . || true

# Format code
format:
	@echo "✨ Formatting code..."
	@cd shared && poetry run black . && poetry run isort . || true
	@cd services/auth-service && poetry run black . && poetry run isort . || true
	@cd services/creator-hub-service && poetry run black . && poetry run isort . || true
	@cd services/ai-engine-service && poetry run black . && poetry run isort . || true
	@cd services/channel-service && poetry run black . && poetry run isort . || true

# Install dependencies
install-deps:
	@echo "📦 Installing dependencies..."
	@cd shared && poetry install
	@cd services/auth-service && poetry install
	@cd services/creator-hub-service && poetry install
	@cd services/ai-engine-service && poetry install
	@cd services/channel-service && poetry install

# Setup development credentials
dev-credentials:
	@echo "🔐 Setting up development credentials..."
	@if [ ! -f .env ]; then cp .env.example .env; echo "📝 Created .env file"; fi
	@echo "Starting Vault for development..."
	@docker-compose -f docker-compose.vault.yml up -d
	@sleep 10
	@echo "Loading secrets from Vault..."
	@bash scripts/load-secrets.sh || echo "⚠️  Vault not available, using .env file"
	@echo "✅ Development credentials setup complete"

# Vault management commands
vault-start:
	@echo "🚀 Starting Vault development server..."
	@docker-compose -f docker-compose.vault.yml up -d

vault-stop:
	@echo "🛑 Stopping Vault development server..."
	@docker-compose -f docker-compose.vault.yml down

vault-status:
	@echo "🔍 Checking Vault status..."
	@docker-compose -f docker-compose.vault.yml ps vault

vault-logs:
	@echo "📋 Vault logs..."
	@docker-compose -f docker-compose.vault.yml logs -f vault

# Environment validation
validate-env:
	@echo "🔍 Validating environment variables..."
	@python scripts/validate-env.py

validate-env-service:
	@echo "🔍 Validating environment variables for $(SERVICE)..."
	@python scripts/validate-env.py $(SERVICE)

# Service-specific log commands
auth-logs:
	@echo "📋 Auth Service logs..."
	@docker-compose logs -f --tail=100 auth-service

creator-hub-logs:
	@echo "📋 Creator Hub Service logs..."
	@docker-compose logs -f --tail=100 creator-hub-service

ai-engine-logs:
	@echo "📋 AI Engine Service logs..."
	@docker-compose logs -f --tail=100 ai-engine-service

channel-logs:
	@echo "📋 Channel Service logs..."
	@docker-compose logs -f --tail=100 channel-service

postgres-logs:
	@echo "📋 PostgreSQL logs..."
	@docker-compose logs -f --tail=100 postgres

redis-logs:
	@echo "📋 Redis logs..."
	@docker-compose logs -f --tail=100 redis

ollama-logs:
	@echo "📋 Ollama logs..."
	@docker-compose logs -f --tail=100 ollama

chromadb-logs:
	@echo "📋 ChromaDB logs..."
	@docker-compose logs -f --tail=100 chromadb

nginx-logs:
	@echo "📋 Nginx logs..."
	@docker-compose logs -f --tail=100 nginx

# Service-specific log analysis
auth-errors:
	@echo "🚨 Auth Service errors..."
	@docker-compose logs auth-service | grep -i "error\|exception\|failed\|fatal" || echo "No errors found"

creator-hub-errors:
	@echo "🚨 Creator Hub Service errors..."
	@docker-compose logs creator-hub-service | grep -i "error\|exception\|failed\|fatal" || echo "No errors found"

ai-engine-errors:
	@echo "🚨 AI Engine Service errors..."
	@docker-compose logs ai-engine-service | grep -i "error\|exception\|failed\|fatal" || echo "No errors found"

channel-errors:
	@echo "🚨 Channel Service errors..."
	@docker-compose logs channel-service | grep -i "error\|exception\|failed\|fatal" || echo "No errors found"

# Database commands
db-shell:
	@docker-compose exec postgres psql -U postgres -d mvp_coaching

db-migrate:
	@echo "🚀 Running database migrations..."
	@python scripts/run-migrations.py

db-reset:
	@echo "🔄 Resetting database..."
	@docker-compose exec postgres psql -U postgres -c "DROP DATABASE IF EXISTS mvp_coaching"
	@docker-compose exec postgres psql -U postgres -c "CREATE DATABASE mvp_coaching"
	@python scripts/run-migrations.py

db-seed:
	@echo "🌱 Seeding database with development data..."
	@alembic upgrade head

redis-shell:
	@docker-compose exec redis redis-cli

# Multi-tenant testing
test-isolation:
	@echo "🔒 Testing multi-tenant data isolation..."
	@python -m pytest tests/test_multi_tenant_isolation.py -v

# Health checks
health:
	@echo "🔍 Checking service health..."
	@curl -f http://localhost:8001/health || echo "❌ Auth service unhealthy"
	@curl -f http://localhost:8002/health || echo "❌ Creator Hub service unhealthy"
	@curl -f http://localhost:8003/health || echo "❌ AI Engine service unhealthy"
	@curl -f http://localhost:8004/health || echo "❌ Channel service unhealthy"