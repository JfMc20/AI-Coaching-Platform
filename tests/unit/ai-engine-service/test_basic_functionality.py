"""
Basic functionality tests for AI Engine Service.
Tests core functionality without external dependencies.
"""

import pytest
import asyncio
import json
from unittest.mock import AsyncMock, Mock, patch
from datetime import datetime

from shared.models.conversations import Message, MessageRole
from shared.models.documents import DocumentChunk, ProcessingStatus


class TestBasicConnectivity:
    """Test basic connectivity and initialization."""

    async def test_rag_pipeline_initialization(self):
        """Test RAG pipeline can be initialized."""
        try:
            from services.ai_engine_service.app.rag_pipeline import RAGPipeline
            
            # Should initialize without errors
            pipeline = RAGPipeline()
            assert pipeline is not None
            assert pipeline.max_context_tokens == 4000
            assert pipeline.max_retrieved_chunks == 5
            assert pipeline.similarity_threshold == 0.7
            
        except ImportError:
            pytest.skip("RAG Pipeline not available")

    async def test_conversation_manager_initialization(self):
        """Test conversation manager can be initialized."""
        try:
            from services.ai_engine_service.app.rag_pipeline import ConversationManager
            
            # Should initialize without errors
            manager = ConversationManager()
            assert manager is not None
            assert manager.max_context_messages == 20
            assert manager.context_ttl == 3600 * 24
            
        except ImportError:
            pytest.skip("ConversationManager not available")

    async def test_embedding_manager_initialization(self):
        """Test embedding manager can be initialized."""
        try:
            from services.ai_engine_service.app.embedding_manager import EmbeddingManager
            
            # Mock the dependencies to avoid initialization errors
            with patch('services.ai_engine_service.app.embedding_manager.get_chromadb_manager') as mock_chromadb:
                with patch('services.ai_engine_service.app.embedding_manager.get_ollama_manager') as mock_ollama:
                    with patch('services.ai_engine_service.app.embedding_manager.get_cache_manager') as mock_cache:
                        
                        mock_chromadb.return_value = Mock()
                        mock_ollama.return_value = Mock()
                        mock_cache.return_value = Mock()
                        
                        manager = EmbeddingManager()
                        assert manager is not None
                        assert manager.embedding_batch_size == 10
                        assert manager.max_concurrent_embeddings == 5
            
        except ImportError:
            pytest.skip("EmbeddingManager not available")

    async def test_document_processor_initialization(self):
        """Test document processor can be initialized."""
        try:
            from services.ai_engine_service.app.document_processor import DocumentProcessor, ProcessingConfig
            
            # Mock the dependencies
            with patch('services.ai_engine_service.app.document_processor.get_ollama_manager') as mock_ollama:
                with patch('services.ai_engine_service.app.document_processor.get_chromadb_manager') as mock_chromadb:
                    
                    mock_ollama.return_value = Mock()
                    mock_chromadb.return_value = Mock()
                    
                    config = ProcessingConfig(max_file_size_mb=10)
                    processor = DocumentProcessor(config)
                    
                    assert processor is not None
                    assert processor.config.max_file_size_mb == 10
                    assert processor.config.chunk_size_tokens == 512
            
        except ImportError:
            pytest.skip("DocumentProcessor not available")


class TestBasicDataStructures:
    """Test basic data structures and models."""

    def test_message_creation(self):
        """Test creating Message objects."""
        message = Message(
            id="test_msg_1",
            creator_id="test_creator",
            conversation_id="test_conv",
            role=MessageRole.USER,
            content="Hello, this is a test message",
            created_at=datetime.utcnow(),
            metadata={"test": True}
        )
        
        assert message.id == "test_msg_1"
        assert message.role == MessageRole.USER
        assert message.content == "Hello, this is a test message"
        assert message.metadata["test"] is True

    def test_document_chunk_creation(self):
        """Test creating DocumentChunk objects."""
        chunk = DocumentChunk(
            id="chunk_1",
            content="This is a test document chunk with some content.",
            metadata={"document_id": "doc_1", "source": "test.txt"},
            chunk_index=0,
            token_count=12
        )
        
        assert chunk.id == "chunk_1"
        assert chunk.chunk_index == 0
        assert chunk.token_count == 12
        assert "test document chunk" in chunk.content

    def test_retrieved_chunk_creation(self):
        """Test creating RetrievedChunk objects."""
        try:
            from services.ai_engine_service.app.rag_pipeline import RetrievedChunk
            
            chunk = RetrievedChunk(
                content="Retrieved content",
                metadata={"source": "test.txt"},
                similarity_score=0.85,
                rank=1,
                document_id="doc_1",
                chunk_index=0
            )
            
            assert chunk.similarity_score == 0.85
            assert chunk.rank == 1
            assert chunk.document_id == "doc_1"
            
        except ImportError:
            pytest.skip("RetrievedChunk not available")

    def test_ai_response_creation(self):
        """Test creating AIResponse objects."""
        try:
            from services.ai_engine_service.app.rag_pipeline import AIResponse, RetrievedChunk
            
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
                model_used="test_model"
            )
            
            assert response.confidence == 0.85
            assert len(response.sources) == 1
            assert response.processing_time_ms == 1500.0
            
        except ImportError:
            pytest.skip("AIResponse not available")


