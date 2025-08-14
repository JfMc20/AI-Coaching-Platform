"""
Channel service specific fixtures.
Provides fixtures for WebSocket testing and real-time communication features.
"""

import pytest
import pytest_asyncio
from httpx import AsyncClient
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, Mock

try:
    from services.channel_service.app.main import app
except ImportError:
    # Channel service might have missing dependencies in test environment
    app = None


@pytest_asyncio.fixture
async def channel_client():
    """Create test client for channel service."""
    if app is None:
        pytest.skip("services.channel_service.app.main.app not available")
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def websocket_client():
    """Create WebSocket test client."""
    if app is None:
        pytest.skip("services.channel_service.app.main.app not available")
    return TestClient(app)


@pytest.fixture
def mock_connection_manager():
    """Mock WebSocket connection manager."""
    mock = Mock()
    mock.active_connections = {}
    mock.connect = AsyncMock()
    mock.disconnect = AsyncMock()
    mock.send_personal_message = AsyncMock()
    mock.broadcast = AsyncMock()
    mock.get_connection_count = Mock(return_value=0)
    return mock


@pytest.fixture
def test_websocket_session():
    """Provide test WebSocket session data."""
    return {
        "session_id": "test-session-123",
        "user_id": "user-456",
        "tenant_id": "test-tenant"
    }


@pytest.fixture
def test_message_data():
    """Provide test message data for WebSocket communication."""
    return {
        "type": "chat_message",
        "content": "Hello, this is a test message",
        "sender_id": "user-123",
        "timestamp": "2023-12-01T10:00:00Z",
        "metadata": {
            "channel": "web",
            "session_id": "test-session-123"
        }
    }


@pytest.fixture
def test_notification_data():
    """Provide test notification data."""
    return {
        "type": "notification",
        "title": "Test Notification",
        "message": "This is a test notification",
        "priority": "normal",
        "recipient_id": "user-123",
        "metadata": {
            "category": "coaching",
            "action_required": False
        }
    }


@pytest.fixture
def mock_message_queue():
    """Mock message queue for testing."""
    mock = AsyncMock()
    mock.publish = AsyncMock()
    mock.subscribe = AsyncMock()
    mock.get_messages = AsyncMock(return_value=[])
    return mock


@pytest.fixture
def test_channel_config():
    """Provide test channel configuration."""
    return {
        "channel_id": "test-channel-1",
        "name": "Test Channel",
        "type": "websocket",
        "settings": {
            "max_connections": 1000,
            "message_rate_limit": 10,
            "auto_reconnect": True
        },
        "enabled": True
    }


@pytest.fixture
def multiple_test_sessions():
    """Provide multiple test sessions for concurrent testing."""
    return [
        {
            "session_id": f"session-{i}",
            "user_id": f"user-{i}",
            "tenant_id": "test-tenant"
        }
        for i in range(5)
    ]