---
inclusion: fileMatch
fileMatchPattern: ['tests/**/*.py', 'conftest.py']
---

# Test Fixture Organization Guidelines

## Centralized Fixture Architecture
All test fixtures are consolidated into a centralized system under `tests/fixtures/` to eliminate duplication and ensure consistency across services.

## Fixture Structure

### Directory Organization
```
tests/
├── conftest.py                    # Main configuration with pytest_plugins
├── fixtures/
│   ├── __init__.py               # Package initialization
│   ├── auth_fixtures.py          # Auth service fixtures
│   ├── ai_fixtures.py            # AI engine service fixtures
│   ├── channel_fixtures.py       # Channel service fixtures
│   └── creator_hub_fixtures.py   # Creator hub service fixtures
```

### Configuration Rules
- **Main conftest.py**: Contains `pytest_plugins` configuration to auto-load all fixture modules
- **Service-specific fixtures**: Isolated in dedicated modules under `tests/fixtures/`
- **No duplicate conftest.py files**: Service-specific conftest.py files are prohibited
- **Import resilience**: Fixture modules must handle missing dependencies gracefully

## Available Fixtures

### Common Fixtures (tests/conftest.py)
- `event_loop` - Async event loop for all tests
- `test_client_factory` - Factory for creating FastAPI test clients  
- `async_client_factory` - Factory for creating async HTTP clients
- `common_test_user_data` - Common user data for integration tests
- `common_auth_headers` - Common auth headers for integration tests

### Service-Specific Fixtures

#### Auth Service (tests.fixtures.auth_fixtures)
- `auth_client` - Auth service test client
- `test_user_data` - Auth-specific user data
- `registered_user` - Pre-registered test user
- `authenticated_user` - User with valid JWT token
- `jwt_manager` - JWT token manager
- `password_hasher` - Password hashing utilities

#### AI Engine Service (tests.fixtures.ai_fixtures)
- `ai_client` - AI engine test client
- `mock_ollama_manager` - Mocked Ollama integration
- `mock_chromadb_manager` - Mocked ChromaDB integration
- `test_embedding_request` - Sample embedding requests
- `test_chat_request` - Sample chat requests

#### Channel Service (tests.fixtures.channel_fixtures)
- `channel_client` - Channel service test client
- `websocket_client` - WebSocket test client
- `mock_connection_manager` - Mocked WebSocket manager
- `test_websocket_session` - WebSocket session data

#### Creator Hub Service (tests.fixtures.creator_hub_fixtures)
- `creator_hub_client` - Creator hub test client
- `mock_auth_service` - Mocked auth service responses
- `mock_ai_engine_service` - Mocked AI engine responses
- `test_creator_profile` - Sample creator profile data

## Usage Patterns

### Automatic Fixture Loading
Fixtures are automatically available through `pytest_plugins` configuration - no imports needed:

```python
async def test_auth_endpoint(auth_client, test_user_data):
    response = await auth_client.post("/register", json=test_user_data)
    assert response.status_code == 201
```

### Fixture Naming Conventions
- **Service clients**: `{service}_client` (e.g., `auth_client`, `ai_client`)
- **Mock objects**: `mock_{component}` (e.g., `mock_ollama_manager`)
- **Test data**: `test_{data_type}` (e.g., `test_user_data`, `test_message_data`)
- **Common fixtures**: `common_{purpose}` (e.g., `common_test_user_data`)

### Adding New Fixtures
1. **Service-specific**: Add to appropriate module in `tests/fixtures/`
2. **Common fixtures**: Add to `tests/conftest.py`
3. **Follow naming conventions**: Use consistent naming patterns
4. **Handle dependencies**: Make imports resilient to missing dependencies

### Error Handling Requirements
- Fixture modules must gracefully handle missing service dependencies
- Use try/except blocks for service imports
- Provide meaningful error messages for missing dependencies
- Ensure tests can run even if some services are unavailable