-- Create extensions after database is created
-- This script runs in the ai_platform_test database

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Only create pg_stat_statements if shared_preload_libraries includes it
DO $$
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
$$;

-- Log successful initialization
SELECT 'Test database extensions initialized successfully' as status;