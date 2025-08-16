"""
Channel Service - MVP Coaching AI Platform
Multi-channel messaging service with WhatsApp, Telegram, and Web Widget support
"""

import logging
from contextlib import asynccontextmanager
from typing import Dict, List, Optional, Any
from datetime import datetime

from fastapi import FastAPI, HTTPException, status, WebSocket, WebSocketDisconnect, Depends, Query, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from shared.config.settings import validate_service_environment, get_database_session_async
# Centralized environment constants and configuration management
from shared.config.env_constants import CORS_ORIGINS, REQUIRED_VARS_BY_SERVICE, get_env_value
from shared.security.jwt_manager import get_current_creator_id
from shared.models.database import get_tenant_session

from .channel_manager import ChannelManager
from .models import (
    ChannelConfiguration, 
    ChannelConfigurationCreate,
    ChannelConfigurationUpdate,
    OutboundMessage,
    WebSocketMessage,
    WebSocketResponse
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Environment variables validation using centralized configuration
required_env_vars = REQUIRED_VARS_BY_SERVICE["channel_service"]

validate_service_environment(required_env_vars, logger)


# WebSocket connection manager for Web Widget
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, Dict[str, Any]] = {}
    
    async def connect(self, websocket: WebSocket, session_id: str, user_info: Dict[str, Any]):
        await websocket.accept()
        self.active_connections[session_id] = {
            "websocket": websocket,
            "user_info": user_info,
            "connected_at": datetime.utcnow()
        }
        logger.info(f"WebSocket connected: {session_id}")
    
    def disconnect(self, session_id: str):
        if session_id in self.active_connections:
            del self.active_connections[session_id]
            logger.info(f"WebSocket disconnected: {session_id}")
    
    async def send_message(self, session_id: str, message: dict):
        if session_id in self.active_connections:
            websocket = self.active_connections[session_id]["websocket"]
            await websocket.send_json(message)
    
    def get_active_sessions(self) -> List[str]:
        return list(self.active_connections.keys())


manager = ConnectionManager()
channel_manager: Optional[ChannelManager] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    global channel_manager
    
    logger.info("🚀 Channel Service starting up...")
    
    try:
        # Initialize database session
        async with get_database_session_async() as session:
            # Initialize channel manager
            channel_manager = ChannelManager(session)
            logger.info("✅ Channel Manager initialized")
            
            # Run health checks on active channels
            # TODO: Implement periodic health checks
            
    except Exception as e:
        logger.error(f"❌ Failed to initialize Channel Service: {e}")
        raise
    
    yield
    
    logger.info("🛑 Channel Service shutting down...")
    
    # Cleanup logic
    if channel_manager:
        await channel_manager.cleanup_inactive_services()
        logger.info("✅ Channel services cleaned up")


# Create FastAPI application
app = FastAPI(
    title="Channel Service API",
    description="Multi-channel messaging service for MVP Coaching AI Platform",
    version="2.0.0",
    lifespan=lifespan,
    openapi_tags=[
        {
            "name": "channels",
            "description": "Channel configuration and management"
        },
        {
            "name": "messages",
            "description": "Message sending and handling"
        },
        {
            "name": "webhooks",
            "description": "Webhook endpoints for channel integrations"
        },
        {
            "name": "websocket",
            "description": "WebSocket communication for Web Widget"
        },
        {
            "name": "health",
            "description": "Service and channel health checks"
        }
    ]
)

# CORS middleware using centralized configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=(get_env_value(CORS_ORIGINS, fallback=True) or "http://localhost:3000").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Dependency for getting channel manager
async def get_channel_manager() -> ChannelManager:
    """Get channel manager instance"""
    if not channel_manager:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Channel manager not initialized"
        )
    return channel_manager


# =====================================================
# Health Check Endpoints
# =====================================================

@app.get("/health", tags=["health"])
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "channel-service",
        "version": "2.0.0",
        "active_websocket_connections": len(manager.active_connections),
        "channel_manager_initialized": channel_manager is not None
    }


@app.get("/ready", tags=["health"])
async def readiness_check(cm: ChannelManager = Depends(get_channel_manager)):
    """Readiness check endpoint"""
    try:
        # Check supported channel types
        supported_types = cm.get_supported_channel_types()
        
        return {
            "status": "ready",
            "service": "channel-service",
            "supported_channels": supported_types,
            "checks": {
                "channel_manager": "initialized",
                "database": "connected"
            }
        }
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service not ready"
        )


