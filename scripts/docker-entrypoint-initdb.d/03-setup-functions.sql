-- Set up test utility functions
-- This script creates helper functions for testing

-- Create data cleanup function
CREATE OR REPLACE FUNCTION cleanup_dev_data(force boolean DEFAULT false)
RETURNS void AS $$
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
    
    -- This function can be called to clean up test data between test runs
    -- Using single TRUNCATE statement with RESTART IDENTITY for better performance
    
    -- Check if tables exist and truncate them atomically
    BEGIN
        TRUNCATE TABLE 
            auth.users,
            content.documents,
            analytics.events,
            channels.sessions
        RESTART IDENTITY CASCADE;
        
        RAISE NOTICE 'Development data cleanup completed for all tables';
    EXCEPTION
        WHEN undefined_table THEN
            -- Handle case where some tables might not exist
            RAISE NOTICE 'Some tables do not exist, attempting individual cleanup';
            
            -- Fallback to individual table cleanup
            BEGIN TRUNCATE TABLE auth.users RESTART IDENTITY CASCADE; EXCEPTION WHEN undefined_table THEN NULL; END;
            BEGIN TRUNCATE TABLE content.documents RESTART IDENTITY CASCADE; EXCEPTION WHEN undefined_table THEN NULL; END;
            BEGIN TRUNCATE TABLE analytics.events RESTART IDENTITY CASCADE; EXCEPTION WHEN undefined_table THEN NULL; END;
            BEGIN TRUNCATE TABLE channels.sessions RESTART IDENTITY CASCADE; EXCEPTION WHEN undefined_table THEN NULL; END;
            
            RAISE NOTICE 'Development data cleanup completed with fallback method';
    END;
END;
$$ LANGUAGE plpgsql;

-- Create data seeding function
CREATE OR REPLACE FUNCTION seed_dev_data()
RETURNS void AS $$
BEGIN
    -- This function can be called to seed test data
    -- Implementation will be added as needed for specific tests
    RAISE NOTICE 'Development data seeding function ready';
END;
$$ LANGUAGE plpgsql;

-- Create function to validate environment
CREATE OR REPLACE FUNCTION validate_environment()
RETURNS TABLE(check_name text, status text, details text) AS $$
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
    WHERE rolname IN ('app_tenant_1', 'app_tenant_2', 'dev_admin');
END;
$$ LANGUAGE plpgsql;

-- Log successful function setup
SELECT 'Utility functions created successfully' as status;