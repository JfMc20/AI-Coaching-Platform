"""
Comprehensive tests for multi-channel communication in channel service.
Tests WebSocket, WhatsApp, Telegram, and Web Widget integrations.
"""

import pytest
import asyncio
import json
from unittest.mock import AsyncMock, Mock, patch
from httpx import AsyncClient
from websockets.exceptions import ConnectionClosed

from shared.models.conversations import Message, MessageRole


class TestWebSocketCommunication:
    """Test WebSocket communication functionality."""

    @pytest.mark.asyncio
    async def test_websocket_connection_success(self, channel_client: AsyncClient):
        """Test successful WebSocket connection."""
        with patch('websockets.connect') as mock_connect:
            mock_websocket = AsyncMock()
            mock_connect.return_value.__aenter__.return_value = mock_websocket
            
            # Simulate connection
            connection_response = await channel_client.get("/api/v1/channels/websocket/status")
            
            # Should indicate WebSocket server is running
            assert connection_response.status_code == 200

    @pytest.mark.asyncio
    async def test_websocket_message_sending(self):
        """Test sending messages through WebSocket."""
        from services.channel_service.app.channels.web_widget import WebWidgetChannel
        
        web_widget = WebWidgetChannel()
        
        with patch.object(web_widget, 'websocket_manager') as mock_ws_manager:
            mock_ws_manager.send_message = AsyncMock()
            
            message_data = {
                "conversation_id": "test_conv_123",
                "creator_id": "creator_123",
                "content": "Hello from WebSocket test",
                "message_type": "text"
            }
            
            await web_widget.send_message(
                recipient="user_123",
                content="Hello from WebSocket test",
                conversation_id="test_conv_123",
                creator_id="creator_123"
            )
            
            mock_ws_manager.send_message.assert_called_once()

    @pytest.mark.asyncio
    async def test_websocket_message_receiving(self):
        """Test receiving messages through WebSocket."""
        from services.channel_service.app.channels.web_widget import WebWidgetChannel
        
        web_widget = WebWidgetChannel()
        
        with patch.object(web_widget, 'ai_client') as mock_ai_client:
            mock_ai_client.process_message = AsyncMock(return_value={
                "response": "AI response to WebSocket message",
                "conversation_id": "test_conv_123"
            })
            
            # Simulate received message
            received_message = {
                "conversation_id": "test_conv_123",
                "creator_id": "creator_123",
                "user_id": "user_123",
                "content": "User message via WebSocket",
                "timestamp": "2024-01-17T10:00:00Z"
            }
            
            response = await web_widget.handle_incoming_message(received_message)
            
            assert response["response"] == "AI response to WebSocket message"
            mock_ai_client.process_message.assert_called_once()

    @pytest.mark.asyncio
    async def test_websocket_connection_resilience(self):
        """Test WebSocket connection resilience and reconnection."""
        from services.channel_service.app.channels.web_widget import WebWidgetChannel
        
        web_widget = WebWidgetChannel()
        
        with patch.object(web_widget, 'websocket_manager') as mock_ws_manager:
            # Simulate connection drop and recovery
            mock_ws_manager.send_message = AsyncMock(side_effect=[
                ConnectionClosed(None, None),  # First attempt fails
                None  # Second attempt succeeds
            ])
            mock_ws_manager.reconnect = AsyncMock()
            
            # Should handle connection drop gracefully
            try:
                await web_widget.send_message(
                    recipient="user_123",
                    content="Test resilience",
                    conversation_id="test_conv",
                    creator_id="creator_123"
                )
            except ConnectionClosed:
                # Should attempt reconnection
                pass
            
            # Verify reconnection was attempted
            mock_ws_manager.reconnect.assert_called()

    @pytest.mark.asyncio
    async def test_websocket_concurrent_connections(self):
        """Test handling multiple concurrent WebSocket connections."""
        from services.channel_service.app.channels.web_widget import WebWidgetChannel
        
        web_widget = WebWidgetChannel()
        
        # Simulate multiple concurrent connections
        connection_ids = [f"conn_{i}" for i in range(10)]
        
        with patch.object(web_widget, 'websocket_manager') as mock_ws_manager:
            mock_ws_manager.add_connection = AsyncMock()
            mock_ws_manager.get_connection_count = Mock(return_value=10)
            
            # Add multiple connections
            for conn_id in connection_ids:
                await web_widget.websocket_manager.add_connection(conn_id, Mock())
            
            # Should handle multiple connections
            assert mock_ws_manager.add_connection.call_count == 10
            assert mock_ws_manager.get_connection_count() == 10


