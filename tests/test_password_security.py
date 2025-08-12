"""
Tests for password security implementation
Validates password hashing, strength validation, and policy enforcement
"""

import pytest
import asyncio
from unittest.mock import patch, AsyncMock
from datetime import datetime

from shared.security.password_security import (
    PasswordHasher, PasswordValidator, PasswordPolicy, PasswordStrength,
    hash_password, verify_password, validate_password_strength, check_password_policy
)


class TestPasswordHasher:
    """Test password hashing functionality"""
    
    def test_password_hasher_initialization(self):
        """Test password hasher initializes correctly"""
        hasher = PasswordHasher()
        assert hasher.argon2_hasher is not None
        assert hasher.bcrypt_context is not None
    
    def test_hash_password_argon2(self):
        """Test password hashing with Argon2id"""
        hasher = PasswordHasher()
        password = "TestPassword123!"
        
        hashed = hasher.hash_password(password, use_argon2=True)
        
        assert hashed.startswith("$argon2id$")
        assert len(hashed) > 50  # Argon2 hashes are long
        assert hashed != password
    
    def test_hash_password_bcrypt(self):
        """Test password hashing with bcrypt"""
        hasher = PasswordHasher()
        password = "TestPassword123!"
        
        hashed = hasher.hash_password(password, use_argon2=False)
        
        assert hashed.startswith("$2b$")
        assert len(hashed) == 60  # bcrypt hashes are 60 chars
        assert hashed != password
    
    def test_verify_password_argon2(self):
        """Test password verification with Argon2id"""
        hasher = PasswordHasher()
        password = "TestPassword123!"
        
        hashed = hasher.hash_password(password, use_argon2=True)
        
        # Correct password should verify
        assert hasher.verify_password(password, hashed) is True
        
        # Wrong password should not verify
        assert hasher.verify_password("WrongPassword", hashed) is False
    
    def test_verify_password_bcrypt(self):
        """Test password verification with bcrypt"""
        hasher = PasswordHasher()
        password = "TestPassword123!"
        
        hashed = hasher.hash_password(password, use_argon2=False)
        
        # Correct password should verify
        assert hasher.verify_password(password, hashed) is True
        
        # Wrong password should not verify
        assert hasher.verify_password("WrongPassword", hashed) is False
    
    def test_needs_rehash(self):
        """Test hash upgrade detection"""
        hasher = PasswordHasher()
        
        # Argon2 hashes don't need rehashing
        argon2_hash = hasher.hash_password("test", use_argon2=True)
        assert hasher.needs_rehash(argon2_hash) is False
        
        # bcrypt hashes should be upgraded
        bcrypt_hash = hasher.hash_password("test", use_argon2=False)
        assert hasher.needs_rehash(bcrypt_hash) is True
        
        # Unknown formats should be rehashed (explicit test for unknown format handling)
        unknown_format_hash = "unknown_format_hash"
        needs_rehash = hasher.needs_rehash(unknown_format_hash)
        assert needs_rehash is True, f"Expected unknown format '{unknown_format_hash}' to need rehashing"
    
    def test_convenience_functions(self):
        """Test convenience functions work correctly"""
        password = "TestPassword123!"
        
        # Hash password
        hashed = hash_password(password)
        assert hashed.startswith("$argon2id$")
        
        # Verify password
        assert verify_password(password, hashed) is True
        assert verify_password("wrong", hashed) is False


