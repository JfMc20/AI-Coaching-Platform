"""
Configuration management for MVP Coaching AI Platform
Handles environment variables, secrets, and configuration validation

This module has been updated to use centralized environment constants from env_constants.py.
All environment variable names and defaults are now sourced from the centralized system
while maintaining backward compatibility with existing APIs.
"""

import logging
from typing import Optional, Dict, Any, List
try:
    from pydantic_settings import BaseSettings
    from pydantic import Field, field_validator
except ImportError:
    try:
        # Fallback for older pydantic versions
        from pydantic import BaseSettings, Field, validator as field_validator
    except ImportError:
        # If pydantic is not available, create dummy classes for the validation function to work
        BaseSettings = object
        Field = lambda *args, **kwargs: None
        field_validator = lambda *args, **kwargs: lambda func: func
from functools import lru_cache

# Import centralized environment constants and helper functions
from shared.config.env_constants import (
    # Environment variable constants
    DATABASE_URL, REDIS_URL, ENVIRONMENT, DEBUG, LOG_LEVEL,
    CORS_ORIGINS, ALLOWED_HOSTS, RATE_LIMIT_PER_MINUTE, RATE_LIMIT_PER_HOUR,
    JWT_SECRET_KEY, JWT_ALGORITHM, JWT_ACCESS_TOKEN_EXPIRE_MINUTES, JWT_REFRESH_TOKEN_EXPIRE_DAYS,
    AUTH_SERVICE_URL, AI_ENGINE_SERVICE_URL, MAX_UPLOAD_SIZE, UPLOADS_DIR, SUPPORTED_FORMATS,
    OLLAMA_URL, CHROMADB_URL, EMBEDDING_MODEL, CHAT_MODEL, CHROMA_SHARD_COUNT,
    CHROMA_MAX_CONNECTIONS_PER_INSTANCE, DEFAULT_CHUNK_SIZE, DEFAULT_CHUNK_OVERLAP,
    WEBSOCKET_TIMEOUT, MAX_CONNECTIONS_PER_INSTANCE, HEARTBEAT_INTERVAL,
    VAULT_URL, VAULT_TOKEN, VAULT_MOUNT_POINT, VAULT_ENABLED,
    # Helper functions
    get_env_value, get_environment_defaults, get_current_environment, validate_environment_variables,
    REQUIRED_VARS_BY_SERVICE
)

# Logger declaration for better clarity and maintainability
logger = logging.getLogger(__name__)


def safe_int_env(env_var: str, default: int, fallback: bool = True) -> int:
    """
    Safely convert environment variable to integer with fallback.
    
    Args:
        env_var: Environment variable name
        default: Default value if conversion fails
        fallback: Whether to use environment defaults
        
    Returns:
        int: Converted integer or default value
    """
    try:
        value = get_env_value(env_var, fallback=fallback)
        if value is None:
            return default
        
        # Strip whitespace and handle empty strings
        value_stripped = value.strip()
        if not value_stripped:
            return default
        
        # Check if string contains only numeric characters (with optional minus sign)
        if not (value_stripped.isdigit() or (value_stripped.startswith('-') and value_stripped[1:].isdigit())):
            logger.warning(f"Environment variable {env_var}='{value}' contains non-numeric characters. Using default: {default}")
            return default
        
        return int(value_stripped)
    except (ValueError, TypeError) as e:
        logger.warning(f"Failed to convert {env_var}='{value}' to int: {e}. Using default: {default}")
        return default


def validate_service_environment(required_vars: List[str], logger: Optional[logging.Logger] = None) -> None:
    """
    Centralized environment variable validation for services
    
    Updated to use the centralized environment constants system for validation.
    Validates that all required environment variables are set and logs any missing variables.
    Raises RuntimeError with the same message format used by all services for backward compatibility.
    
    Args:
        required_vars: List of required environment variable names. Must be a non-empty list of strings.
        logger: Optional logger instance from the calling service. If not provided,
                uses a specific logger for environment validation.
        
    Raises:
        ValueError: If required_vars is not a valid list of strings
        RuntimeError: If any required environment variables are missing
    """
    # Input validation
    if not isinstance(required_vars, list):
        raise ValueError("required_vars must be a list")
    
    if not required_vars:
        raise ValueError("required_vars cannot be empty")
    
    if not all(isinstance(var, str) and var.strip() for var in required_vars):
        raise ValueError("required_vars must contain only non-empty strings")
    
    # Use centralized validation function
    is_valid, missing_vars = validate_environment_variables(required_vars)
    if not is_valid:
        # Use service logger if provided, otherwise use a specific logger for env validation
        env_logger = logger if logger is not None else logging.getLogger('shared.config.env_validation')
        env_logger.error(f"Missing required environment variables: {missing_vars}")
        raise RuntimeError(f"Missing required environment variables: {missing_vars}")


