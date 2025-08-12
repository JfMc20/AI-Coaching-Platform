"""
Integration tests for Ollama LLM and embedding functionality
Tests model loading, embedding generation, and chat completion
"""

import pytest
import asyncio
import uuid
from typing import List, Dict, Any

from shared.ai.ollama_manager import OllamaManager, OllamaError, OllamaConnectionError, OllamaModelError


class TestOllamaIntegration:
    """Test Ollama LLM integration"""
    
    @pytest.fixture
    async def ollama_manager(self):
        """Create Ollama manager for testing"""
        manager = OllamaManager(
            ollama_url="http://localhost:11434",
            embedding_model="nomic-embed-text",
            chat_model="gpt-oss-20b",
            timeout=30,
            max_retries=2
        )
        yield manager
        await manager.close()
    
    @pytest.fixture
    def sample_texts(self) -> List[str]:
        """Generate sample texts for embedding"""
        return [
            "This is a test document about artificial intelligence and machine learning.",
            "Natural language processing is a subfield of AI that focuses on text analysis.",
            "Computer vision enables machines to interpret and understand visual information.",
            "Deep learning uses neural networks with multiple layers to learn complex patterns."
        ]
    
    @pytest.fixture
    def sample_prompts(self) -> List[str]:
        """Generate sample prompts for chat testing"""
        return [
            "What is artificial intelligence?",
            "Explain machine learning in simple terms.",
            "How does natural language processing work?",
            "What are the applications of computer vision?"
        ]
    
    @pytest.mark.asyncio
    async def test_health_check(self, ollama_manager):
        """Test Ollama health check"""
        health = await ollama_manager.health_check()
        
        assert health["status"] == "healthy"
        assert "url" in health
        assert "models_count" in health
        assert "embedding_model" in health
        assert "chat_model" in health
        assert "timestamp" in health
        
        # Check model availability
        assert health["embedding_model"]["name"] == "nomic-embed-text"
        assert health["chat_model"]["name"] == "gpt-oss-20b"
    
    @pytest.mark.asyncio
    async def test_list_models(self, ollama_manager):
        """Test listing available models"""
        models = await ollama_manager.list_models()
        
        assert isinstance(models, list)
        assert len(models) >= 0  # May be empty if no models are pulled
        
        # Test caching
        models_cached = await ollama_manager.list_models()
        assert len(models_cached) == len(models)
        
        # Test force refresh
        models_refreshed = await ollama_manager.list_models(force_refresh=True)
        assert len(models_refreshed) == len(models)
    
    @pytest.mark.asyncio
    async def test_ensure_models_available(self, ollama_manager):
        """Test ensuring required models are available"""
        # This test may take a while if models need to be downloaded
        model_status = await ollama_manager.ensure_models_available()
        
        assert "embedding_model" in model_status
        assert "chat_model" in model_status
        assert model_status["embedding_model"] is True
        assert model_status["chat_model"] is True
    
    @pytest.mark.asyncio
    async def test_generate_embeddings_single_text(self, ollama_manager):
        """Test embedding generation for single text"""
        test_text = "This is a test document for embedding generation."
        
        response = await ollama_manager.generate_embeddings([test_text])
        
        assert response.model == "nomic-embed-text"
        assert len(response.embeddings) == 1
        assert len(response.embeddings[0]) > 0  # Should have embedding dimensions
        assert response.processing_time_ms > 0
        assert response.token_count > 0
        
        # Verify embedding is numeric
        embedding = response.embeddings[0]
        assert all(isinstance(val, (int, float)) for val in embedding)
    
    @pytest.mark.asyncio
    async def test_generate_embeddings_multiple_texts(self, ollama_manager, sample_texts):
        """Test embedding generation for multiple texts"""
        response = await ollama_manager.generate_embeddings(sample_texts)
        
        assert response.model == "nomic-embed-text"
        assert len(response.embeddings) == len(sample_texts)
        assert response.processing_time_ms > 0
        assert response.token_count > 0
        
        # Verify all embeddings have same dimensions
        embedding_dims = [len(emb) for emb in response.embeddings]
        assert all(dim == embedding_dims[0] for dim in embedding_dims)
        
        # Verify embeddings are different for different texts
        assert response.embeddings[0] != response.embeddings[1]
    
    @pytest.mark.asyncio
    async def test_embedding_consistency(self, ollama_manager):
        """Test that same text produces consistent embeddings"""
        test_text = "Consistent embedding test text."
        
        # Generate embeddings twice
        response1 = await ollama_manager.generate_embeddings([test_text])
        response2 = await ollama_manager.generate_embeddings([test_text])
        
        # Should be identical (deterministic)
        assert response1.embeddings[0] == response2.embeddings[0]
    
    @pytest.mark.asyncio
    async def test_generate_chat_response_basic(self, ollama_manager):
        """Test basic chat response generation"""
        prompt = "Hello! Please respond with a simple greeting."
        
        response = await ollama_manager.generate_chat_response(prompt)
        
        assert response.model == "gpt-oss-20b"
        assert len(response.response) > 0
        assert response.processing_time_ms > 0
        assert response.done is True
        
        # Response should be relevant to greeting
        assert any(word in response.response.lower() for word in ["hello", "hi", "greetings"])
    
    @pytest.mark.asyncio
    async def test_generate_chat_response_with_parameters(self, ollama_manager):
        """Test chat response with custom parameters"""
        prompt = "Explain AI in exactly one sentence."
        system_prompt = "You are a helpful AI assistant that provides concise answers."
        
        response = await ollama_manager.generate_chat_response(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=0.3,  # Lower temperature for more focused response
            max_tokens=50
        )
        
        assert response.model == "gpt-oss-20b"
        assert len(response.response) > 0
        assert response.processing_time_ms > 0
        
        # Should mention AI
        assert "ai" in response.response.lower() or "artificial intelligence" in response.response.lower()
    
    @pytest.mark.asyncio
    async def test_chat_with_context(self, ollama_manager):
        """Test chat response with conversation context"""
        # First message
        response1 = await ollama_manager.generate_chat_response(
            "My name is Alice. What's your name?"
        )
        
        assert len(response1.response) > 0
        context = response1.context
        
        # Second message with context
        if context:
            response2 = await ollama_manager.generate_chat_response(
                "What did I tell you my name was?",
                context=context
            )
            
            assert len(response2.response) > 0
            # Should remember the name Alice
            assert "alice" in response2.response.lower()
    
    @pytest.mark.asyncio
    async def test_concurrent_embedding_generation(self, ollama_manager, sample_texts):
        """Test concurrent embedding generation"""
        # Create multiple concurrent embedding tasks
        tasks = [
            ollama_manager.generate_embeddings([text])
            for text in sample_texts[:3]  # Limit to avoid overwhelming
        ]
        
        responses = await asyncio.gather(*tasks)
        
        assert len(responses) == 3
        for response in responses:
            assert len(response.embeddings) == 1
            assert len(response.embeddings[0]) > 0
    
    @pytest.mark.asyncio
    async def test_concurrent_chat_generation(self, ollama_manager, sample_prompts):
        """Test concurrent chat generation"""
        # Create multiple concurrent chat tasks
        tasks = [
            ollama_manager.generate_chat_response(prompt)
            for prompt in sample_prompts[:2]  # Limit to avoid overwhelming
        ]
        
        responses = await asyncio.gather(*tasks)
        
        assert len(responses) == 2
        for response in responses:
            assert len(response.response) > 0
            assert response.processing_time_ms > 0
    
    @pytest.mark.asyncio
    async def test_error_handling_empty_text(self, ollama_manager):
        """Test error handling for empty text"""
        with pytest.raises(ValueError, match="texts cannot be empty"):
            await ollama_manager.generate_embeddings([])
        
        with pytest.raises(ValueError, match="prompt cannot be empty"):
            await ollama_manager.generate_chat_response("")
        
        with pytest.raises(ValueError, match="prompt cannot be empty"):
            await ollama_manager.generate_chat_response("   ")  # Whitespace only
    
    @pytest.mark.asyncio
    async def test_error_handling_invalid_model(self, ollama_manager):
        """Test error handling for invalid model names"""
        with pytest.raises(OllamaModelError):
            await ollama_manager.generate_embeddings(
                ["test text"],
                model="non-existent-model"
            )
        
        with pytest.raises(OllamaModelError):
            await ollama_manager.generate_chat_response(
                "test prompt",
                model="non-existent-chat-model"
            )
    
    @pytest.mark.asyncio
    async def test_retry_mechanism(self, ollama_manager):
        """Test retry mechanism for failed requests"""
        # Create manager with invalid URL to test retry
        invalid_manager = OllamaManager(
            ollama_url="http://invalid-host:11434",
            timeout=1,
            max_retries=2
        )
        
        try:
            with pytest.raises(OllamaConnectionError):
                await invalid_manager.health_check()
        finally:
            await invalid_manager.close()
    
    @pytest.mark.asyncio
    async def test_timeout_handling(self, ollama_manager):
        """Test timeout handling for long requests"""
        # Create manager with very short timeout
        timeout_manager = OllamaManager(
            ollama_url="http://localhost:11434",
            timeout=0.001,  # Very short timeout
            max_retries=1
        )
        
        try:
            with pytest.raises((OllamaConnectionError, OllamaError)):
                await timeout_manager.generate_embeddings(["test text"])
        finally:
            await timeout_manager.close()
    
    @pytest.mark.asyncio
    async def test_large_text_embedding(self, ollama_manager):
        """Test embedding generation for large text"""
        # Create a large text (but not too large to avoid timeout)
        large_text = "This is a test sentence. " * 100  # ~500 words
        
        response = await ollama_manager.generate_embeddings([large_text])
        
        assert len(response.embeddings) == 1
        assert len(response.embeddings[0]) > 0
        assert response.token_count > 100  # Should have many tokens
    
    @pytest.mark.asyncio
    async def test_session_management(self, ollama_manager):
        """Test HTTP session management"""
        # Make multiple requests to test session reuse
        tasks = [
            ollama_manager.generate_embeddings(["test text 1"]),
            ollama_manager.generate_embeddings(["test text 2"]),
            ollama_manager.generate_embeddings(["test text 3"])
        ]
        
        responses = await asyncio.gather(*tasks)
        
        assert len(responses) == 3
        for response in responses:
            assert len(response.embeddings) == 1
        
        # Session should be reused (same instance)
        assert ollama_manager._session is not None
        assert not ollama_manager._session.closed
    
    @pytest.mark.asyncio
    async def test_model_caching(self, ollama_manager):
        """Test model information caching"""
        # First call should populate cache
        models1 = await ollama_manager.list_models()
        cache_time1 = ollama_manager._last_cache_update
        
        # Second call should use cache
        models2 = await ollama_manager.list_models()
        cache_time2 = ollama_manager._last_cache_update
        
        assert cache_time1 == cache_time2  # Cache should be used
        assert len(models1) == len(models2)
        
        # Force refresh should update cache
        models3 = await ollama_manager.list_models(force_refresh=True)
        cache_time3 = ollama_manager._last_cache_update
        
        assert cache_time3 > cache_time2  # Cache should be updated


