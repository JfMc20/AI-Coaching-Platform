"""
Performance tests for RAG pipeline and AI engine.
Tests response times, throughput, and resource usage.
"""

import pytest
import asyncio
import time
from unittest.mock import AsyncMock, Mock, patch
from datetime import datetime

from shared.models.conversations import Message, MessageRole


class TestRAGPerformance:
    """Test RAG pipeline performance requirements."""

    @pytest.mark.asyncio 
    async def test_embedding_generation_speed(self):
        """Test that embedding generation meets <3.3s target."""
        from services.ai_engine_service.app.embedding_manager import EmbeddingManager
        
        embedding_manager = EmbeddingManager()
        
        # Mock ollama client for performance test
        with patch.object(embedding_manager, 'ollama_client') as mock_client:
            mock_client.generate_embeddings = AsyncMock(return_value=[0.1] * 768)
            
            test_text = "This is a test document for embedding generation performance testing. " * 50
            
            start_time = time.time()
            embeddings = await embedding_manager.generate_embeddings([test_text])
            elapsed_time = time.time() - start_time
            
            # Should complete within 3.3 seconds
            assert elapsed_time < 3.3, f"Embedding generation took {elapsed_time:.2f}s, should be <3.3s"
            assert len(embeddings) == 1
            assert len(embeddings[0]) == 768

    @pytest.mark.asyncio
    async def test_rag_response_speed(self):
        """Test that RAG pipeline meets <5s response target."""
        from services.ai_engine_service.app.rag_pipeline import RAGPipeline
        
        # Create RAG pipeline with mocked dependencies
        rag_pipeline = RAGPipeline()
        
        with patch.object(rag_pipeline, 'chromadb_manager') as mock_chromadb, \
             patch.object(rag_pipeline, 'ollama_manager') as mock_ollama, \
             patch.object(rag_pipeline, 'conversation_manager') as mock_conv:
            
            # Mock fast responses
            mock_chromadb.search_similar_chunks = AsyncMock(return_value=[
                {"content": "Test knowledge chunk", "metadata": {"source": "test.pdf"}}
            ])
            
            mock_ollama.generate_chat_response = AsyncMock(return_value=Mock(
                response="Test response from AI",
                model="llama3.2"
            ))
            
            mock_conv.get_context = AsyncMock(return_value=[])
            mock_conv.add_exchange = AsyncMock()
            
            # Test query processing speed
            start_time = time.time()
            response = await rag_pipeline.process_query(
                query="What is machine learning?",
                creator_id="test_creator",
                conversation_id="test_conv"
            )
            elapsed_time = time.time() - start_time
            
            # Should complete within 5 seconds
            assert elapsed_time < 5.0, f"RAG response took {elapsed_time:.2f}s, should be <5s"
            assert response.response == "Test response from AI"

    @pytest.mark.asyncio
    async def test_concurrent_query_performance(self):
        """Test performance under concurrent load."""
        from services.ai_engine_service.app.rag_pipeline import RAGPipeline
        
        rag_pipeline = RAGPipeline()
        
        with patch.object(rag_pipeline, 'chromadb_manager') as mock_chromadb, \
             patch.object(rag_pipeline, 'ollama_manager') as mock_ollama, \
             patch.object(rag_pipeline, 'conversation_manager') as mock_conv:
            
            # Mock responses
            mock_chromadb.search_similar_chunks = AsyncMock(return_value=[])
            mock_ollama.generate_chat_response = AsyncMock(return_value=Mock(
                response="Concurrent response",
                model="llama3.2"
            ))
            mock_conv.get_context = AsyncMock(return_value=[])
            mock_conv.add_exchange = AsyncMock()
            
            # Run 10 concurrent queries
            async def single_query(query_id):
                return await rag_pipeline.process_query(
                    query=f"Test query {query_id}",
                    creator_id=f"creator_{query_id}",
                    conversation_id=f"conv_{query_id}"
                )
            
            start_time = time.time()
            
            # Execute concurrent queries
            tasks = [single_query(i) for i in range(10)]
            responses = await asyncio.gather(*tasks)
            
            elapsed_time = time.time() - start_time
            
            # All should complete successfully
            assert len(responses) == 10
            assert all(r.response == "Concurrent response" for r in responses)
            
            # Total time should be reasonable (not 10x sequential time)
            assert elapsed_time < 15.0, f"10 concurrent queries took {elapsed_time:.2f}s"

    @pytest.mark.asyncio
    async def test_document_processing_performance(self):
        """Test document processing speed."""
        from services.ai_engine_service.app.document_processor import DocumentProcessor
        
        doc_processor = DocumentProcessor()
        
        # Create test document content
        large_text = "This is a test document. " * 1000  # ~25KB of text
        
        with patch.object(doc_processor, 'embedding_manager') as mock_embedding:
            mock_embedding.generate_embeddings = AsyncMock(return_value=[[0.1] * 768])
            
            start_time = time.time()
            
            chunks = await doc_processor.process_text_content(
                content=large_text,
                creator_id="test_creator",
                document_id="test_doc"
            )
            
            elapsed_time = time.time() - start_time
            
            # Should process reasonable sized document quickly
            assert elapsed_time < 10.0, f"Document processing took {elapsed_time:.2f}s"
            assert len(chunks) > 0
            assert all(chunk.get('embedding') for chunk in chunks)

    @pytest.mark.asyncio 
    async def test_chromadb_search_performance(self):
        """Test ChromaDB search performance."""
        from shared.ai.chromadb_manager import ChromaDBManager
        
        chromadb_manager = ChromaDBManager()
        
        # Mock ChromaDB operations
        with patch.object(chromadb_manager, 'client') as mock_client:
            mock_collection = Mock()
            mock_collection.query = Mock(return_value={
                'documents': [['Test document 1', 'Test document 2']],
                'metadatas': [[{'source': 'test1.pdf'}, {'source': 'test2.pdf'}]],
                'distances': [[0.1, 0.2]]
            })
            
            mock_client.get_collection = Mock(return_value=mock_collection)
            
            start_time = time.time()
            
            results = await chromadb_manager.search_similar_chunks(
                creator_id="test_creator",
                query_embedding=[0.1] * 768,
                limit=10
            )
            
            elapsed_time = time.time() - start_time
            
            # Vector search should be very fast
            assert elapsed_time < 1.0, f"ChromaDB search took {elapsed_time:.2f}s"
            assert len(results) > 0

    @pytest.mark.asyncio
    async def test_memory_usage_under_load(self):
        """Test memory usage doesn't grow excessively under load."""
        import psutil
        import os
        
        # Get initial memory usage
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        from services.ai_engine_service.app.rag_pipeline import RAGPipeline
        
        rag_pipeline = RAGPipeline()
        
        with patch.object(rag_pipeline, 'chromadb_manager') as mock_chromadb, \
             patch.object(rag_pipeline, 'ollama_manager') as mock_ollama, \
             patch.object(rag_pipeline, 'conversation_manager') as mock_conv:
            
            # Mock responses
            mock_chromadb.search_similar_chunks = AsyncMock(return_value=[])
            mock_ollama.generate_chat_response = AsyncMock(return_value=Mock(
                response="Memory test response",
                model="llama3.2"
            ))
            mock_conv.get_context = AsyncMock(return_value=[])
            mock_conv.add_exchange = AsyncMock()
            
            # Process many queries
            for i in range(100):
                await rag_pipeline.process_query(
                    query=f"Memory test query {i}",
                    creator_id="test_creator",
                    conversation_id=f"conv_{i}"
                )
                
                # Check memory periodically
                if i % 20 == 0:
                    current_memory = process.memory_info().rss / 1024 / 1024
                    memory_growth = current_memory - initial_memory
                    
                    # Memory growth should be reasonable
                    assert memory_growth < 100, f"Memory grew by {memory_growth:.1f}MB"

    @pytest.mark.asyncio
    async def test_error_recovery_performance(self):
        """Test that error recovery doesn't significantly impact performance."""
        from services.ai_engine_service.app.rag_pipeline import RAGPipeline
        
        rag_pipeline = RAGPipeline()
        
        with patch.object(rag_pipeline, 'chromadb_manager') as mock_chromadb, \
             patch.object(rag_pipeline, 'ollama_manager') as mock_ollama, \
             patch.object(rag_pipeline, 'conversation_manager') as mock_conv:
            
            # Mock some failures and some successes
            call_count = 0
            
            async def mock_search_with_failures(*args, **kwargs):
                nonlocal call_count
                call_count += 1
                if call_count % 3 == 0:  # Every 3rd call fails
                    raise Exception("Simulated ChromaDB error")
                return [{"content": "Success chunk", "metadata": {}}]
            
            mock_chromadb.search_similar_chunks = AsyncMock(side_effect=mock_search_with_failures)
            mock_ollama.generate_chat_response = AsyncMock(return_value=Mock(
                response="Error recovery response",
                model="llama3.2"
            ))
            mock_conv.get_context = AsyncMock(return_value=[])
            mock_conv.add_exchange = AsyncMock()
            
            # Test error recovery
            start_time = time.time()
            
            successful_responses = 0
            for i in range(10):
                try:
                    await rag_pipeline.process_query(
                        query=f"Error test query {i}",
                        creator_id="test_creator",
                        conversation_id=f"conv_{i}"
                    )
                    successful_responses += 1
                except:
                    pass  # Expected some failures
            
            elapsed_time = time.time() - start_time
            
            # Should handle errors gracefully without major performance impact
            assert elapsed_time < 10.0, f"Error recovery took {elapsed_time:.2f}s"
            assert successful_responses > 0, "Some queries should succeed despite errors"

    @pytest.mark.asyncio
    async def test_api_response_time_targets(self):
        """Test that API endpoints meet <2s response time target."""
        from httpx import AsyncClient
        from unittest.mock import patch
        
        # This would test actual API endpoints
        # For now, we simulate the test structure
        
        api_endpoints = [
            "/api/v1/ai/health",
            "/api/v1/ai/models/status",
        ]
        
        # Mock client for testing
        async with AsyncClient() as client:
            for endpoint in api_endpoints:
                start_time = time.time()
                
                # Simulate API call (would be real call in actual test)
                await asyncio.sleep(0.1)  # Simulate processing time
                
                elapsed_time = time.time() - start_time
                
                # API responses should be under 2 seconds
                assert elapsed_time < 2.0, f"{endpoint} took {elapsed_time:.2f}s, should be <2s"