def get_database_url_with_validation(
    async_url: bool = True, 
    fallback_config: Optional[Any] = None, 
    required: bool = True
) -> Optional[str]:
    """
    Centralized DATABASE_URL parsing, validation, and conversion
    
    Updated to use the centralized DATABASE_URL constant from env_constants.
    Consolidates all DATABASE_URL handling logic from auth-service, migrations, and alembic.
    Handles URL validation, scheme normalization, and async/sync conversion.
    
    Args:
        async_url: If True, converts to postgresql+asyncpg:// scheme. If False, uses postgresql://
        fallback_config: Optional config object to fallback to config.get_main_option("sqlalchemy.url")
        required: If True, raises ValueError when URL is not found. If False, returns None
        
    Returns:
        Validated and normalized database URL, or None if not required and not found
        
    Raises:
        ValueError: If URL is required but not found, or if URL has invalid scheme
    """
    # Try environment variable first using centralized constant
    database_url = get_env_value(DATABASE_URL, fallback=False)
    
    # Fallback to config file if provided
    if not database_url and fallback_config is not None:
        try:
            database_url = fallback_config.get_main_option("sqlalchemy.url")
        except (AttributeError, TypeError):
            # Config object doesn't have get_main_option method or is invalid
            pass
    
    # Handle missing URL based on required flag
    if not database_url:
        if required:
            raise ValueError(
                f"No database URL found. Please set the {DATABASE_URL} environment variable"
                + (" or configure sqlalchemy.url in alembic.ini" if fallback_config else "")
            )
        return None
    
    # Normalize legacy postgres:// prefix to postgresql://
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)
    
    # Validate scheme before conversion - allow SQLite for development
    allowed_schemes = ["postgresql://", "postgresql+asyncpg://", "sqlite://", "sqlite+aiosqlite://"]
    if not any(database_url.startswith(scheme) for scheme in allowed_schemes):
        raise ValueError(f"{DATABASE_URL} must use one of these schemes: {', '.join(allowed_schemes)}")
    
    # Convert between sync and async URLs based on async_url parameter
    if async_url:
        if database_url.startswith("postgresql://"):
            database_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)
        elif database_url.startswith("sqlite://"):
            database_url = database_url.replace("sqlite://", "sqlite+aiosqlite://", 1)
    else:
        if database_url.startswith("postgresql+asyncpg://"):
            database_url = database_url.replace("postgresql+asyncpg://", "postgresql://", 1)
        elif database_url.startswith("sqlite+aiosqlite://"):
            database_url = database_url.replace("sqlite+aiosqlite://", "sqlite://", 1)
    
    return database_url


class BaseConfig(BaseSettings):
    """
    Base configuration class with common settings
    
    Updated to use centralized environment constants from env_constants.py.
    All environment variable names are now sourced from the centralized system.
    """
    
    # Environment - using centralized constants and defaults
    environment: str = Field(
        default=get_env_value(ENVIRONMENT, fallback=True) or "development",
        env=ENVIRONMENT
    )
    debug: bool = Field(
        default=(get_env_value(DEBUG, fallback=True) or "false").lower() == "true",
        env=DEBUG
    )
    log_level: str = Field(
        default=get_env_value(LOG_LEVEL, fallback=True) or "INFO",
        env=LOG_LEVEL
    )
    
    # Database - using centralized constants
    database_url: str = Field(..., env=DATABASE_URL)
    
    # Redis - using centralized constants
    redis_url: str = Field(..., env=REDIS_URL)
    
    # Security - using centralized constants and defaults
    cors_origins: List[str] = Field(
        default=(get_env_value(CORS_ORIGINS, fallback=True) or "http://localhost:3000").split(","),
        env=CORS_ORIGINS
    )
    allowed_hosts: List[str] = Field(
        default=(get_env_value(ALLOWED_HOSTS, fallback=True) or "localhost,127.0.0.1").split(","),
        env=ALLOWED_HOSTS
    )
    
    # Rate limiting - using centralized constants and defaults
    rate_limit_per_minute: int = Field(
        default_factory=lambda: safe_int_env(RATE_LIMIT_PER_MINUTE, 100),
        env=RATE_LIMIT_PER_MINUTE
    )
    rate_limit_per_hour: int = Field(
        default_factory=lambda: safe_int_env(RATE_LIMIT_PER_HOUR, 1000),
        env=RATE_LIMIT_PER_HOUR
    )
    
    model_config = {
        "env_file": ".env",
        "case_sensitive": False,
    }
    
    @field_validator('cors_origins', 'allowed_hosts', mode='before')
    @classmethod
    def parse_list_from_string(cls, v):
        if isinstance(v, str):
            return [x.strip() for x in v.split(',')]
        return v
    
    @field_validator('log_level')
    @classmethod
    def validate_log_level(cls, v):
        if not isinstance(v, str):
            raise ValueError(f"Log level must be a string, got {type(v).__name__}: {v}")
        
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if v.upper() not in valid_levels:
            raise ValueError(f'log_level must be one of {valid_levels}')
        return v.upper()


