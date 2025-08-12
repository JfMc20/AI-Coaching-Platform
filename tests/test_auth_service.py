"""
Tests for authentication service
Validates creator registration, login, token management, and security features
"""

import pytest
import uuid
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession

from shared.models.auth import CreatorCreate, LoginRequest, TokenRefreshRequest
from shared.models.database import Creator, RefreshToken
from services.auth_service.app.services.auth_service import AuthService


@pytest.fixture
def auth_service():
    """Create auth service instance for testing"""
    with patch.dict('os.environ', {
        'JWT_SECRET_KEY': 'test-secret-key-for-testing-only',
        'JWT_ALGORITHM': 'HS256',  # Use HS256 for testing simplicity
        'JWT_ACCESS_TOKEN_EXPIRE_MINUTES': '60',
        'JWT_REFRESH_TOKEN_EXPIRE_DAYS': '30'
    }):
        return AuthService()


@pytest.fixture
def mock_db():
    """Create mock database session"""
    return AsyncMock(spec=AsyncSession)


@pytest.fixture
def sample_creator_data():
    """Sample creator registration data"""
    return CreatorCreate(
        email="test@example.com",
        password="SecureP@ssw0rd123!",
        full_name="Test Creator",
        company_name="Test Company"
    )


@pytest.fixture
def sample_login_data():
    """Sample login data"""
    return LoginRequest(
        email="test@example.com",
        password="SecureP@ssw0rd123!",
        remember_me=False
    )


class TestAuthServiceRegistration:
    """Test creator registration functionality"""
    
    @pytest.mark.asyncio
    async def test_successful_registration(self, auth_service, mock_db, sample_creator_data):
        """Test successful creator registration"""
        # Mock database responses
        mock_db.execute.return_value.scalar_one_or_none.return_value = None  # No existing creator
        mock_db.flush = AsyncMock()
        mock_db.commit = AsyncMock()
        
        # Mock creator object after creation
        mock_creator = MagicMock()
        mock_creator.id = uuid.uuid4()
        mock_creator.email = sample_creator_data.email
        mock_creator.full_name = sample_creator_data.full_name
        mock_creator.company_name = sample_creator_data.company_name
        mock_creator.is_active = True
        mock_creator.subscription_tier = "free"
        mock_creator.created_at = datetime.utcnow()
        mock_creator.updated_at = datetime.utcnow()
        
        # Mock the add method to set the creator
        def mock_add(obj):
            if isinstance(obj, Creator):
                obj.id = mock_creator.id
                obj.created_at = mock_creator.created_at
                obj.updated_at = mock_creator.updated_at
        
        mock_db.add.side_effect = mock_add
        
        # Test registration
        creator_response, token_response = await auth_service.register_creator(
            creator_data=sample_creator_data,
            db=mock_db,
            client_ip="127.0.0.1",
            user_agent="test-agent"
        )
        
        # Verify results
        assert creator_response.email == sample_creator_data.email
        assert creator_response.full_name == sample_creator_data.full_name
        assert creator_response.is_active is True
        assert creator_response.subscription_tier == "free"
        
        assert token_response.access_token is not None
        assert token_response.refresh_token is not None
        assert token_response.token_type == "bearer"
        assert token_response.expires_in > 0
        
        # Verify database interactions
        mock_db.add.assert_called()
        mock_db.flush.assert_called_once()
        mock_db.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_registration_duplicate_email(self, auth_service, mock_db, sample_creator_data):
        """Test registration with duplicate email"""
        # Mock existing creator
        existing_creator = MagicMock()
        existing_creator.email = sample_creator_data.email
        mock_db.execute.return_value.scalar_one_or_none.return_value = existing_creator
        
        # Test registration should fail
        with pytest.raises(Exception) as exc_info:
            await auth_service.register_creator(
                creator_data=sample_creator_data,
                db=mock_db
            )
        
        # Should rollback on error
        mock_db.rollback.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('shared.security.validate_password_strength')
    async def test_registration_weak_password(self, mock_validate, auth_service, mock_db, sample_creator_data):
        """Test registration with weak password"""
        # Mock no existing creator
        mock_db.execute.return_value.scalar_one_or_none.return_value = None
        
        # Mock weak password validation
        mock_result = MagicMock()
        mock_result.is_valid = False
        mock_result.violations = ["Password is too weak"]
        mock_result.suggestions = ["Add more complexity"]
        mock_validate.return_value = mock_result
        
        # Test registration should fail
        with pytest.raises(Exception) as exc_info:
            await auth_service.register_creator(
                creator_data=sample_creator_data,
                db=mock_db
            )
        
        # Should rollback on error
        mock_db.rollback.assert_called_once()


