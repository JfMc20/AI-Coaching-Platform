"""
Channel integrations package
Modular channel services for multi-platform messaging
"""

from .base import BaseChannelService
from .whatsapp import WhatsAppService
from .telegram import TelegramService
from .web_widget import WebWidgetService

__all__ = [
    "BaseChannelService",
    "WhatsAppService", 
    "TelegramService",
    "WebWidgetService"
]