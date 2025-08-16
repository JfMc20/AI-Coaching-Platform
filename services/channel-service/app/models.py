"""
Pydantic models for Channel Service
Multi-channel messaging with WhatsApp, Telegram, and Web Widget support
"""

from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field, validator
from shared.models.base import TenantAwareEntity


class ChannelType(str, Enum):
    """Supported channel types"""
    WHATSAPP = "whatsapp"
    TELEGRAM = "telegram"
    WEB_WIDGET = "web_widget"
    MOBILE_APP = "mobile_app"
    INSTAGRAM = "instagram"
    FACEBOOK = "facebook"


class MessageType(str, Enum):
    """Supported message types"""
    TEXT = "text"
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"
    DOCUMENT = "document"
    LOCATION = "location"
    CONTACT = "contact"


class MessageDirection(str, Enum):
    """Message direction"""
    INBOUND = "inbound"
    OUTBOUND = "outbound"


class ProcessingStatus(str, Enum):
    """Message processing status"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class DeliveryStatus(str, Enum):
    """Message delivery status"""
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    READ = "read"
    FAILED = "failed"


class HealthStatus(str, Enum):
    """Channel health status"""
    HEALTHY = "healthy"
    WARNING = "warning"
    ERROR = "error"
    UNKNOWN = "unknown"


# =====================================================
# Channel Configuration Models
# =====================================================

class ChannelConfigurationBase(BaseModel):
    """Base channel configuration"""
    channel_type: ChannelType = Field(..., description="Channel type")
    channel_name: str = Field(..., max_length=100, description="Channel name")
    is_active: bool = Field(default=True, description="Channel active status")
    configuration: Dict[str, Any] = Field(default_factory=dict, description="Channel-specific configuration")
    daily_message_limit: int = Field(default=1000, ge=1, le=10000, description="Daily message limit")
    monthly_message_limit: int = Field(default=30000, ge=1, le=500000, description="Monthly message limit")


class ChannelConfigurationCreate(ChannelConfigurationBase):
    """Create channel configuration"""
    api_token: Optional[str] = Field(None, description="Channel API token")
    webhook_secret: Optional[str] = Field(None, description="Webhook secret")


class ChannelConfigurationUpdate(BaseModel):
    """Update channel configuration"""
    channel_name: Optional[str] = Field(None, max_length=100)
    is_active: Optional[bool] = None
    configuration: Optional[Dict[str, Any]] = None
    api_token: Optional[str] = None
    webhook_secret: Optional[str] = None
    daily_message_limit: Optional[int] = Field(None, ge=1, le=10000)
    monthly_message_limit: Optional[int] = Field(None, ge=1, le=500000)


class ChannelConfiguration(TenantAwareEntity, ChannelConfigurationBase):
    """Channel configuration response"""
    id: str = Field(..., description="Channel configuration ID")
    webhook_url: Optional[str] = Field(None, description="Webhook URL")
    current_daily_count: int = Field(default=0, description="Current daily message count")
    current_monthly_count: int = Field(default=0, description="Current monthly message count")
    last_health_check: Optional[datetime] = Field(None, description="Last health check timestamp")
    health_status: HealthStatus = Field(default=HealthStatus.UNKNOWN, description="Channel health status")
    error_message: Optional[str] = Field(None, description="Last error message")


# =====================================================
# Message Models
# =====================================================

class MessageBase(BaseModel):
    """Base message model"""
    content: str = Field(..., description="Message content")
    message_type: MessageType = Field(default=MessageType.TEXT, description="Message type")
    channel_metadata: Dict[str, Any] = Field(default_factory=dict, description="Channel-specific metadata")
    user_identifier: Optional[str] = Field(None, description="User identifier (phone, username, etc.)")
    user_name: Optional[str] = Field(None, description="User display name")
    user_metadata: Dict[str, Any] = Field(default_factory=dict, description="User metadata")


class InboundMessage(MessageBase):
    """Inbound message from channel"""
    conversation_id: Optional[str] = Field(None, description="Conversation ID")
    external_message_id: Optional[str] = Field(None, description="External message ID")
    received_at: Optional[datetime] = Field(None, description="Message received timestamp")


class OutboundMessage(MessageBase):
    """Outbound message to channel"""
    conversation_id: str = Field(..., description="Conversation ID")
    channel_config_id: str = Field(..., description="Channel configuration ID")


class MessageCreate(MessageBase):
    """Create message"""
    conversation_id: str = Field(..., description="Conversation ID")
    channel_config_id: str = Field(..., description="Channel configuration ID")
    direction: MessageDirection = Field(..., description="Message direction")
    external_message_id: Optional[str] = Field(None, description="External message ID")


class Message(TenantAwareEntity, MessageBase):
    """Message response"""
    id: str = Field(..., description="Message ID")
    conversation_id: str = Field(..., description="Conversation ID")
    channel_config_id: str = Field(..., description="Channel configuration ID")
    direction: MessageDirection = Field(..., description="Message direction")
    external_message_id: Optional[str] = Field(None, description="External message ID")
    processing_status: ProcessingStatus = Field(default=ProcessingStatus.PENDING, description="Processing status")
    ai_processed: bool = Field(default=False, description="AI processed flag")
    ai_response: Optional[str] = Field(None, description="AI response")
    ai_processing_time: Optional[float] = Field(None, description="AI processing time in seconds")
    delivery_status: DeliveryStatus = Field(default=DeliveryStatus.PENDING, description="Delivery status")
    delivered_at: Optional[datetime] = Field(None, description="Delivered timestamp")
    read_at: Optional[datetime] = Field(None, description="Read timestamp")
    error_count: int = Field(default=0, description="Error count")
    last_error: Optional[str] = Field(None, description="Last error message")
    sent_at: Optional[datetime] = Field(None, description="Sent timestamp")
    received_at: Optional[datetime] = Field(None, description="Received timestamp")


# =====================================================
# Webhook Models
# =====================================================

class WebhookEventBase(BaseModel):
    """Base webhook event"""
    event_type: str = Field(..., description="Event type")
    event_source: ChannelType = Field(..., description="Event source channel")
    payload: Dict[str, Any] = Field(..., description="Event payload")
    headers: Dict[str, str] = Field(default_factory=dict, description="Request headers")
    signature: Optional[str] = Field(None, description="Webhook signature")


class WebhookEventCreate(WebhookEventBase):
    """Create webhook event"""
    channel_config_id: str = Field(..., description="Channel configuration ID")
    source_ip: Optional[str] = Field(None, description="Source IP address")
    user_agent: Optional[str] = Field(None, description="User agent")
    request_id: Optional[str] = Field(None, description="Request ID")


class WebhookEvent(TenantAwareEntity, WebhookEventBase):
    """Webhook event response"""
    id: str = Field(..., description="Event ID")
    channel_config_id: str = Field(..., description="Channel configuration ID")
    processing_status: ProcessingStatus = Field(default=ProcessingStatus.PENDING, description="Processing status")
    processed_at: Optional[datetime] = Field(None, description="Processed timestamp")
    message_id: Optional[str] = Field(None, description="Related message ID")
    source_ip: Optional[str] = Field(None, description="Source IP address")
    user_agent: Optional[str] = Field(None, description="User agent")
    request_id: Optional[str] = Field(None, description="Request ID")
    error_message: Optional[str] = Field(None, description="Error message")
    retry_count: int = Field(default=0, description="Retry count")


# =====================================================
# Channel-Specific Configuration Models
# =====================================================

class WhatsAppConfiguration(BaseModel):
    """WhatsApp Business API configuration"""
    phone_number_id: str = Field(..., description="WhatsApp Phone Number ID")
    business_account_id: str = Field(..., description="WhatsApp Business Account ID")
    webhook_verify_token: str = Field(..., description="Webhook verification token")
    api_version: str = Field(default="v18.0", description="WhatsApp API version")
    message_template_namespace: Optional[str] = Field(None, description="Message template namespace")


class TelegramConfiguration(BaseModel):
    """Telegram Bot API configuration"""
    bot_username: str = Field(..., description="Bot username")
    webhook_secret_token: Optional[str] = Field(None, description="Webhook secret token")
    allowed_updates: List[str] = Field(default=["message", "callback_query"], description="Allowed update types")
    max_connections: int = Field(default=40, ge=1, le=100, description="Max webhook connections")


class WebWidgetConfiguration(BaseModel):
    """Web Widget configuration"""
    allowed_domains: List[str] = Field(default_factory=list, description="Allowed domains")
    theme_color: str = Field(default="#007bff", description="Widget theme color")
    welcome_message: str = Field(default="Hello! How can I help you?", description="Welcome message")
    placeholder_text: str = Field(default="Type your message...", description="Input placeholder")
    enable_file_upload: bool = Field(default=True, description="Enable file upload")
    enable_voice_input: bool = Field(default=False, description="Enable voice input")
    rate_limit_messages: int = Field(default=10, ge=1, le=100, description="Rate limit per minute")


# =====================================================
# Response Models
# =====================================================

class MessageListResponse(BaseModel):
    """Message list response"""
    messages: List[Message] = Field(..., description="List of messages")
    total: int = Field(..., description="Total message count")
    page: int = Field(..., description="Current page")
    size: int = Field(..., description="Page size")


class ChannelConfigurationListResponse(BaseModel):
    """Channel configuration list response"""
    configurations: List[ChannelConfiguration] = Field(..., description="List of configurations")
    total: int = Field(..., description="Total configuration count")


class ChannelHealthResponse(BaseModel):
    """Channel health response"""
    channel_id: str = Field(..., description="Channel configuration ID")
    channel_type: ChannelType = Field(..., description="Channel type")
    health_status: HealthStatus = Field(..., description="Health status")
    last_check: Optional[datetime] = Field(None, description="Last health check")
    error_message: Optional[str] = Field(None, description="Error message if any")
    metrics: Dict[str, Any] = Field(default_factory=dict, description="Health metrics")


class WebSocketMessage(BaseModel):
    """WebSocket message structure"""
    type: str = Field(..., description="Message type")
    conversation_id: Optional[str] = Field(None, description="Conversation ID")
    content: str = Field(..., description="Message content")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Message metadata")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Message timestamp")


class WebSocketResponse(BaseModel):
    """WebSocket response structure"""
    type: str = Field(..., description="Response type")
    status: str = Field(..., description="Response status")
    data: Optional[Dict[str, Any]] = Field(None, description="Response data")
    error: Optional[str] = Field(None, description="Error message")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")