"""
Tests for security features including password hashing, JWT management, and GDPR compliance.
Tests security components and validates against common vulnerabilities.
"""

import pytest
from datetime import datetime, timedelta
import jwt

from shared.security.jwt_manager import JWTManager
from shared.security.password_security import PasswordSecurity
from shared.security.gdpr_compliance import GDPRCompliance


class TestPasswordSecurity:
    """Test password security functionality."""

    def test_password_hashing(self, password_security: PasswordSecurity):
        """Test password hashing functionality."""
        password = "TestPassword123!"
        hashed = password_security.hash_password(password)
        
        assert hashed != password
        assert len(hashed) > 0
        assert password_security.verify_password(password, hashed)

    def test_password_verification_failure(self, password_security: PasswordSecurity):
        """Test password verification with wrong password."""
        password = "TestPassword123!"
        wrong_password = "WrongPassword123!"
        hashed = password_security.hash_password(password)
        
        assert not password_security.verify_password(wrong_password, hashed)

    def test_password_strength_validation(self, password_security: PasswordSecurity):
        """Test password strength validation."""
        # Strong password
        strong_password = "StrongPassword123!"
        assert password_security.validate_password_strength(strong_password)
        
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
        
        for weak_password in weak_passwords:
            assert not password_security.validate_password_strength(weak_password)

    def test_password_hash_uniqueness(self, password_security: PasswordSecurity):
        """Test that same password produces different hashes (salt)."""
        password = "TestPassword123!"
        hash1 = password_security.hash_password(password)
        hash2 = password_security.hash_password(password)
        
        # Hashes should be different due to salt
        assert hash1 != hash2
        
        # But both should verify correctly
        assert password_security.verify_password(password, hash1)
        assert password_security.verify_password(password, hash2)


class TestJWTManager:
    """Test JWT token management."""

    def test_token_creation(self, jwt_manager: JWTManager):
        """Test JWT token creation."""
        payload = {
            "sub": "test@example.com",
            "user_id": "123",
            "tenant_id": "test-tenant"
        }
        
        token = jwt_manager.create_access_token(payload)
        assert isinstance(token, str)
        assert len(token) > 0

    def test_token_validation(self, jwt_manager: JWTManager):
        """Test JWT token validation."""
        payload = {
            "sub": "test@example.com",
            "user_id": "123",
            "tenant_id": "test-tenant"
        }
        
        token = jwt_manager.create_access_token(payload)
        decoded_payload = jwt_manager.validate_token(token)
        
        assert decoded_payload["sub"] == payload["sub"]
        assert decoded_payload["user_id"] == payload["user_id"]
        assert decoded_payload["tenant_id"] == payload["tenant_id"]

    def test_token_expiration(self, jwt_manager: JWTManager):
        """Test JWT token expiration."""
        payload = {
            "sub": "test@example.com",
            "user_id": "123",
            "tenant_id": "test-tenant"
        }
        
        # Create token with very short expiration
        token = jwt_manager.create_access_token(payload, expires_delta=timedelta(seconds=-1))
        
        # Token should be expired and validation should fail
        with pytest.raises(jwt.ExpiredSignatureError):
            jwt_manager.validate_token(token)

    def test_invalid_token(self, jwt_manager: JWTManager):
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

    def test_refresh_token_creation(self, jwt_manager: JWTManager):
        """Test refresh token creation."""
        payload = {
            "sub": "test@example.com",
            "user_id": "123",
            "tenant_id": "test-tenant"
        }
        
        refresh_token = jwt_manager.create_refresh_token(payload)
        assert isinstance(refresh_token, str)
        assert len(refresh_token) > 0
        
        # Refresh token should have longer expiration
        decoded = jwt_manager.validate_token(refresh_token)
        assert "exp" in decoded

    def test_token_blacklisting(self, jwt_manager: JWTManager):
        """Test token blacklisting functionality."""
        payload = {
            "sub": "test@example.com",
            "user_id": "123",
            "tenant_id": "test-tenant"
        }
        
        token = jwt_manager.create_access_token(payload)
        
        # Token should be valid initially
        decoded = jwt_manager.validate_token(token)
        assert decoded is not None
        
        # Blacklist the token
        jwt_manager.blacklist_token(token)
        
        # Token should now be invalid
        assert jwt_manager.is_token_blacklisted(token)


