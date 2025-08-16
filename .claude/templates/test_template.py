"""
Test Template for Multi-Tenant AI Platform
Use this template when creating new test files
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from unittest.mock import AsyncMock, patch

# Import test fixtures
from tests.fixtures.auth_fixtures import auth_fixtures, test_user_data
from tests.fixtures.common_fixtures import db_session, redis_client
from tests.conftest import async_client

# Import models and dependencies being tested
from your_service.models import YourFeature
from your_service.endpoints import create_your_feature

class TestYourFeature:
    """Test suite for your feature with multi-tenant isolation"""
    
    @pytest.mark.asyncio
    async def test_create_feature_success(
        self, 
        async_client: AsyncClient,
        auth_fixtures: dict,
        db_session: AsyncSession
    ):
        """Test successful feature creation"""
        # Arrange
        creator_id = "test-creator-1"
        token = auth_fixtures["valid_token"]
        
        request_data = {
            "name": "Test Feature",
            "creator_id": creator_id
        }
        
        # Act
        response = await async_client.post(
            "/api/v1/your-feature",
            json=request_data,
            headers={"Authorization": f"Bearer {token}"}
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Test Feature"
        assert data["creator_id"] == creator_id
        assert "id" in data
        assert "created_at" in data
        
        # Verify database persistence
        feature = await db_session.get(YourFeature, data["id"])
        assert feature is not None
        assert feature.creator_id == creator_id
    
    @pytest.mark.asyncio
    async def test_create_feature_unauthorized(self, async_client: AsyncClient):
        """Test feature creation without authentication"""
        # Arrange
        request_data = {
            "name": "Test Feature",
            "creator_id": "test-creator-1"
        }
        
        # Act
        response = await async_client.post(
            "/api/v1/your-feature",
            json=request_data
            # No Authorization header
        )
        
        # Assert
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_create_feature_forbidden_cross_tenant(
        self,
        async_client: AsyncClient,
        auth_fixtures: dict
    ):
        """Test that users cannot create features for other creators"""
        # Arrange
        token = auth_fixtures["valid_token"]  # Token for creator1
        different_creator_id = "different-creator-2"
        
        request_data = {
            "name": "Test Feature",
            "creator_id": different_creator_id  # Different creator
        }
        
        # Act
        response = await async_client.post(
            "/api/v1/your-feature",
            json=request_data,
            headers={"Authorization": f"Bearer {token}"}
        )
        
        # Assert
        assert response.status_code == 403
        assert "Access denied" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_get_feature_success(
        self,
        async_client: AsyncClient,
        auth_fixtures: dict,
        db_session: AsyncSession
    ):
        """Test successful feature retrieval"""
        # Arrange - Create test feature
        creator_id = "test-creator-1"
        token = auth_fixtures["valid_token"]
        
        feature = YourFeature(
            name="Test Feature",
            creator_id=creator_id
        )
        db_session.add(feature)
        await db_session.commit()
        await db_session.refresh(feature)
        
        # Act
        response = await async_client.get(
            f"/api/v1/your-feature/{feature.id}",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(feature.id)
        assert data["name"] == "Test Feature"
        assert data["creator_id"] == creator_id
    
    @pytest.mark.asyncio
    async def test_get_feature_not_found(
        self,
        async_client: AsyncClient,
        auth_fixtures: dict
    ):
        """Test feature retrieval with non-existent ID"""
        # Arrange
        token = auth_fixtures["valid_token"]
        non_existent_id = "00000000-0000-0000-0000-000000000000"
        
        # Act
        response = await async_client.get(
            f"/api/v1/your-feature/{non_existent_id}",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        # Assert
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    @pytest.mark.asyncio
    async def test_multi_tenant_isolation(
        self,
        async_client: AsyncClient,
        auth_fixtures: dict,
        db_session: AsyncSession
    ):
        """Test that creators can only see their own features"""
        # Arrange - Create features for different creators
        creator1_id = "creator-1"
        creator2_id = "creator-2"
        
        feature1 = YourFeature(name="Creator 1 Feature", creator_id=creator1_id)
        feature2 = YourFeature(name="Creator 2 Feature", creator_id=creator2_id)
        
        db_session.add_all([feature1, feature2])
        await db_session.commit()
        await db_session.refresh(feature1)
        await db_session.refresh(feature2)
        
        # Act - Creator 1 tries to access Creator 2's feature
        token1 = auth_fixtures["creator1_token"]
        response = await async_client.get(
            f"/api/v1/your-feature/{feature2.id}",
            headers={"Authorization": f"Bearer {token1}"}
        )
        
        # Assert - Should not find the feature (due to RLS)
        assert response.status_code == 404
    
    @pytest.mark.asyncio
    async def test_validation_errors(self, async_client: AsyncClient, auth_fixtures: dict):
        """Test input validation"""
        # Arrange
        token = auth_fixtures["valid_token"]
        
        invalid_requests = [
            {},  # Missing required fields
            {"name": ""},  # Empty name
            {"name": "Valid Name"},  # Missing creator_id
            {"creator_id": "valid-creator"},  # Missing name
            {"name": "x" * 300, "creator_id": "valid-creator"},  # Name too long
        ]
        
        for invalid_request in invalid_requests:
            # Act
            response = await async_client.post(
                "/api/v1/your-feature",
                json=invalid_request,
                headers={"Authorization": f"Bearer {token}"}
            )
            
            # Assert
            assert response.status_code == 422  # Validation error

# Integration test class
class TestYourFeatureIntegration:
    """Integration tests for your feature"""
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_feature_lifecycle(
        self,
        async_client: AsyncClient,
        auth_fixtures: dict,
        db_session: AsyncSession
    ):
        """Test complete feature lifecycle"""
        creator_id = "test-creator-1"
        token = auth_fixtures["valid_token"]
        
        # Create feature
        create_response = await async_client.post(
            "/api/v1/your-feature",
            json={"name": "Lifecycle Test", "creator_id": creator_id},
            headers={"Authorization": f"Bearer {token}"}
        )
        assert create_response.status_code == 200
        feature_id = create_response.json()["id"]
        
        # Read feature
        get_response = await async_client.get(
            f"/api/v1/your-feature/{feature_id}",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert get_response.status_code == 200
        assert get_response.json()["name"] == "Lifecycle Test"
        
        # Verify in database
        feature = await db_session.get(YourFeature, feature_id)
        assert feature is not None
        assert feature.creator_id == creator_id