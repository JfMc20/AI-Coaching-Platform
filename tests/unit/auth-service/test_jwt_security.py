"""
Comprehensive JWT security tests for auth service.
Tests JWT generation, validation, blacklisting, and security edge cases.
"""

import pytest
import jwt
import time
from datetime import datetime, timedelta
from httpx import AsyncClient
from unittest.mock import AsyncMock, patch, MagicMock

from shared.security.jwt_manager import JWTManager
from shared.exceptions.auth import InvalidTokenError, TokenExpiredError


class TestJWTSecurity:
    """Test JWT security implementation."""

    async def test_jwt_generation_and_validation(self, auth_client: AsyncClient):
        """Test JWT token generation and validation cycle."""
        # Register and login user
        user_data = {
            "email": "test@example.com",
            "password": "SecurePass123!",
            "full_name": "Test User",
            "tenant_id": "tenant_1"
        }
        
        await auth_client.post("/api/v1/auth/register", json=user_data)
        
        login_response = await auth_client.post("/api/v1/auth/login", json={
            "email": user_data["email"],
            "password": user_data["password"]
        })
        
        assert login_response.status_code == 200
        token_data = login_response.json()
        
        # Verify token structure
        assert "access_token" in token_data
        assert "refresh_token" in token_data
        assert "token_type" in token_data
        assert "expires_in" in token_data
        assert token_data["token_type"] == "bearer"
        
        access_token = token_data["access_token"]
        
        # Test token validation with protected endpoint
        profile_response = await auth_client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        
        assert profile_response.status_code == 200
        user_profile = profile_response.json()
        assert user_profile["email"] == user_data["email"]

    async def test_jwt_token_expiration(self, auth_client: AsyncClient):
        """Test that expired tokens are rejected."""
        # Mock JWT manager to create expired token
        with patch('shared.security.jwt_manager.JWTManager.generate_tokens') as mock_generate:
            # Create an expired token (expired 1 hour ago)
            expired_time = datetime.utcnow() - timedelta(hours=1)
            
            mock_generate.return_value = {
                "access_token": jwt.encode({
                    "sub": "test_user_id",
                    "email": "test@example.com", 
                    "tenant_id": "tenant_1",
                    "exp": expired_time,
                    "iat": expired_time - timedelta(minutes=15),
                    "type": "access"
                }, "test-secret", algorithm="HS256"),
                "refresh_token": "mock_refresh_token",
                "expires_in": -3600  # Negative to indicate expired
            }
            
            # Register and login to get expired token
            user_data = {
                "email": "test@example.com",
                "password": "SecurePass123!",
                "full_name": "Test User",
                "tenant_id": "tenant_1"
            }
            
            await auth_client.post("/api/v1/auth/register", json=user_data)
            login_response = await auth_client.post("/api/v1/auth/login", json={
                "email": user_data["email"],
                "password": user_data["password"]
            })
            
            expired_token = login_response.json()["access_token"]
        
        # Try to use expired token
        response = await auth_client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {expired_token}"}
        )
        
        assert response.status_code == 401
        error_data = response.json()
        assert "expired" in error_data["detail"].lower()

    async def test_jwt_token_blacklisting(self, auth_client: AsyncClient):
        """Test JWT token blacklisting on logout."""
        # Register and login
        user_data = {
            "email": "test@example.com",
            "password": "SecurePass123!",
            "full_name": "Test User",
            "tenant_id": "tenant_1"
        }
        
        await auth_client.post("/api/v1/auth/register", json=user_data)
        login_response = await auth_client.post("/api/v1/auth/login", json={
            "email": user_data["email"],
            "password": user_data["password"]
        })
        
        access_token = login_response.json()["access_token"]
        
        # Verify token works before logout
        profile_response = await auth_client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        assert profile_response.status_code == 200
        
        # Logout to blacklist token
        logout_response = await auth_client.post(
            "/api/v1/auth/logout",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        assert logout_response.status_code == 200
        
        # Try to use blacklisted token
        blacklisted_response = await auth_client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        assert blacklisted_response.status_code == 401
        error_data = blacklisted_response.json()
        assert "revoked" in error_data["detail"].lower() or "blacklisted" in error_data["detail"].lower()

    async def test_jwt_refresh_token_flow(self, auth_client: AsyncClient):
        """Test refresh token flow for access token renewal."""
        # Register and login
        user_data = {
            "email": "test@example.com",
            "password": "SecurePass123!",
            "full_name": "Test User", 
            "tenant_id": "tenant_1"
        }
        
        await auth_client.post("/api/v1/auth/register", json=user_data)
        login_response = await auth_client.post("/api/v1/auth/login", json={
            "email": user_data["email"],
            "password": user_data["password"]
        })
        
        original_access_token = login_response.json()["access_token"]
        refresh_token = login_response.json()["refresh_token"]
        
        # Use refresh token to get new access token
        refresh_response = await auth_client.post("/api/v1/auth/refresh", json={
            "refresh_token": refresh_token
        })
        
        assert refresh_response.status_code == 200
        new_token_data = refresh_response.json()
        
        assert "access_token" in new_token_data
        assert "refresh_token" in new_token_data
        
        new_access_token = new_token_data["access_token"]
        new_refresh_token = new_token_data["refresh_token"]
        
        # Verify new tokens are different
        assert new_access_token != original_access_token
        assert new_refresh_token != refresh_token
        
        # Verify new access token works
        profile_response = await auth_client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {new_access_token}"}
        )
        assert profile_response.status_code == 200

    async def test_jwt_invalid_signature(self, auth_client: AsyncClient):
        """Test that tokens with invalid signatures are rejected."""
        # Create a token with wrong signature
        fake_token = jwt.encode({
            "sub": "fake_user_id",
            "email": "fake@example.com",
            "tenant_id": "tenant_1", 
            "exp": datetime.utcnow() + timedelta(hours=1),
            "iat": datetime.utcnow(),
            "type": "access"
        }, "wrong-secret", algorithm="HS256")
        
        # Try to use fake token
        response = await auth_client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {fake_token}"}
        )
        
        assert response.status_code == 401
        error_data = response.json()
        assert "invalid" in error_data["detail"].lower() or "signature" in error_data["detail"].lower()

    async def test_jwt_malformed_token(self, auth_client: AsyncClient):
        """Test that malformed tokens are rejected."""
        malformed_tokens = [
            "not.a.jwt",
            "definitely-not-a-jwt-token",
            "header.payload",  # Missing signature
            "",  # Empty token
            "Bearer token",  # Wrong format
        ]
        
        for malformed_token in malformed_tokens:
            response = await auth_client.get(
                "/api/v1/auth/me",
                headers={"Authorization": f"Bearer {malformed_token}"}
            )
            
            assert response.status_code == 401
            error_data = response.json()
            assert "invalid" in error_data["detail"].lower() or "malformed" in error_data["detail"].lower()

    async def test_jwt_missing_claims(self, auth_client: AsyncClient):
        """Test that tokens missing required claims are rejected."""
        # Create token with missing required claims
        incomplete_token = jwt.encode({
            "sub": "user_id",
            # Missing email, tenant_id, exp, etc.
        }, "test-secret", algorithm="HS256")
        
        response = await auth_client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {incomplete_token}"}
        )
        
        assert response.status_code == 401
        error_data = response.json()
        assert "invalid" in error_data["detail"].lower() or "claims" in error_data["detail"].lower()

    async def test_jwt_wrong_token_type(self, auth_client: AsyncClient):
        """Test that refresh tokens cannot be used as access tokens."""
        # Register and login
        user_data = {
            "email": "test@example.com",
            "password": "SecurePass123!",
            "full_name": "Test User",
            "tenant_id": "tenant_1"
        }
        
        await auth_client.post("/api/v1/auth/register", json=user_data)
        login_response = await auth_client.post("/api/v1/auth/login", json={
            "email": user_data["email"], 
            "password": user_data["password"]
        })
        
        refresh_token = login_response.json()["refresh_token"]
        
        # Try to use refresh token as access token
        response = await auth_client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {refresh_token}"}
        )
        
        assert response.status_code == 401
        error_data = response.json()
        assert "invalid" in error_data["detail"].lower() or "type" in error_data["detail"].lower()

    async def test_jwt_algorithm_confusion(self, auth_client: AsyncClient):
        """Test protection against algorithm confusion attacks."""
        # Try to create token with 'none' algorithm
        none_token = jwt.encode({
            "sub": "fake_user_id",
            "email": "fake@example.com",
            "tenant_id": "tenant_1",
            "exp": datetime.utcnow() + timedelta(hours=1),
            "iat": datetime.utcnow(),
            "type": "access"
        }, "", algorithm="none")
        
        response = await auth_client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {none_token}"}
        )
        
        assert response.status_code == 401
        error_data = response.json()
        assert "invalid" in error_data["detail"].lower()

    @pytest.mark.asyncio
    async def test_jwt_concurrent_validation(self, auth_client: AsyncClient):
        """Test JWT validation under concurrent load."""
        import asyncio
        
        # Register and login
        user_data = {
            "email": "test@example.com",
            "password": "SecurePass123!",
            "full_name": "Test User",
            "tenant_id": "tenant_1"
        }
        
        await auth_client.post("/api/v1/auth/register", json=user_data)
        login_response = await auth_client.post("/api/v1/auth/login", json={
            "email": user_data["email"],
            "password": user_data["password"]
        })
        
        access_token = login_response.json()["access_token"]
        
        # Make multiple concurrent requests with same token
        async def validate_token():
            response = await auth_client.get(
                "/api/v1/auth/me",
                headers={"Authorization": f"Bearer {access_token}"}
            )
            return response.status_code
        
        # Run 10 concurrent validation requests
        tasks = [validate_token() for _ in range(10)]
        results = await asyncio.gather(*tasks)
        
        # All should succeed
        assert all(status == 200 for status in results)

    async def test_jwt_key_rotation_compatibility(self):
        """Test JWT manager key rotation functionality."""
        # This test verifies that the JWT manager can handle key rotation
        jwt_manager = JWTManager()
        
        # Mock key rotation scenario
        with patch.object(jwt_manager, '_get_current_signing_key') as mock_key:
            mock_key.return_value = "new-signing-key"
            
            # Generate token with new key
            token_data = await jwt_manager.generate_tokens(
                user_id="test_user",
                email="test@example.com",
                tenant_id="tenant_1"
            )
            
            assert "access_token" in token_data
            assert "refresh_token" in token_data
            
            # Verify token can be validated
            is_valid = await jwt_manager.validate_token(token_data["access_token"])
            assert is_valid is True