"""
Centralized environment variable constants and configuration management.

This module provides a single source of truth for all environment variable names,
their default values per environment, and helper functions for retrieval and validation.
"""

import os
from typing import Any, Dict, List, Optional, Tuple


# ============================================================================
# ENVIRONMENT VARIABLE CONSTANTS
# ============================================================================

# Database Configuration
DATABASE_URL = "DATABASE_URL"
POSTGRES_DB = "POSTGRES_DB"
POSTGRES_USER = "POSTGRES_USER"
POSTGRES_PASSWORD = "POSTGRES_PASSWORD"
POSTGRES_MAX_CONNECTIONS = "POSTGRES_MAX_CONNECTIONS"
POSTGRES_SHARED_BUFFERS = "POSTGRES_SHARED_BUFFERS"
POSTGRES_EFFECTIVE_CACHE_SIZE = "POSTGRES_EFFECTIVE_CACHE_SIZE"
POSTGRES_WORK_MEM = "POSTGRES_WORK_MEM"
POSTGRES_MAINTENANCE_WORK_MEM = "POSTGRES_MAINTENANCE_WORK_MEM"
POSTGRES_CHECKPOINT_COMPLETION_TARGET = "POSTGRES_CHECKPOINT_COMPLETION_TARGET"
POSTGRES_WAL_BUFFERS = "POSTGRES_WAL_BUFFERS"
POSTGRES_DEFAULT_STATISTICS_TARGET = "POSTGRES_DEFAULT_STATISTICS_TARGET"
POSTGRES_SHARED_PRELOAD_LIBRARIES = "POSTGRES_SHARED_PRELOAD_LIBRARIES"

# Redis Configuration
REDIS_URL = "REDIS_URL"

# JWT/Authentication Configuration
JWT_SECRET_KEY = "JWT_SECRET_KEY"
JWT_ALGORITHM = "JWT_ALGORITHM"
JWT_ACCESS_TOKEN_EXPIRE_MINUTES = "JWT_ACCESS_TOKEN_EXPIRE_MINUTES"
JWT_REFRESH_TOKEN_EXPIRE_DAYS = "JWT_REFRESH_TOKEN_EXPIRE_DAYS"
JWT_AUDIENCE = "JWT_AUDIENCE"
JWT_ISSUER = "JWT_ISSUER"
JWT_KEYS_DIR = "JWT_KEYS_DIR"
JWT_KEY_ROTATION_DAYS = "JWT_KEY_ROTATION_DAYS"

# AI Service Configuration
OLLAMA_URL = "OLLAMA_URL"
OLLAMA_HOST = "OLLAMA_HOST"
CHROMADB_URL = "CHROMADB_URL"
CHROMA_SERVER_HOST = "CHROMA_SERVER_HOST"
CHROMA_SERVER_HTTP_PORT = "CHROMA_SERVER_HTTP_PORT"
EMBEDDING_MODEL = "EMBEDDING_MODEL"
CHAT_MODEL = "CHAT_MODEL"
CHROMA_SHARD_COUNT = "CHROMA_SHARD_COUNT"
CHROMA_MAX_CONNECTIONS_PER_INSTANCE = "CHROMA_MAX_CONNECTIONS_PER_INSTANCE"
DEFAULT_CHUNK_SIZE = "DEFAULT_CHUNK_SIZE"
DEFAULT_CHUNK_OVERLAP = "DEFAULT_CHUNK_OVERLAP"

# Service URL Configuration
AUTH_SERVICE_URL = "AUTH_SERVICE_URL"
AI_ENGINE_SERVICE_URL = "AI_ENGINE_SERVICE_URL"
CREATOR_HUB_SERVICE_URL = "CREATOR_HUB_SERVICE_URL"
CHANNEL_SERVICE_URL = "CHANNEL_SERVICE_URL"

# Security Configuration
CORS_ORIGINS = "CORS_ORIGINS"
ALLOWED_HOSTS = "ALLOWED_HOSTS"
MAX_FAILED_LOGIN_ATTEMPTS = "MAX_FAILED_LOGIN_ATTEMPTS"
ACCOUNT_LOCKOUT_DURATION_MINUTES = "ACCOUNT_LOCKOUT_DURATION_MINUTES"
PASSWORD_RESET_TOKEN_EXPIRE_MINUTES = "PASSWORD_RESET_TOKEN_EXPIRE_MINUTES"

# File Upload Configuration
MAX_UPLOAD_SIZE = "MAX_UPLOAD_SIZE"
UPLOADS_DIR = "UPLOADS_DIR"
SUPPORTED_FORMATS = "SUPPORTED_FORMATS"

