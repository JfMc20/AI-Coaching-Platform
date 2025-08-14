"""
Creator Hub service specific fixtures.
Provides fixtures for creator profiles, documents, and widget configurations.
"""

import pytest
import pytest_asyncio
from httpx import AsyncClient
from unittest.mock import AsyncMock, Mock

try:
    from services.creator_hub_service.app.main import app
except ImportError:
    # Creator hub service might have missing dependencies in test environment
    app = None


@pytest_asyncio.fixture
async def creator_hub_client():
    """Create test client for creator hub service."""
    if app is None:
        pytest.skip("services.creator_hub_service.app.main.app not available")
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def mock_auth_service():
    """Mock auth service responses."""
    mock = AsyncMock()
    mock.validate_token.return_value = {
        "user_id": "test-user-123",
        "email": "creator@example.com",
        "tenant_id": "test-tenant"
    }
    return mock


@pytest.fixture
def mock_ai_engine_service():
    """Mock AI engine service responses."""
    mock = AsyncMock()
    mock.generate_embedding.return_value = {
        "embedding": [0.1, 0.2, 0.3] * 100,  # Mock 300-dim embedding
        "model": "nomic-embed-text"
    }
    mock.chat_completion.return_value = {
        "response": "This is a mock AI response",
        "model": "llama2:7b-chat"
    }
    return mock


@pytest.fixture
def test_creator_profile():
    """Provide test creator profile data."""
    return {
        "user_id": "creator-123",
        "display_name": "Test Creator",
        "bio": "I'm a test creator for coaching programs",
        "expertise_areas": ["productivity", "mindfulness", "goal-setting"],
        "tenant_id": "test-tenant"
    }


@pytest.fixture
def creator_test_document_data():
    """Provide test document data for creator hub."""
    return {
        "title": "Test Coaching Document",
        "content": "This is test content for a coaching document. It contains valuable information about personal development and goal achievement.",
        "document_type": "coaching_material",
        "tags": ["coaching", "development", "goals"]
    }


@pytest.fixture
def test_widget_config():
    """Provide test widget configuration."""
    return {
        "name": "Test Coaching Widget",
        "description": "A test widget for coaching interactions",
        "settings": {
            "theme": "light",
            "position": "bottom-right",
            "greeting_message": "Hello! How can I help you today?",
            "enabled": True
        },
        "channels": ["web", "mobile"]
    }


@pytest.fixture
def test_coaching_program():
    """Provide test coaching program data."""
    return {
        "title": "Test Coaching Program",
        "description": "A comprehensive test coaching program",
        "duration_weeks": 12,
        "modules": [
            {
                "title": "Module 1: Goal Setting",
                "description": "Learn to set effective goals",
                "order": 1
            },
            {
                "title": "Module 2: Time Management",
                "description": "Master your time",
                "order": 2
            }
        ],
        "target_audience": "professionals",
        "difficulty_level": "beginner"
    }


@pytest.fixture
def authenticated_headers():
    """Provide authentication headers for API tests."""
    return {
        "Authorization": "Bearer test-jwt-token",
        "Content-Type": "application/json"
    }


@pytest.fixture
def mock_database():
    """Mock database operations."""
    mock_db = Mock()
    mock_db.add = Mock()
    mock_db.commit = AsyncMock()
    mock_db.refresh = AsyncMock()
    mock_db.execute = AsyncMock()
    return mock_db