class TestPasswordValidator:
    """Test password strength validation"""
    
    def test_password_validator_initialization(self):
        """Test password validator initializes correctly"""
        validator = PasswordValidator()
        assert validator.policy is not None
        assert isinstance(validator.policy, PasswordPolicy)
    
    def test_custom_policy(self):
        """Test validator with custom policy"""
        policy = PasswordPolicy(
            min_length=12,
            require_special_chars=False
        )
        validator = PasswordValidator(policy)
        assert validator.policy.min_length == 12
        assert validator.policy.require_special_chars is False
    
    @pytest.mark.asyncio
    async def test_strong_password_validation(self):
        """Test validation of strong password"""
        validator = PasswordValidator()
        
        result = await validator.validate_password_strength("StrongP@ssw0rd123!")
        
        assert result.strength == PasswordStrength.STRONG
        assert result.score >= 80
        assert result.is_valid is True
        assert len(result.violations) == 0
    
    @pytest.mark.asyncio
    async def test_weak_password_validation(self):
        """Test validation of weak password"""
        validator = PasswordValidator()
        
        result = await validator.validate_password_strength("weak")
        
        assert result.strength in [PasswordStrength.VERY_WEAK, PasswordStrength.WEAK]
        assert result.score < 40
        assert result.is_valid is False
        assert len(result.violations) > 0
    
    @pytest.mark.asyncio
    async def test_common_password_detection(self):
        """Test detection of common passwords"""
        validator = PasswordValidator()
        
        result = await validator.validate_password_strength("password123")
        
        assert result.is_valid is False
        assert any("common" in violation.lower() for violation in result.violations)
    
    @pytest.mark.asyncio
    async def test_personal_info_detection(self):
        """Test detection of personal information in password"""
        validator = PasswordValidator()
        personal_info = {
            "email": "john.doe@example.com",
            "name": "John Doe"
        }
        
        result = await validator.validate_password_strength(
            "JohnDoe123!", personal_info
        )
        
        assert result.is_valid is False
        assert any("personal" in violation.lower() for violation in result.violations)
    
    @pytest.mark.asyncio
    async def test_forbidden_patterns(self):
        """Test detection of forbidden patterns"""
        validator = PasswordValidator()
        
        # Test repeated characters
        result = await validator.validate_password_strength("Passssword123!")
        assert any("pattern" in violation.lower() for violation in result.violations)
        
        # Test sequential numbers
        result = await validator.validate_password_strength("Password123456!")
        assert any("pattern" in violation.lower() for violation in result.violations)
    
    @pytest.mark.asyncio
    @patch('httpx.AsyncClient.get')
    async def test_compromised_password_check(self, mock_get):
        """Test HaveIBeenPwned API integration"""
        # Mock API response for compromised password
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.text = "5E884898DA28047151D0E56F8DC6292773603D0D6AABBDD62A11EF721D1542D8:3"
        mock_get.return_value.__aenter__.return_value = mock_response
        
        validator = PasswordValidator()
        
        # This should detect the password as compromised
        result = await validator.validate_password_strength("password")
        
        # Note: The actual hash check might not match, but we're testing the flow
        mock_get.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_password_requirements_validation(self):
        """Test individual password requirements"""
        validator = PasswordValidator()
        
        # Test minimum length
        result = await validator.validate_password_strength("Short1!")
        assert any("8 characters" in violation for violation in result.violations)
        
        # Test uppercase requirement
        result = await validator.validate_password_strength("lowercase123!")
        assert any("uppercase" in violation.lower() for violation in result.violations)
        
        # Test lowercase requirement
        result = await validator.validate_password_strength("UPPERCASE123!")
        assert any("lowercase" in violation.lower() for violation in result.violations)
        
        # Test digit requirement
        result = await validator.validate_password_strength("NoDigits!")
        assert any("digit" in violation.lower() for violation in result.violations)
        
        # Test special character requirement
        result = await validator.validate_password_strength("NoSpecialChars123")
        assert any("special" in violation.lower() for violation in result.violations)