# Environment Configuration
ENVIRONMENT = "ENVIRONMENT"
DEBUG = "DEBUG"
LOG_LEVEL = "LOG_LEVEL"
SQL_ECHO = "SQL_ECHO"
SLOW_QUERY_THRESHOLD = "SLOW_QUERY_THRESHOLD"

# Rate Limiting Configuration
RATE_LIMIT_PER_MINUTE = "RATE_LIMIT_PER_MINUTE"
RATE_LIMIT_PER_HOUR = "RATE_LIMIT_PER_HOUR"

# WebSocket Configuration
WEBSOCKET_TIMEOUT = "WEBSOCKET_TIMEOUT"
MAX_CONNECTIONS_PER_INSTANCE = "MAX_CONNECTIONS_PER_INSTANCE"
HEARTBEAT_INTERVAL = "HEARTBEAT_INTERVAL"

# Email Configuration
FRONTEND_URL = "FRONTEND_URL"
EMAIL_SERVICE_ENABLED = "EMAIL_SERVICE_ENABLED"
FROM_EMAIL = "FROM_EMAIL"
SMTP_HOST = "SMTP_HOST"
SMTP_PORT = "SMTP_PORT"
SMTP_USER = "SMTP_USER"
SMTP_PASSWORD = "SMTP_PASSWORD"
SMTP_USE_TLS = "SMTP_USE_TLS"
FROM_NAME = "FROM_NAME"

# Security/Password Configuration
ARGON2_MEMORY_COST = "ARGON2_MEMORY_COST"
ARGON2_TIME_COST = "ARGON2_TIME_COST"
ARGON2_PARALLELISM = "ARGON2_PARALLELISM"

# GDPR/Compliance Configuration
GDPR_ANONYMIZATION_RETENTION_DAYS = "GDPR_ANONYMIZATION_RETENTION_DAYS"
GDPR_AUDIT_RETENTION_YEARS = "GDPR_AUDIT_RETENTION_YEARS"

# Vault Configuration
VAULT_URL = "VAULT_URL"
VAULT_TOKEN = "VAULT_TOKEN"
VAULT_MOUNT_POINT = "VAULT_MOUNT_POINT"
VAULT_ENABLED = "VAULT_ENABLED"

# Monitoring Configuration
MONITORING_SAMPLING_RATE = "MONITORING_SAMPLING_RATE"
MONITORING_RETENTION_DAYS = "MONITORING_RETENTION_DAYS"
ENABLE_PII_DETECTION = "ENABLE_PII_DETECTION"
HEALTH_CHECK_INTERVAL_MINUTES = "HEALTH_CHECK_INTERVAL_MINUTES"

# Health Check Configuration
PORT = "PORT"
HEALTH_CHECK_HOST = "HEALTH_CHECK_HOST"
HEALTH_CHECK_PATH = "HEALTH_CHECK_PATH"

# Infrastructure Configuration
NGINX_WORKER_PROCESSES = "NGINX_WORKER_PROCESSES"
NGINX_WORKER_CONNECTIONS = "NGINX_WORKER_CONNECTIONS"
VAULT_DEV_LISTEN_ADDRESS = "VAULT_DEV_LISTEN_ADDRESS"

# Testing Configuration
TEST_REDIS_URL = "TEST_REDIS_URL"
TEST_DATABASE_URL = "TEST_DATABASE_URL"
DB_AUTO_CREATE = "DB_AUTO_CREATE"


# ============================================================================
# ENVIRONMENT-SPECIFIC DEFAULTS
# ============================================================================

