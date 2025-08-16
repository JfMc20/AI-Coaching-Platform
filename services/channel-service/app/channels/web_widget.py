"""
Web Widget Integration
Handles web widget messaging through WebSocket and HTTP API
"""

import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import secrets

from .base import BaseChannelService
from ..models import (
    InboundMessage, 
    OutboundMessage, 
    ChannelType,
    MessageType,
    MessageDirection,
    HealthStatus,
    WebWidgetConfiguration
)

logger = logging.getLogger(__name__)


class WebWidgetService(BaseChannelService):
    """
    Web Widget integration service
    Handles widget embedding, WebSocket connections, and message processing
    """
    
    def __init__(self, channel_config, db_session):
        super().__init__(channel_config, db_session)
        self.config = WebWidgetConfiguration(**channel_config.configuration)
        self.active_sessions: Dict[str, Dict[str, Any]] = {}
    
    @property
    def channel_type(self) -> str:
        return ChannelType.WEB_WIDGET
    
    async def validate_configuration(self) -> bool:
        """Validate Web Widget configuration"""
        try:
            # Check required configuration
            if not self.config.theme_color:
                self.logger.error("Missing theme color in Web Widget configuration")
                return False
            
            if not self.config.welcome_message:
                self.logger.error("Missing welcome message in Web Widget configuration")
                return False
            
            # Validate rate limits
            if self.config.rate_limit_messages <= 0 or self.config.rate_limit_messages > 100:
                self.logger.error("Invalid rate limit configuration")
                return False
            
            # Validate allowed domains if specified
            if self.config.allowed_domains:
                for domain in self.config.allowed_domains:
                    if not isinstance(domain, str) or not domain.strip():
                        self.logger.error(f"Invalid domain in allowed_domains: {domain}")
                        return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Web Widget configuration validation failed: {e}")
            return False
    
    async def send_message(self, message: OutboundMessage) -> Dict[str, Any]:
        """Send message through Web Widget (WebSocket or polling)"""
        try:
            # Check rate limits
            if not await self.check_rate_limits():
                return {
                    "success": False,
                    "error": "Rate limit exceeded",
                    "status": "rate_limited"
                }
            
            # Save message to database
            message_data = {
                "conversation_id": message.conversation_id,
                "content": message.content,
                "message_type": message.message_type,
                "external_message_id": None,  # Generated after saving
                "channel_metadata": {
                    **message.channel_metadata,
                    "widget_config": {
                        "theme_color": self.config.theme_color,
                        "enable_file_upload": self.config.enable_file_upload
                    }
                },
                "user_identifier": message.user_identifier,
                "user_name": message.user_name,
                "user_metadata": message.user_metadata
            }
            
            message_id = await self.save_message(message_data, MessageDirection.OUTBOUND)
            await self.increment_message_count()
            
            # Try to send via WebSocket if session is active
            session_info = self.active_sessions.get(message.user_identifier)
            if session_info and session_info.get("websocket"):
                try:
                    websocket = session_info["websocket"]
                    websocket_message = {
                        "type": "message",
                        "id": message_id,
                        "content": message.content,
                        "message_type": message.message_type.value,
                        "timestamp": datetime.utcnow().isoformat(),
                        "from": "assistant"
                    }
                    
                    await websocket.send_json(websocket_message)
                    
                    # Update message status
                    await self.update_message_status(message_id, {
                        "delivery_status": "delivered",
                        "delivered_at": datetime.utcnow()
                    })
                    
                    return {
                        "success": True,
                        "message_id": message_id,
                        "status": "delivered",
                        "delivery_method": "websocket"
                    }
                    
                except Exception as ws_error:
                    self.logger.warning(f"WebSocket delivery failed, message queued: {ws_error}")
                    # Message is saved, client will get it via polling
            
            # Message queued for polling retrieval
            return {
                "success": True,
                "message_id": message_id,
                "status": "queued",
                "delivery_method": "polling"
            }
                
        except Exception as e:
            self.logger.error(f"Failed to send Web Widget message: {e}")
            return {
                "success": False,
                "error": str(e),
                "status": "error"
            }
    
    async def process_webhook(self, webhook_data: Dict[str, Any]) -> Optional[InboundMessage]:
        """Process Web Widget message (from HTTP API or WebSocket)"""
        try:
            # Log webhook event
            await self.log_webhook_event(webhook_data, "widget_message")
            
            # Extract message data
            message_content = webhook_data.get("content", "")
            message_type = webhook_data.get("message_type", "text")
            session_id = webhook_data.get("session_id")
            user_identifier = webhook_data.get("user_identifier", session_id)
            
            if not message_content or not user_identifier:
                self.logger.warning("Missing required fields in widget message")
                return None
            
            # Get conversation ID
            conversation_id = await self.get_conversation_id(user_identifier)
            
            # Extract user information
            user_name = webhook_data.get("user_name", "Website Visitor")
            user_metadata = {
                "session_id": session_id,
                "user_agent": webhook_data.get("user_agent"),
                "referrer": webhook_data.get("referrer"),
                "ip_address": webhook_data.get("ip_address"),
                "widget_data": webhook_data.get("widget_metadata", {})
            }
            
            # Create inbound message
            inbound_message = InboundMessage(
                content=message_content,
                message_type=MessageType(message_type),
                conversation_id=conversation_id,
                external_message_id=webhook_data.get("client_message_id"),
                channel_metadata={
                    "widget_data": webhook_data,
                    "session_info": self.active_sessions.get(user_identifier, {}),
                    "domain": webhook_data.get("domain"),
                    "page_url": webhook_data.get("page_url")
                },
                user_identifier=user_identifier,
                user_name=user_name,
                user_metadata=user_metadata,
                received_at=datetime.utcnow()
            )
            
            # Save message to database
            message_data = {
                "conversation_id": conversation_id,
                "content": message_content,
                "message_type": message_type,
                "external_message_id": webhook_data.get("client_message_id"),
                "channel_metadata": inbound_message.channel_metadata,
                "user_identifier": user_identifier,
                "user_name": user_name,
                "user_metadata": user_metadata
            }
            
            await self.save_message(message_data, MessageDirection.INBOUND)
            
            return inbound_message
            
        except Exception as e:
            self.logger.error(f"Failed to process Web Widget webhook: {e}")
            return None
    
    async def check_health(self) -> Dict[str, Any]:
        """Check Web Widget health"""
        try:
            await self.update_health_status(HealthStatus.HEALTHY)
            
            return {
                "status": "healthy",
                "active_sessions": len(self.active_sessions),
                "configuration": {
                    "theme_color": self.config.theme_color,
                    "welcome_message": self.config.welcome_message[:50] + "..." if len(self.config.welcome_message) > 50 else self.config.welcome_message,
                    "file_upload_enabled": self.config.enable_file_upload,
                    "voice_input_enabled": self.config.enable_voice_input,
                    "rate_limit": self.config.rate_limit_messages
                },
                "allowed_domains": self.config.allowed_domains,
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
        """Setup webhook URL for Web Widget (not applicable)"""
        try:
            # Web Widget doesn't need external webhook setup
            # It communicates directly with the channel service
            self.logger.info("Web Widget uses direct API communication, no webhook setup required")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to setup Web Widget webhook: {e}")
            return False
    
    def generate_embed_code(self, base_url: str) -> str:
        """Generate HTML embed code for the widget"""
        try:
            config_json = json.dumps({
                "channelId": self.channel_config.id,
                "creatorId": self.channel_config.creator_id,
                "theme": {
                    "primaryColor": self.config.theme_color,
                    "welcomeMessage": self.config.welcome_message,
                    "placeholderText": self.config.placeholder_text
                },
                "features": {
                    "fileUpload": self.config.enable_file_upload,
                    "voiceInput": self.config.enable_voice_input
                },
                "apiBaseUrl": base_url,
                "rateLimit": self.config.rate_limit_messages
            })
            
            embed_code = f"""
<!-- AI Coaching Widget -->
<div id="ai-coaching-widget"></div>
<script>
(function() {{
    var config = {config_json};
    var script = document.createElement('script');
    script.src = '{base_url}/static/widget/ai-coaching-widget.js';
    script.onload = function() {{
        if (window.AiCoachingWidget) {{
            window.AiCoachingWidget.init(config);
        }}
    }};
    document.head.appendChild(script);
    
    var style = document.createElement('link');
    style.rel = 'stylesheet';
    style.href = '{base_url}/static/widget/ai-coaching-widget.css';
    document.head.appendChild(style);
}})();
</script>
"""
            
            return embed_code.strip()
            
        except Exception as e:
            self.logger.error(f"Failed to generate embed code: {e}")
            return ""
    
    async def register_websocket_session(self, session_id: str, websocket, user_info: Dict[str, Any]):
        """Register WebSocket session for real-time messaging"""
        try:
            self.active_sessions[session_id] = {
                "websocket": websocket,
                "user_info": user_info,
                "connected_at": datetime.utcnow(),
                "last_activity": datetime.utcnow()
            }
            
            self.logger.info(f"Registered WebSocket session: {session_id}")
            
            # Send welcome message
            welcome_message = {
                "type": "welcome",
                "content": self.config.welcome_message,
                "config": {
                    "enable_file_upload": self.config.enable_file_upload,
                    "enable_voice_input": self.config.enable_voice_input,
                    "theme_color": self.config.theme_color
                },
                "timestamp": datetime.utcnow().isoformat()
            }
            
            await websocket.send_json(welcome_message)
            
        except Exception as e:
            self.logger.error(f"Failed to register WebSocket session: {e}")
    
    async def unregister_websocket_session(self, session_id: str):
        """Unregister WebSocket session"""
        try:
            if session_id in self.active_sessions:
                session_info = self.active_sessions.pop(session_id)
                duration = datetime.utcnow() - session_info["connected_at"]
                
                self.logger.info(f"Unregistered WebSocket session: {session_id} (duration: {duration})")
                
        except Exception as e:
            self.logger.error(f"Failed to unregister WebSocket session: {e}")
    
    async def update_session_activity(self, session_id: str):
        """Update last activity for session"""
        if session_id in self.active_sessions:
            self.active_sessions[session_id]["last_activity"] = datetime.utcnow()
    
    def validate_domain(self, domain: str) -> bool:
        """Validate if domain is allowed"""
        try:
            if not self.config.allowed_domains:
                # No domain restrictions
                return True
            
            # Check exact match and wildcard patterns
            for allowed_domain in self.config.allowed_domains:
                if allowed_domain == "*":
                    return True
                
                if allowed_domain.startswith("*."):
                    # Wildcard subdomain match
                    base_domain = allowed_domain[2:]
                    if domain.endswith(base_domain):
                        return True
                
                elif domain == allowed_domain:
                    # Exact match
                    return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Failed to validate domain: {e}")
            return False
    
    async def get_pending_messages(self, user_identifier: str, since: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """Get pending messages for polling clients"""
        try:
            from shared.models.database import Message as DBMessage
            from sqlalchemy import select, and_
            
            # Build query
            query = (
                select(DBMessage)
                .where(DBMessage.creator_id == self.channel_config.creator_id)
                .where(DBMessage.channel_config_id == self.channel_config.id)
                .where(DBMessage.user_identifier == user_identifier)
                .where(DBMessage.direction == MessageDirection.OUTBOUND)
                .where(DBMessage.delivery_status.in_(["pending", "queued"]))
                .order_by(DBMessage.created_at)
            )
            
            if since:
                query = query.where(DBMessage.created_at > since)
            
            result = await self.db_session.execute(query)
            messages = result.scalars().all()
            
            # Format messages for client
            formatted_messages = []
            for message in messages:
                formatted_messages.append({
                    "id": str(message.id),
                    "content": message.content,
                    "message_type": message.message_type,
                    "timestamp": message.created_at.isoformat(),
                    "from": "assistant"
                })
                
                # Mark as delivered
                await self.update_message_status(str(message.id), {
                    "delivery_status": "delivered",
                    "delivered_at": datetime.utcnow()
                })
            
            return formatted_messages
            
        except Exception as e:
            self.logger.error(f"Failed to get pending messages: {e}")
            return []
    
    def generate_session_token(self) -> str:
        """Generate secure session token"""
        return secrets.token_urlsafe(32)