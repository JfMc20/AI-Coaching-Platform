---
inclusion: always
---

# Database Design & Multi-Tenancy Guidelines

## PostgreSQL Schema Design

### Core Table Structure
All tables MUST follow the multi-tenant design pattern with Row Level Security:

```sql
-- Core creators table (tenant root)
CREATE TABLE creators (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    company_name VARCHAR(255),
    subscription_tier VARCHAR(50) DEFAULT 'free',
    is_active BOOLEAN DEFAULT true,
    email_verified BOOLEAN DEFAULT false,
    email_verification_token VARCHAR(255),
    password_reset_token VARCHAR(255),
    password_reset_expires TIMESTAMP WITH TIME ZONE,
    last_login TIMESTAMP WITH TIME ZONE,
    login_count INTEGER DEFAULT 0,
    settings JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- User sessions for end users
CREATE TABLE user_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    creator_id UUID NOT NULL REFERENCES creators(id) ON DELETE CASCADE,
    session_id VARCHAR(255) NOT NULL,
    channel VARCHAR(50) NOT NULL DEFAULT 'widget',
    user_profile JSONB DEFAULT '{}'::jsonb,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_activity TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE DEFAULT (NOW() + INTERVAL '24 hours'),
    is_active BOOLEAN DEFAULT true,
    UNIQUE(creator_id, session_id)
);

-- Conversations between users and AI
CREATE TABLE conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    creator_id UUID NOT NULL REFERENCES creators(id) ON DELETE CASCADE,
    user_session_id UUID NOT NULL REFERENCES user_sessions(id) ON DELETE CASCADE,
    channel VARCHAR(50) NOT NULL,
    status VARCHAR(50) DEFAULT 'active',
    context JSONB DEFAULT '{}'::jsonb,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Individual messages in conversations
CREATE TABLE messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    creator_id UUID NOT NULL, -- Denormalized for RLS
    sender_type VARCHAR(20) NOT NULL CHECK (sender_type IN ('user', 'ai')),
    content TEXT NOT NULL,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    FOREIGN KEY (creator_id) REFERENCES creators(id) ON DELETE CASCADE
);

-- Knowledge base documents
CREATE TABLE knowledge_documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    creator_id UUID NOT NULL REFERENCES creators(id) ON DELETE CASCADE,
    document_id VARCHAR(255) NOT NULL, -- From document processor
    filename VARCHAR(255) NOT NULL,
    original_filename VARCHAR(255) NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    file_size INTEGER NOT NULL,
    mime_type VARCHAR(100) NOT NULL,
    processing_status VARCHAR(50) DEFAULT 'pending',
    processed_at TIMESTAMP WITH TIME ZONE,
    chunk_count INTEGER DEFAULT 0,
    error_message TEXT,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(creator_id, document_id)
);

-- Widget configuration per creator
CREATE TABLE widget_configs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    creator_id UUID NOT NULL REFERENCES creators(id) ON DELETE CASCADE,
    widget_id VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT true,
    theme JSONB DEFAULT '{
        "primary_color": "#007bff",
        "secondary_color": "#6c757d",
        "background_color": "#ffffff",
        "text_color": "#212529",
        "border_radius": 8
    }'::jsonb,
    behavior JSONB DEFAULT '{
        "auto_open": false,
        "greeting_message": "¡Hola! ¿En qué puedo ayudarte?",
        "placeholder_text": "Escribe tu mensaje...",
        "show_typing_indicator": true,
        "response_delay_ms": 1000
    }'::jsonb,
    allowed_domains TEXT[] DEFAULT '{}',
    rate_limit_per_minute INTEGER DEFAULT 10,
    embed_code TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(creator_id)
);

-- Security audit logs
CREATE TABLE security_audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_type VARCHAR(100) NOT NULL,
    creator_id UUID REFERENCES creators(id) ON DELETE SET NULL,
    event_data JSONB NOT NULL,
    severity VARCHAR(20) NOT NULL,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- API usage tracking
CREATE TABLE api_usage_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    creator_id UUID NOT NULL REFERENCES creators(id) ON DELETE CASCADE,
    endpoint VARCHAR(255) NOT NULL,
    method VARCHAR(10) NOT NULL,
    status_code INTEGER NOT NULL,
    response_time_ms INTEGER,
    request_size_bytes INTEGER,
    response_size_bytes INTEGER,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### Row Level Security (RLS) Implementation
Enable RLS on all multi-tenant tables:

```sql
-- Enable RLS on all tenant tables
ALTER TABLE user_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE conversations ENABLE ROW LEVEL SECURITY;
ALTER TABLE messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE knowledge_documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE widget_configs ENABLE ROW LEVEL SECURITY;
ALTER TABLE api_usage_logs ENABLE ROW LEVEL SECURITY;

