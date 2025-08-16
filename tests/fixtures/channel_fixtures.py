"""
Channel service fixtures.
"""

import pytest
from unittest.mock import AsyncMock, Mock


@pytest.fixture
def mock_connection_manager():
    """Mock WebSocket connection manager for testing."""
    mock = AsyncMock()
    mock.connect.return_value = None
    mock.disconnect.return_value = None
    mock.send_message.return_value = True
    mock.broadcast_to_creator.return_value = True
    mock.get_creator_connections.return_value = ["conn1", "conn2"]
    mock.health_check.return_value = {"status": "healthy", "active_connections": 2}
    return mock


@pytest.fixture
def channel_client():
    """Mock channel service client for testing."""
    client = AsyncMock()
    client.get.return_value = Mock(
        status_code=200,
        json=lambda: {"status": "healthy", "timestamp": "2023-01-01T00:00:00Z"}
    )
    client.post.return_value = Mock(
        status_code=200,
        json=lambda: {"message": "Success"}
    )
    return client


@pytest.fixture
def websocket_client():
    """Mock WebSocket client for testing."""
    client = AsyncMock()
    client.connect.return_value = None
    client.send_json.return_value = None
    client.receive_json.return_value = {"type": "message", "content": "test"}
    client.close.return_value = None
    return client


@pytest.fixture
def test_websocket_session():
    """Test WebSocket session data."""
    return {
        "session_id": "test_session_123",
        "creator_id": "test_creator_456",
        "user_id": "test_user_789",
        "channel": "widget"
    }