ENVIRONMENT_DEFAULTS: Dict[str, Dict[str, Any]] = {
    "development": {
        # Database
        DATABASE_URL: "postgresql://postgres:postgres@localhost:5432/ai_platform_dev",
        POSTGRES_DB: "ai_platform_dev",
        POSTGRES_USER: "postgres",
        POSTGRES_PASSWORD: "postgres",
        
        # Redis
        REDIS_URL: "redis://localhost:6379/0",
        
        # JWT/Auth
        JWT_SECRET_KEY: "dev-7f8a9b2c4d6e1f3a5b7c9d2e4f6a8b0c3d5e7f9a1b3c5d7e9f1a3b5c7d9e1f3a5b7c9d2e4f6a8b0c",
        JWT_ALGORITHM: "HS256",
        JWT_ACCESS_TOKEN_EXPIRE_MINUTES: "30",
        JWT_REFRESH_TOKEN_EXPIRE_DAYS: "7",
        JWT_AUDIENCE: "ai-platform-dev",
        JWT_ISSUER: "ai-platform-auth-dev",
        JWT_KEYS_DIR: "/tmp/jwt_keys",
        JWT_KEY_ROTATION_DAYS: "30",
        
        # AI Services
        OLLAMA_URL: "http://localhost:11434",
        OLLAMA_HOST: "0.0.0.0",
        CHROMADB_URL: "http://localhost:8000",
        CHROMA_SERVER_HOST: "0.0.0.0",
        CHROMA_SERVER_HTTP_PORT: "8000",
        EMBEDDING_MODEL: "nomic-embed-text",
        CHAT_MODEL: "llama3.2:1b",
        CHROMA_SHARD_COUNT: "5",
        CHROMA_MAX_CONNECTIONS_PER_INSTANCE: "10",
        DEFAULT_CHUNK_SIZE: "1000",
        DEFAULT_CHUNK_OVERLAP: "200",
        
        # Service URLs
        AUTH_SERVICE_URL: "http://localhost:8001",
        AI_ENGINE_SERVICE_URL: "http://localhost:8003",
        CREATOR_HUB_SERVICE_URL: "http://localhost:8002",
        CHANNEL_SERVICE_URL: "http://localhost:8004",
        
        # Security
        CORS_ORIGINS: "http://localhost:3000,http://localhost:8080",
        ALLOWED_HOSTS: "localhost,127.0.0.1",
        MAX_FAILED_LOGIN_ATTEMPTS: "5",
        ACCOUNT_LOCKOUT_DURATION_MINUTES: "30",
        PASSWORD_RESET_TOKEN_EXPIRE_MINUTES: "60",
        
        # File Upload
        MAX_UPLOAD_SIZE: "10485760",  # 10MB
        UPLOADS_DIR: "./uploads",
        SUPPORTED_FORMATS: "pdf,txt,docx,md",
        
        # Environment
        ENVIRONMENT: "development",
        DEBUG: "true",
        LOG_LEVEL: "DEBUG",
        SQL_ECHO: "true",
        SLOW_QUERY_THRESHOLD: "1.0",
        
        # Rate Limiting
        RATE_LIMIT_PER_MINUTE: "60",
        RATE_LIMIT_PER_HOUR: "1000",
        
        # WebSocket
        WEBSOCKET_TIMEOUT: "60",
        MAX_CONNECTIONS_PER_INSTANCE: "100",
        HEARTBEAT_INTERVAL: "30",
        
        # Email
        FRONTEND_URL: "http://localhost:3000",
        EMAIL_SERVICE_ENABLED: "false",
        FROM_EMAIL: "noreply@example.com",
        SMTP_HOST: "localhost",
        SMTP_PORT: "1025",
        SMTP_USER: "",
        SMTP_PASSWORD: "",
        SMTP_USE_TLS: "false",
        FROM_NAME: "AI Platform Dev",
        
        # Security/Password
        ARGON2_MEMORY_COST: "65536",
        ARGON2_TIME_COST: "3",
        ARGON2_PARALLELISM: "4",
        
        # GDPR
        GDPR_ANONYMIZATION_RETENTION_DAYS: "30",
        GDPR_AUDIT_RETENTION_YEARS: "1",
        
        # Vault
        VAULT_URL: "http://localhost:8200",
        VAULT_TOKEN: "",
        VAULT_MOUNT_POINT: "secret",
        VAULT_ENABLED: "false",
        
        # Health Check
        PORT: "8000",
        HEALTH_CHECK_HOST: "localhost",
        HEALTH_CHECK_PATH: "/health",
        
        # Testing
        TEST_REDIS_URL: "redis://localhost:6379/1",
        TEST_DATABASE_URL: "postgresql://postgres:postgres@localhost:5432/ai_platform_test",
        DB_AUTO_CREATE: "true",
        
        # Monitoring
        MONITORING_SAMPLING_RATE: "0.01",
        MONITORING_RETENTION_DAYS: "30",
        ENABLE_PII_DETECTION: "true",
        HEALTH_CHECK_INTERVAL_MINUTES: "5",
        
        # Infrastructure
        NGINX_WORKER_PROCESSES: "auto",
        NGINX_WORKER_CONNECTIONS: "1024",
        VAULT_DEV_LISTEN_ADDRESS: "0.0.0.0:8200",
    },
    "testing": {
        # Database
        DATABASE_URL: "postgresql://postgres:postgres@postgres:5432/ai_platform_test",
        POSTGRES_DB: "ai_platform_test",
        POSTGRES_USER: "postgres",
        POSTGRES_PASSWORD: "postgres",
        
        # Redis
        REDIS_URL: "redis://redis:6379/1",
        
        # JWT/Auth
        JWT_SECRET_KEY: "test-9a8b7c6d5e4f3a2b1c0d9e8f7a6b5c4d3e2f1a0b9c8d7e6f5a4b3c2d1e0f9a8b7c6d5e4f3a2b1c",
        JWT_ALGORITHM: "HS256",
        JWT_ACCESS_TOKEN_EXPIRE_MINUTES: "5",
        JWT_REFRESH_TOKEN_EXPIRE_DAYS: "1",
        JWT_AUDIENCE: "ai-platform-test",
        JWT_ISSUER: "ai-platform-auth-test",
        JWT_KEYS_DIR: "/tmp/test_jwt_keys",
        JWT_KEY_ROTATION_DAYS: "1",
        
        # AI Services
        OLLAMA_URL: "http://ollama:11434",
        OLLAMA_HOST: "0.0.0.0",
        CHROMADB_URL: "http://chromadb:8000",
        CHROMA_SERVER_HOST: "0.0.0.0",
        CHROMA_SERVER_HTTP_PORT: "8000",
        EMBEDDING_MODEL: "nomic-embed-text",
        CHAT_MODEL: "llama3.2",
        CHROMA_SHARD_COUNT: "5",
        CHROMA_MAX_CONNECTIONS_PER_INSTANCE: "5",
        DEFAULT_CHUNK_SIZE: "500",
        DEFAULT_CHUNK_OVERLAP: "100",
        
        # Service URLs
        AUTH_SERVICE_URL: "http://auth-service:8001",
        AI_ENGINE_SERVICE_URL: "http://ai-engine-service:8003",
        CREATOR_HUB_SERVICE_URL: "http://creator-hub-service:8002",
        CHANNEL_SERVICE_URL: "http://channel-service:8004",
        
        # Security
        CORS_ORIGINS: "http://localhost:3000",
        ALLOWED_HOSTS: "localhost,127.0.0.1,auth-service,ai-engine-service",
        MAX_FAILED_LOGIN_ATTEMPTS: "3",
        ACCOUNT_LOCKOUT_DURATION_MINUTES: "5",
        PASSWORD_RESET_TOKEN_EXPIRE_MINUTES: "30",
        
        # File Upload
        MAX_UPLOAD_SIZE: "5242880",  # 5MB
        UPLOADS_DIR: "/tmp/test_uploads",
        SUPPORTED_FORMATS: "pdf,txt",
        
        # Environment
        ENVIRONMENT: "testing",
        DEBUG: "false",
        LOG_LEVEL: "INFO",
        SQL_ECHO: "false",
        SLOW_QUERY_THRESHOLD: "0.5",
        
        # Rate Limiting
        RATE_LIMIT_PER_MINUTE: "30",
        RATE_LIMIT_PER_HOUR: "500",
        
        # WebSocket
        WEBSOCKET_TIMEOUT: "30",
        MAX_CONNECTIONS_PER_INSTANCE: "50",
        HEARTBEAT_INTERVAL: "15",
        
        # Email
        FRONTEND_URL: "http://localhost:3000",
        EMAIL_SERVICE_ENABLED: "false",
        FROM_EMAIL: "test@example.com",
        SMTP_HOST: "localhost",
        SMTP_PORT: "1025",
        SMTP_USER: "",
        SMTP_PASSWORD: "",
        SMTP_USE_TLS: "false",
        FROM_NAME: "AI Platform Test",
        
        # Security/Password
        ARGON2_MEMORY_COST: "32768",
        ARGON2_TIME_COST: "2",
        ARGON2_PARALLELISM: "2",
        
        # GDPR
        GDPR_ANONYMIZATION_RETENTION_DAYS: "7",
        GDPR_AUDIT_RETENTION_YEARS: "1",
        
        # Vault
        VAULT_URL: "",
        VAULT_TOKEN: "",
        VAULT_MOUNT_POINT: "secret",
        VAULT_ENABLED: "false",
        
        # Health Check
        PORT: "8000",
        HEALTH_CHECK_HOST: "localhost",
        HEALTH_CHECK_PATH: "/health",
        
        # Testing
        TEST_REDIS_URL: "redis://redis:6379/2",
        TEST_DATABASE_URL: "postgresql://postgres:postgres@postgres:5432/ai_platform_test",
        DB_AUTO_CREATE: "true",
        
        # Monitoring
        MONITORING_SAMPLING_RATE: "0.1",
        MONITORING_RETENTION_DAYS: "7",
        ENABLE_PII_DETECTION: "false",
        HEALTH_CHECK_INTERVAL_MINUTES: "2",
        
        # Infrastructure
        NGINX_WORKER_PROCESSES: "auto",
        NGINX_WORKER_CONNECTIONS: "1024",
        VAULT_DEV_LISTEN_ADDRESS: "0.0.0.0:8200",
    },
    "production": {
        # Database
        DATABASE_URL: "",  # Must be set via environment
        POSTGRES_DB: "",  # Must be set via environment
        POSTGRES_USER: "",  # Must be set via environment
        POSTGRES_PASSWORD: "",  # Must be set via environment
        POSTGRES_MAX_CONNECTIONS: "200",
        POSTGRES_SHARED_BUFFERS: "512MB",
        POSTGRES_EFFECTIVE_CACHE_SIZE: "2GB",
        POSTGRES_WORK_MEM: "8MB",
        POSTGRES_MAINTENANCE_WORK_MEM: "128MB",
        POSTGRES_CHECKPOINT_COMPLETION_TARGET: "0.9",
        POSTGRES_WAL_BUFFERS: "16MB",
        POSTGRES_DEFAULT_STATISTICS_TARGET: "100",
        POSTGRES_SHARED_PRELOAD_LIBRARIES: "pg_stat_statements",
        
        # Redis
        REDIS_URL: "",  # Must be set via environment
        
        # JWT/Auth
        JWT_SECRET_KEY: "",  # Must be set via environment
        JWT_ALGORITHM: "RS256",
        JWT_ACCESS_TOKEN_EXPIRE_MINUTES: "15",
        JWT_REFRESH_TOKEN_EXPIRE_DAYS: "30",
        JWT_AUDIENCE: "ai-platform-prod",
        JWT_ISSUER: "ai-platform-auth-prod",
        JWT_KEYS_DIR: "/var/lib/jwt_keys",
        JWT_KEY_ROTATION_DAYS: "90",
        
        # AI Services
        OLLAMA_URL: "",  # Must be set via environment
        OLLAMA_HOST: "0.0.0.0",
        CHROMADB_URL: "",  # Must be set via environment
        CHROMA_SERVER_HOST: "0.0.0.0",
        CHROMA_SERVER_HTTP_PORT: "8000",
        EMBEDDING_MODEL: "nomic-embed-text",
        CHAT_MODEL: "llama3.2",
        CHROMA_SHARD_COUNT: "5",
        CHROMA_MAX_CONNECTIONS_PER_INSTANCE: "20",
        DEFAULT_CHUNK_SIZE: "1000",
        DEFAULT_CHUNK_OVERLAP: "200",
        
        # Service URLs
        AUTH_SERVICE_URL: "",  # Must be set via environment
        AI_ENGINE_SERVICE_URL: "",  # Must be set via environment
        CREATOR_HUB_SERVICE_URL: "",  # Must be set via environment
        CHANNEL_SERVICE_URL: "",  # Must be set via environment
        
        # Security
        CORS_ORIGINS: "",  # Must be set via environment
        ALLOWED_HOSTS: "",  # Must be set via environment
        MAX_FAILED_LOGIN_ATTEMPTS: "3",
        ACCOUNT_LOCKOUT_DURATION_MINUTES: "60",
        PASSWORD_RESET_TOKEN_EXPIRE_MINUTES: "30",
        
        # File Upload
        MAX_UPLOAD_SIZE: "52428800",  # 50MB
        UPLOADS_DIR: "/var/lib/uploads",
        SUPPORTED_FORMATS: "pdf,txt,docx,md,csv,json",
        
        # Environment
        ENVIRONMENT: "production",
        DEBUG: "false",
        LOG_LEVEL: "WARNING",
        SQL_ECHO: "false",
        SLOW_QUERY_THRESHOLD: "2.0",
        
        # Rate Limiting
        RATE_LIMIT_PER_MINUTE: "100",
        RATE_LIMIT_PER_HOUR: "5000",
        
        # WebSocket
        WEBSOCKET_TIMEOUT: "120",
        MAX_CONNECTIONS_PER_INSTANCE: "1000",
        HEARTBEAT_INTERVAL: "60",
        
        # Email
        FRONTEND_URL: "",  # Must be set via environment
        EMAIL_SERVICE_ENABLED: "true",
        FROM_EMAIL: "",  # Must be set via environment
        SMTP_HOST: "",  # Must be set via environment
        SMTP_PORT: "587",
        SMTP_USER: "",  # Must be set via environment
        SMTP_PASSWORD: "",  # Must be set via environment
        SMTP_USE_TLS: "true",
        FROM_NAME: "AI Platform",
        
        # Security/Password
        ARGON2_MEMORY_COST: "131072",
        ARGON2_TIME_COST: "4",
        ARGON2_PARALLELISM: "8",
        
        # GDPR
        GDPR_ANONYMIZATION_RETENTION_DAYS: "90",
        GDPR_AUDIT_RETENTION_YEARS: "7",
        
        # Vault
        VAULT_URL: "",  # Must be set via environment
        VAULT_TOKEN: "",  # Must be set via environment
        VAULT_MOUNT_POINT: "secret",
        VAULT_ENABLED: "true",
        
        # Health Check
        PORT: "8000",
        HEALTH_CHECK_HOST: "0.0.0.0",
        HEALTH_CHECK_PATH: "/health",
        
        # Testing
        TEST_REDIS_URL: "",
        TEST_DATABASE_URL: "",
        DB_AUTO_CREATE: "false",
        
        # Monitoring
        MONITORING_SAMPLING_RATE: "0.01",
        MONITORING_RETENTION_DAYS: "90",
        ENABLE_PII_DETECTION: "true",
        HEALTH_CHECK_INTERVAL_MINUTES: "10",
        
        # Infrastructure
        NGINX_WORKER_PROCESSES: "auto",
        NGINX_WORKER_CONNECTIONS: "4096",
        VAULT_DEV_LISTEN_ADDRESS: "",
    }
}


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_current_environment() -> str:
    """
    Detect the current environment from the ENVIRONMENT variable.
    
    Returns:
        str: The current environment ('development', 'testing', or 'production')
    """
    env = os.getenv(ENVIRONMENT, "development").lower()
    if env not in ENVIRONMENT_DEFAULTS:
        return "development"
    return env


