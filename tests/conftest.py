"""
Global pytest configuration and fixtures for the AI coaching platform.
"""

import os
import sys
import pytest
import asyncio
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Set test environment variables before importing any modules
os.environ.setdefault("ENVIRONMENT", "test")
os.environ.setdefault("DEBUG", "true")
os.environ.setdefault("LOG_LEVEL", "INFO")
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///./test.db")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/1")
os.environ.setdefault("CORS_ORIGINS", "http://localhost:3000,http://localhost:8080")
os.environ.setdefault("ALLOWED_HOSTS", "localhost,127.0.0.1")
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-for-testing-only")
os.environ.setdefault("JWT_ALGORITHM", "HS256")
os.environ.setdefault("OLLAMA_URL", "http://localhost:11434")
os.environ.setdefault("CHROMADB_URL", "http://localhost:8000")
os.environ.setdefault("EMBEDDING_MODEL", "nomic-embed-text")
os.environ.setdefault("CHAT_MODEL", "llama3.2")
os.environ.setdefault("CHROMA_SHARD_COUNT", "5")
os.environ.setdefault("VAULT_ENABLED", "false")

# Load test environment file if it exists
test_env_file = project_root / ".env.test"
if test_env_file.exists():
    from dotenv import load_dotenv
    load_dotenv(test_env_file)


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(autouse=True)
def setup_test_environment():
    """Automatically set up test environment for all tests."""
    # Ensure we're in test mode
    os.environ["ENVIRONMENT"] = "test"
    
    # Create test directories if they don't exist
    test_uploads_dir = project_root / "test_uploads"
    test_uploads_dir.mkdir(exist_ok=True)
    
    yield
    
    # Cleanup after tests
    # Remove test files if needed
    pass


@pytest.fixture
def mock_redis():
    """Mock Redis client for testing."""
    from unittest.mock import AsyncMock, Mock
    
    mock_redis = AsyncMock()
    mock_redis.get = AsyncMock(return_value=None)
    mock_redis.set = AsyncMock(return_value=True)
    mock_redis.delete = AsyncMock(return_value=True)
    mock_redis.exists = AsyncMock(return_value=False)
    mock_redis.expire = AsyncMock(return_value=True)
    mock_redis.ping = AsyncMock(return_value=True)
    
    return mock_redis


@pytest.fixture
def mock_database():
    """Mock database session for testing."""
    from unittest.mock import AsyncMock, Mock
    
    mock_session = AsyncMock()
    mock_session.execute = AsyncMock()
    mock_session.commit = AsyncMock()
    mock_session.rollback = AsyncMock()
    mock_session.close = AsyncMock()
    
    return mock_session


@pytest.fixture
def sample_text_content():
    """Sample text content for testing document processing."""
    return """
    This is a sample document for testing purposes.
    It contains multiple paragraphs and sentences.
    
    The document discusses various topics including:
    - Natural language processing
    - Machine learning algorithms
    - Data preprocessing techniques
    
    This content will be used to test chunking, embedding generation,
    and other document processing functionalities.
    """


@pytest.fixture
def sample_pdf_content():
    """Sample PDF content (as bytes) for testing file uploads."""
    # This is a minimal PDF content for testing
    return b"""%PDF-1.4
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj
2 0 obj
<<
/Type /Pages
/Kids [3 0 R]
/Count 1
>>
endobj
3 0 obj
<<
/Type /Page
/Parent 2 0 R
/MediaBox [0 0 612 792]
/Contents 4 0 R
>>
endobj
4 0 obj
<<
/Length 44
>>
stream
BT
/F1 12 Tf
72 720 Td
(Test PDF content) Tj
ET
endstream
endobj
xref
0 5
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000206 00000 n 
trailer
<<
/Size 5
/Root 1 0 R
>>
startxref
299
%%EOF"""


@pytest.fixture
def test_creator_id():
    """Standard test creator ID."""
    return "test_creator_123"


@pytest.fixture
def test_conversation_id():
    """Standard test conversation ID."""
    return "test_conversation_456"


@pytest.fixture
def test_document_id():
    """Standard test document ID."""
    return "test_document_789"