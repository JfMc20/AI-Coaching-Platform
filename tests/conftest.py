"""
Centralized pytest configuration for all tests.
Provides common fixtures and imports service-specific fixtures.

Fixture Organization:
- Common fixtures (event_loop, clients, database) are defined here
- Service-specific fixtures are in tests/fixtures/ modules
- All fixtures are automatically available to tests through pytest_plugins

Docker Dependencies:
- PostgreSQL and Redis fixtures require Docker to be available
- If Docker is not available, database-dependent tests will be skipped
- Fallback to in-memory SQLite for basic database tests when PostgreSQL is unavailable
"""

import asyncio
import os
import sys
import pytest
import pytest_asyncio
from pathlib import Path
from httpx import AsyncClient
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from testcontainers.postgres import PostgresContainer
from testcontainers.redis import RedisContainer


def enable_namespace_bridging():
    """Enable namespace bridging for hyphenated service directories."""
    import importlib.util
    import types
    from pathlib import Path
    
    # Get absolute repo root path
    repo_root = Path(__file__).resolve().parent.parent
    
    # Create parent 'services' package if it doesn't exist
    if 'services' not in sys.modules:
        services_module = types.ModuleType('services')
        services_module.__path__ = [str(repo_root / "services")]
        sys.modules['services'] = services_module
    
    # Create namespace bridging for services with hyphens
    service_mappings = {
        'services.auth_service': repo_root / "services" / "auth-service",
        'services.ai_engine_service': repo_root / "services" / "ai-engine-service", 
        'services.channel_service': repo_root / "services" / "channel-service",
        'services.creator_hub_service': repo_root / "services" / "creator-hub-service"
    }
    
    for module_name, directory_path in service_mappings.items():
        if not directory_path.exists():
            print(f"[tests] Skipping namespace for {module_name}: {directory_path} not found")
            continue
            
        if module_name not in sys.modules:
            # Create a namespace module with proper __path__
            namespace_module = types.ModuleType(module_name)
            namespace_module.__path__ = [str(directory_path)]
            sys.modules[module_name] = namespace_module


# Enable namespace bridging automatically
enable_namespace_bridging()

# Import all service-specific fixture modules
pytest_plugins = [
    'tests.fixtures.auth_fixtures',
    'tests.fixtures.ai_fixtures', 
    'tests.fixtures.channel_fixtures',
    'tests.fixtures.creator_hub_fixtures'
]

# Simplified configuration without shared module dependencies
AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL", "http://localhost:8001")
AI_ENGINE_SERVICE_URL = os.getenv("AI_ENGINE_SERVICE_URL", "http://localhost:8003")
CREATOR_HUB_SERVICE_URL = os.getenv("CREATOR_HUB_SERVICE_URL", "http://localhost:8002")
CHANNEL_SERVICE_URL = os.getenv("CHANNEL_SERVICE_URL", "http://localhost:8004")


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def test_client_factory():
    """Factory for creating test clients for any FastAPI app."""
    def _create_client(app):
        return TestClient(app)
    return _create_client


@pytest.fixture
async def async_client_factory():
    """Factory for creating async HTTP clients for any FastAPI app."""
    clients = []
    
    def _create_client(app, base_url="http://test"):
        client = AsyncClient(app=app, base_url=base_url)
        clients.append(client)
        return client
    
    yield _create_client
    
    # Cleanup all created clients
    for client in clients:
        await client.aclose()


@pytest.fixture(scope="session")
def postgres_container():
    """Start PostgreSQL test container."""
    try:
        with PostgresContainer("postgres:15") as postgres:
            yield postgres
    except Exception as e:
        pytest.skip(f"PostgreSQL container not available: {e}")


@pytest.fixture(scope="session")
def redis_container():
    """Start Redis test container."""
    try:
        with RedisContainer("redis:7") as redis:
            yield redis
    except Exception as e:
        pytest.skip(f"Redis container not available: {e}")


@pytest_asyncio.fixture(scope="session")
async def test_db_engine(postgres_container):
    """Create async database engine for testing."""
    try:
        database_url = postgres_container.get_connection_url().replace("postgresql://", "postgresql+asyncpg://")
        engine = create_async_engine(database_url, echo=False)
        
        # Skip table creation for now since we don't have Base model
        # async with engine.begin() as conn:
        #     await conn.run_sync(Base.metadata.create_all)
        
        yield engine
        await engine.dispose()
    except Exception as e:
        # Fallback to in-memory SQLite for basic testing
        engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
        yield engine
        await engine.dispose()


@pytest_asyncio.fixture(scope="session")
async def test_redis_client(redis_container):
    """Create Redis client for testing."""
    try:
        import redis.asyncio as aioredis
        redis_url = f"redis://localhost:{redis_container.get_exposed_port(6379)}"
        client = aioredis.from_url(redis_url)
        yield client
        await client.close()
    except Exception as e:
        pytest.skip(f"Redis client not available: {e}")


@pytest_asyncio.fixture
async def common_db_session(test_db_engine):
    """Create async database session for each test."""
    async_session = sessionmaker(
        test_db_engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session() as session:
        yield session
        await session.rollback()


@pytest.fixture
def common_test_user_data():
    """Provide common test user data for cross-service tests."""
    return {
        "email": "integration@example.com",
        "password": "IntegrationTest123!",
        "full_name": "Integration Test User",
        "tenant_id": "integration-tenant"
    }


@pytest.fixture
def common_auth_headers():
    """Provide common authentication headers for integration tests."""
    return {
        "Authorization": "Bearer integration-test-token",
        "Content-Type": "application/json"
    }


@pytest_asyncio.fixture
async def service_clients():
    """Provide HTTP clients for all services."""
    clients = {
        "auth": AsyncClient(base_url=AUTH_SERVICE_URL),
        "creator_hub": AsyncClient(base_url=CREATOR_HUB_SERVICE_URL),
        "ai_engine": AsyncClient(base_url=AI_ENGINE_SERVICE_URL),
        "channel": AsyncClient(base_url=CHANNEL_SERVICE_URL)
    }
    
    yield clients
    
    for client in clients.values():
        await client.aclose()


@pytest_asyncio.fixture
async def cleanup_test_data(test_redis_client):
    """Clean up test data after each test."""
    yield
    # Clean up Redis test data
    try:
        await test_redis_client.flushdb()
    except Exception:
        pass  # Ignore cleanup errors