"""
Tests for shared utilities
"""

import pytest
from shared.utils.helpers import (
    generate_correlation_id, 
    generate_secure_token,
    generate_document_id,
    sanitize_filename
)
from shared.security.password_security import hash_password, verify_password
from shared.utils.serializers import CustomJSONEncoder
import json
from datetime import datetime
from decimal import Decimal
from uuid import UUID
from enum import Enum


class TestHelpers:
    """Test helper functions"""
    
    def test_generate_correlation_id(self):
        """Test correlation ID generation"""
        id1 = generate_correlation_id()
        id2 = generate_correlation_id()
        
        # Should be different
        assert id1 != id2
        
        # Should be valid UUID format
        UUID(id1)  # Will raise ValueError if invalid
        UUID(id2)
    
    def test_generate_secure_token(self):
        """Test secure token generation"""
        token1 = generate_secure_token()
        token2 = generate_secure_token()
        
        # Should be different
        assert token1 != token2
        
        # Should have reasonable length
        assert len(token1) > 20
        assert len(token2) > 20
        
        # Test custom length
        short_token = generate_secure_token(16)
        assert len(short_token) > 10  # URL-safe encoding may vary length
    
    def test_password_hashing(self):
        """Test password hashing and verification using secure Argon2id implementation"""
        password = "SecurePassword123"
        
        # Hash password using Argon2id (default)
        hashed = hash_password(password, use_argon2=True)
        
        # Should not be the same as original
        assert hashed != password
        
        # Should start with Argon2id prefix
        assert hashed.startswith("$argon2id$")
        
        # Should verify correctly
        assert verify_password(password, hashed) is True
        
        # Should not verify wrong password
        assert verify_password("WrongPassword", hashed) is False
        
        # Test bcrypt fallback compatibility
        bcrypt_hash = hash_password(password, use_argon2=False)
        assert bcrypt_hash.startswith("$2b$")
        assert verify_password(password, bcrypt_hash) is True
    
    def test_generate_document_id(self):
        """Test document ID generation"""
        file_path = "/path/to/document.pdf"
        creator_id = "creator_123"
        
        doc_id1 = generate_document_id(file_path, creator_id)
        doc_id2 = generate_document_id(file_path, creator_id)
        
        # Should be different (includes random component)
        assert doc_id1 != doc_id2
        
        # Should have consistent length
        assert len(doc_id1) == 16
        assert len(doc_id2) == 16
    
    def test_sanitize_filename(self):
        """Test filename sanitization"""
        # Test normal filename
        assert sanitize_filename("document.pdf") == "document.pdf"
        
        # Test filename with spaces and special chars
        assert sanitize_filename("my document (1).pdf") == "my_document__1_.pdf"
        
        # Test filename with dangerous chars
        assert sanitize_filename("../../../etc/passwd") == ".._.._.._.._etc_passwd"
        
        # Test very long filename
        long_name = "a" * 200 + ".pdf"
        sanitized = sanitize_filename(long_name)
        assert len(sanitized) <= 100
        assert sanitized.endswith(".pdf")


class TestCustomJSONEncoder:
    """Test custom JSON encoder"""
    
    def test_datetime_encoding(self):
        """Test datetime encoding"""
        dt = datetime(2024, 1, 1, 12, 0, 0)
        encoded = json.dumps(dt, cls=CustomJSONEncoder)
        
        assert "2024-01-01T12:00:00" in encoded
    
    def test_decimal_encoding(self):
        """Test decimal encoding"""
        decimal_val = Decimal("123.45")
        encoded = json.dumps(decimal_val, cls=CustomJSONEncoder)
        
        assert "123.45" in encoded
    
    def test_uuid_encoding(self):
        """Test UUID encoding"""
        uuid_val = UUID("550e8400-e29b-41d4-a716-446655440000")
        encoded = json.dumps(uuid_val, cls=CustomJSONEncoder)
        
        assert "550e8400-e29b-41d4-a716-446655440000" in encoded
    
    def test_enum_encoding(self):
        """Test enum encoding"""
        class TestEnum(Enum):
            VALUE1 = "value1"
            VALUE2 = "value2"
        
        encoded = json.dumps(TestEnum.VALUE1, cls=CustomJSONEncoder)
        assert "value1" in encoded
    
    def test_complex_object_encoding(self):
        """Test encoding complex object with multiple types"""
        complex_obj = {
            "datetime": datetime(2024, 1, 1),
            "decimal": Decimal("99.99"),
            "uuid": UUID("550e8400-e29b-41d4-a716-446655440000"),
            "string": "test"
        }
        
        encoded = json.dumps(complex_obj, cls=CustomJSONEncoder)
        decoded = json.loads(encoded)
        
        assert "2024-01-01T00:00:00" in decoded["datetime"]
        assert decoded["decimal"] == 99.99
        assert decoded["uuid"] == "550e8400-e29b-41d4-a716-446655440000"
        assert decoded["string"] == "test"