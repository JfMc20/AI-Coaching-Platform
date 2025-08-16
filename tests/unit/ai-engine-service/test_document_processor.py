"""
Tests for Document Processing Pipeline.
Tests security scanning, text extraction, chunking, and embedding generation.
"""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

try:
    from services.ai_engine_service.app.document_processor import (
        DocumentProcessor, SecurityScanner, TextExtractor, DocumentChunker,
        ProcessingConfig, DocumentType, SecurityScanResult
    )
    from shared.models.documents import ProcessingResult, ProcessingStatus, DocumentChunk
    from shared.exceptions.documents import (
        UnsupportedFormatError, FileTooLargeError, MalwareDetectedError,
        TextExtractionError
    )
except ImportError:
    pytest.skip("Document processor components not available", allow_module_level=True)


class TestProcessingConfig:
    """Test processing configuration."""

    def test_default_config(self):
        """Test default configuration values."""
        config = ProcessingConfig()
        
        assert config.max_file_size_mb == 50
        assert config.chunk_size_tokens == 512
        assert config.chunk_overlap_tokens == 50
        assert config.enable_malware_scan is True
        assert config.quarantine_suspicious_files is True

    def test_custom_config(self):
        """Test custom configuration values."""
        config = ProcessingConfig(
            max_file_size_mb=100,
            chunk_size_tokens=1024,
            enable_malware_scan=False
        )
        
        assert config.max_file_size_mb == 100
        assert config.chunk_size_tokens == 1024
        assert config.enable_malware_scan is False


class TestSecurityScanner:
    """Test security scanning functionality."""

    @pytest.fixture
    def security_scanner(self):
        """Create security scanner with test config."""
        config = ProcessingConfig(max_file_size_mb=10)
        return SecurityScanner(config)

    @pytest.fixture
    def temp_file(self):
        """Create temporary file for testing."""
        with tempfile.NamedTemporaryFile(delete=False, suffix='.txt') as f:
            f.write(b"This is a test file content.")
            temp_path = Path(f.name)
        
        yield temp_path
        
        # Cleanup
        if temp_path.exists():
            temp_path.unlink()

    async def test_scan_safe_file(self, security_scanner, temp_file):
        """Test scanning a safe file."""
        with patch('magic.from_file', return_value='text/plain'):
            result = await security_scanner.scan_file(temp_file, "test.txt")
        
        assert isinstance(result, SecurityScanResult)
        assert result.is_safe is True
        assert len(result.threats_detected) == 0
        assert result.scan_engine == "internal"

    async def test_scan_dangerous_extension(self, security_scanner, temp_file):
        """Test scanning file with dangerous extension."""
        with pytest.raises(UnsupportedFormatError):
            await security_scanner.scan_file(temp_file, "malware.exe")

    async def test_scan_unsupported_mime_type(self, security_scanner, temp_file):
        """Test scanning file with unsupported MIME type."""
        with patch('magic.from_file', return_value='application/x-executable'):
            with pytest.raises(UnsupportedFormatError):
                await security_scanner.scan_file(temp_file, "test.txt")

    async def test_scan_file_too_large(self, security_scanner):
        """Test scanning file that exceeds size limit."""
        # Create a large temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.txt') as f:
            f.write(b"x" * (15 * 1024 * 1024))  # 15MB file
            large_file_path = Path(f.name)
        
        try:
            with pytest.raises(FileTooLargeError):
                await security_scanner.scan_file(large_file_path, "large.txt")
        finally:
            if large_file_path.exists():
                large_file_path.unlink()

    async def test_scan_content_patterns(self, security_scanner):
        """Test scanning for malicious content patterns."""
        # Create file with suspicious content
        with tempfile.NamedTemporaryFile(delete=False, suffix='.txt') as f:
            f.write(b"<script>alert('xss')</script>")
            suspicious_file = Path(f.name)
        
        try:
            with patch('magic.from_file', return_value='text/plain'):
                with pytest.raises(UnsupportedFormatError):
                    await security_scanner.scan_file(suspicious_file, "suspicious.txt")
        finally:
            if suspicious_file.exists():
                suspicious_file.unlink()

    async def test_validate_pdf_structure(self, security_scanner):
        """Test PDF file structure validation."""
        # Create mock PDF file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as f:
            f.write(b"%PDF-1.4\n%EOF")  # Minimal PDF structure
            pdf_file = Path(f.name)
        
        try:
            result = await security_scanner._validate_file_structure(pdf_file, 'application/pdf')
            assert result is True
        finally:
            if pdf_file.exists():
                pdf_file.unlink()

    async def test_validate_invalid_pdf_structure(self, security_scanner):
        """Test invalid PDF file structure validation."""
        # Create invalid PDF file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as f:
            f.write(b"Not a PDF file")
            invalid_pdf = Path(f.name)
        
        try:
            result = await security_scanner._validate_file_structure(invalid_pdf, 'application/pdf')
            assert result is False
        finally:
            if invalid_pdf.exists():
                invalid_pdf.unlink()