class AuthServiceConfig(BaseConfig):
    """
    Configuration for Auth Service
    
    Updated to use centralized environment constants and defaults.
    """
    
    # JWT Configuration - using centralized constants and defaults
    jwt_secret_key: str = Field(..., env=JWT_SECRET_KEY)
    jwt_algorithm: str = Field(
        default=get_env_value(JWT_ALGORITHM, fallback=True) or "HS256",
        env=JWT_ALGORITHM
    )
    access_token_expire_minutes: int = Field(
        default_factory=lambda: safe_int_env(JWT_ACCESS_TOKEN_EXPIRE_MINUTES, 1440),
        env=JWT_ACCESS_TOKEN_EXPIRE_MINUTES
    )
    refresh_token_expire_days: int = Field(
        default_factory=lambda: safe_int_env(JWT_REFRESH_TOKEN_EXPIRE_DAYS, 30),
        env=JWT_REFRESH_TOKEN_EXPIRE_DAYS
    )
    
    @field_validator('jwt_secret_key')
    @classmethod
    def validate_jwt_secret(cls, v):
        if not isinstance(v, str):
            raise ValueError(f"JWT secret must be a string, got {type(v).__name__}: {v}")
        
        if len(v) < 16:
            logger.warning("JWT secret key is shorter than recommended (16+ characters)")
        if v in ['secret', 'changeme', 'your-secret-key']:
            raise ValueError('JWT secret key must be changed from default value')
        return v


class CreatorHubServiceConfig(BaseConfig):
    """
    Configuration for Creator Hub Service
    
    Updated to use centralized environment constants and defaults.
    """
    
    # Service URLs - using centralized constants
    auth_service_url: str = Field(..., env=AUTH_SERVICE_URL)
    ai_engine_service_url: str = Field(..., env=AI_ENGINE_SERVICE_URL)
    
    # File Upload Configuration - using centralized constants and defaults
    max_upload_size: int = Field(
        default_factory=lambda: safe_int_env(MAX_UPLOAD_SIZE, 52428800),  # 50MB
        env=MAX_UPLOAD_SIZE
    )
    uploads_dir: str = Field(
        default_factory=lambda: get_env_value(UPLOADS_DIR, fallback=True) or "./uploads",
        env=UPLOADS_DIR
    )
    supported_formats: List[str] = Field(
        default_factory=lambda: (get_env_value(SUPPORTED_FORMATS, fallback=True) or "pdf,txt,docx,md").split(","),
        env=SUPPORTED_FORMATS
    )
    
    @field_validator('supported_formats', mode='before')
    @classmethod
    def parse_supported_formats(cls, v):
        if isinstance(v, str):
            return [x.strip() for x in v.split(',')]
        return v


