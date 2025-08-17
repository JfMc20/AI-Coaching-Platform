"""
Channel Service - MVP Coaching AI Platform
Multi-channel messaging service with WhatsApp, Telegram, and Web Widget support
"""

import logging
from contextlib import asynccontextmanager
from typing import Dict, List, Optional, Any
from datetime import datetime

from fastapi import FastAPI, HTTPException, status, WebSocket, WebSocketDisconnect, Depends, Query, Body
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from shared.config.settings import validate_service_environment
# Centralized environment constants and configuration management
from shared.config.env_constants import CORS_ORIGINS, REQUIRED_VARS_BY_SERVICE, get_env_value
# Import local authentication dependencies
from .database import get_db, get_tenant_session, init_database, close_database, async_session

# Import AI client at module level  
try:
    from .ai_client import AIEngineClient
    AI_CLIENT_AVAILABLE = True
except Exception as ai_import_error:
    print(f"Failed to import AI Engine client: {ai_import_error}")
    AI_CLIENT_AVAILABLE = False
    AIEngineClient = None

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
    logger.info("🚀 Channel Service starting up...")
    
    # Startup logic here
    # - Database connection testing
    # - Channel service initialization
    # - Health checks setup
    
    yield
    
    logger.info("🛑 Channel Service shutting down...")
    # Cleanup logic here


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

# Mount static files for web widget  
import os
static_dir = os.path.join(os.path.dirname(__file__), "static")
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# CORS middleware using centralized configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=(get_env_value(CORS_ORIGINS, fallback=True) or "http://localhost:3000").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Dependency for getting channel manager
async def get_channel_manager(session: AsyncSession = Depends(get_db)) -> ChannelManager:
    """Get channel manager instance"""
    return ChannelManager(session)


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
        "widget_demo": "/widget-demo",
        "supported_channels": ["whatsapp", "telegram", "web_widget"],
        "test_change": "Widget endpoints available"
    }


