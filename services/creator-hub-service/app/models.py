"""
Creator Hub Service Models
Implements creator profile, knowledge base, and analytics models
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, Field, validator
from shared.models.base import TenantAwareEntity


# ==================== CREATOR PROFILE MODELS ====================

class CreatorStatus(str, Enum):
    """Creator account status"""
    ACTIVE = "active"
    PENDING = "pending"
    SUSPENDED = "suspended"
    INACTIVE = "inactive"


class CreatorProfile(TenantAwareEntity):
    """Creator profile model with multi-tenant support"""
    email: str = Field(..., description="Creator email address")
    display_name: str = Field(..., max_length=100, description="Public display name")
    bio: Optional[str] = Field(None, max_length=500, description="Creator biography")
    avatar_url: Optional[str] = Field(None, description="Profile avatar URL")
    website_url: Optional[str] = Field(None, description="Creator website")
    status: CreatorStatus = Field(default=CreatorStatus.PENDING, description="Account status")
    
    # Coaching specific fields
    coaching_categories: List[str] = Field(default_factory=list, description="Coaching specializations")
    experience_years: Optional[int] = Field(None, ge=0, le=50, description="Years of coaching experience")
    certifications: List[str] = Field(default_factory=list, description="Professional certifications")
    
    # Platform settings
    timezone: str = Field(default="UTC", description="Creator timezone")
    language: str = Field(default="en", description="Primary language")
    onboarding_completed: bool = Field(default=False, description="Onboarding completion status")
    
    @validator('email')
    def validate_email(cls, v):
        # Simple email validation
        if '@' not in v or '.' not in v.split('@')[-1]:
            raise ValueError('Invalid email format')
        return v.lower()
    
    @validator('display_name')
    def validate_display_name(cls, v):
        if not v or not v.strip():
            raise ValueError('Display name cannot be empty')
        return v.strip()


class CreatorProfileUpdate(BaseModel):
    """Model for updating creator profile"""
    display_name: Optional[str] = Field(None, max_length=100)
    bio: Optional[str] = Field(None, max_length=500)
    avatar_url: Optional[str] = None
    website_url: Optional[str] = None
    coaching_categories: Optional[List[str]] = None
    experience_years: Optional[int] = Field(None, ge=0, le=50)
    certifications: Optional[List[str]] = None
    timezone: Optional[str] = None
    language: Optional[str] = None


# ==================== KNOWLEDGE BASE MODELS ====================

class DocumentType(str, Enum):
    """Document type enumeration"""
    PDF = "pdf"
    DOCX = "docx"
    TXT = "txt"
    MD = "md"
    URL = "url"


class DocumentStatus(str, Enum):
    """Document processing status"""
    UPLOADING = "uploading"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    ARCHIVED = "archived"


class DocumentMetadata(BaseModel):
    """Document metadata model"""
    filename: str = Field(..., description="Original filename")
    file_size: int = Field(..., ge=0, description="File size in bytes")
    document_type: DocumentType = Field(..., description="Document type")
    upload_timestamp: datetime = Field(default_factory=datetime.utcnow)
    content_hash: Optional[str] = Field(None, description="Content hash for deduplication")
    page_count: Optional[int] = Field(None, ge=0, description="Number of pages")
    word_count: Optional[int] = Field(None, ge=0, description="Approximate word count")
    language_detected: Optional[str] = Field(None, description="Detected language")
    tags: List[str] = Field(default_factory=list, description="Document tags")


class KnowledgeDocument(TenantAwareEntity):
    """Knowledge base document model"""
    title: str = Field(..., max_length=200, description="Document title")
    description: Optional[str] = Field(None, max_length=1000, description="Document description")
    metadata: DocumentMetadata = Field(..., description="Document metadata")
    status: DocumentStatus = Field(default=DocumentStatus.UPLOADING, description="Processing status")
    
    # Processing results
    chunk_count: int = Field(default=0, ge=0, description="Number of chunks created")
    processing_time: Optional[float] = Field(None, ge=0, description="Processing time in seconds")
    error_message: Optional[str] = Field(None, description="Error message if processing failed")
    
    # Storage information
    file_path: Optional[str] = Field(None, description="File storage path")
    embeddings_stored: bool = Field(default=False, description="Whether embeddings are stored")
    
    @validator('title')
    def validate_title(cls, v):
        if not v or not v.strip():
            raise ValueError('Document title cannot be empty')
        return v.strip()


class DocumentUploadRequest(BaseModel):
    """Document upload request model"""
    title: str = Field(..., max_length=200, description="Document title")
    description: Optional[str] = Field(None, max_length=1000, description="Document description")
    tags: List[str] = Field(default_factory=list, description="Document tags")
    
    @validator('title')
    def validate_title(cls, v):
        if not v or not v.strip():
            raise ValueError('Document title cannot be empty')
        return v.strip()


class DocumentListResponse(BaseModel):
    """Response model for document listing"""
    documents: List[KnowledgeDocument] = Field(..., description="List of documents")
    total_count: int = Field(..., ge=0, description="Total number of documents")
    page: int = Field(..., ge=1, description="Current page number")
    page_size: int = Field(..., ge=1, le=100, description="Page size")
    has_next: bool = Field(..., description="Whether there are more pages")


# ==================== ANALYTICS MODELS ====================

class MetricType(str, Enum):
    """Analytics metric types"""
    CONVERSATIONS_COUNT = "conversations_count"
    MESSAGES_COUNT = "messages_count"
    DOCUMENTS_COUNT = "documents_count"
    ACTIVE_USERS = "active_users"
    RESPONSE_TIME_AVG = "response_time_avg"
    USER_SATISFACTION = "user_satisfaction"


class TimeRange(str, Enum):
    """Time range for analytics"""
    DAY = "day"
    WEEK = "week"
    MONTH = "month"
    QUARTER = "quarter"
    YEAR = "year"


class AnalyticsMetric(BaseModel):
    """Individual analytics metric"""
    metric_type: MetricType = Field(..., description="Type of metric")
    value: float = Field(..., description="Metric value")
    timestamp: datetime = Field(..., description="Metric timestamp")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class DashboardMetrics(TenantAwareEntity):
    """Dashboard metrics for creator"""
    # Conversation metrics
    total_conversations: int = Field(default=0, ge=0, description="Total conversations")
    active_conversations: int = Field(default=0, ge=0, description="Active conversations")
    messages_today: int = Field(default=0, ge=0, description="Messages sent today")
    
    # Knowledge base metrics
    total_documents: int = Field(default=0, ge=0, description="Total documents uploaded")
    documents_processed: int = Field(default=0, ge=0, description="Successfully processed documents")
    total_knowledge_chunks: int = Field(default=0, ge=0, description="Total knowledge chunks")
    
    # Performance metrics
    avg_response_time: float = Field(default=0.0, ge=0, description="Average response time in seconds")
    user_satisfaction_score: Optional[float] = Field(None, ge=1, le=5, description="User satisfaction score (1-5)")
    
    # Usage metrics
    active_users_7d: int = Field(default=0, ge=0, description="Active users in last 7 days")
    active_users_30d: int = Field(default=0, ge=0, description="Active users in last 30 days")
    
    # Timestamps
    last_updated: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")
    period_start: datetime = Field(..., description="Period start date")
    period_end: datetime = Field(..., description="Period end date")


class AnalyticsRequest(BaseModel):
    """Request model for analytics data"""
    time_range: TimeRange = Field(default=TimeRange.WEEK, description="Time range for analytics")
    metrics: List[MetricType] = Field(default_factory=list, description="Specific metrics to retrieve")
    start_date: Optional[datetime] = Field(None, description="Custom start date")
    end_date: Optional[datetime] = Field(None, description="Custom end date")


# ==================== CONVERSATION MODELS ====================

class ConversationStatus(str, Enum):
    """Conversation status enumeration"""
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class ConversationSummary(TenantAwareEntity):
    """Summary model for conversations"""
    title: str = Field(..., description="Conversation title or summary")
    user_name: Optional[str] = Field(None, description="User display name")
    status: ConversationStatus = Field(..., description="Conversation status")
    message_count: int = Field(default=0, ge=0, description="Number of messages")
    last_message_at: Optional[datetime] = Field(None, description="Timestamp of last message")
    satisfaction_rating: Optional[int] = Field(None, ge=1, le=5, description="User satisfaction rating")
    tags: List[str] = Field(default_factory=list, description="Conversation tags")
    

class ConversationListResponse(BaseModel):
    """Response model for conversation listing"""
    conversations: List[ConversationSummary] = Field(..., description="List of conversations")
    total_count: int = Field(..., ge=0, description="Total number of conversations")
    page: int = Field(..., ge=1, description="Current page number")
    page_size: int = Field(..., ge=1, le=100, description="Page size")
    has_next: bool = Field(..., description="Whether there are more pages")


# ==================== WIDGET CONFIGURATION MODELS ====================

class WidgetTheme(str, Enum):
    """Widget theme options"""
    LIGHT = "light"
    DARK = "dark"
    AUTO = "auto"
    CUSTOM = "custom"


class WidgetPosition(str, Enum):
    """Widget position options"""
    BOTTOM_RIGHT = "bottom-right"
    BOTTOM_LEFT = "bottom-left"
    TOP_RIGHT = "top-right"
    TOP_LEFT = "top-left"
    CENTER = "center"


class WidgetSettings(BaseModel):
    """Widget appearance and behavior settings"""
    theme: WidgetTheme = Field(default=WidgetTheme.LIGHT, description="Widget theme")
    position: WidgetPosition = Field(default=WidgetPosition.BOTTOM_RIGHT, description="Widget position")
    primary_color: str = Field(default="#007bff", description="Primary color (hex)")
    secondary_color: str = Field(default="#6c757d", description="Secondary color (hex)")
    text_color: str = Field(default="#333333", description="Text color (hex)")
    background_color: str = Field(default="#ffffff", description="Background color (hex)")
    border_radius: int = Field(default=8, ge=0, le=50, description="Border radius in pixels")
    font_family: str = Field(default="Inter", description="Font family")
    font_size: int = Field(default=14, ge=10, le=24, description="Font size in pixels")


class WidgetConfiguration(TenantAwareEntity):
    """Widget configuration model"""
    name: str = Field(..., max_length=100, description="Widget configuration name")
    description: Optional[str] = Field(None, max_length=500, description="Widget description")
    is_active: bool = Field(default=True, description="Whether widget is active")
    
    # Appearance settings
    settings: WidgetSettings = Field(default_factory=WidgetSettings, description="Widget settings")
    
    # Behavior settings
    welcome_message: str = Field(default="Hello! How can I help you today?", description="Welcome message")
    placeholder_text: str = Field(default="Type your message...", description="Input placeholder text")
    enable_file_upload: bool = Field(default=True, description="Allow file uploads")
    enable_voice_input: bool = Field(default=False, description="Enable voice input")
    
    # Integration settings
    allowed_domains: List[str] = Field(default_factory=list, description="Allowed domains for widget")
    rate_limit_messages: int = Field(default=10, ge=1, le=100, description="Message rate limit per minute")
    
    # Analytics
    track_analytics: bool = Field(default=True, description="Enable analytics tracking")
    
    @validator('name')
    def validate_name(cls, v):
        if not v or not v.strip():
            raise ValueError('Widget name cannot be empty')
        return v.strip()
    
    @validator('primary_color', 'secondary_color', 'text_color', 'background_color')
    def validate_hex_color(cls, v):
        if not v.startswith('#') or len(v) != 7:
            raise ValueError('Color must be a valid hex color (e.g., #007bff)')
        try:
            int(v[1:], 16)
        except ValueError:
            raise ValueError('Invalid hex color format')
        return v


class WidgetEmbedCode(BaseModel):
    """Widget embed code response"""
    embed_code: str = Field(..., description="HTML embed code")
    widget_id: str = Field(..., description="Widget identifier")
    installation_instructions: str = Field(..., description="Installation instructions")
    preview_url: str = Field(..., description="Preview URL")