class AIEngineServiceConfig(BaseConfig):
    """
    Configuration for AI Engine Service
    
    Updated to use centralized environment constants and defaults.
    """
    
    # AI Service URLs - using centralized constants and defaults
    ollama_url: str = Field(
        default=get_env_value(OLLAMA_URL, fallback=True) or "http://localhost:11434",
        env=OLLAMA_URL
    )
    chromadb_url: str = Field(
        default=get_env_value(CHROMADB_URL, fallback=True) or "http://localhost:8000",
        env=CHROMADB_URL
    )
    
    # Model Configuration - using centralized constants and defaults
    embedding_model: str = Field(
        default=get_env_value(EMBEDDING_MODEL, fallback=True) or "nomic-embed-text",
        env=EMBEDDING_MODEL
    )
    chat_model: str = Field(
        default=get_env_value(CHAT_MODEL, fallback=True) or "llama2:7b-chat",
        env=CHAT_MODEL
    )
    
    # ChromaDB Configuration - using centralized constants and defaults
    chroma_shard_count: int = Field(
        default_factory=lambda: safe_int_env(CHROMA_SHARD_COUNT, 10),
        env=CHROMA_SHARD_COUNT
    )
    chroma_max_connections: int = Field(
        default_factory=lambda: safe_int_env(CHROMA_MAX_CONNECTIONS_PER_INSTANCE, 10),
        env=CHROMA_MAX_CONNECTIONS_PER_INSTANCE
    )
    
    # Processing Configuration - using centralized constants and defaults
    default_chunk_size: int = Field(
        default_factory=lambda: safe_int_env(DEFAULT_CHUNK_SIZE, 1000),
        env=DEFAULT_CHUNK_SIZE
    )
    default_chunk_overlap: int = Field(
        default_factory=lambda: safe_int_env(DEFAULT_CHUNK_OVERLAP, 200),
        env=DEFAULT_CHUNK_OVERLAP
    )
    
    @field_validator('chroma_shard_count')
    @classmethod
    def validate_shard_count(cls, v):
        if not 5 <= v <= 50:
            raise ValueError('chroma_shard_count must be between 5 and 50')
        return v


class ChannelServiceConfig(BaseConfig):
    """
    Configuration for Channel Service
    
    Updated to use centralized environment constants and defaults.
    """
    
    # Service URLs - using centralized constants
    auth_service_url: str = Field(..., env=AUTH_SERVICE_URL)
    ai_engine_service_url: str = Field(..., env=AI_ENGINE_SERVICE_URL)
    
    # WebSocket Configuration - using centralized constants and defaults
    websocket_timeout: int = Field(
        default_factory=lambda: safe_int_env(WEBSOCKET_TIMEOUT, 300),
        env=WEBSOCKET_TIMEOUT
    )
    max_connections_per_instance: int = Field(
        default_factory=lambda: safe_int_env(MAX_CONNECTIONS_PER_INSTANCE, 1000),
        env=MAX_CONNECTIONS_PER_INSTANCE
    )
    heartbeat_interval: int = Field(
        default_factory=lambda: safe_int_env(HEARTBEAT_INTERVAL, 30),
        env=HEARTBEAT_INTERVAL
    )


class VaultConfig(BaseSettings):
    """
    Vault configuration for secret management
    
    Updated to use centralized environment constants and defaults.
    """
    
    vault_url: str = Field(
        default=get_env_value(VAULT_URL, fallback=True) or "http://localhost:8200",
        env=VAULT_URL
    )
    vault_token: str = Field(
        default=get_env_value(VAULT_TOKEN, fallback=True) or "",
        env=VAULT_TOKEN
    )
    vault_mount_point: str = Field(
        default=get_env_value(VAULT_MOUNT_POINT, fallback=True) or "secret",
        env=VAULT_MOUNT_POINT
    )
    vault_enabled: bool = Field(
        default=(get_env_value(VAULT_ENABLED, fallback=True) or "false").lower() == "true",
        env=VAULT_ENABLED
    )
    
    model_config = {
        "env_file": ".env"
    }


def validate_required_env_vars(required_vars: List[str]) -> Dict[str, str]:
    """
    Validate that required environment variables are set.
    
    Args:
        required_vars: List of environment variable names to validate
        
    Returns:
        Dict mapping variable names to their raw values (may be None or falsey
        to accurately represent the environment state)
        
    Raises:
        RuntimeError: If any required variable is missing (None)
    """
    is_valid, missing_vars = validate_environment_variables(required_vars)
    if not is_valid:
        raise RuntimeError(f"Missing required environment variables: {missing_vars}")
    
    # Build return dictionary with actual values - return raw values without coercion
    env_vars = {}
    for var in required_vars:
        value = get_env_value(var, fallback=True)
        env_vars[var] = value  # Return raw value without coercion
    
    return env_vars





@lru_cache()
def get_auth_config() -> AuthServiceConfig:
    """Get Auth Service configuration"""
    return AuthServiceConfig()


@lru_cache()
def get_creator_hub_config() -> CreatorHubServiceConfig:
    """Get Creator Hub Service configuration"""
    return CreatorHubServiceConfig()


@lru_cache()
def get_ai_engine_config() -> AIEngineServiceConfig:
    """Get AI Engine Service configuration"""
    return AIEngineServiceConfig()


@lru_cache()
def get_channel_config() -> ChannelServiceConfig:
    """Get Channel Service configuration"""
    return ChannelServiceConfig()


@lru_cache()
def get_vault_config() -> VaultConfig:
    """Get Vault configuration"""
    return VaultConfig()