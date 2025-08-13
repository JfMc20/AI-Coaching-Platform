"""
Auth service specific pytest configuration.
Provides fixtures for authentication testing, database setup, and mock data.
"""

import pytest
import pytest_asyncio
from httpx import AsyncClient
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from services.auth_service.app.main import app
from services.auth_service.app.database import get_db
from shared.models.database import Base
from shared.security.jwt_manager import JWTManager
from shared.security.password_security import PasswordSecurity


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    import asyncio
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def test_engine():
    """Create test database engine."""
    # Use in-memory SQLite for fast testing
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=True)
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    await engine.dispose()


@pytest.fixture
async def db_session(test_engine):
    """Create database session for each test."""
    async_session = sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session() as session:
        yield session
        await session.rollback()


@pytest.fixture
def override_get_db(db_session):
    """Override database dependency for testing."""
    async def _override_get_db():
        yield db_session
    
    app.dependency_overrides[get_db] = _override_get_db
    yield
    app.dependency_overrides.clear()


@pytest.fixture
async def client(override_get_db):
    """Create test client for auth service."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def test_user_data():
    """Provide test user data."""
    return {
        "email": "test@example.com",
        "password": "TestPassword123!",
        "full_name": "Test User",
        "tenant_id": "test-tenant"
    }


@pytest.fixture
def test_users_data():
    """Provide multiple test users data."""
    return [
        {
            "email": "user1@example.com",
            "password": "Password123!",
            "full_name": "User One",
            "tenant_id": "tenant-1"
        },
        {
            "email": "user2@example.com",
            "password": "Password123!",
            "full_name": "User Two",
            "tenant_id": "tenant-2"
        },
        {
            "email": "user3@example.com",
            "password": "Password123!",
            "full_name": "User Three",
            "tenant_id": "tenant-1"  # Same tenant as user1
        }
    ]


@pytest.fixture
async def registered_user(client, test_user_data):
    """Create and return a registered user."""
    response = await client.post("/api/v1/auth/register", json=test_user_data)
    assert response.status_code == 201
    return response.json()


@pytest.fixture
async def authenticated_user(client, test_user_data, registered_user):
    """Create authenticated user with token."""
    login_response = await client.post("/api/v1/auth/login", json={
        "email": test_user_data["email"],
        "password": test_user_data["password"]
    })
    assert login_response.status_code == 200
    
    token_data = login_response.json()
    return {
        "user": registered_user,
        "token": token_data["access_token"],
        "refresh_token": token_data["refresh_token"],
        "headers": {"Authorization": f"Bearer {token_data['access_token']}"}
    }


@pytest.fixture
def jwt_manager():
    """Provide JWT manager for testing."""
    return JWTManager()


@pytest.fixture
def password_security():
    """Provide password security manager for testing."""
    return PasswordSecurity()


@pytest.fixture
def mock_jwt_payload():
    """Provide mock JWT payload for testing."""
    return {
        "sub": "test@example.com",
        "user_id": "123",
        "tenant_id": "test-tenant",
        "exp": 1234567890,
        "iat": 1234567890
    }


@pytest.fixture
async def multiple_registered_users(client, test_users_data):
    """Register multiple test users."""
    users = []
    for user_data in test_users_data:
        response = await client.post("/api/v1/auth/register", json=user_data)
        assert response.status_code == 201
        users.append(response.json())
    return users