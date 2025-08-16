"""
Telegram Bot API Integration
Handles Telegram messaging through Bot API
"""

import hmac
import hashlib
import json
import logging
from typing import Dict, List, Optional, Any
import httpx
from datetime import datetime

from .base import BaseChannelService
from ..models import (
    InboundMessage, 
    OutboundMessage, 
    ChannelType,
    MessageType,
    MessageDirection,
    HealthStatus,
    TelegramConfiguration
)

logger = logging.getLogger(__name__)


class TelegramService(BaseChannelService):
    """
    Telegram Bot API integration service
    Handles message sending, webhook processing, and health monitoring
    """
    
    def __init__(self, channel_config, db_session):
        super().__init__(channel_config, db_session)
        self.api_base_url = f"https://api.telegram.org/bot{channel_config.api_token}"
        self.config = TelegramConfiguration(**channel_config.configuration)
    
    @property
    def channel_type(self) -> str:
        return ChannelType.TELEGRAM
    
    async def validate_configuration(self) -> bool:
        """Validate Telegram Bot API configuration"""
        try:
            required_fields = ["bot_username"]
            
            for field in required_fields:
                if not getattr(self.config, field, None):
                    self.logger.error(f"Missing required Telegram configuration: {field}")
                    return False
            
            if not self.channel_config.api_token:
                self.logger.error("Missing Telegram bot token")
                return False
            
            # Test API connectivity
            health_check = await self.check_health()
            return health_check.get("status") == "healthy"
            
        except Exception as e:
            self.logger.error(f"Telegram configuration validation failed: {e}")
            return False
    
    async def send_message(self, message: OutboundMessage) -> Dict[str, Any]:
        """Send message through Telegram Bot API"""
        try:
            # Check rate limits
            if not await self.check_rate_limits():
                return {
                    "success": False,
                    "error": "Rate limit exceeded",
                    "status": "rate_limited"
                }
            
            # Prepare API request based on message type
            if message.message_type == MessageType.TEXT:
                url = f"{self.api_base_url}/sendMessage"
                payload = {
                    "chat_id": message.user_identifier,
                    "text": message.content,
                    "parse_mode": message.channel_metadata.get("parse_mode", "Markdown")
                }
            
            elif message.message_type == MessageType.IMAGE:
                url = f"{self.api_base_url}/sendPhoto"
                payload = {
                    "chat_id": message.user_identifier,
                    "photo": message.content,
                    "caption": message.channel_metadata.get("caption", "")
                }
            
            elif message.message_type == MessageType.DOCUMENT:
                url = f"{self.api_base_url}/sendDocument"
                payload = {
                    "chat_id": message.user_identifier,
                    "document": message.content,
                    "caption": message.channel_metadata.get("caption", "")
                }
            
            elif message.message_type == MessageType.AUDIO:
                url = f"{self.api_base_url}/sendAudio"
                payload = {
                    "chat_id": message.user_identifier,
                    "audio": message.content,
                    "caption": message.channel_metadata.get("caption", "")
                }
            
            elif message.message_type == MessageType.VIDEO:
                url = f"{self.api_base_url}/sendVideo"
                payload = {
                    "chat_id": message.user_identifier,
                    "video": message.content,
                    "caption": message.channel_metadata.get("caption", "")
                }
            
            elif message.message_type == MessageType.LOCATION:
                url = f"{self.api_base_url}/sendLocation"
                coords = message.content.split(",")
                payload = {
                    "chat_id": message.user_identifier,
                    "latitude": float(coords[0]),
                    "longitude": float(coords[1])
                }
            
            else:
                # Default to text message
                url = f"{self.api_base_url}/sendMessage"
                payload = {
                    "chat_id": message.user_identifier,
                    "text": message.content
                }
            
            # Add reply markup if specified
            if "reply_markup" in message.channel_metadata:
                payload["reply_markup"] = message.channel_metadata["reply_markup"]
            
            # Send message
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=payload)
                response_data = response.json()
            
            if response.status_code == 200 and response_data.get("ok"):
                # Message sent successfully
                telegram_message = response_data["result"]
                telegram_message_id = telegram_message["message_id"]
                
                # Save message to database
                message_data = {
                    "conversation_id": message.conversation_id,
                    "content": message.content,
                    "message_type": message.message_type,
                    "external_message_id": str(telegram_message_id),
                    "channel_metadata": {
                        **message.channel_metadata,
                        "telegram_response": response_data
                    },
                    "user_identifier": message.user_identifier,
                    "user_name": message.user_name,
                    "user_metadata": message.user_metadata
                }
                
                message_id = await self.save_message(message_data, MessageDirection.OUTBOUND)
                await self.increment_message_count()
                
                return {
                    "success": True,
                    "message_id": message_id,
                    "external_message_id": str(telegram_message_id),
                    "status": "sent"
                }
            else:
                # Message failed
                error_message = response_data.get("description", "Unknown error")
                self.logger.error(f"Telegram message failed: {error_message}")
                
                return {
                    "success": False,
                    "error": error_message,
                    "status": "failed",
                    "error_code": response_data.get("error_code")
                }
                
        except Exception as e:
            self.logger.error(f"Failed to send Telegram message: {e}")
            return {
                "success": False,
                "error": str(e),
                "status": "error"
            }
    
    async def process_webhook(self, webhook_data: Dict[str, Any]) -> Optional[InboundMessage]:
        """Process Telegram webhook update"""
        try:
            # Log webhook event
            await self.log_webhook_event(webhook_data, "update_received")
            
            # Check if this is a message update
            if "message" not in webhook_data:
                self.logger.debug("Webhook update is not a message")
                return None
            
            message_data = webhook_data["message"]
            
            # Extract user information
            user_data = message_data.get("from", {})
            chat_data = message_data.get("chat", {})
            
            user_identifier = str(user_data.get("id"))
            user_name = user_data.get("first_name", "")
            if user_data.get("last_name"):
                user_name += f" {user_data['last_name']}"
            
            # Get conversation ID
            conversation_id = await self.get_conversation_id(user_identifier)
            
            # Extract message content based on type
            content, message_type = self._extract_message_content(message_data)
            
            # Create inbound message
            inbound_message = InboundMessage(
                content=content,
                message_type=message_type,
                conversation_id=conversation_id,
                external_message_id=str(message_data.get("message_id")),
                channel_metadata={
                    "telegram_data": message_data,
                    "chat_data": chat_data,
                    "webhook_data": webhook_data
                },
                user_identifier=user_identifier,
                user_name=user_name,
                user_metadata={
                    "user_data": user_data,
                    "chat_type": chat_data.get("type"),
                    "is_bot": user_data.get("is_bot", False),
                    "language_code": user_data.get("language_code")
                },
                received_at=datetime.fromtimestamp(message_data.get("date", 0))
            )
            
            # Save message to database
            message_data = {
                "conversation_id": conversation_id,
                "content": content,
                "message_type": message_type,
                "external_message_id": str(message_data.get("message_id")),
                "channel_metadata": inbound_message.channel_metadata,
                "user_identifier": user_identifier,
                "user_name": user_name,
                "user_metadata": inbound_message.user_metadata
            }
            
            await self.save_message(message_data, MessageDirection.INBOUND)
            
            # Process message with AI and generate response
            try:
                ai_response = await self.process_message_with_ai(inbound_message, conversation_id)
                
                if ai_response:
                    # Send AI response back to user
                    send_result = await self.send_message(ai_response)
                    
                    if send_result.get("success"):
                        self.logger.info(f"Sent AI response for conversation {conversation_id}")
                    else:
                        self.logger.error(f"Failed to send AI response: {send_result.get('error')}")
                else:
                    self.logger.warning(f"No AI response generated for conversation {conversation_id}")
                    
            except Exception as e:
                self.logger.error(f"Failed to process message with AI: {e}")
                # Continue processing even if AI fails
            
            return inbound_message
            
        except Exception as e:
            self.logger.error(f"Failed to process Telegram webhook: {e}")
            return None
    
    async def check_health(self) -> Dict[str, Any]:
        """Check Telegram Bot API health"""
        try:
            url = f"{self.api_base_url}/getMe"
            
            async with httpx.AsyncClient() as client:
                response = await client.get(url)
                response_data = response.json()
            
            if response.status_code == 200 and response_data.get("ok"):
                bot_info = response_data["result"]
                await self.update_health_status(HealthStatus.HEALTHY)
                
                return {
                    "status": "healthy",
                    "bot_username": bot_info.get("username"),
                    "bot_name": bot_info.get("first_name"),
                    "can_join_groups": bot_info.get("can_join_groups"),
                    "can_read_all_group_messages": bot_info.get("can_read_all_group_messages"),
                    "supports_inline_queries": bot_info.get("supports_inline_queries"),
                    "last_check": datetime.utcnow().isoformat()
                }
            else:
                error_message = response_data.get("description", f"API returned status {response.status_code}")
                await self.update_health_status(HealthStatus.ERROR, error_message)
                
                return {
                    "status": "error",
                    "error": error_message,
                    "last_check": datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            error_message = f"Health check failed: {str(e)}"
            await self.update_health_status(HealthStatus.ERROR, error_message)
            
            return {
                "status": "error",
                "error": error_message,
                "last_check": datetime.utcnow().isoformat()
            }
    
    async def setup_webhook(self, webhook_url: str) -> bool:
        """Setup webhook URL with Telegram Bot API"""
        try:
            url = f"{self.api_base_url}/setWebhook"
            
            payload = {
                "url": webhook_url,
                "allowed_updates": self.config.allowed_updates,
                "max_connections": self.config.max_connections
            }
            
            # Add secret token if configured
            if self.config.webhook_secret_token:
                payload["secret_token"] = self.config.webhook_secret_token
            
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=payload)
                response_data = response.json()
            
            if response.status_code == 200 and response_data.get("ok"):
                self.logger.info(f"Telegram webhook set successfully: {webhook_url}")
                return True
            else:
                error_message = response_data.get("description", "Unknown error")
                self.logger.error(f"Failed to set Telegram webhook: {error_message}")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to setup Telegram webhook: {e}")
            return False
    
    def validate_webhook_signature(self, payload: str, signature: str, secret: str) -> bool:
        """Validate Telegram webhook signature"""
        try:
            if not self.config.webhook_secret_token:
                self.logger.warning("No webhook secret token configured for Telegram")
                return True
            
            # Telegram uses HMAC-SHA256
            expected_signature = hmac.new(
                secret.encode(),
                payload.encode(),
                hashlib.sha256
            ).hexdigest()
            
            return hmac.compare_digest(expected_signature, signature)
            
        except Exception as e:
            self.logger.error(f"Failed to validate Telegram webhook signature: {e}")
            return False
    
    def _extract_message_content(self, message_data: Dict[str, Any]) -> tuple[str, MessageType]:
        """Extract content and type from Telegram message data"""
        
        if "text" in message_data:
            return message_data["text"], MessageType.TEXT
        
        elif "photo" in message_data:
            # Get the largest photo size
            photos = message_data["photo"]
            largest_photo = max(photos, key=lambda p: p.get("file_size", 0))
            return largest_photo["file_id"], MessageType.IMAGE
        
        elif "audio" in message_data:
            return message_data["audio"]["file_id"], MessageType.AUDIO
        
        elif "video" in message_data:
            return message_data["video"]["file_id"], MessageType.VIDEO
        
        elif "document" in message_data:
            return message_data["document"]["file_id"], MessageType.DOCUMENT
        
        elif "location" in message_data:
            location = message_data["location"]
            content = f"{location['latitude']},{location['longitude']}"
            return content, MessageType.LOCATION
        
        elif "contact" in message_data:
            contact = message_data["contact"]
            content = json.dumps(contact)
            return content, MessageType.CONTACT
        
        elif "voice" in message_data:
            return message_data["voice"]["file_id"], MessageType.AUDIO
        
        elif "video_note" in message_data:
            return message_data["video_note"]["file_id"], MessageType.VIDEO
        
        elif "sticker" in message_data:
            return message_data["sticker"]["file_id"], MessageType.IMAGE
        
        else:
            # Fallback for unknown types
            content = f"Unsupported message type"
            return content, MessageType.TEXT
    
    async def download_file(self, file_id: str) -> Optional[Dict[str, Any]]:
        """Download file from Telegram"""
        try:
            # Get file info
            url = f"{self.api_base_url}/getFile"
            payload = {"file_id": file_id}
            
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=payload)
                response_data = response.json()
                
                if response.status_code == 200 and response_data.get("ok"):
                    file_info = response_data["result"]
                    file_path = file_info.get("file_path")
                    
                    if file_path:
                        # Download actual file
                        file_url = f"https://api.telegram.org/file/bot{self.channel_config.api_token}/{file_path}"
                        file_response = await client.get(file_url)
                        
                        if file_response.status_code == 200:
                            return {
                                "content": file_response.content,
                                "content_type": file_response.headers.get("content-type"),
                                "file_path": file_path,
                                "size": file_info.get("file_size", len(file_response.content))
                            }
            
            return None
            
        except Exception as e:
            self.logger.error(f"Failed to download Telegram file {file_id}: {e}")
            return None
    
    async def get_webhook_info(self) -> Dict[str, Any]:
        """Get current webhook information"""
        try:
            url = f"{self.api_base_url}/getWebhookInfo"
            
            async with httpx.AsyncClient() as client:
                response = await client.get(url)
                response_data = response.json()
            
            if response.status_code == 200 and response_data.get("ok"):
                return response_data["result"]
            else:
                self.logger.error(f"Failed to get webhook info: {response_data}")
                return {}
                
        except Exception as e:
            self.logger.error(f"Failed to get Telegram webhook info: {e}")
            return {}