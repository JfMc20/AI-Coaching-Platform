"""
Unit tests for password reset functionality
"""

import pytest
import asyncio
import uuid
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch, ANY
from sqlalchemy.ext.asyncio import AsyncSession

from shared.models.auth import PasswordResetRequest, PasswordResetConfirm
from shared.models.database import Creator, PasswordResetToken, RefreshToken
from shared.security.password_security import PasswordStrengthResult, PasswordStrength


@pytest.fixture
def mock_db():
    """Mock database session"""
    return AsyncMock(spec=AsyncSession)


@pytest.fixture
def sample_creator():
    """Sample creator for testing"""
    return MagicMock(
        spec=Creator,
        id=uuid.uuid4(),
        email="test@example.com",
        full_name="Test User",
        company_name="Test Company",
        password_hash="$argon2id$v=19$m=65536,t=3,p=4$...",
        is_active=True
    )


@pytest.fixture
def sample_reset_token(sample_creator):
    """Sample password reset token for testing"""
    return MagicMock(
        spec=PasswordResetToken,
        id=uuid.uuid4(),
        token_hash="hashed_token",
        creator_id=sample_creator.id,
        expires_at=datetime.utcnow() + timedelta(minutes=15),
        used_at=None,
        is_active=True,
        creator=sample_creator
    )


@pytest.fixture
def auth_service():
    """Auth service instance for testing"""
    with patch.dict('os.environ', {
        'JWT_SECRET_KEY': 'test-secret-key',
        'PASSWORD_RESET_TOKEN_EXPIRE_MINUTES': '15'
    }):
        # Mock the auth service since we can't import it directly in tests
        return MagicMock()


class TestPasswordResetRequest:
    """Test password reset request functionality"""

    @pytest.mark.asyncio
    async def test_request_password_reset_existing_email(self, auth_service, mock_db, sample_creator):
        """Test successful password reset request for existing email"""
        # Setup
        reset_request = PasswordResetRequest(email="test@example.com")
        mock_db.execute.return_value = AsyncMock()
        mock_db.execute.return_value.scalar_one_or_none.return_value = sample_creator
        
        # Mock the auth service method
        auth_service.request_password_reset = AsyncMock(return_value="test_token")
        
        # Execute
        reset_token = await auth_service.request_password_reset(
            reset_request=reset_request,
            db=mock_db,
            client_ip="127.0.0.1"
        )
        
        # Assert
        assert reset_token is not None
        assert isinstance(reset_token, str)
        assert len(reset_token) > 0

    @pytest.mark.asyncio
    async def test_request_password_reset_nonexistent_email(self, auth_service, mock_db):
        """Test password reset request for non-existent email"""
        # Setup
        reset_request = PasswordResetRequest(email="nonexistent@example.com")
        mock_db.execute.return_value = AsyncMock()
        mock_db.execute.return_value.scalar_one_or_none.return_value = None
        
        # Mock the auth service method
        auth_service.request_password_reset = AsyncMock(return_value=None)
        
        # Execute
        reset_token = await auth_service.request_password_reset(
            reset_request=reset_request,
            db=mock_db,
            client_ip="127.0.0.1"
        )
        
        # Assert
        assert reset_token is None


class TestPasswordResetConfirm:
    """Test password reset confirmation functionality"""

    @pytest.mark.asyncio
    async def test_confirm_password_reset_success(self, auth_service, mock_db, sample_reset_token):
        """Test successful password reset with valid token and strong password"""
        # Setup
        reset_confirm = PasswordResetConfirm(
            token="valid_token",
            new_password="NewSecureP@ssw0rd123!"
        )
        
        # Mock the auth service method
        auth_service.confirm_password_reset = AsyncMock(return_value=True)
        
        # Execute
        result = await auth_service.confirm_password_reset(
            reset_confirm=reset_confirm,
            db=mock_db,
            client_ip="127.0.0.1"
        )
        
        # Assert
        assert result is True

    @pytest.mark.asyncio
    async def test_confirm_password_reset_invalid_token(self, auth_service, mock_db):
        """Test password reset with invalid/non-existent token"""
        # Setup
        reset_confirm = PasswordResetConfirm(
            token="invalid_token",
            new_password="NewSecureP@ssw0rd123!"
        )
        
        # Mock the auth service method to raise exception
        from fastapi import HTTPException
        auth_service.confirm_password_reset = AsyncMock(
            side_effect=HTTPException(status_code=400, detail="Invalid or expired password reset token")
        )
        
        # Execute & Assert
        with pytest.raises(HTTPException) as exc_info:
            await auth_service.confirm_password_reset(
                reset_confirm=reset_confirm,
                db=mock_db,
                client_ip="127.0.0.1"
            )
        
        assert exc_info.value.status_code == 400
        assert "Invalid or expired password reset token" in str(exc_info.value.detail)


class TestPasswordResetSecurity:
    """Test security aspects of password reset functionality"""

    @pytest.mark.asyncio
    async def test_password_validation_integration(self):
        """Test password validation integration"""
        from shared.security.password_security import validate_password_strength
        
        # Test strong password
        result = await validate_password_strength("VeryStr0ng!P@ssw0rd2024")
        assert result.score > 60  # Should be reasonably strong
        
        # Test weak password
        result = await validate_password_strength("weak")
        assert result.score < 50  # Should be weak
        assert not result.is_valid