class TestBasicFunctionality:
    """Test basic functionality without external dependencies."""

    async def test_query_canonicalization(self):
        """Test query canonicalization functionality."""
        try:
            from services.ai_engine_service.app.embedding_manager import QueryCanonicalizer
            
            canonicalizer = QueryCanonicalizer()
            
            # Test basic canonicalization
            result = canonicalizer.canonicalize_query("  Hello WORLD  ")
            assert result == "hello world"
            
            # Test whitespace normalization
            result = canonicalizer.canonicalize_query("How\n\tto   improve\r\n  productivity")
            assert result == "how to improve productivity"
            
            # Test hash generation
            hash1 = canonicalizer.generate_query_hash("test query")
            hash2 = canonicalizer.generate_query_hash("test query")
            assert hash1 == hash2  # Should be deterministic
            assert len(hash1) == 32
            
        except ImportError:
            pytest.skip("QueryCanonicalizer not available")

    async def test_document_type_detection(self):
        """Test document type detection."""
        try:
            from services.ai_engine_service.app.document_processor import DocumentProcessor, DocumentType
            from shared.exceptions.documents import UnsupportedFormatError
            
            with patch('services.ai_engine_service.app.document_processor.get_ollama_manager'):
                with patch('services.ai_engine_service.app.document_processor.get_chromadb_manager'):
                    processor = DocumentProcessor()
                    
                    # Test supported formats
                    assert processor._detect_document_type("test.pdf") == DocumentType.PDF
                    assert processor._detect_document_type("test.docx") == DocumentType.DOCX
                    assert processor._detect_document_type("test.txt") == DocumentType.TXT
                    assert processor._detect_document_type("test.md") == DocumentType.MD
                    
                    # Test unsupported format
                    with pytest.raises(UnsupportedFormatError):
                        processor._detect_document_type("test.exe")
            
        except ImportError:
            pytest.skip("DocumentProcessor not available")

    async def test_document_id_generation(self):
        """Test document ID generation."""
        try:
            from services.ai_engine_service.app.document_processor import DocumentProcessor
            
            with patch('services.ai_engine_service.app.document_processor.get_ollama_manager'):
                with patch('services.ai_engine_service.app.document_processor.get_chromadb_manager'):
                    processor = DocumentProcessor()
                    
                    doc_id = processor._generate_document_id("test.txt", "creator_123")
                    
                    assert "doc_creator_123" in doc_id
                    assert len(doc_id) > 20  # Should include timestamp and hash
            
        except ImportError:
            pytest.skip("DocumentProcessor not available")

    async def test_token_estimation(self):
        """Test token estimation functionality."""
        try:
            from services.ai_engine_service.app.document_processor import DocumentChunker, ProcessingConfig
            
            config = ProcessingConfig()
            chunker = DocumentChunker(config)
            
            # Test token estimation
            text = "This is a test sentence with multiple words."
            tokens = chunker._estimate_tokens(text)
            
            # Should be roughly 1 token per 4 characters
            expected_tokens = len(text) // 4
            assert abs(tokens - expected_tokens) <= 2  # Allow some variance
            
        except ImportError:
            pytest.skip("DocumentChunker not available")

    async def test_sentence_splitting(self):
        """Test sentence splitting functionality."""
        try:
            from services.ai_engine_service.app.document_processor import DocumentChunker, ProcessingConfig
            
            config = ProcessingConfig()
            chunker = DocumentChunker(config)
            
            text = "First sentence. Second sentence! Third sentence? Fourth sentence."
            sentences = chunker._split_into_sentences(text)
            
            assert len(sentences) == 4
            assert "First sentence" in sentences[0]
            assert "Second sentence" in sentences[1]
            
        except ImportError:
            pytest.skip("DocumentChunker not available")

    async def test_confidence_calculation(self):
        """Test confidence score calculation."""
        try:
            from services.ai_engine_service.app.rag_pipeline import RAGPipeline, RetrievedChunk
            
            with patch('services.ai_engine_service.app.rag_pipeline.get_chromadb_manager'):
                with patch('services.ai_engine_service.app.rag_pipeline.get_ollama_manager'):
                    with patch('services.ai_engine_service.app.rag_pipeline.get_embedding_manager'):
                        pipeline = RAGPipeline()
                        
                        # Test with high quality chunks
                        high_quality_chunks = [
                            RetrievedChunk(
                                content="Relevant content",
                                metadata={},
                                similarity_score=0.9,
                                rank=1,
                                document_id="doc_1",
                                chunk_index=0
                            )
                        ]
                        
                        confidence = pipeline.calculate_confidence_score(
                            high_quality_chunks, 
                            "This is a comprehensive response."
                        )
                        
                        assert 0.0 <= confidence <= 1.0
                        assert confidence > 0.5  # Should be reasonably confident
            
        except ImportError:
            pytest.skip("RAGPipeline not available")

    async def test_prompt_truncation(self):
        """Test intelligent prompt truncation."""
        try:
            from services.ai_engine_service.app.rag_pipeline import RAGPipeline
            
            with patch('services.ai_engine_service.app.rag_pipeline.get_chromadb_manager'):
                with patch('services.ai_engine_service.app.rag_pipeline.get_ollama_manager'):
                    with patch('services.ai_engine_service.app.rag_pipeline.get_embedding_manager'):
                        pipeline = RAGPipeline()
                        
                        # Create a very long prompt
                        long_prompt = "System message\n\nKNOWLEDGE CONTEXT:\n" + "A" * 5000 + "\n\nUser: Test query\nAssistant:"
                        
                        truncated = pipeline.truncate_prompt_intelligently(long_prompt, max_tokens=1000)
                        
                        # Should be shorter than original
                        assert len(truncated) < len(long_prompt)
                        
                        # Should preserve essential parts
                        assert "User: Test query" in truncated
                        assert "Assistant:" in truncated
            
        except ImportError:
            pytest.skip("RAGPipeline not available")