@app.get("/", tags=["health"])
async def root():
    """Root endpoint"""
    return {
        "message": "Multi-Channel Messaging Service",
        "version": "2.0.0",
        "docs": "/docs",
        "supported_channels": ["whatsapp", "telegram", "web_widget"]
    }


# =====================================================
# Channel Management Endpoints
# =====================================================

@app.get("/api/v1/channels", tags=["channels"])
async def list_channels(
    creator_id: str = Depends(get_current_creator_id),
    cm: ChannelManager = Depends(get_channel_manager)
):
    """List all channels for the authenticated creator"""
    try:
        channels = await cm.get_active_channels(creator_id)
        return {
            "channels": channels,
            "total": len(channels)
        }
    except Exception as e:
        logger.error(f"Failed to list channels: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve channels"
        )


@app.get("/api/v1/channels/{channel_id}/health", tags=["channels", "health"])
async def check_channel_health(
    channel_id: str,
    creator_id: str = Depends(get_current_creator_id),
    cm: ChannelManager = Depends(get_channel_manager)
):
    """Check health of a specific channel"""
    try:
        health_result = await cm.check_channel_health(channel_id, creator_id)
        return health_result
    except Exception as e:
        logger.error(f"Failed to check channel health: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to check channel health"
        )


# =====================================================
# Message Sending Endpoints
# =====================================================

@app.post("/api/v1/channels/{channel_id}/messages", tags=["messages"])
async def send_channel_message(
    channel_id: str,
    message: OutboundMessage,
    creator_id: str = Depends(get_current_creator_id),
    cm: ChannelManager = Depends(get_channel_manager)
):
    """Send message through specified channel"""
    try:
        message_data = message.dict()
        message_data["channel_config_id"] = channel_id
        
        result = await cm.send_message(channel_id, creator_id, message_data)
        return result
        
    except Exception as e:
        logger.error(f"Failed to send message: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send message"
        )


# =====================================================
# Webhook Endpoints
# =====================================================

@app.post("/api/v1/webhooks/whatsapp/{channel_id}", tags=["webhooks"])
async def whatsapp_webhook(
    channel_id: str,
    webhook_data: Dict[str, Any] = Body(...),
    creator_id: str = Query(..., description="Creator ID for the channel"),
    cm: ChannelManager = Depends(get_channel_manager)
):
    """WhatsApp Business API webhook endpoint"""
    try:
        result = await cm.process_webhook(channel_id, creator_id, webhook_data)
        
        if result and result.get("requires_ai_processing"):
            # TODO: Forward to AI Engine Service for processing
            logger.info(f"Message requires AI processing: {result['message']['id']}")
        
        return {"status": "ok"}
        
    except Exception as e:
        logger.error(f"WhatsApp webhook failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Webhook processing failed"
        )


@app.post("/api/v1/webhooks/telegram/{channel_id}", tags=["webhooks"])
async def telegram_webhook(
    channel_id: str,
    webhook_data: Dict[str, Any] = Body(...),
    creator_id: str = Query(..., description="Creator ID for the channel"),
    cm: ChannelManager = Depends(get_channel_manager)
):
    """Telegram Bot API webhook endpoint"""
    try:
        result = await cm.process_webhook(channel_id, creator_id, webhook_data)
        
        if result and result.get("requires_ai_processing"):
            # TODO: Forward to AI Engine Service for processing
            logger.info(f"Message requires AI processing: {result['message']['id']}")
        
        return {"ok": True}
        
    except Exception as e:
        logger.error(f"Telegram webhook failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Webhook processing failed"
        )


# =====================================================
# Web Widget Endpoints
# =====================================================

