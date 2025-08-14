-- Set up test database schemas and roles
-- This script runs after extensions are created

-- Enable Row Level Security globally
ALTER DATABASE ai_platform_dev SET row_security = on;

-- Create test schemas
CREATE SCHEMA IF NOT EXISTS auth;
CREATE SCHEMA IF NOT EXISTS content;
CREATE SCHEMA IF NOT EXISTS analytics;
CREATE SCHEMA IF NOT EXISTS channels;

-- Create test roles for multi-tenancy testing
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'app_tenant_1') THEN
        CREATE ROLE app_tenant_1;
    END IF;
    
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'app_tenant_2') THEN
        CREATE ROLE app_tenant_2;
    END IF;
    
    -- Only create dev_admin role in development environments
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'dev_admin') AND 
       current_database() LIKE '%dev%' THEN
        -- Create restricted dev admin role (no SUPERUSER for security)
        CREATE ROLE dev_admin WITH LOGIN CREATEDB CREATEROLE;
        -- Grant necessary schema permissions
        GRANT ALL PRIVILEGES ON SCHEMA auth, content, analytics, channels TO dev_admin;
    END IF;
END
$$;

-- Grant necessary permissions
GRANT USAGE ON SCHEMA auth TO app_tenant_1, app_tenant_2;
GRANT USAGE ON SCHEMA content TO app_tenant_1, app_tenant_2;
GRANT USAGE ON SCHEMA analytics TO app_tenant_1, app_tenant_2;
GRANT USAGE ON SCHEMA channels TO app_tenant_1, app_tenant_2;

-- Log successful schema setup
SELECT 'Database schemas and roles created successfully' as status;