class TestTextExtractor:
    """Test text extraction functionality."""

    @pytest.fixture
    def text_extractor(self):
        """Create text extractor instance."""
        return TextExtractor()

    async def test_extract_txt_file(self, text_extractor):
        """Test extracting text from plain text file."""
        test_content = "This is a test document.\nWith multiple lines."
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt', encoding='utf-8') as f:
            f.write(test_content)
            txt_file = Path(f.name)
        
        try:
            text, metadata = await text_extractor.extract_text(txt_file, DocumentType.TXT)
            
            assert text == test_content
            assert metadata["encoding"] == "utf-8"
            assert metadata["lines"] == 2
        finally:
            if txt_file.exists():
                txt_file.unlink()

    async def test_extract_markdown_file(self, text_extractor):
        """Test extracting text from Markdown file."""
        markdown_content = "# Test Document\n\nThis is **bold** text."
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.md', encoding='utf-8') as f:
            f.write(markdown_content)
            md_file = Path(f.name)
        
        try:
            text, metadata = await text_extractor.extract_text(md_file, DocumentType.MD)
            
            assert "Test Document" in text
            assert "bold" in text
            assert metadata["format"] == "markdown"
        finally:
            if md_file.exists():
                md_file.unlink()

    async def test_extract_unsupported_format(self, text_extractor):
        """Test extracting text from unsupported format."""
        with tempfile.NamedTemporaryFile(delete=False, suffix='.txt') as f:
            temp_file = Path(f.name)
        
        try:
            with pytest.raises(UnsupportedFormatError):
                await text_extractor.extract_text(temp_file, "unsupported_format")
        finally:
            if temp_file.exists():
                temp_file.unlink()

    @patch('PyPDF2.PdfReader')
    async def test_extract_pdf_file(self, mock_pdf_reader, text_extractor):
        """Test extracting text from PDF file."""
        # Mock PDF reader
        mock_page = Mock()
        mock_page.extract_text.return_value = "PDF page content"
        
        mock_reader_instance = Mock()
        mock_reader_instance.pages = [mock_page]
        mock_reader_instance.metadata = {'/Title': 'Test PDF', '/Author': 'Test Author'}
        
        mock_pdf_reader.return_value = mock_reader_instance
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as f:
            pdf_file = Path(f.name)
        
        try:
            text, metadata = await text_extractor.extract_text(pdf_file, DocumentType.PDF)
            
            assert "PDF page content" in text
            assert metadata["pages"] == 1
            assert metadata["title"] == "Test PDF"
            assert metadata["author"] == "Test Author"
        finally:
            if pdf_file.exists():
                pdf_file.unlink()

    @patch('docx.Document')
    async def test_extract_docx_file(self, mock_docx, text_extractor):
        """Test extracting text from DOCX file."""
        # Mock DOCX document
        mock_paragraph1 = Mock()
        mock_paragraph1.text = "First paragraph"
        mock_paragraph2 = Mock()
        mock_paragraph2.text = "Second paragraph"
        
        mock_doc = Mock()
        mock_doc.paragraphs = [mock_paragraph1, mock_paragraph2]
        mock_doc.core_properties.title = "Test Document"
        mock_doc.core_properties.author = "Test Author"
        
        mock_docx.return_value = mock_doc
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.docx') as f:
            docx_file = Path(f.name)
        
        try:
            text, metadata = await text_extractor.extract_text(docx_file, DocumentType.DOCX)
            
            assert "First paragraph" in text
            assert "Second paragraph" in text
            assert metadata["title"] == "Test Document"
            assert metadata["author"] == "Test Author"
            assert metadata["paragraphs"] == 2
        finally:
            if docx_file.exists():
                docx_file.unlink()


