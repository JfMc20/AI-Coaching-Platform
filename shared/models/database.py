"""
Database models for MVP Coaching AI Platform
Multi-tenant architecture with Row Level Security (RLS)
"""

from sqlalchemy import (
    Column, String, Integer, Boolean, DateTime, Text, ARRAY, 
    ForeignKey, Index, CheckConstraint, BigInteger, Float, JSON
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

Base = declarative_base()


class TimestampMixin:
    """Mixin for created_at and updated_at timestamps"""
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class Creator(Base, TimestampMixin):
    """Creator/tenant table - main entity for multi-tenancy"""
    __tablename__ = "creators"
    __table_args__ = (
        Index('idx_creators_email', 'email'),
        {'schema': 'auth'}
    )
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(100), nullable=False)
    company_name = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    subscription_tier = Column(String(50), default='free', nullable=False)
    
    # Relationships
    user_sessions = relationship("UserSession", back_populates="creator", cascade="all, delete-orphan")
    knowledge_documents = relationship("KnowledgeDocument", back_populates="creator", cascade="all, delete-orphan")
    widget_configs = relationship("WidgetConfig", back_populates="creator", cascade="all, delete-orphan")
    conversations = relationship("Conversation", back_populates="creator", cascade="all, delete-orphan")


class UserSession(Base, TimestampMixin):
    """User sessions for anonymous widget users"""
    __tablename__ = "user_sessions"
    __table_args__ = (
        Index('idx_user_sessions_creator_id', 'creator_id'),
        Index('idx_user_sessions_session_id', 'session_id'),
        {'schema': 'auth'}
    )
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(String(255), unique=True, nullable=False)
    creator_id = Column(UUID(as_uuid=True), ForeignKey('auth.creators.id', ondelete='CASCADE'), nullable=False)
    channel = Column(String(50), default='web_widget', nullable=False)
    metadata = Column(JSON, default={}, nullable=False)
    last_activity = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    creator = relationship("Creator", back_populates="user_sessions")
    conversations = relationship("Conversation", back_populates="user_session", cascade="all, delete-orphan")


class KnowledgeDocument(Base, TimestampMixin):
    """Knowledge base documents"""
    __tablename__ = "knowledge_documents"
    __table_args__ = (
        Index('idx_knowledge_documents_creator_id', 'creator_id'),
        Index('idx_knowledge_documents_status', 'creator_id', 'status'),
        Index('idx_knowledge_documents_document_id', 'creator_id', 'document_id'),
        {'schema': 'content'}
    )
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    creator_id = Column(UUID(as_uuid=True), ForeignKey('auth.creators.id', ondelete='CASCADE'), nullable=False)
    document_id = Column(String(255), nullable=False)
    filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=True)
    file_size = Column(BigInteger, nullable=True)
    mime_type = Column(String(100), nullable=True)
    status = Column(String(50), default='pending', nullable=False)
    total_chunks = Column(Integer, default=0, nullable=False)
    processing_time_seconds = Column(Float, nullable=True)
    error_message = Column(Text, nullable=True)
    metadata = Column(JSON, default={}, nullable=False)
    
    # Relationships
    creator = relationship("Creator", back_populates="knowledge_documents")
    
    # Constraints
    __table_args__ = (
        *__table_args__[:-1],  # Keep existing indexes
        CheckConstraint('total_chunks >= 0', name='check_total_chunks_non_negative'),
        CheckConstraint('file_size >= 0', name='check_file_size_non_negative'),
        CheckConstraint("status IN ('pending', 'processing', 'completed', 'failed')", name='check_valid_status'),
        {'schema': 'content'}
    )


class WidgetConfig(Base, TimestampMixin):
    """Widget configuration for each creator"""
    __tablename__ = "widget_configs"
    __table_args__ = (
        Index('idx_widget_configs_creator_id', 'creator_id'),
        Index('idx_widget_configs_widget_id', 'creator_id', 'widget_id'),
        {'schema': 'content'}
    )
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    creator_id = Column(UUID(as_uuid=True), ForeignKey('auth.creators.id', ondelete='CASCADE'), nullable=False)
    widget_id = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    theme = Column(JSON, default={}, nullable=False)
    behavior = Column(JSON, default={}, nullable=False)
    allowed_domains = Column(ARRAY(String), default=[], nullable=False)
    rate_limit_per_minute = Column(Integer, default=10, nullable=False)
    embed_code = Column(Text, nullable=True)
    
    # Relationships
    creator = relationship("Creator", back_populates="widget_configs")
    
    # Constraints
    __table_args__ = (
        *__table_args__[:-1],  # Keep existing indexes
        CheckConstraint('rate_limit_per_minute > 0', name='check_rate_limit_positive'),
        {'schema': 'content'}
    )


class Conversation(Base, TimestampMixin):
    """Conversations between users and AI"""
    __tablename__ = "conversations"
    __table_args__ = (
        Index('idx_conversations_creator_id', 'creator_id'),
        Index('idx_conversations_session_id', 'session_id'),
        Index('idx_conversations_created_at', 'creator_id', 'created_at'),
        {'schema': 'conversations'}
    )
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    creator_id = Column(UUID(as_uuid=True), ForeignKey('auth.creators.id', ondelete='CASCADE'), nullable=False)
    session_id = Column(UUID(as_uuid=True), ForeignKey('auth.user_sessions.id', ondelete='CASCADE'), nullable=False)
    title = Column(String(255), nullable=True)
    channel = Column(String(50), default='web_widget', nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    message_count = Column(Integer, default=0, nullable=False)
    last_message_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    metadata = Column(JSON, default={}, nullable=False)
    
    # Relationships
    creator = relationship("Creator", back_populates="conversations")
    user_session = relationship("UserSession", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")
    
    # Constraints
    __table_args__ = (
        *__table_args__[:-1],  # Keep existing indexes
        CheckConstraint('message_count >= 0', name='check_message_count_non_negative'),
        {'schema': 'conversations'}
    )


class Message(Base):
    """Individual messages in conversations"""
    __tablename__ = "messages"
    __table_args__ = (
        Index('idx_messages_creator_id', 'creator_id'),
        Index('idx_messages_conversation_id', 'conversation_id'),
        Index('idx_messages_created_at', 'creator_id', 'created_at'),
        {'schema': 'conversations'}
    )
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    creator_id = Column(UUID(as_uuid=True), ForeignKey('auth.creators.id', ondelete='CASCADE'), nullable=False)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey('conversations.conversations.id', ondelete='CASCADE'), nullable=False)
    role = Column(String(20), nullable=False)  # 'user', 'assistant', 'system'
    content = Column(Text, nullable=False)
    metadata = Column(JSON, default={}, nullable=False)
    processing_time_ms = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    conversation = relationship("Conversation", back_populates="messages")
    
    # Constraints
    __table_args__ = (
        *__table_args__[:-1],  # Keep existing indexes
        CheckConstraint("role IN ('user', 'assistant', 'system')", name='check_valid_message_role'),
        CheckConstraint('processing_time_ms >= 0', name='check_processing_time_non_negative'),
        {'schema': 'conversations'}
    )