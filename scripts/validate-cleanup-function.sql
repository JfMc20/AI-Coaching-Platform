-- Test Data Cleanup Validation Script
-- Run this script in your test database to validate cleanup function

-- 1. Check if cleanup function exists
SELECT 
    p.proname as function_name,
    n.nspname as schema_name,
    pg_get_function_result(p.oid) as return_type,
    pg_get_function_arguments(p.oid) as arguments
FROM pg_proc p
JOIN pg_namespace n ON p.pronamespace = n.oid
WHERE p.proname = 'cleanup_test_data';

-- 2. View function source code
SELECT pg_get_functiondef(p.oid) as function_definition
FROM pg_proc p
JOIN pg_namespace n ON p.pronamespace = n.oid
WHERE p.proname = 'cleanup_test_data'
AND n.nspname = 'public';

-- 3. Test function execution (use with caution!)
-- SELECT cleanup_test_data(true);

-- 4. Check table existence for cleanup targets
SELECT 
    schemaname,
    tablename,
    hasindexes,
    hasrules,
    hastriggers
FROM pg_tables 
WHERE schemaname IN ('auth', 'content', 'analytics', 'channels')
ORDER BY schemaname, tablename;

-- 5. Check sequences that should be reset
SELECT 
    schemaname,
    sequencename,
    last_value,
    start_value,
    increment_by
FROM pg_sequences 
WHERE schemaname IN ('auth', 'content', 'analytics', 'channels')
ORDER BY schemaname, sequencename;

-- 6. Validate function safety features
SELECT 
    CASE 
        WHEN pg_get_functiondef(p.oid) LIKE '%force%' THEN 'Has force parameter ✅'
        ELSE 'Missing force parameter ❌'
    END as force_check,
    CASE 
        WHEN pg_get_functiondef(p.oid) LIKE '%EXCEPTION%' THEN 'Has error handling ✅'
        ELSE 'Missing error handling ❌'
    END as error_handling_check,
    CASE 
        WHEN pg_get_functiondef(p.oid) LIKE '%RESTART IDENTITY%' THEN 'Uses RESTART IDENTITY ✅'
        ELSE 'Missing RESTART IDENTITY ❌'
    END as restart_identity_check
FROM pg_proc p
JOIN pg_namespace n ON p.pronamespace = n.oid
WHERE p.proname = 'cleanup_test_data'
AND n.nspname = 'public';
