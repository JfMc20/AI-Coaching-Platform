"""Alembic environment configuration for MVP Coaching AI Platform"""

import asyncio
import logging
import os
from logging.config import fileConfig
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config
from alembic import context

# Import your models here
from shared.models.database import Base

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def get_database_url(async_url: bool = True):
    """Get database URL from environment or config"""
    # Try environment variable first
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        # Fallback to config file
        database_url = config.get_main_option("sqlalchemy.url")
    
    if not database_url:
        raise ValueError(
            "No database URL found. Please set the DATABASE_URL environment variable "
            "or configure sqlalchemy.url in alembic.ini"
        )
    
    # Normalize legacy postgres:// prefix
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)
    
    # Convert to async URL if needed
    if async_url and database_url.startswith("postgresql://"):
        database_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    elif not async_url and database_url.startswith("postgresql+asyncpg://"):
        database_url = database_url.replace("postgresql+asyncpg://", "postgresql://", 1)
    
    return database_url


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = get_database_url(async_url=False)  # Use sync URL for offline mode
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """Run migrations with database connection"""
# Get database URL to determine dialect
    database_url = get_database_url(async_url=False)
    
    # Conditionally set render_as_batch based on database dialect
    # Only enable batch mode for SQLite
    render_as_batch = database_url.startswith("sqlite://")
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
        compare_server_default=True,
        # Include schemas in autogenerate
        include_schemas=True,
        # Use batch mode for SQLite compatibility
        render_as_batch=render_as_batch,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Run migrations in async mode"""
    configuration = config.get_section(config.config_ini_section)
    configuration["sqlalchemy.url"] = get_database_url(async_url=True)  # Use async URL for online mode
    
    connectable = async_engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    try:
        async with connectable.connect() as connection:
            await connection.run_sync(do_run_migrations)
    finally:
        try:
            await connectable.dispose()
        except Exception as e:
            logging.error(f"Error disposing connectable: {e}", exc_info=True)


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()