"""
Basic tests for Auth Service
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch
import os

# Mock environment variables for testing
test_env_vars = {
    "DATABASE_URL": "postgresql+asyncpg://test:test@localhost:5432/test_db",
    "REDIS_URL": "redis://localhost:6379/0",
    "JWT_SECRET_KEY": "test-secret-key-for-testing-only"
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
    assert data["service"] == "auth-service"
    assert data["version"] == "1.0.0"


@patch.dict(os.environ, test_env_vars)
def test_root_endpoint():
    """Test root endpoint"""
    from app.main import app
    client = TestClient(app)
    
    response = client.get("/")
    assert response.status_code == 200
    
    data = response.json()
    assert data["message"] == "Auth Service API"
    assert data["version"] == "1.0.0"
    assert data["docs"] == "/docs"


@patch.dict(os.environ, test_env_vars)
def test_not_implemented_endpoints():
    """Test that not-yet-implemented endpoints return 501"""
    from app.main import app
    client = TestClient(app)
    
    # Test endpoints that should return 501 (Not Implemented)
    endpoints = [
        "/api/v1/auth/register",
        "/api/v1/auth/login", 
        "/api/v1/auth/refresh",
        "/api/v1/auth/me",
        "/api/v1/auth/logout"
    ]
    
    for endpoint in endpoints:
        if endpoint in ["/api/v1/auth/register", "/api/v1/auth/login", "/api/v1/auth/refresh", "/api/v1/auth/logout"]:
            response = client.post(endpoint)
        else:
            response = client.get(endpoint)
        
        assert response.status_code == 501
        assert "will be implemented" in response.json()["detail"].lower()


def test_missing_environment_variables():
    """Test that missing environment variables raise RuntimeError"""
    with patch.dict(os.environ, {}, clear=True):
        with pytest.raises(RuntimeError) as exc_info:
            from app.main import app
        
        assert "Missing required environment variables" in str(exc_info.value)