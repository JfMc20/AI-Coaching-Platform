"""
Tests for shared security components.
Tests JWT manager, RBAC, GDPR compliance, and password security.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, Mock, patch
from datetime import datetime, timedelta
import jwt


class TestJWTManager:
    """Test JWT token management."""

    def test_jwt_manager_initialization(self):
        """Test JWT manager initialization."""
        try:
            from shared.security.jwt_manager import JWTManager
            
            manager = JWTManager(
                secret_key="test-secret-key",
                algorithm="HS256",
                access_token_expire_minutes=15
            )
            
            assert manager.secret_key == "test-secret-key"
            assert manager.algorithm == "HS256"
            assert manager.access_token_expire_minutes == 15
            
        except ImportError:
            pytest.skip("JWTManager not available")

    def test_create_access_token(self):
        """Test access token creation."""
        try:
            from shared.security.jwt_manager import JWTManager
            
            manager = JWTManager(
                secret_key="test-secret-key",
                algorithm="HS256"
            )
            
            # Create token
            token = manager.create_access_token(
                creator_id="test_creator",
                permissions=["read", "write"]
            )
            
            assert isinstance(token, str)
            assert len(token) > 0
            
            # Verify token can be decoded
            decoded = jwt.decode(token, "test-secret-key", algorithms=["HS256"])
            assert decoded["creator_id"] == "test_creator"
            assert decoded["permissions"] == ["read", "write"]
            
        except ImportError:
            pytest.skip("JWTManager not available")

    def test_create_refresh_token(self):
        """Test refresh token creation."""
        try:
            from shared.security.jwt_manager import JWTManager
            
            manager = JWTManager(
                secret_key="test-secret-key",
                algorithm="HS256"
            )
            
            # Create refresh token
            token = manager.create_refresh_token(creator_id="test_creator")
            
            assert isinstance(token, str)
            assert len(token) > 0
            
            # Verify token
            decoded = jwt.decode(token, "test-secret-key", algorithms=["HS256"])
            assert decoded["creator_id"] == "test_creator"
            assert decoded["token_type"] == "refresh"
            
        except ImportError:
            pytest.skip("JWTManager not available")

    def test_verify_token(self):
        """Test token verification."""
        try:
            from shared.security.jwt_manager import JWTManager
            
            manager = JWTManager(
                secret_key="test-secret-key",
                algorithm="HS256"
            )
            
            # Create and verify token
            token = manager.create_access_token(
                creator_id="test_creator",
                permissions=["read"]
            )
            
            payload = manager.verify_token(token)
            assert payload["creator_id"] == "test_creator"
            assert payload["permissions"] == ["read"]
            
        except ImportError:
            pytest.skip("JWTManager not available")

    def test_verify_expired_token(self):
        """Test verification of expired token."""
        try:
            from shared.security.jwt_manager import JWTManager, SecurityError
            
            manager = JWTManager(
                secret_key="test-secret-key",
                algorithm="HS256",
                access_token_expire_minutes=-1  # Already expired
            )
            
            # Create expired token
            token = manager.create_access_token(
                creator_id="test_creator",
                permissions=["read"]
            )
            
            # Verification should fail
            with pytest.raises(SecurityError, match="expired"):
                manager.verify_token(token)
                
        except ImportError:
            pytest.skip("JWTManager not available")

    def test_verify_invalid_token(self):
        """Test verification of invalid token."""
        try:
            from shared.security.jwt_manager import JWTManager, SecurityError
            
            manager = JWTManager(
                secret_key="test-secret-key",
                algorithm="HS256"
            )
            
            # Try to verify invalid token
            with pytest.raises(SecurityError):
                manager.verify_token("invalid.token.here")
                
        except ImportError:
            pytest.skip("JWTManager not available")

    def test_refresh_access_token(self):
        """Test access token refresh."""
        try:
            from shared.security.jwt_manager import JWTManager
            
            manager = JWTManager(
                secret_key="test-secret-key",
                algorithm="HS256"
            )
            
            # Create refresh token
            refresh_token = manager.create_refresh_token(creator_id="test_creator")
            
            # Mock permission retrieval
            with patch.object(manager, '_get_creator_permissions') as mock_perms:
                mock_perms.return_value = ["read", "write"]
                
                # Refresh access token
                new_token = manager.refresh_access_token(refresh_token)
                
                assert isinstance(new_token, str)
                assert len(new_token) > 0
                
                # Verify new token
                payload = manager.verify_token(new_token)
                assert payload["creator_id"] == "test_creator"
                
        except ImportError:
            pytest.skip("JWTManager not available")


class TestPasswordSecurity:
    """Test password security functions."""

    def test_password_manager_initialization(self):
        """Test password manager initialization."""
        try:
            from shared.security.password_security import PasswordManager
            
            manager = PasswordManager()
            assert manager is not None
            assert manager.min_length >= 8
            
        except ImportError:
            pytest.skip("PasswordManager not available")

    def test_hash_password(self):
        """Test password hashing."""
        try:
            from shared.security.password_security import PasswordManager
            
            manager = PasswordManager()
            
            password = "TestPassword123!"
            hashed = manager.hash_password(password)
            
            assert isinstance(hashed, str)
            assert len(hashed) > 0
            assert hashed != password  # Should be hashed
            
        except ImportError:
            pytest.skip("PasswordManager not available")

    def test_verify_password(self):
        """Test password verification."""
        try:
            from shared.security.password_security import PasswordManager
            
            manager = PasswordManager()
            
            password = "TestPassword123!"
            hashed = manager.hash_password(password)
            
            # Correct password should verify
            assert manager.verify_password(password, hashed) is True
            
            # Wrong password should not verify
            assert manager.verify_password("WrongPassword", hashed) is False
            
        except ImportError:
            pytest.skip("PasswordManager not available")

    def test_validate_password_strength(self):
        """Test password strength validation."""
        try:
            from shared.security.password_security import PasswordManager
            
            manager = PasswordManager()
            
            # Strong password should pass
            strong_password = "StrongP@ssw0rd123"
            manager.validate_password_strength(strong_password)  # Should not raise
            
            # Weak password should fail
            with pytest.raises(Exception):  # ValidationError or similar
                manager.validate_password_strength("weak")
                
        except ImportError:
            pytest.skip("PasswordManager not available")

    def test_generate_secure_password(self):
        """Test secure password generation."""
        try:
            from shared.security.password_security import PasswordManager
            
            manager = PasswordManager()
            
            # Generate password
            password = manager.generate_secure_password(length=16)
            
            assert isinstance(password, str)
            assert len(password) == 16
            
            # Should pass strength validation
            manager.validate_password_strength(password)
            
        except ImportError:
            pytest.skip("PasswordManager not available")


class TestRBAC:
    """Test Role-Based Access Control."""

    def test_rbac_manager_initialization(self):
        """Test RBAC manager initialization."""
        try:
            from shared.security.rbac import RBACManager
            
            manager = RBACManager()
            assert manager is not None
            
        except ImportError:
            pytest.skip("RBACManager not available")

    def test_create_role(self):
        """Test role creation."""
        try:
            from shared.security.rbac import RBACManager
            
            manager = RBACManager()
            
            # Create role
            role = manager.create_role(
                name="test_role",
                permissions=["read", "write"]
            )
            
            assert role["name"] == "test_role"
            assert "read" in role["permissions"]
            assert "write" in role["permissions"]
            
        except ImportError:
            pytest.skip("RBACManager not available")

    def test_assign_role_to_user(self):
        """Test role assignment."""
        try:
            from shared.security.rbac import RBACManager
            
            manager = RBACManager()
            
            # Create role first
            role = manager.create_role("test_role", ["read"])
            
            # Assign role to user
            result = manager.assign_role_to_user("user_123", "test_role")
            assert result is True
            
        except ImportError:
            pytest.skip("RBACManager not available")

    def test_check_permission(self):
        """Test permission checking."""
        try:
            from shared.security.rbac import RBACManager
            
            manager = RBACManager()
            
            # Create role and assign to user
            manager.create_role("test_role", ["read", "write"])
            manager.assign_role_to_user("user_123", "test_role")
            
            # Check permissions
            assert manager.check_permission("user_123", "read") is True
            assert manager.check_permission("user_123", "write") is True
            assert manager.check_permission("user_123", "delete") is False
            
        except ImportError:
            pytest.skip("RBACManager not available")

    def test_revoke_role_from_user(self):
        """Test role revocation."""
        try:
            from shared.security.rbac import RBACManager
            
            manager = RBACManager()
            
            # Create role and assign to user
            manager.create_role("test_role", ["read"])
            manager.assign_role_to_user("user_123", "test_role")
            
            # Revoke role
            result = manager.revoke_role_from_user("user_123", "test_role")
            assert result is True
            
            # Permission should no longer exist
            assert manager.check_permission("user_123", "read") is False
            
        except ImportError:
            pytest.skip("RBACManager not available")

    def test_get_user_permissions(self):
        """Test getting user permissions."""
        try:
            from shared.security.rbac import RBACManager
            
            manager = RBACManager()
            
            # Create roles and assign to user
            manager.create_role("role1", ["read", "write"])
            manager.create_role("role2", ["delete"])
            manager.assign_role_to_user("user_123", "role1")
            manager.assign_role_to_user("user_123", "role2")
            
            # Get all permissions
            permissions = manager.get_user_permissions("user_123")
            
            assert "read" in permissions
            assert "write" in permissions
            assert "delete" in permissions
            
        except ImportError:
            pytest.skip("RBACManager not available")


class TestGDPRCompliance:
    """Test GDPR compliance functions."""

    def test_gdpr_manager_initialization(self):
        """Test GDPR manager initialization."""
        try:
            from shared.security.gdpr_compliance import GDPRManager
            
            manager = GDPRManager()
            assert manager is not None
            
        except ImportError:
            pytest.skip("GDPRManager not available")

    def test_anonymize_personal_data(self):
        """Test personal data anonymization."""
        try:
            from shared.security.gdpr_compliance import GDPRManager
            
            manager = GDPRManager()
            
            # Test data anonymization
            personal_data = {
                "email": "user@example.com",
                "name": "John Doe",
                "phone": "+1234567890",
                "non_personal": "some_value"
            }
            
            anonymized = manager.anonymize_personal_data(personal_data)
            
            # Personal data should be anonymized
            assert anonymized["email"] != "user@example.com"
            assert anonymized["name"] != "John Doe"
            assert anonymized["phone"] != "+1234567890"
            
            # Non-personal data should remain
            assert anonymized["non_personal"] == "some_value"
            
        except ImportError:
            pytest.skip("GDPRManager not available")

    def test_data_export(self):
        """Test data export for GDPR requests."""
        try:
            from shared.security.gdpr_compliance import GDPRManager
            
            manager = GDPRManager()
            
            # Mock database query
            with patch.object(manager, '_get_user_data') as mock_get_data:
                mock_get_data.return_value = {
                    "profile": {"name": "John Doe", "email": "john@example.com"},
                    "conversations": [{"id": "conv_1", "content": "Hello"}],
                    "documents": [{"id": "doc_1", "filename": "test.pdf"}]
                }
                
                export_data = manager.export_user_data("user_123")
                
                assert "profile" in export_data
                assert "conversations" in export_data
                assert "documents" in export_data
                assert export_data["profile"]["name"] == "John Doe"
                
        except ImportError:
            pytest.skip("GDPRManager not available")

    def test_data_deletion(self):
        """Test data deletion for GDPR requests."""
        try:
            from shared.security.gdpr_compliance import GDPRManager
            
            manager = GDPRManager()
            
            # Mock database operations
            with patch.object(manager, '_delete_user_data') as mock_delete:
                mock_delete.return_value = True
                
                result = manager.delete_user_data("user_123")
                assert result is True
                mock_delete.assert_called_once_with("user_123")
                
        except ImportError:
            pytest.skip("GDPRManager not available")

    def test_consent_management(self):
        """Test consent management."""
        try:
            from shared.security.gdpr_compliance import GDPRManager
            
            manager = GDPRManager()
            
            # Record consent
            consent_result = manager.record_consent(
                user_id="user_123",
                consent_type="data_processing",
                granted=True
            )
            assert consent_result is True
            
            # Check consent
            has_consent = manager.check_consent("user_123", "data_processing")
            assert has_consent is True
            
            # Revoke consent
            revoke_result = manager.revoke_consent("user_123", "data_processing")
            assert revoke_result is True
            
            # Check consent after revocation
            has_consent_after = manager.check_consent("user_123", "data_processing")
            assert has_consent_after is False
            
        except ImportError:
            pytest.skip("GDPRManager not available")

    def test_data_retention_policy(self):
        """Test data retention policy enforcement."""
        try:
            from shared.security.gdpr_compliance import GDPRManager
            
            manager = GDPRManager()
            
            # Mock expired data identification
            with patch.object(manager, '_find_expired_data') as mock_find:
                mock_find.return_value = ["data_1", "data_2", "data_3"]
                
                with patch.object(manager, '_delete_expired_data') as mock_delete:
                    mock_delete.return_value = 3
                    
                    deleted_count = manager.enforce_retention_policy()
                    assert deleted_count == 3
                    
        except ImportError:
            pytest.skip("GDPRManager not available")


class TestSecurityIntegration:
    """Test security component integration."""

    def test_security_middleware_initialization(self):
        """Test security middleware initialization."""
        try:
            from shared.security import SecurityMiddleware
            
            middleware = SecurityMiddleware()
            assert middleware is not None
            
        except ImportError:
            pytest.skip("SecurityMiddleware not available")

    def test_authentication_flow(self):
        """Test complete authentication flow."""
        try:
            from shared.security.jwt_manager import JWTManager
            from shared.security.password_security import PasswordManager
            
            jwt_manager = JWTManager(secret_key="test-secret")
            password_manager = PasswordManager()
            
            # Simulate user registration
            password = "TestPassword123!"
            hashed_password = password_manager.hash_password(password)
            
            # Simulate login
            is_valid = password_manager.verify_password(password, hashed_password)
            assert is_valid is True
            
            # Create token after successful login
            token = jwt_manager.create_access_token(
                creator_id="user_123",
                permissions=["read", "write"]
            )
            
            # Verify token
            payload = jwt_manager.verify_token(token)
            assert payload["creator_id"] == "user_123"
            
        except ImportError:
            pytest.skip("Security components not available")

    def test_authorization_flow(self):
        """Test complete authorization flow."""
        try:
            from shared.security.rbac import RBACManager
            from shared.security.jwt_manager import JWTManager
            
            rbac_manager = RBACManager()
            jwt_manager = JWTManager(secret_key="test-secret")
            
            # Setup roles and permissions
            rbac_manager.create_role("user", ["read"])
            rbac_manager.create_role("admin", ["read", "write", "delete"])
            rbac_manager.assign_role_to_user("user_123", "user")
            
            # Create token with permissions
            user_permissions = rbac_manager.get_user_permissions("user_123")
            token = jwt_manager.create_access_token(
                creator_id="user_123",
                permissions=user_permissions
            )
            
            # Verify authorization
            payload = jwt_manager.verify_token(token)
            assert "read" in payload["permissions"]
            assert "write" not in payload["permissions"]
            
        except ImportError:
            pytest.skip("Security components not available")

    def test_security_audit_logging(self):
        """Test security audit logging."""
        try:
            from shared.security import SecurityAuditLogger
            
            logger = SecurityAuditLogger()
            
            # Mock database operations
            with patch.object(logger, '_write_audit_log') as mock_write:
                mock_write.return_value = True
                
                # Log authentication attempt
                logger.log_authentication_attempt(
                    email="test@example.com",
                    success=True,
                    ip_address="127.0.0.1",
                    user_agent="Test Agent"
                )
                
                mock_write.assert_called_once()
                
        except ImportError:
            pytest.skip("SecurityAuditLogger not available")