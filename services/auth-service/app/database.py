"""
Database configuration for Auth Service
Async SQLAlchemy setup with connection pooling and multi-tenant support
"""

import os
import logging
from typing import AsyncGenerator, Optional
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool
from sqlalchemy import event, text
import time

from shared.models.database import Base

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Database manager with connection pooling and health checks"""
    
    def __init__(self):
        # Get database URL from environment
        self.database_url = os.getenv("DATABASE_URL")
        if not self.database_url:
            raise ValueError("DATABASE_URL environment variable is required")
        
        # Convert to async URL if needed
        if self.database_url.startswith("postgresql://"):
            self.database_url = self.database_url.replace("postgresql://", "postgresql+asyncpg://", 1)
        elif not self.database_url.startswith("postgresql+asyncpg://"):
            raise ValueError("DATABASE_URL must use postgresql:// or postgresql+asyncpg:// scheme")
        
        # Create async engine with optimized settings
        self.engine = create_async_engine(
            self.database_url,
            # Connection pool settings
            pool_size=20,           # Number of connections to maintain
            max_overflow=30,        # Additional connections beyond pool_size
            pool_pre_ping=True,     # Validate connections before use
            pool_recycle=3600,      # Recycle connections after 1 hour
            
            # Performance settings
            echo=os.getenv("SQL_ECHO", "false").lower() == "true",
            future=True,
            
            # Connection settings
            connect_args={
                "server_settings": {
                    "application_name": "auth-service",
                    "jit": "off"  # Disable JIT for better connection startup time
                }
            }
        )
        
        # Create session factory
        self.async_session = async_sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=True,
            autocommit=False
        )
        
        # Setup event listeners
        self._setup_event_listeners()
    
    def _setup_event_listeners(self):
        """Setup SQLAlchemy event listeners for monitoring and security"""
        
# Get slow query threshold from environment variable, default to 1.0 seconds
        slow_query_threshold = float(os.getenv("SLOW_QUERY_THRESHOLD", "1.0"))
        
        @event.listens_for(self.engine.sync_engine, "before_cursor_execute")
        def log_slow_queries(conn, cursor, statement, parameters, context, executemany):
            """Log slow queries for performance monitoring"""
            context._query_start_time = time.time()
        
        @event.listens_for(self.engine.sync_engine, "after_cursor_execute")
        def log_slow_queries_after(conn, cursor, statement, parameters, context, executemany):
            """Log queries that took longer than threshold"""
            # Check if _query_start_time exists before using it
            if hasattr(context, '_query_start_time'):
                total = time.time() - context._query_start_time
                if total > slow_query_threshold:  # Use configurable threshold
                    logger.warning(f"Slow query ({total:.2f}s): {statement[:200]}...")
            else:
                logger.warning("Missing _query_start_time in context for slow query detection")
    
    @asynccontextmanager
    async def get_session(self) -> AsyncSession:
        """
        Context manager for database sessions with automatic cleanup
        
        Yields:
            AsyncSession: Database session
        """
        async with self.async_session() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()
    
    async def health_check(self) -> bool:
        """
        Check database connectivity and basic functionality
        
        Returns:
            bool: True if database is healthy
        """
        try:
            async with self.get_session() as session:
                # Simple query to test connectivity
                result = await session.execute(text("SELECT 1"))
                return result.scalar() == 1
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False
    
    async def close(self):
        """Close database connections"""
        await self.engine.dispose()


# Global database manager instance (initialized lazily)
db_manager: Optional[DatabaseManager] = None


def get_db_manager() -> DatabaseManager:
    """Get or create database manager instance"""
    global db_manager
    if db_manager is None:
        db_manager = DatabaseManager()
    return db_manager


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency for database sessions
    
    Yields:
        AsyncSession: Database session with automatic cleanup
    """
    manager = get_db_manager()
    async with manager.get_session() as session:
        yield session


async def set_tenant_context(creator_id: str, db: AsyncSession):
    """
    Set tenant context for Row Level Security policies
    
    Args:
        creator_id: Creator ID to set as current tenant
        db: Database session
    """
    try:
        await db.execute(
            text("SELECT set_config('app.current_creator_id', :creator_id, true)"),
            {"creator_id": creator_id}
        )
        logger.debug(f"Tenant context set for creator: {creator_id}")
    except Exception as e:
        logger.error(f"Failed to set tenant context for {creator_id}: {e}")
        raise


async def init_database():
    """
    Initialize database schema and Row Level Security policies
    This should be run during application startup
    """
    try:
        manager = get_db_manager()
        
        # Create tables
        async with manager.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        # Setup Row Level Security policies
        await setup_rls_policies()
        
        logger.info("Database initialization completed successfully")
        
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise


async def setup_rls_policies():
    """Setup Row Level Security policies for multi-tenant isolation"""
    
    rls_policies = [
        # Refresh tokens policy
        """
        DO $$ BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_policies 
                WHERE tablename = 'refresh_tokens' AND policyname = 'tenant_isolation'
            ) THEN
                ALTER TABLE refresh_tokens ENABLE ROW LEVEL SECURITY;
                CREATE POLICY tenant_isolation ON refresh_tokens
                    FOR ALL TO authenticated_user
                    USING (creator_id = current_setting('app.current_creator_id')::uuid);
            END IF;
        END $$;
        """,
        
        # User sessions policy
        """
        DO $$ BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_policies 
                WHERE tablename = 'user_sessions' AND policyname = 'tenant_isolation'
            ) THEN
                ALTER TABLE user_sessions ENABLE ROW LEVEL SECURITY;
                CREATE POLICY tenant_isolation ON user_sessions
                    FOR ALL TO authenticated_user
                    USING (creator_id = current_setting('app.current_creator_id')::uuid);
            END IF;
        END $$;
        """,
        
        # Password reset tokens policy
        """
        DO $$ BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_policies 
                WHERE tablename = 'password_reset_tokens' AND policyname = 'tenant_isolation'
            ) THEN
                ALTER TABLE password_reset_tokens ENABLE ROW LEVEL SECURITY;
                CREATE POLICY tenant_isolation ON password_reset_tokens
                    FOR ALL TO authenticated_user
                    USING (creator_id = current_setting('app.current_creator_id')::uuid);
            END IF;
        END $$;
        """,
        
        # Audit logs policy (creators can only see their own logs)
        """
        DO $$ BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_policies 
                WHERE tablename = 'audit_logs' AND policyname = 'tenant_isolation'
            ) THEN
                ALTER TABLE audit_logs ENABLE ROW LEVEL SECURITY;
                CREATE POLICY tenant_isolation ON audit_logs
                    FOR SELECT TO authenticated_user
                    USING (
                        creator_id = current_setting('app.current_creator_id')::uuid
                        OR current_setting('app.current_creator_id') = 'system'
                    );
            END IF;
        END $$;
        """
    ]
    
    try:
        manager = get_db_manager()
        async with manager.get_session() as session:
            for policy_sql in rls_policies:
                await session.execute(text(policy_sql))
            await session.commit()
        
        logger.info("Row Level Security policies setup completed")
        
    except Exception as e:
        logger.error(f"Failed to setup RLS policies: {e}")
        raise


async def close_db():
    """Close database connections during shutdown"""
    global db_manager
    if db_manager is not None:
        await db_manager.close()
        db_manager = None
