# Quick Start Development Guide

## Essential Commands

### Environment Setup
```bash
# 🚀 Complete environment setup (first time)
make setup              # Initialize environment + pull AI models + health checks

# 🐳 Daily development workflow  
make up                 # Start all services
make health            # Check service health status
make down              # Stop services when done
```

### Testing & Quality
```bash
# 🏃‍♂️ Fast testing workflow
make test-unit                    # Unit tests only (fastest)
make test-auth                   # Auth service tests only
make test-ai-engine             # AI engine tests only
make test                       # Full test suite with coverage

# 🔍 Code quality
make lint                       # Flake8 linting  
make format                     # Black + isort formatting
make pre-commit                 # Run all pre-commit hooks

# 📊 Coverage analysis
make test-coverage              # Generate HTML coverage report → htmlcov/
```

### Debugging & Logs
```bash
# 🔍 Service-specific logs (most useful)
make ai-engine-logs             # AI engine service logs (follow mode)
make auth-logs                  # Auth service logs
make postgres-logs              # Database logs
make logs-errors               # Only error logs from all services

# 📋 Log analysis
make logs-save                  # Save all logs to timestamped files
make logs-analyze              # Analyze error patterns
```

### Database Operations
```bash
make db-shell                   # PostgreSQL shell access
make db-migrate                 # Run Alembic migrations  
make db-reset                   # Reset database (destructive)
make redis-shell               # Redis CLI access
```

### Troubleshooting Commands
```bash
# 🔧 Container issues
docker-compose ps               # Check container status
docker-compose logs SERVICE     # Specific service logs
docker-compose build --no-cache SERVICE  # Rebuild service

# 🌡️ Health diagnostics  
make health                     # All service health checks
curl http://localhost:8003/ready # AI engine readiness
```

## Demo vs Testing Modes

### 📺 Demo Mode (Public-Facing)
- **Location**: `http://localhost:8004/widget-demo`
- **Purpose**: Showcase creator digital twin capabilities to potential clients
- **Features**: 
  - **Knowledge Upload Interface**: "Test with your own content"
  - **Real-time AI Training**: Upload PDF → AI learns → Chat with your clone
  - **Personality Demonstration**: AI speaks AS the creator, not ABOUT content
  - **Proactive Engagement Preview**: Show behavioral trigger examples
  - **Multi-channel Simulation**: Demo across web, mobile, messaging
- **Use Cases**: Sales demos, creator onboarding, investor presentations

### 🔧 Visual Testing Service (Development Tool)
- **Location**: `http://localhost:8005` (Future implementation)
- **Purpose**: Internal debugging, development, and AI training tool
- **Features**:
  - Technical debugging dashboards
  - Real-time message flow visualization
  - AI model training interfaces
  - Performance metrics and analytics
  - Developer-focused tools and logs
- **Use Cases**: Development, QA testing, AI coach training, troubleshooting

## Performance Targets

- API responses: <2s (p95)
- AI responses: <5s (p95) 
- Database queries: <100ms (p95)
- Support: 1,000+ creators, 10,000+ users
- Test coverage: 85%+ required, 90%+ for new features