def get_environment_defaults(environment: Optional[str] = None) -> Dict[str, Any]:
    """
    Get all default values for a specific environment.
    
    Args:
        environment: The environment to get defaults for. If None, uses current environment.
    
    Returns:
        Dict[str, Any]: Dictionary of all default values for the environment
    """
    if environment is None:
        environment = get_current_environment()
    
    if environment not in ENVIRONMENT_DEFAULTS:
        raise ValueError(f"Unknown environment: {environment}")
    
    return ENVIRONMENT_DEFAULTS[environment].copy()


def get_env_value(
    var_name: str,
    environment: Optional[str] = None,
    fallback: bool = True,
    default: Optional[Any] = None
) -> Optional[str]:
    """
    Get an environment variable value with fallback to environment-specific defaults.
    
    Args:
        var_name: The name of the environment variable
        environment: The environment to use for defaults. If None, uses current environment.
        fallback: Whether to fall back to environment defaults if not set
        default: Optional default value to use if variable is not set and no fallback exists
    
    Returns:
        Optional[str]: The environment variable value or default
    """
    # First, try to get from actual environment
    value = os.getenv(var_name)
    if value is not None:
        return value
    
    # If fallback is enabled, try to get from environment defaults
    if fallback:
        if environment is None:
            environment = get_current_environment()
        
        if environment in ENVIRONMENT_DEFAULTS:
            env_defaults = ENVIRONMENT_DEFAULTS[environment]
            if var_name in env_defaults:
                return env_defaults[var_name]
    
    # Return the provided default or None
    return default


