"""
Configuration management for MVP Coaching AI Platform
Handles environment variables, secrets, and configuration validation
"""

import os
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


logger = logging.getLogger(__name__)


def validate_service_environment(required_vars: List[str], logger: Optional[logging.Logger] = None) -> None:
    """
    Centralized environment variable validation for services
    
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
    
    # Check for missing environment variables
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
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
    # Try environment variable first
    database_url = os.getenv("DATABASE_URL")
    
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
                "No database URL found. Please set the DATABASE_URL environment variable"
                + (" or configure sqlalchemy.url in alembic.ini" if fallback_config else "")
            )
        return None
    
    # Normalize legacy postgres:// prefix to postgresql://
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)
    
    # Validate scheme before conversion
    if not (database_url.startswith("postgresql://") or database_url.startswith("postgresql+asyncpg://")):
        raise ValueError("DATABASE_URL must use postgresql:// or postgresql+asyncpg:// scheme")
    
    # Convert between sync and async URLs based on async_url parameter
    if async_url and database_url.startswith("postgresql://"):
        database_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    elif not async_url and database_url.startswith("postgresql+asyncpg://"):
        database_url = database_url.replace("postgresql+asyncpg://", "postgresql://", 1)
    
    return database_url


class BaseConfig(BaseSettings):
    """Base configuration class with common settings"""
    
    # Environment
    environment: str = Field(default="development", env="ENVIRONMENT")
    debug: bool = Field(default=False, env="DEBUG")
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    
    # Database
    database_url: str = Field(..., env="DATABASE_URL")
    
    # Redis
    redis_url: str = Field(..., env="REDIS_URL")
    
    # Security
    cors_origins: List[str] = Field(default=["http://localhost:3000"], env="CORS_ORIGINS")
    allowed_hosts: List[str] = Field(default=["localhost", "127.0.0.1"], env="ALLOWED_HOSTS")
    
    # Rate limiting
    rate_limit_per_minute: int = Field(default=100, env="RATE_LIMIT_PER_MINUTE")
    rate_limit_per_hour: int = Field(default=1000, env="RATE_LIMIT_PER_HOUR")
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        
        @classmethod
        def parse_env_var(cls, field_name: str, raw_val: str) -> Any:
            if field_name in ['cors_origins', 'allowed_hosts']:
                return [x.strip() for x in raw_val.split(',')]
            return cls.json_loads(raw_val)
    
    @field_validator('cors_origins', 'allowed_hosts', mode='before')
    @classmethod
    def parse_list_from_string(cls, v):
        if isinstance(v, str):
            return [x.strip() for x in v.split(',')]
        return v
    
    @field_validator('log_level')
    @classmethod
    def validate_log_level(cls, v):
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if v.upper() not in valid_levels:
            raise ValueError(f'log_level must be one of {valid_levels}')
        return v.upper()


class AuthServiceConfig(BaseConfig):
    """Configuration for Auth Service"""
    
    # JWT Configuration
    jwt_secret_key: str = Field(..., env="JWT_SECRET_KEY")
    jwt_algorithm: str = Field(default="HS256", env="JWT_ALGORITHM")
    access_token_expire_minutes: int = Field(default=1440, env="ACCESS_TOKEN_EXPIRE_MINUTES")
    refresh_token_expire_days: int = Field(default=30, env="REFRESH_TOKEN_EXPIRE_DAYS")
    
    @field_validator('jwt_secret_key')
    @classmethod
    def validate_jwt_secret(cls, v):
        if len(v) < 16:
            logger.warning("JWT secret key is shorter than recommended (16+ characters)")
        if v in ['secret', 'changeme', 'your-secret-key']:
            raise ValueError('JWT secret key must be changed from default value')
        return v


class CreatorHubServiceConfig(BaseConfig):
    """Configuration for Creator Hub Service"""
    
    # Service URLs
    auth_service_url: str = Field(..., env="AUTH_SERVICE_URL")
    ai_engine_service_url: str = Field(..., env="AI_ENGINE_SERVICE_URL")
    
    # File Upload Configuration
    max_upload_size: int = Field(default=52428800, env="MAX_UPLOAD_SIZE")  # 50MB
    uploads_dir: str = Field(default="./uploads", env="UPLOADS_DIR")
    supported_formats: List[str] = Field(default=[".pdf", ".txt", ".docx", ".md"], env="SUPPORTED_FORMATS")
    
    @field_validator('supported_formats', mode='before')
    @classmethod
    def parse_supported_formats(cls, v):
        if isinstance(v, str):
            return [x.strip() for x in v.split(',')]
        return v


class AIEngineServiceConfig(BaseConfig):
    """Configuration for AI Engine Service"""
    
    # AI Service URLs
    ollama_url: str = Field(..., env="OLLAMA_URL")
    chromadb_url: str = Field(..., env="CHROMADB_URL")
    
    # Model Configuration
    embedding_model: str = Field(default="nomic-embed-text", env="EMBEDDING_MODEL")
    chat_model: str = Field(default="llama2:7b-chat", env="CHAT_MODEL")
    
    # ChromaDB Configuration
    chroma_shard_count: int = Field(default=10, env="CHROMA_SHARD_COUNT")
    chroma_max_connections: int = Field(default=10, env="CHROMA_MAX_CONNECTIONS_PER_INSTANCE")
    
    # Processing Configuration
    default_chunk_size: int = Field(default=1000, env="DEFAULT_CHUNK_SIZE")
    default_chunk_overlap: int = Field(default=200, env="DEFAULT_CHUNK_OVERLAP")
    
    @field_validator('chroma_shard_count')
    @classmethod
    def validate_shard_count(cls, v):
        if not 5 <= v <= 50:
            raise ValueError('chroma_shard_count must be between 5 and 50')
        return v


class ChannelServiceConfig(BaseConfig):
    """Configuration for Channel Service"""
    
    # Service URLs
    auth_service_url: str = Field(..., env="AUTH_SERVICE_URL")
    ai_engine_service_url: str = Field(..., env="AI_ENGINE_SERVICE_URL")
    
    # WebSocket Configuration
    websocket_timeout: int = Field(default=300, env="WEBSOCKET_TIMEOUT")
    max_connections_per_instance: int = Field(default=1000, env="MAX_CONNECTIONS_PER_INSTANCE")
    heartbeat_interval: int = Field(default=30, env="HEARTBEAT_INTERVAL")


class VaultConfig(BaseSettings):
    """Vault configuration for secret management"""
    
    vault_url: str = Field(default="http://localhost:8200", env="VAULT_URL")
    vault_token: str = Field(default="", env="VAULT_TOKEN")
    vault_mount_point: str = Field(default="secret", env="VAULT_MOUNT_POINT")
    vault_enabled: bool = Field(default=False, env="VAULT_ENABLED")
    
    class Config:
        env_file = ".env"


def validate_required_env_vars(required_vars: List[str]) -> Dict[str, str]:
    """Validate that required environment variables are set"""
    missing_vars = []
    env_vars = {}
    
    for var in required_vars:
        value = os.getenv(var)
        if not value:
            missing_vars.append(var)
        else:
            env_vars[var] = value
    
    if missing_vars:
        raise RuntimeError(f"Missing required environment variables: {missing_vars}")
    
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