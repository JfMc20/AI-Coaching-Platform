---
inclusion: always
---

# WebSocket & Real-Time Communication Guidelines

## WebSocket Connection Management

### Core WebSocket Manager Implementation
The Channel Service MUST implement scalable WebSocket management:

```python
import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional
from fastapi import WebSocket, WebSocketDisconnect
import redis.asyncio as redis
from redis.exceptions import (
    ConnectionError as RedisConnectionError,
    TimeoutError as RedisTimeoutError,
    ResponseError as RedisResponseError
)

logger = logging.getLogger(__name__)

class WebSocketManager:
    """Manages WebSocket connections with Redis for scalability."""
    
    def __init__(self, redis_url: str = "redis://redis:6379"):
        self.active_connections: Dict[str, WebSocket] = {}
        self.redis_client = None
        self.redis_url = redis_url
        self._connections_lock = asyncio.Lock()
    
    async def _get_redis_client(self):
        """Lazy initialization of async Redis client."""
        if self.redis_client is None:
            try:
                self.redis_client = redis.from_url(
                    self.redis_url, 
                    decode_responses=True
                )
                await self.redis_client.ping()
                logger.info("Redis client initialized successfully")
            except Exception as e:
                logger.exception(f"Failed to initialize Redis client: {e}")
                raise
        return self.redis_client
    
    async def connect(
        self, 
        websocket: WebSocket, 
        creator_id: str, 
        session_id: str
    ):
        """Accept WebSocket connection and register it."""
        await websocket.accept()
        connection_id = f"{creator_id}_{session_id}"
        
        # Thread-safe connection registration
        async with self._connections_lock:
            self.active_connections[connection_id] = websocket
        
        # Register in Redis for scalability
        try:
            redis_client = await self._get_redis_client()
            await redis_client.hset(
                "active_connections",
                connection_id,
                json.dumps({
                    "creator_id": creator_id,
                    "session_id": session_id,
                    "connected_at": datetime.utcnow().isoformat()
                })
            )
            logger.info(f"WebSocket connected: {connection_id}")
        except Exception as e:
            logger.exception(f"Failed to register connection: {e}")
    
    async def disconnect(self, connection_id: str):
        """Disconnect WebSocket and cleanup."""
        async with self._connections_lock:
            websocket = self.active_connections.get(connection_id)
        
        if websocket:
            try:
                await websocket.close()
            except Exception as e:
                logger.exception(f"Error closing websocket: {e}")
            finally:
                await self._remove_connection(connection_id)
    
    async def send_message(self, connection_id: str, message: dict):
        """Send message to specific connection."""
        async with self._connections_lock:
            websocket = self.active_connections.get(connection_id)
        
        if websocket:
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.exception(f"Failed to send message: {e}")
                await self._remove_connection(connection_id)
    
    async def broadcast_to_creator(self, creator_id: str, message: dict):
        """Broadcast message to all creator's connections."""
        connections = await self.get_creator_connections(creator_id)
        
        tasks = [
            self.send_message(conn_id, message) 
            for conn_id in connections
        ]
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
    
    async def get_creator_connections(self, creator_id: str) -> List[str]:
        """Get all active connections for a creator."""
        try:
            redis_client = await self._get_redis_client()
            all_connections = await redis_client.hgetall("active_connections")
            
            creator_connections = []
            for connection_id, connection_data in all_connections.items():
                try:
                    data = json.loads(connection_data)
                    if data.get("creator_id") == creator_id:
                        # Verify connection is still active locally
                        async with self._connections_lock:
                            is_active = connection_id in self.active_connections
                        
                        if is_active:
                            creator_connections.append(connection_id)
                        else:
                            # Clean up stale connection
                            await redis_client.hdel("active_connections", connection_id)
                except json.JSONDecodeError:
                    await redis_client.hdel("active_connections", connection_id)
            
            return creator_connections
            
        except Exception as e:
            logger.exception(f"Error getting creator connections: {e}")
            return []
    
    async def _remove_connection(self, connection_id: str):
        """Remove connection from local and Redis registries."""
        try:
            # Remove from local registry
            async with self._connections_lock:
                if connection_id in self.active_connections:
                    del self.active_connections[connection_id]
            
            # Remove from Redis
            redis_client = await self._get_redis_client()
            await redis_client.hdel("active_connections", connection_id)
            
            logger.info(f"Removed connection: {connection_id}")
            
        except Exception as e:
            logger.exception(f"Error removing connection: {e}")
    
    async def shutdown(self):
        """Graceful shutdown of WebSocketManager."""
        logger.info("Starting WebSocketManager shutdown...")
        
        try:
            # Get all active connections
            async with self._connections_lock:
                active_connection_ids = list(self.active_connections.keys())
            
            # Close all WebSocket connections
            close_tasks = []
            for connection_id in active_connection_ids:
                async with self._connections_lock:
                    websocket = self.active_connections.get(connection_id)
                
                if websocket:
                    close_tasks.append(
                        self._close_websocket_safely(websocket, connection_id)
                    )
            
            # Wait for all connections to close with timeout
            if close_tasks:
                try:
                    await asyncio.wait_for(
                        asyncio.gather(*close_tasks, return_exceptions=True),
                        timeout=30.0
                    )
                except asyncio.TimeoutError:
                    logger.warning("Timeout waiting for connections to close")
            
            # Clear local registry
            async with self._connections_lock:
                self.active_connections.clear()
            
            # Close Redis client
            if self.redis_client:
                await self.redis_client.close()
            
            logger.info("WebSocketManager shutdown completed")
            
        except Exception as e:
            logger.exception(f"Error during shutdown: {e}")
    
    async def _close_websocket_safely(self, websocket: WebSocket, connection_id: str):
        """Safely close WebSocket connection."""
        try:
            await websocket.close(code=1001, reason="Server shutdown")
            
            # Remove from Redis
            try:
                if self.redis_client:
                    await self.redis_client.hdel("active_connections", connection_id)
            except Exception:
                pass  # Best effort cleanup
            
        except Exception as e:
            logger.exception(f"Error closing WebSocket {connection_id}: {e}")
```

