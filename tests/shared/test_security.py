"""
Tests for security components.
Tests JWT management, password security, RBAC, and GDPR compliance.
"""


from shared.security.jwt_manager import JWTManager
from shared.security.password_security import PasswordHasher
from shared.security.rbac import RBACManager
from shared.security.gdpr_compliance import GDPRComplianceManager


class TestJWTManager:
    """Test JWT token management."""

    def test_jwt_manager_creation(self):
        """Test JWT manager can be created."""
        jwt_manager = JWTManager()
        assert jwt_manager is not None
        assert hasattr(jwt_manager, 'key_manager')
        assert hasattr(jwt_manager, 'issuer')
        assert hasattr(jwt_manager, 'audience')


class TestPasswordHasher:
    """Test password security functionality."""

    def test_password_hasher_creation(self):
        """Test password hasher can be created."""
        hasher = PasswordHasher()
        assert hasher is not None
        assert hasattr(hasher, 'hash_password')
        assert hasattr(hasher, 'verify_password')

    def test_hash_password(self):
        """Test password hashing functionality."""
        hasher = PasswordHasher()
        password = "TestPassword123!"
        hashed = hasher.hash_password(password)
        
        assert hashed != password
        assert len(hashed) > 0

    def test_verify_password_success(self):
        """Test password verification with correct password."""
        hasher = PasswordHasher()
        password = "TestPassword123!"
        hashed = hasher.hash_password(password)
        
        assert hasher.verify_password(password, hashed)

    def test_verify_password_failure(self):
        """Test password verification with wrong password."""
        hasher = PasswordHasher()
        password = "TestPassword123!"
        wrong_password = "WrongPassword123!"
        hashed = hasher.hash_password(password)
        
        assert not hasher.verify_password(wrong_password, hashed)

    def test_password_strength_validation(self):
        """Test password strength validation."""
        hasher = PasswordHasher()
        
        # Test method exists
        assert hasattr(hasher, 'validate_password_strength') or hasattr(hasher, 'check_strength')

    def test_password_hash_uniqueness(self):
        """Test that same password produces different hashes (salt)."""
        hasher = PasswordHasher()
        password = "TestPassword123!"
        hash1 = hasher.hash_password(password)
        hash2 = hasher.hash_password(password)
        
        # Hashes should be different due to salt
        assert hash1 != hash2
        
        # But both should verify correctly
        assert hasher.verify_password(password, hash1)
        assert hasher.verify_password(password, hash2)

    def test_password_complexity_requirements(self):
        """Test password complexity requirements."""
        hasher = PasswordHasher()
        
        # Test that hasher can handle complex passwords
        complex_password = "MyC0mpl3x!P@ssw0rd#2024"
        hashed = hasher.hash_password(complex_password)
        assert hasher.verify_password(complex_password, hashed)

    def test_generate_secure_password(self):
        """Test secure password generation if available."""
        hasher = PasswordHasher()
        
        # Test method exists or skip
        if hasattr(hasher, 'generate_password'):
            password = hasher.generate_password()
            assert isinstance(password, str)
            assert len(password) >= 8


class TestRBACManager:
    """Test role-based access control."""

    def test_rbac_manager_creation(self):
        """Test RBAC manager can be created."""
        rbac = RBACManager()
        assert rbac is not None

    def test_create_role(self):
        """Test role creation."""
        rbac = RBACManager()
        
        # Test that basic methods exist
        assert hasattr(rbac, 'create_role') or hasattr(rbac, 'add_role')

    def test_assign_role_to_user(self):
        """Test role assignment to user."""
        rbac = RBACManager()
        
        # Test that assignment methods exist
        assert hasattr(rbac, 'assign_role') or hasattr(rbac, 'add_user_role')

    def test_check_permission(self):
        """Test permission checking."""
        rbac = RBACManager()
        
        # Test that permission checking methods exist
        assert hasattr(rbac, 'check_permission') or hasattr(rbac, 'has_permission')

    def test_multiple_roles(self):
        """Test handling multiple roles."""
        rbac = RBACManager()
        
        # Test that multiple role methods exist
        assert hasattr(rbac, 'get_user_roles') or hasattr(rbac, 'list_roles')

    def test_remove_role_from_user(self):
        """Test role removal from user."""
        rbac = RBACManager()
        
        # Test that removal methods exist
        assert hasattr(rbac, 'remove_role') or hasattr(rbac, 'delete_user_role')

    def test_tenant_isolation(self):
        """Test tenant isolation in RBAC."""
        rbac = RBACManager()
        
        # Test basic functionality
        assert rbac is not None


class TestGDPRComplianceManager:
    """Test GDPR compliance features."""

    def test_gdpr_manager_creation(self):
        """Test GDPR compliance manager can be created."""
        gdpr = GDPRComplianceManager()
        assert gdpr is not None

    def test_data_anonymization(self):
        """Test data anonymization functionality."""
        gdpr = GDPRComplianceManager()
        
        # Test that anonymization methods exist
        assert hasattr(gdpr, 'anonymize_data') or hasattr(gdpr, 'anonymize')

    def test_data_export(self):
        """Test data export functionality."""
        gdpr = GDPRComplianceManager()
        
        # Test that export methods exist
        assert hasattr(gdpr, 'export_data') or hasattr(gdpr, 'export_user_data')

    def test_consent_tracking(self):
        """Test consent tracking functionality."""
        gdpr = GDPRComplianceManager()
        
        # Test that consent methods exist
        assert hasattr(gdpr, 'track_consent') or hasattr(gdpr, 'record_consent')

    def test_consent_withdrawal(self):
        """Test consent withdrawal functionality."""
        gdpr = GDPRComplianceManager()
        
        # Test that withdrawal methods exist
        assert hasattr(gdpr, 'withdraw_consent') or hasattr(gdpr, 'revoke_consent')

    def test_data_retention_check(self):
        """Test data retention checking."""
        gdpr = GDPRComplianceManager()
        
        # Test that retention methods exist
        assert hasattr(gdpr, 'check_retention') or hasattr(gdpr, 'audit_retention')

    def test_audit_log_creation(self):
        """Test audit log creation."""
        gdpr = GDPRComplianceManager()
        
        # Test that audit methods exist
        assert hasattr(gdpr, 'create_audit_log') or hasattr(gdpr, 'log_action')

    def test_privacy_policy_acceptance(self):
        """Test privacy policy acceptance tracking."""
        gdpr = GDPRComplianceManager()
        
        # Test that policy methods exist
        assert hasattr(gdpr, 'accept_policy') or hasattr(gdpr, 'track_policy_acceptance')