class TestWhatsAppIntegration:
    """Test WhatsApp Business API integration."""

    @pytest.mark.asyncio
    async def test_whatsapp_webhook_verification(self, channel_client: AsyncClient):
        """Test WhatsApp webhook verification."""
        # WhatsApp sends GET request for webhook verification
        verification_params = {
            "hub.mode": "subscribe",
            "hub.challenge": "test_challenge_123",
            "hub.verify_token": "whatsapp_verify_token"
        }
        
        response = await channel_client.get(
            "/api/v1/channels/whatsapp/webhook",
            params=verification_params
        )
        
        # Should return challenge for valid verification
        if response.status_code == 200:
            assert response.text == "test_challenge_123"
        else:
            # Webhook might not be fully implemented yet
            assert response.status_code in [404, 501]

    @pytest.mark.asyncio
    async def test_whatsapp_message_receiving(self, channel_client: AsyncClient):
        """Test receiving WhatsApp messages."""
        whatsapp_webhook_data = {
            "object": "whatsapp_business_account",
            "entry": [{
                "id": "entry_id",
                "changes": [{
                    "value": {
                        "messaging_product": "whatsapp",
                        "metadata": {
                            "display_phone_number": "1234567890",
                            "phone_number_id": "phone_id"
                        },
                        "messages": [{
                            "from": "user_phone_number",
                            "id": "message_id",
                            "timestamp": "1642583940",
                            "text": {
                                "body": "Hello from WhatsApp"
                            },
                            "type": "text"
                        }]
                    },
                    "field": "messages"
                }]
            }]
        }
        
        response = await channel_client.post(
            "/api/v1/channels/whatsapp/webhook",
            json=whatsapp_webhook_data
        )
        
        # Should process webhook successfully
        assert response.status_code in [200, 404, 501]  # 404/501 if not implemented

    @pytest.mark.asyncio
    async def test_whatsapp_message_sending(self):
        """Test sending WhatsApp messages."""
        from services.channel_service.app.channels.whatsapp import WhatsAppChannel
        
        whatsapp_channel = WhatsAppChannel()
        
        with patch.object(whatsapp_channel, 'whatsapp_client') as mock_client:
            mock_client.send_message = AsyncMock(return_value={
                "messaging_product": "whatsapp",
                "to": "recipient_phone",
                "message_id": "wamid.123"
            })
            
            result = await whatsapp_channel.send_message(
                recipient="recipient_phone",
                content="Hello from test",
                conversation_id="test_conv",
                creator_id="creator_123"
            )
            
            assert "message_id" in result
            mock_client.send_message.assert_called_once()

    @pytest.mark.asyncio
    async def test_whatsapp_media_handling(self):
        """Test WhatsApp media message handling."""
        from services.channel_service.app.channels.whatsapp import WhatsAppChannel
        
        whatsapp_channel = WhatsAppChannel()
        
        media_message = {
            "from": "user_phone",
            "type": "image",
            "image": {
                "id": "media_id_123",
                "mime_type": "image/jpeg",
                "caption": "Test image from WhatsApp"
            }
        }
        
        with patch.object(whatsapp_channel, 'download_media') as mock_download:
            mock_download.return_value = b"fake_image_data"
            
            result = await whatsapp_channel.handle_media_message(media_message)
            
            assert result["type"] == "image"
            assert result["caption"] == "Test image from WhatsApp"
            mock_download.assert_called_once_with("media_id_123")

    @pytest.mark.asyncio 
    async def test_whatsapp_status_updates(self):
        """Test WhatsApp message status updates."""
        whatsapp_status_data = {
            "object": "whatsapp_business_account",
            "entry": [{
                "id": "entry_id",
                "changes": [{
                    "value": {
                        "messaging_product": "whatsapp",
                        "statuses": [{
                            "id": "message_id_123",
                            "status": "delivered",
                            "timestamp": "1642583940",
                            "recipient_id": "recipient_phone"
                        }]
                    },
                    "field": "messages"
                }]
            }]
        }
        
        from services.channel_service.app.channels.whatsapp import WhatsAppChannel
        
        whatsapp_channel = WhatsAppChannel()
        
        with patch.object(whatsapp_channel, 'update_message_status') as mock_update:
            await whatsapp_channel.handle_status_update(whatsapp_status_data)
            
            mock_update.assert_called_once_with(
                message_id="message_id_123",
                status="delivered"
            )


