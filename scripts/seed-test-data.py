#!/usr/bin/env python3
"""
Test data seeding script.
Seeds the test database with consistent data for testing.
"""

import os
import sys
import asyncio
import asyncpg
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


async def seed_test_database():
    """Seed the test database with consistent test data."""
    database_url = os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5433/ai_platform_test')
    
    try:
        conn = await asyncpg.connect(database_url)
        logger.info("Connected to test database")
        
        # Clean existing data first
        logger.info("Cleaning existing test data...")
        await conn.execute("SELECT cleanup_test_data(true);")
        
        # Seed basic test data
        logger.info("Seeding test users...")
        await conn.execute("""
            INSERT INTO auth.users (id, email, username, is_active, created_at) 
            VALUES 
                ('test-user-1', 'test1@example.com', 'testuser1', true, NOW()),
                ('test-user-2', 'test2@example.com', 'testuser2', true, NOW()),
                ('admin-user', 'admin@example.com', 'admin', true, NOW())
            ON CONFLICT (email) DO NOTHING;
        """)
        
        logger.info("Seeding test content...")
        await conn.execute("""
            INSERT INTO content.documents (id, title, content, user_id, created_at)
            VALUES 
                ('doc-1', 'Test Document 1', 'This is test content 1', 'test-user-1', NOW()),
                ('doc-2', 'Test Document 2', 'This is test content 2', 'test-user-2', NOW())
            ON CONFLICT (id) DO NOTHING;
        """)
        
        logger.info("Seeding test analytics...")
        await conn.execute("""
            INSERT INTO analytics.events (id, event_type, user_id, data, created_at)
            VALUES 
                ('event-1', 'login', 'test-user-1', '{"source": "test"}', NOW()),
                ('event-2', 'document_view', 'test-user-1', '{"document_id": "doc-1"}', NOW())
            ON CONFLICT (id) DO NOTHING;
        """)
        
        # Verify seeded data
        user_count = await conn.fetchval("SELECT COUNT(*) FROM auth.users")
        doc_count = await conn.fetchval("SELECT COUNT(*) FROM content.documents")
        event_count = await conn.fetchval("SELECT COUNT(*) FROM analytics.events")
        
        logger.info(f"Test data seeded successfully:")
        logger.info(f"  Users: {user_count}")
        logger.info(f"  Documents: {doc_count}")
        logger.info(f"  Events: {event_count}")
        
        await conn.close()
        return True
        
    except Exception as e:
        logger.error(f"Failed to seed test database: {e}")
        return False


async def main():
    """Main seeding function."""
    logger.info("Starting test data seeding...")
    
    success = await seed_test_database()
    
    if success:
        logger.info("✅ Test data seeding completed successfully")
        return True
    else:
        logger.error("❌ Test data seeding failed")
        return False


if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        logger.info("Test data seeding interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Test data seeding failed with error: {e}")
        sys.exit(1)