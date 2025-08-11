"""
Configuration management for MVP Coaching AI Platform
Handles environment variables, secrets, and configuration validation
"""

import os
import logging
from typing import Optional, Dict, Any, List
from pydantic import BaseSettings, Field, validator
from functools import lru_cache


logger = logging.getLogger(__name__)


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
    
    @validator('cors_origins', 'allowed_hosts', pre=True)
    def parse_list_from_string(cls, v):
        if isinstance(v, str):
            return [x.strip() for x in v.split(',')]
        return v
    
    @validator('log_level')
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
    
    @validator('jwt_secret_key')
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
    
    @validator('supported_formats', pre=True)
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
    
    @validator('chroma_shard_count')
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