-- Create RLS policies for tenant isolation
CREATE POLICY tenant_isolation_user_sessions ON user_sessions
    FOR ALL TO authenticated_user
    USING (creator_id = current_setting('app.current_creator_id')::UUID);

CREATE POLICY tenant_isolation_conversations ON conversations
    FOR ALL TO authenticated_user
    USING (creator_id = current_setting('app.current_creator_id')::UUID);

CREATE POLICY tenant_isolation_messages ON messages
    FOR ALL TO authenticated_user
    USING (creator_id = current_setting('app.current_creator_id')::UUID);

CREATE POLICY tenant_isolation_knowledge_documents ON knowledge_documents
    FOR ALL TO authenticated_user
    USING (creator_id = current_setting('app.current_creator_id')::UUID);

CREATE POLICY tenant_isolation_widget_configs ON widget_configs
    FOR ALL TO authenticated_user
    USING (creator_id = current_setting('app.current_creator_id')::UUID);

CREATE POLICY tenant_isolation_api_usage_logs ON api_usage_logs
    FOR ALL TO authenticated_user
    USING (creator_id = current_setting('app.current_creator_id')::UUID);

-- Security audit logs - special policy (admins can see all, users see their own)
ALTER TABLE security_audit_logs ENABLE ROW LEVEL SECURITY;
CREATE POLICY security_audit_policy ON security_audit_logs
    FOR SELECT TO authenticated_user
    USING (
        creator_id = current_setting('app.current_creator_id')::UUID 
        OR current_setting('app.user_role') = 'admin'
    );
```

### Performance Indexes
Create comprehensive indexes for optimal query performance:

```sql
-- Primary indexes for tenant isolation
CREATE INDEX idx_user_sessions_creator_id ON user_sessions(creator_id);
CREATE INDEX idx_conversations_creator_id ON conversations(creator_id);
CREATE INDEX idx_messages_creator_id ON messages(creator_id);
CREATE INDEX idx_knowledge_documents_creator_id ON knowledge_documents(creator_id);
CREATE INDEX idx_widget_configs_creator_id ON widget_configs(creator_id);
CREATE INDEX idx_api_usage_logs_creator_id ON api_usage_logs(creator_id);

-- Composite indexes for common query patterns
CREATE INDEX idx_user_sessions_creator_session ON user_sessions(creator_id, session_id);
CREATE INDEX idx_conversations_creator_user_session ON conversations(creator_id, user_session_id);
CREATE INDEX idx_messages_conversation_created ON messages(conversation_id, created_at DESC);
CREATE INDEX idx_knowledge_documents_creator_status ON knowledge_documents(creator_id, processing_status);

-- Time-based indexes for analytics and cleanup
CREATE INDEX idx_user_sessions_last_activity ON user_sessions(last_activity);
CREATE INDEX idx_conversations_updated_at ON conversations(updated_at);
CREATE INDEX idx_messages_created_at ON messages(created_at);
CREATE INDEX idx_security_audit_logs_created_at ON security_audit_logs(created_at);
CREATE INDEX idx_api_usage_logs_created_at ON api_usage_logs(created_at);

