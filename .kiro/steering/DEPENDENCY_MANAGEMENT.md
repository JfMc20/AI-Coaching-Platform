---
inclusion: always
---

# Centralized Dependency Management

## Core Principles

This project uses centralized dependency management to ensure version consistency across all microservices and prevent dependency conflicts.

### File Structure
- **`pyproject.toml`**: Single source of truth for all dependencies and versions
- **`scripts/generate-requirements.py`**: Automated script that generates service-specific requirements
- **`services/{service-name}/requirements.txt`**: Auto-generated files - **NEVER EDIT MANUALLY**

## Dependency Management Workflow

### Adding/Updating Dependencies ✅ REQUIRED PROCESS

1. **Edit `pyproject.toml` only**:
   ```toml
   [tool.poetry.dependencies]
   new-package = "^1.0.0"
   ```

2. **Regenerate requirements**:
   ```bash
   python scripts/generate-requirements.py
   ```

3. **Rebuild affected services**:
   ```bash
   docker compose build {service-name}
   # or rebuild all: docker compose build
   ```

### Forbidden Actions ❌ NEVER DO THIS
- Manually editing `services/*/requirements.txt` files
- Adding dependencies directly in Dockerfiles
- Using different package versions between services
- Installing packages with pip in containers

## Service-Specific Dependencies

### Base Dependencies (All Services)
- `fastapi`, `uvicorn`, `pydantic`, `sqlalchemy`, `asyncpg`, `redis`, `python-jose`, `passlib`

### Auth Service Extensions
- `alembic`, `psycopg2-binary`, `argon2-cffi`

### Creator Hub Service Extensions  
- `aiofiles`, `python-magic`, `PyPDF2`, `python-docx`, `python-multipart`

### AI Engine Service Extensions
- `chromadb`, `ollama`, `numpy`, `opentelemetry-api`, `prometheus-client`

### Channel Service Extensions
- `websockets`, `aiofiles`, `python-socketio`

## Conflict Resolution

### Common Conflict Pattern
```
ERROR: package-a 1.0.0 depends on shared-dep<2.0.0
ERROR: package-b 2.0.0 depends on shared-dep>=2.0.0
```

### Resolution Steps
1. Identify the conflicting dependency in `pyproject.toml`
2. Find compatible version range that satisfies both packages
3. Update version constraint: `shared-dep = ">=1.8.0,<2.1.0"`
4. Regenerate and test: `python scripts/generate-requirements.py && docker compose build`

### Version Pinning Strategy
- Use `^` for minor version flexibility: `package = "^1.2.0"` (allows 1.2.0 to <2.0.0)
- Use `~` for patch version flexibility: `package = "~1.2.0"` (allows 1.2.0 to <1.3.0)
- Use exact versions only when necessary: `package = "1.2.0"`

## Development Commands

```bash
# Check current dependencies
python scripts/generate-requirements.py --dry-run

# Regenerate all requirements files
python scripts/generate-requirements.py

# Rebuild specific service
docker compose build auth-service

# Rebuild all services
docker compose build

# View service dependencies
cat services/auth-service/requirements.txt

# Check for dependency conflicts
pip-compile --dry-run pyproject.toml
```

## Troubleshooting

### Build Failures After Dependency Changes
1. Clear Docker build cache: `docker system prune -f`
2. Regenerate requirements: `python scripts/generate-requirements.py`
3. Rebuild from scratch: `docker compose build --no-cache`

### Version Conflict Resolution
1. Check conflict details in build logs
2. Research compatible versions on PyPI
3. Update `pyproject.toml` with compatible range
4. Test build and functionality

### New Service Setup
1. Add service-specific dependencies to `pyproject.toml`
2. Run generation script to create requirements.txt
3. Reference generated file in service Dockerfile
4. Never bypass the centralized system

## Quality Assurance

### Pre-commit Checks
- Verify `requirements.txt` files are generated, not manually edited
- Ensure all services use same base dependency versions
- Test Docker builds after dependency changes

### CI/CD Integration
- Automated dependency vulnerability scanning
- Build verification for all services
- Version consistency validation across services

This centralized approach ensures consistent environments, reduces debugging complexity, and maintains scalability as the platform grows.