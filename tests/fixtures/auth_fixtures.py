"""
Auth service fixtures.
"""

import pytest
from unittest.mock import AsyncMock, Mock, patch


@pytest.fixture
def jwt_manager():
    """JWT manager for testing - properly mocked to avoid key file dependencies."""
    with patch('shared.security.jwt_manager.JWTManager') as mock_class:
        mock_instance = Mock()
        mock_instance.create_access_token.return_value = "test.access.token"
        mock_instance.create_refresh_token.return_value = "test.refresh.token"
        mock_instance.verify_token.return_value = {
            "sub": "test_user_123",
            "creator_id": "test_creator_123",
            "permissions": ["read", "write"],
            "exp": 9999999999  # Far future
        }
        mock_instance.refresh_access_token.return_value = "new.access.token"
        mock_class.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def password_hasher():
    """Password hasher for testing."""
    from shared.security.password_security import PasswordHasher
    return PasswordHasher()


@pytest.fixture
def auth_client():
    """Mock auth service client for testing."""
    client = AsyncMock()
    client.post.return_value = Mock(
        status_code=201,
        json=lambda: {
            "id": "test_user_123",
            "email": "test@example.com",
            "full_name": "Test User",
            "created_at": "2023-01-01T00:00:00Z"
        }
    )
    client.get.return_value = Mock(
        status_code=200,
        json=lambda: {"status": "healthy", "timestamp": "2023-01-01T00:00:00Z"}
    )
    return client


@pytest.fixture
def registered_user():
    """Pre-registered test user data."""
    return {
        "id": "test_user_123",
        "email": "registered@example.com",
        "full_name": "Registered User",
        "is_active": True,
        "created_at": "2023-01-01T00:00:00Z"
    }


@pytest.fixture
def authenticated_user():
    """Authenticated user with valid token."""
    return {
        "user": {
            "id": "test_user_123",
            "email": "authenticated@example.com",
            "full_name": "Authenticated User"
        },
        "token": "valid.jwt.token",
        "refresh_token": "valid.refresh.token"
    }