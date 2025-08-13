-- Create test database script
-- This script should be run against the postgres database to create the test database

-- Create test database if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_database WHERE datname = 'ai_platform_test') THEN
        CREATE DATABASE ai_platform_test;
        RAISE NOTICE 'Database ai_platform_test created successfully';
    ELSE
        RAISE NOTICE 'Database ai_platform_test already exists';
    END IF;
END
$$;