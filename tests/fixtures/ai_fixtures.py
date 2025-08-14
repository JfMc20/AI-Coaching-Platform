"""
AI Engine service specific fixtures.
Provides fixtures for Ollama and ChromaDB testing, mock AI responses.
"""

import pytest
import pytest_asyncio
from httpx import AsyncClient
from unittest.mock import AsyncMock, Mock

try:
    from services.ai_engine_service.app.main import app
except ImportError:
    # AI service might have missing dependencies in test environment
    app = None


@pytest_asyncio.fixture
async def ai_client():
    """Create test client for AI engine service."""
    if app is None:
        pytest.skip("services.ai_engine_service.app.main.app not available")
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def mock_ollama_manager():
    """Mock Ollama manager for testing."""
    mock = AsyncMock()
    
    # Mock embedding generation
    mock.generate_embedding.return_value = {
        "embedding": [0.1, 0.2, 0.3] * 128,  # Mock 384-dim embedding
        "model": "nomic-embed-text",
        "usage": {"prompt_tokens": 10, "total_tokens": 10}
    }
    
    # Mock chat completion
    mock.chat_completion.return_value = {
        "response": "This is a helpful AI response to your question.",
        "model": "llama2:7b-chat",
        "usage": {"prompt_tokens": 20, "completion_tokens": 15, "total_tokens": 35}
    }
    
    # Mock model availability
    mock.is_model_available.return_value = True
    mock.list_models.return_value = ["llama2:7b-chat", "nomic-embed-text"]
    
    return mock


@pytest.fixture
def mock_chromadb_manager():
    """Mock ChromaDB manager for testing."""
    mock = AsyncMock()
    
    # Mock collection operations
    mock.create_collection.return_value = {"name": "test-collection", "id": "test-id"}
    mock.add_documents.return_value = {"added": 1}
    mock.query_documents.return_value = {
        "documents": ["Test document content"],
        "metadatas": [{"source": "test.txt", "tenant_id": "test-tenant"}],
        "distances": [0.1],
        "ids": ["doc-1"]
    }
    
    # Mock collection management
    mock.list_collections.return_value = ["test-collection"]
    mock.delete_collection.return_value = {"deleted": True}
    
    return mock


@pytest.fixture
def test_embedding_request():
    """Provide test embedding request data."""
    return {
        "text": "This is a test document for embedding generation. It contains meaningful content that should be processed by the AI model.",
        "model": "nomic-embed-text"
    }


@pytest.fixture
def test_chat_request():
    """Provide test chat request data."""
    return {
        "message": "Hello, can you help me with goal setting strategies?",
        "context": "The user is interested in personal development and productivity.",
        "model": "llama2:7b-chat",
        "max_tokens": 150,
        "temperature": 0.7
    }


@pytest.fixture
def test_document_data():
    """Provide test document data for ChromaDB."""
    return {
        "documents": [
            "This is the first test document about productivity and time management.",
            "This is the second test document about goal setting and achievement.",
            "This is the third test document about mindfulness and stress reduction."
        ],
        "metadatas": [
            {"source": "productivity.txt", "tenant_id": "test-tenant", "type": "coaching"},
            {"source": "goals.txt", "tenant_id": "test-tenant", "type": "coaching"},
            {"source": "mindfulness.txt", "tenant_id": "test-tenant", "type": "coaching"}
        ],
        "ids": ["doc-1", "doc-2", "doc-3"]
    }


@pytest.fixture
def test_query_request():
    """Provide test query request for document search."""
    return {
        "query": "How can I improve my productivity?",
        "collection_name": "test-collection",
        "n_results": 3,
        "tenant_id": "test-tenant"
    }


@pytest.fixture
def mock_ai_responses():
    """Provide various mock AI responses for testing."""
    return {
        "greeting": "Hello! I'm here to help you with your coaching journey.",
        "goal_setting": "Setting SMART goals is crucial for success. Start by making your goals Specific, Measurable, Achievable, Relevant, and Time-bound.",
        "productivity": "To improve productivity, try the Pomodoro Technique: work for 25 minutes, then take a 5-minute break.",
        "error": "I apologize, but I couldn't process your request. Please try rephrasing your question."
    }


@pytest.fixture
def test_embeddings():
    """Provide test embedding vectors."""
    import random
    # Use seeded random for deterministic test data
    r = random.Random(42)
    return {
        "embedding_384": [r.random() for _ in range(384)],
        "embedding_768": [r.random() for _ in range(768)],
        "embedding_1536": [r.random() for _ in range(1536)]
    }


@pytest.fixture
def performance_test_data():
    """Provide data for performance testing."""
    return {
        "short_text": "Short test text.",
        "medium_text": "This is a medium length text for testing AI processing capabilities. " * 10,
        "long_text": "This is a very long text document that will be used to test the AI engine's ability to handle large inputs efficiently. " * 100,
        "concurrent_requests": [
            f"Test request number {i} for concurrent processing."
            for i in range(10)
        ]
    }


@pytest.fixture
def mock_model_config():
    """Mock model configuration for testing."""
    return {
        "embedding_model": {
            "name": "nomic-embed-text",
            "dimensions": 384,
            "max_tokens": 8192
        },
        "chat_model": {
            "name": "llama2:7b-chat",
            "max_tokens": 4096,
            "temperature": 0.7,
            "top_p": 0.9
        }
    }