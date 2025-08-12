"""
Database models for the MVP Coaching AI Platform
SQLAlchemy models with multi-tenant Row Level Security support
"""

import uuid
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from sqlalchemy import (
    Column, String, Boolean, DateTime, Text, JSON, Integer,
    ForeignKey, Index, UniqueConstraint, CheckConstraint
)
from sqlalchemy.dialects.postgresql import UUID
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