class TestAuthServiceLogin:
    """Test creator authentication functionality"""
    
    @pytest.mark.asyncio
    async def test_successful_login(self, auth_service, mock_db, sample_login_data):
        """Test successful creator login"""
        # Mock creator in database
        mock_creator = MagicMock()
        mock_creator.id = uuid.uuid4()
        mock_creator.email = sample_login_data.email
        mock_creator.full_name = "Test Creator"
        mock_creator.company_name = "Test Company"
        mock_creator.is_active = True
        mock_creator.subscription_tier = "free"
        mock_creator.locked_until = None
        mock_creator.failed_login_attempts = 0
        mock_creator.password_hash = "$argon2id$v=19$m=65536,t=3,p=4$test"
        mock_creator.created_at = datetime.utcnow()
        mock_creator.updated_at = datetime.utcnow()
        
        mock_db.execute.return_value.scalar_one_or_none.return_value = mock_creator
        mock_db.commit = AsyncMock()
        
        # Mock password verification
        with patch.object(auth_service.password_hasher, 'verify_password', return_value=True):
            with patch.object(auth_service.password_hasher, 'needs_rehash', return_value=False):
                # Test login
                creator_response, token_response = await auth_service.authenticate_creator(
                    login_data=sample_login_data,
                    db=mock_db,
                    client_ip="127.0.0.1",
                    user_agent="test-agent"
                )
        
        # Verify results
        assert creator_response.email == sample_login_data.email
        assert creator_response.is_active is True
        
        assert token_response.access_token is not None
        assert token_response.refresh_token is not None
        assert token_response.token_type == "bearer"
        
        # Verify database interactions
        mock_db.commit.assert_called_once()
        
        # Verify failed attempts reset
        assert mock_creator.failed_login_attempts == 0
        assert mock_creator.locked_until is None
    
    @pytest.mark.asyncio
    async def test_login_invalid_email(self, auth_service, mock_db, sample_login_data):
        """Test login with non-existent email"""
        # Mock no creator found
        mock_db.execute.return_value.scalar_one_or_none.return_value = None
        
        # Test login should fail
        with pytest.raises(Exception) as exc_info:
            await auth_service.authenticate_creator(
                login_data=sample_login_data,
                db=mock_db
            )
    
    @pytest.mark.asyncio
    async def test_login_invalid_password(self, auth_service, mock_db, sample_login_data):
        """Test login with invalid password"""
        # Mock creator in database
        mock_creator = MagicMock()
        mock_creator.id = uuid.uuid4()
        mock_creator.email = sample_login_data.email
        mock_creator.is_active = True
        mock_creator.locked_until = None
        mock_creator.failed_login_attempts = 0
        mock_creator.password_hash = "$argon2id$v=19$m=65536,t=3,p=4$test"
        
        mock_db.execute.return_value.scalar_one_or_none.return_value = mock_creator
        mock_db.commit = AsyncMock()
        
        # Mock password verification failure
        with patch.object(auth_service.password_hasher, 'verify_password', return_value=False):
            # Test login should fail
            with pytest.raises(Exception) as exc_info:
                await auth_service.authenticate_creator(
                    login_data=sample_login_data,
                    db=mock_db
                )
        
        # Verify failed attempts incremented
        assert mock_creator.failed_login_attempts == 1
        mock_db.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_login_account_locked(self, auth_service, mock_db, sample_login_data):
        """Test login with locked account"""
        # Mock locked creator
        mock_creator = MagicMock()
        mock_creator.id = uuid.uuid4()
        mock_creator.email = sample_login_data.email
        mock_creator.is_active = True
        mock_creator.locked_until = datetime.utcnow() + timedelta(minutes=30)
        mock_creator.failed_login_attempts = 5
        
        mock_db.execute.return_value.scalar_one_or_none.return_value = mock_creator
        
        # Test login should fail
        with pytest.raises(Exception) as exc_info:
            await auth_service.authenticate_creator(
                login_data=sample_login_data,
                db=mock_db
            )
    
    @pytest.mark.asyncio
    async def test_login_inactive_account(self, auth_service, mock_db, sample_login_data):
        """Test login with inactive account"""
        # Mock inactive creator
        mock_creator = MagicMock()
        mock_creator.id = uuid.uuid4()
        mock_creator.email = sample_login_data.email
        mock_creator.is_active = False
        mock_creator.locked_until = None
        
        mock_db.execute.return_value.scalar_one_or_none.return_value = mock_creator
        
        # Test login should fail
        with pytest.raises(Exception) as exc_info:
            await auth_service.authenticate_creator(
                login_data=sample_login_data,
                db=mock_db
            )