-- Search and filtering indexes
CREATE INDEX idx_creators_email ON creators(email);
CREATE INDEX idx_creators_subscription_tier ON creators(subscription_tier);
CREATE INDEX idx_user_sessions_channel ON user_sessions(channel);
CREATE INDEX idx_conversations_status ON conversations(status);
CREATE INDEX idx_messages_sender_type ON messages(sender_type);

-- JSONB indexes for metadata queries
CREATE INDEX idx_user_sessions_profile_gin ON user_sessions USING GIN(user_profile);
CREATE INDEX idx_conversations_context_gin ON conversations USING GIN(context);
CREATE INDEX idx_messages_metadata_gin ON messages USING GIN(metadata);
CREATE INDEX idx_knowledge_documents_metadata_gin ON knowledge_documents USING GIN(metadata);
CREATE INDEX idx_widget_configs_theme_gin ON widget_configs USING GIN(theme);
CREATE INDEX idx_widget_configs_behavior_gin ON widget_configs USING GIN(behavior);

-- Partial indexes for active records
CREATE INDEX idx_user_sessions_active ON user_sessions(creator_id, last_activity) 
    WHERE is_active = true;
CREATE INDEX idx_conversations_active ON conversations(creator_id, updated_at) 
    WHERE status = 'active';
CREATE INDEX idx_knowledge_documents_completed ON knowledge_documents(creator_id, created_at) 
    WHERE processing_status = 'completed';
```

## Database Connection Management

### Async SQLAlchemy Configuration
Implement proper async database connection handling:

```python
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy.pool import NullPool
from contextlib import asynccontextmanager
from typing import AsyncGenerator
import logging

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Manages async database connections and sessions."""
    
    def __init__(self, database_url: str):
        # Configure async engine
        self.engine = create_async_engine(
            database_url,
            echo=False,  # Set to True for SQL debugging
            pool_size=20,
            max_overflow=30,
            pool_timeout=30,
            pool_recycle=3600,  # Recycle connections every hour
            pool_pre_ping=True,  # Validate connections before use
            poolclass=NullPool if "sqlite" in database_url else None
        )
        
        # Create session factory
        self.async_session_factory = async_sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False
        )
    
    @asynccontextmanager
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get async database session with proper cleanup."""
        
        async with self.async_session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception as e:
                await session.rollback()
                logger.exception(f"Database session error: {e}")
                raise
            finally:
                await session.close()
    
    async def set_tenant_context(self, session: AsyncSession, creator_id: str) -> None:
        """Set tenant context for RLS policies."""
        
        try:
            await session.execute(
                text("SET app.current_creator_id = :creator_id"),
                {"creator_id": creator_id}
            )
        except Exception as e:
            logger.exception(f"Failed to set tenant context: {e}")
            raise
    
    async def health_check(self) -> bool:
        """Check database connectivity and health."""
        
        try:
            async with self.get_session() as session:
                result = await session.execute(text("SELECT 1"))
                return result.scalar() == 1
        except Exception as e:
            logger.exception(f"Database health check failed: {e}")
            return False
    
    async def close(self) -> None:
        """Close database engine and connections."""
        
        try:
            await self.engine.dispose()
            logger.info("Database connections closed")
        except Exception as e:
            logger.exception(f"Error closing database: {e}")

# Usage in FastAPI dependency
database_manager = DatabaseManager(DATABASE_URL)

