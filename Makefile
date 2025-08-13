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
	@echo "🔧 Development:"
	@echo "  lint           - Run linting for all services"
	@echo "  format         - Format code for all services"
	@echo "  install-deps   - Install dependencies for all services"
	@echo "  dev-credentials - Setup development credentials"
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

# Initial setup
setup:
	@echo "🚀 Setting up development environment..."
	@if [ ! -f .env ]; then cp .env.example .env; echo "📝 Created .env file"; fi
	@mkdir -p uploads logs
	@touch uploads/.gitkeep logs/.gitkeep
	@docker-compose up -d --build
	@echo "⏳ Waiting for services..."
	@echo "⏳ Waiting for services to be healthy..."
	@./scripts/wait-for-services.sh
	@echo "📥 Pulling AI models..."
	@./scripts/pull-ollama-models.sh
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
	$(eval TIMESTAMP := $(shell date +%Y-%m-%d))
	$(eval TIME_SUFFIX := $(shell date +%H-%M-%S))
	@mkdir -p logs/$(TIMESTAMP)
	@for service in all-services postgres redis auth-service creator-hub-service ai-engine-service channel-service; do \
		if [ "$$service" = "all-services" ]; then \
			docker-compose logs --no-color > logs/$(TIMESTAMP)/$$service-$(TIME_SUFFIX).log; \
		else \
			docker-compose logs --no-color $$service > logs/$(TIMESTAMP)/$$service-$(TIME_SUFFIX).log; \
		fi; \
	done
	@echo "✅ Logs saved to logs/$(TIMESTAMP)/"

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

# Testing commands
test:
	@echo "🧪 Running all tests..."
	@pytest --cov=shared --cov=services --cov-report=html --cov-report=term-missing

test-unit:
	@echo "🧪 Running unit tests..."
	@pytest -m unit --cov=shared --cov=services --cov-report=term-missing

test-integration:
	@echo "🧪 Running integration tests..."
	@pytest -m integration --cov=shared --cov=services --cov-report=term-missing

test-e2e:
	@echo "🧪 Running end-to-end tests..."
	@pytest -m e2e --cov=shared --cov=services --cov-report=term-missing

test-security:
	@echo "🔒 Running security tests..."
	@pytest -m security --cov=shared --cov=services --cov-report=term-missing

test-performance:
	@echo "⚡ Running performance tests..."
	@pytest -m performance --benchmark-json=benchmark.json

test-auth:
	@echo "🔐 Running auth service tests..."
	@pytest services/auth-service/tests/ --cov=services/auth-service --cov-report=term-missing

test-ai-engine:
	@echo "🤖 Running AI engine service tests..."
	@pytest services/ai-engine-service/tests/ --cov=services/ai-engine-service --cov-report=term-missing

test-creator-hub:
	@echo "🎨 Running creator hub service tests..."
	@pytest services/creator-hub-service/tests/ --cov=services/creator-hub-service --cov-report=term-missing

test-channel:
	@echo "📡 Running channel service tests..."
	@pytest services/channel-service/tests/ --cov=services/channel-service --cov-report=term-missing

test-shared:
	@echo "🔧 Running shared components tests..."
	@pytest shared/tests/ --cov=shared --cov-report=term-missing

test-docker:
	@echo "🐳 Running tests in Docker environment..."
	@make test-prune
	@make test-seed
	@docker-compose -f docker-compose.test.yml up --build --abort-on-container-exit test-runner

test-watch:
	@echo "👀 Running tests in watch mode..."
	@pytest --cov=shared --cov=services -f

test-coverage:
	@echo "📊 Generating test coverage report..."
	@pytest --cov=shared --cov=services --cov-report=html --cov-report=xml
	@echo "📊 Coverage report generated in htmlcov/"

