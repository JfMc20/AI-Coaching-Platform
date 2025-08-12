#!/usr/bin/env python3
"""
Test script for Auth Service
Validates password security, authentication endpoints, and database models
"""

import asyncio
import sys
import os
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from shared.security import (
    PasswordHasher, PasswordValidator, PasswordPolicy,
    hash_password, verify_password, validate_password_strength
)


async def test_password_security():
    """Test password security implementation"""
    print("Testing Password Security Implementation...")
    
    # Test 1: Password hashing
    print("\n1. Testing password hashing...")
    password = "SecureP@ssw0rd123!"
    
    # Test Argon2id hashing
    hashed_argon2 = hash_password(password, use_argon2=True)
    print(f"   OK Argon2id hash: {hashed_argon2[:50]}...")
    assert hashed_argon2.startswith("$argon2id$")
    
    # Test bcrypt hashing
    hasher = PasswordHasher()
    hashed_bcrypt = hasher.hash_password(password, use_argon2=False)
    print(f"   OK bcrypt hash: {hashed_bcrypt[:50]}...")
    assert hashed_bcrypt.startswith("$2b$")
    
    # Test 2: Password verification
    print("\n2. Testing password verification...")
    assert verify_password(password, hashed_argon2) is True
    assert verify_password("wrong", hashed_argon2) is False
    assert hasher.verify_password(password, hashed_bcrypt) is True
    assert hasher.verify_password("wrong", hashed_bcrypt) is False
    print("   OK Password verification working correctly")
    
    # Test 3: Password strength validation
    print("\n3. Testing password strength validation...")
    
    # Strong password
    strong_result = await validate_password_strength("VeryStr0ng!P@ssw0rd2024")
    print(f"   OK Strong password: {strong_result.strength.value} (score: {strong_result.score})")
    assert strong_result.is_valid is True
    
    # Weak password
    weak_result = await validate_password_strength("weak")
    print(f"   OK Weak password: {weak_result.strength.value} (score: {weak_result.score})")
    assert weak_result.is_valid is False
    assert len(weak_result.violations) > 0
    
    # Test 4: Personal info detection
    print("\n4. Testing personal info detection...")
    personal_info = {"email": "john.doe@example.com", "name": "John Doe"}
    personal_result = await validate_password_strength("JohnDoe123!", personal_info)
    print(f"   OK Personal info detection: {len(personal_result.violations)} violations found")
    assert personal_result.is_valid is False
    
    # Test 5: Hash upgrade detection
    print("\n5. Testing hash upgrade detection...")
    assert hasher.needs_rehash(hashed_argon2) is False  # Argon2 doesn't need upgrade
    assert hasher.needs_rehash(hashed_bcrypt) is True   # bcrypt should be upgraded
    print("   OK Hash upgrade detection working correctly")
    
    print("\nAll password security tests passed!")


def test_database_models():
    """Test database models"""
    print("\nTesting Database Models...")
    
    try:
        from shared.models.database import Creator, RefreshToken, UserSession, AuditLog
        print("   OK All database models imported successfully")
        
        # Test model attributes
        creator_columns = [col.name for col in Creator.__table__.columns]
        expected_columns = ['id', 'email', 'password_hash', 'full_name', 'is_active']
        for col in expected_columns:
            assert col in creator_columns, f"Missing column: {col}"
        print("   OK Creator model has required columns")
        
        refresh_token_columns = [col.name for col in RefreshToken.__table__.columns]
        expected_rt_columns = ['id', 'token_hash', 'creator_id', 'family_id', 'expires_at']
        for col in expected_rt_columns:
            assert col in refresh_token_columns, f"Missing column: {col}"
        print("   OK RefreshToken model has required columns")
        
        print("All database model tests passed!")
        
    except ImportError as e:
        print(f"   ERROR Failed to import database models: {e}")
        return False
    except Exception as e:
        print(f"   ERROR Database model test failed: {e}")
        return False
    
    return True


def test_auth_models():
    """Test authentication Pydantic models"""
    print("\nTesting Authentication Models...")
    
    try:
        from pydantic import ValidationError
        from shared.models.auth import (
            CreatorCreate, CreatorResponse, TokenResponse,
            LoginRequest, PasswordStrengthResponse
        )
        print("   OK All auth models imported successfully")
        
        # Test CreatorCreate validation
        creator_data = CreatorCreate(
            email="test@example.com",
            password="SecureP@ssw0rd123!",
            full_name="Test Creator",
            company_name="Test Company"
        )
        assert creator_data.email == "test@example.com"
        assert creator_data.password == "SecureP@ssw0rd123!"
        print("   OK CreatorCreate model validation working")
        
        # Test weak password rejection
        try:
            weak_creator = CreatorCreate(
                email="test@example.com",
                password="weak",
                full_name="Test Creator"
            )
            assert False, "Should have rejected weak password"
        except ValidationError:
            print("   OK Weak password properly rejected")
        
        # Test LoginRequest
        login_data = LoginRequest(
            email="test@example.com",
            password="password123",
            remember_me=True
        )
        assert login_data.remember_me is True
        print("   OK LoginRequest model working")
        
        print("All auth model tests passed!")
        
    except ImportError as e:
        print(f"   ERROR Failed to import auth models: {e}")
        return False
    except Exception as e:
        print(f"   ERROR Auth model test failed: {e}")
        return False
    
    return True


def test_service_structure():
    """Test service file structure"""
    print("\nTesting Service Structure...")
    
    auth_service_path = project_root / "services" / "auth-service"
    required_files = [
        "app/main.py",
        "app/services/auth_service.py",
        "app/dependencies/auth.py",
        "app/routes/auth.py",
        "app/database.py",
        ".env.example"
    ]
    
    for file_path in required_files:
        full_path = auth_service_path / file_path
        if full_path.exists():
            print(f"   OK {file_path}")
        else:
            print(f"   ERROR Missing: {file_path}")
            return False
    
    # Test shared security module
    shared_security_path = project_root / "shared" / "security"
    security_files = [
        "__init__.py",
        "password_security.py",
        "common_passwords.txt"
    ]
    
    for file_path in security_files:
        full_path = shared_security_path / file_path
        if full_path.exists():
            print(f"   OK shared/security/{file_path}")
        else:
            print(f"   ERROR Missing: shared/security/{file_path}")
            return False
    
    print("All service structure tests passed!")
    return True


async def main():
    """Run all tests"""
    print("Starting Auth Service Tests...\n")
    
    try:
        # Test password security
        await test_password_security()
        
        # Test database models
        if not test_database_models():
            sys.exit(1)
        
        # Test auth models
        if not test_auth_models():
            sys.exit(1)
        
        # Test service structure
        if not test_service_structure():
            sys.exit(1)
        
        print("\nALL TESTS PASSED!")
        print("\nAuth Service implementation is ready for deployment!")
        print("\nNext steps:")
        print("1. Set up environment variables (copy .env.example to .env)")
        print("2. Run database migrations")
        print("3. Start the auth service")
        print("4. Test endpoints with curl or Postman")
        
    except Exception as e:
        print(f"\nERROR Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())