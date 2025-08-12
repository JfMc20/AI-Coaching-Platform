---
inclusion: always
---

# Code Quality & Architecture Standards

## Project Context
Multi-Channel Proactive Coaching Platform with microservices architecture: FastAPI, PostgreSQL (RLS), Redis, Ollama, ChromaDB.

## Mandatory Development Patterns

### Code Reuse & Discovery
- **Search first**: Always check existing files for similar functionality before creating new code
- **Use shared/**: Leverage `shared/utils/`, `shared/models/`, `shared/cache/` for common functionality
- **Match patterns**: Follow existing service structure and naming conventions
- **Eliminate duplication**: Consolidate repeated logic immediately

### Python & FastAPI Requirements
- **Type hints**: MANDATORY for all function parameters and return values
- **Pydantic models**: Required for all request/response validation
- **Async patterns**: Use `async/await` for ALL I/O operations (DB, Redis, HTTP)
- **SQLAlchemy 2.0**: Use async syntax with proper session management
- **Error handling**: Implement proper HTTP status codes and structured exceptions

### Async Implementation Patterns

**Required Libraries:**
- `aiohttp` (not `requests`), `asyncpg` (not `psycopg2`), `aioredis` (not `redis`)
- `sqlalchemy.ext.asyncio`, `asyncio.sleep` (not `time.sleep`)

**Blocking Code Pattern:**
```python
# Isolate blocking operations in thread pool
async def handle_blocking_operation(data: str) -> str:
    loop = asyncio.get_event_loop()
    with ThreadPoolExecutor() as executor:
        return await loop.run_in_executor(executor, blocking_function, data)
```

**Database Session Pattern:**
```python
# Use existing DatabaseManager from shared/
async with db_manager.get_session() as session:
    await session.flush()  # Get ID without committing
    await session.commit()  # Explicit commit
```

### Architecture Requirements
- **Service isolation**: Logic stays within `services/{service-name}/`
- **Multi-tenancy**: ALWAYS implement Row Level Security for data isolation
- **Configuration**: Environment variables only, never hardcode values
- **Migrations**: Use Alembic for ALL schema changes

### Quality Gates (Non-Negotiable)
- **Cyclomatic Complexity**: ≤ 10 per function
- **Test Coverage**: ≥ 80% for business logic
- **Line Length**: 100 characters max (Black formatter)
- **Type Hints**: Required on ALL functions

### 5. Multi-Tenant Implementation Standards

#### Row Level Security (RLS) Implementation
```sql
-- Example RLS Policy for tenant isolation
CREATE POLICY tenant_isolation ON coaching_programs
    FOR ALL TO authenticated_user
    USING (creator_id = current_setting('app.current_creator_id')::uuid);

-- Enable RLS on all tenant tables
ALTER TABLE coaching_programs ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE ai_conversations ENABLE ROW LEVEL SECURITY;
```

#### Application Tenant Context
```python
# Required pattern for setting tenant context
async def set_tenant_context(creator_id: str, db: AsyncSession):
    """Set tenant context for RLS policies"""
    await db.execute(
        text("SELECT set_config('app.current_creator_id', :creator_id, true)"),
        {"creator_id": creator_id}
    )

# Usage in FastAPI dependencies
async def get_tenant_db(
    creator_id: str = Depends(get_current_creator_id),
    db: AsyncSession = Depends(get_db)
) -> AsyncSession:
    await set_tenant_context(creator_id, db)
    return db
```

#### Cross-Tenant Security Tests
```python
# Required test pattern for tenant isolation
async def test_cross_tenant_data_isolation():
    """Verify no data leakage between tenants"""
    # Create data for tenant A
    tenant_a_data = await create_coaching_program(creator_id="tenant-a")
    
    # Switch to tenant B context
    await set_tenant_context("tenant-b", db)
    
    # Verify tenant B cannot access tenant A's data
    result = await db.execute(
        select(CoachingProgram).where(CoachingProgram.id == tenant_a_data.id)
    )
    assert result.scalar_one_or_none() is None
```

#### Performance Isolation
- **Resource Limits**: Implement per-tenant rate limiting and resource quotas
- **Query Optimization**: Use tenant-specific indexes and partitioning
- **Cache Isolation**: Namespace Redis keys by tenant ID
- **Monitoring**: Track per-tenant resource usage and performance metrics

### 6. AI/ML Operations Standards

#### Model Registry & Versioning
```python
# Required model metadata structure
@dataclass
class ModelMetadata:
    name: str
    version: str
    created_at: datetime
    creator_id: str
    model_type: str  # "embedding", "chat", "classification"
    performance_metrics: Dict[str, float]
    training_data_hash: str
    dependencies: List[str]

# Model registry implementation
class ModelRegistry:
    async def register_model(self, metadata: ModelMetadata, model_path: str):
        """Register model with full metadata tracking"""
        pass
    
    async def get_model(self, name: str, version: str = "latest"):
        """Retrieve model with version fallback"""
        pass
```

#### Embedding Schema Migration Strategy
```python
# Migration pattern for embedding changes
class EmbeddingMigration:
    async def migrate_embeddings(
        self, 
        old_model: str, 
        new_model: str,
        batch_size: int = 100
    ):
        """Migrate embeddings with zero-downtime strategy"""
        # 1. Create new embedding columns
        # 2. Dual-write to both old and new embeddings
        # 3. Backfill existing data in batches
        # 4. Switch reads to new embeddings
        # 5. Drop old embedding columns
        pass
```

#### Prompt Template Management
```python
# Versioned prompt templates with fallbacks
class PromptTemplate:
    def __init__(self, template_id: str, version: str = "v1"):
        self.template_id = template_id
        self.version = version
        self.fallback_versions = ["v1"]  # Always include v1 as fallback
    
    async def render(self, context: Dict[str, Any]) -> str:
        """Render prompt with fallback strategy"""
        for version in [self.version] + self.fallback_versions:
            try:
                template = await self.get_template(version)
                return template.render(**context)
            except TemplateError:
                continue
        raise PromptRenderError("All template versions failed")
```

#### ML Testing Requirements
- **Model Performance Tests**: Validate accuracy/precision metrics
- **Embedding Consistency**: Test that same input produces same embeddings
- **Fallback Testing**: Verify graceful degradation when models fail
- **Cross-Tenant Model Isolation**: Ensure models don't leak data between tenants

## Anti-Patterns to Avoid
- Hardcoded values instead of environment variables
- Synchronous I/O operations in async contexts
- Circular imports between modules
- Direct database access without repository patterns
- Missing error handling or generic exceptions
- Code duplication across services

## Automated Code Quality Enforcement

### Pre-Commit Configuration
Create `.pre-commit-config.yaml` in project root:

```yaml
repos:
  - repo: https://github.com/psf/black
    rev: 23.9.1
    hooks:
      - id: black
        language_version: python3.11
        args: [--line-length=100]

  - repo: https://github.com/pycqa/isort
    rev: 5.12.0
    hooks:
      - id: isort
        args: [--profile=black, --line-length=100]

  - repo: https://github.com/charliermarsh/ruff-pre-commit
    rev: v0.0.292
    hooks:
      - id: ruff
        args: [--fix, --exit-non-zero-on-fix]

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.5.1
    hooks:
      - id: mypy
        additional_dependencies: [types-all]
        args: [--strict, --ignore-missing-imports]

  - repo: local
    hooks:
      - id: complexity-check
        name: Complexity Check
        entry: radon cc --min B --show-complexity
        language: system
        files: \.py$
        
      - id: maintainability-check
        name: Maintainability Check
        entry: radon mi --min B
        language: system
        files: \.py$
```

### CI/CD Pipeline Configuration

#### GitHub Actions Workflow (`.github/workflows/quality.yml`)
```yaml
name: Code Quality & Tests

on: [push, pull_request]

jobs:
  quality:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
          
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install black ruff isort mypy radon pytest pytest-cov bandit safety
          
      - name: Format check
        run: |
          black --check --line-length=100 .
          isort --check-only --profile=black .
          
      - name: Lint check
        run: |
          ruff check .
          mypy . --strict --ignore-missing-imports
          
      - name: Complexity check
        run: |
          radon cc . --min B --show-complexity
          radon mi . --min B
          
      - name: Security scan
        run: |
          bandit -r . -f json -o bandit-report.json
          safety check --json --output safety-report.json
          
      - name: Run tests
        run: |
          pytest --cov=. --cov-report=xml --cov-fail-under=80
          
      - name: API Schema Check
        run: |
          # Generate current OpenAPI schemas
          python scripts/generate_openapi_schemas.py
          # Check if schemas changed without documentation update
          git diff --exit-code docs/api/ || (echo "API schemas changed without documentation update" && exit 1)
```

#### GitLab CI Configuration (`.gitlab-ci.yml`)
```yaml
stages:
  - quality
  - test
  - security

variables:
  PIP_CACHE_DIR: "$CI_PROJECT_DIR/.cache/pip"

cache:
  paths:
    - .cache/pip/
    - venv/

before_script:
  - python -m venv venv
  - source venv/bin/activate
  - pip install -r requirements.txt
  - pip install black ruff isort mypy radon pytest pytest-cov bandit safety

format_check:
  stage: quality
  script:
    - black --check --line-length=100 .
    - isort --check-only --profile=black .
    - ruff check .
    - mypy . --strict --ignore-missing-imports

complexity_check:
  stage: quality
  script:
    - radon cc . --min B --show-complexity --json > complexity-report.json
    - radon mi . --min B --json > maintainability-report.json
  artifacts:
    reports:
      junit: complexity-report.json
    paths:
      - complexity-report.json
      - maintainability-report.json

unit_tests:
  stage: test
  script:
    - pytest --cov=. --cov-report=xml --cov-fail-under=80 --junitxml=report.xml
  artifacts:
    reports:
      junit: report.xml
      coverage_report:
        coverage_format: cobertura
        path: coverage.xml

security_scan:
  stage: security
  script:
    - bandit -r . -f json -o bandit-report.json
    - safety check --json --output safety-report.json
  artifacts:
    reports:
      sast: bandit-report.json
    paths:
      - safety-report.json
```

### Pull Request Template
Create `.github/pull_request_template.md`:

```markdown
## Description
Brief description of changes made.

## Type of Change
- [ ] Bug fix (non-breaking change which fixes an issue)
- [ ] New feature (non-breaking change which adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Documentation update

## Pre-Implementation Checklist
- [ ] I have searched for similar functionality before creating new code
- [ ] I have followed the established patterns and naming conventions
- [ ] I have added type hints to all function parameters and return values
- [ ] I have used async/await for all I/O operations
- [ ] I have implemented proper error handling with appropriate HTTP status codes

## Post-Implementation Checklist
- [ ] Code follows the style guidelines (Black, isort, ruff)
- [ ] Self-review of code has been performed
- [ ] Code is commented, particularly in hard-to-understand areas
- [ ] Corresponding changes to documentation have been made
- [ ] Unit tests have been added/updated and pass locally
- [ ] Multi-tenant isolation has been verified (if applicable)
- [ ] No code duplication exists
- [ ] Cyclomatic complexity is under 10 for all functions
- [ ] Test coverage is above 80% for new code

## API Changes (if applicable)
- [ ] OpenAPI documentation has been updated
- [ ] Breaking changes are documented with migration guide
- [ ] Backward compatibility is maintained or properly deprecated

## Security Considerations
- [ ] No hardcoded secrets or credentials
- [ ] Input validation implemented
- [ ] SQL injection prevention verified
- [ ] Cross-tenant data access prevented

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests added/updated (if applicable)
- [ ] Manual testing performed
- [ ] Cross-tenant isolation tested (if applicable)

## Deployment Notes
Any special deployment considerations or migration steps required.
```

### Quality Gate Configuration
```python
# scripts/quality_gates.py - CI quality gate enforcement
import sys
import json
import subprocess
from typing import Dict, Any

class QualityGates:
    def __init__(self):
        self.gates = {
            'complexity': {'max_cyclomatic': 10, 'max_maintainability_index': 20},
            'coverage': {'min_percentage': 80},
            'duplication': {'max_percentage': 5},
            'security': {'max_high_severity': 0, 'max_medium_severity': 5}
        }
    
    def check_complexity(self) -> bool:
        """Check cyclomatic complexity and maintainability"""
        result = subprocess.run(['radon', 'cc', '.', '--json'], capture_output=True, text=True)
        complexity_data = json.loads(result.stdout)
        
        for file_data in complexity_data.values():
            for item in file_data:
                if item['complexity'] > self.gates['complexity']['max_cyclomatic']:
                    print(f"❌ Complexity violation: {item['name']} has complexity {item['complexity']}")
                    return False
        return True
    
    def check_api_schema_sync(self) -> bool:
        """Verify API schemas are in sync with documentation"""
        # Generate current schemas
        subprocess.run(['python', 'scripts/generate_openapi_schemas.py'])
        
        # Check for changes
        result = subprocess.run(['git', 'diff', '--exit-code', 'docs/api/'], capture_output=True)
        if result.returncode != 0:
            print("❌ API schemas changed without documentation update")
            return False
        return True

if __name__ == "__main__":
    gates = QualityGates()
    
    checks = [
        gates.check_complexity(),
        gates.check_api_schema_sync(),
    ]
    
    if not all(checks):
        sys.exit(1)
    
    print("✅ All quality gates passed")
```

## Quality Checklist
Before completing any task:
- [ ] No code duplication exists
- [ ] Type hints and Pydantic schemas implemented
- [ ] Async patterns used for I/O operations
- [ ] Multi-tenant isolation verified
- [ ] Error handling implemented
- [ ] Tests written for business logic
- [ ] Documentation updated
- [ ] Pre-commit hooks pass
- [ ] CI quality gates pass
- [ ] Code complexity under thresholds
- [ ] Security scan passes