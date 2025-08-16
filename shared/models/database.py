"""
Database models for the MVP Coaching AI Platform
SQLAlchemy models with multi-tenant Row Level Security support
"""

import uuid
from sqlalchemy import (
    Column, String, Boolean, DateTime, Text, JSON, Integer, Float,
    ForeignKey, Index, CheckConstraint
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

Base = declarative_base()


class Creator(Base):
    """Creator/Tenant model with multi-tenant isolation"""
    __tablename__ = "creators"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Authentication fields
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(100), nullable=False)
    company_name = Column(String(100), nullable=True)
    
    # Account status
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    subscription_tier = Column(String(50), default="free", nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    last_login_at = Column(DateTime(timezone=True), nullable=True)
    
    # Password security
    password_changed_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    failed_login_attempts = Column(Integer, default=0, nullable=False)
    locked_until = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    refresh_tokens = relationship("RefreshToken", back_populates="creator", cascade="all, delete-orphan")
    user_sessions = relationship("UserSession", back_populates="creator", cascade="all, delete-orphan")
    password_reset_tokens = relationship("PasswordResetToken", back_populates="creator", cascade="all, delete-orphan")
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_creators_email', 'email'),
        Index('idx_creators_active', 'is_active'),
        Index('idx_creators_subscription', 'subscription_tier'),
        CheckConstraint(r"email ~ '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$'", name='valid_email'),
        CheckConstraint('subscription_tier IN (\'free\', \'pro\', \'enterprise\')', name='valid_subscription_tier'),
    )


class RefreshToken(Base):
    """Refresh tokens for JWT authentication with rotation support"""
    __tablename__ = "refresh_tokens"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Token data
    token_hash = Column(String(255), unique=True, nullable=False, index=True)
    creator_id = Column(UUID(as_uuid=True), ForeignKey("creators.id", ondelete="CASCADE"), nullable=False)
    
    # Token family for rotation tracking
    family_id = Column(UUID(as_uuid=True), default=uuid.uuid4, nullable=False, index=True)
    
    # Token lifecycle
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    used_at = Column(DateTime(timezone=True), nullable=True)
    revoked_at = Column(DateTime(timezone=True), nullable=True)
    
    # Security tracking
    client_ip = Column(String(45), nullable=True)  # IPv6 support
    user_agent = Column(Text, nullable=True)
    
    # Status flags
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Relationships
    creator = relationship("Creator", back_populates="refresh_tokens")
    
    # Row Level Security - all queries filtered by creator_id
    __table_args__ = (
        Index('idx_refresh_tokens_creator', 'creator_id'),
        Index('idx_refresh_tokens_family', 'family_id'),
        Index('idx_refresh_tokens_expires', 'expires_at'),
        Index('idx_refresh_tokens_active', 'is_active'),
        CheckConstraint('expires_at > created_at', name='valid_refresh_token_expiration'),
        # RLS Policy will be: creator_id = current_setting('app.current_creator_id')::uuid
    )


