-- Create test database script
-- This script should be run against the postgres database to create the test database

-- Check if database exists and create conditionally
-- Note: This uses \gexec to execute the CREATE DATABASE outside of a transaction
SELECT 'CREATE DATABASE ai_platform_test;' 
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'ai_platform_test') \gexec

-- Alternative approach for shell-based execution:
-- Use: psql -tc "SELECT 1 FROM pg_database WHERE datname='ai_platform_test'" | grep -q 1 || createdb ai_platform_test