test-clean:
	@echo "🧹 Cleaning test artifacts..."
	@rm -rf .pytest_cache htmlcov .coverage coverage.xml
	@find . -name "*.pyc" -delete
	@find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true

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
	@if ! python scripts/validate-env.py $(SERVICE); then \
		echo "❌ Environment validation failed for $(SERVICE)"; \
		echo "📋 Saving validation logs..."; \
		mkdir -p logs; \
		python scripts/validate-env.py $(SERVICE) > logs/env-validation-$(SERVICE)-$(shell date +%Y%m%d-%H%M%S).log 2>&1 || true; \
		echo "💾 Validation logs saved to logs/"; \
		exit 1; \
	fi

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

# Code analysis and cleanup
analyze-dead-code:
	@echo "🔍 Analyzing dead code..."
	@python scripts/dead_code_analysis.py

analyze-hardcoded:
	@echo "🔍 Analyzing hardcoded values..."
	@python scripts/hardcoded_values_analysis.py

cleanup-env:
	@echo "🧹 Cleaning up environment variables..."
	@python scripts/env_cleanup.py

pre-commit:
	@echo "🔧 Running pre-commit hooks..."
	@pre-commit run --all-files

pre-commit-install:
	@echo "🔧 Installing pre-commit hooks..."
	@pre-commit install

# Test environment setup
test-setup:
	@echo "🔧 Setting up test environment..."
	@echo "🔍 Validating Docker Compose configuration..."
	@if ! python scripts/validate-compose-services.py docker-compose.test.yml --services postgres-test redis-test --check-health --check-deps; then \
		echo "❌ Docker Compose validation failed"; \
		mkdir -p logs; \
		python scripts/validate-compose-services.py docker-compose.test.yml --services postgres-test redis-test --check-health --check-deps > logs/compose-validation-$(shell date +%Y%m%d-%H%M%S).log 2>&1 || true; \
		echo "💾 Validation logs saved to logs/"; \
		exit 1; \
	fi
	@echo "🧹 Ensuring clean state..."
	@make test-clean-volumes
	@echo "🚀 Starting test services..."
	@docker-compose -f docker-compose.test.yml up -d postgres-test redis-test
	@echo "⏳ Waiting for test services to be healthy..."
	@./scripts/wait-for-test-services.sh
	@echo "🔍 Validating test setup..."
	@if ! python scripts/validate-test-setup.py; then \
		echo "❌ Test setup validation failed"; \
		echo "📋 Saving validation logs..."; \
		mkdir -p logs; \
		python scripts/validate-test-setup.py > logs/test-validation-$(shell date +%Y%m%d-%H%M%S).log 2>&1 || true; \
		echo "💾 Validation logs saved to logs/"; \
		exit 1; \
	fi

test-teardown:
	@echo "🧹 Tearing down test environment..."
	@docker-compose -f docker-compose.test.yml down -v
	@echo "🧹 Cleaning up test volumes..."
	@docker volume prune -f || true

test-clean-volumes:
	@echo "🧹 Cleaning test volumes to ensure fresh state..."
	@python scripts/clean-test-state.py --skip-directories --wait 3

test-clean-all:
	@echo "🧹 Complete test state cleanup..."
	@python scripts/clean-test-state.py --wait 5

# Test environment seeding for consistent state
test-seed:
	@echo "🌱 Seeding test environment..."
	@echo "🔄 Resetting test database..."
	@docker-compose -f docker-compose.test.yml exec -T postgres-test psql -U postgres -d ai_platform_test -c "SELECT cleanup_test_data(true);" || true
	@echo "📊 Seeding test data..."
	@python scripts/seed-test-data.py || echo "⚠️  Test seeding script not found"
	@echo "✅ Test environment seeded"

# Comprehensive test cleanup for CI/CD
test-prune:
	@echo "🧹 Pruning test environment for CI/CD..."
	@echo "🛑 Stopping all test containers..."
	@docker-compose -f docker-compose.test.yml down -v --remove-orphans || true
	@echo "🧹 Cleaning test volumes..."
	@docker volume ls -q | grep -E "(test|Test)" | xargs -r docker volume rm || true
	@echo "🌐 Cleaning test networks..."
	@docker network ls -q | xargs -r docker network inspect | grep -l "test\|Test" | xargs -r docker network rm || true
	@echo "🧹 Pruning unused Docker resources..."
	@docker system prune -f --volumes
	@echo "✅ Test environment pruned"