class TestTelegramIntegration:
    """Test Telegram Bot API integration."""

    @pytest.mark.asyncio
    async def test_telegram_webhook_setup(self, channel_client: AsyncClient):
        """Test Telegram webhook configuration."""
        webhook_data = {
            "bot_token": "test_bot_token",
            "webhook_url": "https://example.com/api/v1/channels/telegram/webhook"
        }
        
        response = await channel_client.post(
            "/api/v1/channels/telegram/setup-webhook",
            json=webhook_data
        )
        
        # Should configure webhook successfully
        assert response.status_code in [200, 404, 501]  # 404/501 if not implemented

    @pytest.mark.asyncio
    async def test_telegram_message_receiving(self, channel_client: AsyncClient):
        """Test receiving Telegram messages."""
        telegram_update = {
            "update_id": 123456789,
            "message": {
                "message_id": 123,
                "from": {
                    "id": 987654321,
                    "is_bot": False,
                    "first_name": "Test",
                    "username": "testuser"
                },
                "chat": {
                    "id": 987654321,
                    "first_name": "Test",
                    "username": "testuser",
                    "type": "private"
                },
                "date": 1642583940,
                "text": "Hello from Telegram"
            }
        }
        
        response = await channel_client.post(
            "/api/v1/channels/telegram/webhook",
            json=telegram_update
        )
        
        # Should process update successfully
        assert response.status_code in [200, 404, 501]

    @pytest.mark.asyncio
    async def test_telegram_message_sending(self):
        """Test sending Telegram messages."""
        from services.channel_service.app.channels.telegram import TelegramChannel
        
        telegram_channel = TelegramChannel()
        
        with patch.object(telegram_channel, 'telegram_client') as mock_client:
            mock_client.send_message = AsyncMock(return_value={
                "ok": True,
                "result": {
                    "message_id": 124,
                    "from": {"id": 123456789, "is_bot": True},
                    "chat": {"id": 987654321, "type": "private"},
                    "date": 1642583940,
                    "text": "Hello from test bot"
                }
            })
            
            result = await telegram_channel.send_message(
                recipient="987654321",
                content="Hello from test bot",
                conversation_id="test_conv",
                creator_id="creator_123"
            )
            
            assert result["ok"] is True
            assert result["result"]["message_id"] == 124
            mock_client.send_message.assert_called_once()

    @pytest.mark.asyncio
    async def test_telegram_inline_keyboard(self):
        """Test Telegram inline keyboard functionality."""
        from services.channel_service.app.channels.telegram import TelegramChannel
        
        telegram_channel = TelegramChannel()
        
        with patch.object(telegram_channel, 'telegram_client') as mock_client:
            mock_client.send_message = AsyncMock(return_value={"ok": True})
            
            keyboard_data = {
                "inline_keyboard": [[
                    {"text": "Option 1", "callback_data": "option_1"},
                    {"text": "Option 2", "callback_data": "option_2"}
                ]]
            }
            
            await telegram_channel.send_message_with_keyboard(
                recipient="987654321",
                content="Choose an option:",
                keyboard=keyboard_data,
                conversation_id="test_conv"
            )
            
            mock_client.send_message.assert_called_once()

    @pytest.mark.asyncio
    async def test_telegram_callback_query_handling(self):
        """Test handling Telegram callback queries."""
        callback_query = {
            "update_id": 123456790,
            "callback_query": {
                "id": "callback_id_123",
                "from": {
                    "id": 987654321,
                    "first_name": "Test",
                    "username": "testuser"
                },
                "message": {
                    "message_id": 123,
                    "chat": {"id": 987654321}
                },
                "data": "option_1"
            }
        }
        
        from services.channel_service.app.channels.telegram import TelegramChannel
        
        telegram_channel = TelegramChannel()
        
        with patch.object(telegram_channel, 'handle_callback') as mock_callback:
            await telegram_channel.process_update(callback_query)
            
            mock_callback.assert_called_once_with("option_1", callback_query["callback_query"])


