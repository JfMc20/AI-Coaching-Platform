"""
Database configuration and session management for Channel Service
"""

import logging
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool

from shared.config.env_constants import get_env_value, DATABASE_URL

logger = logging.getLogger(__name__)

# Database configuration
DATABASE_URL_VALUE = get_env_value(DATABASE_URL)

# Create async engine
engine = create_async_engine(
    DATABASE_URL_VALUE,
    echo=False,  # Set to True for SQL logging in development
    poolclass=NullPool,  # Disable connection pooling for simplicity
    future=True
)

# Create async session factory
async_session = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Database session dependency for FastAPI
    
    Yields:
        AsyncSession: Database session
    """
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def set_tenant_context(session: AsyncSession, creator_id: str) -> None:
    """
    Set tenant context for Row Level Security (RLS)
    
    Args:
        session: Database session
        creator_id: Creator ID for tenant isolation
    """
    try:
        from sqlalchemy import text
        await session.execute(
            text("SET app.current_creator_id = :creator_id"),
            {"creator_id": creator_id}
        )
        logger.debug(f"Set tenant context for creator {creator_id}")
    except Exception as e:
        logger.error(f"Failed to set tenant context for {creator_id}: {e}")
        raise


async def get_tenant_session(creator_id: str) -> AsyncGenerator[AsyncSession, None]:
    """
    Get database session with tenant context set
    
    Args:
        creator_id: Creator ID for tenant isolation
        
    Yields:
        AsyncSession: Database session with tenant context
    """
    async with async_session() as session:
        try:
            # Set tenant context for RLS
            await set_tenant_context(session, creator_id)
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_database():
    """Initialize database connections and validate connectivity"""
    try:
        async with engine.begin() as conn:
            # Test connectivity
            from sqlalchemy import text
            result = await conn.execute(text("SELECT 1"))
            logger.info("✅ Database connection established successfully")
    except Exception as e:
        logger.error(f"❌ Database connection failed: {e}")
        raise


async def close_database():
    """Close database connections"""
    try:
        await engine.dispose()
        logger.info("✅ Database connections closed")
    except Exception as e:
        logger.error(f"❌ Error closing database: {e}")