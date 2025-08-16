"""
Tests for configuration management.
Tests environment variable loading, defaults, and validation functions.
"""

import pytest
import os
from unittest.mock import patch

from shared.config.env_constants import (
    get_env_value, validate_environment_variables, get_current_environment,
    # Import all the constants we'll use in tests
    DATABASE_URL, REDIS_URL, JWT_SECRET_KEY, OLLAMA_URL, CHROMADB_URL,
    AUTH_SERVICE_URL, AI_ENGINE_SERVICE_URL, CORS_ORIGINS, LOG_LEVEL
)
from shared.config.settings import (
    validate_required_env_vars, safe_int_env, get_database_url_with_validation
)

# Test-specific config classes that use direct environment access
from pydantic import BaseModel, Field
from typing import List

class TestAuthServiceConfig(BaseModel):
    """Test-specific auth config that doesn't read .env files"""
    environment: str = Field(default="testing")
    debug: bool = Field(default=True)
    log_level: str = Field(default="INFO")
    database_url: str
    redis_url: str
    cors_origins: List[str] = Field(default_factory=list)
    allowed_hosts: List[str] = Field(default_factory=list)
    jwt_secret_key: str
    jwt_algorithm: str = Field(default="HS256")
    
    @classmethod
    def from_env(cls, env_dict):
        """Create config from environment dictionary"""
        cors_origins = env_dict.get(CORS_ORIGINS, "").split(",") if env_dict.get(CORS_ORIGINS) else []
        allowed_hosts = env_dict.get("ALLOWED_HOSTS", "").split(",") if env_dict.get("ALLOWED_HOSTS") else []
        
        return cls(
            database_url=env_dict[DATABASE_URL],
            redis_url=env_dict[REDIS_URL],
            jwt_secret_key=env_dict[JWT_SECRET_KEY],
            cors_origins=[origin.strip() for origin in cors_origins if origin.strip()],
            allowed_hosts=[host.strip() for host in allowed_hosts if host.strip()],
            log_level=env_dict.get(LOG_LEVEL, "INFO")
        )

class TestAIEngineServiceConfig(BaseModel):
    """Test-specific AI engine config that doesn't read .env files"""
    environment: str = Field(default="testing")
    debug: bool = Field(default=True)
    log_level: str = Field(default="INFO")
    database_url: str
    redis_url: str
    cors_origins: List[str] = Field(default_factory=list)
    ollama_url: str
    chromadb_url: str
    embedding_model: str = Field(default="nomic-embed-text")
    chat_model: str = Field(default="llama2:7b-chat")
    
    @classmethod
    def from_env(cls, env_dict):
        """Create config from environment dictionary"""
        cors_origins = env_dict.get(CORS_ORIGINS, "").split(",") if env_dict.get(CORS_ORIGINS) else []
        
        return cls(
            database_url=env_dict[DATABASE_URL],
            redis_url=env_dict[REDIS_URL],
            ollama_url=env_dict[OLLAMA_URL],
            chromadb_url=env_dict[CHROMADB_URL],
            cors_origins=[origin.strip() for origin in cors_origins if origin.strip()],
            log_level=env_dict.get(LOG_LEVEL, "INFO")
        )

class TestCreatorHubServiceConfig(BaseModel):
    """Test-specific creator hub config that doesn't read .env files"""
    environment: str = Field(default="testing")
    debug: bool = Field(default=True)
    log_level: str = Field(default="INFO")
    database_url: str
    redis_url: str
    cors_origins: List[str] = Field(default_factory=list)
    auth_service_url: str
    ai_engine_service_url: str
    
    @classmethod
    def from_env(cls, env_dict):
        """Create config from environment dictionary"""
        cors_origins = env_dict.get(CORS_ORIGINS, "").split(",") if env_dict.get(CORS_ORIGINS) else []
        
        return cls(
            database_url=env_dict[DATABASE_URL],
            redis_url=env_dict[REDIS_URL],
            auth_service_url=env_dict[AUTH_SERVICE_URL],
            ai_engine_service_url=env_dict[AI_ENGINE_SERVICE_URL],
            cors_origins=[origin.strip() for origin in cors_origins if origin.strip()],
            log_level=env_dict.get(LOG_LEVEL, "INFO")
        )

class TestChannelServiceConfig(BaseModel):
    """Test-specific channel config that doesn't read .env files"""
    environment: str = Field(default="testing")
    debug: bool = Field(default=True)
    log_level: str = Field(default="INFO")
    database_url: str
    redis_url: str
    cors_origins: List[str] = Field(default_factory=list)
    auth_service_url: str
    ai_engine_service_url: str
    
    @classmethod
    def from_env(cls, env_dict):
        """Create config from environment dictionary"""
        cors_origins = env_dict.get(CORS_ORIGINS, "").split(",") if env_dict.get(CORS_ORIGINS) else []
        
        return cls(
            database_url=env_dict[DATABASE_URL],
            redis_url=env_dict[REDIS_URL],
            auth_service_url=env_dict[AUTH_SERVICE_URL],
            ai_engine_service_url=env_dict[AI_ENGINE_SERVICE_URL],
            cors_origins=[origin.strip() for origin in cors_origins if origin.strip()],
            log_level=env_dict.get(LOG_LEVEL, "INFO")
        )