@app.websocket("/ws/widget/{channel_id}")
async def widget_websocket(
    websocket: WebSocket, 
    channel_id: str,
    creator_id: str = Query(..., description="Creator ID"),
    session_id: str = Query(..., description="Session ID"),
    user_name: str = Query("Anonymous", description="User name")
):
    """WebSocket endpoint for Web Widget real-time communication"""
    try:
        # Get channel service for Web Widget
        async with get_database_session_async() as session:
            cm = ChannelManager(session)
            
            # Validate channel exists and is Web Widget type
            from .models import ChannelType
            channel_config = await cm._get_channel_config(channel_id, creator_id)
            if not channel_config or channel_config.channel_type != ChannelType.WEB_WIDGET:
                await websocket.close(code=4004, reason="Channel not found or invalid type")
                return
            
            # Get Web Widget service
            widget_service = await cm.get_channel_service(channel_config)
            if not widget_service:
                await websocket.close(code=4003, reason="Widget service unavailable")
                return
            
            # Register WebSocket session
            user_info = {"user_name": user_name, "creator_id": creator_id}
            await widget_service.register_websocket_session(session_id, websocket, user_info)
            await manager.connect(websocket, session_id, user_info)
            
            while True:
                # Receive message from client
                data = await websocket.receive_json()
                logger.info(f"Widget message from {session_id}: {data}")
                
                # Process message through Web Widget service
                webhook_data = {
                    "content": data.get("content", ""),
                    "message_type": data.get("message_type", "text"),
                    "session_id": session_id,
                    "user_identifier": session_id,
                    "user_name": user_name,
                    "channel_metadata": data.get("metadata", {}),
                    "user_agent": data.get("user_agent"),
                    "page_url": data.get("page_url")
                }
                
                result = await cm.process_webhook(channel_id, creator_id, webhook_data)
                
                if result and result.get("requires_ai_processing"):
                    # TODO: Forward to AI Engine Service for processing
                    logger.info(f"Widget message requires AI processing: {result['message']['id']}")
                    
                    # Send acknowledgment
                    response = WebSocketResponse(
                        type="message_received",
                        status="processing",
                        data={"message_id": result['message']['id']}
                    )
                    await websocket.send_json(response.dict())
    
    except WebSocketDisconnect:
        manager.disconnect(session_id)
        if 'widget_service' in locals():
            await widget_service.unregister_websocket_session(session_id)
    except Exception as e:
        logger.error(f"Widget WebSocket error for {session_id}: {str(e)}")
        manager.disconnect(session_id)
        if 'widget_service' in locals():
            await widget_service.unregister_websocket_session(session_id)


@app.get("/api/v1/widget/{channel_id}/embed", tags=["web_widget"], response_class=HTMLResponse)
async def get_widget_embed_code(
    channel_id: str,
    creator_id: str = Query(..., description="Creator ID"),
    base_url: str = Query("http://localhost:8004", description="Base URL for widget"),
    cm: ChannelManager = Depends(get_channel_manager)
):
    """Get HTML embed code for Web Widget"""
    try:
        # Get channel configuration
        channel_config = await cm._get_channel_config(channel_id, creator_id)
        if not channel_config:
            raise HTTPException(status_code=404, detail="Channel not found")
        
        from .models import ChannelType
        if channel_config.channel_type != ChannelType.WEB_WIDGET:
            raise HTTPException(status_code=400, detail="Channel is not a Web Widget")
        
        # Get Web Widget service
        widget_service = await cm.get_channel_service(channel_config)
        if not widget_service:
            raise HTTPException(status_code=503, detail="Widget service unavailable")
        
        # Generate embed code
        embed_code = widget_service.generate_embed_code(base_url)
        
        return HTMLResponse(content=f"""
<!DOCTYPE html>
<html>
<head>
    <title>Widget Embed Code</title>
    <style>
        body {{ font-family: monospace; margin: 20px; }}
        .code {{ background: #f5f5f5; padding: 15px; border: 1px solid #ddd; }}
    </style>
</head>
<body>
    <h2>AI Coaching Widget Embed Code</h2>
    <p>Copy and paste this code into your website:</p>
    <div class="code">
        <pre>{embed_code}</pre>
    </div>
</body>
</html>
        """)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to generate embed code: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate embed code"
        )


# =====================================================
# Connection Status Endpoints
# =====================================================

@app.get("/api/v1/connections", tags=["websocket"])
async def get_active_connections():
    """Get active WebSocket connections"""
    return {
        "active_websocket_connections": len(manager.active_connections),
        "sessions": manager.get_active_sessions()
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8004)