"""
Integration tests for authentication flow across services.
Tests user registration, login, token management, and multi-tenant isolation.
"""

import pytest
from httpx import AsyncClient


class TestAuthenticationFlow:
    """Test complete authentication workflows."""

    async def test_user_registration_flow(self, service_clients, test_user_data):
        """Test user registration with validation."""
        auth_client = service_clients["auth"]
        
        # Test user registration
        response = await auth_client.post("/api/v1/auth/register", json=test_user_data)
        assert response.status_code == 201
        
        user_data = response.json()
        assert user_data["email"] == test_user_data["email"]
        assert user_data["full_name"] == test_user_data["full_name"]
        assert "id" in user_data
        assert "password" not in user_data  # Password should not be returned

    async def test_user_login_flow(self, service_clients, test_user_data):
        """Test user login and token generation."""
        auth_client = service_clients["auth"]
        
        # Register user first
        await auth_client.post("/api/v1/auth/register", json=test_user_data)
        
        # Test login
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

    async def test_token_validation_across_services(self, service_clients, test_user_data):
        """Test JWT token validation across different services."""
        auth_client = service_clients["auth"]
        creator_hub_client = service_clients["creator_hub"]
        
        # Register and login user
        await auth_client.post("/api/v1/auth/register", json=test_user_data)
        login_response = await auth_client.post("/api/v1/auth/login", json={
            "email": test_user_data["email"],
            "password": test_user_data["password"]
        })
        
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Test token validation in creator-hub service
        response = await creator_hub_client.get("/api/v1/health", headers=headers)
        # Should not return 401 Unauthorized if token is valid
        assert response.status_code != 401

    async def test_token_refresh_flow(self, service_clients, test_user_data):
        """Test JWT token refresh mechanism."""
        auth_client = service_clients["auth"]
        
        # Register and login user
        await auth_client.post("/api/v1/auth/register", json=test_user_data)
        login_response = await auth_client.post("/api/v1/auth/login", json={
            "email": test_user_data["email"],
            "password": test_user_data["password"]
        })
        
        refresh_token = login_response.json()["refresh_token"]
        
        # Test token refresh
        response = await auth_client.post("/api/v1/auth/refresh", json={
            "refresh_token": refresh_token
        })
        assert response.status_code == 200
        
        new_token_data = response.json()
        assert "access_token" in new_token_data
        assert "refresh_token" in new_token_data

    async def test_multi_tenant_isolation(self, service_clients):
        """Test that users from different tenants are properly isolated."""
        auth_client = service_clients["auth"]
        
        # Create users in different tenants
        user1_data = {
            "email": "user1@tenant1.com",
            "password": "Password123!",
            "full_name": "User One",
            "tenant_id": "tenant-1"
        }
        
        user2_data = {
            "email": "user2@tenant2.com",
            "password": "Password123!",
            "full_name": "User Two",
            "tenant_id": "tenant-2"
        }
        
        # Register users
        response1 = await auth_client.post("/api/v1/auth/register", json=user1_data)
        response2 = await auth_client.post("/api/v1/auth/register", json=user2_data)
        
        assert response1.status_code == 201
        assert response2.status_code == 201
        
        # Verify users have different tenant IDs
        user1 = response1.json()
        user2 = response2.json()
        assert user1["tenant_id"] != user2["tenant_id"]

    async def test_invalid_credentials(self, service_clients, test_user_data):
        """Test authentication with invalid credentials."""
        auth_client = service_clients["auth"]
        
        # Register user first
        await auth_client.post("/api/v1/auth/register", json=test_user_data)
        
        # Test with wrong password
        response = await auth_client.post("/api/v1/auth/login", json={
            "email": test_user_data["email"],
            "password": "WrongPassword"
        })
        assert response.status_code == 401
        
        # Test with non-existent user
        response = await auth_client.post("/api/v1/auth/login", json={
            "email": "nonexistent@example.com",
            "password": "Password123!"
        })
        assert response.status_code == 401

    async def test_duplicate_user_registration(self, service_clients, test_user_data):
        """Test that duplicate user registration is prevented."""
        auth_client = service_clients["auth"]
        
        # Register user first time
        response1 = await auth_client.post("/api/v1/auth/register", json=test_user_data)
        assert response1.status_code == 201
        
        # Try to register same user again
        response2 = await auth_client.post("/api/v1/auth/register", json=test_user_data)
        assert response2.status_code == 409  # Conflict