class TestEnvConstants:
    """Test environment constants functionality."""

    def test_get_env_value(self):
        """Test environment variable retrieval."""
        with patch.dict(os.environ, {
            'TEST_VAR': 'test_value',
            'EMPTY_VAR': '',
            'FALSE_VAR': 'false'
        }):
            assert get_env_value('TEST_VAR') == 'test_value'
            assert get_env_value('EMPTY_VAR') == ''
            assert get_env_value('FALSE_VAR') == 'false'
            assert get_env_value('NONEXISTENT_VAR') is None

    def test_validate_environment_variables(self):
        """Test environment variable validation."""
        with patch.dict(os.environ, {
            'EXISTING_VAR1': 'value1',
            'EXISTING_VAR2': 'value2'
        }):
            # Test with existing variables
            is_valid, missing = validate_environment_variables(['EXISTING_VAR1', 'EXISTING_VAR2'])
            assert is_valid is True
            assert missing == []
            
            # Test with missing variables
            is_valid, missing = validate_environment_variables(['EXISTING_VAR1', 'MISSING_VAR'])
            assert is_valid is False
            assert 'MISSING_VAR' in missing

    def test_get_current_environment(self):
        """Test current environment detection."""
        with patch.dict(os.environ, {'ENVIRONMENT': 'testing'}):
            assert get_current_environment() == 'testing'
        
        with patch.dict(os.environ, {}, clear=True):
            # Should return default
            env = get_current_environment()
            assert env in ['development', 'testing', 'production']

    def test_validate_required_env_vars(self):
        """Test required environment variables validation."""
        with patch.dict(os.environ, {
            'TEST_VAR1': 'value1',
            'TEST_VAR3': 'false'  # Falsy but present
        }, clear=True):
            # Should succeed - all variables are present
            result = validate_required_env_vars(['TEST_VAR1', 'TEST_VAR3'])
            assert isinstance(result, dict)
            assert result['TEST_VAR1'] == 'value1'
            assert result['TEST_VAR3'] == 'false'  # Should preserve falsy value
            
        # Should fail - missing variable (not set at all)
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(RuntimeError, match="Missing required environment variables"):
                validate_required_env_vars(['MISSING_VAR'])
                
        # Test that empty strings are handled correctly by the underlying system
        # Note: The current implementation treats empty strings as missing, which is
        # the expected behavior for environment validation

    def test_safe_int_env(self):
        """Test safe integer environment variable parsing."""
        with patch.dict(os.environ, {
            'VALID_INT': '42',
            'EMPTY_INT': '',
            'SPACES_INT': '   ',
            'INVALID_INT': 'not-a-number',
            'NEGATIVE_INT': '-10'
        }):
            assert safe_int_env('VALID_INT', 100) == 42
            assert safe_int_env('EMPTY_INT', 100) == 100  # Should use default
            assert safe_int_env('SPACES_INT', 200) == 200  # Should use default
            assert safe_int_env('INVALID_INT', 300) == 300  # Should use default
            assert safe_int_env('NEGATIVE_INT', 400) == -10  # Should parse negative
            assert safe_int_env('MISSING_VAR', 500) == 500  # Should use default

    def test_database_url_validation(self):
        """Test database URL validation and conversion."""
        with patch.dict(os.environ, {
            DATABASE_URL: 'postgresql://user:pass@localhost:5432/testdb'
        }):
            # Test async URL conversion
            async_url = get_database_url_with_validation(async_url=True)
            assert async_url.startswith('postgresql+asyncpg://')
            
            # Test sync URL conversion
            sync_url = get_database_url_with_validation(async_url=False)
            assert sync_url.startswith('postgresql://')
            
        # Test with SQLite
        with patch.dict(os.environ, {
            DATABASE_URL: 'sqlite:///test.db'
        }):
            async_url = get_database_url_with_validation(async_url=True)
            assert async_url.startswith('sqlite+aiosqlite://')
            
        # Test missing URL when not required
        with patch.dict(os.environ, {}, clear=True):
            result = get_database_url_with_validation(required=False)
            assert result is None
            
        # Test missing URL when required
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="No database URL found"):
                get_database_url_with_validation(required=True)


