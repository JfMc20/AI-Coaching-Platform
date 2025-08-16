"""Add channel service tables

Revision ID: 004_add_channel_service_tables
Revises: 003_autogenerate_creator_hub_tables
Create Date: 2025-01-16 15:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '004_add_channel_service_tables'
down_revision = '003_autogenerate_creator_hub_tables'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create channel_configurations table
    op.create_table('channel_configurations',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('creator_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('channel_type', sa.String(length=50), nullable=False),
        sa.Column('channel_name', sa.String(length=100), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('configuration', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('api_token', sa.Text(), nullable=True),
        sa.Column('webhook_url', sa.String(length=500), nullable=True),
        sa.Column('webhook_secret', sa.String(length=255), nullable=True),
        sa.Column('daily_message_limit', sa.Integer(), nullable=False),
        sa.Column('monthly_message_limit', sa.Integer(), nullable=False),
        sa.Column('current_daily_count', sa.Integer(), nullable=False),
        sa.Column('current_monthly_count', sa.Integer(), nullable=False),
        sa.Column('last_health_check', sa.DateTime(timezone=True), nullable=True),
        sa.Column('health_status', sa.String(length=50), nullable=False),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.CheckConstraint('channel_type IN (\'whatsapp\', \'telegram\', \'web_widget\', \'mobile_app\', \'instagram\', \'facebook\')', name='valid_channel_type'),
        sa.CheckConstraint('health_status IN (\'healthy\', \'warning\', \'error\', \'unknown\')', name='valid_health_status'),
        sa.CheckConstraint('daily_message_limit > 0 AND daily_message_limit <= 10000', name='valid_daily_limit'),
        sa.CheckConstraint('monthly_message_limit > 0 AND monthly_message_limit <= 500000', name='valid_monthly_limit'),
        sa.CheckConstraint('current_daily_count >= 0', name='valid_daily_count'),
        sa.CheckConstraint('current_monthly_count >= 0', name='valid_monthly_count'),
        sa.ForeignKeyConstraint(['creator_id'], ['creators.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for channel_configurations
    op.create_index('idx_channel_configs_creator_id', 'channel_configurations', ['creator_id'])
    op.create_index('idx_channel_configs_type', 'channel_configurations', ['channel_type'])
    op.create_index('idx_channel_configs_active', 'channel_configurations', ['is_active'])
    op.create_index('idx_channel_configs_creator_type', 'channel_configurations', ['creator_id', 'channel_type'])
    
    # Create messages table
    op.create_table('messages',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('creator_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('conversation_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('channel_config_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('message_type', sa.String(length=50), nullable=False),
        sa.Column('direction', sa.String(length=20), nullable=False),
        sa.Column('external_message_id', sa.String(length=255), nullable=True),
        sa.Column('channel_metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('user_identifier', sa.String(length=255), nullable=True),
        sa.Column('user_name', sa.String(length=200), nullable=True),
        sa.Column('user_metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('processing_status', sa.String(length=50), nullable=False),
        sa.Column('ai_processed', sa.Boolean(), nullable=False),
        sa.Column('ai_response', sa.Text(), nullable=True),
        sa.Column('ai_processing_time', sa.Float(), nullable=True),
        sa.Column('delivery_status', sa.String(length=50), nullable=False),
        sa.Column('delivered_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('read_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('error_count', sa.Integer(), nullable=False),
        sa.Column('last_error', sa.Text(), nullable=True),
        sa.Column('sent_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('received_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.CheckConstraint('message_type IN (\'text\', \'image\', \'audio\', \'video\', \'document\', \'location\', \'contact\')', name='valid_message_type'),
        sa.CheckConstraint('direction IN (\'inbound\', \'outbound\')', name='valid_direction'),
        sa.CheckConstraint('processing_status IN (\'pending\', \'processing\', \'completed\', \'failed\', \'skipped\')', name='valid_processing_status'),
        sa.CheckConstraint('delivery_status IN (\'pending\', \'sent\', \'delivered\', \'read\', \'failed\')', name='valid_delivery_status'),
        sa.CheckConstraint('error_count >= 0', name='valid_error_count'),
        sa.CheckConstraint('ai_processing_time IS NULL OR ai_processing_time >= 0', name='valid_processing_time'),
        sa.ForeignKeyConstraint(['channel_config_id'], ['channel_configurations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['conversation_id'], ['conversations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['creator_id'], ['creators.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for messages
    op.create_index('idx_messages_creator_id', 'messages', ['creator_id'])
    op.create_index('idx_messages_conversation_id', 'messages', ['conversation_id'])
    op.create_index('idx_messages_channel_config_id', 'messages', ['channel_config_id'])
    op.create_index('idx_messages_direction', 'messages', ['direction'])
    op.create_index('idx_messages_processing_status', 'messages', ['processing_status'])
    op.create_index('idx_messages_created_at', 'messages', ['created_at'])
    op.create_index('idx_messages_external_id', 'messages', ['external_message_id'])
    op.create_index('idx_messages_user_identifier', 'messages', ['user_identifier'])
    op.create_index('idx_messages_creator_conversation', 'messages', ['creator_id', 'conversation_id'])
    
    # Create webhook_events table
    op.create_table('webhook_events',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('creator_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('channel_config_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('event_type', sa.String(length=100), nullable=False),
        sa.Column('event_source', sa.String(length=50), nullable=False),
        sa.Column('payload', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('headers', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('signature', sa.String(length=500), nullable=True),
        sa.Column('processing_status', sa.String(length=50), nullable=False),
        sa.Column('processed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('message_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('source_ip', sa.String(length=45), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('request_id', sa.String(length=255), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('retry_count', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.CheckConstraint('event_source IN (\'whatsapp\', \'telegram\', \'web_widget\', \'mobile_app\', \'instagram\', \'facebook\')', name='valid_event_source'),
        sa.CheckConstraint('processing_status IN (\'pending\', \'processing\', \'completed\', \'failed\', \'ignored\')', name='valid_webhook_processing_status'),
        sa.CheckConstraint('retry_count >= 0 AND retry_count <= 10', name='valid_retry_count'),
        sa.ForeignKeyConstraint(['channel_config_id'], ['channel_configurations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['creator_id'], ['creators.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['message_id'], ['messages.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for webhook_events
    op.create_index('idx_webhook_events_creator_id', 'webhook_events', ['creator_id'])
    op.create_index('idx_webhook_events_channel_config_id', 'webhook_events', ['channel_config_id'])
    op.create_index('idx_webhook_events_event_type', 'webhook_events', ['event_type'])
    op.create_index('idx_webhook_events_source', 'webhook_events', ['event_source'])
    op.create_index('idx_webhook_events_processing_status', 'webhook_events', ['processing_status'])
    op.create_index('idx_webhook_events_created_at', 'webhook_events', ['created_at'])
    op.create_index('idx_webhook_events_request_id', 'webhook_events', ['request_id'])
    
    # Set default values
    op.execute("ALTER TABLE channel_configurations ALTER COLUMN is_active SET DEFAULT true")
    op.execute("ALTER TABLE channel_configurations ALTER COLUMN configuration SET DEFAULT '{}'")
    op.execute("ALTER TABLE channel_configurations ALTER COLUMN daily_message_limit SET DEFAULT 1000")
    op.execute("ALTER TABLE channel_configurations ALTER COLUMN monthly_message_limit SET DEFAULT 30000")
    op.execute("ALTER TABLE channel_configurations ALTER COLUMN current_daily_count SET DEFAULT 0")
    op.execute("ALTER TABLE channel_configurations ALTER COLUMN current_monthly_count SET DEFAULT 0")
    op.execute("ALTER TABLE channel_configurations ALTER COLUMN health_status SET DEFAULT 'unknown'")
    
    op.execute("ALTER TABLE messages ALTER COLUMN message_type SET DEFAULT 'text'")
    op.execute("ALTER TABLE messages ALTER COLUMN channel_metadata SET DEFAULT '{}'")
    op.execute("ALTER TABLE messages ALTER COLUMN user_metadata SET DEFAULT '{}'")
    op.execute("ALTER TABLE messages ALTER COLUMN processing_status SET DEFAULT 'pending'")
    op.execute("ALTER TABLE messages ALTER COLUMN ai_processed SET DEFAULT false")
    op.execute("ALTER TABLE messages ALTER COLUMN delivery_status SET DEFAULT 'pending'")
    op.execute("ALTER TABLE messages ALTER COLUMN error_count SET DEFAULT 0")
    
    op.execute("ALTER TABLE webhook_events ALTER COLUMN headers SET DEFAULT '{}'")
    op.execute("ALTER TABLE webhook_events ALTER COLUMN processing_status SET DEFAULT 'pending'")
    op.execute("ALTER TABLE webhook_events ALTER COLUMN retry_count SET DEFAULT 0")
    
    # Create updated_at triggers
    op.execute("""
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = CURRENT_TIMESTAMP;
            RETURN NEW;
        END;
        $$ language 'plpgsql';
    """)
    
    op.execute("""
        CREATE TRIGGER update_channel_configurations_updated_at 
        BEFORE UPDATE ON channel_configurations 
        FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    """)
    
    op.execute("""
        CREATE TRIGGER update_messages_updated_at 
        BEFORE UPDATE ON messages 
        FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    """)
    
    op.execute("""
        CREATE TRIGGER update_webhook_events_updated_at 
        BEFORE UPDATE ON webhook_events 
        FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    """)
    
    # Create RLS policies for multi-tenant isolation
    
    # Enable RLS
    op.execute("ALTER TABLE channel_configurations ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE messages ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE webhook_events ENABLE ROW LEVEL SECURITY")
    
    # Create RLS policies
    op.execute("""
        CREATE POLICY channel_configurations_tenant_isolation 
        ON channel_configurations 
        USING (creator_id = current_setting('app.current_creator_id')::uuid)
    """)
    
    op.execute("""
        CREATE POLICY messages_tenant_isolation 
        ON messages 
        USING (creator_id = current_setting('app.current_creator_id')::uuid)
    """)
    
    op.execute("""
        CREATE POLICY webhook_events_tenant_isolation 
        ON webhook_events 
        USING (creator_id = current_setting('app.current_creator_id')::uuid)
    """)


def downgrade() -> None:
    # Drop RLS policies
    op.execute("DROP POLICY IF EXISTS webhook_events_tenant_isolation ON webhook_events")
    op.execute("DROP POLICY IF EXISTS messages_tenant_isolation ON messages")
    op.execute("DROP POLICY IF EXISTS channel_configurations_tenant_isolation ON channel_configurations")
    
    # Disable RLS
    op.execute("ALTER TABLE webhook_events DISABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE messages DISABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE channel_configurations DISABLE ROW LEVEL SECURITY")
    
    # Drop triggers
    op.execute("DROP TRIGGER IF EXISTS update_webhook_events_updated_at ON webhook_events")
    op.execute("DROP TRIGGER IF EXISTS update_messages_updated_at ON messages")
    op.execute("DROP TRIGGER IF EXISTS update_channel_configurations_updated_at ON channel_configurations")
    
    # Drop indexes
    op.drop_index('idx_webhook_events_request_id', table_name='webhook_events')
    op.drop_index('idx_webhook_events_created_at', table_name='webhook_events')
    op.drop_index('idx_webhook_events_processing_status', table_name='webhook_events')
    op.drop_index('idx_webhook_events_source', table_name='webhook_events')
    op.drop_index('idx_webhook_events_event_type', table_name='webhook_events')
    op.drop_index('idx_webhook_events_channel_config_id', table_name='webhook_events')
    op.drop_index('idx_webhook_events_creator_id', table_name='webhook_events')
    
    op.drop_index('idx_messages_creator_conversation', table_name='messages')
    op.drop_index('idx_messages_user_identifier', table_name='messages')
    op.drop_index('idx_messages_external_id', table_name='messages')
    op.drop_index('idx_messages_created_at', table_name='messages')
    op.drop_index('idx_messages_processing_status', table_name='messages')
    op.drop_index('idx_messages_direction', table_name='messages')
    op.drop_index('idx_messages_channel_config_id', table_name='messages')
    op.drop_index('idx_messages_conversation_id', table_name='messages')
    op.drop_index('idx_messages_creator_id', table_name='messages')
    
    op.drop_index('idx_channel_configs_creator_type', table_name='channel_configurations')
    op.drop_index('idx_channel_configs_active', table_name='channel_configurations')
    op.drop_index('idx_channel_configs_type', table_name='channel_configurations')
    op.drop_index('idx_channel_configs_creator_id', table_name='channel_configurations')
    
    # Drop tables
    op.drop_table('webhook_events')
    op.drop_table('messages')
    op.drop_table('channel_configurations')