async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency for database sessions."""
    async with database_manager.get_session() as session:
        yield session

async def get_tenant_session(
    creator_id: str = Depends(get_current_creator_id),
    session: AsyncSession = Depends(get_db_session)
) -> AsyncSession:
    """FastAPI dependency for tenant-aware database sessions."""
    await database_manager.set_tenant_context(session, creator_id)
    return session
```

### Repository Pattern Implementation
Implement repository pattern for clean data access:

```python
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, and_, or_
from sqlalchemy.orm import selectinload
from datetime import datetime

class BaseRepository(ABC):
    """Base repository with common CRUD operations."""
    
    def __init__(self, session: AsyncSession, model_class):
        self.session = session
        self.model_class = model_class
    
    async def create(self, **kwargs) -> Any:
        """Create new record."""
        instance = self.model_class(**kwargs)
        self.session.add(instance)
        await self.session.flush()
        await self.session.refresh(instance)
        return instance
    
    async def get_by_id(self, id: str) -> Optional[Any]:
        """Get record by ID."""
        result = await self.session.execute(
            select(self.model_class).where(self.model_class.id == id)
        )
        return result.scalar_one_or_none()
    
    async def update(self, id: str, **kwargs) -> Optional[Any]:
        """Update record by ID."""
        kwargs['updated_at'] = datetime.utcnow()
        
        result = await self.session.execute(
            update(self.model_class)
            .where(self.model_class.id == id)
            .values(**kwargs)
            .returning(self.model_class)
        )
        return result.scalar_one_or_none()
    
    async def delete(self, id: str) -> bool:
        """Delete record by ID."""
        result = await self.session.execute(
            delete(self.model_class).where(self.model_class.id == id)
        )
        return result.rowcount > 0
    
    async def list_paginated(
        self, 
        page: int = 1, 
        per_page: int = 20,
        filters: Optional[Dict[str, Any]] = None,
        order_by: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get paginated list of records."""
        
        query = select(self.model_class)
        
        # Apply filters
        if filters:
            for field, value in filters.items():
                if hasattr(self.model_class, field):
                    query = query.where(getattr(self.model_class, field) == value)
        
        # Apply ordering
        if order_by and hasattr(self.model_class, order_by):
            query = query.order_by(getattr(self.model_class, order_by).desc())
        else:
            query = query.order_by(self.model_class.created_at.desc())
        
        # Count total records
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.session.execute(count_query)
        total = total_result.scalar()
        
        # Apply pagination
        offset = (page - 1) * per_page
        query = query.offset(offset).limit(per_page)
        
        result = await self.session.execute(query)
        items = result.scalars().all()
        
        return {
            "items": items,
            "total": total,
            "page": page,
            "per_page": per_page,
            "total_pages": (total + per_page - 1) // per_page,
            "has_next": page * per_page < total,
            "has_prev": page > 1
        }

