"""
Auth service specific fixtures.
Provides fixtures for authentication testing, database setup, and mock data.
"""

import pytest
import pytest_asyncio
import time
from httpx import AsyncClient
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from testcontainers.postgres import PostgresContainer

try:
    from services.auth_service.app.main import app
    from services.auth_service.app.database import get_db
except ImportError:
    app = None
    get_db = None

from shared.models.database import Base
try:
    from shared.security.jwt_manager import JWTManager
except ImportError:
    JWTManager = None

try:
    from shared.security.password_security import PasswordHasher, PasswordValidator
except ImportError:
    PasswordHasher = None
    PasswordValidator = None


@pytest_asyncio.fixture(scope="session")
async def test_engine(test_db_engine):
    """Use shared test database engine and create auth tables."""
    # Ensure all models are imported so Base.metadata sees them
    import importlib
    model_modules = [
        'shared.models.database',
        'shared.models.auth',
    ]
    
    for module in model_modules:
        try:
            importlib.import_module(module)
        except ImportError:
            pass  # Skip if module doesn't exist
    
    # Create all tables
    async with test_db_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield test_db_engine


@pytest_asyncio.fixture
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
    if app is None or get_db is None:
        pytest.skip("auth service app or get_db not available")
    
    async def _override_get_db():
        yield db_session
    
    app.dependency_overrides[get_db] = _override_get_db
    try:
        yield
    finally:
        app.dependency_overrides.pop(get_db, None)


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


@pytest_asyncio.fixture
async def registered_user(auth_client, test_user_data):
    """Create and return a registered user."""
    response = await auth_client.post("/api/v1/auth/register", json=test_user_data)
    assert response.status_code == 201
    return response.json()


@pytest_asyncio.fixture
async def authenticated_user(auth_client, test_user_data, registered_user):
    """Create authenticated user with token."""
    login_response = await auth_client.post("/api/v1/auth/login", json={
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
    try:
        from shared.security.jwt_manager import JWTManager
        return JWTManager()
    except ImportError:
        pytest.skip("JWTManager not available; skipping JWT tests")


@pytest.fixture
def password_hasher():
    """Provide password hasher for testing."""
    if PasswordHasher:
        return PasswordHasher()
    return None


@pytest.fixture
def password_validator():
    """Provide password validator for testing."""
    if PasswordValidator:
        return PasswordValidator()
    return None


@pytest.fixture
def password_security():
    """Provide password security instance for testing."""
    try:
        from shared.security.password_security import PasswordSecurity
        return PasswordSecurity()
    except ImportError:
        pytest.skip("PasswordSecurity not available; skipping security tests")


@pytest.fixture
def mock_jwt_payload():
    """Provide mock JWT payload for testing."""
    current_time = int(time.time())
    return {
        "sub": "test@example.com",
        "user_id": "123",
        "tenant_id": "test-tenant",
        "iat": current_time,
        "exp": current_time + 3600  # Expires in 1 hour
    }


@pytest_asyncio.fixture
async def multiple_registered_users(auth_client, test_users_data):
    """Register multiple test users."""
    users = []
    for user_data in test_users_data:
        response = await auth_client.post("/api/v1/auth/register", json=user_data)
        assert response.status_code == 201
        users.append(response.json())
    return users


@pytest_asyncio.fixture
async def auth_client(override_get_db):
    """Create test client for auth service."""
    if app is None:
        pytest.skip("auth service app not available")
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac