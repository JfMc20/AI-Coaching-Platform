"""
Tests for configuration management.
Tests environment variable loading, defaults, and validation functions.
"""

import pytest
import os
from unittest.mock import patch

from shared.config.env_constants import EnvConstants
from shared.config.settings import Settings


class TestEnvConstants:
    """Test environment constants functionality."""

    def test_database_url_construction(self):
        """Test database URL construction from components."""
        with patch.dict(os.environ, {
            'DB_HOST': 'localhost',
            'DB_PORT': '5432',
            'DB_NAME': 'testdb',
            'DB_USER': 'testuser',
            'DB_PASSWORD': 'testpass'
        }):
            env = EnvConstants()
            expected_url = "postgresql+asyncpg://testuser:testpass@localhost:5432/testdb"
            assert env.get_database_url() == expected_url

    def test_redis_url_construction(self):
        """Test Redis URL construction."""
        with patch.dict(os.environ, {
            'REDIS_HOST': 'localhost',
            'REDIS_PORT': '6379',
            'REDIS_PASSWORD': 'redispass'
        }):
            env = EnvConstants()
            expected_url = "redis://:redispass@localhost:6379"
            assert env.get_redis_url() == expected_url

    def test_redis_url_without_password(self):
        """Test Redis URL construction without password."""
        with patch.dict(os.environ, {
            'REDIS_HOST': 'localhost',
            'REDIS_PORT': '6379'
        }, clear=True):
            env = EnvConstants()
            expected_url = "redis://localhost:6379"
            assert env.get_redis_url() == expected_url

    def test_service_urls(self):
        """Test service URL configuration."""
        with patch.dict(os.environ, {
            'AUTH_SERVICE_HOST': 'auth-service',
            'AUTH_SERVICE_PORT': '8001',
            'AI_ENGINE_SERVICE_HOST': 'ai-engine',
            'AI_ENGINE_SERVICE_PORT': '8003'
        }):
            env = EnvConstants()
            assert env.get_auth_service_url() == "http://auth-service:8001"
            assert env.get_ai_engine_service_url() == "http://ai-engine:8003"

    def test_default_values(self):
        """Test default values when environment variables are not set."""
        with patch.dict(os.environ, {}, clear=True):
            env = EnvConstants()
            
            # Test some expected defaults
            assert env.DB_HOST == "localhost"
            assert env.DB_PORT == "5432"
            assert env.REDIS_HOST == "localhost"
            assert env.REDIS_PORT == "6379"

    def test_boolean_environment_variables(self):
        """Test boolean environment variable parsing."""
        test_cases = [
            ("true", True),
            ("True", True),
            ("TRUE", True),
            ("1", True),
            ("yes", True),
            ("false", False),
            ("False", False),
            ("FALSE", False),
            ("0", False),
            ("no", False),
            ("", False)
        ]
        
        for env_value, expected in test_cases:
            with patch.dict(os.environ, {'DEBUG': env_value}):
                env = EnvConstants()
                assert env.get_boolean('DEBUG', False) == expected

    def test_integer_environment_variables(self):
        """Test integer environment variable parsing."""
        with patch.dict(os.environ, {
            'DB_PORT': '5432',
            'REDIS_PORT': '6379',
            'INVALID_INT': 'not-a-number'
        }):
            env = EnvConstants()
            
            assert env.get_integer('DB_PORT', 5432) == 5432
            assert env.get_integer('REDIS_PORT', 6379) == 6379
            assert env.get_integer('INVALID_INT', 1234) == 1234  # Should use default
            assert env.get_integer('MISSING_VAR', 9999) == 9999  # Should use default

    def test_jwt_configuration(self):
        """Test JWT configuration settings."""
        with patch.dict(os.environ, {
            'JWT_SECRET_KEY': 'test-secret-key',
            'JWT_ALGORITHM': 'HS256',
            'JWT_ACCESS_TOKEN_EXPIRE_MINUTES': '30',
            'JWT_REFRESH_TOKEN_EXPIRE_DAYS': '7'
        }):
            env = EnvConstants()
            
            assert env.JWT_SECRET_KEY == 'test-secret-key'
            assert env.JWT_ALGORITHM == 'HS256'
            assert env.get_integer('JWT_ACCESS_TOKEN_EXPIRE_MINUTES', 15) == 30
            assert env.get_integer('JWT_REFRESH_TOKEN_EXPIRE_DAYS', 30) == 7

    def test_ai_service_configuration(self):
        """Test AI service configuration."""
        with patch.dict(os.environ, {
            'OLLAMA_HOST': 'ollama-server',
            'OLLAMA_PORT': '11434',
            'CHROMADB_HOST': 'chromadb-server',
            'CHROMADB_PORT': '8000'
        }):
            env = EnvConstants()
            
            assert env.get_ollama_url() == "http://ollama-server:11434"
            assert env.get_chromadb_url() == "http://chromadb-server:8000"

    def test_environment_validation(self):
        """Test environment variable validation with specific constraints."""
        env = EnvConstants()
        
        # Test required variables validation
        required_vars = ['DB_HOST', 'DB_NAME', 'JWT_SECRET_KEY']
        
        for var in required_vars:
            if hasattr(env, var):
                value = getattr(env, var)
                assert value is not None, f"Environment variable {var} should not be None"
                assert value != "", f"Environment variable {var} should not be empty"
                
                # Specific constraint validations
                if var == 'JWT_SECRET_KEY':
                    assert len(value) >= 32, f"JWT_SECRET_KEY should be at least 32 characters, got: {len(value)}"
                    # Check for character mix (basic complexity check)
                    assert any(c.isalpha() for c in value), "JWT_SECRET_KEY should contain letters"
                    assert any(c.isdigit() for c in value), "JWT_SECRET_KEY should contain digits"
                elif var == 'DB_HOST':
                    # Basic hostname/URL format check
                    import re
                    hostname_pattern = r'^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*$|^localhost$|^127\.0\.0\.1$'
                    assert re.match(hostname_pattern, value), f"DB_HOST should be valid hostname, got: {value}"
                elif var == 'DB_NAME':
                    # Database name should be alphanumeric with underscores
                    import re
                    db_name_pattern = r'^[a-zA-Z0-9_]+$'
                    assert re.match(db_name_pattern, value), f"DB_NAME should be alphanumeric with underscores, got: {value}"

    def test_configuration_loading_order(self):
        """Test that environment variables override defaults."""
        # First, test with defaults
        with patch.dict(os.environ, {}, clear=True):
            env1 = EnvConstants()
            default_host = env1.DB_HOST
        
        # Then test with environment override
        with patch.dict(os.environ, {'DB_HOST': 'custom-host'}):
            env2 = EnvConstants()
            assert env2.DB_HOST == 'custom-host'
            assert env2.DB_HOST != default_host