class UserSession(Base):
    """End-user sessions for anonymous widget interactions"""
    __tablename__ = "user_sessions"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Session identification
    session_id = Column(String(255), unique=True, nullable=False, index=True)
    creator_id = Column(UUID(as_uuid=True), ForeignKey("creators.id", ondelete="CASCADE"), nullable=False)
    
    # Channel information
    channel = Column(String(50), default="web_widget", nullable=False)
    
    # Session lifecycle
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    last_activity = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    
    # Session data
    session_metadata = Column(JSON, default=dict, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Client information
    client_ip = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    referrer = Column(Text, nullable=True)
    
    # Relationships
    creator = relationship("Creator", back_populates="user_sessions")
    
    # Row Level Security - all queries filtered by creator_id
    __table_args__ = (
        Index('idx_user_sessions_creator', 'creator_id'),
        Index('idx_user_sessions_session_id', 'session_id'),
        Index('idx_user_sessions_channel', 'channel'),
        Index('idx_user_sessions_active', 'is_active'),
        Index('idx_user_sessions_last_activity', 'last_activity'),
        CheckConstraint('channel IN (\'web_widget\', \'whatsapp\', \'telegram\', \'mobile_app\')', name='valid_channel'),
        # RLS Policy will be: creator_id = current_setting('app.current_creator_id')::uuid
    )


class PasswordResetToken(Base):
    """Password reset tokens with short expiration"""
    __tablename__ = "password_reset_tokens"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Token data
    token_hash = Column(String(255), unique=True, nullable=False, index=True)
    creator_id = Column(UUID(as_uuid=True), ForeignKey("creators.id", ondelete="CASCADE"), nullable=False)
    
    # Token lifecycle (15 minutes expiration)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    used_at = Column(DateTime(timezone=True), nullable=True)
    
    # Security tracking
    client_ip = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Relationships
    creator = relationship("Creator", back_populates="password_reset_tokens")
    
    # Indexes
    __table_args__ = (
        Index('idx_password_reset_tokens_creator', 'creator_id'),
        Index('idx_password_reset_tokens_expires', 'expires_at'),
        Index('idx_password_reset_tokens_active', 'is_active'),
        CheckConstraint('expires_at > created_at', name='valid_reset_token_expiration'),
        # RLS Policy will be: creator_id = current_setting('app.current_creator_id')::uuid
    )


class JWTBlacklist(Base):
    """Blacklisted JWT tokens (JTI tracking)"""
    __tablename__ = "jwt_blacklist"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # JWT identification
    jti = Column(String(255), unique=True, nullable=False, index=True)  # JWT ID
    creator_id = Column(UUID(as_uuid=True), ForeignKey("creators.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Token lifecycle
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)  # TTL for cleanup
    
    # Blacklist reason
    reason = Column(String(100), nullable=False)  # 'logout', 'security', 'expired'
    
    # Indexes for fast lookup
    __table_args__ = (
        Index('idx_jwt_blacklist_jti', 'jti'),
        Index('idx_jwt_blacklist_creator', 'creator_id'),
        Index('idx_jwt_blacklist_expires', 'expires_at'),
        CheckConstraint('reason IN (\'logout\', \'security\', \'expired\', \'revoked\')', name='valid_blacklist_reason'),
        CheckConstraint('expires_at > created_at', name='valid_token_expiration'),
    )


class AuditLog(Base):
    """Audit log for security events"""
    __tablename__ = "audit_logs"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Event identification
    creator_id = Column(UUID(as_uuid=True), ForeignKey("creators.id", ondelete="SET NULL"), nullable=True, index=True)  # Nullable for system events
    event_type = Column(String(50), nullable=False, index=True)
    event_category = Column(String(50), nullable=False, index=True)
    
    # Event details
    description = Column(Text, nullable=False)
    event_metadata = Column(JSON, default=dict, nullable=False)
    
    # Request context
    client_ip = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    request_id = Column(String(255), nullable=True, index=True)
    
    # Timestamp
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Severity level
    severity = Column(String(20), default="info", nullable=False)
    
    # Indexes for querying
    __table_args__ = (
        Index('idx_audit_logs_creator', 'creator_id'),
        Index('idx_audit_logs_event_type', 'event_type'),
        Index('idx_audit_logs_category', 'event_category'),
        Index('idx_audit_logs_created_at', 'created_at'),
        Index('idx_audit_logs_severity', 'severity'),
        CheckConstraint('event_category IN (\'auth\', \'data\', \'admin\', \'security\', \'system\')', name='valid_event_category'),
        CheckConstraint('severity IN (\'debug\', \'info\', \'warning\', \'error\', \'critical\')', name='valid_severity'),
    )


# =====================================================
# Creator Hub Service Models
# =====================================================

class Document(Base):
    """Document model for Creator Hub knowledge base"""
    __tablename__ = "documents"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Tenant isolation
    creator_id = Column(UUID(as_uuid=True), ForeignKey("creators.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Document metadata
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    document_metadata = Column(JSONB, default=dict, nullable=False)
    
    # Processing status
    status = Column(String(50), default="uploading", nullable=False)
    chunk_count = Column(Integer, default=0, nullable=False)
    processing_time = Column(Float, nullable=True)
    error_message = Column(Text, nullable=True)
    
    # Storage information
    file_path = Column(String(500), nullable=True)
    embeddings_stored = Column(Boolean, default=False, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    creator = relationship("Creator", backref="documents")
    
    # Indexes and constraints
    __table_args__ = (
        Index('idx_documents_creator_id', 'creator_id'),
        Index('idx_documents_status', 'status'),
        Index('idx_documents_created_at', 'created_at'),
        Index('idx_documents_creator_status', 'creator_id', 'status'),
        CheckConstraint('status IN (\'uploading\', \'processing\', \'completed\', \'failed\', \'archived\')', name='valid_document_status'),
        CheckConstraint('chunk_count >= 0', name='valid_chunk_count'),
        CheckConstraint('processing_time IS NULL OR processing_time >= 0', name='valid_processing_time'),
        # RLS: creator_id = current_setting('app.current_creator_id')::uuid
    )


class WidgetConfiguration(Base):
    """Widget configuration for Creator Hub"""
    __tablename__ = "widget_configurations"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Tenant isolation
    creator_id = Column(UUID(as_uuid=True), ForeignKey("creators.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Configuration metadata
    name = Column(String(100), nullable=False)
    description = Column(String(500), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Widget settings (JSON)
    settings = Column(JSONB, default=dict, nullable=False)
    
    # Behavior settings
    welcome_message = Column(Text, default="Hello! How can I help you today?", nullable=False)
    placeholder_text = Column(String(200), default="Type your message...", nullable=False)
    enable_file_upload = Column(Boolean, default=True, nullable=False)
    enable_voice_input = Column(Boolean, default=False, nullable=False)
    
    # Security and integration
    allowed_domains = Column(JSONB, default=list, nullable=False)
    rate_limit_messages = Column(Integer, default=10, nullable=False)
    track_analytics = Column(Boolean, default=True, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    creator = relationship("Creator", backref="widget_configurations")
    
    # Indexes and constraints
    __table_args__ = (
        Index('idx_widget_configs_creator_id', 'creator_id'),
        Index('idx_widget_configs_active', 'is_active'),
        CheckConstraint('rate_limit_messages > 0 AND rate_limit_messages <= 100', name='valid_rate_limit'),
        # RLS: creator_id = current_setting('app.current_creator_id')::uuid
    )


class Conversation(Base):
    """Conversation model for Creator Hub analytics"""
    __tablename__ = "conversations"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Tenant isolation
    creator_id = Column(UUID(as_uuid=True), ForeignKey("creators.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # User information (nullable for anonymous)
    user_id = Column(UUID(as_uuid=True), nullable=True)
    
    # Conversation metadata
    title = Column(String(200), nullable=True)
    status = Column(String(50), default="active", nullable=False)
    message_count = Column(Integer, default=0, nullable=False)
    satisfaction_rating = Column(Integer, nullable=True)
    
    # Categorization
    tags = Column(JSONB, default=list, nullable=False)
    conversation_metadata = Column(JSONB, default=dict, nullable=False)
    
    # Timestamps
    last_message_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    creator = relationship("Creator", backref="conversations")
    
    # Indexes and constraints
    __table_args__ = (
        Index('idx_conversations_creator_id', 'creator_id'),
        Index('idx_conversations_status', 'status'),
        Index('idx_conversations_created_at', 'created_at'),
        Index('idx_conversations_last_message', 'last_message_at'),
        CheckConstraint('status IN (\'active\', \'paused\', \'completed\', \'archived\')', name='valid_conversation_status'),
        CheckConstraint('satisfaction_rating IS NULL OR (satisfaction_rating >= 1 AND satisfaction_rating <= 5)', name='valid_rating'),
        CheckConstraint('message_count >= 0', name='valid_message_count'),
        # RLS: creator_id = current_setting('app.current_creator_id')::uuid
    )


# =====================================================
# Channel Service Models
# =====================================================

class ChannelConfiguration(Base):
    """Channel configuration for multi-channel support"""
    __tablename__ = "channel_configurations"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Tenant isolation
    creator_id = Column(UUID(as_uuid=True), ForeignKey("creators.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Channel identification
    channel_type = Column(String(50), nullable=False)  # whatsapp, telegram, web_widget, mobile_app
    channel_name = Column(String(100), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Channel-specific configuration (JSON)
    configuration = Column(JSONB, default=dict, nullable=False)
    
    # Authentication and connectivity
    api_token = Column(Text, nullable=True)  # Encrypted channel API tokens
    webhook_url = Column(String(500), nullable=True)
    webhook_secret = Column(String(255), nullable=True)
    
    # Rate limiting and quotas
    daily_message_limit = Column(Integer, default=1000, nullable=False)
    monthly_message_limit = Column(Integer, default=30000, nullable=False)
    current_daily_count = Column(Integer, default=0, nullable=False)
    current_monthly_count = Column(Integer, default=0, nullable=False)
    
    # Status and health
    last_health_check = Column(DateTime(timezone=True), nullable=True)
    health_status = Column(String(50), default="unknown", nullable=False)
    error_message = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    creator = relationship("Creator", backref="channel_configurations")
    
    # Indexes and constraints
    __table_args__ = (
        Index('idx_channel_configs_creator_id', 'creator_id'),
        Index('idx_channel_configs_type', 'channel_type'),
        Index('idx_channel_configs_active', 'is_active'),
        Index('idx_channel_configs_creator_type', 'creator_id', 'channel_type'),
        CheckConstraint('channel_type IN (\'whatsapp\', \'telegram\', \'web_widget\', \'mobile_app\', \'instagram\', \'facebook\')', name='valid_channel_type'),
        CheckConstraint('health_status IN (\'healthy\', \'warning\', \'error\', \'unknown\')', name='valid_health_status'),
        CheckConstraint('daily_message_limit > 0 AND daily_message_limit <= 10000', name='valid_daily_limit'),
        CheckConstraint('monthly_message_limit > 0 AND monthly_message_limit <= 500000', name='valid_monthly_limit'),
        CheckConstraint('current_daily_count >= 0', name='valid_daily_count'),
        CheckConstraint('current_monthly_count >= 0', name='valid_monthly_count'),
        # RLS: creator_id = current_setting('app.current_creator_id')::uuid
    )


class Message(Base):
    """Message model for cross-channel messaging"""
    __tablename__ = "messages"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Tenant isolation
    creator_id = Column(UUID(as_uuid=True), ForeignKey("creators.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Message identification
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, index=True)
    channel_config_id = Column(UUID(as_uuid=True), ForeignKey("channel_configurations.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Message content
    content = Column(Text, nullable=False)
    message_type = Column(String(50), default="text", nullable=False)
    direction = Column(String(20), nullable=False)  # inbound, outbound
    
    # Channel-specific data
    external_message_id = Column(String(255), nullable=True, index=True)  # Channel's message ID
    channel_metadata = Column(JSONB, default=dict, nullable=False)
    
    # User information
    user_identifier = Column(String(255), nullable=True, index=True)  # Phone, username, etc.
    user_name = Column(String(200), nullable=True)
    user_metadata = Column(JSONB, default=dict, nullable=False)
    
    # Processing status
    processing_status = Column(String(50), default="pending", nullable=False)
    ai_processed = Column(Boolean, default=False, nullable=False)
    ai_response = Column(Text, nullable=True)
    ai_processing_time = Column(Float, nullable=True)
    
    # Delivery status (for outbound messages)
    delivery_status = Column(String(50), default="pending", nullable=False)
    delivered_at = Column(DateTime(timezone=True), nullable=True)
    read_at = Column(DateTime(timezone=True), nullable=True)
    
    # Error handling
    error_count = Column(Integer, default=0, nullable=False)
    last_error = Column(Text, nullable=True)
    
    # Timestamps
    sent_at = Column(DateTime(timezone=True), nullable=True)
    received_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    creator = relationship("Creator", backref="messages")
    conversation = relationship("Conversation", backref="messages")
    channel_configuration = relationship("ChannelConfiguration", backref="messages")
    
    # Indexes and constraints
    __table_args__ = (
        Index('idx_messages_creator_id', 'creator_id'),
        Index('idx_messages_conversation_id', 'conversation_id'),
        Index('idx_messages_channel_config_id', 'channel_config_id'),
        Index('idx_messages_direction', 'direction'),
        Index('idx_messages_processing_status', 'processing_status'),
        Index('idx_messages_created_at', 'created_at'),
        Index('idx_messages_external_id', 'external_message_id'),
        Index('idx_messages_user_identifier', 'user_identifier'),
        Index('idx_messages_creator_conversation', 'creator_id', 'conversation_id'),
        CheckConstraint('message_type IN (\'text\', \'image\', \'audio\', \'video\', \'document\', \'location\', \'contact\')', name='valid_message_type'),
        CheckConstraint('direction IN (\'inbound\', \'outbound\')', name='valid_direction'),
        CheckConstraint('processing_status IN (\'pending\', \'processing\', \'completed\', \'failed\', \'skipped\')', name='valid_processing_status'),
        CheckConstraint('delivery_status IN (\'pending\', \'sent\', \'delivered\', \'read\', \'failed\')', name='valid_delivery_status'),
        CheckConstraint('error_count >= 0', name='valid_error_count'),
        CheckConstraint('ai_processing_time IS NULL OR ai_processing_time >= 0', name='valid_processing_time'),
        # RLS: creator_id = current_setting('app.current_creator_id')::uuid
    )


class WebhookEvent(Base):
    """Webhook event log for channel integrations"""
    __tablename__ = "webhook_events"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Tenant isolation
    creator_id = Column(UUID(as_uuid=True), ForeignKey("creators.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Event identification
    channel_config_id = Column(UUID(as_uuid=True), ForeignKey("channel_configurations.id", ondelete="CASCADE"), nullable=False, index=True)
    event_type = Column(String(100), nullable=False, index=True)
    event_source = Column(String(50), nullable=False)  # whatsapp, telegram, etc.
    
    # Event data
    payload = Column(JSONB, nullable=False)
    headers = Column(JSONB, default=dict, nullable=False)
    signature = Column(String(500), nullable=True)
    
    # Processing status
    processing_status = Column(String(50), default="pending", nullable=False)
    processed_at = Column(DateTime(timezone=True), nullable=True)
    message_id = Column(UUID(as_uuid=True), ForeignKey("messages.id", ondelete="SET NULL"), nullable=True, index=True)
    
    # Request metadata
    source_ip = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    request_id = Column(String(255), nullable=True, index=True)
    
    # Error handling
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    creator = relationship("Creator", backref="webhook_events")
    channel_configuration = relationship("ChannelConfiguration", backref="webhook_events")
    message = relationship("Message", backref="webhook_events")
    
    # Indexes and constraints
    __table_args__ = (
        Index('idx_webhook_events_creator_id', 'creator_id'),
        Index('idx_webhook_events_channel_config_id', 'channel_config_id'),
        Index('idx_webhook_events_event_type', 'event_type'),
        Index('idx_webhook_events_source', 'event_source'),
        Index('idx_webhook_events_processing_status', 'processing_status'),
        Index('idx_webhook_events_created_at', 'created_at'),
        Index('idx_webhook_events_request_id', 'request_id'),
        CheckConstraint('event_source IN (\'whatsapp\', \'telegram\', \'web_widget\', \'mobile_app\', \'instagram\', \'facebook\')', name='valid_event_source'),
        CheckConstraint('processing_status IN (\'pending\', \'processing\', \'completed\', \'failed\', \'ignored\')', name='valid_webhook_processing_status'),
        CheckConstraint('retry_count >= 0 AND retry_count <= 10', name='valid_retry_count'),
        # RLS: creator_id = current_setting('app.current_creator_id')::uuid
    )