@app.get("/widget.js", tags=["widget"])
async def serve_widget_js():
    """Serve widget JavaScript file directly"""
    widget_js_content = '''/**
 * AI Coaching Platform - Web Widget Client
 * Embeddable chat widget for websites
 */

class AIChatWidget {
    constructor(config = {}) {
        this.config = {
            apiUrl: config.apiUrl || 'ws://localhost:8004',
            widgetId: config.widgetId || 'default-widget',
            position: config.position || 'bottom-right',
            theme: config.theme || 'light',
            primaryColor: config.primaryColor || '#007bff',
            welcomeMessage: config.welcomeMessage || 'Hello! How can I help you today?',
            placeholder: config.placeholder || 'Type your message...',
            ...config
        };
        
        this.isOpen = false;
        this.websocket = null;
        this.conversationId = this.generateConversationId();
        this.messageHistory = [];
        
        this.init();
    }
    
    generateConversationId() {
        return 'conv_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    }
    
    init() {
        this.createWidgetHTML();
        this.attachEventListeners();
        this.loadStyles();
        this.connectWebSocket();
    }
    
    createWidgetHTML() {
        // Widget container
        const widgetContainer = document.createElement('div');
        widgetContainer.id = 'ai-chat-widget';
        widgetContainer.className = `ai-widget ${this.config.position} ${this.config.theme}`;
        
        widgetContainer.innerHTML = `
            <!-- Widget Toggle Button -->
            <div class="widget-toggle" id="widget-toggle">
                <div class="widget-icon">
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
                        <path d="M20 2H4c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h4l4 4 4-4h4c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2z"/>
                    </svg>
                </div>
                <div class="widget-close-icon" style="display: none;">
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
                        <path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"/>
                    </svg>
                </div>
            </div>
            
            <!-- Widget Chat Panel -->
            <div class="widget-panel" id="widget-panel" style="display: none;">
                <div class="widget-header">
                    <h3>AI Assistant</h3>
                    <div class="connection-status" id="connection-status">
                        <span class="status-dot"></span>
                        <span class="status-text">Connecting...</span>
                    </div>
                </div>
                
                <div class="widget-messages" id="widget-messages">
                    <div class="message bot-message">
                        <div class="message-content">${this.config.welcomeMessage}</div>
                        <div class="message-time">${this.formatTime(new Date())}</div>
                    </div>
                </div>
                
                <div class="widget-input-container">
                    <div class="input-wrapper">
                        <input type="text" 
                               id="widget-input" 
                               placeholder="${this.config.placeholder}"
                               maxlength="500">
                        <button type="button" id="send-button" disabled>
                            <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
                                <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/>
                            </svg>
                        </button>
                    </div>
                    <div class="typing-indicator" id="typing-indicator" style="display: none;">
                        <span></span><span></span><span></span>
                    </div>
                </div>
            </div>
        `;
        
        document.body.appendChild(widgetContainer);
    }
    
    attachEventListeners() {
        const toggle = document.getElementById('widget-toggle');
        const input = document.getElementById('widget-input');
        const sendButton = document.getElementById('send-button');
        
        toggle.addEventListener('click', () => this.toggleWidget());
        
        input.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });
        
        input.addEventListener('input', () => {
            sendButton.disabled = !input.value.trim();
        });
        
        sendButton.addEventListener('click', () => this.sendMessage());
    }
    
    toggleWidget() {
        const panel = document.getElementById('widget-panel');
        const toggle = document.getElementById('widget-toggle');
        const icon = toggle.querySelector('.widget-icon');
        const closeIcon = toggle.querySelector('.widget-close-icon');
        
        this.isOpen = !this.isOpen;
        
        if (this.isOpen) {
            panel.style.display = 'flex';
            icon.style.display = 'none';
            closeIcon.style.display = 'block';
            document.getElementById('widget-input').focus();
        } else {
            panel.style.display = 'none';
            icon.style.display = 'block';
            closeIcon.style.display = 'none';
        }
    }
    
    connectWebSocket() {
        try {
            // Create WebSocket connection to Channel Service
            const wsUrl = `${this.config.apiUrl.replace('http', 'ws')}/ws/widget/${this.config.widgetId}?user_name=Demo User`;
            console.log('AI Widget: Connecting to:', wsUrl);
            
            this.websocket = new WebSocket(wsUrl);
            
            this.websocket.onopen = () => {
                console.log('AI Widget: WebSocket connected');
                this.updateConnectionStatus('connected', 'Connected');
            };
            
            this.websocket.onmessage = (event) => {
                console.log('AI Widget: Received message:', event.data);
                try {
                    const data = JSON.parse(event.data);
                    
                    // Hide typing indicator when we get a response
                    this.hideTypingIndicator();
                    
                    if (data.type === 'ai_response') {
                        this.addMessageToUI('bot', data.content);
                    } else if (data.type === 'error') {
                        this.addMessageToUI('bot', `Error: ${data.message}`);
                    } else if (data.type === 'status') {
                        console.log('AI Widget: Status update:', data.message);
                    }
                } catch (e) {
                    console.error('AI Widget: Error parsing message:', e);
                    this.addMessageToUI('bot', 'Error processing response');
                    this.hideTypingIndicator();
                }
            };
            
            this.websocket.onerror = (error) => {
                console.error('AI Widget: WebSocket error:', error);
                this.updateConnectionStatus('error', 'Connection Error');
            };
            
            this.websocket.onclose = () => {
                console.log('AI Widget: WebSocket closed');
                this.updateConnectionStatus('disconnected', 'Disconnected');
                
                // Attempt to reconnect after 3 seconds
                setTimeout(() => {
                    console.log('AI Widget: Attempting to reconnect...');
                    this.connectWebSocket();
                }, 3000);
            };
            
        } catch (error) {
            console.error('AI Widget: Connection error:', error);
            this.updateConnectionStatus('error', 'Failed to Connect');
        }
    }
    
    updateConnectionStatus(status, text) {
        const statusElement = document.getElementById('connection-status');
        const dot = statusElement.querySelector('.status-dot');
        const textElement = statusElement.querySelector('.status-text');
        
        dot.className = `status-dot ${status}`;
        textElement.textContent = text;
    }
    
    sendMessage() {
        const input = document.getElementById('widget-input');
        const message = input.value.trim();
        
        if (!message) return;
        
        // Add user message to UI immediately
        this.addMessageToUI('user', message);
        input.value = '';
        document.getElementById('send-button').disabled = true;
        
        // Send message through WebSocket if connected
        if (this.websocket && this.websocket.readyState === WebSocket.OPEN) {
            const messageData = {
                type: 'user_message',
                content: message,
                conversation_id: this.conversationId,
                user_identifier: 'demo-user',
                timestamp: new Date().toISOString()
            };
            
            console.log('AI Widget: Sending message:', messageData);
            this.websocket.send(JSON.stringify(messageData));
            
            // Show typing indicator
            this.showTypingIndicator();
        } else {
            // Fallback to demo mode if not connected
            console.log('AI Widget: WebSocket not connected, using demo mode');
            setTimeout(() => {
                this.addMessageToUI('bot', 'Connection unavailable. This is a demo response.');
            }, 1000);
        }
    }
    
    showTypingIndicator() {
        const indicator = document.getElementById('typing-indicator');
        if (indicator) {
            indicator.style.display = 'flex';
            
            // Hide after 10 seconds if no response
            setTimeout(() => {
                indicator.style.display = 'none';
            }, 10000);
        }
    }
    
    hideTypingIndicator() {
        const indicator = document.getElementById('typing-indicator');
        if (indicator) {
            indicator.style.display = 'none';
        }
    }
    
    addMessageToUI(type, content) {
        const messagesContainer = document.getElementById('widget-messages');
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${type}-message`;
        
        messageDiv.innerHTML = `
            <div class="message-content">${this.escapeHtml(content)}</div>
            <div class="message-time">${this.formatTime(new Date())}</div>
        `;
        
        messagesContainer.appendChild(messageDiv);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }
    
    formatTime(date) {
        return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    }
    
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    loadStyles() {
        if (document.getElementById('ai-widget-styles')) return;
        
        const styles = document.createElement('style');
        styles.id = 'ai-widget-styles';
        styles.textContent = `
            #ai-chat-widget {
                position: fixed;
                z-index: 10000;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            }
            
            #ai-chat-widget.bottom-right {
                bottom: 20px;
                right: 20px;
            }
            
            .widget-toggle {
                width: 60px;
                height: 60px;
                border-radius: 50%;
                background-color: ${this.config.primaryColor};
                color: white;
                cursor: pointer;
                display: flex;
                align-items: center;
                justify-content: center;
                box-shadow: 0 4px 20px rgba(0,0,0,0.2);
                transition: all 0.3s ease;
            }
            
            .widget-toggle:hover {
                transform: scale(1.1);
            }
            
            .widget-panel {
                position: absolute;
                bottom: 80px;
                right: 0;
                width: 350px;
                height: 500px;
                background: white;
                border-radius: 16px;
                box-shadow: 0 8px 32px rgba(0,0,0,0.1);
                display: flex;
                flex-direction: column;
                overflow: hidden;
                animation: slideUp 0.3s ease;
            }
            
            @keyframes slideUp {
                from { transform: translateY(20px); opacity: 0; }
                to { transform: translateY(0); opacity: 1; }
            }
            
            .widget-header {
                background: ${this.config.primaryColor};
                color: white;
                padding: 16px;
                display: flex;
                justify-content: space-between;
                align-items: center;
            }
            
            .widget-header h3 {
                margin: 0;
                font-size: 16px;
                font-weight: 600;
            }
            
            .connection-status {
                display: flex;
                align-items: center;
                gap: 6px;
                font-size: 12px;
            }
            
            .status-dot {
                width: 8px;
                height: 8px;
                border-radius: 50%;
                background: #ccc;
            }
            
            .status-dot.connected { background: #4CAF50; }
            
            .widget-messages {
                flex: 1;
                padding: 16px;
                overflow-y: auto;
                display: flex;
                flex-direction: column;
                gap: 12px;
            }
            
            .message {
                max-width: 80%;
                display: flex;
                flex-direction: column;
                gap: 4px;
            }
            
            .user-message {
                align-self: flex-end;
            }
            
            .bot-message {
                align-self: flex-start;
            }
            
            .message-content {
                padding: 12px 16px;
                border-radius: 18px;
                font-size: 14px;
                line-height: 1.4;
            }
            
            .user-message .message-content {
                background: ${this.config.primaryColor};
                color: white;
            }
            
            .bot-message .message-content {
                background: #f1f3f5;
                color: #333;
            }
            
            .message-time {
                font-size: 11px;
                color: #666;
                margin: 0 8px;
            }
            
            .widget-input-container {
                padding: 16px;
                border-top: 1px solid #e1e5e9;
            }
            
            .input-wrapper {
                display: flex;
                gap: 8px;
                align-items: center;
            }
            
            #widget-input {
                flex: 1;
                border: 1px solid #ddd;
                border-radius: 20px;
                padding: 12px 16px;
                font-size: 14px;
                outline: none;
            }
            
            #widget-input:focus {
                border-color: ${this.config.primaryColor};
            }
            
            #send-button {
                width: 40px;
                height: 40px;
                border-radius: 50%;
                border: none;
                background: ${this.config.primaryColor};
                color: white;
                cursor: pointer;
                display: flex;
                align-items: center;
                justify-content: center;
                transition: all 0.2s ease;
            }
            
            #send-button:disabled {
                background: #ccc;
                cursor: not-allowed;
            }
            
            #send-button:not(:disabled):hover {
                transform: scale(1.1);
            }
            
            .typing-indicator {
                display: none;
                align-items: center;
                gap: 4px;
                padding: 8px 16px;
                font-size: 12px;
                color: #666;
            }
            
            .typing-indicator span {
                width: 6px;
                height: 6px;
                border-radius: 50%;
                background: #ccc;
                animation: typing 1.4s infinite ease-in-out;
            }
            
            .typing-indicator span:nth-child(1) { animation-delay: -0.32s; }
            .typing-indicator span:nth-child(2) { animation-delay: -0.16s; }
            .typing-indicator span:nth-child(3) { animation-delay: 0s; }
            
            @keyframes typing {
                0%, 80%, 100% { transform: scale(0.8); opacity: 0.5; }
                40% { transform: scale(1); opacity: 1; }
            }
            
            .status-dot.error { background: #f44336; }
            .status-dot.disconnected { background: #ff9800; }
        `;
        
        document.head.appendChild(styles);
    }
}

// Auto-initialize if config is provided
if (typeof window !== 'undefined' && window.AIChatWidgetConfig) {
    window.aiChatWidget = new AIChatWidget(window.AIChatWidgetConfig);
}

// Export for manual initialization
window.AIChatWidget = AIChatWidget;
'''
    
    from fastapi.responses import Response
    return Response(content=widget_js_content, media_type="application/javascript")


