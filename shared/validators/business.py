"""Business logic validators"""

import uuid


def validate_creator_id(creator_id: str) -> bool:
    """Validate creator ID format"""
    if not creator_id or not creator_id.strip():
        return False
    
    # Check if it's a valid UUID format
    try:
        uuid.UUID(creator_id)
        return True
    except ValueError:
        # Allow other formats but ensure it's not empty and reasonable length
        return len(creator_id.strip()) >= 3 and len(creator_id.strip()) <= 50


def validate_session_id(session_id: str) -> bool:
    """Validate session ID format"""
    if not session_id or not session_id.strip():
        return False
    
    # Check if it's a valid UUID format
    try:
        uuid.UUID(session_id)
        return True
    except ValueError:
        # Allow other formats but ensure it's not empty and reasonable length
        return len(session_id.strip()) >= 10 and len(session_id.strip()) <= 100


def validate_document_id(document_id: str) -> bool:
    """Validate document ID format"""
    if not document_id or not document_id.strip():
        return False
    
    # Similar to creator_id validation
    try:
        uuid.UUID(document_id)
        return True
    except ValueError:
        return len(document_id.strip()) >= 3 and len(document_id.strip()) <= 50