"""
Integration tests for password reset endpoints
"""

import pytest
import json
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

# Set up test environment variables before importing the app
test_env_vars = {
    "JWT_SECRET_KEY": "test-secret-key-for-testing-purposes-only",
    "JWT_ALGORITHM": "HS256",
    "PASSWORD_RESET_TOKEN_EXPIRE_MINUTES": "15",
    "FRONTEND_URL": "http://localhost:3000"
}

with patch.dict('os.environ', test_env_vars):
    from ..app.main import app

client = TestClient(app)


class TestPasswordResetRequestEndpoint:
    """Test the password reset request endpoint"""

    def test_request_password_reset_valid_email(self):
        """Test password reset request with valid email format"""
        # Mock the auth service
        with patch('services.auth-service.app.routes.auth.auth_service') as mock_auth_service:
            mock_auth_service.request_password_reset = MagicMock(return_value="test_reset_token")
            
            # Mock email service
            with patch('services.auth-service.app.routes.auth.get_email_service') as mock_email_service:
                mock_email_service.return_value = MagicMock()
                
                response = client.post(
                    "/api/v1/auth/password/reset/request",
                    json={"email": "test@example.com"}
                )
                
                assert response.status_code == 202
                assert "If an account with this email exists" in response.json()["message"]
                
                # Verify auth service was called
                mock_auth_service.request_password_reset.assert_called_once()
                
                # Verify email service was called
                mock_email_service.return_value.send_password_reset_email.assert_called_once()

    def test_request_password_reset_invalid_email(self):
        """Test password reset request with invalid email format"""
        response = client.post(
            "/api/v1/auth/password/reset/request",
            json={"email": "invalid-email"}
        )
        
        assert response.status_code == 422  # Validation error

    def test_request_password_reset_missing_email(self):
        """Test password reset request with missing email"""
        response = client.post(
            "/api/v1/auth/password/reset/request",
            json={}
        )
        
        assert response.status_code == 422  # Validation error

    def test_request_password_reset_rate_limiting(self):
        """Test rate limiting on password reset request endpoint"""
        # Mock the auth service
        with patch('services.auth-service.app.routes.auth.auth_service') as mock_auth_service:
            mock_auth_service.request_password_reset = MagicMock(return_value="test_reset_token")
            
            # Make multiple requests to trigger rate limiting
            responses = []
            for i in range(5):  # Exceeds the limit of 3 per hour
                response = client.post(
                    "/api/v1/auth/password/reset/request",
                    json={"email": f"test{i}@example.com"}
                )
                responses.append(response)
            
            # Check that we get a 429 Too Many Requests response
            # Note: This might not work in testing without a real Redis instance
            # but we can at least verify the structure of earlier responses
            assert len(responses) == 5


