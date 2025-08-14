"""
Integration test to verify fixture fixes work correctly.
"""

import pytest
import pytest_asyncio


@pytest.mark.usefixtures("cleanup_test_data")
class TestFixtureIntegration:
    """Test that all fixtures work correctly after fixes."""
    
    def test_common_db_session_available(self, common_db_session):
        """Test that common_db_session fixture is available."""
        assert common_db_session is not None
    
    def test_test_client_factory(self, test_client_factory):
        """Test that test client factory works."""
        assert test_client_factory is not None
        assert callable(test_client_factory)
    
    @pytest_asyncio.fixture
    async def async_client_factory_test(self, async_client_factory):
        """Test that async client factory works."""
        assert async_client_factory is not None
        assert callable(async_client_factory)
    
    def test_common_test_data(self, common_test_user_data, common_auth_headers):
        """Test that common test data fixtures work."""
        assert common_test_user_data is not None
        assert "email" in common_test_user_data
        assert common_auth_headers is not None
        assert "Authorization" in common_auth_headers
    
    @pytest_asyncio.fixture
    async def service_clients_test(self, service_clients):
        """Test that service clients fixture works."""
        assert service_clients is not None
        assert "auth" in service_clients
        assert "creator_hub" in service_clients
        assert "ai_engine" in service_clients
        assert "channel" in service_clients


class TestAuthFixtures:
    """Test auth-specific fixtures."""
    
    def test_test_user_data(self, test_user_data):
        """Test that test user data is available."""
        assert test_user_data is not None
        assert "email" in test_user_data
        assert "password" in test_user_data
    
    def test_password_security_fixture(self, password_security):
        """Test password security fixture."""
        # This will skip if PasswordSecurity is not available
        assert password_security is not None


class TestMockFixtures:
    """Test mock fixtures work correctly."""
    
    def test_mock_ollama_manager(self, mock_ollama_manager):
        """Test mock Ollama manager."""
        assert mock_ollama_manager is not None
        assert hasattr(mock_ollama_manager, 'generate_embedding')
        assert hasattr(mock_ollama_manager, 'chat_completion')
    
    def test_mock_chromadb_manager(self, mock_chromadb_manager):
        """Test mock ChromaDB manager."""
        assert mock_chromadb_manager is not None
        assert hasattr(mock_chromadb_manager, 'create_collection')
        assert hasattr(mock_chromadb_manager, 'add_documents')
    
    def test_mock_connection_manager(self, mock_connection_manager):
        """Test mock connection manager."""
        assert mock_connection_manager is not None
        assert hasattr(mock_connection_manager, 'connect')
        assert hasattr(mock_connection_manager, 'disconnect')