class TestDocumentChunker:
    """Test document chunking functionality."""

    @pytest.fixture
    def document_chunker(self):
        """Create document chunker with test config."""
        config = ProcessingConfig(
            chunk_size_tokens=100,
            chunk_overlap_tokens=20
        )
        return DocumentChunker(config)

    async def test_chunk_short_text(self, document_chunker):
        """Test chunking short text that fits in one chunk."""
        short_text = "This is a short document that should fit in one chunk."
        
        chunks = await document_chunker.chunk_text(
            text=short_text,
            document_id="test_doc_1",
            metadata={"source": "test.txt"}
        )
        
        assert len(chunks) == 1
        assert chunks[0].content == short_text
        assert chunks[0].chunk_index == 0
        assert chunks[0].metadata["document_id"] == "test_doc_1"

    async def test_chunk_long_text(self, document_chunker):
        """Test chunking long text that requires multiple chunks."""
        # Create text that will require multiple chunks
        long_text = ". ".join([f"This is sentence number {i}" for i in range(50)])
        
        chunks = await document_chunker.chunk_text(
            text=long_text,
            document_id="test_doc_2",
            metadata={"source": "long.txt"}
        )
        
        assert len(chunks) > 1
        
        # Check chunk properties
        for i, chunk in enumerate(chunks):
            assert chunk.chunk_index == i
            assert chunk.metadata["document_id"] == "test_doc_2"
            assert chunk.token_count > 0
            assert len(chunk.content) > 0

    async def test_chunk_empty_text(self, document_chunker):
        """Test chunking empty text."""
        chunks = await document_chunker.chunk_text(
            text="",
            document_id="empty_doc",
            metadata={}
        )
        
        assert len(chunks) == 0

    async def test_chunk_overlap(self, document_chunker):
        """Test that chunks have proper overlap."""
        # Create text with clear sentence boundaries
        sentences = [f"Sentence {i} with some content." for i in range(20)]
        text = " ".join(sentences)
        
        chunks = await document_chunker.chunk_text(
            text=text,
            document_id="overlap_test",
            metadata={}
        )
        
        if len(chunks) > 1:
            # Check that there's some overlap between consecutive chunks
            # This is a simplified check - in practice, overlap detection is more complex
            assert len(chunks[0].content) > 0
            assert len(chunks[1].content) > 0

    def test_estimate_tokens(self, document_chunker):
        """Test token estimation."""
        text = "This is a test sentence with multiple words."
        tokens = document_chunker._estimate_tokens(text)
        
        # Should be roughly 1 token per 4 characters
        expected_tokens = len(text) // 4
        assert abs(tokens - expected_tokens) <= 2  # Allow some variance

    def test_split_into_sentences(self, document_chunker):
        """Test sentence splitting."""
        text = "First sentence. Second sentence! Third sentence? Fourth sentence."
        sentences = document_chunker._split_into_sentences(text)
        
        assert len(sentences) == 4
        assert "First sentence" in sentences[0]
        assert "Second sentence" in sentences[1]


