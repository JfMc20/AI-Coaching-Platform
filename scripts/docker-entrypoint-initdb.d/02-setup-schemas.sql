-- Set up test database schemas and roles
-- This script runs after extensions are created

-- Enable Row Level Security globally
ALTER DATABASE ai_platform_test SET row_security = on;

-- Create test schemas
CREATE SCHEMA IF NOT EXISTS auth;
CREATE SCHEMA IF NOT EXISTS content;
CREATE SCHEMA IF NOT EXISTS analytics;
CREATE SCHEMA IF NOT EXISTS channels;

-- Create test roles for multi-tenancy testing
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'test_tenant_1') THEN
        CREATE ROLE test_tenant_1;
    END IF;
    
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'test_tenant_2') THEN
        CREATE ROLE test_tenant_2;
    END IF;
    
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'test_admin') THEN
        CREATE ROLE test_admin WITH SUPERUSER;
    END IF;
END
$$;

-- Grant necessary permissions
GRANT USAGE ON SCHEMA auth TO test_tenant_1, test_tenant_2;
GRANT USAGE ON SCHEMA content TO test_tenant_1, test_tenant_2;
GRANT USAGE ON SCHEMA analytics TO test_tenant_1, test_tenant_2;
GRANT USAGE ON SCHEMA channels TO test_tenant_1, test_tenant_2;

-- Log successful schema setup
SELECT 'Test database schemas and roles created successfully' as status;