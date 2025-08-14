#!/usr/bin/env python3
"""
Script to verify that all test fixture fixes have been implemented correctly.
This script checks the test files and runs basic validation.
"""

import sys
import os
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def check_file_exists(file_path: str) -> bool:
    """Check if a file exists."""
    return Path(file_path).exists()


def check_string_in_file(file_path: str, search_string: str) -> bool:
    """Check if a string exists in a file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            return search_string in content
    except Exception:
        return False


def verify_comment_1_db_session_fixtures():
    """Verify Comment 1: Conflicting db_session fixtures are resolved."""
    print("✓ Checking Comment 1: Database session fixtures...")
    
    # Check that common_db_session exists in conftest.py
    conftest_has_common = check_string_in_file(
        "tests/conftest.py", 
        "async def common_db_session"
    )
    
    # Check that auth fixtures still has db_session
    auth_has_db_session = check_string_in_file(
        "tests/fixtures/auth_fixtures.py",
        "async def db_session"
    )
    
    if conftest_has_common and auth_has_db_session:
        print("  ✅ Database session fixtures are properly separated")
        return True
    else:
        print("  ❌ Database session fixtures issue not resolved")
        return False


def verify_comment_2_password_security():
    """Verify Comment 2: Password security fixture is added."""
    print("✓ Checking Comment 2: Password security fixture...")
    
    has_fixture = check_string_in_file(
        "tests/fixtures/auth_fixtures.py",
        "def password_security():"
    )
    
    if has_fixture:
        print("  ✅ Password security fixture is present")
        return True
    else:
        print("  ❌ Password security fixture is missing")
        return False


def verify_comment_3_async_decorators():
    """Verify Comment 3: Async fixtures use correct decorators."""
    print("✓ Checking Comment 3: Async fixture decorators...")
    
    # Check for pytest_asyncio.fixture usage
    auth_has_asyncio = check_string_in_file(
        "tests/fixtures/auth_fixtures.py",
        "@pytest_asyncio.fixture"
    )
    
    channel_has_asyncio = check_string_in_file(
        "tests/fixtures/channel_fixtures.py",
        "@pytest_asyncio.fixture"
    )
    
    if auth_has_asyncio and channel_has_asyncio:
        print("  ✅ Async fixtures use correct decorators")
        return True
    else:
        print("  ❌ Some async fixtures still use incorrect decorators")
        return False


def verify_comment_4_client_skipping():
    """Verify Comment 4: Client fixtures skip when app unavailable."""
    print("✓ Checking Comment 4: Client fixture skipping...")
    
    # Check for pytest.skip usage in client fixtures
    ai_has_skip = check_string_in_file(
        "tests/fixtures/ai_fixtures.py",
        "pytest.skip("
    )
    
    channel_has_skip = check_string_in_file(
        "tests/fixtures/channel_fixtures.py",
        "pytest.skip("
    )
    
    creator_has_skip = check_string_in_file(
        "tests/fixtures/creator_hub_fixtures.py",
        "pytest.skip("
    )
    
    if ai_has_skip and channel_has_skip and creator_has_skip:
        print("  ✅ Client fixtures properly skip when app unavailable")
        return True
    else:
        print("  ❌ Some client fixtures don't skip properly")
        return False


def verify_comment_5_dependency_cleanup():
    """Verify Comment 5: Dependency override cleanup is limited."""
    print("✓ Checking Comment 5: Dependency override cleanup...")
    
    # Check for specific cleanup instead of clear()
    has_specific_cleanup = check_string_in_file(
        "tests/fixtures/auth_fixtures.py",
        "app.dependency_overrides.pop(get_db, None)"
    )
    
    # Check that clear() is not used
    has_clear = check_string_in_file(
        "tests/fixtures/auth_fixtures.py",
        "app.dependency_overrides.clear()"
    )
    
    if has_specific_cleanup and not has_clear:
        print("  ✅ Dependency override cleanup is properly limited")
        return True
    else:
        print("  ❌ Dependency override cleanup issue not resolved")
        return False


def verify_comment_6_namespace_bridging():
    """Verify Comment 6: Namespace bridging is centralized."""
    print("✓ Checking Comment 6: Namespace bridging centralization...")
    
    # Check that conftest.py has namespace bridging
    conftest_has_bridging = check_string_in_file(
        "tests/conftest.py",
        "def enable_namespace_bridging():"
    )
    
    # Check that fixture files don't have duplicate bridging
    auth_no_bridging = not check_string_in_file(
        "tests/fixtures/auth_fixtures.py",
        "def enable_namespace_bridging():"
    )
    
    if conftest_has_bridging and auth_no_bridging:
        print("  ✅ Namespace bridging is centralized in conftest.py")
        return True
    else:
        print("  ❌ Namespace bridging is still duplicated")
        return False


def verify_comment_7_sync_containers():
    """Verify Comment 7: Container fixtures are sync."""
    print("✓ Checking Comment 7: Container fixtures are sync...")
    
    # Check that container fixtures don't use async def
    postgres_is_sync = check_string_in_file(
        "tests/conftest.py",
        "def postgres_container():"
    ) and not check_string_in_file(
        "tests/conftest.py",
        "async def postgres_container():"
    )
    
    redis_is_sync = check_string_in_file(
        "tests/conftest.py",
        "def redis_container():"
    ) and not check_string_in_file(
        "tests/conftest.py",
        "async def redis_container():"
    )
    
    if postgres_is_sync and redis_is_sync:
        print("  ✅ Container fixtures are synchronous")
        return True
    else:
        print("  ❌ Some container fixtures are still async")
        return False


def verify_comment_8_unified_database():
    """Verify Comment 8: Database containers are unified."""
    print("✓ Checking Comment 8: Database container unification...")
    
    # Check that auth fixtures use shared engine
    uses_shared_engine = check_string_in_file(
        "tests/fixtures/auth_fixtures.py",
        "async def test_engine(test_db_engine):"
    )
    
    if uses_shared_engine:
        print("  ✅ Database containers are unified")
        return True
    else:
        print("  ❌ Database containers are not unified")
        return False


def verify_comment_9_env_vars():
    """Verify Comment 9: Environment variable accessor is fixed."""
    print("✓ Checking Comment 9: Environment variable accessor...")
    
    # Check for proper os.getenv usage
    has_proper_env = check_string_in_file(
        "tests/conftest.py",
        'os.getenv("AUTH_SERVICE_URL"'
    )
    
    # Check that get_env_value is not used incorrectly
    no_bad_accessor = not check_string_in_file(
        "tests/conftest.py",
        "get_env_value(AUTH_SERVICE_URL"
    )
    
    if has_proper_env and no_bad_accessor:
        print("  ✅ Environment variable accessor is fixed")
        return True
    else:
        print("  ❌ Environment variable accessor issue not resolved")
        return False


def verify_comment_10_model_registration():
    """Verify Comment 10: Models are registered before table creation."""
    print("✓ Checking Comment 10: Model registration...")
    
    # Check for model imports in auth fixtures
    has_model_imports = check_string_in_file(
        "tests/fixtures/auth_fixtures.py",
        "from shared.models.database import Creator"
    )
    
    if has_model_imports:
        print("  ✅ Models are properly imported before table creation")
        return True
    else:
        print("  ❌ Model registration issue not resolved")
        return False


def verify_comment_11_redis_cleanup():
    """Verify Comment 11: Redis cleanup is scoped properly."""
    print("✓ Checking Comment 11: Redis cleanup scoping...")
    
    # Check that autouse=True is removed
    no_autouse = not check_string_in_file(
        "tests/conftest.py",
        "autouse=True"
    )
    
    # Check that cleanup fixture exists without autouse
    has_cleanup = check_string_in_file(
        "tests/conftest.py",
        "async def cleanup_test_data"
    )
    
    if no_autouse and has_cleanup:
        print("  ✅ Redis cleanup is properly scoped")
        return True
    else:
        print("  ❌ Redis cleanup scoping issue not resolved")
        return False


def main():
    """Run all verification checks."""
    print("🔍 Verifying test fixture fixes implementation...\n")
    
    checks = [
        verify_comment_1_db_session_fixtures,
        verify_comment_2_password_security,
        verify_comment_3_async_decorators,
        verify_comment_4_client_skipping,
        verify_comment_5_dependency_cleanup,
        verify_comment_6_namespace_bridging,
        verify_comment_7_sync_containers,
        verify_comment_8_unified_database,
        verify_comment_9_env_vars,
        verify_comment_10_model_registration,
        verify_comment_11_redis_cleanup,
    ]
    
    results = []
    for check in checks:
        try:
            result = check()
            results.append(result)
        except Exception as e:
            print(f"  ❌ Error running check: {e}")
            results.append(False)
        print()
    
    # Summary
    passed = sum(results)
    total = len(results)
    
    print("=" * 50)
    print(f"📊 VERIFICATION SUMMARY: {passed}/{total} checks passed")
    
    if passed == total:
        print("🎉 All test fixture fixes have been successfully implemented!")
        return 0
    else:
        print("⚠️  Some issues remain. Please review the failed checks above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())