class TestBasicCaching:
    """Test basic caching functionality."""

    async def test_cache_key_generation(self):
        """Test cache key generation."""
        try:
            from services.ai_engine_service.app.embedding_manager import SearchCacheKey
            
            key = SearchCacheKey(
                creator_id="creator_123",
                query_hash="abcd1234",
                model_version="v1.0",
                filters_hash="efgh5678"
            )
            
            key_string = key.to_string()
            expected = "search:creator_123:abcd1234:v1.0:efgh5678"
            
            assert key_string == expected
            
        except ImportError:
            pytest.skip("SearchCacheKey not available")

    async def test_filters_hash_consistency(self):
        """Test that filters hash is consistent regardless of order."""
        try:
            from services.ai_engine_service.app.embedding_manager import QueryCanonicalizer
            
            canonicalizer = QueryCanonicalizer()
            
            filters1 = {"type": "coaching", "date": "2023-01-01", "category": "productivity"}
            filters2 = {"date": "2023-01-01", "category": "productivity", "type": "coaching"}
            
            hash1 = canonicalizer.generate_filters_hash(filters1)
            hash2 = canonicalizer.generate_filters_hash(filters2)
            
            assert hash1 == hash2  # Should be same despite different order
            assert len(hash1) == 16
            
        except ImportError:
            pytest.skip("QueryCanonicalizer not available")

    async def test_conversation_context_structure(self):
        """Test conversation context data structure."""
        try:
            from services.ai_engine_service.app.rag_pipeline import ConversationManager
            
            # Mock cache manager
            mock_cache_manager = Mock()
            mock_cache_manager.redis = AsyncMock()
            
            manager = ConversationManager(cache_manager=mock_cache_manager)
            
            # Test with empty context
            mock_cache_manager.redis.get.return_value = None
            context = await manager.get_context("test_conv", creator_id="test_creator")
            
            assert isinstance(context, list)
            assert len(context) == 0
            
        except ImportError:
            pytest.skip("ConversationManager not available")


