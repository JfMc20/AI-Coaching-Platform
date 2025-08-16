"""
Channel Manager
Central manager for all channel integrations and message routing
"""

import logging
from typing import Dict, List, Optional, Any, Type
from sqlalchemy.ext.asyncio import AsyncSession

from .models import ChannelConfiguration, ChannelType
from .channels import BaseChannelService, WhatsAppService, TelegramService, WebWidgetService

logger = logging.getLogger(__name__)


class ChannelManager:
    """
    Central manager for channel integrations
    Handles channel registration, message routing, and service lifecycle
    """
    
    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session
        self.service_registry: Dict[ChannelType, Type[BaseChannelService]] = {
            ChannelType.WHATSAPP: WhatsAppService,
            ChannelType.TELEGRAM: TelegramService,
            ChannelType.WEB_WIDGET: WebWidgetService,
        }
        self.active_services: Dict[str, BaseChannelService] = {}
        self.logger = logging.getLogger(__name__)
    
    def register_channel_service(self, channel_type: ChannelType, service_class: Type[BaseChannelService]):
        """Register a new channel service class"""
        self.service_registry[channel_type] = service_class
        self.logger.info(f"Registered channel service: {channel_type}")
    
    async def get_channel_service(self, channel_config: ChannelConfiguration) -> Optional[BaseChannelService]:
        """Get or create channel service instance"""
        try:
            service_key = f"{channel_config.creator_id}:{channel_config.id}"
            
            # Return existing service if available
            if service_key in self.active_services:
                return self.active_services[service_key]
            
            # Get service class for channel type
            service_class = self.service_registry.get(channel_config.channel_type)
            if not service_class:
                self.logger.error(f"No service registered for channel type: {channel_config.channel_type}")
                return None
            
            # Create new service instance
            service = service_class(channel_config, self.db_session)
            
            # Validate configuration
            if not await service.validate_configuration():
                self.logger.error(f"Invalid configuration for channel {channel_config.id}")
                return None
            
            # Cache service instance
            self.active_services[service_key] = service
            self.logger.info(f"Created channel service: {service_key} ({channel_config.channel_type})")
            
            return service
            
        except Exception as e:
            self.logger.error(f"Failed to get channel service: {e}")
            return None
    
    async def send_message(self, channel_id: str, creator_id: str, message_data: Dict[str, Any]) -> Dict[str, Any]:
        """Send message through specified channel"""
        try:
            # Get channel configuration
            channel_config = await self._get_channel_config(channel_id, creator_id)
            if not channel_config:
                return {
                    "success": False,
                    "error": "Channel not found or not accessible",
                    "status": "not_found"
                }
            
            # Check if channel is active
            if not channel_config.is_active:
                return {
                    "success": False,
                    "error": "Channel is disabled",
                    "status": "disabled"
                }
            
            # Get channel service
            service = await self.get_channel_service(channel_config)
            if not service:
                return {
                    "success": False,
                    "error": "Channel service unavailable",
                    "status": "service_unavailable"
                }
            
            # Create outbound message
            from .models import OutboundMessage
            outbound_message = OutboundMessage(**message_data)
            
            # Send message
            result = await service.send_message(outbound_message)
            
            self.logger.info(f"Message sent via {channel_config.channel_type}: {result}")
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to send message: {e}")
            return {
                "success": False,
                "error": str(e),
                "status": "error"
            }
    
    async def process_webhook(self, channel_id: str, creator_id: str, webhook_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Process webhook event for specified channel"""
        try:
            # Get channel configuration
            channel_config = await self._get_channel_config(channel_id, creator_id)
            if not channel_config:
                self.logger.warning(f"Webhook received for unknown channel: {channel_id}")
                return None
            
            # Get channel service
            service = await self.get_channel_service(channel_config)
            if not service:
                self.logger.error(f"No service available for channel: {channel_id}")
                return None
            
            # Process webhook
            inbound_message = await service.process_webhook(webhook_data)
            
            if inbound_message:
                self.logger.info(f"Processed webhook for {channel_config.channel_type}: {inbound_message.conversation_id}")
                
                # Return processed message data for AI processing
                return {
                    "message": inbound_message.dict(),
                    "channel_config": channel_config.dict(),
                    "requires_ai_processing": True
                }
            
            return None
            
        except Exception as e:
            self.logger.error(f"Failed to process webhook: {e}")
            return None
    
    async def check_channel_health(self, channel_id: str, creator_id: str) -> Dict[str, Any]:
        """Check health of specified channel"""
        try:
            # Get channel configuration
            channel_config = await self._get_channel_config(channel_id, creator_id)
            if not channel_config:
                return {
                    "status": "not_found",
                    "error": "Channel not found"
                }
            
            # Get channel service
            service = await self.get_channel_service(channel_config)
            if not service:
                return {
                    "status": "service_unavailable",
                    "error": "Channel service unavailable"
                }
            
            # Check health
            health_result = await service.check_health()
            health_result["channel_id"] = channel_id
            health_result["channel_type"] = channel_config.channel_type
            
            return health_result
            
        except Exception as e:
            self.logger.error(f"Failed to check channel health: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def setup_channel_webhook(self, channel_id: str, creator_id: str, webhook_url: str) -> bool:
        """Setup webhook for specified channel"""
        try:
            # Get channel configuration
            channel_config = await self._get_channel_config(channel_id, creator_id)
            if not channel_config:
                return False
            
            # Get channel service
            service = await self.get_channel_service(channel_config)
            if not service:
                return False
            
            # Setup webhook
            result = await service.setup_webhook(webhook_url)
            
            if result:
                # Update webhook URL in configuration
                await self._update_webhook_url(channel_id, creator_id, webhook_url)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to setup channel webhook: {e}")
            return False
    
    async def get_active_channels(self, creator_id: str) -> List[Dict[str, Any]]:
        """Get all active channels for a creator"""
        try:
            from shared.models.database import ChannelConfiguration as DBChannelConfig
            from sqlalchemy import select
            
            query = (
                select(DBChannelConfig)
                .where(DBChannelConfig.creator_id == creator_id)
                .where(DBChannelConfig.is_active == True)
                .order_by(DBChannelConfig.created_at)
            )
            
            result = await self.db_session.execute(query)
            channels = result.scalars().all()
            
            channel_list = []
            for channel in channels:
                channel_info = {
                    "id": str(channel.id),
                    "channel_type": channel.channel_type,
                    "channel_name": channel.channel_name,
                    "health_status": channel.health_status,
                    "last_health_check": channel.last_health_check.isoformat() if channel.last_health_check else None,
                    "daily_count": channel.current_daily_count,
                    "monthly_count": channel.current_monthly_count,
                    "daily_limit": channel.daily_message_limit,
                    "monthly_limit": channel.monthly_message_limit,
                    "created_at": channel.created_at.isoformat()
                }
                
                # Add service-specific information
                service = await self.get_channel_service(ChannelConfiguration.from_orm(channel))
                if service:
                    health_info = await service.check_health()
                    channel_info["service_health"] = health_info
                
                channel_list.append(channel_info)
            
            return channel_list
            
        except Exception as e:
            self.logger.error(f"Failed to get active channels: {e}")
            return []
    
    async def cleanup_inactive_services(self):
        """Cleanup inactive service instances"""
        try:
            # Remove services for inactive channels
            inactive_keys = []
            
            for service_key, service in self.active_services.items():
                if not service.channel_config.is_active:
                    inactive_keys.append(service_key)
            
            for key in inactive_keys:
                del self.active_services[key]
                self.logger.info(f"Removed inactive service: {key}")
                
        except Exception as e:
            self.logger.error(f"Failed to cleanup inactive services: {e}")
    
    async def _get_channel_config(self, channel_id: str, creator_id: str) -> Optional[ChannelConfiguration]:
        """Get channel configuration from database"""
        try:
            from shared.models.database import ChannelConfiguration as DBChannelConfig
            from sqlalchemy import select
            
            query = (
                select(DBChannelConfig)
                .where(DBChannelConfig.id == channel_id)
                .where(DBChannelConfig.creator_id == creator_id)
            )
            
            result = await self.db_session.execute(query)
            channel = result.scalar_one_or_none()
            
            if channel:
                return ChannelConfiguration.from_orm(channel)
            
            return None
            
        except Exception as e:
            self.logger.error(f"Failed to get channel config: {e}")
            return None
    
    async def _update_webhook_url(self, channel_id: str, creator_id: str, webhook_url: str) -> bool:
        """Update webhook URL in database"""
        try:
            from shared.models.database import ChannelConfiguration as DBChannelConfig
            from sqlalchemy import update
            
            stmt = (
                update(DBChannelConfig)
                .where(DBChannelConfig.id == channel_id)
                .where(DBChannelConfig.creator_id == creator_id)
                .values(webhook_url=webhook_url)
            )
            
            result = await self.db_session.execute(stmt)
            await self.db_session.commit()
            
            return result.rowcount > 0
            
        except Exception as e:
            self.logger.error(f"Failed to update webhook URL: {e}")
            await self.db_session.rollback()
            return False
    
    def get_supported_channel_types(self) -> List[str]:
        """Get list of supported channel types"""
        return [channel_type.value for channel_type in self.service_registry.keys()]
    
    async def validate_webhook_signature(self, channel_id: str, creator_id: str, payload: str, signature: str) -> bool:
        """Validate webhook signature for specified channel"""
        try:
            # Get channel configuration
            channel_config = await self._get_channel_config(channel_id, creator_id)
            if not channel_config:
                return False
            
            # Get channel service
            service = await self.get_channel_service(channel_config)
            if not service:
                return False
            
            # Validate signature
            secret = channel_config.webhook_secret or ""
            return service.validate_webhook_signature(payload, signature, secret)
            
        except Exception as e:
            self.logger.error(f"Failed to validate webhook signature: {e}")
            return False