def validate_environment_variables(
    required_vars: List[str],
    environment: Optional[str] = None
) -> Tuple[bool, List[str]]:
    """
    Validate that required environment variables are set.
    
    Args:
        required_vars: List of required environment variable names
        environment: The environment to validate against. If None, uses current environment.
    
    Returns:
        Tuple[bool, List[str]]: (all_valid, list_of_missing_vars)
    """
    if environment is None:
        environment = get_current_environment()
    
    missing_vars = []
    for var_name in required_vars:
        value = get_env_value(var_name, environment=environment, fallback=True)
        if not value:
            missing_vars.append(var_name)
    
    return len(missing_vars) == 0, missing_vars


# ============================================================================
# UTILITY COLLECTIONS
# ============================================================================

# All environment variable names as a tuple
ALL_ENV_VARS: Tuple[str, ...] = (
    # Database
    DATABASE_URL, POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD,
    POSTGRES_MAX_CONNECTIONS, POSTGRES_SHARED_BUFFERS, POSTGRES_EFFECTIVE_CACHE_SIZE,
    POSTGRES_WORK_MEM, POSTGRES_MAINTENANCE_WORK_MEM, POSTGRES_CHECKPOINT_COMPLETION_TARGET,
    POSTGRES_WAL_BUFFERS, POSTGRES_DEFAULT_STATISTICS_TARGET, POSTGRES_SHARED_PRELOAD_LIBRARIES,
    # Redis
    REDIS_URL,
    # JWT/Auth
    JWT_SECRET_KEY, JWT_ALGORITHM, JWT_ACCESS_TOKEN_EXPIRE_MINUTES,
    JWT_REFRESH_TOKEN_EXPIRE_DAYS, JWT_AUDIENCE, JWT_ISSUER,
    JWT_KEYS_DIR, JWT_KEY_ROTATION_DAYS,
    # AI Services
    OLLAMA_URL, OLLAMA_HOST, CHROMADB_URL, CHROMA_SERVER_HOST, CHROMA_SERVER_HTTP_PORT,
    EMBEDDING_MODEL, CHAT_MODEL, CHROMA_SHARD_COUNT, CHROMA_MAX_CONNECTIONS_PER_INSTANCE,
    DEFAULT_CHUNK_SIZE, DEFAULT_CHUNK_OVERLAP,
    # Service URLs
    AUTH_SERVICE_URL, AI_ENGINE_SERVICE_URL, CREATOR_HUB_SERVICE_URL, CHANNEL_SERVICE_URL,
    # Security
    CORS_ORIGINS, ALLOWED_HOSTS, MAX_FAILED_LOGIN_ATTEMPTS,
    ACCOUNT_LOCKOUT_DURATION_MINUTES, PASSWORD_RESET_TOKEN_EXPIRE_MINUTES,
    # File Upload
    MAX_UPLOAD_SIZE, UPLOADS_DIR, SUPPORTED_FORMATS,
    # Environment
    ENVIRONMENT, DEBUG, LOG_LEVEL, SQL_ECHO, SLOW_QUERY_THRESHOLD,
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE, RATE_LIMIT_PER_HOUR,
    # WebSocket
    WEBSOCKET_TIMEOUT, MAX_CONNECTIONS_PER_INSTANCE, HEARTBEAT_INTERVAL,
    # Email
    FRONTEND_URL, EMAIL_SERVICE_ENABLED, FROM_EMAIL, SMTP_HOST,
    SMTP_PORT, SMTP_USER, SMTP_PASSWORD, SMTP_USE_TLS, FROM_NAME,
    # Security/Password
    ARGON2_MEMORY_COST, ARGON2_TIME_COST, ARGON2_PARALLELISM,
    # GDPR
    GDPR_ANONYMIZATION_RETENTION_DAYS, GDPR_AUDIT_RETENTION_YEARS,
    # Health Check
    PORT, HEALTH_CHECK_HOST, HEALTH_CHECK_PATH,
    # Vault
    VAULT_URL, VAULT_TOKEN, VAULT_MOUNT_POINT, VAULT_ENABLED,
    # Monitoring
    MONITORING_SAMPLING_RATE, MONITORING_RETENTION_DAYS, ENABLE_PII_DETECTION, HEALTH_CHECK_INTERVAL_MINUTES,
    # Testing
    TEST_REDIS_URL, TEST_DATABASE_URL, DB_AUTO_CREATE,
    # Infrastructure
    NGINX_WORKER_PROCESSES, NGINX_WORKER_CONNECTIONS, VAULT_DEV_LISTEN_ADDRESS,
)

