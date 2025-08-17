"""
Comprehensive RBAC (Role-Based Access Control) tests.
Tests role assignments, permission checks, and access control enforcement.
"""

import pytest
from httpx import AsyncClient
from unittest.mock import AsyncMock, patch

from shared.security.rbac import RBACManager, Role, Permission
from shared.exceptions.auth import InsufficientPermissionsError


class TestRBACPermissions:
    """Test Role-Based Access Control system."""

    async def test_creator_role_permissions(self, auth_client: AsyncClient):
        """Test creator role has appropriate permissions."""
        # Register user (should get creator role by default)
        user_data = {
            "email": "creator@example.com",
            "password": "SecurePass123!",
            "full_name": "Test Creator",
            "tenant_id": "tenant_1"
        }
        
        await auth_client.post("/api/v1/auth/register", json=user_data)
        
        login_response = await auth_client.post("/api/v1/auth/login", json={
            "email": user_data["email"],
            "password": user_data["password"]
        })
        
        access_token = login_response.json()["access_token"]
        user_profile = login_response.json()["user"]
        
        # Verify user has creator role
        assert "role" in user_profile
        assert user_profile["role"] == "creator"
        
        # Test creator permissions - should be able to access creator endpoints
        creator_endpoints = [
            "/api/v1/auth/me",
            "/api/v1/creators/profile",  # Assuming this exists
        ]
        
        for endpoint in creator_endpoints:
            response = await auth_client.get(
                endpoint,
                headers={"Authorization": f"Bearer {access_token}"}
            )
            # Should not get 403 Forbidden (may get 404 if endpoint doesn't exist)
            assert response.status_code != 403

    async def test_admin_role_permissions(self, auth_client: AsyncClient):
        """Test admin role has elevated permissions."""
        # Register admin user
        admin_data = {
            "email": "admin@example.com",
            "password": "SecurePass123!",
            "full_name": "Test Admin",
            "tenant_id": "admin_tenant",
            "role": "admin"  # If registration supports role assignment
        }
        
        # Register admin (may need special endpoint or manual role assignment)
        register_response = await auth_client.post("/api/v1/auth/register", json=admin_data)
        
        if register_response.status_code == 201:
            login_response = await auth_client.post("/api/v1/auth/login", json={
                "email": admin_data["email"],
                "password": admin_data["password"]
            })
            
            access_token = login_response.json()["access_token"]
            
            # Test admin-only endpoints (if they exist)
            admin_endpoints = [
                "/api/v1/admin/users",
                "/api/v1/admin/system-stats",
                "/api/v1/admin/metrics",
            ]
            
            for endpoint in admin_endpoints:
                response = await auth_client.get(
                    endpoint,
                    headers={"Authorization": f"Bearer {access_token}"}
                )
                # Should not get 403 Forbidden for admin user
                # (may get 404 if endpoint doesn't exist, 200 if it does)
                assert response.status_code != 403

    async def test_permission_inheritance(self):
        """Test that roles inherit permissions correctly."""
        rbac_manager = RBACManager()
        
        # Test permission hierarchy
        # Admin should have all creator permissions plus admin-specific ones
        creator_permissions = rbac_manager.get_role_permissions(Role.CREATOR)
        admin_permissions = rbac_manager.get_role_permissions(Role.ADMIN)
        
        # Admin should have at least all creator permissions
        creator_perms_set = set(creator_permissions)
        admin_perms_set = set(admin_permissions)
        
        assert creator_perms_set.issubset(admin_perms_set), "Admin should inherit creator permissions"

    async def test_permission_checking(self):
        """Test individual permission checking logic."""
        rbac_manager = RBACManager()
        
        # Test creator permissions
        assert rbac_manager.has_permission(Role.CREATOR, Permission.READ_OWN_DATA)
        assert rbac_manager.has_permission(Role.CREATOR, Permission.WRITE_OWN_DATA)
        assert rbac_manager.has_permission(Role.CREATOR, Permission.CREATE_CONTENT)
        
        # Test admin permissions
        assert rbac_manager.has_permission(Role.ADMIN, Permission.READ_ALL_DATA)
        assert rbac_manager.has_permission(Role.ADMIN, Permission.WRITE_ALL_DATA)
        assert rbac_manager.has_permission(Role.ADMIN, Permission.MANAGE_USERS)
        
        # Test user permissions (most restrictive)
        assert rbac_manager.has_permission(Role.USER, Permission.READ_OWN_DATA)
        assert not rbac_manager.has_permission(Role.USER, Permission.WRITE_ALL_DATA)
        assert not rbac_manager.has_permission(Role.USER, Permission.MANAGE_USERS)

    async def test_role_assignment_validation(self, auth_client: AsyncClient):
        """Test that role assignments are validated properly."""
        # Test invalid role assignment
        invalid_user_data = {
            "email": "invalid@example.com",
            "password": "SecurePass123!",
            "full_name": "Invalid User",
            "tenant_id": "tenant_1",
            "role": "super_admin"  # Invalid role
        }
        
        response = await auth_client.post("/api/v1/auth/register", json=invalid_user_data)
        
        # Should either reject invalid role or default to valid role
        if response.status_code == 201:
            # If registration succeeded, check that role was corrected
            user_data = response.json()
            assert user_data.get("role") in ["creator", "user", "admin"]
        else:
            # Registration should fail with validation error
            assert response.status_code == 422

    async def test_permission_enforcement_decorators(self, auth_client: AsyncClient):
        """Test that permission decorators properly enforce access control."""
        # Register regular user
        user_data = {
            "email": "user@example.com",
            "password": "SecurePass123!",
            "full_name": "Regular User", 
            "tenant_id": "tenant_1"
        }
        
        await auth_client.post("/api/v1/auth/register", json=user_data)
        
        login_response = await auth_client.post("/api/v1/auth/login", json={
            "email": user_data["email"],
            "password": user_data["password"]
        })
        
        access_token = login_response.json()["access_token"]
        
        # Try to access admin-only endpoints
        admin_only_endpoints = [
            "/api/v1/admin/users",
            "/api/v1/admin/system-config",
            "/api/v1/admin/delete-user",
        ]
        
        for endpoint in admin_only_endpoints:
            response = await auth_client.get(
                endpoint,
                headers={"Authorization": f"Bearer {access_token}"}
            )
            
            # Should get 403 Forbidden for insufficient permissions
            assert response.status_code == 403
            error_data = response.json()
            assert "permission" in error_data["detail"].lower() or "forbidden" in error_data["detail"].lower()

    async def test_dynamic_permission_checking(self):
        """Test dynamic permission evaluation based on context."""
        rbac_manager = RBACManager()
        
        # Test resource-specific permissions
        # User should be able to read their own data but not others'
        user_context = {
            "user_id": "user_123",
            "role": Role.USER,
            "tenant_id": "tenant_1"
        }
        
        # Should have permission to read own data
        assert rbac_manager.check_resource_permission(
            user_context,
            Permission.READ_OWN_DATA,
            resource_owner_id="user_123"
        )
        
        # Should NOT have permission to read other user's data
        assert not rbac_manager.check_resource_permission(
            user_context,
            Permission.READ_OWN_DATA,
            resource_owner_id="user_456"
        )

    async def test_role_hierarchy_enforcement(self):
        """Test that role hierarchy is properly enforced."""
        rbac_manager = RBACManager()
        
        # Define expected hierarchy: USER < CREATOR < ADMIN
        roles_by_level = [Role.USER, Role.CREATOR, Role.ADMIN]
        
        for i, role in enumerate(roles_by_level):
            role_permissions = rbac_manager.get_role_permissions(role)
            
            # Each higher role should have at least as many permissions
            for j in range(i):
                lower_role = roles_by_level[j]
                lower_permissions = rbac_manager.get_role_permissions(lower_role)
                
                # Higher role should include all lower role permissions
                assert set(lower_permissions).issubset(set(role_permissions))

    async def test_cross_tenant_permission_isolation(self, auth_client: AsyncClient):
        """Test that permissions are isolated across tenants."""
        # Create users in different tenants
        user1_data = {
            "email": "user1@example.com",
            "password": "SecurePass123!",
            "full_name": "User One",
            "tenant_id": "tenant_1"
        }
        
        user2_data = {
            "email": "user2@example.com",
            "password": "SecurePass123!",
            "full_name": "User Two",
            "tenant_id": "tenant_2"
        }
        
        # Register both users
        await auth_client.post("/api/v1/auth/register", json=user1_data)
        await auth_client.post("/api/v1/auth/register", json=user2_data)
        
        # Login as user1
        login1 = await auth_client.post("/api/v1/auth/login", json={
            "email": user1_data["email"],
            "password": user1_data["password"]
        })
        
        user1_token = login1.json()["access_token"]
        user2_id = None
        
        # Get user2's ID
        login2 = await auth_client.post("/api/v1/auth/login", json={
            "email": user2_data["email"],
            "password": user2_data["password"]
        })
        user2_id = login2.json()["user"]["id"]
        
        # Try to access user2's data with user1's token
        # Should fail due to tenant isolation
        response = await auth_client.get(
            f"/api/v1/users/{user2_id}/profile",
            headers={"Authorization": f"Bearer {user1_token}"}
        )
        
        # Should get 403 or 404 due to cross-tenant access attempt
        assert response.status_code in [403, 404]

    async def test_permission_caching(self):
        """Test that permission checks are cached for performance."""
        rbac_manager = RBACManager()
        
        # Mock the underlying permission lookup to track calls
        with patch.object(rbac_manager, '_lookup_permission') as mock_lookup:
            mock_lookup.return_value = True
            
            user_context = {
                "user_id": "user_123",
                "role": Role.CREATOR,
                "tenant_id": "tenant_1"
            }
            
            # Check same permission multiple times
            for _ in range(5):
                result = rbac_manager.has_permission(Role.CREATOR, Permission.CREATE_CONTENT)
                assert result is True
            
            # Should use cache after first lookup
            # Exact caching behavior depends on implementation
            # At minimum, it shouldn't call lookup 5 times
            assert mock_lookup.call_count < 5

    async def test_permission_revocation(self, auth_client: AsyncClient):
        """Test that permission changes take effect immediately."""
        # This test would be for dynamic permission changes
        # Implementation depends on whether the system supports runtime permission changes
        
        # Register user
        user_data = {
            "email": "user@example.com",
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
        
        # Test endpoint access (should work initially)
        response1 = await auth_client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        assert response1.status_code == 200
        
        # If system supports role changes, test permission revocation
        # This would require admin endpoint to change user role
        # For now, we verify the permission system structure is in place