class TestSecurityVulnerabilities:
    """Test protection against common security vulnerabilities."""

    async def test_sql_injection_protection(self, client):
        """Test protection against SQL injection attacks."""
        # Attempt SQL injection in email field
        malicious_payloads = [
            "test@example.com'; DROP TABLE users; --",
            "test@example.com' OR '1'='1",
            "test@example.com'; INSERT INTO users (email) VALUES ('hacked@example.com'); --"
        ]
        
        for payload in malicious_payloads:
            response = await client.post("/api/v1/auth/login", json={
                "email": payload,
                "password": "password"
            })
            
            # Should return 401 (unauthorized) or 422 (validation error), not 500 (server error)
            assert response.status_code in [401, 422]

    async def test_xss_protection(self, client, test_user_data):
        """Test protection against XSS attacks."""
        # Attempt XSS in user registration
        xss_payloads = [
            "<script>alert('xss')</script>",
            "javascript:alert('xss')",
            "<img src=x onerror=alert('xss')>",
            "';alert('xss');//"
        ]
        
        for payload in xss_payloads:
            user_data = test_user_data.copy()
            user_data["full_name"] = payload
            
            response = await client.post("/api/v1/auth/register", json=user_data)
            
            if response.status_code == 201:
                # If registration succeeds, check that payload is properly escaped
                user_info = response.json()
                assert "<script>" not in user_info["full_name"]
                assert "javascript:" not in user_info["full_name"]

    async def test_brute_force_protection(self, client, test_user_data):
        """Test protection against brute force attacks."""
        # Register a user first
        await client.post("/api/v1/auth/register", json=test_user_data)
        
        # Attempt multiple failed logins
        failed_attempts = 0
        for i in range(20):  # Try 20 failed login attempts
            response = await client.post("/api/v1/auth/login", json={
                "email": test_user_data["email"],
                "password": f"wrong_password_{i}"
            })
            
            if response.status_code == 429:  # Rate limited
                break
            elif response.status_code == 401:  # Unauthorized
                failed_attempts += 1
            
        # Should eventually get rate limited or have some protection
        # This test assumes some form of rate limiting is implemented
        assert failed_attempts < 20 or response.status_code == 429

    async def test_csrf_protection(self, client):
        """Test CSRF protection mechanisms."""
        # This test would check for CSRF tokens in forms
        # For API-only services, this might not be applicable
        # But we can test that state-changing operations require authentication
        
        response = await client.post("/api/v1/auth/logout")
        assert response.status_code == 401  # Should require authentication

    def test_timing_attack_protection(self, password_security: PasswordSecurity):
        """Test protection against timing attacks."""
        import time
        
        password = "TestPassword123!"
        correct_hash = password_security.hash_password(password)
        
        # Time verification with correct password
        start_time = time.time()
        result1 = password_security.verify_password(password, correct_hash)
        correct_time = time.time() - start_time
        
        # Time verification with incorrect password
        start_time = time.time()
        result2 = password_security.verify_password("WrongPassword", correct_hash)
        incorrect_time = time.time() - start_time
        
        assert result1 is True
        assert result2 is False
        
        # Time difference should be minimal (constant time comparison)
        time_difference = abs(correct_time - incorrect_time)
        assert time_difference < 0.01  # Less than 10ms difference


class TestGDPRCompliance:
    """Test GDPR compliance features."""

    def test_data_anonymization(self):
        """Test user data anonymization."""
        gdpr = GDPRCompliance()
        
        user_data = {
            "email": "user@example.com",
            "full_name": "John Doe",
            "phone": "+1234567890",
            "address": "123 Main St"
        }
        
        anonymized = gdpr.anonymize_user_data(user_data)
        
        assert anonymized["email"] != user_data["email"]
        assert anonymized["full_name"] != user_data["full_name"]
        assert "anonymized" in anonymized["email"].lower()

    def test_data_export(self):
        """Test user data export functionality."""
        gdpr = GDPRCompliance()
        
        user_data = {
            "id": "123",
            "email": "user@example.com",
            "full_name": "John Doe",
            "created_at": "2023-01-01T00:00:00Z",
            "login_history": ["2023-01-01", "2023-01-02"]
        }
        
        exported_data = gdpr.export_user_data(user_data)
        
        assert "personal_information" in exported_data
        assert "account_activity" in exported_data
        assert exported_data["personal_information"]["email"] == user_data["email"]

    def test_consent_tracking(self):
        """Test consent tracking functionality."""
        gdpr = GDPRCompliance()
        
        consent_data = {
            "user_id": "123",
            "consent_type": "marketing",
            "granted": True,
            "timestamp": datetime.utcnow()
        }
        
        consent_record = gdpr.record_consent(consent_data)
        
        assert consent_record["user_id"] == consent_data["user_id"]
        assert consent_record["consent_type"] == consent_data["consent_type"]
        assert consent_record["granted"] == consent_data["granted"]
        assert "timestamp" in consent_record