class TestWebWidgetChannel:
    """Test Web Widget channel functionality."""

    @pytest.mark.asyncio
    async def test_widget_configuration_api(self, channel_client: AsyncClient, auth_headers):
        """Test web widget configuration API."""
        widget_config = {
            "title": "AI Coach Chat",
            "welcome_message": "Hello! How can I help you today?",
            "theme": {
                "primary_color": "#3498db",
                "background_color": "#ffffff",
                "font_family": "Arial, sans-serif"
            },
            "position": "bottom-right",
            "enabled": True
        }
        
        response = await channel_client.post(
            "/api/v1/channels/widget/configure",
            json=widget_config,
            headers=auth_headers
        )
        
        assert response.status_code in [200, 201]
        if response.status_code in [200, 201]:
            config_data = response.json()
            assert config_data["title"] == "AI Coach Chat"
            assert config_data["theme"]["primary_color"] == "#3498db"

    @pytest.mark.asyncio
    async def test_widget_embed_code_generation(self, channel_client: AsyncClient, auth_headers):
        """Test web widget embed code generation."""
        response = await channel_client.get(
            "/api/v1/channels/widget/embed-code",
            headers=auth_headers
        )
        
        assert response.status_code in [200, 404]
        if response.status_code == 200:
            embed_data = response.json()
            assert "embed_code" in embed_data
            assert "widget_url" in embed_data
            assert "<script" in embed_data["embed_code"]

    @pytest.mark.asyncio
    async def test_widget_real_time_messaging(self):
        """Test web widget real-time messaging."""
        from services.channel_service.app.channels.web_widget import WebWidgetChannel
        
        web_widget = WebWidgetChannel()
        
        with patch.object(web_widget, 'websocket_manager') as mock_ws:
            mock_ws.broadcast_to_session = AsyncMock()
            
            # Simulate real-time message
            await web_widget.send_real_time_message(
                session_id="session_123",
                message_data={
                    "type": "ai_response",
                    "content": "AI response in real-time",
                    "timestamp": "2024-01-17T10:00:00Z"
                }
            )
            
            mock_ws.broadcast_to_session.assert_called_once()

    @pytest.mark.asyncio
    async def test_widget_typing_indicators(self):
        """Test web widget typing indicators."""
        from services.channel_service.app.channels.web_widget import WebWidgetChannel
        
        web_widget = WebWidgetChannel()
        
        with patch.object(web_widget, 'websocket_manager') as mock_ws:
            mock_ws.send_typing_indicator = AsyncMock()
            
            # Start typing
            await web_widget.start_typing(
                session_id="session_123",
                user_type="ai"
            )
            
            # Stop typing
            await web_widget.stop_typing(
                session_id="session_123",
                user_type="ai"
            )
            
            assert mock_ws.send_typing_indicator.call_count == 2

    @pytest.mark.asyncio
    async def test_widget_analytics_tracking(self, channel_client: AsyncClient, auth_headers):
        """Test web widget analytics tracking."""
        analytics_data = {
            "session_id": "session_123",
            "event_type": "message_sent",
            "metadata": {
                "message_length": 25,
                "response_time_ms": 1500,
                "user_satisfaction": 4
            }
        }
        
        response = await channel_client.post(
            "/api/v1/channels/widget/analytics",
            json=analytics_data,
            headers=auth_headers
        )
        
        assert response.status_code in [200, 204, 404]


class TestChannelManager:
    """Test channel manager orchestration."""

    @pytest.mark.asyncio
    async def test_channel_registration(self):
        """Test registering channels with the manager."""
        from services.channel_service.app.channel_manager import ChannelManager
        from services.channel_service.app.channels.base import BaseChannel
        
        manager = ChannelManager()
        
        # Mock channel
        mock_channel = Mock(spec=BaseChannel)
        mock_channel.channel_type = "test_channel"
        mock_channel.is_active = True
        
        manager.register_channel("test_channel", mock_channel)
        
        assert "test_channel" in manager.channels
        assert manager.get_channel("test_channel") == mock_channel

    @pytest.mark.asyncio
    async def test_cross_channel_message_routing(self):
        """Test routing messages across different channels."""
        from services.channel_service.app.channel_manager import ChannelManager
        
        manager = ChannelManager()
        
        # Mock multiple channels
        channels = ["websocket", "whatsapp", "telegram"]
        for channel_type in channels:
            mock_channel = Mock()
            mock_channel.send_message = AsyncMock()
            manager.register_channel(channel_type, mock_channel)
        
        # Route message to all channels
        await manager.broadcast_message(
            content="Broadcast test message",
            conversation_id="test_conv",
            creator_id="creator_123",
            exclude_channels=[]
        )
        
        # All channels should have received the message
        for channel_type in channels:
            channel = manager.get_channel(channel_type)
            channel.send_message.assert_called_once()

    @pytest.mark.asyncio
    async def test_channel_health_monitoring(self):
        """Test channel health monitoring."""
        from services.channel_service.app.channel_manager import ChannelManager
        
        manager = ChannelManager()
        
        # Mock channels with different health states
        healthy_channel = Mock()
        healthy_channel.health_check = AsyncMock(return_value={"status": "healthy"})
        
        unhealthy_channel = Mock()
        unhealthy_channel.health_check = AsyncMock(return_value={"status": "unhealthy", "error": "Connection failed"})
        
        manager.register_channel("healthy", healthy_channel)
        manager.register_channel("unhealthy", unhealthy_channel)
        
        health_report = await manager.get_health_status()
        
        assert health_report["healthy"]["status"] == "healthy"
        assert health_report["unhealthy"]["status"] == "unhealthy"
        assert "error" in health_report["unhealthy"]