"""
Channel Service - MVP Coaching AI Platform
Handles real-time communication, WebSocket connections, and messaging
"""

import logging
from contextlib import asynccontextmanager
from typing import Dict

from fastapi import FastAPI, HTTPException, status, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from shared.config.settings import validate_service_environment
# Centralized environment constants and configuration management
from shared.config.env_constants import CORS_ORIGINS, REQUIRED_VARS_BY_SERVICE, get_env_value

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Environment variables validation using centralized configuration
required_env_vars = REQUIRED_VARS_BY_SERVICE["channel_service"]

validate_service_environment(required_env_vars, logger)


# WebSocket connection manager (basic implementation)
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
    
    async def connect(self, websocket: WebSocket, session_id: str):
        await websocket.accept()
        self.active_connections[session_id] = websocket
        logger.info(f"WebSocket connected: {session_id}")
    
    def disconnect(self, session_id: str):
        if session_id in self.active_connections:
            del self.active_connections[session_id]
            logger.info(f"WebSocket disconnected: {session_id}")
    
    async def send_message(self, session_id: str, message: dict):
        if session_id in self.active_connections:
            websocket = self.active_connections[session_id]
            await websocket.send_json(message)


manager = ConnectionManager()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    logger.info("🚀 Channel Service starting up...")
    
    # Startup logic here
    # - Database connection
    # - Redis connection
    # - Service connectivity checks
    # - WebSocket manager initialization
    
    yield
    
    logger.info("🛑 Channel Service shutting down...")
    # Cleanup logic here


# Create FastAPI application
app = FastAPI(
    title="Channel Service API",
    description="Real-time communication service for MVP Coaching AI Platform",
    version="1.0.0",
    lifespan=lifespan,
    openapi_tags=[
        {
            "name": "websocket",
            "description": "WebSocket communication"
        },
        {
            "name": "sessions",
            "description": "User session management"
        },
        {
            "name": "messages",
            "description": "Message handling"
        },
        {
            "name": "health",
            "description": "Service health checks"
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


@app.get("/health", tags=["health"])
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "channel-service",
        "version": "1.0.0",
        "active_connections": len(manager.active_connections)
    }


@app.get("/ready", tags=["health"])
async def readiness_check():
    """Readiness check endpoint"""
    # TODO: Check database, Redis, and service connectivity
    return {
        "status": "ready",
        "service": "channel-service",
        "checks": {
            "database": "connected",
            "redis": "connected",
            "auth_service": "connected",
            "ai_engine_service": "connected"
        }
    }


@app.get("/", tags=["health"])
async def root():
    """Root endpoint"""
    return {
        "message": "Channel Service API",
        "version": "1.0.0",
        "docs": "/docs"
    }


# WebSocket endpoint
@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """WebSocket endpoint for real-time communication"""
    await manager.connect(websocket, session_id)
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_json()
            logger.info(f"Received message from {session_id}: {data}")
            
            # TODO: Implement message processing in task 8
            # - Validate message
            # - Forward to AI Engine
            # - Store in database
            # - Send response
            
            # For now, echo the message back
            response = {
                "type": "response",
                "message": f"Echo: {data.get('message', '')}",
                "session_id": session_id,
                "status": "not_implemented"
            }
            
            await manager.send_message(session_id, response)
            
    except WebSocketDisconnect:
        manager.disconnect(session_id)
    except Exception as e:
        logger.error(f"WebSocket error for {session_id}: {str(e)}")
        manager.disconnect(session_id)


# Session management endpoints (to be implemented in subsequent tasks)
@app.post("/api/v1/channels/sessions", tags=["sessions"])
async def create_session():
    """Create a new user session"""
    # TODO: Implement in task 2.4
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Endpoint will be implemented in task 2.4"
    )


@app.get("/api/v1/channels/sessions/{session_id}", tags=["sessions"])
async def get_session(session_id: str):
    """Get session information"""
    # TODO: Implement in task 2.4
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Endpoint will be implemented in task 2.4"
    )


# Message handling endpoints
@app.post("/api/v1/channels/messages", tags=["messages"])
async def send_message():
    """Send a message through the channel"""
    # TODO: Implement in task 8
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Endpoint will be implemented in task 8"
    )


@app.get("/api/v1/channels/messages/{session_id}", tags=["messages"])
async def get_messages(session_id: str):
    """Get message history for a session"""
    # TODO: Implement in task 8
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Endpoint will be implemented in task 8"
    )


# Connection status endpoint
@app.get("/api/v1/channels/connections", tags=["websocket"])
async def get_active_connections():
    """Get active WebSocket connections"""
    return {
        "active_connections": len(manager.active_connections),
        "connection_ids": list(manager.active_connections.keys())
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8004)