## Message Processing Pipeline

### Async Message Handler
Implement comprehensive message processing:

```python
from typing import Dict, Any, Optional
from enum import Enum
import uuid
from datetime import datetime

class MessageType(Enum):
    USER_MESSAGE = "user_message"
    AI_RESPONSE = "ai_response"
    TYPING_INDICATOR = "typing_indicator"
    CONNECTION_STATUS = "connection_status"
    ERROR = "error"

class MessageProcessor:
    """Process messages between users and AI with proper error handling."""
    
    def __init__(self, ai_engine_client, websocket_manager, rate_limiter):
        self.ai_engine = ai_engine_client
        self.websocket_manager = websocket_manager
        self.rate_limiter = rate_limiter
    
    async def process_user_message(
        self,
        websocket: WebSocket,
        message_data: Dict[str, Any],
        creator_id: str,
        session_id: str
    ) -> None:
        """Process incoming user message and generate AI response."""
        
        connection_id = f"{creator_id}_{session_id}"
        
        try:
            # Validate message
            user_message = message_data.get("content", "").strip()
            if not user_message:
                await self._send_error(websocket, "Empty message not allowed")
                return
            
            # Check rate limiting (identifier first: creator_id, action, session_id)
            if not await self.rate_limiter.check_rate_limit(
                creator_id, "chat", session_id
            ):
                await self._send_error(websocket, "Rate limit exceeded")
                return
            
            # Send typing indicator
            await self._send_typing_indicator(websocket, True)
            
            # Process with AI Engine
            ai_response = await self.ai_engine.process_query(
                query=user_message,
                creator_id=creator_id,
                session_id=session_id
            )
            
            # Send AI response
            await self._send_ai_response(websocket, ai_response)
            
        except Exception as e:
            logger.exception(f"Error processing message: {e}")
            await self._send_error(websocket, "Failed to process message")
        finally:
            # Always stop typing indicator
            await self._send_typing_indicator(websocket, False)
    
    async def _send_ai_response(self, websocket: WebSocket, response: Dict[str, Any]):
        """Send AI response to WebSocket."""
        
        message = {
            "type": MessageType.AI_RESPONSE.value,
            "content": response.get("response", ""),
            "confidence": response.get("confidence", 0.0),
            "sources": response.get("sources", []),
            "timestamp": datetime.utcnow().isoformat(),
            "message_id": str(uuid.uuid4())
        }
        
        await websocket.send_json(message)
    
    async def _send_typing_indicator(self, websocket: WebSocket, is_typing: bool):
        """Send typing indicator status."""
        
        message = {
            "type": MessageType.TYPING_INDICATOR.value,
            "is_typing": is_typing,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        await websocket.send_json(message)
    
    async def _send_error(self, websocket: WebSocket, error_message: str):
        """Send error message to WebSocket."""
        
        message = {
            "type": MessageType.ERROR.value,
            "error": error_message,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        await websocket.send_json(message)
    
    async def _send_connection_status(
        self, 
        websocket: WebSocket, 
        status: str,
        details: Optional[Dict[str, Any]] = None
    ):
        """Send connection status update."""
        
        message = {
            "type": MessageType.CONNECTION_STATUS.value,
            "status": status,
            "details": details or {},
            "timestamp": datetime.utcnow().isoformat()
        }
        
        await websocket.send_json(message)
```

