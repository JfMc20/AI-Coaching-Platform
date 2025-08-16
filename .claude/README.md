# Claude Code Configuration

This directory contains Claude Code specific configurations and templates for the Multi-Channel AI Coaching Platform.

## 📁 Contents

### Configuration Files
- **`config.json`** - Project metadata and service configuration for Claude Code
- **`vscode_settings.json`** - Recommended VS Code settings for optimal development
- **`snippets.json`** - Code snippets for common patterns and templates

### Templates
- **`templates/fastapi_endpoint.py`** - Template for creating new API endpoints with multi-tenant authentication
- **`templates/test_template.py`** - Template for creating comprehensive test suites

### Guides
- **`development_guide.md`** - Comprehensive development guide for Claude Code users

## 🚀 Quick Setup

### 1. VS Code Configuration
Copy the recommended settings to your VS Code workspace:

```bash
# Copy VS Code settings (optional)
cp .claude/vscode_settings.json .vscode/settings.json
```

### 2. Code Snippets
The snippets in `snippets.json` provide quick templates for:

- `fastapi-endpoint` - Create new API endpoints
- `pydantic-model` - Create request/response models  
- `db-model` - Create database models with multi-tenant support
- `test-class` - Create test classes
- `test-isolation` - Create multi-tenant isolation tests
- `ai-integration` - Create AI features with Ollama/ChromaDB
- `env-value` - Use environment variables properly

### 3. Development Templates
Use the templates in `templates/` directory:

```bash
# Create new endpoint
cp .claude/templates/fastapi_endpoint.py services/ai-engine-service/app/new_feature.py

# Create new test file
cp .claude/templates/test_template.py tests/unit/ai-engine-service/test_new_feature.py
```

## 🛠️ Claude Code Workflows

### Adding New Features
1. **Plan**: Check `.kiro/specs/mvp-foundation-platform/tasks.md`
2. **Model**: Create database model (if needed) using `db-model` snippet
3. **API**: Create endpoint using `fastapi-endpoint` template
4. **Test**: Create tests using `test_template.py`
5. **Validate**: Run `make test-SERVICE` and `make test-coverage`

### Common Development Commands
```bash
# Start development environment
make up && make health

# Create and test new feature
make test-ai-engine          # Test specific service
make format && make lint     # Format and lint code
make test-coverage          # Check coverage

# Debug issues
make ai-engine-logs         # View service logs
make logs-errors           # Filter error logs
make health                # Check service health
```

### Multi-Tenant Development
Always ensure:
- ✅ Use `get_current_user()` for authentication
- ✅ Use `get_tenant_session()` for database access  
- ✅ Inherit from `BaseTenantModel` for database models
- ✅ Test creator isolation with `test-isolation` snippet
- ✅ Validate `creator_id` in all operations

## 🧪 Testing Strategy

### Required Test Types
1. **Unit Tests**: Business logic validation
2. **Multi-Tenant Tests**: Creator isolation (CRITICAL)
3. **Authentication Tests**: JWT validation
4. **Integration Tests**: Service interaction
5. **API Tests**: Endpoint validation

### Coverage Requirements
- **Existing Code**: 85%+ coverage maintained
- **New Features**: 90%+ coverage required
- **Critical Paths**: 100% coverage (auth, multi-tenant, AI)

## 🔧 Project-Specific Patterns

### Environment Variables
```python
# ✅ Always use get_env_value()
from shared.config.env_constants import get_env_value, VARIABLE_NAME
value = get_env_value(VARIABLE_NAME, default="fallback")

# ❌ Never use os.environ directly
import os
value = os.environ.get("VARIABLE_NAME")  # Don't do this
```

### Database Operations
```python
# ✅ Multi-tenant pattern
@app.post("/api/v1/endpoint")
async def endpoint(
    request: RequestModel,
    current_user: UserContext = Depends(get_current_user),
    session: AsyncSession = Depends(get_tenant_session),
):
    # Automatic creator_id filtering via RLS
```

### AI Integration
```python
# ✅ Creator-isolated AI operations
collection_name = f"creator_{creator_id}_knowledge"
results = await chromadb.query_collection(collection_name, embeddings)
```

## 📚 Additional Resources

- **Main Documentation**: `/CLAUDE.md` - Complete project guide
- **Development Guide**: `.claude/development_guide.md` - Detailed workflows
- **Project Specs**: `.kiro/specs/mvp-foundation-platform/tasks.md` - Current tasks
- **API Docs**: http://localhost:8003/docs - Interactive API documentation
- **Test Coverage**: `htmlcov/index.html` - Coverage reports

## 🆘 Getting Help

### Common Issues
1. **Multi-tenant data leakage** → Check RLS policies and `get_tenant_session()`
2. **Authentication failures** → Verify JWT tokens and `get_current_user()`
3. **Environment variable issues** → Use `get_env_value()` with proper constants
4. **Container issues** → Run `make health` and check service logs

### Debug Commands
```bash
make health                 # Check all services
make ai-engine-logs        # Most common issues
make logs-errors           # Filter error logs
docker-compose ps          # Container status
make db-shell             # Database access
```

### Performance Targets
- API responses: <2s (p95)
- AI responses: <5s (p95)
- Database queries: <100ms (p95)
- Test coverage: 85%+ (existing), 90%+ (new)