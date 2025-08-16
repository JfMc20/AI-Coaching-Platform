-- =====================================================
-- PostgreSQL Database Initialization Script
-- Multi-Channel AI Coaching Platform
-- =====================================================

-- Create database if not exists (PostgreSQL doesn't support IF NOT EXISTS for databases)
-- The database is created by the POSTGRES_DB environment variable

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";

-- Set timezone
SET timezone = 'UTC';

-- Create application user if not exists
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'app_user') THEN
        CREATE ROLE app_user WITH LOGIN PASSWORD 'app_password';
    END IF;
END
$$;

-- Grant necessary permissions
GRANT CONNECT ON DATABASE ai_platform_dev TO app_user;
GRANT USAGE ON SCHEMA public TO app_user;
GRANT CREATE ON SCHEMA public TO app_user;

-- Create basic configuration
CREATE TABLE IF NOT EXISTS _database_info (
    key VARCHAR(50) PRIMARY KEY,
    value TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Insert database metadata
INSERT INTO _database_info (key, value) VALUES 
    ('version', '1.0.0'),
    ('initialized_at', NOW()::TEXT),
    ('platform', 'multi-channel-ai-coaching')
ON CONFLICT (key) DO UPDATE SET 
    value = EXCLUDED.value,
    created_at = NOW();

-- Log initialization
\echo 'Database initialization completed successfully'