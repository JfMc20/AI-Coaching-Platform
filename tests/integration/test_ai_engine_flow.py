"""
Integration tests for AI engine service workflow.
Tests document processing, embedding generation, chat responses, and ChromaDB operations.
"""

import pytest
from httpx import AsyncClient


class TestAIEngineFlow:
    """Test complete AI engine workflows."""

    async def test_ollama_embedding_endpoint(self, service_clients):
        """Test Ollama embedding generation endpoint."""
        ai_client = service_clients["ai_engine"]
        
        test_data = {
            "text": "This is a test document for embedding generation."
        }
        
        response = await ai_client.post("/api/v1/ai/ollama/test-embedding", json=test_data)
        assert response.status_code == 200
        
        result = response.json()
        assert "embedding" in result
        assert isinstance(result["embedding"], list)
        assert len(result["embedding"]) > 0
        assert "model" in result

    async def test_ollama_chat_endpoint(self, service_clients):
        """Test Ollama chat response endpoint."""
        ai_client = service_clients["ai_engine"]
        
        test_data = {
            "message": "Hello, how are you?",
            "context": "This is a test conversation."
        }
        
        response = await ai_client.post("/api/v1/ai/ollama/test-chat", json=test_data)
        assert response.status_code == 200
        
        result = response.json()
        assert "response" in result
        assert isinstance(result["response"], str)
        assert len(result["response"]) > 0
        assert "model" in result

    async def test_embedding_quality(self, service_clients):
        """Test embedding generation quality and consistency."""
        ai_client = service_clients["ai_engine"]
        
        # Test same text produces consistent embeddings
        test_text = "Machine learning is a subset of artificial intelligence."
        
        response1 = await ai_client.post("/api/v1/ai/ollama/test-embedding", json={"text": test_text})
        response2 = await ai_client.post("/api/v1/ai/ollama/test-embedding", json={"text": test_text})
        
        assert response1.status_code == 200
        assert response2.status_code == 200
        
        embedding1 = response1.json()["embedding"]
        embedding2 = response2.json()["embedding"]
        
        # Embeddings should be identical for same input
        assert embedding1 == embedding2
        assert len(embedding1) == len(embedding2)

    async def test_chat_response_quality(self, service_clients):
        """Test chat response quality and relevance."""
        ai_client = service_clients["ai_engine"]
        
        test_cases = [
            {
                "message": "What is machine learning?",
                "expected_keywords": ["machine", "learning", "algorithm", "data"]
            },
            {
                "message": "How do I improve my productivity?",
                "expected_keywords": ["productivity", "time", "focus", "goals"]
            }
        ]
        
        for test_case in test_cases:
            response = await ai_client.post("/api/v1/ai/ollama/test-chat", json={
                "message": test_case["message"]
            })
            
            assert response.status_code == 200
            result = response.json()
            response_text = result["response"].lower()
            
            # Check if response contains relevant keywords
            keyword_found = any(keyword in response_text for keyword in test_case["expected_keywords"])
            assert keyword_found, f"Response doesn't contain relevant keywords for: {test_case['message']}"

    async def test_ai_service_health(self, service_clients):
        """Test AI service health and availability."""
        ai_client = service_clients["ai_engine"]
        
        response = await ai_client.get("/api/v1/health")
        assert response.status_code == 200
        
        health_data = response.json()
        assert health_data["status"] == "healthy"
        assert "ollama" in health_data["dependencies"]
        assert "chromadb" in health_data["dependencies"]

    async def test_error_handling(self, service_clients):
        """Test AI service error handling for invalid inputs."""
        ai_client = service_clients["ai_engine"]
        
        # Test empty text for embedding
        response = await ai_client.post("/api/v1/ai/ollama/test-embedding", json={"text": ""})
        assert response.status_code == 422  # Validation error
        
        # Test empty message for chat
        response = await ai_client.post("/api/v1/ai/ollama/test-chat", json={"message": ""})
        assert response.status_code == 422  # Validation error
        
        # Test invalid JSON
        response = await ai_client.post("/api/v1/ai/ollama/test-embedding", json={})
        assert response.status_code == 422  # Missing required field

    async def test_concurrent_requests(self, service_clients):
        """Test AI service handling of concurrent requests."""
        ai_client = service_clients["ai_engine"]
        
        import asyncio
        
        # Create multiple concurrent requests
        tasks = []
        for i in range(5):
            task = ai_client.post("/api/v1/ai/ollama/test-chat", json={
                "message": f"Test message {i}"
            })
            tasks.append(task)
        
        responses = await asyncio.gather(*tasks)
        
        # All requests should succeed
        for response in responses:
            assert response.status_code == 200
            result = response.json()
            assert "response" in result
            assert len(result["response"]) > 0

    async def test_large_text_handling(self, service_clients):
        """Test AI service handling of large text inputs."""
        ai_client = service_clients["ai_engine"]
        
        # Test with large text (but within reasonable limits)
        large_text = "This is a test sentence. " * 100  # ~2500 characters
        
        response = await ai_client.post("/api/v1/ai/ollama/test-embedding", json={
            "text": large_text
        })
        
        assert response.status_code == 200
        result = response.json()
        assert "embedding" in result
        assert len(result["embedding"]) > 0

    async def test_special_characters_handling(self, service_clients):
        """Test AI service handling of special characters and unicode."""
        ai_client = service_clients["ai_engine"]
        
        special_text = "Hello! 🌟 This contains émojis and spëcial characters: @#$%^&*()"
        
        response = await ai_client.post("/api/v1/ai/ollama/test-embedding", json={
            "text": special_text
        })
        
        assert response.status_code == 200
        result = response.json()
        assert "embedding" in result
        
        # Test chat with special characters
        response = await ai_client.post("/api/v1/ai/ollama/test-chat", json={
            "message": special_text
        })
        
        assert response.status_code == 200
        result = response.json()
        assert "response" in result