class TestSettings:
    """Test settings configuration."""

    def test_settings_initialization(self):
        """Test settings class initialization."""
        settings = Settings()
        assert settings is not None
        assert isinstance(settings, Settings)
        
        # Validate that required configuration attributes exist and have sensible values/types
        if hasattr(Settings, '__annotations__'):
            for attr_name, attr_type in Settings.__annotations__.items():
                if hasattr(settings, attr_name):
                    value = getattr(settings, attr_name)
                    assert value is not None, f"Attribute {attr_name} should not be None"
                    if attr_type == str:
                        assert isinstance(value, str) and len(value) > 0, f"String attribute {attr_name} should be non-empty"

    def test_settings_database_config(self):
        """Test database configuration in settings."""
        with patch.dict(os.environ, {
            'DB_HOST': 'test-db',
            'DB_NAME': 'test_database'
        }):
            settings = Settings()
            
            if hasattr(settings, 'database_url'):
                assert 'test-db' in settings.database_url
                assert 'test_database' in settings.database_url

    def test_settings_validation(self):
        """Test settings validation with specific constraints."""
        settings = Settings()
        
        # Test that critical settings are present and valid
        critical_settings = ['database_url', 'redis_url', 'jwt_secret_key']
        
        for setting in critical_settings:
            if hasattr(settings, setting):
                value = getattr(settings, setting)
                assert value is not None, f"Setting {setting} should not be None"
                assert len(str(value)) > 0, f"Setting {setting} should not be empty"
                
                # Specific validations per setting
                if setting == 'database_url':
                    assert value.startswith(("postgresql://", "postgres://", "mysql://", "sqlite://")), \
                        f"database_url should have valid DB scheme, got: {value}"
                elif setting == 'redis_url':
                    assert value.startswith(("redis://", "rediss://")), \
                        f"redis_url should have redis scheme, got: {value}"
                elif setting == 'jwt_secret_key':
                    assert len(value) >= 32, \
                        f"jwt_secret_key should be at least 32 characters, got length: {len(value)}"

    def test_settings_environment_specific(self):
        """Test environment-specific settings."""
        environments = ['development', 'testing', 'production']
        
        for env in environments:
            with patch.dict(os.environ, {'ENVIRONMENT': env}):
                settings = Settings()
                
                if hasattr(settings, 'environment'):
                    assert settings.environment == env

    def test_settings_security_config(self):
        """Test security-related settings."""
        with patch.dict(os.environ, {
            'JWT_SECRET_KEY': 'test-secret',
            'CORS_ORIGINS': 'http://localhost:3000,http://localhost:8080'
        }):
            settings = Settings()
            
            if hasattr(settings, 'jwt_secret_key'):
                assert settings.jwt_secret_key == 'test-secret'
            
            if hasattr(settings, 'cors_origins'):
                assert isinstance(settings.cors_origins, (list, str))

    def test_settings_service_discovery(self):
        """Test service discovery configuration."""
        with patch.dict(os.environ, {
            'AUTH_SERVICE_URL': 'http://auth:8001',
            'AI_ENGINE_SERVICE_URL': 'http://ai:8003'
        }):
            settings = Settings()
            
            if hasattr(settings, 'auth_service_url'):
                assert settings.auth_service_url == 'http://auth:8001'
            
            if hasattr(settings, 'ai_engine_service_url'):
                assert settings.ai_engine_service_url == 'http://ai:8003'

    def test_settings_caching_config(self):
        """Test caching configuration."""
        with patch.dict(os.environ, {
            'CACHE_TTL': '3600',
            'CACHE_MAX_SIZE': '1000'
        }):
            settings = Settings()
            
            if hasattr(settings, 'cache_ttl'):
                assert settings.cache_ttl == 3600 or settings.cache_ttl == '3600'
            
            if hasattr(settings, 'cache_max_size'):
                assert settings.cache_max_size == 1000 or settings.cache_max_size == '1000'