"""
Tests for shared models
"""

import pytest
from datetime import datetime
from pydantic import ValidationError

from shared.models.auth import CreatorCreate, CreatorResponse, TokenResponse, UserSession
from shared.models.documents import ProcessingResult, DocumentChunk, ProcessingStatus
from shared.models.widgets import WidgetConfig, WidgetTheme, WidgetBehavior
from shared.models.conversations import Message, Conversation, MessageRole


class TestAuthModels:
    """Test authentication models"""
    
    def test_creator_create_valid(self):
        """Test valid creator creation"""
        creator = CreatorCreate(
            email="test@example.com",
            password="SecurePass123",
            full_name="Test Creator",
            company_name="Test Company"
        )
        
        assert creator.email == "test@example.com"
        assert creator.password == "SecurePass123"
        assert creator.full_name == "Test Creator"
        assert creator.company_name == "Test Company"
    
    def test_creator_create_password_validation(self):
        """Test password validation"""
        # Test weak password
        with pytest.raises(ValidationError) as exc_info:
            CreatorCreate(
                email="test@example.com",
                password="weak",
                full_name="Test Creator"
            )
        
        assert "Password must be at least 8 characters" in str(exc_info.value)
        
        # Test password without uppercase
        with pytest.raises(ValidationError) as exc_info:
            CreatorCreate(
                email="test@example.com",
                password="lowercase123",
                full_name="Test Creator"
            )
        
        assert "uppercase letter" in str(exc_info.value)
    
    def test_token_response(self):
        """Test token response model"""
        token = TokenResponse(
            access_token="access_token_here",
            refresh_token="refresh_token_here",
            expires_in=3600
        )
        
        assert token.access_token == "access_token_here"
        assert token.refresh_token == "refresh_token_here"
        assert token.token_type == "bearer"
        assert token.expires_in == 3600
    
    def test_user_session(self):
        """Test user session model"""
        session = UserSession(
            session_id="session_123",
            creator_id="creator_456",
            channel="web_widget",
            metadata={"ip": "127.0.0.1"}
        )
        
        assert session.session_id == "session_123"
        assert session.creator_id == "creator_456"
        assert session.channel == "web_widget"
        assert session.metadata["ip"] == "127.0.0.1"


class TestDocumentModels:
    """Test document processing models"""
    
    def test_document_chunk(self):
        """Test document chunk model"""
        chunk = DocumentChunk(
            id="chunk_123",
            content="This is a test chunk",
            chunk_index=0,
            token_count=5,
            metadata={"page": 1}
        )
        
        assert chunk.id == "chunk_123"
        assert chunk.content == "This is a test chunk"
        assert chunk.chunk_index == 0
        assert chunk.token_count == 5
        assert chunk.metadata["page"] == 1
    
    def test_document_chunk_empty_content(self):
        """Test document chunk with empty content"""
        with pytest.raises(ValidationError) as exc_info:
            DocumentChunk(
                id="chunk_123",
                content="",
                chunk_index=0,
                token_count=0
            )
        
        assert "cannot be empty" in str(exc_info.value)
    
    def test_processing_result(self):
        """Test processing result model"""
        chunks = [
            DocumentChunk(
                id="chunk_1",
                content="First chunk",
                chunk_index=0,
                token_count=2
            ),
            DocumentChunk(
                id="chunk_2", 
                content="Second chunk",
                chunk_index=1,
                token_count=2
            )
        ]
        
        result = ProcessingResult(
            document_id="doc_123",
            creator_id="creator_456",
            status=ProcessingStatus.COMPLETED,
            chunks=chunks,
            total_chunks=2,
            processing_time_seconds=1.5
        )
        
        assert result.document_id == "doc_123"
        assert result.creator_id == "creator_456"
        assert result.status == ProcessingStatus.COMPLETED
        assert len(result.chunks) == 2
        assert result.total_chunks == 2
        assert result.processing_time_seconds == 1.5


class TestWidgetModels:
    """Test widget configuration models"""
    
    def test_widget_theme(self):
        """Test widget theme model"""
        theme = WidgetTheme(
            primary_color="#007bff",
            secondary_color="#6c757d",
            background_color="#ffffff",
            text_color="#212529",
            border_radius=8
        )
        
        assert theme.primary_color == "#007bff"
        assert theme.secondary_color == "#6c757d"
        assert theme.background_color == "#ffffff"
        assert theme.text_color == "#212529"
        assert theme.border_radius == 8
    
    def test_widget_theme_invalid_color(self):
        """Test widget theme with invalid color"""
        with pytest.raises(ValidationError) as exc_info:
            WidgetTheme(primary_color="invalid_color")
        
        assert "valid hex color" in str(exc_info.value)
    
    def test_widget_behavior(self):
        """Test widget behavior model"""
        behavior = WidgetBehavior(
            auto_open=True,
            greeting_message="Hello!",
            placeholder_text="Type here...",
            show_typing_indicator=True,
            response_delay_ms=1000
        )
        
        assert behavior.auto_open is True
        assert behavior.greeting_message == "Hello!"
        assert behavior.placeholder_text == "Type here..."
        assert behavior.show_typing_indicator is True
        assert behavior.response_delay_ms == 1000
    
    def test_widget_config(self):
        """Test complete widget configuration"""
        config = WidgetConfig(
            creator_id="creator_123",
            widget_id="widget_456",
            is_active=True,
            allowed_domains=["example.com", "test.com"],
            rate_limit_per_minute=10
        )
        
        assert config.creator_id == "creator_123"
        assert config.widget_id == "widget_456"
        assert config.is_active is True
        assert config.allowed_domains == ["example.com", "test.com"]
        assert config.rate_limit_per_minute == 10


class TestConversationModels:
    """Test conversation models"""
    
    def test_message(self):
        """Test message model"""
        message = Message(
            creator_id="creator_123",
            conversation_id="conv_456",
            role=MessageRole.USER,
            content="Hello, how are you?",
            processing_time_ms=100
        )
        
        assert message.creator_id == "creator_123"
        assert message.conversation_id == "conv_456"
        assert message.role == MessageRole.USER
        assert message.content == "Hello, how are you?"
        assert message.processing_time_ms == 100
    
    def test_message_empty_content(self):
        """Test message with empty content"""
        with pytest.raises(ValidationError) as exc_info:
            Message(
                creator_id="creator_123",
                conversation_id="conv_456",
                role=MessageRole.USER,
                content=""
            )
        
        assert "cannot be empty" in str(exc_info.value)
    
    def test_conversation(self):
        """Test conversation model"""
        conversation = Conversation(
            creator_id="creator_123",
            session_id="session_456",
            title="Test Conversation",
            channel="web_widget",
            is_active=True,
            message_count=5
        )
        
        assert conversation.creator_id == "creator_123"
        assert conversation.session_id == "session_456"
        assert conversation.title == "Test Conversation"
        assert conversation.channel == "web_widget"
        assert conversation.is_active is True
        assert conversation.message_count == 5