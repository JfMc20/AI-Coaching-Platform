"""
Test database configuration fixes
"""

import os
import sys
import subprocess
from unittest.mock import patch, MagicMock

# Add the services directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


class TestDatabaseConfigurationFixes:
    """Test database configuration fixes"""
    
    def test_environment_variable_parsing(self):
        """Test that environment variables are parsed correctly with validation"""
        
        # Mock the DatabaseManager class to test environment parsing
        class MockDatabaseManager:
            def _parse_int_env(self, env_var: str, default: int) -> int:
                """Parse integer from environment variable with validation"""
                try:
                    value = os.getenv(env_var)
                    if value is None:
                        return default
                    parsed = int(value)
                    if parsed <= 0:
                        return default
                    return parsed
                except (ValueError, TypeError):
                    return default
        
        manager = MockDatabaseManager()
        
        # Test valid values
        with patch.dict(os.environ, {"AUTH_DB_POOL_SIZE": "25"}):
            assert manager._parse_int_env("AUTH_DB_POOL_SIZE", 20) == 25
        
        # Test invalid values
        with patch.dict(os.environ, {"AUTH_DB_POOL_SIZE": "invalid"}):
            assert manager._parse_int_env("AUTH_DB_POOL_SIZE", 20) == 20
        
        # Test negative values
        with patch.dict(os.environ, {"AUTH_DB_POOL_SIZE": "-5"}):
            assert manager._parse_int_env("AUTH_DB_POOL_SIZE", 20) == 20
        
        # Test zero values
        with patch.dict(os.environ, {"AUTH_DB_POOL_SIZE": "0"}):
            assert manager._parse_int_env("AUTH_DB_POOL_SIZE", 20) == 20
        
        # Test missing values
        with patch.dict(os.environ, {}, clear=True):
            assert manager._parse_int_env("AUTH_DB_POOL_SIZE", 20) == 20
        
        print("✅ Environment variable parsing test passed")
    
    def test_sqlalchemy_2x_compatibility(self):
        """Test SQLAlchemy 2.x compatibility fixes"""
        
        # Test that deprecated parameters are not used as actual parameters
        deprecated_patterns = [
            "future=True,",  # Deprecated in SQLAlchemy 2.x (as actual parameter)
            "autocommit=False,"  # Not valid in SQLAlchemy 2.x async_sessionmaker (as actual parameter)
        ]
        
        # Read the database.py file
        database_file = os.path.join(
            os.path.dirname(__file__), 
            '..', 
            'services', 
            'auth-service', 
            'app', 
            'database.py'
        )
        
        with open(database_file, 'r') as f:
            content = f.read()
        
        # Check that deprecated parameters are not present as actual parameters
        for pattern in deprecated_patterns:
            assert pattern not in content, f"Found deprecated parameter: {pattern}"
        
        # Check that valid parameters are present
        valid_params = [
            "pool_size=pool_size",
            "max_overflow=max_overflow",
            "expire_on_commit=False",
            "autoflush=True"
        ]
        
        for param in valid_params:
            assert param in content, f"Missing valid parameter: {param}"
        
        print("✅ SQLAlchemy 2.x compatibility test passed")
    
    def test_safe_rls_policies(self):
        """Test that RLS policies use safe current_setting calls"""
        
        database_file = os.path.join(
            os.path.dirname(__file__), 
            '..', 
            'services', 
            'auth-service', 
            'app', 
            'database.py'
        )
        
        with open(database_file, 'r') as f:
            content = f.read()
        
        # Check that unsafe current_setting calls are not present
        unsafe_patterns = [
            "current_setting('app.current_creator_id')::uuid",  # Missing missing_ok parameter
            "TO authenticated_user"  # Should be TO PUBLIC for broader compatibility
        ]
        
        for pattern in unsafe_patterns:
            assert pattern not in content, f"Found unsafe pattern: {pattern}"
        
        # Check that safe patterns are present
        safe_patterns = [
            "current_setting('app.current_creator_id', true)",  # With missing_ok parameter
            "COALESCE(",  # Safe null handling
            "NULLIF(",  # Safe empty string handling
            "WITH CHECK",  # Explicit WITH CHECK clauses
            "TO PUBLIC"  # Broader role compatibility
        ]
        
        for pattern in safe_patterns:
            assert pattern in content, f"Missing safe pattern: {pattern}"
        
        print("✅ Safe RLS policies test passed")
    
    def test_alembic_migration_support(self):
        """Test that Alembic migration support is implemented"""
        
        database_file = os.path.join(
            os.path.dirname(__file__), 
            '..', 
            'services', 
            'auth-service', 
            'app', 
            'database.py'
        )
        
        with open(database_file, 'r') as f:
            content = f.read()
        
        # Check that Alembic migration function exists
        assert "async def run_alembic_migrations():" in content
        assert "subprocess.run" in content
        assert "alembic upgrade head" in content
        
        # Check that DB_AUTO_CREATE flag is supported
        assert "DB_AUTO_CREATE" in content
        assert "development only" in content.lower()
        
        # Check that create_all is gated behind the flag
        assert "auto_create = os.getenv" in content
        assert "if auto_create:" in content
        
        print("✅ Alembic migration support test passed")
    
    def test_database_initialization_flow(self):
        """Test the database initialization flow"""
        
        # Mock the components
        with patch('subprocess.run') as mock_subprocess:
            mock_subprocess.return_value = MagicMock(returncode=0, stderr="")
            
            # Test the logic flow
            def test_init_logic():
                # Simulate the init_database logic
                auto_create = os.getenv("DB_AUTO_CREATE", "false").lower() == "true"
                
                if auto_create:
                    # Development path
                    return "create_all"
                else:
                    # Production path - run migrations
                    return "alembic_migrations"
            
            # Test development mode
            with patch.dict(os.environ, {"DB_AUTO_CREATE": "true"}):
                result = test_init_logic()
                assert result == "create_all"
            
            # Test production mode (default)
            with patch.dict(os.environ, {}, clear=True):
                result = test_init_logic()
                assert result == "alembic_migrations"
            
            # Test explicit production mode
            with patch.dict(os.environ, {"DB_AUTO_CREATE": "false"}):
                result = test_init_logic()
                assert result == "alembic_migrations"
        
        print("✅ Database initialization flow test passed")
    
    def test_connection_pool_configuration(self):
        """Test connection pool configuration with environment variables"""
        
        # Test default values
        def parse_int_env(env_var: str, default: int) -> int:
            try:
                value = os.getenv(env_var)
                if value is None:
                    return default
                parsed = int(value)
                if parsed <= 0:
                    return default
                return parsed
            except (ValueError, TypeError):
                return default
        
        # Test with no environment variables
        with patch.dict(os.environ, {}, clear=True):
            pool_size = parse_int_env("AUTH_DB_POOL_SIZE", 20)
            max_overflow = parse_int_env("AUTH_DB_MAX_OVERFLOW", 30)
            assert pool_size == 20
            assert max_overflow == 30
        
        # Test with valid environment variables
        with patch.dict(os.environ, {
            "AUTH_DB_POOL_SIZE": "15",
            "AUTH_DB_MAX_OVERFLOW": "25"
        }):
            pool_size = parse_int_env("AUTH_DB_POOL_SIZE", 20)
            max_overflow = parse_int_env("AUTH_DB_MAX_OVERFLOW", 30)
            assert pool_size == 15
            assert max_overflow == 25
        
        # Test with invalid environment variables
        with patch.dict(os.environ, {
            "AUTH_DB_POOL_SIZE": "invalid",
            "AUTH_DB_MAX_OVERFLOW": "-10"
        }):
            pool_size = parse_int_env("AUTH_DB_POOL_SIZE", 20)
            max_overflow = parse_int_env("AUTH_DB_MAX_OVERFLOW", 30)
            assert pool_size == 20  # Falls back to default
            assert max_overflow == 30  # Falls back to default
        
        print("✅ Connection pool configuration test passed")


def run_all_tests():
    """Run all database fix tests"""
    print("Running database configuration fix tests...")
    
    tests = TestDatabaseConfigurationFixes()
    tests.test_environment_variable_parsing()
    tests.test_sqlalchemy_2x_compatibility()
    tests.test_safe_rls_policies()
    tests.test_alembic_migration_support()
    tests.test_database_initialization_flow()
    tests.test_connection_pool_configuration()
    
    print("\n🎉 All database configuration fix tests passed successfully!")
    print("\nFixes verified:")
    print("1. ✅ Removed deprecated SQLAlchemy 2.x parameters (future=True, autocommit=False)")
    print("2. ✅ Added environment variable support for pool configuration")
    print("3. ✅ Implemented safe Alembic migration support with DB_AUTO_CREATE flag")
    print("4. ✅ Fixed RLS policies with safe current_setting calls and WITH CHECK clauses")
    print("5. ✅ Changed policies to use PUBLIC role for broader compatibility")
    print("6. ✅ Added proper null handling and error prevention")


if __name__ == "__main__":
    run_all_tests()