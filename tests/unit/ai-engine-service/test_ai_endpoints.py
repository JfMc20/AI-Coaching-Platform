"""
Tests for AI engine service endpoints.
Tests Ollama integration, embedding generation, chat responses, and error handling.

Fixtures are now centralized in tests/fixtures/ai_fixtures.py and automatically
available through the main conftest.py configuration.
"""

import pytest
import asyncio
import time
from httpx import AsyncClient


class TestAIEndpoints:
    """Test AI engine API endpoints."""

    async def test_conversation_endpoint_success(self, ai_client: AsyncClient, mock_rag_pipeline):
        """Test successful conversation processing."""
        with patch('services.ai_engine_service.app.main.get_rag_pipeline', return_value=mock_rag_pipeline):
            request_data = {
                "query": "How can I improve my productivity?",
                "creator_id": "test_creator",
                "conversation_id": "test_conv_1"
            }
            
            response = await ai_client.post("/api/v1/ai/conversations", json=request_data)
            
            assert response.status_code == 200
            result = response.json()
            
            assert "response" in result
            assert "confidence" in result
            assert "processing_time_ms" in result
            assert "sources_count" in result
            assert result["conversation_id"] == "test_conv_1"

    async def test_conversation_endpoint_validation(self, ai_client: AsyncClient):
        """Test conversation endpoint input validation."""
        # Test empty query
        response = await ai_client.post("/api/v1/ai/conversations", json={
            "query": "",
            "creator_id": "test_creator",
            "conversation_id": "test_conv"
        })
        assert response.status_code == 422
        
        # Test missing creator_id
        response = await ai_client.post("/api/v1/ai/conversations", json={
            "query": "Test query",
            "conversation_id": "test_conv"
        })
        assert response.status_code == 422

    async def test_conversation_context_endpoint(self, ai_client: AsyncClient, mock_rag_pipeline, test_conversation_data):
        """Test getting conversation context."""
        mock_conversation_manager = AsyncMock()
        mock_conversation_manager.get_context.return_value = []
        mock_conversation_manager.get_conversation_summary.return_value = {
            "total_messages": 2,
            "user_messages": 1,
            "ai_messages": 1
        }
        
        mock_rag_pipeline.conversation_manager = mock_conversation_manager
        
        with patch('services.ai_engine_service.app.main.get_rag_pipeline', return_value=mock_rag_pipeline):
            response = await ai_client.get("/api/v1/ai/conversations/test_conv_1/context")
            
            assert response.status_code == 200
            result = response.json()
            
            assert "conversation_id" in result
            assert "messages" in result
            assert "total_messages" in result

    async def test_document_processing_endpoint_success(self, ai_client: AsyncClient, mock_document_processor, test_file_content):
        """Test successful document processing."""
        with patch('services.ai_engine_service.app.main.get_document_processor', return_value=mock_document_processor):
            # Create test file
            files = {"file": ("test.txt", test_file_content["txt_content"], "text/plain")}
            data = {"creator_id": "test_creator"}
            
            response = await ai_client.post("/api/v1/ai/documents/process", files=files, data=data)
            
            assert response.status_code == 200
            result = response.json()
            
            assert "document_id" in result
            assert "status" in result
            assert "total_chunks" in result
            assert "processing_time_seconds" in result

    async def test_document_processing_endpoint_validation(self, ai_client: AsyncClient):
        """Test document processing endpoint validation."""
        # Test missing file
        response = await ai_client.post("/api/v1/ai/documents/process", data={"creator_id": "test_creator"})
        assert response.status_code == 422
        
        # Test missing creator_id
        files = {"file": ("test.txt", b"content", "text/plain")}
        response = await ai_client.post("/api/v1/ai/documents/process", files=files)
        assert response.status_code == 422

    async def test_document_search_endpoint_success(self, ai_client: AsyncClient, mock_rag_pipeline):
        """Test successful document search."""
        with patch('services.ai_engine_service.app.main.get_rag_pipeline', return_value=mock_rag_pipeline):
            request_data = {
                "query": "productivity tips",
                "creator_id": "test_creator",
                "limit": 5,
                "similarity_threshold": 0.7
            }
            
            response = await ai_client.post("/api/v1/ai/documents/search", json=request_data)
            
            assert response.status_code == 200
            result = response.json()
            
            assert "query" in result
            assert "results" in result
            assert "total_results" in result
            assert "processing_time_ms" in result

    async def test_embedding_stats_endpoint(self, ai_client: AsyncClient, mock_embedding_manager):
        """Test embedding statistics endpoint."""
        with patch('services.ai_engine_service.app.main.get_embedding_manager', return_value=mock_embedding_manager):
            response = await ai_client.get("/api/v1/ai/embeddings/stats/test_creator")
            
            assert response.status_code == 200
            result = response.json()
            
            assert "status" in result
            assert "creator_id" in result
            assert "stats" in result
            assert result["creator_id"] == "test_creator"

    async def test_cache_invalidation_endpoint(self, ai_client: AsyncClient, mock_embedding_manager):
        """Test cache invalidation endpoint."""
        mock_embedding_manager.invalidate_document_cache.return_value = True
        
        with patch('services.ai_engine_service.app.main.get_embedding_manager', return_value=mock_embedding_manager):
            response = await ai_client.delete("/api/v1/ai/cache/test_creator/document/test_doc")
            
            assert response.status_code == 200
            result = response.json()
            
            assert result["status"] == "success"
            assert result["creator_id"] == "test_creator"
            assert result["document_id"] == "test_doc"

    async def test_cache_warming_endpoint(self, ai_client: AsyncClient, mock_embedding_manager):
        """Test cache warming endpoint."""
        mock_search_cache = AsyncMock()
        mock_search_cache.warm_popular_queries.return_value = 5
        mock_embedding_manager.search_cache = mock_search_cache
        
        with patch('services.ai_engine_service.app.main.get_embedding_manager', return_value=mock_embedding_manager):
            response = await ai_client.post("/api/v1/ai/cache/test_creator/warm")
            
            assert response.status_code == 200
            result = response.json()
            
            assert result["status"] == "success"
            assert result["warmed_queries"] == 5

    async def test_pipeline_performance_endpoint(self, ai_client: AsyncClient, mock_rag_pipeline):
        """Test pipeline performance endpoint."""
        mock_rag_pipeline.get_pipeline_stats.return_value = {
            "total_queries": 100,
            "avg_processing_time_ms": 1500.0,
            "p95_processing_time_ms": 2500.0
        }
        
        with patch('services.ai_engine_service.app.main.get_rag_pipeline', return_value=mock_rag_pipeline):
            response = await ai_client.get("/api/v1/ai/pipeline/performance")
            
            assert response.status_code == 200
            result = response.json()
            
            assert "status" in result
            assert "performance_stats" in result
            assert result["performance_stats"]["total_queries"] == 100

    async def test_embedding_endpoint_success(self, ai_client: AsyncClient, test_embedding_request):
        """Test successful embedding generation."""
        response = await ai_client.post("/api/v1/ai/ollama/test-embedding", json=test_embedding_request)
        
        assert response.status_code == 200
        result = response.json()
        
        assert "embedding" in result
        assert isinstance(result["embedding"], list)
        assert len(result["embedding"]) > 0
        assert "model" in result
        assert result["model"] == test_embedding_request.get("model", "nomic-embed-text")

    async def test_embedding_endpoint_validation(self, ai_client: AsyncClient):
        """Test embedding endpoint input validation."""
        # Test empty text
        response = await ai_client.post("/api/v1/ai/ollama/test-embedding", json={"text": ""})
        assert response.status_code == 422
        
        # Test missing text field
        response = await ai_client.post("/api/v1/ai/ollama/test-embedding", json={})
        assert response.status_code == 422
        
        # Test invalid JSON
        response = await ai_client.post("/api/v1/ai/ollama/test-embedding", data="invalid json")
        assert response.status_code == 422

    async def test_chat_endpoint_success(self, ai_client: AsyncClient, test_chat_request):
        """Test successful chat completion."""
        response = await ai_client.post("/api/v1/ai/ollama/test-chat", json=test_chat_request)
        
        assert response.status_code == 200
        result = response.json()
        
        assert "response" in result
        assert isinstance(result["response"], str)
        assert len(result["response"]) > 0
        assert "model" in result

    async def test_chat_endpoint_minimal_request(self, ai_client: AsyncClient):
        """Test chat endpoint with minimal required data."""
        minimal_request = {"message": "Hello, how are you?"}
        
        response = await ai_client.post("/api/v1/ai/ollama/test-chat", json=minimal_request)
        assert response.status_code == 200
        
        result = response.json()
        assert "response" in result
        assert len(result["response"]) > 0

    async def test_chat_endpoint_with_context(self, ai_client: AsyncClient):
        """Test chat endpoint with context."""
        request_with_context = {
            "message": "What should I focus on?",
            "context": "The user is a software developer looking to improve productivity."
        }
        
        response = await ai_client.post("/api/v1/ai/ollama/test-chat", json=request_with_context)
        assert response.status_code == 200
        
        result = response.json()
        assert "response" in result
        # Response should be relevant to the context
        response_text = result["response"].lower()
        assert any(keyword in response_text for keyword in ["productivity", "focus", "developer", "software"])

    async def test_chat_endpoint_validation(self, ai_client: AsyncClient):
        """Test chat endpoint input validation."""
        # Test empty message
        response = await ai_client.post("/api/v1/ai/ollama/test-chat", json={"message": ""})
        assert response.status_code == 422
        
        # Test missing message field
        response = await ai_client.post("/api/v1/ai/ollama/test-chat", json={})
        assert response.status_code == 422

    async def test_embedding_consistency(self, ai_client: AsyncClient):
        """Test that same input produces consistent embeddings."""
        test_text = {"text": "Consistent embedding test text"}
        
        # Generate embedding twice
        response1 = await ai_client.post("/api/v1/ai/ollama/test-embedding", json=test_text)
        response2 = await ai_client.post("/api/v1/ai/ollama/test-embedding", json=test_text)
        
        assert response1.status_code == 200
        assert response2.status_code == 200
        
        embedding1 = response1.json()["embedding"]
        embedding2 = response2.json()["embedding"]
        
        # Embeddings should be identical for same input
        assert embedding1 == embedding2

    async def test_large_text_embedding(self, ai_client: AsyncClient, performance_test_data):
        """Test embedding generation with large text."""
        large_text_request = {"text": performance_test_data["long_text"]}
        
        response = await ai_client.post("/api/v1/ai/ollama/test-embedding", json=large_text_request)
        
        # Should handle large text or return appropriate error
        assert response.status_code in [200, 413, 422]  # OK, Payload Too Large, or Validation Error
        
        if response.status_code == 200:
            result = response.json()
            assert "embedding" in result
            assert len(result["embedding"]) > 0

    async def test_special_characters_handling(self, ai_client: AsyncClient):
        """Test AI endpoints with special characters and unicode."""
        special_text = {
            "text": "Special characters: émojis 🌟, symbols @#$%^&*(), and unicode: 你好世界"
        }
        
        # Test embedding
        response = await ai_client.post("/api/v1/ai/ollama/test-embedding", json=special_text)
        assert response.status_code == 200
        
        # Test chat
        chat_request = {
            "message": "Hello with émojis 🌟 and unicode: 你好"
        }
        response = await ai_client.post("/api/v1/ai/ollama/test-chat", json=chat_request)
        assert response.status_code == 200

    async def test_concurrent_ai_requests(self, ai_client: AsyncClient, performance_test_data):
        """Test concurrent AI requests."""
        
        # Create concurrent embedding requests
        embedding_tasks = [
            ai_client.post("/api/v1/ai/ollama/test-embedding", json={"text": text})
            for text in performance_test_data["concurrent_requests"][:5]
        ]
        
        # Create concurrent chat requests
        chat_tasks = [
            ai_client.post("/api/v1/ai/ollama/test-chat", json={"message": text})
            for text in performance_test_data["concurrent_requests"][:5]
        ]
        
        # Execute all requests concurrently
        all_tasks = embedding_tasks + chat_tasks
        responses = await asyncio.gather(*all_tasks, return_exceptions=True)
        
        # Check that most requests succeeded
        successful_responses = [
            r for r in responses 
            if not isinstance(r, Exception) and r.status_code == 200
        ]
        
        success_rate = len(successful_responses) / len(responses)
        assert success_rate >= 0.7  # At least 70% success rate

    async def test_ai_response_quality(self, ai_client: AsyncClient, mock_ai_responses):
        """Test AI response quality and relevance."""
        test_cases = [
            {
                "message": "How do I set better goals?",
                "expected_keywords": ["goal", "smart", "specific", "measurable", "achievable"]
            },
            {
                "message": "I need help with time management",
                "expected_keywords": ["time", "management", "productivity", "schedule", "priority"]
            },
            {
                "message": "What are some stress reduction techniques?",
                "expected_keywords": ["stress", "relax", "mindfulness", "breathing", "meditation"]
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
            keyword_found = any(
                keyword in response_text 
                for keyword in test_case["expected_keywords"]
            )
            assert keyword_found, f"Response lacks relevant keywords for: {test_case['message']}"

    async def test_ai_error_handling(self, ai_client: AsyncClient):
        """Test AI service error handling."""
        # Test with extremely long text that might cause issues
        very_long_text = {"text": "A" * 100000}  # 100k characters
        
        response = await ai_client.post("/api/v1/ai/ollama/test-embedding", json=very_long_text)
        # Should handle gracefully with appropriate error code
        assert response.status_code in [200, 413, 422, 500]
        
        if response.status_code >= 400:
            error_data = response.json()
            assert "detail" in error_data or "message" in error_data

    async def test_model_availability(self, ai_client: AsyncClient):
        """Test model availability and configuration."""
        # Test with specific model request
        model_request = {
            "text": "Test with specific model",
            "model": "nomic-embed-text"
        }
        
        response = await ai_client.post("/api/v1/ai/ollama/test-embedding", json=model_request)
        
        if response.status_code == 200:
            result = response.json()
            assert result["model"] == "nomic-embed-text"
        else:
            # Model might not be available, which is acceptable in test environment
            assert response.status_code in [404, 503]

    async def test_response_time_performance(self, ai_client: AsyncClient):
        """Test AI endpoint response times."""
        
        # Test embedding response time
        start_time = time.time()
        response = await ai_client.post("/api/v1/ai/ollama/test-embedding", json={
            "text": "Performance test for embedding generation"
        })
        embedding_time = time.time() - start_time
        
        assert response.status_code == 200
        # Embedding should complete within reasonable time (10 seconds)
        assert embedding_time < 10.0
        
        # Test chat response time
        start_time = time.time()
        response = await ai_client.post("/api/v1/ai/ollama/test-chat", json={
            "message": "Quick performance test question"
        })
        chat_time = time.time() - start_time
        
        assert response.status_code == 200
        # Chat should complete within reasonable time (15 seconds)
        assert chat_time < 15.0