test-validate:
	@echo "🔍 Validating test configuration..."
	@if ! python scripts/validate-test-setup.py; then \
		echo "❌ Test validation failed"; \
		echo "📋 Saving validation logs..."; \
		mkdir -p logs; \
		python scripts/validate-test-setup.py > logs/test-validation-$(shell date +%Y%m%d-%H%M%S).log 2>&1 || true; \
		echo "💾 Validation logs saved to logs/"; \
		exit 1; \
	fi

# CI/CD simulation
ci-test:
	@echo "🚀 Running CI/CD test simulation..."
	@make pre-commit
	@make analyze-dead-code
	@make analyze-hardcoded
	@make test-unit
	@make test-integration
	@make test-security
	@echo "✅ CI/CD simulation completed successfully!"

# 🔧 Testing Infrastructure Improvements
validate-improvements:
	@echo "🔍 Validating all testing infrastructure improvements..."
	@python scripts/validate-all-improvements.py

demo-improvements:
	@echo "🎬 Demonstrating testing infrastructure improvements..."
	@python scripts/demo-improvements.py

maintenance-guide:
	@echo "📋 Generating maintenance guide..."
	@python scripts/maintenance-guide.py

# Enhanced test validation with logging
test-validate-enhanced:
	@echo "🧪 Running enhanced test validation..."
	@mkdir -p logs
	@python scripts/validate-test-setup.py
	@python scripts/validate-compose-services.py docker-compose.test.yml \
		--services postgres-test redis-test ollama-test chromadb-test \
		--check-health --check-deps --check-networks --verbose

# Optimized cleanup with single command
test-clean-optimized:
	@echo "🧹 Running optimized test cleanup..."
	@python scripts/clean-test-state.py

# Complete test setup with all improvements
test-setup-complete:
	@echo "🚀 Setting up complete test environment with all improvements..."
	@make test-clean-optimized
	@make test-validate-enhanced
	@docker-compose -f docker-compose.test.yml up -d --build
	@echo "✅ Test environment ready with all optimizations!"

# Performance monitoring
test-performance-check:
	@echo "📊 Checking test performance metrics..."
	@echo "Docker system usage:"
	@docker system df
	@echo ""
	@echo "Test logs size:"
	@du -sh logs/ 2>/dev/null || echo "No logs directory"
	@echo ""
	@echo "Container resource usage:"
	@docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}" 2>/dev/null || echo "No containers running"

# Security validation
test-security-check:
	@echo "🔐 Running security validation..."
	@echo "Checking for hardcoded secrets in workflow..."
	@if grep -r "password.*=" .github/workflows/ 2>/dev/null; then \
		echo "❌ Found potential hardcoded secrets"; \
	else \
		echo "✅ No hardcoded secrets found in workflows"; \
	fi
	@echo "Checking Docker socket exposure..."
	@if grep -r "/var/run/docker.sock" docker-compose*.yml 2>/dev/null; then \
		echo "⚠️  Docker socket exposure found"; \
	else \
		echo "✅ No Docker socket exposure found"; \
	fi

# All-in-one improvement validation
validate-all:
	@echo "🎯 Running complete validation of all improvements..."
	@make validate-improvements
	@make test-security-check
	@make test-performance-check
	@echo "🎉 Complete validation finished!"

# Quick improvement demo
quick-demo:
	@echo "⚡ Quick demonstration of key improvements..."
	@echo ""
	@echo "1. 🐳 Docker Optimization:"
	@grep -A 3 "no-install-recommends" Dockerfile.test || echo "   Not found"
	@echo ""
	@echo "2. 📝 Enhanced Logging:"
	@python scripts/validate-compose-services.py docker-compose.test.yml --services postgres-test --verbose 2>/dev/null | head -5 || echo "   Script not available"
	@echo ""
	@echo "3. 🧹 Optimized Cleanup:"
	@python scripts/clean-test-state.py --skip-containers --skip-volumes --wait 0 2>/dev/null | head -3 || echo "   Script not available"
	@echo ""
	@echo "✅ Quick demo complete! Run 'make demo-improvements' for full demo."