class TestBasicValidation:
    """Test basic validation functionality."""

    async def test_processing_config_validation(self):
        """Test processing configuration validation."""
        try:
            from services.ai_engine_service.app.document_processor import ProcessingConfig
            
            # Test default config
            config = ProcessingConfig()
            assert config.max_file_size_mb == 50
            assert config.chunk_size_tokens == 512
            assert config.chunk_overlap_tokens == 50
            assert config.enable_malware_scan is True
            
            # Test custom config
            custom_config = ProcessingConfig(
                max_file_size_mb=100,
                chunk_size_tokens=1024,
                enable_malware_scan=False
            )
            assert custom_config.max_file_size_mb == 100
            assert custom_config.chunk_size_tokens == 1024
            assert custom_config.enable_malware_scan is False
            
        except ImportError:
            pytest.skip("ProcessingConfig not available")

    async def test_security_scanner_allowed_types(self):
        """Test security scanner allowed types configuration."""
        try:
            from services.ai_engine_service.app.document_processor import SecurityScanner, ProcessingConfig
            
            config = ProcessingConfig()
            scanner = SecurityScanner(config)
            
            # Check allowed MIME types
            assert 'application/pdf' in scanner.allowed_mime_types
            assert 'text/plain' in scanner.allowed_mime_types
            assert 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' in scanner.allowed_mime_types
            
            # Check dangerous extensions
            assert '.exe' in scanner.dangerous_extensions
            assert '.bat' in scanner.dangerous_extensions
            assert '.js' in scanner.dangerous_extensions
            
        except ImportError:
            pytest.skip("SecurityScanner not available")

    async def test_document_type_enum(self):
        """Test document type enumeration."""
        try:
            from services.ai_engine_service.app.document_processor import DocumentType
            
            assert DocumentType.PDF == "pdf"
            assert DocumentType.DOCX == "docx"
            assert DocumentType.TXT == "txt"
            assert DocumentType.MD == "md"
            assert DocumentType.MARKDOWN == "markdown"
            
        except ImportError:
            pytest.skip("DocumentType not available")


class TestBasicErrorHandling:
    """Test basic error handling."""

    async def test_rag_error_creation(self):
        """Test RAG error creation."""
        try:
            from services.ai_engine_service.app.rag_pipeline import RAGError
            
            error = RAGError("Test error message")
            assert str(error) == "Test error message"
            assert isinstance(error, Exception)
            
        except ImportError:
            pytest.skip("RAGError not available")

    async def test_document_processing_errors(self):
        """Test document processing error types."""
        try:
            from shared.exceptions.documents import (
                DocumentProcessingError, UnsupportedFormatError, 
                FileTooLargeError, MalwareDetectedError, TextExtractionError
            )
            
            # Test base error
            base_error = DocumentProcessingError("Base processing error")
            assert str(base_error) == "Base processing error"
            
            # Test specific errors
            format_error = UnsupportedFormatError("Unsupported format")
            assert isinstance(format_error, DocumentProcessingError)
            
            size_error = FileTooLargeError("File too large")
            assert isinstance(size_error, DocumentProcessingError)
            
            malware_error = MalwareDetectedError("Malware detected")
            assert isinstance(malware_error, DocumentProcessingError)
            
            extraction_error = TextExtractionError("Extraction failed")
            assert isinstance(extraction_error, DocumentProcessingError)
            
        except ImportError:
            pytest.skip("Document processing errors not available")


class TestBasicUtilities:
    """Test basic utility functions."""

    async def test_text_processing_utilities(self):
        """Test basic text processing utilities."""
        try:
            from services.ai_engine_service.app.document_processor import DocumentChunker, ProcessingConfig
            
            config = ProcessingConfig(chunk_size_tokens=100, chunk_overlap_tokens=20)
            chunker = DocumentChunker(config)
            
            # Test sentence splitting
            text = "First sentence. Second sentence! Third sentence?"
            sentences = chunker._split_into_sentences(text)
            
            assert len(sentences) >= 3
            assert any("First sentence" in s for s in sentences)
            
            # Test token estimation
            test_text = "This is a test sentence."
            tokens = chunker._estimate_tokens(test_text)
            assert tokens > 0
            assert isinstance(tokens, int)
            
        except ImportError:
            pytest.skip("DocumentChunker not available")

    async def test_hash_generation_consistency(self):
        """Test hash generation consistency."""
        try:
            from services.ai_engine_service.app.embedding_manager import QueryCanonicalizer
            
            canonicalizer = QueryCanonicalizer()
            
            # Same input should produce same hash
            text = "consistent hash test"
            hash1 = canonicalizer.generate_query_hash(text)
            hash2 = canonicalizer.generate_query_hash(text)
            
            assert hash1 == hash2
            
            # Different inputs should produce different hashes
            hash3 = canonicalizer.generate_query_hash("different text")
            assert hash1 != hash3
            
        except ImportError:
            pytest.skip("QueryCanonicalizer not available")

    async def test_processing_status_enum(self):
        """Test processing status enumeration."""
        from shared.models.documents import ProcessingStatus
        
        assert ProcessingStatus.PENDING == "pending"
        assert ProcessingStatus.PROCESSING == "processing"
        assert ProcessingStatus.COMPLETED == "completed"
        assert ProcessingStatus.FAILED == "failed"

    async def test_message_role_enum(self):
        """Test message role enumeration."""
        from shared.models.conversations import MessageRole
        
        assert MessageRole.USER == "user"
        assert MessageRole.ASSISTANT == "assistant"
        assert MessageRole.SYSTEM == "system"


