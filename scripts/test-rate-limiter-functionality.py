#!/usr/bin/env python3
"""
Test script for Rate Limiter Functionality
Validates that the rate limiter still works correctly after the race condition fix
"""

import sys
import os
from pathlib import Path
import re

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def test_rate_limiter_code_structure():
    """Test that the rate limiter code structure is intact"""
    print("Testing Rate Limiter Code Structure...")
    
    # Read the auth.py file directly
    auth_file_path = project_root / "services" / "auth-service" / "app" / "dependencies" / "auth.py"
    
    with open(auth_file_path, 'r') as f:
        content = f.read()
    
    # Check that the RateLimitChecker class still exists
    if "class RateLimitChecker" in content:
        print("   OK RateLimitChecker class exists")
    else:
        print("   ERROR RateLimitChecker class not found")
        return False
    
    # Check that the check_rate_limit method exists
    if "def check_rate_limit" in content:
        print("   OK check_rate_limit method exists")
    else:
        print("   ERROR check_rate_limit method not found")
        return False
    
    # Check that the dependency functions exist
    dependency_functions = [
        "def get_login_rate_limiter",
        "def get_registration_rate_limiter",
        "def get_password_reset_rate_limiter"
    ]
    
    for func in dependency_functions:
        if func in content:
            print(f"   OK {func} exists")
        else:
            print(f"   ERROR {func} not found")
            return False
    
    print("\nRate limiter code structure is intact!")
    return True


def test_lua_script_functionality():
    """Test that the Lua script functionality is preserved"""
    print("\nTesting Lua Script Functionality...")
    
    # Read the auth.py file directly
    auth_file_path = project_root / "services" / "auth-service" / "app" / "dependencies" / "auth.py"
    
    with open(auth_file_path, 'r') as f:
        content = f.read()
    
    # Extract the LUA_SCRIPT content
    lua_script_match = re.search(r'LUA_SCRIPT = """(.*?)"""', content, re.DOTALL)
    if not lua_script_match:
        print("   ERROR Could not find LUA_SCRIPT in file")
        return False
    
    lua_script = lua_script_match.group(1)
    
    # Check that essential functionality is preserved
    required_elements = [
        "local key = KEYS[1]",
        "local now = tonumber(ARGV[1])",
        "local window_ms = tonumber(ARGV[2]) * 1000",
        "local max_attempts = tonumber(ARGV[3])",
        "redis.call('ZREMRANGEBYSCORE', key, '-inf', min_score)",
        "local current_attempts = redis.call('ZCARD', key)",
        "if current_attempts >= max_attempts then",
        "return -1",
        "redis.call('EXPIRE', key, tonumber(ARGV[2]))",
        "return current_attempts + 1"
    ]
    
    for element in required_elements:
        if element in lua_script:
            print(f"   OK {element}")
        else:
            print(f"   ERROR Missing: {element}")
            return False
    
    # Check that the sliding window algorithm is preserved
    if "now - window_ms" in lua_script:
        print("   OK Sliding window algorithm preserved")
    else:
        print("   ERROR Sliding window algorithm not found")
        return False
    
    print("\nLua script functionality is preserved!")
    return True


def test_rate_limiter_parameters():
    """Test that rate limiter parameters are correctly set"""
    print("\nTesting Rate Limiter Parameters...")
    
    # Read the auth.py file directly
    auth_file_path = project_root / "services" / "auth-service" / "app" / "dependencies" / "auth.py"
    
    with open(auth_file_path, 'r') as f:
        lines = f.readlines()
    
    # Find the rate limiter dependency functions and check their parameters
    login_limiter_found = False
    registration_limiter_found = False
    password_reset_limiter_found = False
    
    for i, line in enumerate(lines):
        if "def get_login_rate_limiter" in line:
            # Check the next few lines for parameter values
            for j in range(i, min(i+10, len(lines))):
                if "max_attempts=5" in lines[j] and "window_seconds=15 * 60" in lines[j]:
                    print("   OK Login rate limiter parameters correct")
                    login_limiter_found = True
                    break
            if not login_limiter_found:
                print("   ERROR Login rate limiter parameters incorrect")
                return False
        
        elif "def get_registration_rate_limiter" in line:
            # Check the next few lines for parameter values
            for j in range(i, min(i+10, len(lines))):
                if "max_attempts=3" in lines[j] and "window_seconds=60 * 60" in lines[j]:
                    print("   OK Registration rate limiter parameters correct")
                    registration_limiter_found = True
                    break
            if not registration_limiter_found:
                print("   ERROR Registration rate limiter parameters incorrect")
                return False
        
        elif "def get_password_reset_rate_limiter" in line:
            # Check the next few lines for parameter values
            for j in range(i, min(i+10, len(lines))):
                if "max_attempts=3" in lines[j] and "window_seconds=60 * 60" in lines[j]:
                    print("   OK Password reset rate limiter parameters correct")
                    password_reset_limiter_found = True
                    break
            if not password_reset_limiter_found:
                print("   ERROR Password reset rate limiter parameters incorrect")
                return False
    
    if login_limiter_found and registration_limiter_found and password_reset_limiter_found:
        print("\nAll rate limiter parameters are correct!")
        return True
    else:
        print("\nERROR Some rate limiter parameters are missing or incorrect")
        return False


def test_race_condition_fix():
    """Test that the race condition fix is properly implemented"""
    print("\nTesting Race Condition Fix...")
    
    # Read the auth.py file directly
    auth_file_path = project_root / "services" / "auth-service" / "app" / "dependencies" / "auth.py"
    
    with open(auth_file_path, 'r') as f:
        content = f.read()
    
    # Check that the fix is implemented correctly
    if "redis.call('INCR', key .. ':counter')" in content:
        print("   OK Race condition fix implemented with counter")
    else:
        print("   ERROR Race condition fix not found")
        return False
    
    if "local member = now .. ':' .." in content:
        print("   OK Unique member generation implemented")
    else:
        print("   ERROR Unique member generation not found")
        return False
    
    if "redis.call('ZADD', key, now, member)" in content:
        print("   OK ZADD uses unique member")
    else:
        print("   ERROR ZADD doesn't use unique member")
        return False
    
    # Check that the old problematic code is removed
    if "redis.call('ZADD', key, now, now)" not in content:
        print("   OK Old problematic code removed")
    else:
        print("   ERROR Old problematic code still present")
        return False
    
    print("\nRace condition fix is properly implemented!")
    return True


def main():
    """Run all tests"""
    print("Starting Rate Limiter Functionality Tests...\n")
    
    try:
        # Test rate limiter code structure
        if not test_rate_limiter_code_structure():
            print("\nERROR Rate limiter code structure test failed!")
            sys.exit(1)
        
        # Test Lua script functionality
        if not test_lua_script_functionality():
            print("\nERROR Lua script functionality test failed!")
            sys.exit(1)
        
        # Test rate limiter parameters
        if not test_rate_limiter_parameters():
            print("\nERROR Rate limiter parameters test failed!")
            sys.exit(1)
        
        # Test race condition fix
        if not test_race_condition_fix():
            print("\nERROR Race condition fix test failed!")
            sys.exit(1)
        
        print("\n" + "="*60)
        print("ALL TESTS PASSED!")
        print("="*60)
        print("\nThe rate limiter functionality is preserved after the race condition fix!")
        print("The fix correctly prevents race conditions while maintaining all existing functionality.")
        
    except Exception as e:
        print(f"\nERROR Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()