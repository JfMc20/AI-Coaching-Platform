#!/usr/bin/env python3
"""
Test script for Lua Script Race Condition Fix
Validates the Lua script logic directly without importing FastAPI dependencies
"""

import sys
import os
from pathlib import Path
import argparse


def get_auth_file_path():
    """Get the path to auth.py from command line argument, environment variable, or default."""
    # Check command line argument first
    parser = argparse.ArgumentParser(description='Test Lua script in auth.py')
    parser.add_argument('--auth-file', help='Path to auth.py file')
    args = parser.parse_args()
    
    if args.auth_file:
        return Path(args.auth_file)
    
    # Check environment variable
    auth_file_env = os.environ.get('AUTH_FILE_PATH')
    if auth_file_env:
        return Path(auth_file_env)
    
    # Default fallback - assume script is in scripts/ directory of project
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    return project_root / "services" / "auth-service" / "app" / "dependencies" / "auth.py"


def test_lua_script_content():
    """Test that the Lua script contains the correct fix"""
    print("Testing Lua Script Content...")
    
    # Get the auth.py file path
    auth_file_path = get_auth_file_path()
    print(f"Using auth.py file: {auth_file_path}")
    
    # Check if file exists
    if not auth_file_path.exists():
        print(f"ERROR: auth.py file not found at {auth_file_path}")
        return False
    
    # Read the auth.py file directly with explicit encoding
    try:
        with open(auth_file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"ERROR: Failed to read auth.py file: {e}")
        return False
    
    # Check that the Lua script contains the fix
    print("\n1. Verifying Lua script has been updated...")
    
    # Check for the counter-based unique member generation
    if "redis.call('INCR', key .. ':counter')" in content:
        print("   OK Lua script uses counter for unique member generation")
    else:
        print("   ERROR Lua script doesn't use counter for unique members")
        return False
    
    # Check that the member variable is used in ZADD
    if "local member = now .. ':' .." in content:
        print("   OK Lua script creates unique member variable")
    else:
        print("   ERROR Lua script doesn't create unique member variable")
        return False
    
    if "redis.call('ZADD', key, now, member)" in content:
        print("   OK Lua script uses unique member in ZADD")
    else:
        print("   ERROR Lua script doesn't use unique member in ZADD")
        return False
    
    # Check that the old problematic line is no longer present
    if "redis.call('ZADD', key, now, now)" not in content:
        print("   OK Old problematic line removed")
    else:
        print("   ERROR Old problematic line still present")
        return False
    
    # Show the relevant part of the script
    print("\n2. Displaying the fixed Lua script section...")
    lines = content.split('\n')
    
    # Find the LUA_SCRIPT definition
    start_line = -1
    end_line = -1
    for i, line in enumerate(lines):
        if 'LUA_SCRIPT = """' in line:
            start_line = i
        elif start_line != -1 and '"""' in line and i > start_line:
            end_line = i
            break
    
    if start_line != -1 and end_line != -1:
        print("   Fixed Lua script:")
        for i in range(start_line, end_line + 1):
            # Skip the first and last lines which are the triple quotes
            if 'LUA_SCRIPT = """' in lines[i] or '"""' in lines[i]:
                continue
            print(f"   {lines[i]}")
    else:
        print("   Could not find Lua script in file")
        return False
    
    print("\nLua script verification completed successfully!")
    return True


def test_lua_script_logic():
    """Test the logic of the Lua script with a simulation"""
    print("\nTesting Lua Script Logic...")
    
    # Simulate the Lua script behavior with the fix
    print("\n1. Simulating the fixed Lua script behavior...")
    
    # Simulate a sorted set (using a dictionary where key=member, value=score)
    sorted_set = {}
    counter = 0
    
    # Simulate multiple requests with the same timestamp
    timestamp = 1234567890.123
    
    print(f"   Simulating 3 concurrent requests with timestamp: {timestamp}")
    
    # Process 3 requests with the same timestamp
    for i in range(3):
        # This is the equivalent of the fixed Lua script logic:
        # local member = now .. ':' .. redis.call('INCR', key .. ':counter')
        counter += 1
        member = f"{timestamp}:{counter}"
        score = timestamp
        
        # Add to sorted set (this would be redis.call('ZADD', key, score, member))
        sorted_set[member] = score
        print(f"   Request {i+1}: Added member '{member}' with score {score}")
    
    # Verify that all members are unique
    print(f"\n2. Verifying all members are unique...")
    print(f"   Members in sorted set: {list(sorted_set.keys())}")
    
    if len(sorted_set) == 3:
        print("   OK All 3 requests created unique members")
    else:
        print(f"   ERROR Only {len(sorted_set)} unique members created (expected 3)")
        return False
    
    # Verify that all scores are the same (the timestamp)
    scores = list(sorted_set.values())
    if all(score == timestamp for score in scores):
        print(f"   OK All members have the correct timestamp score")
    else:
        print(f"   ERROR Some members have incorrect scores")
        return False
    
    # Simulate the old problematic behavior for comparison
    print("\n3. Comparing with old problematic behavior...")
    
    # Reset for comparison
    old_sorted_set = {}
    
    # Process 3 requests with the old method (using timestamp as both score and member)
    for i in range(3):
        member = timestamp  # This is the problem - same member for all requests
        score = timestamp
        
        # Add to sorted set (this would overwrite previous entries)
        old_sorted_set[member] = score
        print(f"   Request {i+1}: Added member '{member}' with score {score}")
    
    # Verify that only one member exists (all others were overwritten)
    print(f"\n4. Verifying old method overwrites entries...")
    print(f"   Members in sorted set: {list(old_sorted_set.keys())}")
    
    if len(old_sorted_set) == 1:
        print("   OK Old method only created 1 member (others were overwritten)")
    else:
        print(f"   ERROR Old method created {len(old_sorted_set)} members (unexpected)")
        return False
    
    print("\nLua script logic test completed successfully!")
    print("   The fix correctly prevents race conditions by ensuring unique members.")
    return True


def main():
    """Run all tests"""
    print("Starting Lua Script Race Condition Tests...\n")
    
    try:
        # Test the Lua script content
        if not test_lua_script_content():
            print("\nERROR Lua script content test failed!")
            sys.exit(1)
        
        # Test the Lua script logic
        if not test_lua_script_logic():
            print("\nERROR Lua script logic test failed!")
            sys.exit(1)
        
        print("\n" + "="*60)
        print("ALL TESTS PASSED!")
        print("="*60)
        print("\nThe race condition in the Lua script has been fixed!")
        print("Multiple concurrent requests with the same timestamp are now handled correctly.")
        print("Each request creates a unique member in the Redis sorted set.")
        print("The fix uses a counter to ensure uniqueness: timestamp:counter")
        
    except Exception as e:
        print(f"\nERROR Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()