@pytest.mark.asyncio
async def test_ollama_manager_singleton():
    """Test Ollama manager singleton pattern"""
    from shared.ai.ollama_manager import get_ollama_manager, close_ollama_manager
    
    # Get manager instances
    manager1 = get_ollama_manager()
    manager2 = get_ollama_manager()
    
    # Should be same instance
    assert manager1 is manager2
    
    # Cleanup
    await close_ollama_manager()
    
    # After cleanup, should create new instance
    manager3 = get_ollama_manager()
    assert manager3 is not manager1
    
    await close_ollama_manager()


@pytest.mark.asyncio
async def test_integration_embedding_to_chromadb():
    """Test integration between Ollama embeddings and ChromaDB storage"""
    from shared.ai.ollama_manager import get_ollama_manager
    from shared.ai.chromadb_manager import get_chromadb_manager
    
    ollama_manager = get_ollama_manager()
    chromadb_manager = get_chromadb_manager()
    
    try:
        # Generate embeddings with Ollama
        test_texts = [
            "Integration test document 1",
            "Integration test document 2"
        ]
        
        embedding_response = await ollama_manager.generate_embeddings(test_texts)
        
        # Store embeddings in ChromaDB
        creator_id = f"integration-test-{uuid.uuid4()}"
        document_id = f"integration-doc-{uuid.uuid4()}"
        
        metadatas = [
            {"source": "integration_test", "index": i}
            for i in range(len(test_texts))
        ]
        
        ids = await chromadb_manager.add_embeddings(
            creator_id=creator_id,
            document_id=document_id,
            embeddings=embedding_response.embeddings,
            documents=test_texts,
            metadatas=metadatas
        )
        
        assert len(ids) == 2
        
        # Query embeddings from ChromaDB
        query_results = await chromadb_manager.query_embeddings(
            creator_id=creator_id,
            query_embeddings=[embedding_response.embeddings[0]],
            n_results=5
        )
        
        assert len(query_results["ids"][0]) == 2
        assert query_results["documents"][0][0] in test_texts
        
    finally:
        # Cleanup
        from shared.ai.ollama_manager import close_ollama_manager
        from shared.ai.chromadb_manager import close_chromadb_manager
        
        await close_ollama_manager()
        await close_chromadb_manager()


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "--asyncio-mode=auto"])