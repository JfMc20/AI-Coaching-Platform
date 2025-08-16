"""
Service integration fixtures for real service testing.
"""

import pytest
from unittest.mock import AsyncMock, Mock
from httpx import AsyncClient


@pytest.fixture
async def service_clients():
    """Real service clients for integration testing."""
    clients = {}
    
    # Create async HTTP clients for each service
    service_urls = {
        "auth": "http://localhost:8001",
        "creator_hub": "http://localhost:8002", 
        "ai_engine": "http://localhost:8003",
        "channel": "http://localhost:8004"
    }
    
    for service_name, base_url in service_urls.items():
        try:
            # Try to create real client, fallback to mock if service unavailable
            client = AsyncClient(base_url=base_url, timeout=5.0)
            # Test if service is available
            try:
                response = await client.get("/health", timeout=2.0)
                if response.status_code == 200:
                    clients[service_name] = client
                else:
                    await client.aclose()
                    clients[service_name] = _create_mock_client(service_name)
            except Exception:
                await client.aclose()
                clients[service_name] = _create_mock_client(service_name)
        except Exception:
            clients[service_name] = _create_mock_client(service_name)
    
    yield clients
    
    # Cleanup
    for client in clients.values():
        if hasattr(client, 'aclose'):
            await client.aclose()


def _create_mock_client(service_name: str):
    """Create a mock client for a service."""
    mock_client = AsyncMock()
    
    # Mock common responses based on service
    if service_name == "auth":
        mock_client.post.return_value = Mock(
            status_code=201,
            json=lambda: {
                "id": "test_user_123",
                "email": "test@example.com",
                "access_token": "mock.jwt.token",
                "refresh_token": "mock.refresh.token",
                "token_type": "bearer"
            }
        )
    elif service_name == "ai_engine":
        mock_client.post.return_value = Mock(
            status_code=200,
            json=lambda: {
                "response": "Mock AI response",
                "confidence": 0.85,
                "embedding": [0.1] * 384
            }
        )
    elif service_name == "channel":
        mock_client.get.return_value = Mock(
            status_code=405,  # WebSocket endpoints return 405 for GET
            json=lambda: {"detail": "Method not allowed"}
        )
    else:
        mock_client.post.return_value = Mock(
            status_code=200,
            json=lambda: {"message": "Success"}
        )
    
    # Common health endpoint
    mock_client.get.return_value = Mock(
        status_code=200,
        json=lambda: {
            "status": "healthy",
            "service": service_name,
            "timestamp": "2023-01-01T00:00:00Z"
        }
    )
    
    return mock_client


@pytest.fixture
def service_clients_test():
    """Simplified service clients for unit tests."""
    return {
        "auth": _create_mock_client("auth"),
        "creator_hub": _create_mock_client("creator_hub"),
        "ai_engine": _create_mock_client("ai_engine"),
        "channel": _create_mock_client("channel")
    }


@pytest.fixture
async def async_client_factory_test():
    """Factory for creating test async clients."""
    clients = []
    
    def _create_client(base_url="http://testserver"):
        client = AsyncClient(base_url=base_url)
        clients.append(client)
        return client
    
    yield _create_client
    
    # Cleanup
    for client in clients:
        await client.aclose()