## WebSocket Endpoint Implementation

### FastAPI WebSocket Endpoint
Implement production-ready WebSocket endpoint:

```python
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, Query
from fastapi.responses import HTMLResponse
from typing import Optional
import json
import uuid
import logging

logger = logging.getLogger(__name__)

async def validate_websocket_token(token: str) -> Optional[Dict[str, Any]]:
    """Validate WebSocket authentication token."""
    try:
        # TODO: Implement your JWT validation logic here
        # This should validate the token and return claims
        # Example: return jwt_manager.verify_token(token)
        pass
    except Exception as e:
        logger.exception(f"Token validation failed: {e}")
        return None

app = FastAPI()
websocket_manager = WebSocketManager()
message_processor = MessageProcessor(ai_engine_client, websocket_manager, rate_limiter)

@app.websocket("/api/v1/channels/widget/{creator_id}/connect")
async def websocket_endpoint(
    websocket: WebSocket,
    creator_id: str,
    session_id: Optional[str] = None,
    token: Optional[str] = Query(None)
):
    """WebSocket endpoint for widget connections with authentication."""
    
    # Authenticate connection before accepting
    try:
        if not token:
            await websocket.close(code=4001, reason="Authentication token required")
            return
        
        # Validate token and extract claims
        auth_claims = await validate_websocket_token(token)
        if not auth_claims or auth_claims.get("creator_id") != creator_id:
            await websocket.close(code=4003, reason="Invalid or unauthorized token")
            return
        
        # Generate session ID if not provided
        if not session_id:
            session_id = str(uuid.uuid4())
        
        connection_id = f"{creator_id}_{session_id}"
        
        logger.info(f"Authenticated WebSocket connection: {connection_id}")
        
    except Exception as e:
        logger.exception(f"WebSocket authentication failed: {e}")
        await websocket.close(code=4003, reason="Authentication failed")
        return
    
    try:
        # Establish connection
        await websocket_manager.connect(websocket, creator_id, session_id)
        
        # Send connection confirmation
        await message_processor._send_connection_status(
            websocket, "connected", {"session_id": session_id}
        )
        
        # Message handling loop
        while True:
            try:
                # Receive message
                data = await websocket.receive_text()
                message_data = json.loads(data)
                
                # Process based on message type
                message_type = message_data.get("type")
                
                if message_type == "user_message":
                    await message_processor.process_user_message(
                        websocket, message_data, creator_id, session_id
                    )
                elif message_type == "ping":
                    await websocket.send_json({"type": "pong"})
                else:
                    await message_processor._send_error(
                        websocket, f"Unknown message type: {message_type}"
                    )
                    
            except WebSocketDisconnect:
                logger.info(f"WebSocket disconnected: {connection_id}")
                break
            except json.JSONDecodeError:
                await message_processor._send_error(
                    websocket, "Invalid JSON format"
                )
            except Exception as e:
                logger.exception(f"Error in WebSocket communication: {e}")
                await message_processor._send_error(
                    websocket, "Internal server error"
                )
                break
    
    except Exception as e:
        logger.exception(f"WebSocket connection error: {e}")
    
    finally:
        # Cleanup connection
        await websocket_manager.disconnect(connection_id)

# Graceful shutdown handling
@app.on_event("shutdown")
async def shutdown_event():
    """Handle application shutdown."""
    await websocket_manager.shutdown()
```

