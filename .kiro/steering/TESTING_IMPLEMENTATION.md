---
inclusion: always
---

# Testing Implementation Guidelines

## Test Organization Structure

### Directory Layout
```
tests/
├── conftest.py                    # Shared fixtures and configuration
├── integration/                   # Cross-service integration tests
├── e2e/                          # End-to-end user journey tests
└── shared/                       # Shared component tests

services/{service-name}/tests/     # Service-specific tests
```

### Test Categories
- **Unit Tests**: Individual functions/classes in isolation
- **Integration Tests**: Service interactions and database operations
- **End-to-End Tests**: Complete user workflows
- **Performance Tests**: Load testing and benchmarks
- **Security Tests**: Authentication, authorization, input validation

## Configuration Requirements

### Environment Configuration
- Use `shared/config/env_constants.py` for all service URLs
- Support dynamic URL resolution based on environment (dev/test/CI)
- Test containers for PostgreSQL and Redis isolation

### Test Database Setup
- Separate test database with RLS policies enabled
- Automatic schema migrations before test runs
- Proper tenant isolation testing with `creator_id` context

## Test Execution

### Essential Commands
```bash
make test                         # Run all tests
pytest tests/integration/        # Integration tests only
pytest services/{service}/tests/ # Service-specific tests
pytest --cov=shared --cov=services --cov-report=html # With coverage
```

### Required Test Markers
```python
@pytest.mark.unit           # Unit tests
@pytest.mark.integration    # Integration tests
@pytest.mark.e2e           # End-to-end tests
@pytest.mark.performance   # Performance benchmarks
@pytest.mark.security      # Security validation
```

## Service Testing Requirements

### Auth Service (8001)
- JWT token lifecycle (creation, validation, refresh)
- Password security (bcrypt, strength validation)
- Rate limiting per IP and user
- Multi-tenant data isolation with RLS

### AI Engine Service (8003)
- Ollama model integration (embeddings, chat completion)
- ChromaDB operations (per-tenant collections)
- RAG pipeline accuracy and performance
- Context window management

### Creator Hub Service (8002)
- Document processing workflows
- Widget configuration and embed code generation
- File upload security and validation

### Channel Service (8004)
- WebSocket connection lifecycle
- Message routing and broadcasting
- Real-time communication reliability

## Test Fixtures & Mocking

### Required Fixtures
- `test_user_data`: Standard test user with valid credentials
- `authenticated_user`: User with JWT token and auth headers
- `tenant_session`: Database session with `creator_id` context set
- `service_clients`: HTTP clients for all services

### Mock External Services
- Mock Ollama for AI model responses
- Mock ChromaDB for vector operations
- Mock Redis for caching tests
- Use `AsyncMock` for async service calls

## CI/CD Pipeline

### Quality Gates
1. Code formatting (black, isort)
2. Type checking (mypy)
3. Security scanning (bandit)
4. Unit tests with 90% coverage
5. Integration tests with Docker Compose
6. Performance benchmarks

### Test Environment
- Use `docker-compose.test.yml` for isolated test services
- PostgreSQL test database on port 5433
- Redis test instance on port 6380

## Performance Testing

### Benchmarks
- API endpoints: < 200ms response time (95th percentile)
- Database queries: < 100ms for standard operations
- AI processing: < 5s for embedding generation
- WebSocket: Support 1000+ concurrent connections

### Load Testing Patterns
```python
@pytest.mark.performance
async def test_concurrent_requests():
    """Test service under concurrent load."""
    # Use asyncio.gather for concurrent requests
    # Assert response times and success rates
    # Monitor memory usage with psutil
```

## Security Testing

### Authentication Security
- JWT token expiration and tampering detection
- Password strength validation and bcrypt hashing
- Rate limiting enforcement (429 status codes)
- Session management and cleanup

### Input Validation
- SQL injection protection (parameterized queries)
- XSS prevention (input sanitization)
- File upload security (MIME type validation)
- Domain validation for widget configuration

### Data Protection
- Multi-tenant data isolation with RLS
- Sensitive data encryption at rest
- Audit logging for security events

## Testing Best Practices

### Test Writing Guidelines
- Use descriptive test names that explain the scenario
- Follow Arrange-Act-Assert pattern
- Ensure test independence (no shared state)
- Test both success and failure scenarios
- Use realistic test data

### Async Testing
- Use `pytest-asyncio` for async test support
- Proper async context managers for database sessions
- Avoid blocking operations in async tests
- Use `AsyncMock` for mocking async dependencies

### Debugging
```bash
pytest -v -s                    # Verbose output
pytest --pdb                    # Debug on failure
pytest --cov-report=term-missing # Coverage gaps
```

## Quality Requirements

### Coverage Standards
- Unit tests: 90% minimum code coverage
- Integration tests: All API endpoints must be tested
- Multi-tenant isolation: Verify RLS policies work correctly
- Error handling: Test all exception paths

### Performance Benchmarks
- API endpoints: < 200ms response time (95th percentile)
- Database operations: < 100ms for standard queries
- AI processing: < 5s for embedding generation
- WebSocket handling: 1000+ concurrent connections

### Test Data Management
- Use factories for consistent test data generation
- Implement proper cleanup after each test
- Isolate test data by tenant/creator
- Mock external services for reliability