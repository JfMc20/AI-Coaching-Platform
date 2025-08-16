"""
Common fixtures shared across all services.
"""

import pytest
from unittest.mock import Mock
from httpx import AsyncClient


@pytest.fixture
def test_user_data():
    """Standard test user data for all services."""
    return {
        "email": "test@example.com",
        "password": "TestPassword123!",
        "full_name": "Test User",
        "company_name": "Test Company"
    }


@pytest.fixture
def common_test_user_data():
    """Common user data for integration tests."""
    return {
        "email": "integration@example.com",
        "password": "IntegrationTest123!",
        "full_name": "Integration Test User",
        "company_name": "Integration Test Company"
    }


@pytest.fixture
def common_auth_headers():
    """Common auth headers for integration tests."""
    return {
        "Authorization": "Bearer test-token",
        "Content-Type": "application/json"
    }


@pytest.fixture
async def test_client_factory():
    """Factory for creating FastAPI test clients."""
    clients = []
    
    def _create_client(app, base_url="http://testserver"):
        from fastapi.testclient import TestClient
        client = TestClient(app, base_url=base_url)
        clients.append(client)
        return client
    
    yield _create_client
    
    # Cleanup
    for client in clients:
        client.close()


@pytest.fixture
async def async_client_factory():
    """Factory for creating async HTTP clients."""
    clients = []
    
    def _create_client(base_url="http://testserver"):
        client = AsyncClient(base_url=base_url)
        clients.append(client)
        return client
    
    yield _create_client
    
    # Cleanup
    for client in clients:
        await client.aclose()


@pytest.fixture
def service_clients():
    """Mock service clients for integration testing."""
    return {
        "auth": Mock(),
        "creator_hub": Mock(),
        "ai_engine": Mock(),
        "channel": Mock()
    }


@pytest.fixture
def cleanup_test_data():
    """Fixture for test data cleanup."""
    yield
    # Cleanup logic would go here


@pytest.fixture
def password_security():
    """Password security utilities for testing."""
    from shared.security.password_security import PasswordHasher
    return PasswordHasher()


@pytest.fixture
def verification_test_data():
    """Test data for verification tests."""
    return {
        "test_string": "verification_test",
        "test_number": 42,
        "test_list": ["item1", "item2", "item3"]
    }