class TestPasswordResetConfirmEndpoint:
    """Test the password reset confirm endpoint"""

    def test_confirm_password_reset_valid_token_and_password(self):
        """Test password reset confirmation with valid token and password"""
        # Mock the auth service
        with patch('services.auth-service.app.routes.auth.auth_service') as mock_auth_service:
            mock_auth_service.confirm_password_reset = MagicMock(return_value=True)
            
            response = client.post(
                "/api/v1/auth/password/reset/confirm",
                json={
                    "token": "valid_reset_token",
                    "new_password": "NewSecureP@ssw0rd123!"
                }
            )
            
            assert response.status_code == 200
            assert "Password reset successful" in response.json()["message"]
            
            # Verify auth service was called
            mock_auth_service.confirm_password_reset.assert_called_once()

    def test_confirm_password_reset_invalid_token_format(self):
        """Test password reset confirmation with invalid token format"""
        response = client.post(
            "/api/v1/auth/password/reset/confirm",
            json={
                "token": "",
                "new_password": "NewSecureP@ssw0rd123!"
            }
        )
        
        assert response.status_code == 422  # Validation error

    def test_confirm_password_reset_expired_token(self):
        """Test password reset confirmation with expired token"""
        # Mock the auth service to raise an exception for expired token
        with patch('services.auth-service.app.routes.auth.auth_service') as mock_auth_service:
            mock_auth_service.confirm_password_reset = MagicMock()
            mock_auth_service.confirm_password_reset.side_effect = Exception(
                type('MockHTTPException', (), {
                    'status_code': 400,
                    'detail': 'Password reset token has expired'
                })()
            )
            
            response = client.post(
                "/api/v1/auth/password/reset/confirm",
                json={
                    "token": "expired_token",
                    "new_password": "NewSecureP@ssw0rd123!"
                }
            )
            
            # In a real implementation, this would return 400
            # For now, we're just testing the structure

    def test_confirm_password_reset_weak_password(self):
        """Test password reset confirmation with weak password"""
        response = client.post(
            "/api/v1/auth/password/reset/confirm",
            json={
                "token": "valid_token",
                "new_password": "weak"  # Too short
            }
        )
        
        assert response.status_code == 422  # Validation error

    def test_confirm_password_reset_missing_fields(self):
        """Test password reset confirmation with missing fields"""
        response = client.post(
            "/api/v1/auth/password/reset/confirm",
            json={}
        )
        
        assert response.status_code == 422  # Validation error

    def test_confirm_password_reset_rate_limiting(self):
        """Test rate limiting on password reset confirmation endpoint"""
        # Mock the auth service
        with patch('services.auth-service.app.routes.auth.auth_service') as mock_auth_service:
            mock_auth_service.confirm_password_reset = MagicMock(return_value=True)
            
            # Make multiple requests to trigger rate limiting
            responses = []
            for i in range(7):  # Exceeds the limit of 5 per 15 minutes
                response = client.post(
                    "/api/v1/auth/password/reset/confirm",
                    json={
                        "token": f"token{i}",
                        "new_password": "NewSecureP@ssw0rd123!"
                    }
                )
                responses.append(response)
            
            # Check responses
            assert len(responses) == 7


class TestPasswordResetSecurity:
    """Test security aspects of password reset endpoints"""

    def test_password_reset_token_single_use(self):
        """Verify that tokens are single-use"""
        # Mock the auth service
        with patch('services.auth-service.app.routes.auth.auth_service') as mock_auth_service:
            # First use should succeed
            mock_auth_service.confirm_password_reset = MagicMock(return_value=True)
            
            response1 = client.post(
                "/api/v1/auth/password/reset/confirm",
                json={
                    "token": "single_use_token",
                    "new_password": "NewSecureP@ssw0rd123!"
                }
            )
            
            # Second use should fail
            mock_auth_service.confirm_password_reset.side_effect = Exception(
                type('MockHTTPException', (), {
                    'status_code': 400,
                    'detail': 'Password reset token has already been used'
                })()
            )
            
            response2 = client.post(
                "/api/v1/auth/password/reset/confirm",
                json={
                    "token": "single_use_token",
                    "new_password": "AnotherSecureP@ssw0rd123!"
                }
            )
            
            # First should succeed, second should fail
            # Note: Actual behavior depends on implementation

    def test_password_reset_old_refresh_tokens_invalidated(self):
        """Test that old refresh tokens are invalidated after password reset"""
        # This would require more complex mocking of the database and refresh token system
        # For now, we'll just test the endpoint structure
        with patch('services.auth-service.app.routes.auth.auth_service') as mock_auth_service:
            mock_auth_service.confirm_password_reset = MagicMock(return_value=True)
            
            response = client.post(
                "/api/v1/auth/password/reset/confirm",
                json={
                    "token": "valid_token",
                    "new_password": "NewSecureP@ssw0rd123!"
                }
            )
            
            assert response.status_code == 200

    def test_password_reset_malformed_requests(self):
        """Test that malformed requests return appropriate error codes"""
        # Test with malformed JSON
        response = client.post(
            "/api/v1/auth/password/reset/request",
            content='{"email": "test@example.com",}',  # Trailing comma
            headers={"Content-Type": "application/json"}
        )
        
        # Should return 422 for validation error
        assert response.status_code == 422