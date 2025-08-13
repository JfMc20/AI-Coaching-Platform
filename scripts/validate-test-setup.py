#!/usr/bin/env python3
"""
Test setup validation script.
Validates that the testing environment is properly configured.
"""

import os
import sys
import asyncio
import asyncpg
import redis
from pathlib import Path


async def validate_database_connection():
    """Validate PostgreSQL database connection."""
    database_url = os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5433/ai_platform_test')
    conn = None
    
    try:
        conn = await asyncpg.connect(database_url)
        
        # Test basic query
        result = await conn.fetchval('SELECT 1')
        if result != 1:
            print("❌ Database basic query failed: Expected 1, got {result}")
            return False
        
        # Check if test database exists
        db_exists = await conn.fetchval(
            "SELECT EXISTS(SELECT 1 FROM pg_database WHERE datname = 'ai_platform_test')"
        )
        if not db_exists:
            print("❌ Test database 'ai_platform_test' does not exist")
            return False
        
        # Check extensions
        extensions = await conn.fetch("SELECT extname FROM pg_extension")
        extension_names = [ext['extname'] for ext in extensions]
        
        required_extensions = ['uuid-ossp', 'pgcrypto']
        for ext in required_extensions:
            if ext not in extension_names:
                print(f"⚠️  Extension '{ext}' not found, but may be installed later")
        
        print("✅ Database connection: OK")
        return True
        
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False
    finally:
        if conn:
            try:
                await conn.close()
            except Exception as e:
                print(f"⚠️  Warning: Failed to close database connection: {e}")


async def validate_redis_connection():
    """Validate Redis connection."""
    try:
        import redis.asyncio as aioredis
        import uuid
        
        redis_url = os.getenv('REDIS_URL', 'redis://localhost:6380/0')
        r = aioredis.from_url(redis_url)
        
        # Generate unique key to avoid collisions in shared environments
        test_key = f'test_key_{uuid.uuid4().hex}'
        
        try:
            # Test basic operation
            await r.ping()
            
            # Test set/get with TTL for automatic cleanup
            set_result = await r.set(test_key, 'test_value', ex=5)  # 5 second TTL
            
            # Verify set operation succeeded
            if not set_result:
                print("❌ Redis set operation failed")
                return False
            
            value = await r.get(test_key)
            
            # Check if value is not None before processing
            if value is None:
                print("❌ Redis get operation returned None")
                return False
            
            # Normalize value - handle both bytes and string types
            if isinstance(value, bytes):
                normalized_value = value.decode()
            elif isinstance(value, str):
                normalized_value = value
            else:
                print(f"❌ Redis returned unexpected value type: {type(value)}")
                return False
            
            # Use normalized value for comparison
            if normalized_value != 'test_value':
                print(f"❌ Redis value mismatch: expected 'test_value', got '{normalized_value}'")
                return False
                
            # Manual cleanup with error handling (TTL provides backup)
            try:
                delete_result = await r.delete(test_key)
                if delete_result == 0:
                    print("⚠️  Warning: Redis delete operation indicated key was not found (may have expired)")
            except Exception as delete_error:
                print(f"⚠️  Warning: Redis cleanup failed: {delete_error} (TTL will handle cleanup)")
            
            print("✅ Redis connection: OK")
            return True
            
        finally:
            await r.close()
        
    except Exception as e:
        print(f"❌ Redis connection failed: {e}")
        return False


def validate_environment_variables():
    """Validate required environment variables."""
    required_vars = [
        'DATABASE_URL',
        'REDIS_URL',
        'JWT_SECRET_KEY',
        'ENVIRONMENT'
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ Missing environment variables: {', '.join(missing_vars)}")
        return False
    
    # Validate environment value
    env = os.getenv('ENVIRONMENT')
    if env not in ['testing', 'development']:
        print(f"⚠️  Environment is '{env}', expected 'testing' or 'development'")
    
    print("✅ Environment variables: OK")
    return True


def validate_test_directories():
    """Validate test directories exist and are writable."""
    test_dirs = [
        'test-results',
        'coverage',
        'logs'
    ]
    
    for dir_name in test_dirs:
        dir_path = Path(dir_name)
        
        # Create directory if it doesn't exist
        dir_path.mkdir(exist_ok=True)
        
        # Test write permissions
        test_file = dir_path / 'test_write.tmp'
        try:
            test_file.write_text('test')
            test_file.unlink()
        except Exception as e:
            print(f"❌ Cannot write to {dir_name}: {e}")
            return False
    
    print("✅ Test directories: OK")
    return True


def validate_python_dependencies():
    """Validate required Python packages are installed."""
    import importlib.util
    import importlib.metadata
    
    # Mapping of pip package names to their import names
    package_mapping = {
        'pytest': 'pytest',
        'pytest-asyncio': 'pytest_asyncio',
        'pytest-cov': 'pytest_cov',
        'httpx': 'httpx',
        'asyncpg': 'asyncpg',
        'redis': 'redis',
        'testcontainers': 'testcontainers'
    }
    
    missing_packages = []
    
    for pip_name, import_name in package_mapping.items():
        try:
            # First try to find the spec for the import name
            spec = importlib.util.find_spec(import_name)
            if spec is None:
                # If spec not found, try checking installed distributions
                try:
                    importlib.metadata.distribution(pip_name)
                except importlib.metadata.PackageNotFoundError:
                    missing_packages.append(pip_name)
        except Exception as e:
            print(f"⚠️  Warning: Could not check package {pip_name}: {e}")
            missing_packages.append(pip_name)
    
    if missing_packages:
        print(f"❌ Missing Python packages: {', '.join(missing_packages)}")
        print("💡 Install with: pip install -r requirements-test.txt")
        return False
    
    print("✅ Python dependencies: OK")
    return True


async def main():
    """Run all validation checks."""
    print("🔍 Validating test setup...")
    print("=" * 50)
    
    checks = [
        validate_environment_variables(),
        validate_test_directories(),
        validate_python_dependencies(),
        await validate_redis_connection(),
        await validate_database_connection()
    ]
    
    success_count = sum(checks)
    total_checks = len(checks)
    
    print("=" * 50)
    print(f"📊 Validation Results: {success_count}/{total_checks} checks passed")
    
    if success_count == total_checks:
        print("🎉 Test setup validation completed successfully!")
        return True
    else:
        print("❌ Test setup validation failed!")
        print("💡 Please fix the issues above before running tests")
        return False


if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⚠️  Validation interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"💥 Validation failed with error: {e}")
        sys.exit(1)