#!/usr/bin/env python3
"""
Test script to verify JSONDecodeError handling in auth service logout endpoint
"""

import asyncio
import aiohttp
import json
import sys
from typing import Dict, Any

# Configuration
AUTH_SERVICE_URL = "http://localhost:8001"
LOGOUT_ENDPOINT = f"{AUTH_SERVICE_URL}/api/v1/auth/logout"

# Test cases
TEST_CASES = [
    {
        "name": "Valid JSON with refresh token",
        "data": json.dumps({"refresh_token": "test-refresh-token"}),
        "content_type": "application/json",
        "expected_status": 401  # Unauthorized (no auth token)
    },
    {
        "name": "Invalid JSON - malformed",
        "data": '{"refresh_token": "test-token"',  # Missing closing brace
        "content_type": "application/json",
        "expected_status": 401  # Should still return 401, not 500
    },
    {
        "name": "Invalid JSON - trailing comma",
        "data": '{"refresh_token": "test-token",}',
        "content_type": "application/json",
        "expected_status": 401
    },
    {
        "name": "Empty body",
        "data": "",
        "content_type": "application/json",
        "expected_status": 401
    },
    {
        "name": "Non-JSON content type",
        "data": "refresh_token=test-token",
        "content_type": "application/x-www-form-urlencoded",
        "expected_status": 401
    },
    {
        "name": "Valid JSON without refresh token",
        "data": json.dumps({"other_field": "value"}),
        "content_type": "application/json",
        "expected_status": 401
    }
]


async def test_logout_json_handling():
    """Test various JSON parsing scenarios for logout endpoint"""
    print("Testing JSON error handling in logout endpoint...")
    print("=" * 60)
    
    async with aiohttp.ClientSession() as session:
        for test_case in TEST_CASES:
            print(f"\nTest: {test_case['name']}")
            print(f"Data: {test_case['data'][:50]}..." if len(test_case['data']) > 50 else f"Data: {test_case['data']}")
            
            try:
                headers = {
                    "Content-Type": test_case["content_type"]
                }
                
                # Add a fake authorization header to test the endpoint
                # (it will fail auth, but we're testing JSON parsing)
                headers["Authorization"] = "Bearer fake-token-for-testing"
                
                async with session.post(
                    LOGOUT_ENDPOINT,
                    data=test_case["data"].encode() if test_case["data"] else b"",
                    headers=headers
                ) as response:
                    status = response.status
                    
                    # Try to read response body
                    try:
                        response_data = await response.json()
                    except:
                        response_data = await response.text()
                    
                    print(f"Status: {status}")
                    print(f"Expected: {test_case['expected_status']}")
                    print(f"Response: {response_data}")
                    
                    # Check if we got expected status (not 500 Internal Server Error)
                    if status == 500:
                        print("❌ FAILED: Got 500 Internal Server Error - bare except might still be catching errors")
                    elif status == test_case["expected_status"]:
                        print("✅ PASSED: Got expected status code")
                    else:
                        print(f"⚠️  WARNING: Got {status}, expected {test_case['expected_status']}")
                    
            except Exception as e:
                print(f"❌ ERROR: {type(e).__name__}: {e}")
            
            print("-" * 40)


async def check_service_health():
    """Check if auth service is running"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{AUTH_SERVICE_URL}/health") as response:
                if response.status == 200:
                    print("✅ Auth service is healthy")
                    return True
                else:
                    print(f"⚠️  Auth service returned status {response.status}")
                    return False
    except Exception as e:
        print(f"❌ Cannot connect to auth service: {e}")
        return False


async def main():
    """Main test runner"""
    print("JSON Error Handling Test for Auth Service")
    print("=" * 60)
    
    # Check service health first
    if not await check_service_health():
        print("\n⚠️  Auth service is not available. Please ensure it's running.")
        print("You can start it with: docker-compose up auth-service")
        return 1
    
    print()
    
    # Run tests
    await test_logout_json_handling()
    
    print("\n" + "=" * 60)
    print("Test Summary:")
    print("- The logout endpoint should handle invalid JSON gracefully")
    print("- It should log JSONDecodeError with correlation ID")
    print("- It should NOT return 500 Internal Server Error")
    print("- Check the auth-service logs for proper error logging")
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)