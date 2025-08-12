"""Initial auth tables with multi-tenant RLS

Revision ID: 001
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create creators table
    op.create_table('creators',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('full_name', sa.String(length=100), nullable=False),
        sa.Column('company_name', sa.String(length=100), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('is_verified', sa.Boolean(), nullable=False),
        sa.Column('subscription_tier', sa.String(length=50), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('last_login_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('password_changed_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('failed_login_attempts', sa.Integer(), nullable=False),
        sa.Column('locked_until', sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("email ~ '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,}$'", name='valid_email'),
        sa.CheckConstraint("subscription_tier IN ('free', 'pro', 'enterprise')", name='valid_subscription_tier'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email')
    )
    op.create_index('idx_creators_active', 'creators', ['is_active'], unique=False)
    op.create_index('idx_creators_email', 'creators', ['email'], unique=False)
    op.create_index('idx_creators_subscription', 'creators', ['subscription_tier'], unique=False)

    # Create refresh_tokens table
    op.create_table('refresh_tokens',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('token_hash', sa.String(length=255), nullable=False),
        sa.Column('creator_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('family_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('used_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('revoked_at', sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint('expires_at > created_at', name='valid_refresh_token_expiration'),
        sa.Column('client_ip', sa.String(length=45), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(['creator_id'], ['creators.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('token_hash')
    )
    op.create_index('idx_refresh_tokens_active', 'refresh_tokens', ['is_active'], unique=False)
    op.create_index('idx_refresh_tokens_creator', 'refresh_tokens', ['creator_id'], unique=False)
    op.create_index('idx_refresh_tokens_expires', 'refresh_tokens', ['expires_at'], unique=False)
    op.create_index('idx_refresh_tokens_family', 'refresh_tokens', ['family_id'], unique=False)

    # Create user_sessions table
    op.create_table('user_sessions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('session_id', sa.String(length=255), nullable=False),
        sa.Column('creator_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('channel', sa.String(length=50), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('last_activity', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('session_metadata', sa.JSON(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('client_ip', sa.String(length=45), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('referrer', sa.Text(), nullable=True),
        sa.CheckConstraint("channel IN ('web_widget', 'whatsapp', 'telegram', 'mobile_app')", name='valid_channel'),
        sa.ForeignKeyConstraint(['creator_id'], ['creators.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('session_id')
    )
    op.create_index('idx_user_sessions_active', 'user_sessions', ['is_active'], unique=False)
    op.create_index('idx_user_sessions_channel', 'user_sessions', ['channel'], unique=False)
    op.create_index('idx_user_sessions_creator', 'user_sessions', ['creator_id'], unique=False)
    op.create_index('idx_user_sessions_last_activity', 'user_sessions', ['last_activity'], unique=False)
    op.create_index('idx_user_sessions_session_id', 'user_sessions', ['session_id'], unique=False)

    # Create password_reset_tokens table
    op.create_table('password_reset_tokens',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('token_hash', sa.String(length=255), nullable=False),
        sa.Column('creator_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('used_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('client_ip', sa.String(length=45), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.CheckConstraint('expires_at > created_at', name='valid_reset_token_expiration'),
        sa.ForeignKeyConstraint(['creator_id'], ['creators.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('token_hash')
    )
    op.create_index('idx_password_reset_tokens_active', 'password_reset_tokens', ['is_active'], unique=False)
    op.create_index('idx_password_reset_tokens_creator', 'password_reset_tokens', ['creator_id'], unique=False)
    op.create_index('idx_password_reset_tokens_expires', 'password_reset_tokens', ['expires_at'], unique=False)

    # Create jwt_blacklist table
    op.create_table('jwt_blacklist',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('jti', sa.String(length=255), nullable=False),
        sa.Column('creator_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('reason', sa.String(length=100), nullable=False),
        sa.CheckConstraint("reason IN ('logout', 'security', 'expired', 'revoked')", name='valid_blacklist_reason'),
        sa.CheckConstraint('expires_at > created_at', name='valid_token_expiration'),
        sa.ForeignKeyConstraint(['creator_id'], ['creators.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('jti')
    )
    op.create_index('idx_jwt_blacklist_creator', 'jwt_blacklist', ['creator_id'], unique=False)
    op.create_index('idx_jwt_blacklist_expires', 'jwt_blacklist', ['expires_at'], unique=False)
    op.create_index('idx_jwt_blacklist_jti', 'jwt_blacklist', ['jti'], unique=False)

    # Create audit_logs table
    op.create_table('audit_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('creator_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('event_type', sa.String(length=50), nullable=False),
        sa.Column('event_category', sa.String(length=50), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('event_metadata', sa.JSON(), nullable=False),
        sa.Column('client_ip', sa.String(length=45), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('request_id', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('severity', sa.String(length=20), nullable=False),
        sa.CheckConstraint("event_category IN ('auth', 'data', 'admin', 'security', 'system')", name='valid_event_category'),
        sa.CheckConstraint("severity IN ('debug', 'info', 'warning', 'error', 'critical')", name='valid_severity'),
        sa.ForeignKeyConstraint(['creator_id'], ['creators.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_audit_logs_category', 'audit_logs', ['event_category'], unique=False)
    op.create_index('idx_audit_logs_created_at', 'audit_logs', ['created_at'], unique=False)
    op.create_index('idx_audit_logs_creator', 'audit_logs', ['creator_id'], unique=False)
    op.create_index('idx_audit_logs_event_type', 'audit_logs', ['event_type'], unique=False)
    op.create_index('idx_audit_logs_severity', 'audit_logs', ['severity'], unique=False)

    # Setup Row Level Security policies
    op.execute("""
        -- Enable RLS on refresh_tokens
        ALTER TABLE refresh_tokens ENABLE ROW LEVEL SECURITY;
        
        -- Create policy for refresh_tokens
        CREATE POLICY tenant_isolation ON refresh_tokens
            FOR ALL TO authenticated_user
            USING (creator_id = current_setting('app.current_creator_id')::uuid);
    """)
    
    op.execute("""
        -- Enable RLS on user_sessions
        ALTER TABLE user_sessions ENABLE ROW LEVEL SECURITY;
        
        -- Create policy for user_sessions
        CREATE POLICY tenant_isolation ON user_sessions
            FOR ALL TO authenticated_user
            USING (creator_id = current_setting('app.current_creator_id')::uuid);
    """)
    
    op.execute("""
        -- Enable RLS on password_reset_tokens
        ALTER TABLE password_reset_tokens ENABLE ROW LEVEL SECURITY;
        
        -- Create policy for password_reset_tokens
        CREATE POLICY tenant_isolation ON password_reset_tokens
            FOR ALL TO authenticated_user
            USING (creator_id = current_setting('app.current_creator_id')::uuid);
    """)
    
    op.execute("""
        -- Enable RLS on audit_logs
        ALTER TABLE audit_logs ENABLE ROW LEVEL SECURITY;
        
        -- Create policy for audit_logs (creators can only see their own logs)
        CREATE POLICY tenant_isolation ON audit_logs
            FOR SELECT TO authenticated_user
            USING (
                creator_id = current_setting('app.current_creator_id')::uuid
                OR current_setting('app.current_creator_id') = 'system'
            );
    """)


def downgrade() -> None:
    # Drop RLS policies first
    op.execute("DROP POLICY IF EXISTS tenant_isolation ON audit_logs;")
    op.execute("DROP POLICY IF EXISTS tenant_isolation ON password_reset_tokens;")
    op.execute("DROP POLICY IF EXISTS tenant_isolation ON user_sessions;")
    op.execute("DROP POLICY IF EXISTS tenant_isolation ON refresh_tokens;")
    
    # Drop tables in reverse order
    op.drop_table('audit_logs')
    op.drop_table('jwt_blacklist')
    op.drop_table('password_reset_tokens')
    op.drop_table('user_sessions')
    op.drop_table('refresh_tokens')
    op.drop_table('creators')