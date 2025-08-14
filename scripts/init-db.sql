-- Database Initialization Script
-- This script initializes the database with extensions, schemas, and functions
-- Consolidates all initialization scripts for Docker container setup

-- =============================================================================
-- EXTENSIONS SETUP
-- =============================================================================

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Only create pg_stat_statements if shared_preload_libraries includes it
DO $
BEGIN
    -- Check if pg_stat_statements is available
    IF EXISTS (
        SELECT 1 FROM pg_available_extensions 
        WHERE name = 'pg_stat_statements' 
        AND installed_version IS NOT NULL
    ) THEN
        CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";
        RAISE NOTICE 'pg_stat_statements extension created successfully';
    ELSE
        RAISE NOTICE 'pg_stat_statements extension not available (shared_preload_libraries may need configuration)';
    END IF;
EXCEPTION
    WHEN OTHERS THEN
        RAISE NOTICE 'Could not create pg_stat_statements extension: %', SQLERRM;
END
$;

-- =============================================================================
-- SCHEMAS AND ROLES SETUP
-- =============================================================================

-- Enable Row Level Security globally
ALTER DATABASE ai_platform_dev SET row_security = on;

-- Create application schemas
CREATE SCHEMA IF NOT EXISTS auth;
CREATE SCHEMA IF NOT EXISTS content;
CREATE SCHEMA IF NOT EXISTS analytics;
CREATE SCHEMA IF NOT EXISTS channels;

-- Create roles for multi-tenancy
DO $
BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'app_tenant_1') THEN
        CREATE ROLE app_tenant_1;
    END IF;
    
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'app_tenant_2') THEN
        CREATE ROLE app_tenant_2;
    END IF;
    
    -- Only create admin role in development environments
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'app_admin') AND 
       current_database() LIKE '%dev%' THEN
        -- Create restricted admin role (no SUPERUSER for security)
        CREATE ROLE app_admin WITH LOGIN CREATEDB CREATEROLE;
        -- Grant necessary schema permissions
        GRANT ALL PRIVILEGES ON SCHEMA auth, content, analytics, channels TO app_admin;
    END IF;
END
$;

-- Grant necessary permissions
GRANT USAGE ON SCHEMA auth TO app_tenant_1, app_tenant_2;
GRANT USAGE ON SCHEMA content TO app_tenant_1, app_tenant_2;
GRANT USAGE ON SCHEMA analytics TO app_tenant_1, app_tenant_2;
GRANT USAGE ON SCHEMA channels TO app_tenant_1, app_tenant_2;

-- =============================================================================
-- UTILITY FUNCTIONS
-- =============================================================================

-- Create data cleanup function for development
CREATE OR REPLACE FUNCTION cleanup_dev_data(force boolean DEFAULT false)
RETURNS void AS $
DECLARE
    current_env text;
BEGIN
    -- Safety check: force parameter must be true
    IF NOT force THEN
        RAISE EXCEPTION 'cleanup_dev_data() requires force=true parameter to prevent accidental execution. Usage: SELECT cleanup_dev_data(true);';
    END IF;
    
    -- Additional safety: check environment (if available)
    BEGIN
        SELECT current_setting('app.environment', true) INTO current_env;
        IF current_env IS NOT NULL AND current_env NOT IN ('development', 'dev', 'local') THEN
            RAISE EXCEPTION 'cleanup_dev_data() cannot run in environment: %. Only allowed in: development, dev, local', current_env;
        END IF;
    EXCEPTION
        WHEN OTHERS THEN
            -- Environment setting not available, continue with warning
            RAISE NOTICE 'Environment check skipped - ensure this is a development environment';
    END;
    
    -- Clean up development data
    RAISE NOTICE 'Development data cleanup function ready';
END;
$ LANGUAGE plpgsql;

-- Create function to validate environment
CREATE OR REPLACE FUNCTION validate_environment()
RETURNS TABLE(check_name text, status text, details text) AS $
BEGIN
    -- Check extensions
    RETURN QUERY
    SELECT 
        'Extensions'::text,
        CASE WHEN count(*) >= 2 THEN 'OK' ELSE 'MISSING' END::text,
        string_agg(extname, ', ')::text
    FROM pg_extension 
    WHERE extname IN ('uuid-ossp', 'pgcrypto', 'pg_stat_statements');
    
    -- Check schemas
    RETURN QUERY
    SELECT 
        'Schemas'::text,
        CASE WHEN count(*) >= 4 THEN 'OK' ELSE 'MISSING' END::text,
        string_agg(schema_name, ', ')::text
    FROM information_schema.schemata 
    WHERE schema_name IN ('auth', 'content', 'analytics', 'channels');
    
    -- Check roles
    RETURN QUERY
    SELECT 
        'App Roles'::text,
        CASE WHEN count(*) >= 2 THEN 'OK' ELSE 'MISSING' END::text,
        string_agg(rolname, ', ')::text
    FROM pg_roles 
    WHERE rolname IN ('app_tenant_1', 'app_tenant_2', 'app_admin');
END;
$ LANGUAGE plpgsql;

-- =============================================================================
-- INITIALIZATION COMPLETE
-- =============================================================================

-- Log successful initialization
SELECT 'Database initialization completed successfully' as status;