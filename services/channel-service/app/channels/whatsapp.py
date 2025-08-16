"""
WhatsApp Business API Integration
Handles WhatsApp messaging through Meta's Business API
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
    WhatsAppConfiguration
)

logger = logging.getLogger(__name__)


class WhatsAppService(BaseChannelService):
    """
    WhatsApp Business API integration service
    Handles message sending, webhook processing, and health monitoring
    """
    
    def __init__(self, channel_config, db_session):
        super().__init__(channel_config, db_session)
        self.api_base_url = "https://graph.facebook.com"
        self.config = WhatsAppConfiguration(**channel_config.configuration)
        self.headers = {
            "Authorization": f"Bearer {channel_config.api_token}",
            "Content-Type": "application/json"
        }
    
    @property
    def channel_type(self) -> str:
        return ChannelType.WHATSAPP
    
    async def validate_configuration(self) -> bool:
        """Validate WhatsApp Business API configuration"""
        try:
            required_fields = ["phone_number_id", "business_account_id", "webhook_verify_token"]
            
            for field in required_fields:
                if not getattr(self.config, field, None):
                    self.logger.error(f"Missing required WhatsApp configuration: {field}")
                    return False
            
            if not self.channel_config.api_token:
                self.logger.error("Missing WhatsApp API token")
                return False
            
            # Test API connectivity
            health_check = await self.check_health()
            return health_check.get("status") == "healthy"
            
        except Exception as e:
            self.logger.error(f"WhatsApp configuration validation failed: {e}")
            return False
    
    async def send_message(self, message: OutboundMessage) -> Dict[str, Any]:
        """Send message through WhatsApp Business API"""
        try:
            # Check rate limits
            if not await self.check_rate_limits():
                return {
                    "success": False,
                    "error": "Rate limit exceeded",
                    "status": "rate_limited"
                }
            
            # Prepare API request
            url = f"{self.api_base_url}/{self.config.api_version}/{self.config.phone_number_id}/messages"
            
            payload = {
                "messaging_product": "whatsapp",
                "to": message.user_identifier,
                "type": self._get_whatsapp_message_type(message.message_type),
            }
            
            # Add message content based on type
            if message.message_type == MessageType.TEXT:
                payload["text"] = {"body": message.content}
            elif message.message_type == MessageType.IMAGE:
                payload["image"] = {
                    "link": message.content,
                    "caption": message.channel_metadata.get("caption", "")
                }
            elif message.message_type == MessageType.DOCUMENT:
                payload["document"] = {
                    "link": message.content,
                    "filename": message.channel_metadata.get("filename", "document")
                }
            
            # Send message
            async with httpx.AsyncClient() as client:
                response = await client.post(url, headers=self.headers, json=payload)
                response_data = response.json()
            
            if response.status_code == 200 and response_data.get("messages"):
                # Message sent successfully
                whatsapp_message_id = response_data["messages"][0]["id"]
                
                # Save message to database
                message_data = {
                    "conversation_id": message.conversation_id,
                    "content": message.content,
                    "message_type": message.message_type,
                    "external_message_id": whatsapp_message_id,
                    "channel_metadata": {
                        **message.channel_metadata,
                        "whatsapp_response": response_data
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
                    "external_message_id": whatsapp_message_id,
                    "status": "sent"
                }
            else:
                # Message failed
                error_message = response_data.get("error", {}).get("message", "Unknown error")
                self.logger.error(f"WhatsApp message failed: {error_message}")
                
                return {
                    "success": False,
                    "error": error_message,
                    "status": "failed",
                    "error_code": response_data.get("error", {}).get("code")
                }
                
        except Exception as e:
            self.logger.error(f"Failed to send WhatsApp message: {e}")
            return {
                "success": False,
                "error": str(e),
                "status": "error"
            }
    
    async def process_webhook(self, webhook_data: Dict[str, Any]) -> Optional[InboundMessage]:
        """Process WhatsApp webhook event"""
        try:
            # Log webhook event
            await self.log_webhook_event(webhook_data, "message_received")
            
            # Extract message data from webhook
            entry = webhook_data.get("entry", [{}])[0]
            changes = entry.get("changes", [{}])[0]
            value = changes.get("value", {})
            
            if not value.get("messages"):
                self.logger.debug("Webhook event is not a message")
                return None
            
            message_data = value["messages"][0]
            contact_data = value.get("contacts", [{}])[0]
            
            # Extract user information
            user_identifier = message_data.get("from")
            user_name = contact_data.get("profile", {}).get("name", "Unknown User")
            
            # Get conversation ID
            conversation_id = await self.get_conversation_id(user_identifier)
            
            # Extract message content based on type
            content, message_type = self._extract_message_content(message_data)
            
            # Create inbound message
            inbound_message = InboundMessage(
                content=content,
                message_type=message_type,
                conversation_id=conversation_id,
                external_message_id=message_data.get("id"),
                channel_metadata={
                    "whatsapp_data": message_data,
                    "contact_data": contact_data,
                    "webhook_data": value
                },
                user_identifier=user_identifier,
                user_name=user_name,
                user_metadata={
                    "profile": contact_data.get("profile", {}),
                    "wa_id": contact_data.get("wa_id")
                },
                received_at=datetime.utcnow()
            )
            
            # Save message to database
            message_data = {
                "conversation_id": conversation_id,
                "content": content,
                "message_type": message_type,
                "external_message_id": message_data.get("id"),
                "channel_metadata": inbound_message.channel_metadata,
                "user_identifier": user_identifier,
                "user_name": user_name,
                "user_metadata": inbound_message.user_metadata
            }
            
            await self.save_message(message_data, MessageDirection.INBOUND)
            
            return inbound_message
            
        except Exception as e:
            self.logger.error(f"Failed to process WhatsApp webhook: {e}")
            return None
    
    async def check_health(self) -> Dict[str, Any]:
        """Check WhatsApp Business API health"""
        try:
            url = f"{self.api_base_url}/{self.config.api_version}/{self.config.phone_number_id}"
            
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=self.headers)
            
            if response.status_code == 200:
                data = response.json()
                await self.update_health_status(HealthStatus.HEALTHY)
                
                return {
                    "status": "healthy",
                    "phone_number": data.get("display_phone_number"),
                    "verified_name": data.get("verified_name"),
                    "quality_rating": data.get("quality_rating"),
                    "last_check": datetime.utcnow().isoformat()
                }
            else:
                error_message = f"API returned status {response.status_code}"
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
        """Setup webhook URL with WhatsApp Business API"""
        try:
            # WhatsApp webhooks are typically set up through the Meta App Dashboard
            # This method would be used to verify webhook setup programmatically
            
            self.logger.info(f"WhatsApp webhook should be configured manually in Meta App Dashboard")
            self.logger.info(f"Webhook URL: {webhook_url}")
            self.logger.info(f"Verify Token: {self.config.webhook_verify_token}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to setup WhatsApp webhook: {e}")
            return False
    
    def validate_webhook_signature(self, payload: str, signature: str, secret: str) -> bool:
        """Validate WhatsApp webhook signature"""
        try:
            # WhatsApp uses SHA256 HMAC
            expected_signature = hmac.new(
                secret.encode(),
                payload.encode(),
                hashlib.sha256
            ).hexdigest()
            
            # Remove 'sha256=' prefix if present
            if signature.startswith("sha256="):
                signature = signature[7:]
            
            return hmac.compare_digest(expected_signature, signature)
            
        except Exception as e:
            self.logger.error(f"Failed to validate WhatsApp webhook signature: {e}")
            return False
    
    def _get_whatsapp_message_type(self, message_type: MessageType) -> str:
        """Convert internal message type to WhatsApp API type"""
        type_mapping = {
            MessageType.TEXT: "text",
            MessageType.IMAGE: "image",
            MessageType.AUDIO: "audio",
            MessageType.VIDEO: "video",
            MessageType.DOCUMENT: "document",
            MessageType.LOCATION: "location",
            MessageType.CONTACT: "contacts"
        }
        return type_mapping.get(message_type, "text")
    
    def _extract_message_content(self, message_data: Dict[str, Any]) -> tuple[str, MessageType]:
        """Extract content and type from WhatsApp message data"""
        message_type_str = message_data.get("type", "text")
        
        if message_type_str == "text":
            content = message_data.get("text", {}).get("body", "")
            return content, MessageType.TEXT
        
        elif message_type_str == "image":
            image_data = message_data.get("image", {})
            content = image_data.get("id", "")  # Media ID
            return content, MessageType.IMAGE
        
        elif message_type_str == "audio":
            audio_data = message_data.get("audio", {})
            content = audio_data.get("id", "")  # Media ID
            return content, MessageType.AUDIO
        
        elif message_type_str == "video":
            video_data = message_data.get("video", {})
            content = video_data.get("id", "")  # Media ID
            return content, MessageType.VIDEO
        
        elif message_type_str == "document":
            document_data = message_data.get("document", {})
            content = document_data.get("id", "")  # Media ID
            return content, MessageType.DOCUMENT
        
        elif message_type_str == "location":
            location_data = message_data.get("location", {})
            latitude = location_data.get("latitude")
            longitude = location_data.get("longitude")
            content = f"{latitude},{longitude}"
            return content, MessageType.LOCATION
        
        elif message_type_str == "contacts":
            contacts_data = message_data.get("contacts", [])
            content = json.dumps(contacts_data)
            return content, MessageType.CONTACT
        
        else:
            # Fallback for unknown types
            content = f"Unsupported message type: {message_type_str}"
            return content, MessageType.TEXT
    
    async def download_media(self, media_id: str) -> Optional[Dict[str, Any]]:
        """Download media file from WhatsApp"""
        try:
            # Get media URL
            url = f"{self.api_base_url}/{self.config.api_version}/{media_id}"
            
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=self.headers)
                
                if response.status_code == 200:
                    media_info = response.json()
                    media_url = media_info.get("url")
                    
                    if media_url:
                        # Download actual media file
                        media_response = await client.get(media_url, headers=self.headers)
                        
                        if media_response.status_code == 200:
                            return {
                                "content": media_response.content,
                                "content_type": media_response.headers.get("content-type"),
                                "filename": media_info.get("filename"),
                                "size": len(media_response.content)
                            }
            
            return None
            
        except Exception as e:
            self.logger.error(f"Failed to download WhatsApp media {media_id}: {e}")
            return None