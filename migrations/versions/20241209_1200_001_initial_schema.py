"""Initial multi-tenant schema with RLS

Revision ID: 001
Revises: 
Create Date: 2024-12-09 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create initial multi-tenant schema with Row Level Security"""
    
    # Enable UUID extension
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
    
    # Enable Row Level Security globally
    op.execute('ALTER DATABASE mvp_coaching SET row_security = on')
    
    # Create schemas
    op.execute('CREATE SCHEMA IF NOT EXISTS auth')
    op.execute('CREATE SCHEMA IF NOT EXISTS content')
    op.execute('CREATE SCHEMA IF NOT EXISTS conversations')
    op.execute('CREATE SCHEMA IF NOT EXISTS analytics')
    
    # Grant permissions on schemas
    op.execute('GRANT USAGE ON SCHEMA auth TO postgres')
    op.execute('GRANT USAGE ON SCHEMA content TO postgres')
    op.execute('GRANT USAGE ON SCHEMA conversations TO postgres')
    op.execute('GRANT USAGE ON SCHEMA analytics TO postgres')
    
    # Create creators table (main tenant table)
    op.create_table('creators',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('full_name', sa.String(length=100), nullable=False),
        sa.Column('company_name', sa.String(length=100), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('subscription_tier', sa.String(length=50), nullable=False, server_default=sa.text("'free'")),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email'),
        schema='auth'
    )
    
    # Create indexes for creators
    op.create_index('idx_creators_email', 'creators', ['email'], unique=False, schema='auth')
    
    # Enable RLS on creators table
    op.execute('ALTER TABLE auth.creators ENABLE ROW LEVEL SECURITY')
    
    # Create RLS policy for creators (creators can only see their own data)
    op.execute('''
        CREATE POLICY creator_isolation_policy ON auth.creators
            FOR ALL
            TO postgres
            USING (id = current_setting('app.current_creator_id', true)::uuid)
    ''')
    
    # Create user_sessions table
    op.create_table('user_sessions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('session_id', sa.String(length=255), nullable=False),
        sa.Column('creator_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('channel', sa.String(length=50), nullable=False, server_default=sa.text("'web_widget'")),
        sa.Column('metadata', postgresql.JSON(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'")),
        sa.Column('last_activity', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['creator_id'], ['auth.creators.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('session_id'),
        schema='auth'
    )
    
    # Create indexes for user_sessions
    op.create_index('idx_user_sessions_creator_id', 'user_sessions', ['creator_id'], unique=False, schema='auth')
    op.create_index('idx_user_sessions_session_id', 'user_sessions', ['session_id'], unique=False, schema='auth')
    
    # Enable RLS on user_sessions
    op.execute('ALTER TABLE auth.user_sessions ENABLE ROW LEVEL SECURITY')
    
    # Create RLS policy for user_sessions
    op.execute('''
        CREATE POLICY user_sessions_isolation_policy ON auth.user_sessions
            FOR ALL
            TO postgres
            USING (creator_id = current_setting('app.current_creator_id', true)::uuid)
    ''')
    
    # Create knowledge_documents table
    op.create_table('knowledge_documents',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('creator_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('document_id', sa.String(length=255), nullable=False),
        sa.Column('filename', sa.String(length=255), nullable=False),
        sa.Column('file_path', sa.String(length=500), nullable=True),
        sa.Column('file_size', sa.BigInteger(), nullable=True),
        sa.Column('mime_type', sa.String(length=100), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False, server_default=sa.text("'pending'")),
        sa.Column('total_chunks', sa.Integer(), nullable=False, server_default=sa.text('0')),
        sa.Column('processing_time_seconds', sa.Float(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('metadata', postgresql.JSON(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'")),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.CheckConstraint('total_chunks >= 0', name='check_total_chunks_non_negative'),
        sa.CheckConstraint('file_size >= 0', name='check_file_size_non_negative'),
        sa.CheckConstraint("status IN ('pending', 'processing', 'completed', 'failed')", name='check_valid_status'),
        sa.ForeignKeyConstraint(['creator_id'], ['auth.creators.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        schema='content'
    )
    
    # Create indexes for knowledge_documents
    op.create_index('idx_knowledge_documents_creator_id', 'knowledge_documents', ['creator_id'], unique=False, schema='content')
    op.create_index('idx_knowledge_documents_status', 'knowledge_documents', ['creator_id', 'status'], unique=False, schema='content')
    op.create_index('idx_knowledge_documents_document_id', 'knowledge_documents', ['creator_id', 'document_id'], unique=False, schema='content')
    
    # Enable RLS on knowledge_documents
    op.execute('ALTER TABLE content.knowledge_documents ENABLE ROW LEVEL SECURITY')
    
    # Create RLS policy for knowledge_documents
    op.execute('''
        CREATE POLICY knowledge_documents_isolation_policy ON content.knowledge_documents
            FOR ALL
            TO postgres
            USING (creator_id = current_setting('app.current_creator_id', true)::uuid)
    ''')
    
    # Create widget_configs table
    op.create_table('widget_configs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('creator_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('widget_id', sa.String(length=255), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('theme', postgresql.JSON(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'")),
        sa.Column('behavior', postgresql.JSON(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'")),
        sa.Column('allowed_domains', postgresql.ARRAY(sa.String()), nullable=False, server_default=sa.text("'{}'")),
        sa.Column('rate_limit_per_minute', sa.Integer(), nullable=False, server_default=sa.text('10')),
        sa.Column('embed_code', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.CheckConstraint('rate_limit_per_minute > 0', name='check_rate_limit_positive'),
        sa.ForeignKeyConstraint(['creator_id'], ['auth.creators.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        schema='content'
    )
    
    # Create indexes for widget_configs
    op.create_index('idx_widget_configs_creator_id', 'widget_configs', ['creator_id'], unique=False, schema='content')
    op.create_index('idx_widget_configs_widget_id', 'widget_configs', ['creator_id', 'widget_id'], unique=False, schema='content')
    
    # Enable RLS on widget_configs
    op.execute('ALTER TABLE content.widget_configs ENABLE ROW LEVEL SECURITY')
    
    # Create RLS policy for widget_configs
    op.execute('''
        CREATE POLICY widget_configs_isolation_policy ON content.widget_configs
            FOR ALL
            TO postgres
            USING (creator_id = current_setting('app.current_creator_id', true)::uuid)
    ''')
    
    # Create conversations table
    op.create_table('conversations',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('creator_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('session_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=True),
        sa.Column('channel', sa.String(length=50), nullable=False, server_default=sa.text("'web_widget'")),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('message_count', sa.Integer(), nullable=False, server_default=sa.text('0')),
        sa.Column('last_message_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('metadata', postgresql.JSON(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'")),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.CheckConstraint('message_count >= 0', name='check_message_count_non_negative'),
        sa.ForeignKeyConstraint(['creator_id'], ['auth.creators.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['session_id'], ['auth.user_sessions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        schema='conversations'
    )
    
    # Create indexes for conversations
    op.create_index('idx_conversations_creator_id', 'conversations', ['creator_id'], unique=False, schema='conversations')
    op.create_index('idx_conversations_session_id', 'conversations', ['session_id'], unique=False, schema='conversations')
    op.create_index('idx_conversations_created_at', 'conversations', ['creator_id', 'created_at'], unique=False, schema='conversations')
    
    # Enable RLS on conversations
    op.execute('ALTER TABLE conversations.conversations ENABLE ROW LEVEL SECURITY')
    
    # Create RLS policy for conversations
    op.execute('''
        CREATE POLICY conversations_isolation_policy ON conversations.conversations
            FOR ALL
            TO postgres
            USING (creator_id = current_setting('app.current_creator_id', true)::uuid)
    ''')
    
    # Create messages table
    op.create_table('messages',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('creator_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('conversation_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('role', sa.String(length=20), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('metadata', postgresql.JSON(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'")),
        sa.Column('processing_time_ms', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.CheckConstraint("role IN ('user', 'assistant', 'system')", name='check_valid_message_role'),
        sa.CheckConstraint('processing_time_ms >= 0', name='check_processing_time_non_negative'),
        sa.ForeignKeyConstraint(['conversation_id'], ['conversations.conversations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        schema='conversations'
    )
    
    # Create indexes for messages
    op.create_index('idx_messages_creator_id', 'messages', ['creator_id'], unique=False, schema='conversations')
    op.create_index('idx_messages_conversation_id', 'messages', ['conversation_id'], unique=False, schema='conversations')
    op.create_index('idx_messages_created_at', 'messages', ['creator_id', 'created_at'], unique=False, schema='conversations')
    
    # Enable RLS on messages
    op.execute('ALTER TABLE conversations.messages ENABLE ROW LEVEL SECURITY')
    
    # Create RLS policy for messages
    op.execute('''
        CREATE POLICY messages_isolation_policy ON conversations.messages
            FOR ALL
            TO postgres
            USING (creator_id = current_setting('app.current_creator_id', true)::uuid)
    ''')
    
    # Create function to update updated_at timestamp
    op.execute('''
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = CURRENT_TIMESTAMP;
            RETURN NEW;
        END;
        $$ language 'plpgsql'
    ''')
    
    # Create triggers for updated_at
    op.execute('CREATE TRIGGER update_creators_updated_at BEFORE UPDATE ON auth.creators FOR EACH ROW EXECUTE FUNCTION update_updated_at_column()')
    op.execute('CREATE TRIGGER update_user_sessions_updated_at BEFORE UPDATE ON auth.user_sessions FOR EACH ROW EXECUTE FUNCTION update_updated_at_column()')
    op.execute('CREATE TRIGGER update_knowledge_documents_updated_at BEFORE UPDATE ON content.knowledge_documents FOR EACH ROW EXECUTE FUNCTION update_updated_at_column()')
    op.execute('CREATE TRIGGER update_widget_configs_updated_at BEFORE UPDATE ON content.widget_configs FOR EACH ROW EXECUTE FUNCTION update_updated_at_column()')
    op.execute('CREATE TRIGGER update_conversations_updated_at BEFORE UPDATE ON conversations.conversations FOR EACH ROW EXECUTE FUNCTION update_updated_at_column()')


def downgrade() -> None:
    """Drop all tables and schemas"""
    
    # Drop triggers
    op.execute('DROP TRIGGER IF EXISTS update_creators_updated_at ON auth.creators')
    op.execute('DROP TRIGGER IF EXISTS update_user_sessions_updated_at ON auth.user_sessions')
    op.execute('DROP TRIGGER IF EXISTS update_knowledge_documents_updated_at ON content.knowledge_documents')
    op.execute('DROP TRIGGER IF EXISTS update_widget_configs_updated_at ON content.widget_configs')
    op.execute('DROP TRIGGER IF EXISTS update_conversations_updated_at ON conversations.conversations')
    
    # Drop function
    op.execute('DROP FUNCTION IF EXISTS update_updated_at_column()')
    
    # Drop tables (in reverse order due to foreign keys)
    op.drop_table('messages', schema='conversations')
    op.drop_table('conversations', schema='conversations')
    op.drop_table('widget_configs', schema='content')
    op.drop_table('knowledge_documents', schema='content')
    op.drop_table('user_sessions', schema='auth')
    op.drop_table('creators', schema='auth')
    
    # Drop schemas
    op.execute('DROP SCHEMA IF EXISTS analytics CASCADE')
    op.execute('DROP SCHEMA IF EXISTS conversations CASCADE')
    op.execute('DROP SCHEMA IF EXISTS content CASCADE')
    op.execute('DROP SCHEMA IF EXISTS auth CASCADE')
    
    # Drop extension
    op.execute('DROP EXTENSION IF EXISTS "uuid-ossp"')