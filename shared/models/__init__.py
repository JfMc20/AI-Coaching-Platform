"""Shared Pydantic models for all services"""

from .auth import CreatorCreate, CreatorResponse, TokenResponse, UserSession
from .documents import ProcessingResult, DocumentChunk, ProcessingStatus
from .widgets import WidgetConfig, WidgetTheme, WidgetBehavior
from .conversations import Message, Conversation, ConversationContext

__all__ = [
    "CreatorCreate",
    "CreatorResponse", 
    "TokenResponse",
    "UserSession",
    "ProcessingResult",
    "DocumentChunk",
    "ProcessingStatus",
    "WidgetConfig",
    "WidgetTheme",
    "WidgetBehavior",
    "Message",
    "Conversation",
    "ConversationContext",
]