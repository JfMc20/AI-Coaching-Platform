"""
Tests for RAG Pipeline implementation.
Tests conversation management, knowledge retrieval, prompt building, and response generation.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, Mock, patch
from datetime import datetime

from shared.models.conversations import Message, MessageRole
from shared.exceptions.base import BaseServiceException

try:
    from services.ai_engine_service.app.rag_pipeline import (
        RAGPipeline, ConversationManager, RetrievedChunk, AIResponse,
        RAGError, ConversationError
    )
except ImportError:
    pytest.skip("RAG Pipeline components not available", allow_module_level=True)


class TestConversationManager:
    """Test conversation context management."""

    @pytest.fixture
    def conversation_manager(self):
        """Create conversation manager with mocked cache."""
        mock_cache_manager = Mock()
        mock_cache_manager.redis = AsyncMock()
        return ConversationManager(cache_manager=mock_cache_manager)

    async def test_get_context_empty(self, conversation_manager):
        """Test getting context for new conversation."""
        conversation_manager.cache_manager.redis.get.return_value = None
        
        context = await conversation_manager.get_context(
            conversation_id="test_conv_1",
            max_messages=10,
            creator_id="test_creator"
        )
        
        assert context == []

    async def test_get_context_with_messages(self, conversation_manager):
        """Test getting context with existing messages."""
        # Mock cached messages
        cached_messages = [
            {
                "id": "msg_1",
                "creator_id": "test_creator",
                "conversation_id": "test_conv_1",
                "role": "user",
                "content": "Hello",
                "created_at": datetime.utcnow().isoformat(),
                "metadata": {}
            },
            {
                "id": "msg_2",
                "creator_id": "test_creator",
                "conversation_id": "test_conv_1",
                "role": "assistant",
                "content": "Hi there!",
                "created_at": datetime.utcnow().isoformat(),
                "processing_time_ms": 500,
                "metadata": {"model_used": "llama2:7b-chat"}
            }
        ]
        
        conversation_manager.cache_manager.redis.get.return_value = cached_messages
        
        context = await conversation_manager.get_context(
            conversation_id="test_conv_1",
            max_messages=10,
            creator_id="test_creator"
        )
        
        assert len(context) == 2
        assert context[0].role == MessageRole.USER
        assert context[1].role == MessageRole.ASSISTANT
        assert context[0].content == "Hello"
        assert context[1].content == "Hi there!"

    async def test_add_exchange(self, conversation_manager):
        """Test adding user-AI exchange to conversation."""
        conversation_manager.cache_manager.redis.get.return_value = []
        conversation_manager.cache_manager.redis.set.return_value = True
        
        success = await conversation_manager.add_exchange(
            conversation_id="test_conv_1",
            user_message="How can I improve my productivity?",
            ai_response="Try the Pomodoro technique for better focus.",
            creator_id="test_creator",
            processing_time_ms=1500,
            model_used="llama2:7b-chat"
        )
        
        assert success is True
        conversation_manager.cache_manager.redis.set.assert_called_once()

    async def test_get_conversation_summary(self, conversation_manager):
        """Test getting conversation summary statistics."""
        # Mock messages for summary
        messages = [
            Message(
                id="msg_1",
                creator_id="test_creator",
                conversation_id="test_conv_1",
                role=MessageRole.USER,
                content="Hello",
                created_at=datetime.utcnow(),
                metadata={}
            ),
            Message(
                id="msg_2",
                creator_id="test_creator",
                conversation_id="test_conv_1",
                role=MessageRole.ASSISTANT,
                content="Hi there!",
                created_at=datetime.utcnow(),
                processing_time_ms=500,
                metadata={}
            )
        ]
        
        with patch.object(conversation_manager, 'get_context', return_value=messages):
            summary = await conversation_manager.get_conversation_summary(
                conversation_id="test_conv_1",
                creator_id="test_creator"
            )
        
        assert summary is not None
        assert summary["total_messages"] == 2
        assert summary["user_messages"] == 1
        assert summary["ai_messages"] == 1
        assert summary["avg_response_time_ms"] == 500


class TestRAGPipeline:
    """Test RAG pipeline functionality."""

    @pytest.fixture
    def mock_managers(self):
        """Create mocked managers for RAG pipeline."""
        mock_chromadb = AsyncMock()
        mock_ollama = AsyncMock()
        mock_conversation = AsyncMock()
        mock_embedding = AsyncMock()
        
        return {
            "chromadb": mock_chromadb,
            "ollama": mock_ollama,
            "conversation": mock_conversation,
            "embedding": mock_embedding
        }

    @pytest.fixture
    def rag_pipeline(self, mock_managers):
        """Create RAG pipeline with mocked dependencies."""
        return RAGPipeline(
            chromadb_manager=mock_managers["chromadb"],
            ollama_manager=mock_managers["ollama"],
            conversation_manager=mock_managers["conversation"],
            embedding_manager=mock_managers["embedding"]
        )

    async def test_retrieve_knowledge_success(self, rag_pipeline, mock_managers):
        """Test successful knowledge retrieval."""
        # Mock embedding manager search results
        mock_search_results = [
            {
                "document_id": "doc_1",
                "chunk_index": 0,
                "content": "Productivity tips: Use the Pomodoro technique.",
                "similarity_score": 0.85,
                "metadata": {"source": "productivity.txt"},
                "rank": 1
            },
            {
                "document_id": "doc_2",
                "chunk_index": 1,
                "content": "Time management strategies for better focus.",
                "similarity_score": 0.78,
                "metadata": {"source": "time_management.txt"},
                "rank": 2
            }
        ]
        
        mock_managers["embedding"].search_similar_documents.return_value = mock_search_results
        
        chunks = await rag_pipeline.retrieve_knowledge(
            query="How to improve productivity?",
            creator_id="test_creator",
            limit=5
        )
        
        assert len(chunks) == 2
        assert chunks[0].similarity_score == 0.85
        assert chunks[1].similarity_score == 0.78
        assert "Pomodoro" in chunks[0].content

    async def test_build_contextual_prompt(self, rag_pipeline):
        """Test contextual prompt building."""
        # Mock conversation context
        conversation_context = [
            Message(
                id="msg_1",
                creator_id="test_creator",
                conversation_id="test_conv",
                role=MessageRole.USER,
                content="I need help with time management",
                created_at=datetime.utcnow(),
                metadata={}
            )
        ]
        
        # Mock knowledge chunks
        knowledge_chunks = [
            RetrievedChunk(
                content="The Pomodoro Technique is effective for time management.",
                metadata={"source": "productivity.txt"},
                similarity_score=0.85,
                rank=1,
                document_id="doc_1",
                chunk_index=0
            )
        ]
        
        prompt = await rag_pipeline.build_contextual_prompt(
            query="What are some specific techniques?",
            conversation_context=conversation_context,
            knowledge_chunks=knowledge_chunks,
            max_tokens=4000
        )
        
        assert "AI coaching assistant" in prompt
        assert "KNOWLEDGE CONTEXT" in prompt
        assert "Pomodoro Technique" in prompt
        assert "CONVERSATION HISTORY" in prompt
        assert "time management" in prompt
        assert "What are some specific techniques?" in prompt

    async def test_calculate_confidence_score(self, rag_pipeline):
        """Test confidence score calculation."""
        # High quality chunks
        high_quality_chunks = [
            RetrievedChunk(
                content="Relevant content",
                metadata={},
                similarity_score=0.9,
                rank=1,
                document_id="doc_1",
                chunk_index=0
            ),
            RetrievedChunk(
                content="Also relevant",
                metadata={},
                similarity_score=0.85,
                rank=2,
                document_id="doc_2",
                chunk_index=0
            )
        ]
        
        response = "This is a comprehensive response with good length and detail."
        
        confidence = rag_pipeline.calculate_confidence_score(high_quality_chunks, response)
        
        assert 0.7 <= confidence <= 1.0  # Should be high confidence
        
        # Low quality chunks
        low_quality_chunks = [
            RetrievedChunk(
                content="Less relevant",
                metadata={},
                similarity_score=0.3,
                rank=1,
                document_id="doc_3",
                chunk_index=0
            )
        ]
        
        confidence_low = rag_pipeline.calculate_confidence_score(low_quality_chunks, "Short.")
        
        assert confidence_low < confidence  # Should be lower confidence

    async def test_process_query_complete_pipeline(self, rag_pipeline, mock_managers):
        """Test complete query processing pipeline."""
        # Mock conversation context
        mock_managers["conversation"].get_context.return_value = []
        
        # Mock knowledge retrieval
        mock_search_results = [
            {
                "document_id": "doc_1",
                "chunk_index": 0,
                "content": "Productivity advice content",
                "similarity_score": 0.85,
                "metadata": {"source": "productivity.txt"},
                "rank": 1
            }
        ]
        mock_managers["embedding"].search_similar_documents.return_value = mock_search_results
        
        # Mock AI response
        mock_chat_response = Mock()
        mock_chat_response.response = "Here's some helpful productivity advice."
        mock_chat_response.model = "llama2:7b-chat"
        mock_managers["ollama"].generate_chat_response.return_value = mock_chat_response
        
        # Mock conversation update
        mock_managers["conversation"].add_exchange.return_value = True
        
        result = await rag_pipeline.process_query(
            query="How can I be more productive?",
            creator_id="test_creator",
            conversation_id="test_conv_1"
        )
        
        assert isinstance(result, AIResponse)
        assert result.response == "Here's some helpful productivity advice."
        assert result.model_used == "llama2:7b-chat"
        assert len(result.sources) == 1
        assert result.confidence > 0
        assert result.processing_time_ms > 0

    async def test_process_query_error_handling(self, rag_pipeline, mock_managers):
        """Test error handling in query processing."""
        # Mock embedding manager to raise error
        mock_managers["embedding"].search_similar_documents.side_effect = Exception("Search failed")
        
        with pytest.raises(RAGError):
            await rag_pipeline.process_query(
                query="Test query",
                creator_id="test_creator",
                conversation_id="test_conv_1"
            )

    async def test_truncate_prompt_intelligently(self, rag_pipeline):
        """Test intelligent prompt truncation."""
        # Create a very long prompt
        long_prompt = "System message\n\nKNOWLEDGE CONTEXT:\n" + "A" * 10000 + "\n\nCONVERSATION HISTORY:\nUser: Hello\nAssistant: Hi\n\nUser: Test query\nAssistant:"
        
        truncated = rag_pipeline.truncate_prompt_intelligently(long_prompt, max_tokens=1000)
        
        # Should be shorter than original
        assert len(truncated) < len(long_prompt)
        
        # Should preserve essential parts
        assert "User: Test query" in truncated
        assert "Assistant:" in truncated

    async def test_get_pipeline_stats(self, rag_pipeline):
        """Test pipeline performance statistics."""
        # Add some processing times
        rag_pipeline._processing_times = [100.0, 150.0, 200.0, 120.0, 180.0]
        
        stats = await rag_pipeline.get_pipeline_stats()
        
        assert stats["total_queries"] == 5
        assert stats["avg_processing_time_ms"] == 150.0
        assert stats["min_processing_time_ms"] == 100.0
        assert stats["max_processing_time_ms"] == 200.0
        assert "p95_processing_time_ms" in stats


class TestRetrievedChunk:
    """Test RetrievedChunk data structure."""

    def test_retrieved_chunk_creation(self):
        """Test creating RetrievedChunk instance."""
        chunk = RetrievedChunk(
            content="Test content",
            metadata={"source": "test.txt"},
            similarity_score=0.85,
            rank=1,
            document_id="doc_1",
            chunk_index=0
        )
        
        assert chunk.content == "Test content"
        assert chunk.similarity_score == 0.85
        assert chunk.rank == 1
        assert chunk.document_id == "doc_1"


class TestAIResponse:
    """Test AIResponse data structure."""

    def test_ai_response_creation(self):
        """Test creating AIResponse instance."""
        sources = [
            RetrievedChunk(
                content="Source content",
                metadata={},
                similarity_score=0.8,
                rank=1,
                document_id="doc_1",
                chunk_index=0
            )
        ]
        
        response = AIResponse(
            response="AI generated response",
            sources=sources,
            confidence=0.85,
            conversation_id="conv_1",
            processing_time_ms=1500.0,
            model_used="llama2:7b-chat"
        )
        
        assert response.response == "AI generated response"
        assert response.confidence == 0.85
        assert len(response.sources) == 1
        assert response.processing_time_ms == 1500.0


class TestRAGPipelineIntegration:
    """Integration tests for RAG pipeline components."""

    async def test_conversation_flow(self):
        """Test complete conversation flow."""
        # This would be an integration test with real components
        # For now, we'll test the flow with mocks
        
        conversation_manager = ConversationManager()
        
        # Mock the cache manager
        with patch.object(conversation_manager, 'cache_manager') as mock_cache:
            mock_cache.redis.get.return_value = []
            mock_cache.redis.set.return_value = True
            
            # Add first exchange
            success1 = await conversation_manager.add_exchange(
                conversation_id="flow_test",
                user_message="Hello",
                ai_response="Hi there!",
                creator_id="test_creator"
            )
            
            # Add second exchange
            success2 = await conversation_manager.add_exchange(
                conversation_id="flow_test",
                user_message="How are you?",
                ai_response="I'm doing well, thank you!",
                creator_id="test_creator"
            )
            
            assert success1 is True
            assert success2 is True
            assert mock_cache.redis.set.call_count == 2

    async def test_error_recovery(self):
        """Test error recovery in RAG pipeline."""
        rag_pipeline = RAGPipeline()
        
        # Test with invalid inputs
        with pytest.raises(RAGError):
            await rag_pipeline.retrieve_knowledge("", "invalid_creator", 0)

    async def test_concurrent_processing(self):
        """Test concurrent query processing."""
        rag_pipeline = RAGPipeline()
        
        # Mock dependencies
        with patch.object(rag_pipeline, 'embedding_manager') as mock_embedding:
            mock_embedding.search_similar_documents.return_value = []
            
            with patch.object(rag_pipeline, 'ollama_manager') as mock_ollama:
                mock_response = Mock()
                mock_response.response = "Concurrent response"
                mock_response.model = "test_model"
                mock_ollama.generate_chat_response.return_value = mock_response
                
                with patch.object(rag_pipeline, 'conversation_manager') as mock_conv:
                    mock_conv.get_context.return_value = []
                    mock_conv.add_exchange.return_value = True
                    
                    # Process multiple queries concurrently
                    tasks = [
                        rag_pipeline.process_query(
                            f"Query {i}",
                            "test_creator",
                            f"conv_{i}"
                        )
                        for i in range(3)
                    ]
                    
                    results = await asyncio.gather(*tasks)
                    
                    assert len(results) == 3
                    for result in results:
                        assert isinstance(result, AIResponse)
                        assert result.response == "Concurrent response"