"""Common utility functions"""

import uuid
import hashlib
import secrets
from typing import Optional


def generate_correlation_id() -> str:
    """Generate a unique correlation ID for request tracking"""
    return str(uuid.uuid4())


def generate_secure_token(length: int = 32) -> str:
    """Generate a cryptographically secure random token"""
    return secrets.token_urlsafe(length)


def generate_document_id(file_path: str, creator_id: str) -> str:
    """Generate a deterministic document ID based on file path and creator"""
    content = f"{creator_id}:{file_path}:{secrets.token_hex(8)}"
    return hashlib.sha256(content.encode()).hexdigest()[:16]


def sanitize_filename(filename: str) -> str:
    """Sanitize filename for safe storage"""
    # Remove or replace dangerous characters
    import re
    # Keep only alphanumeric, dots, hyphens, and underscores
    sanitized = re.sub(r'[^a-zA-Z0-9._-]', '_', filename)
    # Limit length
    if len(sanitized) > 100:
        name, ext = sanitized.rsplit('.', 1) if '.' in sanitized else (sanitized, '')
        sanitized = name[:95] + ('.' + ext if ext else '')
    return sanitized