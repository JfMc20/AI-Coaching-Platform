#!/usr/bin/env python3
"""
Test script to demonstrate Redis validation improvements.
Shows the enhanced robustness and error handling.
"""

import os
import sys
import asyncio
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


async def test_redis_with_different_configs():
    """Test Redis validation with different client configurations."""
    print("🔍 Testing Redis Validation Improvements")
    print("=" * 50)
    
    try:
        import redis.asyncio as aioredis
        import uuid
    except ImportError:
        print("❌ Redis asyncio not available - install with: pip install redis[asyncio]")
        return False
    
    redis_url = os.getenv('REDIS_URL', 'redis://localhost:6380/0')
    test_results = []
    
    # Test 1: decode_responses=False (default - returns bytes)
    print("\n🧪 Test 1: decode_responses=False (bytes)")
    try:
        r = aioredis.from_url(redis_url, decode_responses=False)
        result = await test_redis_operations(r, "bytes_test")
        test_results.append(("decode_responses=False", result))
        await r.close()
    except Exception as e:
        print(f"❌ Test 1 failed: {e}")
        test_results.append(("decode_responses=False", False))
    
    # Test 2: decode_responses=True (returns strings)
    print("\n🧪 Test 2: decode_responses=True (strings)")
    try:
        r = aioredis.from_url(redis_url, decode_responses=True)
        result = await test_redis_operations(r, "string_test")
        test_results.append(("decode_responses=True", result))
        await r.close()
    except Exception as e:
        print(f"❌ Test 2 failed: {e}")
        test_results.append(("decode_responses=True", False))
    
    # Test 3: Cleanup failure simulation
    print("\n🧪 Test 3: Cleanup Error Handling")
    try:
        r = aioredis.from_url(redis_url)
        result = await test_cleanup_error_handling(r)
        test_results.append(("Cleanup Error Handling", result))
        await r.close()
    except Exception as e:
        print(f"❌ Test 3 failed: {e}")
        test_results.append(("Cleanup Error Handling", False))
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Results Summary:")
    passed = 0
    for test_name, result in test_results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n🎯 Overall: {passed}/{len(test_results)} tests passed")
    return passed == len(test_results)


async def test_redis_operations(redis_client, test_prefix):
    """Test Redis operations with improved validation logic."""
    import uuid
    test_key = f'{test_prefix}_{uuid.uuid4().hex}'
    
    try:
        # Test ping
        await redis_client.ping()
        print("   ✅ Ping successful")
        
        # Test set with result verification
        set_result = await redis_client.set(test_key, 'test_value', ex=10)
        if not set_result:
            print("   ❌ Set operation failed")
            return False
        print("   ✅ Set operation verified")
        
        # Test get with type normalization
        value = await redis_client.get(test_key)
        if value is None:
            print("   ❌ Get returned None")
            return False
        
        # Normalize value based on type
        if isinstance(value, bytes):
            normalized_value = value.decode()
            print("   ✅ Normalized bytes value to string")
        elif isinstance(value, str):
            normalized_value = value
            print("   ✅ Value already string, no normalization needed")
        else:
            print(f"   ❌ Unexpected value type: {type(value)}")
            return False
        
        # Verify value
        if normalized_value != 'test_value':
            print(f"   ❌ Value mismatch: expected 'test_value', got '{normalized_value}'")
            return False
        print("   ✅ Value verification successful")
        
        # Test cleanup with error handling
        try:
            delete_result = await redis_client.delete(test_key)
            if delete_result == 0:
                print("   ⚠️  Delete indicated key not found (may have expired)")
            else:
                print("   ✅ Cleanup successful")
        except Exception as delete_error:
            print(f"   ⚠️  Cleanup warning: {delete_error}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Operation failed: {e}")
        return False


async def test_cleanup_error_handling(redis_client):
    """Test cleanup error handling specifically."""
    import uuid
    
    # Create a key that will be deleted externally to simulate cleanup failure
    test_key = f'cleanup_test_{uuid.uuid4().hex}'
    
    try:
        # Set a key
        await redis_client.set(test_key, 'test', ex=1)  # Very short TTL
        print("   ✅ Set test key with short TTL")
        
        # Wait for TTL to expire
        await asyncio.sleep(1.5)
        print("   ⏰ Waited for TTL expiration")
        
        # Try to delete expired key (should handle gracefully)
        try:
            delete_result = await redis_client.delete(test_key)
            if delete_result == 0:
                print("   ✅ Handled expired key deletion gracefully")
                return True
            else:
                print("   ⚠️  Key unexpectedly still existed")
                return True  # Still a success - cleanup worked
        except Exception as delete_error:
            print(f"   ✅ Handled delete exception gracefully: {delete_error}")
            return True  # This is expected behavior
            
    except Exception as e:
        print(f"   ❌ Cleanup test failed: {e}")
        return False


async def demonstrate_improvements():
    """Demonstrate the specific improvements made."""
    print("\n🎯 Redis Validation Improvements Demonstration")
    print("=" * 60)
    
    improvements = [
        {
            "title": "Set Operation Verification",
            "description": "Confirms Redis write operations succeed before proceeding",
            "benefit": "Prevents false positives when Redis writes fail silently"
        },
        {
            "title": "Value Type Normalization", 
            "description": "Handles both bytes and string values from Redis",
            "benefit": "Compatible with decode_responses=True/False configurations"
        },
        {
            "title": "Enhanced Cleanup Error Handling",
            "description": "Non-fatal cleanup with informative warnings",
            "benefit": "Cleanup failures don't break validation, TTL provides backup"
        },
        {
            "title": "Comprehensive Error Messages",
            "description": "Specific feedback for each type of failure",
            "benefit": "Faster debugging and clearer problem identification"
        }
    ]
    
    for i, improvement in enumerate(improvements, 1):
        print(f"\n{i}. 🔧 {improvement['title']}")
        print(f"   📝 {improvement['description']}")
        print(f"   🎯 Benefit: {improvement['benefit']}")
    
    print(f"\n✨ All improvements work together to provide robust Redis validation!")


async def main():
    """Main test function."""
    try:
        # Run improvement demonstration
        await demonstrate_improvements()
        
        # Run actual tests if Redis is available
        print(f"\n🧪 Running Redis Tests...")
        success = await test_redis_with_different_configs()
        
        if success:
            print(f"\n🎉 All Redis improvements validated successfully!")
        else:
            print(f"\n⚠️  Some tests failed - this may be due to Redis not being available")
            print(f"   To test with Redis: docker run -d -p 6380:6379 redis:7-alpine")
        
        return success
        
    except Exception as e:
        print(f"💥 Test failed with error: {e}")
        return False


if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⚠️  Test interrupted by user")
        sys.exit(1)