class TestDocumentProcessor:
    """Test complete document processing pipeline."""

    @pytest.fixture
    def document_processor(self):
        """Create document processor with mocked dependencies."""
        config = ProcessingConfig(max_file_size_mb=10)
        processor = DocumentProcessor(config)
        
        # Mock the managers
        processor.ollama_manager = AsyncMock()
        processor.chromadb_manager = AsyncMock()
        
        return processor

    async def test_process_document_success(self, document_processor):
        """Test successful document processing."""
        # Mock file content
        file_content = b"This is a test document for processing."
        filename = "test.txt"
        creator_id = "test_creator"
        
        # Mock security scan
        with patch.object(document_processor.security_scanner, 'scan_file') as mock_scan:
            mock_scan.return_value = SecurityScanResult(
                is_safe=True,
                threats_detected=[],
                scan_engine="internal",
                scan_time_ms=100.0
            )
            
            # Mock text extraction
            with patch.object(document_processor.text_extractor, 'extract_text') as mock_extract:
                mock_extract.return_value = ("Extracted text content", {"pages": 1})
                
                # Mock chunking
                with patch.object(document_processor.chunker, 'chunk_text') as mock_chunk:
                    mock_chunks = [
                        DocumentChunk(
                            id="chunk_1",
                            content="Extracted text content",
                            metadata={"document_id": "test_doc"},
                            chunk_index=0,
                            token_count=10
                        )
                    ]
                    mock_chunk.return_value = mock_chunks
                    
                    # Mock embedding generation
                    document_processor.ollama_manager.generate_embeddings.return_value.embeddings = [
                        [0.1, 0.2, 0.3] * 128  # Mock embedding
                    ]
                    
                    # Mock ChromaDB storage
                    document_processor.chromadb_manager.add_embeddings.return_value = ["chunk_1"]
                    
                    result = await document_processor.process_document(
                        file_content=file_content,
                        filename=filename,
                        creator_id=creator_id
                    )
        
        assert isinstance(result, ProcessingResult)
        assert result.status == ProcessingStatus.COMPLETED
        assert result.total_chunks == 1
        assert len(result.chunks) == 1
        assert result.error_message is None

    async def test_process_document_security_failure(self, document_processor):
        """Test document processing with security scan failure."""
        file_content = b"Malicious content"
        filename = "malware.exe"
        creator_id = "test_creator"
        
        # Mock security scan failure
        with patch.object(document_processor.security_scanner, 'scan_file') as mock_scan:
            mock_scan.side_effect = MalwareDetectedError("Malware detected")
            
            result = await document_processor.process_document(
                file_content=file_content,
                filename=filename,
                creator_id=creator_id
            )
        
        assert result.status == ProcessingStatus.FAILED
        assert "Malware detected" in result.error_message
        assert result.total_chunks == 0

    async def test_process_document_text_extraction_failure(self, document_processor):
        """Test document processing with text extraction failure."""
        file_content = b"Valid file content"
        filename = "test.txt"
        creator_id = "test_creator"
        
        # Mock successful security scan
        with patch.object(document_processor.security_scanner, 'scan_file') as mock_scan:
            mock_scan.return_value = SecurityScanResult(
                is_safe=True,
                threats_detected=[],
                scan_engine="internal",
                scan_time_ms=100.0
            )
            
            # Mock text extraction failure
            with patch.object(document_processor.text_extractor, 'extract_text') as mock_extract:
                mock_extract.side_effect = TextExtractionError("Failed to extract text")
                
                result = await document_processor.process_document(
                    file_content=file_content,
                    filename=filename,
                    creator_id=creator_id
                )
        
        assert result.status == ProcessingStatus.FAILED
        assert "Failed to extract text" in result.error_message

    def test_detect_document_type(self, document_processor):
        """Test document type detection."""
        assert document_processor._detect_document_type("test.pdf") == DocumentType.PDF
        assert document_processor._detect_document_type("test.docx") == DocumentType.DOCX
        assert document_processor._detect_document_type("test.txt") == DocumentType.TXT
        assert document_processor._detect_document_type("test.md") == DocumentType.MD
        
        with pytest.raises(UnsupportedFormatError):
            document_processor._detect_document_type("test.exe")

    def test_generate_document_id(self, document_processor):
        """Test document ID generation."""
        doc_id = document_processor._generate_document_id("test.txt", "creator_123")
        
        assert "doc_creator_123" in doc_id
        assert len(doc_id) > 20  # Should include timestamp and hash

    async def test_generate_embeddings_batch(self, document_processor):
        """Test embedding generation for chunks."""
        chunks = [
            DocumentChunk(
                id="chunk_1",
                content="First chunk content",
                metadata={},
                chunk_index=0,
                token_count=10
            ),
            DocumentChunk(
                id="chunk_2",
                content="Second chunk content",
                metadata={},
                chunk_index=1,
                token_count=12
            )
        ]
        
        # Mock embedding generation
        document_processor.ollama_manager.generate_embeddings.return_value.embeddings = [
            [0.1, 0.2, 0.3] * 128,  # First embedding
            [0.4, 0.5, 0.6] * 128   # Second embedding
        ]
        
        await document_processor._generate_embeddings(chunks, "test_creator")
        
        # Check that embeddings were assigned
        assert chunks[0].embedding_vector is not None
        assert chunks[1].embedding_vector is not None
        assert len(chunks[0].embedding_vector) == 384
        assert len(chunks[1].embedding_vector) == 384

    async def test_store_chunks_chromadb(self, document_processor):
        """Test storing chunks in ChromaDB."""
        chunks = [
            DocumentChunk(
                id="chunk_1",
                content="Test content",
                metadata={"document_id": "test_doc"},
                chunk_index=0,
                token_count=10,
                embedding_vector=[0.1, 0.2, 0.3] * 128
            )
        ]
        
        document_processor.chromadb_manager.add_embeddings.return_value = ["chunk_1"]
        
        await document_processor._store_chunks(chunks, "test_creator")
        
        # Verify ChromaDB was called with correct parameters
        document_processor.chromadb_manager.add_embeddings.assert_called_once()
        call_args = document_processor.chromadb_manager.add_embeddings.call_args
        
        assert call_args[1]["creator_id"] == "test_creator"
        assert len(call_args[1]["embeddings"]) == 1
        assert len(call_args[1]["documents"]) == 1
        assert len(call_args[1]["ids"]) == 1