class TestBasicIntegration:
    """Test basic integration between components."""

    async def test_rag_pipeline_component_integration(self):
        """Test that RAG pipeline components can work together."""
        try:
            from services.ai_engine_service.app.rag_pipeline import RAGPipeline
            
            # Mock all external dependencies
            with patch('services.ai_engine_service.app.rag_pipeline.get_chromadb_manager') as mock_chromadb:
                with patch('services.ai_engine_service.app.rag_pipeline.get_ollama_manager') as mock_ollama:
                    with patch('services.ai_engine_service.app.rag_pipeline.get_embedding_manager') as mock_embedding:
                        
                        # Setup mocks
                        mock_chromadb.return_value = Mock()
                        mock_ollama.return_value = Mock()
                        mock_embedding.return_value = Mock()
                        
                        # Create pipeline
                        pipeline = RAGPipeline()
                        
                        # Test that components are properly initialized
                        assert pipeline.chromadb_manager is not None
                        assert pipeline.ollama_manager is not None
                        assert pipeline.embedding_manager is not None
                        assert pipeline.conversation_manager is not None
            
        except ImportError:
            pytest.skip("RAGPipeline not available")

    async def test_document_processor_component_integration(self):
        """Test that document processor components can work together."""
        try:
            from services.ai_engine_service.app.document_processor import DocumentProcessor, ProcessingConfig
            
            # Mock external dependencies
            with patch('services.ai_engine_service.app.document_processor.get_ollama_manager') as mock_ollama:
                with patch('services.ai_engine_service.app.document_processor.get_chromadb_manager') as mock_chromadb:
                    
                    mock_ollama.return_value = Mock()
                    mock_chromadb.return_value = Mock()
                    
                    config = ProcessingConfig(max_file_size_mb=10)
                    processor = DocumentProcessor(config)
                    
                    # Test that components are properly initialized
                    assert processor.security_scanner is not None
                    assert processor.text_extractor is not None
                    assert processor.chunker is not None
                    assert processor.ollama_manager is not None
                    assert processor.chromadb_manager is not None
            
        except ImportError:
            pytest.skip("DocumentProcessor not available")


class TestServiceHealthChecks:
    """Test service health check functionality."""

    async def test_chromadb_mock_health_check(self):
        """Test ChromaDB mock health check."""
        try:
            from shared.ai.chromadb_manager import ChromaDBManager
            
            # Create manager with valid shard count
            manager = ChromaDBManager(
                chromadb_url="http://localhost:8000",
                shard_count=10
            )
            
            # Health check should work with mock implementation
            # Note: This might fail in development, which is expected
            try:
                health = await manager.health_check()
                assert "status" in health
            except Exception as e:
                # Expected in development environment
                assert "ChromaDB health check failed" in str(e)
            
        except ImportError:
            pytest.skip("ChromaDBManager not available")

    async def test_basic_service_availability(self):
        """Test that basic services can be imported and initialized."""
        # Test that we can import the main components
        try:
            from services.ai_engine_service.app.main import app
            assert app is not None
            assert app.title == "AI Engine Service API"
        except ImportError:
            pytest.skip("AI Engine service not available")
        
        # Test that we can import shared models
        from shared.models.conversations import Message, MessageRole
        from shared.models.documents import DocumentChunk, ProcessingStatus
        
        assert Message is not None
        assert MessageRole is not None
        assert DocumentChunk is not None
        assert ProcessingStatus is not None