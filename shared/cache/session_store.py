"""
Redis-based session storage for MVP Coaching AI Platform
Handles user sessions with multi-tenant support
"""

import json
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import uuid
from .redis_client import RedisClient

logger = logging.getLogger(__name__)


class SessionStore:
    """Redis-based session storage with multi-tenant support"""
    
    def __init__(self, redis_client: RedisClient, default_ttl: int = 86400):  # 24 hours
        """
        Initialize session store
        
        Args:
            redis_client: Redis client instance
            default_ttl: Default session TTL in seconds
        """
        self.redis = redis_client
        self.default_ttl = default_ttl
    
    def _get_session_key(self, session_id: str) -> str:
        """Generate session key"""
        return f"session:{session_id}"
    
    def _get_user_sessions_key(self, creator_id: str, user_id: str) -> str:
        """Generate key for user's active sessions"""
        return f"user_sessions:{user_id}"
    
    async def create_session(
        self, 
        creator_id: str, 
        user_id: Optional[str] = None,
        channel: str = "web_widget",
        metadata: Optional[Dict[str, Any]] = None,
        ttl: Optional[int] = None
    ) -> str:
        """
        Create a new session
        
        Args:
            creator_id: Creator/tenant ID
            user_id: User ID (optional for anonymous sessions)
            channel: Channel type (web_widget, whatsapp, etc.)
            metadata: Additional session metadata
            ttl: Session TTL in seconds
            
        Returns:
            Session ID
        """
        session_id = str(uuid.uuid4())
        
        if ttl is None:
            ttl = self.default_ttl
        
        session_data = {
            "session_id": session_id,
            "creator_id": creator_id,
            "user_id": user_id,
            "channel": channel,
            "metadata": metadata or {},
            "created_at": datetime.utcnow().isoformat(),
            "last_activity": datetime.utcnow().isoformat(),
            "is_active": True
        }
        
        # Store session data
        session_key = self._get_session_key(session_id)
        success = await self.redis.set(creator_id, session_key, session_data, ttl)
        
        if success and user_id:
            # Add to user's active sessions list
            user_sessions_key = self._get_user_sessions_key(creator_id, user_id)
            await self.redis.set(creator_id, f"{user_sessions_key}:{session_id}", session_id, ttl)
        
        logger.info(f"Created session {session_id} for creator {creator_id}")
        return session_id
    
    async def get_session(self, creator_id: str, session_id: str, update_activity: bool = True) -> Optional[Dict[str, Any]]:
        """
        Get session data
        
        Args:
            creator_id: Creator/tenant ID
            session_id: Session ID
            update_activity: Whether to update last activity timestamp
            
        Returns:
            Session data or None if not found
        """
        session_key = self._get_session_key(session_id)
        session_data = await self.redis.get(creator_id, session_key)
        
        if session_data and session_data.get("is_active"):
            if update_activity:
                # Update last activity atomically
                await self.update_session(creator_id, session_id, {})
            return session_data
        
        return None
    
    async def update_session(
        self, 
        creator_id: str, 
        session_id: str, 
        updates: Dict[str, Any]
    ) -> bool:
        """
        Update session data atomically using Lua script
        
        Args:
            creator_id: Creator/tenant ID
            session_id: Session ID
            updates: Data to update
            
        Returns:
            True if successful
        """
        session_key = self._get_session_key(session_id)
        namespaced_key = self.redis._get_namespaced_key(creator_id, session_key)
        
        # Lua script for atomic session update
        lua_script = """
        local key = KEYS[1]
        local updates_json = ARGV[1]
        local current_time = ARGV[2]
        
        -- Get current session data
        local current_data = redis.call('GET', key)
        if not current_data then
            return 0  -- Session not found
        end
        
        -- Parse current data
        local session_data = cjson.decode(current_data)
        if not session_data.is_active then
            return 0  -- Session not active
        end
        
        -- Parse updates
        local updates = cjson.decode(updates_json)
        
        -- Apply updates
        for k, v in pairs(updates) do
            session_data[k] = v
        end
        
        -- Update last activity
        session_data.last_activity = current_time
        
        -- Save updated data with original TTL
        local ttl = redis.call('TTL', key)
        if ttl > 0 then
            redis.call('SETEX', key, ttl, cjson.encode(session_data))
        else
            redis.call('SET', key, cjson.encode(session_data))
        end
        
        return 1  -- Success
        """
        
        try:
            client = await self.redis.get_client()
            
            # Prepare arguments
            updates_json = json.dumps(updates)
            current_time = datetime.utcnow().isoformat()
            
            # Execute Lua script
            result = await client.eval(
                lua_script, 
                1, 
                namespaced_key, 
                updates_json, 
                current_time
            )
            
            if result == 1:
                logger.debug(f"Successfully updated session {session_id} for creator {creator_id}")
                return True
            else:
                logger.debug(f"Session {session_id} not found or inactive for creator {creator_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error updating session {session_id}: {e}")
            return False
    
    async def update_last_activity(self, creator_id: str, session_id: str) -> bool:
        """Update session last activity timestamp"""
        return await self.update_session(
            creator_id, 
            session_id, 
            {"last_activity": datetime.utcnow().isoformat()}
        )
    
    async def end_session(self, creator_id: str, session_id: str) -> bool:
        """
        End a session (mark as inactive)
        
        Args:
            creator_id: Creator/tenant ID
            session_id: Session ID
            
        Returns:
            True if successful
        """
        return await self.update_session(
            creator_id, 
            session_id, 
            {
                "is_active": False,
                "ended_at": datetime.utcnow().isoformat()
            }
        )
    
    async def delete_session(self, creator_id: str, session_id: str) -> bool:
        """
        Delete a session completely
        
        Args:
            creator_id: Creator/tenant ID
            session_id: Session ID
            
        Returns:
            True if successful
        """
        session_key = self._get_session_key(session_id)
        return await self.redis.delete(creator_id, session_key)
    
    async def get_user_sessions(self, creator_id: str, user_id: str) -> List[Dict[str, Any]]:
        """
        Get all active sessions for a user
        
        Args:
            creator_id: Creator/tenant ID
            user_id: User ID
            
        Returns:
            List of active sessions
        """
        # Get session IDs for user
        pattern = f"user_sessions:{user_id}:*"
        session_keys = await self.redis.get_keys_pattern(creator_id, pattern)
        
        sessions = []
        for key in session_keys:
            session_id = key.split(":")[-1]
            session_data = await self.get_session(creator_id, session_id)
            if session_data and session_data.get("is_active"):
                sessions.append(session_data)
        
        return sessions
    
    async def cleanup_expired_sessions(self, creator_id: str) -> int:
        """
        Clean up expired sessions for a creator
        
        Args:
            creator_id: Creator/tenant ID
            
        Returns:
            Number of sessions cleaned up
        """
        # Get all session keys
        pattern = "session:*"
        session_keys = await self.redis.get_keys_pattern(creator_id, pattern)
        
        cleaned_count = 0
        for key in session_keys:
            session_data = await self.redis.get(creator_id, key)
            if not session_data:
                continue
            
            # Check if session is expired based on last activity
            try:
                last_activity = datetime.fromisoformat(session_data.get("last_activity", ""))
                if datetime.utcnow() - last_activity > timedelta(seconds=self.default_ttl):
                    await self.redis.delete(creator_id, key)
                    cleaned_count += 1
            except (ValueError, TypeError):
                # Invalid timestamp, delete session
                await self.redis.delete(creator_id, key)
                cleaned_count += 1
        
        if cleaned_count > 0:
            logger.info(f"Cleaned up {cleaned_count} expired sessions for creator {creator_id}")
        
        return cleaned_count
    
    async def get_session_stats(self, creator_id: str) -> Dict[str, Any]:
        """
        Get session statistics for a creator
        
        Args:
            creator_id: Creator/tenant ID
            
        Returns:
            Session statistics
        """
        # Get all session keys
        pattern = "session:*"
        session_keys = await self.redis.get_keys_pattern(creator_id, pattern)
        
        total_sessions = len(session_keys)
        active_sessions = 0
        channels = {}
        
        for key in session_keys:
            session_data = await self.redis.get(creator_id, key)
            if not session_data:
                continue
            
            if session_data.get("is_active"):
                active_sessions += 1
                
                channel = session_data.get("channel", "unknown")
                channels[channel] = channels.get(channel, 0) + 1
        
        return {
            "total_sessions": total_sessions,
            "active_sessions": active_sessions,
            "inactive_sessions": total_sessions - active_sessions,
            "channels": channels
        }


# Global session store instance
_session_store: Optional[SessionStore] = None


def get_session_store() -> SessionStore:
    """Get global session store instance"""
    global _session_store
    if _session_store is None:
        from .redis_client import get_redis_client
        _session_store = SessionStore(get_redis_client())
    return _session_store