## Connection Health & Monitoring

### Connection Health Monitoring
Implement WebSocket connection health checks:

```python
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List

class ConnectionHealthMonitor:
    """Monitor WebSocket connection health and cleanup stale connections."""
    
    def __init__(self, websocket_manager, check_interval: int = 30):
        self.websocket_manager = websocket_manager
        self.check_interval = check_interval
        self.last_ping_times: Dict[str, datetime] = {}
        self._monitoring_task = None
    
    async def start_monitoring(self):
        """Start connection health monitoring with proper error handling."""
        if self._monitoring_task is None:
            try:
                self._monitoring_task = asyncio.create_task(self._monitor_connections())
                
                # Add callback to log uncaught exceptions
                def task_done_callback(task):
                    if task.exception():
                        logger.exception(f"Connection monitoring task failed: {task.exception()}")
                
                self._monitoring_task.add_done_callback(task_done_callback)
                logger.info("Connection health monitoring started")
                
            except Exception as e:
                logger.exception(f"Failed to start connection monitoring: {e}")
                if self._monitoring_task:
                    self._monitoring_task.cancel()
                    self._monitoring_task = None
                raise
    
    async def stop_monitoring(self):
        """Stop connection health monitoring with proper cleanup."""
        if self._monitoring_task:
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass
            self._monitoring_task = None
            logger.info("Connection health monitoring stopped")
    
    async def _monitor_connections(self):
        """Monitor connection health periodically."""
        while True:
            try:
                await asyncio.sleep(self.check_interval)
                await self._check_connection_health()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.exception(f"Error in connection monitoring: {e}")
    
    async def _check_connection_health(self):
        """Check health of all active connections."""
        current_time = datetime.utcnow()
        stale_connections = []
        
        # Get all active connections
        async with self.websocket_manager._connections_lock:
            connection_ids = list(self.websocket_manager.active_connections.keys())
        
        for connection_id in connection_ids:
            # Check if connection responded to recent ping
            last_ping = self.last_ping_times.get(connection_id)
            
            if last_ping and (current_time - last_ping) > timedelta(minutes=2):
                stale_connections.append(connection_id)
            else:
                # Send ping to check connection
                await self._ping_connection(connection_id)
        
        # Cleanup stale connections
        for connection_id in stale_connections:
            logger.warning(f"Removing stale connection: {connection_id}")
            await self.websocket_manager.disconnect(connection_id)
            self.last_ping_times.pop(connection_id, None)
    
    async def _ping_connection(self, connection_id: str):
        """Send ping to connection and track response time."""
        try:
            ping_message = {
                "type": "ping",
                "timestamp": datetime.utcnow().isoformat()
            }
            
            await self.websocket_manager.send_message(connection_id, ping_message)
            self.last_ping_times[connection_id] = datetime.utcnow()
            
        except Exception as e:
            logger.exception(f"Failed to ping connection {connection_id}: {e}")
    
    def record_pong(self, connection_id: str):
        """Record pong response from connection."""
        self.last_ping_times[connection_id] = datetime.utcnow()
    
    async def get_connection_stats(self) -> Dict[str, Any]:
        """Get connection statistics."""
        async with self.websocket_manager._connections_lock:
            total_connections = len(self.websocket_manager.active_connections)
        
        # Group by creator
        creator_stats = {}
        try:
            redis_client = await self.websocket_manager._get_redis_client()
            all_connections = await redis_client.hgetall("active_connections")
            
            for connection_data in all_connections.values():
                try:
                    data = json.loads(connection_data)
                    creator_id = data.get("creator_id")
                    if creator_id:
                        creator_stats[creator_id] = creator_stats.get(creator_id, 0) + 1
                except json.JSONDecodeError:
                    continue
        
        except Exception as e:
            logger.exception(f"Error getting connection stats: {e}")
        
        return {
            "total_connections": total_connections,
            "connections_by_creator": creator_stats,
            "monitoring_active": self._monitoring_task is not None,
            "last_check": datetime.utcnow().isoformat()
        }
```