class ConversationRepository(BaseRepository):
    """Repository for conversation operations."""
    
    def __init__(self, session: AsyncSession):
        super().__init__(session, Conversation)
    
    async def get_with_messages(
        self, 
        conversation_id: str, 
        message_limit: int = 50
    ) -> Optional[Any]:
        """Get conversation with recent messages."""
        
        result = await self.session.execute(
            select(self.model_class)
            .options(
                selectinload(self.model_class.messages)
                .options(selectinload(Message.metadata))
                .limit(message_limit)
            )
            .where(self.model_class.id == conversation_id)
        )
        return result.scalar_one_or_none()
    
    async def get_active_by_session(self, user_session_id: str) -> Optional[Any]:
        """Get active conversation for user session."""
        
        result = await self.session.execute(
            select(self.model_class)
            .where(
                and_(
                    self.model_class.user_session_id == user_session_id,
                    self.model_class.status == 'active'
                )
            )
            .order_by(self.model_class.updated_at.desc())
        )
        return result.scalar_one_or_none()
    
    async def get_creator_conversations(
        self, 
        creator_id: str,
        page: int = 1,
        per_page: int = 20,
        status: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get paginated conversations for creator."""
        
        filters = {"creator_id": creator_id}
        if status:
            filters["status"] = status
        
        return await self.list_paginated(
            page=page,
            per_page=per_page,
            filters=filters,
            order_by="updated_at"
        )

class KnowledgeDocumentRepository(BaseRepository):
    """Repository for knowledge document operations."""
    
    def __init__(self, session: AsyncSession):
        super().__init__(session, KnowledgeDocument)
    
    async def get_by_document_id(
        self, 
        creator_id: str, 
        document_id: str
    ) -> Optional[Any]:
        """Get document by document_id and creator."""
        
        result = await self.session.execute(
            select(self.model_class)
            .where(
                and_(
                    self.model_class.creator_id == creator_id,
                    self.model_class.document_id == document_id
                )
            )
        )
        return result.scalar_one_or_none()
    
    async def get_completed_documents(self, creator_id: str) -> List[Any]:
        """Get all completed documents for creator."""
        
        result = await self.session.execute(
            select(self.model_class)
            .where(
                and_(
                    self.model_class.creator_id == creator_id,
                    self.model_class.processing_status == 'completed'
                )
            )
            .order_by(self.model_class.created_at.desc())
        )
        return result.scalars().all()
    
    async def update_processing_status(
        self, 
        document_id: str, 
        status: str,
        chunk_count: Optional[int] = None,
        error_message: Optional[str] = None
    ) -> Optional[Any]:
        """Update document processing status."""
        
        update_data = {
            "processing_status": status,
            "updated_at": datetime.utcnow()
        }
        
        if status == 'completed':
            update_data["processed_at"] = datetime.utcnow()
            if chunk_count is not None:
                update_data["chunk_count"] = chunk_count
        
        if status == 'failed' and error_message:
            update_data["error_message"] = error_message
        
        result = await self.session.execute(
            update(self.model_class)
            .where(self.model_class.document_id == document_id)
            .values(**update_data)
            .returning(self.model_class)
        )
        return result.scalar_one_or_none()
```

## Database Migrations with Alembic

### Migration Management
Implement proper database migration workflow:

```python
# alembic/env.py
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from sqlalchemy.ext.asyncio import AsyncEngine
from alembic import context
import asyncio

# Import your models here
from shared.models.database import Base

# Alembic Config object
config = context.config

# Interpret the config file for Python logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Target metadata for autogenerate support
target_metadata = Base.metadata

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()

def do_run_migrations(connection):
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()

async def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    connectable = AsyncEngine(
        engine_from_config(
            config.get_section(config.config_ini_section),
            prefix="sqlalchemy.",
            poolclass=pool.NullPool,
        )
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()

if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
```

### Migration Templates
Create standardized migration templates:

```python
# Migration template for new table
"""Add {table_name} table

Revision ID: {revision_id}
Revises: {down_revision}
Create Date: {create_date}
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '{revision_id}'
down_revision = '{down_revision}'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Create table
    op.create_table(
        '{table_name}',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('creator_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('NOW()')),
        sa.ForeignKeyConstraint(['creator_id'], ['creators.id'], ondelete='CASCADE'),
    )
    
    # Create indexes
    op.create_index('idx_{table_name}_creator_id', '{table_name}', ['creator_id'])
    op.create_index('idx_{table_name}_created_at', '{table_name}', ['created_at'])
    
    # Enable RLS
    op.execute('ALTER TABLE {table_name} ENABLE ROW LEVEL SECURITY')
    
    # Create RLS policy
    op.execute('''
        CREATE POLICY tenant_isolation_{table_name} ON {table_name}
        FOR ALL TO authenticated_user
        USING (creator_id = current_setting('app.current_creator_id')::UUID)
    ''')

def downgrade() -> None:
    # Drop RLS policy
    op.execute('DROP POLICY IF EXISTS tenant_isolation_{table_name} ON {table_name}')
    
    # Drop table (indexes dropped automatically)
    op.drop_table('{table_name}')
```

## Data Cleanup & Maintenance

### Automated Cleanup Tasks
Implement database maintenance procedures:

```python
from datetime import datetime, timedelta
from sqlalchemy import text
import logging

logger = logging.getLogger(__name__)

class DatabaseMaintenance:
    """Database cleanup and maintenance tasks."""
    
    def __init__(self, database_manager):
        self.db = database_manager
    
    async def cleanup_expired_sessions(self, days_old: int = 7) -> int:
        """Clean up expired user sessions."""
        
        cutoff_date = datetime.utcnow() - timedelta(days=days_old)
        
        async with self.db.get_session() as session:
            result = await session.execute(
                text("""
                    DELETE FROM user_sessions 
                    WHERE expires_at < :cutoff_date 
                    OR (last_activity < :cutoff_date AND is_active = false)
                """),
                {"cutoff_date": cutoff_date}
            )
            
            deleted_count = result.rowcount
            logger.info(f"Cleaned up {deleted_count} expired sessions")
            return deleted_count
    
    async def cleanup_old_audit_logs(self, days_old: int = 90) -> int:
        """Clean up old security audit logs."""
        
        cutoff_date = datetime.utcnow() - timedelta(days=days_old)
        
        async with self.db.get_session() as session:
            result = await session.execute(
                text("DELETE FROM security_audit_logs WHERE created_at < :cutoff_date"),
                {"cutoff_date": cutoff_date}
            )
            
            deleted_count = result.rowcount
            logger.info(f"Cleaned up {deleted_count} old audit logs")
            return deleted_count
    
    async def cleanup_old_api_logs(self, days_old: int = 30) -> int:
        """Clean up old API usage logs."""
        
        cutoff_date = datetime.utcnow() - timedelta(days=days_old)
        
        async with self.db.get_session() as session:
            result = await session.execute(
                text("DELETE FROM api_usage_logs WHERE created_at < :cutoff_date"),
                {"cutoff_date": cutoff_date}
            )
            
            deleted_count = result.rowcount
            logger.info(f"Cleaned up {deleted_count} old API logs")
            return deleted_count
    
    async def update_table_statistics(self) -> None:
        """Update PostgreSQL table statistics for query optimization."""
        
        tables = [
            'creators', 'user_sessions', 'conversations', 'messages',
            'knowledge_documents', 'widget_configs', 'security_audit_logs',
            'api_usage_logs'
        ]
        
        async with self.db.get_session() as session:
            for table in tables:
                await session.execute(text(f"ANALYZE {table}"))
            
            logger.info(f"Updated statistics for {len(tables)} tables")
    
    async def vacuum_tables(self, full: bool = False) -> None:
        """Vacuum tables to reclaim space and update statistics."""
        
        vacuum_cmd = "VACUUM FULL" if full else "VACUUM"
        
        tables = [
            'user_sessions', 'conversations', 'messages',
            'security_audit_logs', 'api_usage_logs'
        ]
        
        async with self.db.get_session() as session:
            for table in tables:
                await session.execute(text(f"{vacuum_cmd} {table}"))
            
            logger.info(f"Vacuumed {len(tables)} tables (full={full})")
    
    async def get_database_stats(self) -> Dict[str, Any]:
        """Get database size and table statistics."""
        
        async with self.db.get_session() as session:
            # Database size
            db_size_result = await session.execute(
                text("SELECT pg_size_pretty(pg_database_size(current_database()))")
            )
            db_size = db_size_result.scalar()
            
            # Table sizes
            table_sizes_result = await session.execute(
                text("""
                    SELECT 
                        schemaname,
                        tablename,
                        pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size,
                        pg_total_relation_size(schemaname||'.'||tablename) as size_bytes
                    FROM pg_tables 
                    WHERE schemaname = 'public'
                    ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
                """)
            )
            table_sizes = [dict(row) for row in table_sizes_result]
            
            # Row counts
            row_counts = {}
            for table in ['creators', 'user_sessions', 'conversations', 'messages', 'knowledge_documents']:
                count_result = await session.execute(text(f"SELECT COUNT(*) FROM {table}"))
                row_counts[table] = count_result.scalar()
            
            return {
                "database_size": db_size,
                "table_sizes": table_sizes,
                "row_counts": row_counts,
                "timestamp": datetime.utcnow().isoformat()
            }
```