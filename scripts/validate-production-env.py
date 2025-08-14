#!/usr/bin/env python3
"""
Production Environment Validation Script

Validates critical security environment variables before service startup.
Exits with clear error messages if any required variables are missing or invalid.
"""

import os
import sys
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def validate_jwt_config():
    """Validate JWT configuration variables."""
    errors = []
    
    # JWT Secret Key
    jwt_secret = os.environ.get('JWT_SECRET_KEY')
    if not jwt_secret:
        errors.append("JWT_SECRET_KEY is required but not set")
    elif len(jwt_secret) < 32:
        errors.append("JWT_SECRET_KEY must be at least 32 characters long")
    
    # JWT Keys Directory
    jwt_keys_dir = os.environ.get('JWT_KEYS_DIR')
    if jwt_keys_dir:
        keys_path = Path(jwt_keys_dir)
        if not keys_path.exists():
            errors.append(f"JWT_KEYS_DIR path does not exist: {jwt_keys_dir}")
        elif not keys_path.is_dir():
            errors.append(f"JWT_KEYS_DIR is not a directory: {jwt_keys_dir}")
    
    # JWT Algorithm
    jwt_algorithm = os.environ.get('JWT_ALGORITHM', 'RS256')
    allowed_algorithms = ['RS256', 'ES256', 'HS256']
    if jwt_algorithm not in allowed_algorithms:
        errors.append(f"JWT_ALGORITHM must be one of {allowed_algorithms}, got: {jwt_algorithm}")
    
    return errors

def validate_database_config():
    """Validate database configuration variables."""
    errors = []
    
    # Database URL
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        errors.append("DATABASE_URL is required but not set")
    elif not database_url.startswith(('postgresql://', 'postgres://')):
        errors.append("DATABASE_URL must be a valid PostgreSQL connection string")
    
    return errors

def validate_redis_config():
    """Validate Redis configuration variables."""
    errors = []
    
    # Redis URL
    redis_url = os.environ.get('REDIS_URL')
    if not redis_url:
        errors.append("REDIS_URL is required but not set")
    elif not redis_url.startswith('redis://'):
        errors.append("REDIS_URL must be a valid Redis connection string")
    
    return errors

def validate_vault_config():
    """Validate Vault configuration if enabled."""
    errors = []
    
    vault_enabled = os.environ.get('VAULT_ENABLED', 'false').lower()
    if vault_enabled in ['true', '1', 'yes']:
        vault_url = os.environ.get('VAULT_URL')
        if not vault_url:
            errors.append("VAULT_URL is required when VAULT_ENABLED=true")
        
        vault_token = os.environ.get('VAULT_TOKEN')
        vault_role_id = os.environ.get('VAULT_ROLE_ID')
        if not vault_token and not vault_role_id:
            errors.append("Either VAULT_TOKEN or VAULT_ROLE_ID is required when VAULT_ENABLED=true")
    
    return errors

def validate_environment():
    """Validate environment configuration."""
    errors = []
    
    environment = os.environ.get('ENVIRONMENT', 'development')
    if environment == 'production':
        # Additional production-specific validations
        debug = os.environ.get('DEBUG', 'false').lower()
        if debug in ['true', '1', 'yes']:
            errors.append("DEBUG must be disabled in production environment")
        
        log_level = os.environ.get('LOG_LEVEL', 'INFO')
        if log_level.upper() == 'DEBUG':
            errors.append("LOG_LEVEL should not be DEBUG in production environment")
    
    return errors

def main():
    """Main validation function."""
    logger.info("Starting production environment validation...")
    
    all_errors = []
    
    # Run all validations
    all_errors.extend(validate_jwt_config())
    all_errors.extend(validate_database_config())
    all_errors.extend(validate_redis_config())
    all_errors.extend(validate_vault_config())
    all_errors.extend(validate_environment())
    
    if all_errors:
        logger.error("❌ Production environment validation failed:")
        for i, error in enumerate(all_errors, 1):
            logger.error(f"  {i}. {error}")
        
        logger.error("\n🔧 To fix these issues:")
        logger.error("  1. Set all required environment variables")
        logger.error("  2. Use strong, randomly generated secrets")
        logger.error("  3. Ensure all paths exist and are accessible")
        logger.error("  4. Review security configuration settings")
        
        sys.exit(1)
    
    logger.info("✅ Production environment validation passed")
    logger.info("All critical security variables are properly configured")

if __name__ == "__main__":
    main()