"""
AI Engine service fixtures.
"""

import pytest
from unittest.mock import AsyncMock, Mock


@pytest.fixture
def mock_ollama_manager():
    """Mock Ollama manager for testing."""
    mock = AsyncMock()
    mock.generate_embedding.return_value = [0.1, 0.2, 0.3] * 128  # 384-dim embedding
    mock.generate_chat_completion.return_value = "This is a test response from the AI."
    mock.check_model_availability.return_value = True
    mock.health_check.return_value = {"status": "healthy", "models": ["llama3.2", "nomic-embed-text"]}
    return mock


@pytest.fixture
def mock_chromadb_manager():
    """Mock ChromaDB manager for testing."""
    mock = AsyncMock()
    mock.get_or_create_collection.return_value = Mock()
    mock.add_documents.return_value = True
    mock.search_documents.return_value = [
        {
            "content": "Sample document content",
            "metadata": {"source": "test.pdf", "chunk_index": 0},
            "similarity_score": 0.85
        }
    ]
    mock.delete_document.return_value = True
    mock.get_collection_stats.return_value = {
        "total_chunks": 10,
        "collection_name": "test_collection",
        "sources": {"test.pdf": 5, "test2.pdf": 5}
    }
    mock.health_check.return_value = {"status": "healthy", "total_collections": 1}
    return mock


@pytest.fixture
def test_embedding_request():
    """Sample embedding request data."""
    return {
        "text": "This is a test text for embedding generation.",
        "model": "nomic-embed-text"
    }


@pytest.fixture
def test_chat_request():
    """Sample chat request data."""
    return {
        "message": "Hello, how can you help me?",
        "conversation_id": "test_conversation_123",
        "context": []
    }


@pytest.fixture
def mock_rag_pipeline():
    """Mock RAG pipeline for testing."""
    mock = AsyncMock()
    mock.process_query.return_value = {
        "response": "This is a test response from the RAG pipeline.",
        "confidence": 0.95,
        "sources": [
            {"content": "Relevant context 1", "source": "doc1.pdf"},
            {"content": "Relevant context 2", "source": "doc2.pdf"}
        ],
        "processing_time_ms": 150
    }
    mock.get_conversation_context.return_value = []
    mock.health_check.return_value = {"status": "healthy", "components": ["ollama", "chromadb"]}
    return mock


@pytest.fixture
def ai_client():
    """Mock AI engine client for testing."""
    def mock_post(url, json=None, **kwargs):
        """Dynamic mock post that validates input."""
        mock_response = Mock()
        
        # Validate conversation endpoint
        if "/conversations" in url and json:
            if not json.get("query") or not json.get("creator_id"):
                mock_response.status_code = 422
                mock_response.json.return_value = {"detail": "Validation error"}
            else:
                mock_response.status_code = 200
                mock_response.json.return_value = {
                    "response": "Test AI response", 
                    "confidence": 0.9,
                    "conversation_id": json.get("conversation_id", "test_conv"),
                    "processing_time_ms": 100,
                    "sources_count": 2
                }
        # Validate document processing endpoint  
        elif "/documents" in url and json:
            if not json.get("document_content") or not json.get("creator_id"):
                mock_response.status_code = 422
                mock_response.json.return_value = {"detail": "Validation error"}
            else:
                mock_response.status_code = 200
                mock_response.json.return_value = {"status": "processed", "chunks": 5}
        else:
            mock_response.status_code = 200
            mock_response.json.return_value = {"response": "Test response"}
            
        return mock_response
    
    client = AsyncMock()
    client.post.side_effect = mock_post
    client.get.return_value = Mock(
        status_code=200,
        json=lambda: {"status": "healthy", "timestamp": "2023-01-01T00:00:00Z"}
    )
    return client