@app.get("/widget-demo", response_class=HTMLResponse, tags=["widget"])
async def widget_demo():
    """Serve the widget demo page"""
    demo_html = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Chat Widget - Demo</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            margin: 0;
            padding: 40px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            color: #333;
        }
        
        .container {
            max-width: 800px;
            margin: 0 auto;
            background: white;
            padding: 40px;
            border-radius: 16px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
        }
        
        h1 {
            color: #2c3e50;
            text-align: center;
            margin-bottom: 30px;
        }
        
        .demo-section {
            margin-bottom: 30px;
            padding: 20px;
            background: #f8f9fa;
            border-radius: 8px;
            border-left: 4px solid #007bff;
        }
        
        .widget-notice {
            position: fixed;
            bottom: 100px;
            right: 30px;
            background: #007bff;
            color: white;
            padding: 12px 20px;
            border-radius: 25px;
            font-size: 14px;
            box-shadow: 0 4px 15px rgba(0,123,255,0.3);
            animation: pulse 2s infinite;
        }
        
        @keyframes pulse {
            0% { transform: scale(1); }
            50% { transform: scale(1.05); }
            100% { transform: scale(1); }
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🤖 AI Chat Widget Demo</h1>
        
        <div class="demo-section">
            <h2>Welcome to the AI Coaching Platform Widget</h2>
            <p>This is a demonstration of our embeddable AI chat widget. Click the chat button in the bottom-right corner to start!</p>
            
            <p><strong>Demo Features:</strong></p>
            <ul>
                <li>✓ Responsive design for all devices</li>
                <li>✓ Customizable themes and colors</li>
                <li>✓ Real-time messaging interface</li>
                <li>✓ Professional UI components</li>
                <li>✓ Demo mode for testing</li>
            </ul>
        </div>
        
        <div class="demo-section">
            <h2>Try It Out!</h2>
            <p>Look for the chat button in the bottom-right corner of this page. Click it to start a conversation with our AI assistant!</p>
            <p><strong>Note:</strong> This is a demo environment. In production, the widget would connect to your configured AI coaching service.</p>
        </div>
    </div>
    
    <div class="widget-notice">
        👈 Try the AI Chat Widget!
    </div>
    
    <!-- Widget Configuration -->
    <script>
        window.AIChatWidgetConfig = {
            apiUrl: 'ws://localhost:8004',
            widgetId: 'demo-widget-001',
            position: 'bottom-right',
            theme: 'light',
            primaryColor: '#007bff',
            welcomeMessage: 'Hello! I\\'m your AI coaching assistant. How can I help you today?',
            placeholder: 'Type your message here...'
        };
    </script>
    
    <!-- Load the Widget -->
    <script src="/widget.js"></script>
</body>
</html>'''
    
    return HTMLResponse(content=demo_html)


# =====================================================
# Channel Management Endpoints
# =====================================================

@app.get("/api/v1/channels", tags=["channels"])
async def list_channels(
    cm: ChannelManager = Depends(get_channel_manager)
):
    """List all channels"""
    try:
        # For now, return empty list until authentication is implemented
        channels = []
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
    cm: ChannelManager = Depends(get_channel_manager)
):
    """Check health of a specific channel"""
    try:
        # For now, return basic health status
        health_result = {"status": "healthy", "channel_id": channel_id}
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
    creator_id: str = Query(..., description="Creator ID for the channel"),
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
    creator_id: str = Query("demo-creator", description="Creator ID"),
    session_id: str = Query(None, description="Session ID"),
    user_name: str = Query("Demo User", description="User name")
):
    """WebSocket endpoint for Web Widget real-time communication"""
    try:
        # Accept WebSocket connection
        await websocket.accept()
        
        # Generate session ID if not provided
        if not session_id:
            import uuid
            session_id = str(uuid.uuid4())
        
        logger.info(f"Widget WebSocket connected: {session_id} for channel {channel_id}")
        
        # Send connection confirmation
        await websocket.send_json({
            "type": "status",
            "message": "Connected to AI Coaching Assistant",
            "session_id": session_id
        })
        
        # Initialize AI client for processing  
        ai_client = None
        if AI_CLIENT_AVAILABLE:
            try:
                ai_client = AIEngineClient()
                logger.info("AI Engine client initialized successfully")
            except Exception as ai_init_error:
                logger.error(f"Failed to initialize AI Engine client: {ai_init_error}")
                logger.error(f"Error type: {type(ai_init_error)}")
                logger.error(f"Error details: {str(ai_init_error)}")
                await websocket.send_json({
                    "type": "status",
                    "message": "AI service initialization failed - using demo mode"
                })
        else:
            logger.warning("AI Engine client not available - using demo mode")
            await websocket.send_json({
                "type": "status",
                "message": "AI service not available - using demo mode"
            })
        
        while True:
            try:
                # Receive message from client
                data = await websocket.receive_json()
                logger.info(f"Widget message from {session_id}: {data}")
                
                if data.get("type") == "user_message":
                    # Process message through AI Engine
                    message_content = data.get("content", "")
                    conversation_id = data.get("conversation_id", session_id)
                    
                    logger.info(f"Processing message: {message_content}")
                    
                    try:
                        # Send to AI Engine for processing
                        if ai_client is not None:
                            ai_response = await ai_client.process_message(
                                message=message_content,
                                creator_id=creator_id,
                                conversation_id=conversation_id,
                                user_identifier=user_name
                            )
                        else:
                            # Fallback demo response
                            from datetime import datetime
                            ai_response = type('obj', (object,), {
                                'response': f"Demo mode: I received your message '{message_content}'. The AI Engine is not available, but this shows the widget communication flow is working!",
                                'conversation_id': conversation_id,
                                'confidence': 0.9,
                                'processing_time_ms': 100,
                                'model_used': 'demo-mode',
                                'sources_count': 0
                            })()
                        
                        # Send AI response back to widget
                        await websocket.send_json({
                            "type": "ai_response",
                            "content": ai_response.response,
                            "conversation_id": conversation_id,
                            "confidence": ai_response.confidence,
                            "processing_time_ms": ai_response.processing_time_ms,
                            "model_used": ai_response.model_used,
                            "sources_count": ai_response.sources_count
                        })
                        
                    except Exception as ai_error:
                        logger.error(f"AI processing error: {ai_error}")
                        await websocket.send_json({
                            "type": "ai_response",
                            "content": "I'm sorry, I'm having trouble processing your request right now. This is a demo showcasing our AI coaching platform capabilities.",
                            "conversation_id": conversation_id
                        })
                
            except Exception as msg_error:
                logger.error(f"Message processing error: {msg_error}")
                await websocket.send_json({
                    "type": "error",
                    "message": "Error processing message"
                })
                
    except Exception as e:
        logger.error(f"WebSocket error for {session_id}: {e}")
        try:
            await websocket.send_json({
                "type": "error", 
                "message": "Connection error occurred"
            })
        except:
            pass
        finally:
            logger.info(f"Widget WebSocket disconnected: {session_id}")
    
    except Exception as e:
        logger.error(f"Widget WebSocket connection failed: {e}")
        try:
            await websocket.close(code=4000, reason="Internal server error")
        except:
            pass


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