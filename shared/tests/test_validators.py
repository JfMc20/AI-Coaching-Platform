"""
Tests for shared validators
"""

import pytest
from shared.validators.common import validate_email, validate_url, validate_domain, validate_hex_color
from shared.validators.business import validate_creator_id, validate_session_id, validate_document_id


class TestCommonValidators:
    """Test common validation functions"""
    
    def test_validate_email(self):
        """Test email validation"""
        # Valid emails
        assert validate_email("test@example.com") is True
        assert validate_email("user.name@domain.co.uk") is True
        assert validate_email("user+tag@example.org") is True
        
        # Invalid emails
        assert validate_email("invalid-email") is False
        assert validate_email("@example.com") is False
        assert validate_email("test@") is False
        assert validate_email("test.example.com") is False
    
    def test_validate_url(self):
        """Test URL validation"""
        # Valid URLs
        assert validate_url("https://example.com") is True
        assert validate_url("http://localhost:8000") is True
        assert validate_url("https://subdomain.example.com/path") is True
        
        # Invalid URLs
        assert validate_url("not-a-url") is False
        assert validate_url("ftp://example.com") is True  # FTP is valid URL
        assert validate_url("") is False
    
    def test_validate_domain(self):
        """Test domain validation"""
        # Valid domains
        assert validate_domain("example.com") is True
        assert validate_domain("subdomain.example.com") is True
        assert validate_domain("localhost") is True
        
        # Invalid domains
        assert validate_domain("") is False
        assert validate_domain(".example.com") is False
        assert validate_domain("example.com.") is False
        assert validate_domain("ex ample.com") is False
    
    def test_validate_hex_color(self):
        """Test hex color validation"""
        # Valid hex colors
        assert validate_hex_color("#000000") is True
        assert validate_hex_color("#ffffff") is True
        assert validate_hex_color("#007bff") is True
        assert validate_hex_color("#ABC123") is True
        
        # Invalid hex colors
        assert validate_hex_color("000000") is False  # Missing #
        assert validate_hex_color("#00000") is False  # Too short
        assert validate_hex_color("#0000000") is False  # Too long
        assert validate_hex_color("#GGGGGG") is False  # Invalid hex chars


class TestBusinessValidators:
    """Test business logic validators"""
    
    def test_validate_creator_id(self):
        """Test creator ID validation"""
        # Valid creator IDs
        assert validate_creator_id("creator_123") is True
        assert validate_creator_id("550e8400-e29b-41d4-a716-446655440000") is True  # UUID
        assert validate_creator_id("abc123def456") is True
        
        # Invalid creator IDs
        assert validate_creator_id("") is False
        assert validate_creator_id("  ") is False
        assert validate_creator_id("ab") is False  # Too short
        assert validate_creator_id("a" * 51) is False  # Too long
    
    def test_validate_session_id(self):
        """Test session ID validation"""
        # Valid session IDs
        assert validate_session_id("session_123456789") is True
        assert validate_session_id("550e8400-e29b-41d4-a716-446655440000") is True  # UUID
        
        # Invalid session IDs
        assert validate_session_id("") is False
        assert validate_session_id("  ") is False
        assert validate_session_id("short") is False  # Too short
        assert validate_session_id("a" * 101) is False  # Too long
    
    def test_validate_document_id(self):
        """Test document ID validation"""
        # Valid document IDs
        assert validate_document_id("doc_123") is True
        assert validate_document_id("550e8400-e29b-41d4-a716-446655440000") is True  # UUID
        assert validate_document_id("abc123def456") is True
        
        # Invalid document IDs
        assert validate_document_id("") is False
        assert validate_document_id("  ") is False
        assert validate_document_id("ab") is False  # Too short
        assert validate_document_id("a" * 51) is False  # Too long