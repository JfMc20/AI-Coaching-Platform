"""
Redis Streams-based message queue for MVP Coaching AI Platform
Handles asynchronous message processing with multi-tenant support
"""

import json
import logging
from typing import Optional, Dict, Any, Callable, Awaitable
from datetime import datetime
import asyncio
import uuid
from .redis_client import RedisClient

logger = logging.getLogger(__name__)


class MessageQueue:
    """Redis Streams-based message queue with multi-tenant support"""
    
    def __init__(self, redis_client: RedisClient, stream_prefix: str = "queue"):
        """
        Initialize message queue
        
        Args:
            redis_client: Redis client instance
            stream_prefix: Prefix for stream names
        """
        self.redis = redis_client
        self.stream_prefix = stream_prefix
        self._consumers: Dict[str, bool] = {}  # Track active consumers
    
    def _get_stream_name(self, creator_id: str, queue_name: str) -> str:
        """Generate stream name with tenant isolation"""
        return f"tenant:{creator_id}:{self.stream_prefix}:{queue_name}"
    
    def _get_consumer_group_name(self, queue_name: str) -> str:
        """Generate consumer group name"""
        return f"{queue_name}_consumers"
    
    def _get_consumer_name(self, queue_name: str) -> str:
        """Generate unique consumer name"""
        return f"{queue_name}_consumer_{uuid.uuid4().hex[:8]}"
    
    async def create_stream(self, creator_id: str, queue_name: str) -> bool:
        """
        Create a stream and consumer group
        
        Args:
            creator_id: Creator/tenant ID
            queue_name: Queue name
            
        Returns:
            True if successful
        """
        try:
            client = await self.redis.get_client()
            stream_name = self._get_stream_name(creator_id, queue_name)
            group_name = self._get_consumer_group_name(queue_name)
            
            # Create consumer group (this also creates the stream if it doesn't exist)
            try:
                await client.xgroup_create(stream_name, group_name, id="0", mkstream=True)
                logger.info(f"Created stream {stream_name} with consumer group {group_name}")
            except Exception as e:
                if "BUSYGROUP" in str(e):
                    # Consumer group already exists
                    logger.debug(f"Consumer group {group_name} already exists for stream {stream_name}")
                else:
                    raise e
            
            return True
        except Exception as e:
            logger.error(f"Failed to create stream {queue_name} for creator {creator_id}: {e}")
            return False
    
    async def send_message(
        self, 
        creator_id: str, 
        queue_name: str, 
        message_type: str,
        data: Dict[str, Any],
        priority: str = "normal"
    ) -> Optional[str]:
        """
        Send a message to the queue
        
        Args:
            creator_id: Creator/tenant ID
            queue_name: Queue name
            message_type: Type of message
            data: Message data
            priority: Message priority (high, normal, low)
            
        Returns:
            Message ID if successful
        """
        try:
            client = await self.redis.get_client()
            stream_name = self._get_stream_name(creator_id, queue_name)
            
            # Prepare message
            message = {
                "id": str(uuid.uuid4()),
                "type": message_type,
                "creator_id": creator_id,
                "priority": priority,
                "data": json.dumps(data),
                "timestamp": datetime.utcnow().isoformat(),
                "retry_count": "0"
            }
            
            # Send to stream
            message_id = await client.xadd(stream_name, message)
            logger.debug(f"Sent message {message['id']} to queue {queue_name}")
            
            return message_id
        except Exception as e:
            logger.error(f"Failed to send message to queue {queue_name} for creator {creator_id}: {e}")
            return None
    
    async def consume_messages(
        self, 
        creator_id: str, 
        queue_name: str,
        handler: Callable[[Dict[str, Any]], Awaitable[bool]],
        batch_size: int = 10,
        block_time: int = 1000  # milliseconds
    ) -> None:
        """
        Consume messages from the queue
        
        Args:
            creator_id: Creator/tenant ID
            queue_name: Queue name
            handler: Async function to handle messages
            batch_size: Number of messages to process at once
            block_time: Time to block waiting for messages (ms)
        """
        client = await self.redis.get_client()
        stream_name = self._get_stream_name(creator_id, queue_name)
        group_name = self._get_consumer_group_name(queue_name)
        consumer_name = self._get_consumer_name(queue_name)
        
        # Ensure stream and consumer group exist
        await self.create_stream(creator_id, queue_name)
        
        consumer_key = f"{creator_id}:{queue_name}:{consumer_name}"
        self._consumers[consumer_key] = True
        
        logger.info(f"Starting consumer {consumer_name} for queue {queue_name}")
        
        try:
            while self._consumers.get(consumer_key, False):
                try:
                    # Read messages from stream
                    messages = await client.xreadgroup(
                        group_name,
                        consumer_name,
                        {stream_name: ">"},
                        count=batch_size,
                        block=block_time
                    )
                    
                    if not messages:
                        continue
                    
                    # Process messages
                    for stream, stream_messages in messages:
                        for message_id, fields in stream_messages:
                            try:
                                # Parse message
                                message_data = {
                                    "message_id": message_id,
                                    "id": fields.get("id"),
                                    "type": fields.get("type"),
                                    "creator_id": fields.get("creator_id"),
                                    "priority": fields.get("priority", "normal"),
                                    "data": json.loads(fields.get("data", "{}")),
                                    "timestamp": fields.get("timestamp"),
                                    "retry_count": int(fields.get("retry_count", 0))
                                }
                                
                                # Handle message
                                success = await handler(message_data)
                                
                                if success:
                                    # Acknowledge message
                                    await client.xack(stream_name, group_name, message_id)
                                    logger.debug(f"Processed message {message_data['id']}")
                                else:
                                    # Handle retry logic
                                    await self._handle_message_retry(
                                        client, stream_name, group_name, message_id, message_data
                                    )
                                
                            except Exception as e:
                                logger.error(f"Error processing message {message_id}: {e}")
                                # Handle retry logic
                                await self._handle_message_retry(
                                    client, stream_name, group_name, message_id, 
                                    {"retry_count": int(fields.get("retry_count", 0))}
                                )
                
                except Exception as e:
                    logger.error(f"Error in message consumer loop: {e}")
                    await asyncio.sleep(5)  # Wait before retrying
        
        finally:
            logger.info(f"Stopping consumer {consumer_name} for queue {queue_name}")
            self._consumers.pop(consumer_key, None)
    
    async def _handle_message_retry(
        self, 
        client, 
        stream_name: str, 
        group_name: str, 
        message_id: str,
        message_data: Dict[str, Any],
        max_retries: int = 3
    ) -> None:
        """Handle message retry logic"""
        retry_count = message_data.get("retry_count", 0)
        
        if retry_count < max_retries:
            # Increment retry count and re-add to stream
            retry_count += 1
            retry_message = {
                "id": message_data.get("id", str(uuid.uuid4())),
                "type": message_data.get("type", "unknown"),
                "creator_id": message_data.get("creator_id"),
                "priority": message_data.get("priority", "normal"),
                "data": json.dumps(message_data.get("data", {})),
                "timestamp": datetime.utcnow().isoformat(),
                "retry_count": str(retry_count),
                "original_message_id": message_id
            }
            
            await client.xadd(stream_name, retry_message)
            logger.warning(f"Retrying message {message_data.get('id')} (attempt {retry_count})")
        else:
            # Move to dead letter queue
            dead_letter_stream = f"{stream_name}:dead_letter"
            dead_letter_message = {
                "original_message_id": message_id,
                "failed_at": datetime.utcnow().isoformat(),
                "retry_count": str(retry_count),
                **{k: v for k, v in message_data.items() if k != "retry_count"}
            }
            
            await client.xadd(dead_letter_stream, dead_letter_message)
            logger.error(f"Message {message_data.get('id')} moved to dead letter queue after {retry_count} retries")
        
        # Acknowledge original message
        await client.xack(stream_name, group_name, message_id)
    
    async def stop_consumer(self, creator_id: str, queue_name: str, consumer_name: str) -> None:
        """Stop a specific consumer"""
        consumer_key = f"{creator_id}:{queue_name}:{consumer_name}"
        self._consumers[consumer_key] = False
    
    async def stop_all_consumers(self) -> None:
        """Stop all consumers"""
        for key in self._consumers:
            self._consumers[key] = False
    
    async def get_queue_info(self, creator_id: str, queue_name: str) -> Dict[str, Any]:
        """
        Get information about a queue
        
        Args:
            creator_id: Creator/tenant ID
            queue_name: Queue name
            
        Returns:
            Queue information
        """
        try:
            client = await self.redis.get_client()
            stream_name = self._get_stream_name(creator_id, queue_name)
            
            # Get stream info
            info = await client.xinfo_stream(stream_name)
            
            return {
                "stream_name": stream_name,
                "length": info.get("length", 0),
                "first_entry": info.get("first-entry"),
                "last_entry": info.get("last-entry"),
                "groups": info.get("groups", 0)
            }
        except Exception as e:
            logger.error(f"Failed to get queue info for {queue_name}: {e}")
            return {}
    
    async def purge_queue(self, creator_id: str, queue_name: str) -> bool:
        """
        Purge all messages from a queue
        
        Args:
            creator_id: Creator/tenant ID
            queue_name: Queue name
            
        Returns:
            True if successful
        """
        try:
            client = await self.redis.get_client()
            stream_name = self._get_stream_name(creator_id, queue_name)
            
            # Delete the stream (this removes all messages)
            await client.delete(stream_name)
            
            # Recreate the stream and consumer group
            await self.create_stream(creator_id, queue_name)
            
            logger.info(f"Purged queue {queue_name} for creator {creator_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to purge queue {queue_name} for creator {creator_id}: {e}")
            return False


# Global message queue instance
_message_queue: Optional[MessageQueue] = None


def get_message_queue() -> MessageQueue:
    """Get global message queue instance"""
    global _message_queue
    if _message_queue is None:
        from .redis_client import get_redis_client
        _message_queue = MessageQueue(get_redis_client())
    return _message_queue