class TestAuthServiceTokenRefresh:
    """Test token refresh functionality"""
    
    @pytest.mark.asyncio
    async def test_successful_token_refresh(self, auth_service, mock_db):
        """Test successful token refresh"""
        # Mock refresh token and creator
        mock_refresh_token = MagicMock()
        mock_refresh_token.id = uuid.uuid4()
        mock_refresh_token.family_id = uuid.uuid4()
        mock_refresh_token.creator_id = uuid.uuid4()
        mock_refresh_token.used_at = None
        mock_refresh_token.revoked_at = None
        mock_refresh_token.is_active = True
        mock_refresh_token.expires_at = datetime.utcnow() + timedelta(days=30)
        
        mock_creator = MagicMock()
        mock_creator.id = mock_refresh_token.creator_id
        mock_creator.email = "test@example.com"
        mock_creator.is_active = True
        
        # Mock database response
        mock_db.execute.return_value.first.return_value = (mock_refresh_token, mock_creator)
        mock_db.commit = AsyncMock()
        
        # Test token refresh
        refresh_request = TokenRefreshRequest(refresh_token="test-refresh-token")
        
        token_response = await auth_service.refresh_token(
            refresh_request=refresh_request,
            db=mock_db,
            client_ip="127.0.0.1",
            user_agent="test-agent"
        )
        
        # Verify results
        assert token_response.access_token is not None
        assert token_response.refresh_token is not None
        assert token_response.token_type == "bearer"
        
        # Verify old token marked as used
        assert mock_refresh_token.used_at is not None
        assert mock_refresh_token.is_active is False
        
        mock_db.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_token_refresh_invalid_token(self, auth_service, mock_db):
        """Test token refresh with invalid token"""
        # Mock no token found
        mock_db.execute.return_value.first.return_value = None
        
        refresh_request = TokenRefreshRequest(refresh_token="invalid-token")
        
        # Test should fail
        with pytest.raises(Exception) as exc_info:
            await auth_service.refresh_token(
                refresh_request=refresh_request,
                db=mock_db
            )
        
        mock_db.rollback.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_token_refresh_reuse_detection(self, auth_service, mock_db):
        """Test token reuse detection (security breach)"""
        # Mock already used refresh token
        mock_refresh_token = MagicMock()
        mock_refresh_token.id = uuid.uuid4()
        mock_refresh_token.family_id = uuid.uuid4()
        mock_refresh_token.creator_id = uuid.uuid4()
        mock_refresh_token.used_at = datetime.utcnow() - timedelta(minutes=5)  # Already used
        mock_refresh_token.revoked_at = None
        mock_refresh_token.is_active = True
        mock_refresh_token.expires_at = datetime.utcnow() + timedelta(days=30)
        
        mock_creator = MagicMock()
        mock_creator.id = mock_refresh_token.creator_id
        mock_creator.email = "test@example.com"
        
        # Mock database response
        mock_db.execute.return_value.first.return_value = (mock_refresh_token, mock_creator)
        
        refresh_request = TokenRefreshRequest(refresh_token="reused-token")
        
        # Test should fail and revoke token family
        with pytest.raises(Exception) as exc_info:
            await auth_service.refresh_token(
                refresh_request=refresh_request,
                db=mock_db
            )


class TestAuthServiceLogout:
    """Test logout functionality"""
    
    @pytest.mark.asyncio
    async def test_successful_logout(self, auth_service, mock_db):
        """Test successful logout"""
        creator_id = uuid.uuid4()
        refresh_token = "test-refresh-token"
        
        # Mock refresh token in database
        mock_refresh_token = MagicMock()
        mock_refresh_token.id = uuid.uuid4()
        mock_refresh_token.creator_id = creator_id
        mock_refresh_token.is_active = True
        
        mock_db.execute.return_value.scalar_one_or_none.return_value = mock_refresh_token
        mock_db.commit = AsyncMock()
        
        # Test logout
        result = await auth_service.logout_creator(
            creator_id=creator_id,
            refresh_token=refresh_token,
            db=mock_db,
            client_ip="127.0.0.1",
            user_agent="test-agent"
        )
        
        # Verify results
        assert result is True
        
        # Verify token revoked
        assert mock_refresh_token.revoked_at is not None
        assert mock_refresh_token.is_active is False
        
        mock_db.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_logout_without_refresh_token(self, auth_service, mock_db):
        """Test logout without refresh token"""
        creator_id = uuid.uuid4()
        
        mock_db.commit = AsyncMock()
        
        # Test logout without refresh token
        result = await auth_service.logout_creator(
            creator_id=creator_id,
            refresh_token=None,
            db=mock_db
        )
        
        # Should still succeed
        assert result is True
        mock_db.commit.assert_called_once()


class TestAuthServicePasswordValidation:
    """Test password validation endpoint"""
    
    @pytest.mark.asyncio
    @patch('shared.security.validate_password_strength')
    async def test_password_validation_endpoint(self, mock_validate, auth_service):
        """Test password validation endpoint"""
        # Mock validation result
        mock_result = MagicMock()
        mock_result.strength.value = "strong"
        mock_result.score = 85
        mock_result.is_valid = True
        mock_result.violations = []
        mock_result.suggestions = []
        mock_result.estimated_crack_time = "centuries"
        mock_validate.return_value = mock_result
        
        # Test validation
        result = await auth_service.validate_password_strength_endpoint(
            password="StrongP@ssw0rd123!",
            personal_info={"email": "test@example.com"}
        )
        
        # Verify results
        assert result.strength == "strong"
        assert result.score == 85
        assert result.is_valid is True
        assert len(result.violations) == 0
        assert result.estimated_crack_time == "centuries"
        
        # Verify validation called with correct parameters
        mock_validate.assert_called_once_with(
            "StrongP@ssw0rd123!",
            {"email": "test@example.com"}
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])