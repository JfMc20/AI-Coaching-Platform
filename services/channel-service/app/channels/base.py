"""
Base Channel Service
Abstract base class for all channel integrations
"""

import logging
import uuid
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from ..models import (
    ChannelConfiguration, 
    Message, 
    InboundMessage, 
    OutboundMessage,
    WebhookEvent,
    HealthStatus,
    MessageDirection,
    ProcessingStatus,
    DeliveryStatus
)
from ..ai_client import get_ai_client, ConversationResponse

logger = logging.getLogger(__name__)


class BaseChannelService(ABC):
    """
    Abstract base class for channel integrations
    Provides common functionality and interface for all channels
    """
    
    def __init__(self, channel_config: ChannelConfiguration, db_session: AsyncSession):
        self.channel_config = channel_config
        self.db_session = db_session
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    @property
    @abstractmethod
    def channel_type(self) -> str:
        """Return the channel type identifier"""
        pass
    
    @abstractmethod
    async def validate_configuration(self) -> bool:
        """
        Validate channel configuration
        Returns True if configuration is valid, False otherwise
        """
        pass
    
    @abstractmethod
    async def send_message(self, message: OutboundMessage) -> Dict[str, Any]:
        """
        Send message through the channel
        Returns delivery status and metadata
        """
        pass
    
    @abstractmethod
    async def process_webhook(self, webhook_data: Dict[str, Any]) -> Optional[InboundMessage]:
        """
        Process incoming webhook from channel
        Returns parsed inbound message or None if not a message event
        """
        pass
    
    @abstractmethod
    async def check_health(self) -> Dict[str, Any]:
        """
        Check channel health and connectivity
        Returns health status and metrics
        """
        pass
    
    @abstractmethod
    async def setup_webhook(self, webhook_url: str) -> bool:
        """
        Setup webhook URL with the channel provider
        Returns True if successful, False otherwise
        """
        pass
    
    # Common utility methods
    
    async def log_webhook_event(self, event_data: Dict[str, Any], event_type: str) -> str:
        """Log webhook event to database"""
        try:
            from shared.models.database import WebhookEvent
            import uuid
            
            webhook_event = WebhookEvent(
                id=uuid.uuid4(),
                creator_id=self.channel_config.creator_id,
                channel_config_id=self.channel_config.id,
                event_type=event_type,
                event_source=self.channel_type,
                payload=event_data,
                headers=event_data.get("headers", {}),
                processing_status="pending"
            )
            
            self.db_session.add(webhook_event)
            await self.db_session.commit()
            
            self.logger.info(f"Logged webhook event {webhook_event.id} for channel {self.channel_config.id}")
            return str(webhook_event.id)
            
        except Exception as e:
            self.logger.error(f"Failed to log webhook event: {e}")
            await self.db_session.rollback()
            raise
    
    async def save_message(self, message_data: Dict[str, Any], direction: MessageDirection) -> str:
        """Save message to database"""
        try:
            from shared.models.database import Message as DBMessage
            import uuid
            
            message = DBMessage(
                id=uuid.uuid4(),
                creator_id=self.channel_config.creator_id,
                conversation_id=message_data.get("conversation_id"),
                channel_config_id=self.channel_config.id,
                content=message_data.get("content", ""),
                message_type=message_data.get("message_type", "text"),
                direction=direction,
                external_message_id=message_data.get("external_message_id"),
                channel_metadata=message_data.get("channel_metadata", {}),
                user_identifier=message_data.get("user_identifier"),
                user_name=message_data.get("user_name"),
                user_metadata=message_data.get("user_metadata", {}),
                processing_status="pending" if direction == MessageDirection.INBOUND else "completed",
                received_at=datetime.utcnow() if direction == MessageDirection.INBOUND else None,
                sent_at=datetime.utcnow() if direction == MessageDirection.OUTBOUND else None
            )
            
            self.db_session.add(message)
            await self.db_session.commit()
            
            self.logger.info(f"Saved {direction} message {message.id} for channel {self.channel_config.id}")
            return str(message.id)
            
        except Exception as e:
            self.logger.error(f"Failed to save message: {e}")
            await self.db_session.rollback()
            raise
    
    async def update_message_status(self, message_id: str, status_updates: Dict[str, Any]) -> bool:
        """Update message status in database"""
        try:
            from shared.models.database import Message as DBMessage
            from sqlalchemy import select, update
            
            stmt = (
                update(DBMessage)
                .where(DBMessage.id == message_id)
                .where(DBMessage.creator_id == self.channel_config.creator_id)
                .values(**status_updates)
            )
            
            result = await self.db_session.execute(stmt)
            await self.db_session.commit()
            
            if result.rowcount > 0:
                self.logger.info(f"Updated message {message_id} status: {status_updates}")
                return True
            else:
                self.logger.warning(f"Message {message_id} not found for update")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to update message status: {e}")
            await self.db_session.rollback()
            return False
    
    async def process_message_with_ai(
        self, 
        inbound_message: InboundMessage,
        conversation_id: Optional[str] = None
    ) -> Optional[OutboundMessage]:
        """
        Process an inbound message with AI Engine and generate response
        
        Args:
            inbound_message: The inbound message to process
            conversation_id: Optional conversation ID, will generate if not provided
            
        Returns:
            OutboundMessage with AI response, or None if processing failed
        """
        try:
            # Generate conversation ID if not provided
            if not conversation_id:
                conversation_id = str(uuid.uuid4())
            
            # Get AI client
            ai_client = get_ai_client()
            
            # Process message with AI Engine
            ai_response: ConversationResponse = await ai_client.process_message(
                message=inbound_message.content,
                creator_id=self.channel_config.creator_id,
                conversation_id=conversation_id,
                user_identifier=inbound_message.user_identifier
            )
            
            # Create outbound message with AI response
            outbound_message = OutboundMessage(
                content=ai_response.response,
                message_type=inbound_message.message_type,
                user_identifier=inbound_message.user_identifier,
                conversation_id=ai_response.conversation_id,
                channel_metadata={
                    "ai_processed": True,
                    "ai_metadata": ai_response.metadata,
                    "original_message_id": inbound_message.external_message_id
                }
            )
            
            self.logger.info(f"Generated AI response for conversation {conversation_id}")
            return outbound_message
            
        except Exception as e:
            self.logger.error(f"Failed to process message with AI: {e}")
            
            # Return fallback response
            fallback_message = OutboundMessage(
                content="I apologize, but I'm having trouble processing your message right now. Please try again later.",
                message_type=inbound_message.message_type,
                user_identifier=inbound_message.user_identifier,
                conversation_id=conversation_id or str(uuid.uuid4()),
                channel_metadata={
                    "ai_processed": False,
                    "fallback_response": True,
                    "error": str(e)
                }
            )
            
            return fallback_message
    
    async def increment_message_count(self) -> bool:
        """Increment daily and monthly message counts"""
        try:
            from shared.models.database import ChannelConfiguration as DBChannelConfig
            from sqlalchemy import update
            
            stmt = (
                update(DBChannelConfig)
                .where(DBChannelConfig.id == self.channel_config.id)
                .where(DBChannelConfig.creator_id == self.channel_config.creator_id)
                .values(
                    current_daily_count=DBChannelConfig.current_daily_count + 1,
                    current_monthly_count=DBChannelConfig.current_monthly_count + 1
                )
            )
            
            result = await self.db_session.execute(stmt)
            await self.db_session.commit()
            
            return result.rowcount > 0
            
        except Exception as e:
            self.logger.error(f"Failed to increment message count: {e}")
            await self.db_session.rollback()
            return False
    
    async def check_rate_limits(self) -> bool:
        """Check if channel has exceeded rate limits"""
        try:
            daily_limit = self.channel_config.daily_message_limit
            monthly_limit = self.channel_config.monthly_message_limit
            daily_count = self.channel_config.current_daily_count
            monthly_count = self.channel_config.current_monthly_count
            
            if daily_count >= daily_limit:
                self.logger.warning(f"Daily rate limit exceeded: {daily_count}/{daily_limit}")
                return False
            
            if monthly_count >= monthly_limit:
                self.logger.warning(f"Monthly rate limit exceeded: {monthly_count}/{monthly_limit}")
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to check rate limits: {e}")
            return False
    
    async def update_health_status(self, status: HealthStatus, error_message: Optional[str] = None) -> bool:
        """Update channel health status"""
        try:
            from shared.models.database import ChannelConfiguration as DBChannelConfig
            from sqlalchemy import update
            
            update_data = {
                "health_status": status,
                "last_health_check": datetime.utcnow()
            }
            
            if error_message:
                update_data["error_message"] = error_message
            
            stmt = (
                update(DBChannelConfig)
                .where(DBChannelConfig.id == self.channel_config.id)
                .where(DBChannelConfig.creator_id == self.channel_config.creator_id)
                .values(**update_data)
            )
            
            result = await self.db_session.execute(stmt)
            await self.db_session.commit()
            
            return result.rowcount > 0
            
        except Exception as e:
            self.logger.error(f"Failed to update health status: {e}")
            await self.db_session.rollback()
            return False
    
    def validate_webhook_signature(self, payload: str, signature: str, secret: str) -> bool:
        """
        Validate webhook signature (to be implemented by each channel)
        Default implementation returns True
        """
        self.logger.warning("Webhook signature validation not implemented for this channel")
        return True
    
    def extract_user_info(self, webhook_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract user information from webhook data
        Default implementation returns empty dict
        """
        return {
            "user_identifier": webhook_data.get("from", {}).get("id", "unknown"),
            "user_name": webhook_data.get("from", {}).get("name", "Unknown User"),
            "user_metadata": {}
        }
    
    def format_message_content(self, content: str, message_type: str = "text") -> str:
        """
        Format message content for the specific channel
        Default implementation returns content as-is
        """
        return content
    
    async def get_conversation_id(self, user_identifier: str) -> str:
        """
        Get or create conversation ID for user
        Creates new conversation if none exists
        """
        try:
            from shared.models.database import Conversation
            from sqlalchemy import select
            import uuid
            
            # Try to find existing active conversation
            stmt = (
                select(Conversation)
                .where(Conversation.creator_id == self.channel_config.creator_id)
                .where(Conversation.status == "active")
                .where(Conversation.conversation_metadata["user_identifier"].astext == user_identifier)
            )
            
            result = await self.db_session.execute(stmt)
            conversation = result.scalar_one_or_none()
            
            if conversation:
                return str(conversation.id)
            
            # Create new conversation
            new_conversation = Conversation(
                id=uuid.uuid4(),
                creator_id=self.channel_config.creator_id,
                status="active",
                conversation_metadata={"user_identifier": user_identifier, "channel_type": self.channel_type}
            )
            
            self.db_session.add(new_conversation)
            await self.db_session.commit()
            
            self.logger.info(f"Created new conversation {new_conversation.id} for user {user_identifier}")
            return str(new_conversation.id)
            
        except Exception as e:
            self.logger.error(f"Failed to get conversation ID: {e}")
            await self.db_session.rollback()
            raise