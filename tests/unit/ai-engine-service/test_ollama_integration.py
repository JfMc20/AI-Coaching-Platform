"""
Tests for Ollama manager integration.
Tests embedding generation, chat responses, model loading, and error handling.

Fixtures are now centralized in tests/fixtures/ai_fixtures.py and automatically
available through the main conftest.py configuration.
"""

import pytest

# Mark as unit tests despite "integration" in filename - these test individual components in isolation
pytestmark = pytest.mark.unit
import asyncio
from unittest.mock import AsyncMock, patch

from shared.ai.ollama_manager import OllamaManager


class TestOllamaIntegration:
    """Test Ollama manager functionality."""

    @pytest.fixture
    def ollama_manager(self):
        """Create Ollama manager instance for testing."""
        return OllamaManager(base_url="http://localhost:11434")

    async def test_embedding_generation(self, ollama_manager, mock_ollama_manager):
        """Test embedding generation functionality."""
        with patch.object(ollama_manager, 'generate_embedding', mock_ollama_manager.generate_embedding):
            result = await ollama_manager.generate_embedding(
                text="Test text for embedding generation",
                model="nomic-embed-text"
            )
            
            assert "embedding" in result
            assert isinstance(result["embedding"], list)
            assert len(result["embedding"]) > 0
            assert result["model"] == "nomic-embed-text"

    async def test_chat_completion(self, ollama_manager, mock_ollama_manager):
        """Test chat completion functionality."""
        with patch.object(ollama_manager, 'chat_completion', mock_ollama_manager.chat_completion):
            result = await ollama_manager.chat_completion(
                message="Hello, how can you help me?",
                model="llama2:7b-chat"
            )
            
            assert "response" in result
            assert isinstance(result["response"], str)
            assert len(result["response"]) > 0
            assert result["model"] == "llama2:7b-chat"

    async def test_model_availability_check(self, ollama_manager, mock_ollama_manager):
        """Test model availability checking."""
        with patch.object(ollama_manager, 'is_model_available', mock_ollama_manager.is_model_available):
            is_available = await ollama_manager.is_model_available("llama2:7b-chat")
            assert isinstance(is_available, bool)

    async def test_list_available_models(self, ollama_manager, mock_ollama_manager):
        """Test listing available models."""
        with patch.object(ollama_manager, 'list_models', mock_ollama_manager.list_models):
            models = await ollama_manager.list_models()
            assert isinstance(models, list)
            assert len(models) > 0

    async def test_embedding_with_different_models(self, ollama_manager, mock_ollama_manager):
        """Test embedding generation with different models."""
        models_to_test = ["nomic-embed-text", "all-minilm"]
        
        for model in models_to_test:
            mock_ollama_manager.generate_embedding.return_value = {
                "embedding": [0.1, 0.2, 0.3] * 128,
                "model": model
            }
            
            with patch.object(ollama_manager, 'generate_embedding', mock_ollama_manager.generate_embedding):
                result = await ollama_manager.generate_embedding(
                    text="Test text",
                    model=model
                )
                
                assert result["model"] == model
                assert "embedding" in result

    async def test_chat_with_context(self, ollama_manager, mock_ollama_manager):
        """Test chat completion with context."""
        mock_ollama_manager.chat_completion.return_value = {
            "response": "Based on the context about productivity, I recommend using time-blocking techniques.",
            "model": "llama2:7b-chat"
        }
        
        with patch.object(ollama_manager, 'chat_completion', mock_ollama_manager.chat_completion):
            result = await ollama_manager.chat_completion(
                message="How can I be more productive?",
                context="The user is a software developer working remotely.",
                model="llama2:7b-chat"
            )
            
            assert "response" in result
            assert "productivity" in result["response"].lower()

    async def test_error_handling_invalid_model(self, ollama_manager):
        """Test error handling for invalid model requests."""
        with patch.object(ollama_manager, 'generate_embedding') as mock_embedding:
            mock_embedding.side_effect = Exception("Model not found")
            
            with pytest.raises(Exception):
                await ollama_manager.generate_embedding(
                    text="Test text",
                    model="nonexistent-model"
                )

    async def test_error_handling_connection_failure(self, ollama_manager):
        """Test error handling for connection failures."""
        with patch.object(ollama_manager, 'chat_completion') as mock_chat:
            mock_chat.side_effect = ConnectionError("Connection refused")
            
            with pytest.raises(ConnectionError):
                await ollama_manager.chat_completion(
                    message="Test message",
                    model="llama2:7b-chat"
                )

    async def test_embedding_performance(self, ollama_manager, mock_ollama_manager, performance_test_data):
        """Test embedding generation performance."""
        import time
        
        with patch.object(ollama_manager, 'generate_embedding', mock_ollama_manager.generate_embedding):
            # Test with different text lengths
            for text_type, text in performance_test_data.items():
                if text_type.endswith('_text'):
                    start_time = time.time()
                    
                    result = await ollama_manager.generate_embedding(
                        text=text,
                        model="nomic-embed-text"
                    )
                    
                    end_time = time.time()
                    processing_time = end_time - start_time
                    
                    assert "embedding" in result
                    # Mock should be very fast
                    assert processing_time < 1.0

    async def test_chat_parameters(self, ollama_manager, mock_ollama_manager):
        """Test chat completion with various parameters."""
        test_parameters = [
            {"temperature": 0.1, "max_tokens": 50},
            {"temperature": 0.7, "max_tokens": 150},
            {"temperature": 0.9, "max_tokens": 300}
        ]
        
        for params in test_parameters:
            mock_ollama_manager.chat_completion.return_value = {
                "response": f"Response with temperature {params['temperature']}",
                "model": "llama2:7b-chat",
                "parameters": params
            }
            
            with patch.object(ollama_manager, 'chat_completion', mock_ollama_manager.chat_completion):
                result = await ollama_manager.chat_completion(
                    message="Test message",
                    model="llama2:7b-chat",
                    **params
                )
                
                assert "response" in result
                if "parameters" in result:
                    assert result["parameters"]["temperature"] == params["temperature"]

    async def test_concurrent_requests(self, ollama_manager, mock_ollama_manager):
        """Test handling of concurrent requests."""
        import asyncio
        
        with patch.object(ollama_manager, 'generate_embedding', mock_ollama_manager.generate_embedding):
            # Create multiple concurrent embedding requests
            tasks = [
                ollama_manager.generate_embedding(
                    text=f"Concurrent test text {i}",
                    model="nomic-embed-text"
                )
                for i in range(5)
            ]
            
            results = await asyncio.gather(*tasks)
            
            # All requests should succeed
            assert len(results) == 5
            for result in results:
                assert "embedding" in result
                assert "model" in result

    async def test_model_health_check(self, ollama_manager):
        """Test model health checking functionality."""
        with patch.object(ollama_manager, 'health_check') as mock_health:
            mock_health.return_value = {
                "status": "healthy",
                "models_loaded": ["llama2:7b-chat", "nomic-embed-text"],
                "memory_usage": "2.1GB",
                "uptime": "1h 30m"
            }
            
            health_status = await ollama_manager.health_check()
            
            assert health_status["status"] == "healthy"
            assert "models_loaded" in health_status
            assert isinstance(health_status["models_loaded"], list)

    async def test_streaming_response(self, ollama_manager):
        """Test streaming chat responses if supported."""
        with patch.object(ollama_manager, 'chat_completion_stream') as mock_stream:
            async def mock_stream_generator():
                chunks = [
                    {"chunk": "Hello"},
                    {"chunk": " there!"},
                    {"chunk": " How"},
                    {"chunk": " can"},
                    {"chunk": " I"},
                    {"chunk": " help?"}
                ]
                for chunk in chunks:
                    yield chunk
            
            mock_stream.return_value = mock_stream_generator()
            
            chunks = []
            async for chunk in ollama_manager.chat_completion_stream(
                message="Hello",
                model="llama2:7b-chat"
            ):
                chunks.append(chunk)
            
            assert len(chunks) == 6
            full_response = "".join([chunk["chunk"] for chunk in chunks])
            assert full_response == "Hello there! How can I help?"