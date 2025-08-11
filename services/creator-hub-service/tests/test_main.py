"""
Basic tests for Creator Hub Service
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch
import os

# Mock environment variables for testing
test_env_vars = {
    "DATABASE_URL": "postgresql+asyncpg://test:test@localhost:5432/test_db",
    "REDIS_URL": "redis://localhost:6379/1",
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
    assert data["service"] == "creator-hub-service"
    assert data["version"] == "1.0.0"


@patch.dict(os.environ, test_env_vars)
def test_root_endpoint():
    """Test root endpoint"""
    from app.main import app
    client = TestClient(app)
    
    response = client.get("/")
    assert response.status_code == 200
    
    data = response.json()
    assert data["message"] == "Creator Hub Service API"
    assert data["version"] == "1.0.0"
    assert data["docs"] == "/docs"


@patch.dict(os.environ, test_env_vars)
def test_not_implemented_endpoints():
    """Test that not-yet-implemented endpoints return 501"""
    from app.main import app
    client = TestClient(app)
    
    # Test GET endpoints
    get_endpoints = [
        "/api/v1/creators/profile",
        "/api/v1/creators/dashboard/metrics",
        "/api/v1/creators/knowledge/documents",
        "/api/v1/creators/widget/config",
        "/api/v1/creators/widget/embed-code",
        "/api/v1/creators/conversations",
        "/api/v1/creators/conversations/test-id"
    ]
    
    for endpoint in get_endpoints:
        response = client.get(endpoint)
        assert response.status_code == 501
        assert "will be implemented" in response.json()["detail"].lower()
    
    # Test POST endpoints
    post_endpoints = [
        "/api/v1/creators/knowledge/upload"
    ]
    
    for endpoint in post_endpoints:
        response = client.post(endpoint)
        assert response.status_code == 501
        assert "will be implemented" in response.json()["detail"].lower()
    
    # Test PUT endpoints
    put_endpoints = [
        "/api/v1/creators/profile",
        "/api/v1/creators/widget/config"
    ]
    
    for endpoint in put_endpoints:
        response = client.put(endpoint)
        assert response.status_code == 501
        assert "will be implemented" in response.json()["detail"].lower()
    
    # Test DELETE endpoints
    response = client.delete("/api/v1/creators/knowledge/documents/test-id")
    assert response.status_code == 501
    assert "will be implemented" in response.json()["detail"].lower()


def test_missing_environment_variables():
    """Test that missing environment variables raise RuntimeError"""
    with patch.dict(os.environ, {}, clear=True):
        with pytest.raises(RuntimeError) as exc_info:
            from app.main import app
        
        assert "Missing required environment variables" in str(exc_info.value)