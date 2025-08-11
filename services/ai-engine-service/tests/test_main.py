"""
Basic tests for AI Engine Service
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch
import os

# Mock environment variables for testing
test_env_vars = {
    "DATABASE_URL": "postgresql+asyncpg://test:test@localhost:5432/test_db",
    "REDIS_URL": "redis://localhost:6379/2",
    "OLLAMA_URL": "http://localhost:11434",
    "CHROMADB_URL": "http://localhost:8000",
    "EMBEDDING_MODEL": "nomic-embed-text",
    "CHAT_MODEL": "llama2:7b-chat"
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
    assert data["service"] == "ai-engine-service"
    assert data["version"] == "1.0.0"


@patch.dict(os.environ, test_env_vars)
def test_root_endpoint():
    """Test root endpoint"""
    from app.main import app
    client = TestClient(app)
    
    response = client.get("/")
    assert response.status_code == 200
    
    data = response.json()
    assert data["message"] == "AI Engine Service API"
    assert data["version"] == "1.0.0"
    assert data["docs"] == "/docs"


@patch.dict(os.environ, test_env_vars)
def test_models_status_endpoint():
    """Test models status endpoint (partially implemented)"""
    from app.main import app
    client = TestClient(app)
    
    response = client.get("/api/v1/ai/models/status")
    assert response.status_code == 200
    
    data = response.json()
    assert "embedding_model" in data
    assert "chat_model" in data
    assert data["embedding_model"]["name"] == "nomic-embed-text"
    assert data["chat_model"]["name"] == "llama2:7b-chat"
    assert data["embedding_model"]["status"] == "not_implemented"
    assert data["chat_model"]["status"] == "not_implemented"


@patch.dict(os.environ, test_env_vars)
def test_not_implemented_endpoints():
    """Test that not-yet-implemented endpoints return 501"""
    from app.main import app
    client = TestClient(app)
    
    # Test POST endpoints
    post_endpoints = [
        "/api/v1/ai/conversations",
        "/api/v1/ai/documents/process",
        "/api/v1/ai/documents/search",
        "/api/v1/ai/models/reload"
    ]
    
    for endpoint in post_endpoints:
        response = client.post(endpoint)
        assert response.status_code == 501
        assert "will be implemented" in response.json()["detail"].lower()
    
    # Test GET endpoints
    response = client.get("/api/v1/ai/conversations/test-id/context")
    assert response.status_code == 501
    assert "will be implemented" in response.json()["detail"].lower()


def test_missing_environment_variables():
    """Test that missing environment variables raise RuntimeError"""
    with patch.dict(os.environ, {}, clear=True):
        with pytest.raises(RuntimeError) as exc_info:
            from app.main import app
        
        assert "Missing required environment variables" in str(exc_info.value)