# Test Redis improvements specifically
test-redis-improvements:
	@echo "🔍 Testing Redis validation improvements..."
	@python scripts/test-redis-improvements.py

# Final comprehensive validation of all improvements
final-validation:
	@echo "🎯 Running final comprehensive validation..."
	@python scripts/final-validation.py

# Maintenance and monitoring commands
check-dependencies:
	@echo "🔍 Checking dependencies for security and updates..."
	@python scripts/check-dependencies.py

setup-performance-monitoring:
	@echo "📊 Setting up performance monitoring..."
	@python scripts/setup-performance-monitoring.py

run-performance-tests:
	@echo "🚀 Running performance benchmarks..."
	@python scripts/run-performance-tests.py

validate-test-cleanup:
	@echo "🧹 Validating test data cleanup function..."
	@python scripts/validate-test-data-cleanup.py

# Maintenance tasks
maintenance-weekly:
	@echo "📅 Running weekly maintenance tasks..."
	@echo "🔍 Checking Docker system usage:"
	@docker system df || echo "Docker not available"
	@echo "📋 Checking log files:"
	@du -sh logs/ 2>/dev/null || echo "No logs directory"
	@echo "🔐 Checking for security updates:"
	@python scripts/check-dependencies.py

maintenance-monthly:
	@echo "📅 Running monthly maintenance tasks..."
	@echo "🐳 Checking Docker images for updates..."
	@docker images --format "table {{.Repository}}\t{{.Tag}}\t{{.CreatedAt}}" | head -10 || echo "Docker not available"
	@echo "📊 Running performance tests..."
	@python scripts/run-performance-tests.py || echo "Performance tests not available"
	@echo "🧹 Validating cleanup functions..."
	@python scripts/validate-test-data-cleanup.py || echo "Database not available"

# Help for new improvement commands
help-improvements:
	@echo "🔧 Testing Infrastructure Improvements Commands:"
	@echo ""
	@echo "📊 Validation & Monitoring:"
	@echo "  validate-improvements    - Validate all improvements are working"
	@echo "  demo-improvements       - Full demonstration of improvements"
	@echo "  maintenance-guide       - Generate maintenance recommendations"
	@echo "  validate-all           - Complete validation (improvements + security + performance)"
	@echo ""
	@echo "🧪 Enhanced Testing:"
	@echo "  test-validate-enhanced  - Enhanced test validation with logging"
	@echo "  test-clean-optimized   - Optimized cleanup (single command)"
	@echo "  test-setup-complete    - Complete test setup with all improvements"
	@echo "  test-redis-improvements - Test Redis validation robustness improvements"
	@echo "  final-validation       - Final comprehensive validation of all improvements"
	@echo ""
	@echo "🔧 Maintenance & Monitoring:"
	@echo "  check-dependencies     - Check for security vulnerabilities and updates"
	@echo "  setup-performance-monitoring - Set up performance monitoring tools"
	@echo "  run-performance-tests  - Run performance benchmarks"
	@echo "  validate-test-cleanup  - Validate test data cleanup function"
	@echo "  maintenance-weekly     - Run weekly maintenance tasks"
	@echo "  maintenance-monthly    - Run monthly maintenance tasks"
	@echo ""
	@echo "🔍 Monitoring & Security:"
	@echo "  test-performance-check - Check performance metrics"
	@echo "  test-security-check    - Validate security improvements"
	@echo "  quick-demo            - Quick demo of key improvements"
	@echo ""
	@echo "💡 Usage Examples:"
	@echo "  make validate-all      # Complete validation"
	@echo "  make quick-demo        # Quick overview"
	@echo "  make demo-improvements # Full demonstration"