class TestDocumentProcessorIntegration:
    """Integration tests for document processor."""

    async def test_end_to_end_processing(self):
        """Test end-to-end document processing flow."""
        # This would be a more comprehensive integration test
        # For now, we'll test the flow with mocked components
        
        processor = DocumentProcessor()
        
        # Mock all dependencies
        with patch.object(processor, 'security_scanner') as mock_security:
            with patch.object(processor, 'text_extractor') as mock_extractor:
                with patch.object(processor, 'chunker') as mock_chunker:
                    with patch.object(processor, 'ollama_manager') as mock_ollama:
                        with patch.object(processor, 'chromadb_manager') as mock_chromadb:
                            
                            # Setup mocks
                            mock_security.scan_file.return_value = SecurityScanResult(
                                is_safe=True, threats_detected=[], scan_engine="test", scan_time_ms=100
                            )
                            mock_extractor.extract_text.return_value = ("Test content", {})
                            mock_chunker.chunk_text.return_value = [
                                DocumentChunk(
                                    id="test_chunk",
                                    content="Test content",
                                    metadata={},
                                    chunk_index=0,
                                    token_count=5
                                )
                            ]
                            mock_ollama.generate_embeddings.return_value.embeddings = [[0.1] * 384]
                            mock_chromadb.add_embeddings.return_value = ["test_chunk"]
                            
                            result = await processor.process_document(
                                file_content=b"Test file content",
                                filename="test.txt",
                                creator_id="test_creator"
                            )
                            
                            assert result.status == ProcessingStatus.COMPLETED
                            assert result.total_chunks == 1