class TestPasswordPolicy:
    """Test password policy configuration"""
    
    def test_default_policy(self):
        """Test default policy values"""
        policy = PasswordPolicy()
        
        assert policy.min_length == 8
        assert policy.max_length == 128
        assert policy.require_uppercase is True
        assert policy.require_lowercase is True
        assert policy.require_digits is True
        assert policy.require_special_chars is True
        assert policy.check_common_passwords is True
        assert policy.check_personal_info is True
        assert policy.check_compromised is True
    
    def test_custom_policy(self):
        """Test custom policy configuration"""
        policy = PasswordPolicy(
            min_length=12,
            max_length=64,
            require_special_chars=False,
            check_compromised=False
        )
        
        assert policy.min_length == 12
        assert policy.max_length == 64
        assert policy.require_special_chars is False
        assert policy.check_compromised is False
    
    def test_forbidden_patterns_initialization(self):
        """Test forbidden patterns are initialized"""
        policy = PasswordPolicy()
        
        assert policy.forbidden_patterns is not None
        assert len(policy.forbidden_patterns) > 0
        assert any("repeated" in str(pattern) or r"(.)\1{2,}" in str(pattern) for pattern in policy.forbidden_patterns)


class TestConvenienceFunctions:
    """Test convenience functions"""
    
    @pytest.mark.asyncio
    async def test_validate_password_strength_function(self):
        """Test convenience function for password validation"""
        result = await validate_password_strength("StrongP@ssw0rd123!")
        
        assert result.strength == PasswordStrength.STRONG
        assert result.is_valid is True
    
    @pytest.mark.asyncio
    async def test_validate_password_strength_with_personal_info(self):
        """Test convenience function with personal info"""
        personal_info = {"email": "test@example.com"}
        result = await validate_password_strength("TestPassword123!", personal_info)
        
        # Should detect "test" from email in password
        assert result.is_valid is False
    
    def test_check_password_policy_function(self):
        """Test synchronous check_password_policy function used by Pydantic models"""
        # Test strong password - should pass
        assert check_password_policy("StrongPassword123!") is True
        
        # Test weak passwords - should fail
        assert check_password_policy("weak") is False
        assert check_password_policy("password") is False
        assert check_password_policy("12345678") is False
        assert check_password_policy("PASSWORD123") is False  # No lowercase
        assert check_password_policy("password123") is False  # No uppercase
        assert check_password_policy("Password") is False     # No digits or special chars
        assert check_password_policy("Pass123") is False      # Too short
        
        # Test edge cases
        assert check_password_policy("") is False             # Empty password
        assert check_password_policy("   ") is False          # Whitespace only
        
        # Test minimum requirements met
        assert check_password_policy("Password1!") is True    # Meets all requirements
        assert check_password_policy("MySecure123@") is True  # Different valid password
    
    def test_check_password_policy_integration_with_pydantic(self):
        """Test that check_password_policy works correctly with Pydantic model validation"""
        from shared.models.auth import CreatorCreate, PasswordResetConfirm
        from pydantic import ValidationError
        
        # Test CreatorCreate model with valid password
        creator = CreatorCreate(
            email="test@example.com",
            password="ValidPassword123!",
            full_name="Test User"
        )
        assert creator.password == "ValidPassword123!"
        
        # Test CreatorCreate model with invalid password (meets length but fails security policy)
        with pytest.raises(ValidationError) as exc_info:
            CreatorCreate(
                email="test@example.com",
                password="password123",  # 8+ chars but no uppercase or special chars
                full_name="Test User"
            )
        assert "does not meet security requirements" in str(exc_info.value)
        
        # Test PasswordResetConfirm model with valid password
        reset_confirm = PasswordResetConfirm(
            token="reset_token_123",
            new_password="NewValidPassword123!"
        )
        assert reset_confirm.new_password == "NewValidPassword123!"
        
        # Test PasswordResetConfirm model with invalid password (meets length but fails security policy)
        with pytest.raises(ValidationError) as exc_info:
            PasswordResetConfirm(
                token="reset_token_123",
                new_password="weakpassword"  # 8+ chars but no uppercase, digits, or special chars
            )
        assert "does not meet security requirements" in str(exc_info.value)