## Multi-Channel Support Architecture

### Channel Abstraction Layer
Design for future multi-channel expansion:

```python
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

class ChannelHandler(ABC):
    """Abstract base class for channel handlers."""
    
    @abstractmethod
    async def send_message(self, recipient: str, message: Dict[str, Any]) -> bool:
        """Send message through this channel."""
        pass
    
    @abstractmethod
    async def receive_message(self, raw_message: Any) -> Optional[Dict[str, Any]]:
        """Process incoming message from this channel."""
        pass
    
    @abstractmethod
    async def validate_recipient(self, recipient: str) -> bool:
        """Validate recipient identifier for this channel."""
        pass

class WebWidgetHandler(ChannelHandler):
    """Handler for web widget channel."""
    
    def __init__(self, websocket_manager):
        self.websocket_manager = websocket_manager
    
    async def send_message(self, recipient: str, message: Dict[str, Any]) -> bool:
        """Send message via WebSocket."""
        try:
            await self.websocket_manager.send_message(recipient, message)
            return True
        except Exception as e:
            logger.exception(f"Failed to send widget message: {e}")
            return False
    
    async def receive_message(self, raw_message: Any) -> Optional[Dict[str, Any]]:
        """Process WebSocket message."""
        try:
            if isinstance(raw_message, str):
                return json.loads(raw_message)
            return raw_message
        except json.JSONDecodeError:
            return None
    
    async def validate_recipient(self, recipient: str) -> bool:
        """Validate WebSocket connection ID."""
        return "_" in recipient and len(recipient.split("_")) == 2

class ChannelRouter:
    """Routes messages to appropriate channel handlers."""
    
    def __init__(self):
        self.handlers: Dict[str, ChannelHandler] = {}
    
    def register_handler(self, channel_type: str, handler: ChannelHandler):
        """Register a channel handler."""
        self.handlers[channel_type] = handler
        logger.info(f"Registered handler for channel: {channel_type}")
    
    async def send_message(
        self, 
        channel_type: str, 
        recipient: str, 
        message: Dict[str, Any]
    ) -> bool:
        """Send message through specified channel."""
        
        handler = self.handlers.get(channel_type)
        if not handler:
            logger.error(f"No handler for channel type: {channel_type}")
            return False
        
        if not await handler.validate_recipient(recipient):
            logger.error(f"Invalid recipient for {channel_type}: {recipient}")
            return False
        
        return await handler.send_message(recipient, message)
    
    async def process_message(
        self, 
        channel_type: str, 
        raw_message: Any
    ) -> Optional[Dict[str, Any]]:
        """Process incoming message from specified channel."""
        
        handler = self.handlers.get(channel_type)
        if not handler:
            logger.error(f"No handler for channel type: {channel_type}")
            return None
        
        return await handler.receive_message(raw_message)

# Usage example
channel_router = ChannelRouter()
channel_router.register_handler("widget", WebWidgetHandler(websocket_manager))

# Future channel handlers can be added:
# channel_router.register_handler("whatsapp", WhatsAppHandler())
# channel_router.register_handler("telegram", TelegramHandler())
```