# Required variables by service
REQUIRED_VARS_BY_SERVICE: Dict[str, List[str]] = {
    "auth_service": [
        DATABASE_URL,
        REDIS_URL,
        JWT_SECRET_KEY,
        JWT_ALGORITHM,
    ],
    "ai_engine_service": [
        DATABASE_URL,
        REDIS_URL,
        OLLAMA_URL,
        CHROMADB_URL,
        EMBEDDING_MODEL,
        CHAT_MODEL,
    ],
    "creator_hub_service": [
        DATABASE_URL,
        REDIS_URL,
        AUTH_SERVICE_URL,
        AI_ENGINE_SERVICE_URL,
    ],
    "channel_service": [
        DATABASE_URL,
        REDIS_URL,
        AUTH_SERVICE_URL,
    ],
}

# Variables organized by category
CATEGORY_VARS: Dict[str, List[str]] = {
    "database": [
        DATABASE_URL, POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD,
        POSTGRES_MAX_CONNECTIONS, POSTGRES_SHARED_BUFFERS, POSTGRES_EFFECTIVE_CACHE_SIZE,
        POSTGRES_WORK_MEM, POSTGRES_MAINTENANCE_WORK_MEM, POSTGRES_CHECKPOINT_COMPLETION_TARGET,
        POSTGRES_WAL_BUFFERS, POSTGRES_DEFAULT_STATISTICS_TARGET, POSTGRES_SHARED_PRELOAD_LIBRARIES,
    ],
    "redis": [
        REDIS_URL,
    ],
    "jwt_auth": [
        JWT_SECRET_KEY, JWT_ALGORITHM, JWT_ACCESS_TOKEN_EXPIRE_MINUTES,
        JWT_REFRESH_TOKEN_EXPIRE_DAYS, JWT_AUDIENCE, JWT_ISSUER,
        JWT_KEYS_DIR, JWT_KEY_ROTATION_DAYS,
    ],
    "ai_services": [
        OLLAMA_URL, OLLAMA_HOST, CHROMADB_URL, CHROMA_SERVER_HOST, CHROMA_SERVER_HTTP_PORT,
        EMBEDDING_MODEL, CHAT_MODEL, CHROMA_SHARD_COUNT, CHROMA_MAX_CONNECTIONS_PER_INSTANCE,
        DEFAULT_CHUNK_SIZE, DEFAULT_CHUNK_OVERLAP,
    ],
    "service_urls": [
        AUTH_SERVICE_URL, AI_ENGINE_SERVICE_URL, CREATOR_HUB_SERVICE_URL, CHANNEL_SERVICE_URL,
    ],
    "security": [
        CORS_ORIGINS, ALLOWED_HOSTS, MAX_FAILED_LOGIN_ATTEMPTS,
        ACCOUNT_LOCKOUT_DURATION_MINUTES, PASSWORD_RESET_TOKEN_EXPIRE_MINUTES,
        ARGON2_MEMORY_COST, ARGON2_TIME_COST, ARGON2_PARALLELISM,
    ],
    "file_upload": [
        MAX_UPLOAD_SIZE, UPLOADS_DIR, SUPPORTED_FORMATS,
    ],
    "environment": [
        ENVIRONMENT, DEBUG, LOG_LEVEL, SQL_ECHO, SLOW_QUERY_THRESHOLD,
    ],
    "rate_limiting": [
        RATE_LIMIT_PER_MINUTE, RATE_LIMIT_PER_HOUR,
    ],
    "websocket": [
        WEBSOCKET_TIMEOUT, MAX_CONNECTIONS_PER_INSTANCE, HEARTBEAT_INTERVAL,
    ],
    "email": [
        FRONTEND_URL, EMAIL_SERVICE_ENABLED, FROM_EMAIL, SMTP_HOST,
        SMTP_PORT, SMTP_USER, SMTP_PASSWORD, SMTP_USE_TLS, FROM_NAME,
    ],
    "gdpr": [
        GDPR_ANONYMIZATION_RETENTION_DAYS, GDPR_AUDIT_RETENTION_YEARS,
    ],
    "vault": [
        VAULT_URL, VAULT_TOKEN, VAULT_MOUNT_POINT, VAULT_ENABLED,
    ],
    "health_check": [
        PORT, HEALTH_CHECK_HOST, HEALTH_CHECK_PATH,
    ],
    "testing": [
        TEST_REDIS_URL, TEST_DATABASE_URL, DB_AUTO_CREATE,
    ],
    "monitoring": [
        MONITORING_SAMPLING_RATE, MONITORING_RETENTION_DAYS, ENABLE_PII_DETECTION, HEALTH_CHECK_INTERVAL_MINUTES,
    ],
    "infrastructure": [
        NGINX_WORKER_PROCESSES, NGINX_WORKER_CONNECTIONS, VAULT_DEV_LISTEN_ADDRESS,
    ],
}


# ============================================================================
# EXPORT CONVENIENCE
# ============================================================================

__all__ = [
    # All environment variable names
    *ALL_ENV_VARS,
    # Helper functions
    "get_env_value",
    "get_environment_defaults",
    "get_current_environment",
    "validate_environment_variables",
    # Collections
    "ALL_ENV_VARS",
    "REQUIRED_VARS_BY_SERVICE",
    "CATEGORY_VARS",
    "ENVIRONMENT_DEFAULTS",
]