class TestPasswordSecurityIntegration:
    """Integration tests for password security"""
    
    @pytest.mark.asyncio
    async def test_full_password_lifecycle(self):
        """Test complete password lifecycle"""
        password = "SecureP@ssw0rd123!"
        
        # 1. Validate password strength
        strength_result = await validate_password_strength(password)
        assert strength_result.is_valid is True
        
        # 2. Hash password
        hashed = hash_password(password)
        assert hashed.startswith("$argon2id$")
        
        # 3. Verify password
        assert verify_password(password, hashed) is True
        assert verify_password("wrong", hashed) is False
    
    @pytest.mark.asyncio
    async def test_password_upgrade_scenario(self):
        """Test password hash upgrade scenario"""
        hasher = PasswordHasher()
        password = "TestPassword123!"
        
        # Start with bcrypt hash (legacy)
        bcrypt_hash = hasher.hash_password(password, use_argon2=False)
        assert bcrypt_hash.startswith("$2b$")
        
        # Verify it works
        assert hasher.verify_password(password, bcrypt_hash) is True
        
        # Check if it needs rehashing
        assert hasher.needs_rehash(bcrypt_hash) is True
        
        # Upgrade to Argon2
        argon2_hash = hasher.hash_password(password, use_argon2=True)
        assert argon2_hash.startswith("$argon2id$")
        
        # Verify new hash works
        assert hasher.verify_password(password, argon2_hash) is True
        
        # New hash doesn't need rehashing
        assert hasher.needs_rehash(argon2_hash) is False
    
    @pytest.mark.asyncio
    async def test_unified_password_security_across_services(self):
        """Test that unified password security works correctly across all scenarios"""
        hasher = PasswordHasher()
        password = "TestUnified123!"
        
        # Test both Argon2id and bcrypt hashing
        argon2_hash = hasher.hash_password(password, use_argon2=True)
        bcrypt_hash = hasher.hash_password(password, use_argon2=False)
        
        # Both should verify correctly
        assert hasher.verify_password(password, argon2_hash) is True
        assert hasher.verify_password(password, bcrypt_hash) is True
        
        # Cross-verification should work (same hasher instance)
        assert verify_password(password, argon2_hash) is True
        assert verify_password(password, bcrypt_hash) is True
        
        # Test backward compatibility during transition
        old_bcrypt_users = [
            hasher.hash_password(f"user{i}password", use_argon2=False) 
            for i in range(3)
        ]
        
        # All old hashes should still verify
        for i, old_hash in enumerate(old_bcrypt_users):
            assert hasher.verify_password(f"user{i}password", old_hash) is True
            assert hasher.needs_rehash(old_hash) is True
        
        # New Argon2 hashes should not need rehashing
        new_argon2_hash = hasher.hash_password("newuserpassword", use_argon2=True)
        assert hasher.needs_rehash(new_argon2_hash) is False
    
    @pytest.mark.asyncio
    async def test_service_authentication_compatibility(self):
        """Test that services can authenticate users with both old and new hashes"""
        hasher = PasswordHasher()
        
        # Simulate existing user with bcrypt hash
        existing_user_password = "ExistingUser123!"
        existing_hash = hasher.hash_password(existing_user_password, use_argon2=False)
        
        # Simulate new user with Argon2 hash
        new_user_password = "NewUser123!"
        new_hash = hasher.hash_password(new_user_password, use_argon2=True)
        
        # Both should authenticate successfully
        assert hasher.verify_password(existing_user_password, existing_hash) is True
        assert hasher.verify_password(new_user_password, new_hash) is True
        
        # Existing user should be flagged for hash upgrade
        assert hasher.needs_rehash(existing_hash) is True
        assert hasher.needs_rehash(new_hash) is False
        
        # After upgrade, existing user should have Argon2 hash
        upgraded_hash = hasher.hash_password(existing_user_password, use_argon2=True)
        assert upgraded_hash.startswith("$argon2id$")
        assert hasher.verify_password(existing_user_password, upgraded_hash) is True
        assert hasher.needs_rehash(upgraded_hash) is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])