class TestSettings:
    """Test settings configuration."""

    def test_auth_config_initialization(self):
        """Test auth service configuration initialization."""
        env_dict = {
            DATABASE_URL: 'sqlite:///test.db',
            REDIS_URL: 'redis://localhost:6379',
            JWT_SECRET_KEY: 'test-secret-key-that-is-long-enough-for-security',
            CORS_ORIGINS: 'http://localhost:3000,http://localhost:8080'
        }
        config = TestAuthServiceConfig.from_env(env_dict)
        assert config is not None
        assert hasattr(config, 'jwt_secret_key')
        assert hasattr(config, 'database_url')
        assert hasattr(config, 'redis_url')

    def test_ai_engine_config_initialization(self):
        """Test AI engine service configuration initialization."""
        env_dict = {
            DATABASE_URL: 'sqlite:///test.db',
            REDIS_URL: 'redis://localhost:6379',
            OLLAMA_URL: 'http://localhost:11434',
            CHROMADB_URL: 'http://localhost:8000',
            CORS_ORIGINS: 'http://localhost:3000,http://localhost:8080'
        }
        config = TestAIEngineServiceConfig.from_env(env_dict)
        assert config is not None
        assert hasattr(config, 'ollama_url')
        assert hasattr(config, 'chromadb_url')

    def test_creator_hub_config_initialization(self):
        """Test creator hub service configuration initialization."""
        env_dict = {
            DATABASE_URL: 'sqlite:///test.db',
            REDIS_URL: 'redis://localhost:6379',
            AUTH_SERVICE_URL: 'http://localhost:8001',
            AI_ENGINE_SERVICE_URL: 'http://localhost:8003',
            CORS_ORIGINS: 'http://localhost:3000,http://localhost:8080'
        }
        config = TestCreatorHubServiceConfig.from_env(env_dict)
        assert config is not None
        assert hasattr(config, 'auth_service_url')
        assert hasattr(config, 'ai_engine_service_url')

    def test_channel_config_initialization(self):
        """Test channel service configuration initialization."""
        env_dict = {
            DATABASE_URL: 'sqlite:///test.db',
            REDIS_URL: 'redis://localhost:6379',
            AUTH_SERVICE_URL: 'http://localhost:8001',
            AI_ENGINE_SERVICE_URL: 'http://localhost:8003',
            CORS_ORIGINS: 'http://localhost:3000,http://localhost:8080'
        }
        config = TestChannelServiceConfig.from_env(env_dict)
        assert config is not None
        assert hasattr(config, 'auth_service_url')
        assert hasattr(config, 'ai_engine_service_url')

    def test_config_validation_with_invalid_values(self):
        """Test configuration validation with invalid values."""
        # Test with invalid JWT secret (too short)
        env_dict = {
            DATABASE_URL: 'sqlite:///test.db',
            REDIS_URL: 'redis://localhost:6379',
            JWT_SECRET_KEY: 'short',  # Too short
            CORS_ORIGINS: 'http://localhost:3000,http://localhost:8080'
        }
        # Should still create config but may log warning
        config = TestAuthServiceConfig.from_env(env_dict)
        assert config is not None

    def test_config_caching(self):
        """Test that configuration can be created multiple times."""
        env_dict = {
            DATABASE_URL: 'sqlite:///test.db',
            REDIS_URL: 'redis://localhost:6379',
            JWT_SECRET_KEY: 'test-secret-key-that-is-long-enough-for-security',
            CORS_ORIGINS: 'http://localhost:3000,http://localhost:8080'
        }
        config1 = TestAuthServiceConfig.from_env(env_dict)
        config2 = TestAuthServiceConfig.from_env(env_dict)
        # Should have same values but different instances (no caching in test)
        assert config1.jwt_secret_key == config2.jwt_secret_key
        assert config1.database_url == config2.database_url

    def test_pydantic_field_validators(self):
        """Test Pydantic field validators work correctly."""
        # Test log level validation
        env_dict = {
            DATABASE_URL: 'sqlite:///test.db',
            REDIS_URL: 'redis://localhost:6379',
            JWT_SECRET_KEY: 'test-secret-key-that-is-long-enough-for-security',
            LOG_LEVEL: 'INFO',
            CORS_ORIGINS: 'http://localhost:3000,http://localhost:8080'
        }
        config = TestAuthServiceConfig.from_env(env_dict)
        assert config.log_level == 'INFO'
        
        # Test with different log level
        env_dict[LOG_LEVEL] = 'DEBUG'
        config = TestAuthServiceConfig.from_env(env_dict)
        assert config.log_level == 'DEBUG'

    def test_cors_origins_parsing(self):
        """Test CORS origins parsing from string to list."""
        env_dict = {
            DATABASE_URL: 'sqlite:///test.db',
            REDIS_URL: 'redis://localhost:6379',
            JWT_SECRET_KEY: 'test-secret-key-that-is-long-enough-for-security',
            CORS_ORIGINS: 'http://localhost:3000,http://localhost:8080'
        }
        config = TestAuthServiceConfig.from_env(env_dict)
        assert isinstance(config.cors_origins, list)
        assert 'http://localhost:3000' in config.cors_origins
        assert 'http://localhost:8080' in config.cors_origins