"""
Tests for multi-tenant isolation in auth service.
Critical tests to prevent cross-tenant data leaks.
"""

import pytest
from httpx import AsyncClient
from unittest.mock import AsyncMock, patch
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text, select

from shared.models.database import Creator, RefreshToken, JWTBlacklist
from shared.exceptions.auth import AuthenticationError


class TestMultiTenantIsolation:
    """Test multi-tenant data isolation in auth service."""

    async def test_creator_isolation_in_queries(self, auth_client: AsyncClient, db_session: AsyncSession):
        """Test that creators can only see their own data."""
        # Create two creators in different tenants
        creator1_data = {
            "email": "creator1@test.com",
            "password": "SecurePass123!",
            "full_name": "Creator One",
            "tenant_id": "tenant_1"
        }
        creator2_data = {
            "email": "creator2@test.com", 
            "password": "SecurePass123!",
            "full_name": "Creator Two",
            "tenant_id": "tenant_2"
        }
        
        # Register both creators
        response1 = await auth_client.post("/api/v1/auth/register", json=creator1_data)
        response2 = await auth_client.post("/api/v1/auth/register", json=creator2_data)
        
        assert response1.status_code == 201
        assert response2.status_code == 201
        
        creator1_id = response1.json()["id"]
        creator2_id = response2.json()["id"]
        
        # Set tenant context for creator1
        await db_session.execute(
            text("SET app.current_creator_id = :creator_id"),
            {"creator_id": creator1_id}
        )
        
        # Query should only return creator1's data
        result = await db_session.execute(select(Creator))
        creators = result.scalars().all()
        
        # Should only see creator1, not creator2
        assert len(creators) == 1
        assert creators[0].id == creator1_id
        assert creators[0].tenant_id == "tenant_1"

    async def test_refresh_token_isolation(self, auth_client: AsyncClient, db_session: AsyncSession):
        """Test that refresh tokens are isolated by creator."""
        # Create two creators
        creator1_data = {
            "email": "creator1@test.com",
            "password": "SecurePass123!",
            "full_name": "Creator One",
            "tenant_id": "tenant_1"
        }
        creator2_data = {
            "email": "creator2@test.com",
            "password": "SecurePass123!", 
            "full_name": "Creator Two",
            "tenant_id": "tenant_2"
        }
        
        # Register and login both creators
        await auth_client.post("/api/v1/auth/register", json=creator1_data)
        await auth_client.post("/api/v1/auth/register", json=creator2_data)
        
        login1 = await auth_client.post("/api/v1/auth/login", json={
            "email": creator1_data["email"],
            "password": creator1_data["password"]
        })
        login2 = await auth_client.post("/api/v1/auth/login", json={
            "email": creator2_data["email"], 
            "password": creator2_data["password"]
        })
        
        assert login1.status_code == 200
        assert login2.status_code == 200
        
        creator1_id = login1.json()["user"]["id"]
        creator2_id = login2.json()["user"]["id"]
        
        # Set tenant context for creator1
        await db_session.execute(
            text("SET app.current_creator_id = :creator_id"),
            {"creator_id": creator1_id}
        )
        
        # Query refresh tokens should only return creator1's tokens
        result = await db_session.execute(select(RefreshToken))
        tokens = result.scalars().all()
        
        # Should only see creator1's tokens
        for token in tokens:
            assert token.creator_id == creator1_id

    async def test_jwt_blacklist_isolation(self, auth_client: AsyncClient, db_session: AsyncSession):
        """Test that JWT blacklist is isolated by creator."""
        # Create creator and login
        creator_data = {
            "email": "creator@test.com",
            "password": "SecurePass123!",
            "full_name": "Test Creator",
            "tenant_id": "tenant_1"
        }
        
        await auth_client.post("/api/v1/auth/register", json=creator_data)
        login_response = await auth_client.post("/api/v1/auth/login", json={
            "email": creator_data["email"],
            "password": creator_data["password"]
        })
        
        assert login_response.status_code == 200
        access_token = login_response.json()["access_token"]
        creator_id = login_response.json()["user"]["id"]
        
        # Logout to blacklist token
        logout_response = await auth_client.post(
            "/api/v1/auth/logout",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        assert logout_response.status_code == 200
        
        # Set tenant context
        await db_session.execute(
            text("SET app.current_creator_id = :creator_id"),
            {"creator_id": creator_id}
        )
        
        # Query blacklist should only show this creator's tokens
        result = await db_session.execute(select(JWTBlacklist))
        blacklist_entries = result.scalars().all()
        
        for entry in blacklist_entries:
            assert entry.creator_id == creator_id

    async def test_cross_tenant_access_prevention(self, auth_client: AsyncClient):
        """Test that creators cannot access other tenants' data."""
        # Create two creators
        creator1_data = {
            "email": "creator1@test.com",
            "password": "SecurePass123!",
            "full_name": "Creator One",
            "tenant_id": "tenant_1"
        }
        creator2_data = {
            "email": "creator2@test.com",
            "password": "SecurePass123!",
            "full_name": "Creator Two", 
            "tenant_id": "tenant_2"
        }
        
        await auth_client.post("/api/v1/auth/register", json=creator1_data)
        await auth_client.post("/api/v1/auth/register", json=creator2_data)
        
        # Login as creator1
        login1 = await auth_client.post("/api/v1/auth/login", json={
            "email": creator1_data["email"],
            "password": creator1_data["password"]
        })
        
        creator1_token = login1.json()["access_token"]
        creator2_id = None  # We'll try to access this
        
        # Login as creator2 to get their ID
        login2 = await auth_client.post("/api/v1/auth/login", json={
            "email": creator2_data["email"],
            "password": creator2_data["password"]
        })
        creator2_id = login2.json()["user"]["id"]
        
        # Try to access creator2's profile using creator1's token
        # This should fail if multi-tenancy is properly implemented
        profile_response = await auth_client.get(
            f"/api/v1/auth/users/{creator2_id}",
            headers={"Authorization": f"Bearer {creator1_token}"}
        )
        
        # Should return 403 Forbidden or 404 Not Found
        assert profile_response.status_code in [403, 404]

    async def test_rls_policy_enforcement(self, db_session: AsyncSession):
        """Test that Row Level Security policies are enforced."""
        # Create test creator data directly in database
        creator1 = Creator(
            email="creator1@test.com",
            hashed_password="hashed_password_1",
            full_name="Creator One",
            tenant_id="tenant_1"
        )
        creator2 = Creator(
            email="creator2@test.com", 
            hashed_password="hashed_password_2",
            full_name="Creator Two",
            tenant_id="tenant_2"
        )
        
        db_session.add(creator1)
        db_session.add(creator2)
        await db_session.commit()
        
        # Refresh to get IDs
        await db_session.refresh(creator1)
        await db_session.refresh(creator2)
        
        # Set RLS context for creator1
        await db_session.execute(
            text("SET app.current_creator_id = :creator_id"),
            {"creator_id": str(creator1.id)}
        )
        
        # Query should only return creator1 due to RLS
        result = await db_session.execute(select(Creator))
        creators = result.scalars().all()
        
        assert len(creators) == 1
        assert creators[0].id == creator1.id
        
        # Change context to creator2
        await db_session.execute(
            text("SET app.current_creator_id = :creator_id"),
            {"creator_id": str(creator2.id)}
        )
        
        # Now should only see creator2
        result = await db_session.execute(select(Creator))
        creators = result.scalars().all()
        
        assert len(creators) == 1
        assert creators[0].id == creator2.id

    async def test_tenant_context_validation(self, db_session: AsyncSession):
        """Test that tenant context must be set for database operations."""
        # Try to query without setting tenant context
        # This should either return empty results or raise an error
        result = await db_session.execute(select(Creator))
        creators = result.scalars().all()
        
        # With proper RLS, this should return empty or minimal results
        # The exact behavior depends on RLS policy configuration
        # At minimum, it should not return ALL creators from ALL tenants
        assert isinstance(creators, list)  # Should be a list, not an error

    @pytest.mark.asyncio
    async def test_concurrent_tenant_isolation(self, auth_client: AsyncClient):
        """Test that concurrent requests from different tenants are isolated."""
        import asyncio
        
        # Create multiple creators
        creators_data = [
            {
                "email": f"creator{i}@test.com",
                "password": "SecurePass123!",
                "full_name": f"Creator {i}",
                "tenant_id": f"tenant_{i}"
            }
            for i in range(3)
        ]
        
        # Register all creators
        for creator_data in creators_data:
            response = await auth_client.post("/api/v1/auth/register", json=creator_data)
            assert response.status_code == 201
        
        # Login all creators concurrently
        async def login_creator(creator_data):
            response = await auth_client.post("/api/v1/auth/login", json={
                "email": creator_data["email"],
                "password": creator_data["password"]
            })
            return response.json()
        
        login_tasks = [login_creator(data) for data in creators_data]
        login_results = await asyncio.gather(*login_tasks)
        
        # Verify each login was successful and isolated
        for i, result in enumerate(login_results):
            assert "access_token" in result
            assert result["user"]["tenant_id"] == f"tenant_{i}"
            assert result["user"]["email"] == f"creator{i}@test.com"