"""
Shared pytest configuration for integration and end-to-end tests.
Provides async database and Redis fixtures for cross-service testing.
"""

import asyncio
import os
import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from testcontainers.postgres import PostgresContainer
from testcontainers.redis import RedisContainer

# Simplified configuration without shared module dependencies
AUTH_SERVICE_URL = "http://localhost:8001"
AI_ENGINE_SERVICE_URL = "http://localhost:8003"
CREATOR_HUB_SERVICE_URL = "http://localhost:8002"
CHANNEL_SERVICE_URL = "http://localhost:8004"

def get_env_value(key, fallback=True):
    """Get environment value with fallback."""
    return os.getenv(key, key)  # Return the key itself as fallback


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def postgres_container():
    """Start PostgreSQL test container."""
    with PostgresContainer("postgres:15") as postgres:
        yield postgres


@pytest.fixture(scope="session")
async def redis_container():
    """Start Redis test container."""
    with RedisContainer("redis:7") as redis:
        yield redis


@pytest.fixture(scope="session")
async def test_db_engine(postgres_container):
    """Create async database engine for testing."""
    database_url = postgres_container.get_connection_url().replace("postgresql://", "postgresql+asyncpg://")
    engine = create_async_engine(database_url, echo=False)
    
    # Skip table creation for now since we don't have Base model
    # async with engine.begin() as conn:
    #     await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    await engine.dispose()


@pytest.fixture(scope="session")
async def test_redis_client(redis_container):
    """Create Redis client for testing."""
    import redis.asyncio as aioredis
    redis_url = f"redis://localhost:{redis_container.get_exposed_port(6379)}"
    client = aioredis.from_url(redis_url)
    yield client
    await client.close()


@pytest.fixture
async def db_session(test_db_engine):
    """Create async database session for each test."""
    async_session = sessionmaker(
        test_db_engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session() as session:
        yield session
        await session.rollback()


@pytest.fixture
async def test_user_data():
    """Provide test user data for authentication tests."""
    return {
        "email": "test@example.com",
        "password": "TestPassword123!",
        "full_name": "Test User",
        "tenant_id": "test-tenant"
    }


@pytest.fixture
async def auth_headers(test_user_data):
    """Provide authentication headers for API tests."""
    # This will be implemented once auth service tests are created
    return {"Authorization": "Bearer test-token"}


@pytest.fixture
async def service_clients():
    """Provide HTTP clients for all services."""
    # Get service URLs from centralized configuration
    auth_url = get_env_value(AUTH_SERVICE_URL, fallback=True)
    ai_engine_url = get_env_value(AI_ENGINE_SERVICE_URL, fallback=True)
    creator_hub_url = get_env_value(CREATOR_HUB_SERVICE_URL, fallback=True)
    channel_url = get_env_value(CHANNEL_SERVICE_URL, fallback=True)
    
    clients = {
        "auth": AsyncClient(base_url=auth_url),
        "creator_hub": AsyncClient(base_url=creator_hub_url),
        "ai_engine": AsyncClient(base_url=ai_engine_url),
        "channel": AsyncClient(base_url=channel_url)
    }
    
    yield clients
    
    for client in clients.values():
        await client.aclose()


@pytest.fixture(autouse=True)
async def cleanup_test_data(test_redis_client):
    """Clean up test data after each test."""
    yield
    # Clean up Redis test data
    try:
        await test_redis_client.flushdb()
    except Exception:
        pass  # Ignore cleanup errors