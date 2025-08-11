"""Conversation and messaging models"""

from pydantic import BaseModel, Field, validator
from datetime import datetime
from typing import Optional, Dict, Any, List
from enum import Enum
from .base import TenantAwareEntity


class MessageRole(str, Enum):
    """Message role enumeration"""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class Message(TenantAwareEntity):
    """Individual message in a conversation"""
    conversation_id: str = Field(..., description="Conversation this message belongs to")
    role: MessageRole = Field(..., description="Message role (user, assistant, system)")
    content: str = Field(..., description="Message content")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Message metadata")
    processing_time_ms: Optional[int] = Field(None, ge=0, description="Time taken to generate response")
    
    @validator('content')
    def validate_content_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Message content cannot be empty')
        return v.strip()


class ConversationContext(BaseModel):
    """Context information for conversation processing"""
    recent_messages: List[Message] = Field(default_factory=list, description="Recent conversation messages")
    relevant_documents: List[str] = Field(default_factory=list, description="IDs of relevant documents")
    user_preferences: Dict[str, Any] = Field(default_factory=dict, description="User preferences and settings")
    session_metadata: Dict[str, Any] = Field(default_factory=dict, description="Session-specific metadata")


class Conversation(TenantAwareEntity):
    """Conversation entity"""
    session_id: str = Field(..., description="User session this conversation belongs to")
    title: Optional[str] = Field(None, description="Conversation title (auto-generated or user-set)")
    channel: str = Field(default="web_widget", description="Channel where conversation occurred")
    is_active: bool = Field(default=True, description="Whether conversation is active")
    last_message_at: datetime = Field(default_factory=datetime.utcnow, description="Timestamp of last message")
    message_count: int = Field(default=0, ge=0, description="Total number of messages")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Conversation metadata")
    
    @validator('message_count')
    def validate_message_count(cls, v):
        if v < 0:
            raise ValueError('Message count cannot be negative')
        return v