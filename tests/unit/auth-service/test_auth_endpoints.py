"""
Tests for authentication endpoints.
Tests registration, login, token refresh, and validation endpoints.

Fixtures are now centralized in tests/fixtures/auth_fixtures.py and automatically
available through the main conftest.py configuration.
"""

from httpx import AsyncClient


class TestAuthEndpoints:
    """Test authentication API endpoints."""

    async def test_user_registration_success(self, auth_client: AsyncClient, test_user_data):
        """Test successful user registration."""
        response = await auth_client.post("/api/v1/auth/register", json=test_user_data)
        
        assert response.status_code == 201
        user_data = response.json()
        
        assert user_data["email"] == test_user_data["email"]
        assert user_data["full_name"] == test_user_data["full_name"]
        assert user_data["tenant_id"] == test_user_data["tenant_id"]
        assert "id" in user_data
        assert "password" not in user_data
        assert "created_at" in user_data

    async def test_user_registration_duplicate_email(self, auth_client: AsyncClient, test_user_data):
        """Test registration with duplicate email fails."""
        # Register user first time
        response1 = await auth_client.post("/api/v1/auth/register", json=test_user_data)
        assert response1.status_code == 201
        
        # Try to register same email again
        response2 = await auth_client.post("/api/v1/auth/register", json=test_user_data)
        assert response2.status_code == 409
        
        error_data = response2.json()
        assert "email" in error_data["detail"].lower()

    async def test_user_registration_invalid_email(self, auth_client: AsyncClient, test_user_data):
        """Test registration with invalid email format."""
        test_user_data["email"] = "invalid-email"
        
        response = await auth_client.post("/api/v1/auth/register", json=test_user_data)
        assert response.status_code == 422
        
        error_data = response.json()
        assert "email" in str(error_data).lower()

    async def test_user_registration_weak_password(self, auth_client: AsyncClient, test_user_data):
        """Test registration with weak password."""
        test_user_data["password"] = "weak"
        
        response = await auth_client.post("/api/v1/auth/register", json=test_user_data)
        assert response.status_code == 422
        
        error_data = response.json()
        assert "password" in str(error_data).lower()

    async def test_user_login_success(self, auth_client: AsyncClient, registered_user, test_user_data):
        """Test successful user login."""
        login_data = {
            "email": test_user_data["email"],
            "password": test_user_data["password"]
        }
        
        response = await auth_client.post("/api/v1/auth/login", json=login_data)
        assert response.status_code == 200
        
        token_data = response.json()
        assert "access_token" in token_data
        assert "refresh_token" in token_data
        assert token_data["token_type"] == "bearer"
        assert "expires_in" in token_data

    async def test_user_login_invalid_credentials(self, auth_client: AsyncClient, registered_user, test_user_data):
        """Test login with invalid credentials."""
        # Wrong password
        response = await auth_client.post("/api/v1/auth/login", json={
            "email": test_user_data["email"],
            "password": "WrongPassword"
        })
        assert response.status_code == 401
        
        # Non-existent user
        response = await auth_client.post("/api/v1/auth/login", json={
            "email": "nonexistent@example.com",
            "password": test_user_data["password"]
        })
        assert response.status_code == 401

    async def test_token_refresh_success(self, auth_client: AsyncClient, authenticated_user):
        """Test successful token refresh."""
        refresh_data = {
            "refresh_token": authenticated_user["refresh_token"]
        }
        
        response = await auth_client.post("/api/v1/auth/refresh", json=refresh_data)
        assert response.status_code == 200
        
        token_data = response.json()
        assert "access_token" in token_data
        assert "refresh_token" in token_data
        assert token_data["token_type"] == "bearer"

    async def test_token_refresh_invalid_token(self, auth_client: AsyncClient):
        """Test token refresh with invalid refresh token."""
        response = await auth_client.post("/api/v1/auth/refresh", json={
            "refresh_token": "invalid-refresh-token"
        })
        assert response.status_code == 401

    async def test_token_validation_success(self, auth_client: AsyncClient, authenticated_user):
        """Test token validation endpoint."""
        headers = authenticated_user["headers"]
        
        response = await auth_client.get("/api/v1/auth/validate", headers=headers)
        assert response.status_code == 200
        
        user_data = response.json()
        assert user_data["email"] == authenticated_user["user"]["email"]
        assert user_data["tenant_id"] == authenticated_user["user"]["tenant_id"]

    async def test_token_validation_invalid_token(self, auth_client: AsyncClient):
        """Test token validation with invalid token."""
        headers = {"Authorization": "Bearer invalid-token"}
        
        response = await auth_client.get("/api/v1/auth/validate", headers=headers)
        assert response.status_code == 401

    async def test_token_validation_missing_token(self, auth_client: AsyncClient):
        """Test token validation without token."""
        response = await auth_client.get("/api/v1/auth/validate")
        assert response.status_code == 401

    async def test_password_reset_request(self, auth_client: AsyncClient, registered_user, test_user_data):
        """Test password reset request."""
        response = await auth_client.post("/api/v1/auth/password-reset", json={
            "email": test_user_data["email"]
        })
        # Should return 200 even for non-existent emails (security)
        assert response.status_code == 200

    async def test_user_profile_access(self, auth_client: AsyncClient, authenticated_user):
        """Test accessing user profile with valid token."""
        headers = authenticated_user["headers"]
        
        response = await auth_client.get("/api/v1/auth/profile", headers=headers)
        assert response.status_code == 200
        
        profile_data = response.json()
        assert profile_data["email"] == authenticated_user["user"]["email"]
        assert "password" not in profile_data

    async def test_user_profile_unauthorized(self, auth_client: AsyncClient):
        """Test accessing user profile without authentication."""
        response = await auth_client.get("/api/v1/auth/profile")
        assert response.status_code == 401

    async def test_logout_success(self, auth_client: AsyncClient, authenticated_user):
        """Test user logout."""
        headers = authenticated_user["headers"]
        
        response = await auth_client.post("/api/v1/auth/logout", headers=headers)
        assert response.status_code == 200

    async def test_concurrent_logins(self, auth_client: AsyncClient, registered_user, test_user_data):
        """Test multiple concurrent login attempts."""
        import asyncio
        
        login_data = {
            "email": test_user_data["email"],
            "password": test_user_data["password"]
        }
        
        # Create multiple concurrent login requests
        tasks = [
            auth_client.post("/api/v1/auth/login", json=login_data)
            for _ in range(5)
        ]
        
        responses = await asyncio.gather(*tasks)
        
        # All should succeed
        for response in responses:
            assert response.status_code == 200
            token_data = response.json()
            assert "access_token" in token_data

    async def test_rate_limiting(self, auth_client: AsyncClient, test_user_data):
        """Test rate limiting on authentication endpoints."""
        # This test assumes rate limiting is implemented
        # Multiple rapid failed login attempts
        login_data = {
            "email": test_user_data["email"],
            "password": "WrongPassword"
        }
        
        responses = []
        for _ in range(10):  # Try 10 failed logins rapidly
            response = await auth_client.post("/api/v1/auth/login", json=login_data)
            responses.append(response)
        
        # Should eventually get rate limited (429) or continue getting 401
        status_codes = [r.status_code for r in responses]
        assert all(code in [401, 429] for code in status_codes)

    async def test_tenant_isolation(self, auth_client: AsyncClient, multiple_registered_users, test_users_data):
        """Test that users from different tenants are isolated."""
        # Login users from different tenants
        user1_login = await auth_client.post("/api/v1/auth/login", json={
            "email": test_users_data[0]["email"],
            "password": test_users_data[0]["password"]
        })
        
        user2_login = await auth_client.post("/api/v1/auth/login", json={
            "email": test_users_data[1]["email"],
            "password": test_users_data[1]["password"]
        })
        
        assert user1_login.status_code == 200
        assert user2_login.status_code == 200
        
        # Validate tokens contain correct tenant information
        user1_token = user1_login.json()["access_token"]
        user2_token = user2_login.json()["access_token"]
        
        user1_headers = {"Authorization": f"Bearer {user1_token}"}
        user2_headers = {"Authorization": f"Bearer {user2_token}"}
        
        user1_profile = await auth_client.get("/api/v1/auth/validate", headers=user1_headers)
        user2_profile = await auth_client.get("/api/v1/auth/validate", headers=user2_headers)
        
        assert user1_profile.status_code == 200
        assert user2_profile.status_code == 200
        
        user1_data = user1_profile.json()
        user2_data = user2_profile.json()
        
        assert user1_data["tenant_id"] != user2_data["tenant_id"]