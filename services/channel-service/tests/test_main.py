"""
Basic tests for Channel Service
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch
import os

# Mock environment variables for testing
test_env_vars = {
    "DATABASE_URL": "postgresql+asyncpg://test:test@localhost:5432/test_db",
    "REDIS_URL": "redis://localhost:6379/3",
    "AUTH_SERVICE_URL": "http://localhost:8001",
    "AI_ENGINE_SERVICE_URL": "http://localhost:8003"
}

@patch.dict(os.environ, test_env_vars)
def test_import_main():
    """Test that main module can be imported without errors"""
    from app.main import app
    assert app is not None


@patch.dict(os.environ, test_env_vars)
def test_health_endpoint():
    """Test health check endpoint"""
    from app.main import app
    client = TestClient(app)
    
    response = client.get("/health")
    assert response.status_code == 200
    
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "channel-service"
    assert data["version"] == "1.0.0"
    assert "active_connections" in data


@patch.dict(os.environ, test_env_vars)
def test_root_endpoint():
    """Test root endpoint"""
    from app.main import app
    client = TestClient(app)
    
    response = client.get("/")
    assert response.status_code == 200
    
    data = response.json()
    assert data["message"] == "Channel Service API"
    assert data["version"] == "1.0.0"
    assert data["docs"] == "/docs"


@patch.dict(os.environ, test_env_vars)
def test_connections_endpoint():
    """Test active connections endpoint"""
    from app.main import app
    client = TestClient(app)
    
    response = client.get("/api/v1/channels/connections")
    assert response.status_code == 200
    
    data = response.json()
    assert "active_connections" in data
    assert "connection_ids" in data
    assert isinstance(data["active_connections"], int)
    assert isinstance(data["connection_ids"], list)


@patch.dict(os.environ, test_env_vars)
def test_websocket_endpoint():
    """Test WebSocket endpoint basic functionality"""
    from app.main import app
    client = TestClient(app)
    
    # Test WebSocket connection (basic test)
    with client.websocket_connect("/ws/test-session-id") as websocket:
        # Send a test message
        websocket.send_json({"message": "Hello, WebSocket!"})
        
        # Receive response
        data = websocket.receive_json()
        
        assert data["type"] == "response"
        assert "Echo: Hello, WebSocket!" in data["message"]
        assert data["session_id"] == "test-session-id"
        assert data["status"] == "not_implemented"


@patch.dict(os.environ, test_env_vars)
def test_not_implemented_endpoints():
    """Test that not-yet-implemented endpoints return 501"""
    from app.main import app
    client = TestClient(app)
    
    # Test POST endpoints
    post_endpoints = [
        "/api/v1/channels/sessions",
        "/api/v1/channels/messages"
    ]
    
    for endpoint in post_endpoints:
        response = client.post(endpoint)
        assert response.status_code == 501
        assert "will be implemented" in response.json()["detail"].lower()
    
    # Test GET endpoints
    get_endpoints = [
        "/api/v1/channels/sessions/test-id",
        "/api/v1/channels/messages/test-session-id"
    ]
    
    for endpoint in get_endpoints:
        response = client.get(endpoint)
        assert response.status_code == 501
        assert "will be implemented" in response.json()["detail"].lower()


def test_missing_environment_variables():
    """Test that missing environment variables raise RuntimeError"""
    with patch.dict(os.environ, {}, clear=True):
        with pytest.raises(RuntimeError) as exc_info:
            from app.main import app
        
        assert "Missing required environment variables" in str(exc_info.value)