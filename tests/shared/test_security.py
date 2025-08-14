"""
Tests for security components.
Tests JWT management, password security, RBAC, and GDPR compliance.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
import jwt

from shared.security.jwt_manager import JWTManager
from shared.security.password_security import PasswordSecurity
from shared.security.rbac import RoleBasedAccessControl
from shared.security.gdpr_compliance import GDPRCompliance


class TestJWTManager:
    """Test JWT token management."""

    @pytest.fixture
    def jwt_manager(self):
        """Create JWT manager for testing."""
        import os
        # Use test-safe secret from environment or secure default
        test_secret = os.environ.get("TEST_JWT_SECRET", "test-9a8b7c6d5e4f3a2b1c0d9e8f7a6b5c4d3e2f1a0b9c8d7e6f5a4b3c2d1e0f9a8b7c6d5e4f3a2b1c")
        return JWTManager(
            secret_key=test_secret,
            algorithm="HS256",
            access_token_expire_minutes=30,
            refresh_token_expire_days=7
        )

    def test_create_access_token(self, jwt_manager):
        """Test access token creation."""
        payload = {
            "sub": "user@example.com",
            "user_id": "123",
            "tenant_id": "test-tenant"
        }

        token = jwt_manager.create_access_token(payload)
        
        assert isinstance(token, str)
        assert len(token) > 0
        
        # Verify token can be decoded using test-safe secret
        import os
        test_secret = os.environ.get("TEST_JWT_SECRET", "test-9a8b7c6d5e4f3a2b1c0d9e8f7a6b5c4d3e2f1a0b9c8d7e6f5a4b3c2d1e0f9a8b7c6d5e4f3a2b1c")
        decoded = jwt.decode(token, test_secret, algorithms=["HS256"])
        assert decoded["sub"] == payload["sub"]
        assert decoded["user_id"] == payload["user_id"]
        assert decoded["tenant_id"] == payload["tenant_id"]

    def test_create_refresh_token(self, jwt_manager):
        """Test refresh token creation."""
        payload = {
            "sub": "user@example.com",
            "user_id": "123",
            "tenant_id": "test-tenant"
        }

        token = jwt_manager.create_refresh_token(payload)
        
        assert isinstance(token, str)
        assert len(token) > 0
        
        # Verify token has longer expiration using timezone-aware datetimes
        import os
        from datetime import timezone
        test_secret = os.environ.get("TEST_JWT_SECRET", "test-9a8b7c6d5e4f3a2b1c0d9e8f7a6b5c4d3e2f1a0b9c8d7e6f5a4b3c2d1e0f9a8b7c6d5e4f3a2b1c")
        decoded = jwt.decode(token, test_secret, algorithms=["HS256"])
        exp_time = datetime.fromtimestamp(decoded["exp"], tz=timezone.utc)
        now = datetime.now(timezone.utc)
        
        # Should expire in about 7 days
        assert (exp_time - now).days >= 6

    def test_validate_token_success(self, jwt_manager):
        """Test successful token validation."""
        payload = {
            "sub": "user@example.com",
            "user_id": "123",
            "tenant_id": "test-tenant"
        }

        token = jwt_manager.create_access_token(payload)
        decoded_payload = jwt_manager.validate_token(token)
        
        assert decoded_payload["sub"] == payload["sub"]
        assert decoded_payload["user_id"] == payload["user_id"]
        assert decoded_payload["tenant_id"] == payload["tenant_id"]

    def test_validate_expired_token(self, jwt_manager):
        """Test validation of expired token."""
        payload = {
            "sub": "user@example.com",
            "user_id": "123",
            "tenant_id": "test-tenant"
        }

        # Create token with clearly past expiration
        token = jwt_manager.create_access_token(
            payload, 
            expires_delta=timedelta(minutes=-1)  # Clearly expired by 1 minute
        )
        
        with pytest.raises(jwt.ExpiredSignatureError):
            jwt_manager.validate_token(token)

    def test_validate_invalid_token(self, jwt_manager):
        """Test validation of invalid tokens."""
        invalid_tokens = [
            "invalid.token.here",
            "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.invalid.signature",
            "",
            "not-a-jwt-token"
        ]

        for invalid_token in invalid_tokens:
            with pytest.raises((jwt.InvalidTokenError, jwt.DecodeError)):
                jwt_manager.validate_token(invalid_token)

    def test_token_blacklisting(self, jwt_manager):
        """Test token blacklisting functionality."""
        payload = {
            "sub": "user@example.com",
            "user_id": "123",
            "tenant_id": "test-tenant"
        }

        token = jwt_manager.create_access_token(payload)
        
        # Token should be valid initially
        decoded = jwt_manager.validate_token(token)
        assert decoded is not None
        
        # Blacklist the token
        jwt_manager.blacklist_token(token)
        
        # Token should now be blacklisted
        assert jwt_manager.is_token_blacklisted(token)

    def test_token_refresh(self, jwt_manager):
        """Test token refresh functionality."""
        payload = {
            "sub": "user@example.com",
            "user_id": "123",
            "tenant_id": "test-tenant"
        }

        refresh_token = jwt_manager.create_refresh_token(payload)
        new_access_token = jwt_manager.refresh_access_token(refresh_token)
        
        assert isinstance(new_access_token, str)
        assert len(new_access_token) > 0
        
        # Verify new token has same payload
        decoded = jwt_manager.validate_token(new_access_token)
        assert decoded["sub"] == payload["sub"]
        assert decoded["user_id"] == payload["user_id"]


class TestPasswordSecurity:
    """Test password security functionality."""

    @pytest.fixture
    def password_security(self):
        """Create password security manager for testing."""
        return PasswordSecurity()

    def test_hash_password(self, password_security):
        """Test password hashing."""
        password = "TestPassword123!"
        hashed = password_security.hash_password(password)
        
        assert hashed != password
        assert len(hashed) > 0
        assert isinstance(hashed, str)

    def test_verify_password_success(self, password_security):
        """Test successful password verification."""
        password = "TestPassword123!"
        hashed = password_security.hash_password(password)
        
        assert password_security.verify_password(password, hashed)

    def test_verify_password_failure(self, password_security):
        """Test password verification failure."""
        password = "TestPassword123!"
        wrong_password = "WrongPassword123!"
        hashed = password_security.hash_password(password)
        
        assert not password_security.verify_password(wrong_password, hashed)

    def test_password_strength_validation(self, password_security):
        """Test password strength validation."""
        # Strong passwords
        strong_passwords = [
            "StrongPassword123!",
            "MySecure@Pass2023",
            "Complex#Password99"
        ]
        
        for password in strong_passwords:
            assert password_security.validate_password_strength(password)
        
        # Weak passwords
        weak_passwords = [
            "weak",
            "12345678",
            "password",
            "PASSWORD",
            "Password",
            "Pass123",  # Too short
            "passwordwithoutuppercase123!",
            "PASSWORDWITHOUTLOWERCASE123!",
            "PasswordWithoutNumbers!",
            "PasswordWithoutSpecialChars123"
        ]
        
        for password in weak_passwords:
            assert not password_security.validate_password_strength(password)

    def test_password_hash_uniqueness(self, password_security):
        """Test that same password produces different hashes due to salt."""
        password = "TestPassword123!"
        hash1 = password_security.hash_password(password)
        hash2 = password_security.hash_password(password)
        
        # Hashes should be different due to salt
        assert hash1 != hash2
        
        # But both should verify correctly
        assert password_security.verify_password(password, hash1)
        assert password_security.verify_password(password, hash2)

    def test_password_complexity_requirements(self, password_security):
        """Test password complexity requirements."""
        requirements = password_security.get_password_requirements()
        
        assert "min_length" in requirements
        assert "require_uppercase" in requirements
        assert "require_lowercase" in requirements
        assert "require_digits" in requirements
        assert "require_special_chars" in requirements

    def test_generate_secure_password(self, password_security):
        """Test secure password generation."""
        password = password_security.generate_secure_password()
        
        assert len(password) >= 12
        assert password_security.validate_password_strength(password)


class TestRoleBasedAccessControl:
    """Test RBAC functionality."""

    @pytest.fixture
    def rbac(self):
        """Create RBAC manager for testing."""
        return RoleBasedAccessControl()

    @pytest.fixture
    def sample_roles(self, rbac):
        """Create sample roles for testing."""
        rbac.create_role("admin", [
            "users:read", "users:write", "users:delete",
            "content:read", "content:write", "content:delete"
        ])
        rbac.create_role("creator", [
            "content:read", "content:write",
            "analytics:read"
        ])
        rbac.create_role("viewer", [
            "content:read"
        ])
        return rbac

    def test_create_role(self, rbac):
        """Test role creation."""
        permissions = ["users:read", "users:write"]
        rbac.create_role("test_role", permissions)
        
        role = rbac.get_role("test_role")
        assert role is not None
        assert set(role["permissions"]) == set(permissions)

    def test_assign_role_to_user(self, sample_roles):
        """Test assigning role to user."""
        user_id = "user-123"
        sample_roles.assign_role_to_user(user_id, "creator")
        
        user_roles = sample_roles.get_user_roles(user_id)
        assert "creator" in user_roles

    def test_check_permission(self, sample_roles):
        """Test permission checking."""
        user_id = "user-123"
        sample_roles.assign_role_to_user(user_id, "creator")
        
        # User should have creator permissions
        assert sample_roles.has_permission(user_id, "content:read")
        assert sample_roles.has_permission(user_id, "content:write")
        assert sample_roles.has_permission(user_id, "analytics:read")
        
        # User should not have admin permissions
        assert not sample_roles.has_permission(user_id, "users:delete")

    def test_multiple_roles(self, sample_roles):
        """Test user with multiple roles."""
        user_id = "user-123"
        sample_roles.assign_role_to_user(user_id, "creator")
        sample_roles.assign_role_to_user(user_id, "viewer")
        
        user_roles = sample_roles.get_user_roles(user_id)
        assert "creator" in user_roles
        assert "viewer" in user_roles
        
        # Should have permissions from both roles
        assert sample_roles.has_permission(user_id, "content:read")
        assert sample_roles.has_permission(user_id, "content:write")

    def test_remove_role_from_user(self, sample_roles):
        """Test removing role from user."""
        user_id = "user-123"
        sample_roles.assign_role_to_user(user_id, "creator")
        sample_roles.remove_role_from_user(user_id, "creator")
        
        user_roles = sample_roles.get_user_roles(user_id)
        assert "creator" not in user_roles

    def test_tenant_isolation(self, rbac):
        """Test tenant isolation in RBAC."""
        # Create roles for different tenants
        rbac.create_role("admin", ["users:read"], tenant_id="tenant-1")
        rbac.create_role("admin", ["content:read"], tenant_id="tenant-2")
        
        # Assign roles to users in different tenants
        rbac.assign_role_to_user("user-1", "admin", tenant_id="tenant-1")
        rbac.assign_role_to_user("user-2", "admin", tenant_id="tenant-2")
        
        # Users should only have permissions in their tenant
        assert rbac.has_permission("user-1", "users:read", tenant_id="tenant-1")
        assert not rbac.has_permission("user-1", "content:read", tenant_id="tenant-1")
        
        assert rbac.has_permission("user-2", "content:read", tenant_id="tenant-2")
        assert not rbac.has_permission("user-2", "users:read", tenant_id="tenant-2")


class TestGDPRCompliance:
    """Test GDPR compliance functionality."""

    @pytest.fixture
    def gdpr(self):
        """Create GDPR compliance manager for testing."""
        return GDPRCompliance()

    def test_data_anonymization(self, gdpr):
        """Test user data anonymization."""
        user_data = {
            "id": "123",
            "email": "user@example.com",
            "full_name": "John Doe",
            "phone": "+1234567890",
            "address": "123 Main St, City, State"
        }

        anonymized = gdpr.anonymize_user_data(user_data)
        
        # Personal data should be anonymized
        assert anonymized["email"] != user_data["email"]
        assert anonymized["full_name"] != user_data["full_name"]
        assert anonymized["phone"] != user_data["phone"]
        assert anonymized["address"] != user_data["address"]
        
        # ID should be preserved for referential integrity
        assert anonymized["id"] == user_data["id"]
        
        # Anonymized data should contain indicators
        assert "anonymized" in anonymized["email"].lower()

    def test_data_export(self, gdpr):
        """Test user data export functionality."""
        user_data = {
            "id": "123",
            "email": "user@example.com",
            "full_name": "John Doe",
            "created_at": "2023-01-01T00:00:00Z",
            "login_history": [
                {"timestamp": "2023-01-01T10:00:00Z", "ip": "192.168.1.1"},
                {"timestamp": "2023-01-02T10:00:00Z", "ip": "192.168.1.1"}
            ],
            "preferences": {
                "theme": "dark",
                "notifications": True
            }
        }

        exported_data = gdpr.export_user_data(user_data)
        
        assert "personal_information" in exported_data
        assert "account_activity" in exported_data
        assert "preferences" in exported_data
        
        # Personal information should be included
        personal_info = exported_data["personal_information"]
        assert personal_info["email"] == user_data["email"]
        assert personal_info["full_name"] == user_data["full_name"]
        
        # Activity data should be included
        activity = exported_data["account_activity"]
        assert "login_history" in activity
        assert len(activity["login_history"]) == 2

    def test_consent_tracking(self, gdpr):
        """Test consent tracking functionality."""
        from datetime import timezone
        
        consent_data = {
            "user_id": "123",
            "consent_type": "marketing",
            "granted": True,
            "timestamp": datetime.now(timezone.utc),
            "ip_address": "192.168.1.1",
            "user_agent": "Mozilla/5.0..."
        }

        consent_record = gdpr.record_consent(consent_data)
        
        assert consent_record["user_id"] == consent_data["user_id"]
        assert consent_record["consent_type"] == consent_data["consent_type"]
        assert consent_record["granted"] == consent_data["granted"]
        assert "timestamp" in consent_record
        assert "consent_id" in consent_record

    def test_consent_withdrawal(self, gdpr):
        """Test consent withdrawal."""
        from datetime import timezone
        
        # Record initial consent
        consent_data = {
            "user_id": "123",
            "consent_type": "marketing",
            "granted": True,
            "timestamp": datetime.now(timezone.utc)
        }
        
        consent_record = gdpr.record_consent(consent_data)
        consent_id = consent_record["consent_id"]
        
        # Withdraw consent
        withdrawal = gdpr.withdraw_consent(consent_id, "123")
        
        assert withdrawal["granted"] is False
        assert withdrawal["withdrawal_timestamp"] is not None

    def test_data_retention_check(self, gdpr):
        """Test data retention policy checking."""
        from datetime import timezone
        
        old_data = {
            "user_id": "123",
            "created_at": datetime.now(timezone.utc) - timedelta(days=400),  # Over 1 year old
            "last_activity": datetime.now(timezone.utc) - timedelta(days=200)
        }
        
        recent_data = {
            "user_id": "456",
            "created_at": datetime.now(timezone.utc) - timedelta(days=30),
            "last_activity": datetime.now(timezone.utc) - timedelta(days=1)
        }
        
        # Check retention policy (assuming 365 days)
        should_delete_old = gdpr.should_delete_data(old_data, retention_days=365)
        should_delete_recent = gdpr.should_delete_data(recent_data, retention_days=365)
        
        assert should_delete_old is True
        assert should_delete_recent is False

    def test_audit_log_creation(self, gdpr):
        """Test GDPR audit log creation."""
        from datetime import timezone
        
        audit_data = {
            "user_id": "123",
            "action": "data_export",
            "timestamp": datetime.now(timezone.utc),
            "ip_address": "192.168.1.1",
            "details": "User requested data export"
        }
        
        audit_record = gdpr.create_audit_log(audit_data)
        
        assert audit_record["user_id"] == audit_data["user_id"]
        assert audit_record["action"] == audit_data["action"]
        assert "audit_id" in audit_record
        assert "timestamp" in audit_record

    def test_privacy_policy_acceptance(self, gdpr):
        """Test privacy policy acceptance tracking."""
        from datetime import timezone
        
        acceptance_data = {
            "user_id": "123",
            "policy_version": "v2.1",
            "accepted_at": datetime.now(timezone.utc),
            "ip_address": "192.168.1.1"
        }
        
        acceptance_record = gdpr.record_policy_acceptance(acceptance_data)
        
        assert acceptance_record["user_id"] == acceptance_data["user_id"]
        assert acceptance_record["policy_version"] == acceptance_data["policy_version"]
        assert "acceptance_id" in acceptance_record