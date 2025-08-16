"""
Redis client configuration and utilities for MVP Coaching AI Platform
Handles multi-tenant caching with namespacing and TTL management
"""

import redis.asyncio as redis
import json
import logging
import asyncio
import inspect
from typing import Optional, Any, Dict, List
from datetime import datetime
import hashlib
import os
from functools import wraps

logger = logging.getLogger(__name__)


class RedisClient:
    """Redis client with multi-tenant support and caching utilities"""
    
    def __init__(self, redis_url: str = None, default_ttl: int = 3600):
        """
        Initialize Redis client
        
        Args:
            redis_url: Redis connection URL
            default_ttl: Default TTL in seconds (1 hour)
        """
        self.redis_url = redis_url or os.getenv("REDIS_URL", "redis://localhost:6379")
        self.default_ttl = default_ttl
        self._client: Optional[redis.Redis] = None
        self._init_lock = asyncio.Lock()
        
    async def get_client(self) -> redis.Redis:
        """Get Redis client instance (lazy initialization with thread safety)"""
        if self._client is None:
            async with self._init_lock:
                # Re-check after acquiring lock to avoid race condition
                if self._client is None:
                    self._client = redis.from_url(
                        self.redis_url,
                        encoding="utf-8",
                        decode_responses=True,
                        socket_connect_timeout=5,
                        socket_timeout=5,
                        retry_on_timeout=True,
                        health_check_interval=30
                    )
        return self._client
    
    async def get_connection(self, creator_id: str):
        """Get Redis connection for transactions"""
        client = await self.get_client()
        return client
    
    async def close(self):
        """Close Redis connection"""
        if self._client:
            await self._client.close()
            self._client = None
    
    def _get_namespaced_key(self, creator_id: str, key: str) -> str:
        """Generate namespaced key for multi-tenant isolation"""
        return f"tenant:{creator_id}:{key}"
    
    def _serialize_value(self, value: Any) -> str:
        """Serialize value for Redis storage"""
        if isinstance(value, str):
            return value
        elif isinstance(value, (int, float)) and not isinstance(value, bool):
            return str(value)
        else:
            # Use JSON serialization for all other types including booleans,
            # lists, dicts, None, etc. to ensure proper deserialization
            return json.dumps(value, default=str)
    
    def _deserialize_value(self, value: str) -> Any:
        """Deserialize value from Redis"""
        if value is None:
            return None
        
        try:
            return json.loads(value)
        except (json.JSONDecodeError, TypeError):
            return value
    
    async def set(
        self, 
        creator_id: str, 
        key: str, 
        value: Any, 
        ttl: Optional[int] = None
    ) -> bool:
        """
        Set a value in Redis with tenant namespacing
        
        Args:
            creator_id: Creator/tenant ID
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds
            
        Returns:
            True if successful
        """
        try:
            client = await self.get_client()
            namespaced_key = self._get_namespaced_key(creator_id, key)
            
            # Wrap value to distinguish between cached None and cache miss
            wrapped_value = {"__cached__": True, "v": value}
            serialized_value = self._serialize_value(wrapped_value)
            
            if ttl is None:
                ttl = self.default_ttl
            
            result = await client.setex(namespaced_key, ttl, serialized_value)
            logger.debug(f"Set cache key: {namespaced_key} (TTL: {ttl}s)")
            return result
        except Exception as e:
            logger.exception(f"Failed to set cache key {key} for creator {creator_id}: {e}")
            return False
    
    async def get(self, creator_id: str, key: str) -> Any:
        """
        Get a value from Redis with tenant namespacing
        
        Args:
            creator_id: Creator/tenant ID
            key: Cache key
            
        Returns:
            Cached value or None if not found
        """
        try:
            client = await self.get_client()
            namespaced_key = self._get_namespaced_key(creator_id, key)
            
            value = await client.get(namespaced_key)
            if value is not None:
                logger.debug(f"Cache hit: {namespaced_key}")
                deserialized = self._deserialize_value(value)
                
                # Check if this is a wrapped cached value
                if isinstance(deserialized, dict) and deserialized.get("__cached__") is True:
                    return deserialized.get("v")
                
                # Fallback for legacy cached values (backward compatibility)
                return deserialized
            
            logger.debug(f"Cache miss: {namespaced_key}")
            return None
        except Exception as e:
            logger.exception(f"Failed to get cache key {key} for creator {creator_id}: {e}")
            return None
    
    async def delete(self, creator_id: str, key: str) -> bool:
        """
        Delete a value from Redis
        
        Args:
            creator_id: Creator/tenant ID
            key: Cache key
            
        Returns:
            True if key was deleted
        """
        try:
            client = await self.get_client()
            namespaced_key = self._get_namespaced_key(creator_id, key)
            
            result = await client.delete(namespaced_key)
            logger.debug(f"Deleted cache key: {namespaced_key}")
            return result > 0
        except Exception as e:
            logger.exception(f"Failed to delete cache key {key} for creator {creator_id}: {e}")
            return False
    
    async def exists(self, creator_id: str, key: str) -> bool:
        """Check if a key exists in Redis"""
        try:
            client = await self.get_client()
            namespaced_key = self._get_namespaced_key(creator_id, key)
            
            result = await client.exists(namespaced_key)
            return result > 0
        except Exception as e:
            logger.exception(f"Failed to check existence of key {key} for creator {creator_id}: {e}")
            return False
    
    async def expire(self, creator_id: str, key: str, ttl: int) -> bool:
        """Set expiration time for a key"""
        try:
            client = await self.get_client()
            namespaced_key = self._get_namespaced_key(creator_id, key)
            
            result = await client.expire(namespaced_key, ttl)
            return result
        except Exception as e:
            logger.exception(f"Failed to set expiration for key {key} for creator {creator_id}: {e}")
            return False
    
    async def get_ttl(self, creator_id: str, key: str) -> int:
        """Get remaining TTL for a key"""
        try:
            client = await self.get_client()
            namespaced_key = self._get_namespaced_key(creator_id, key)
            
            return await client.ttl(namespaced_key)
        except Exception as e:
            logger.exception(f"Failed to get TTL for key {key} for creator {creator_id}: {e}")
            return -1
    
    async def increment(self, creator_id: str, key: str, amount: int = 1) -> int:
        """Increment a numeric value"""
        try:
            client = await self.get_client()
            namespaced_key = self._get_namespaced_key(creator_id, key)
            
            return await client.incrby(namespaced_key, amount)
        except Exception as e:
            logger.exception(f"Failed to increment key {key} for creator {creator_id}: {e}")
            return 0
    
    async def get_keys_pattern(self, creator_id: str, pattern: str) -> List[str]:
        """Get keys matching a pattern for a specific tenant using SCAN"""
        try:
            client = await self.get_client()
            namespaced_pattern = self._get_namespaced_key(creator_id, pattern)
            
            keys = []
            cursor = 0
            prefix = f"tenant:{creator_id}:"
            
            # Use SCAN to iterate through keys in batches
            while True:
                cursor, batch_keys = await client.scan(
                    cursor=cursor, 
                    match=namespaced_pattern, 
                    count=100
                )
                
                # Remove namespace prefix from returned keys
                for key in batch_keys:
                    if key.startswith(prefix):
                        keys.append(key[len(prefix):])
                
                # Break when cursor returns to 0 (full iteration complete)
                if cursor == 0:
                    break
            
            return keys
        except Exception as e:
            logger.exception(f"Failed to get keys with pattern {pattern} for creator {creator_id}: {e}")
            return []
    
    async def clear_tenant_cache(self, creator_id: str) -> int:
        """Clear all cache entries for a specific tenant using SCAN"""
        try:
            client = await self.get_client()
            pattern = f"tenant:{creator_id}:*"
            
            keys = []
            cursor = 0
            
            # Use SCAN to collect all keys in batches
            while True:
                cursor, batch_keys = await client.scan(
                    cursor=cursor, 
                    match=pattern, 
                    count=100
                )
                keys.extend(batch_keys)
                
                # Break when cursor returns to 0 (full iteration complete)
                if cursor == 0:
                    break
            
            if keys:
                # Use UNLINK for non-blocking deletion if available, fallback to DELETE
                try:
                    deleted = await client.unlink(*keys)
                except AttributeError:
                    # Fallback to DELETE if UNLINK is not available
                    deleted = await client.delete(*keys)
                
                logger.info(f"Cleared {deleted} cache entries for creator {creator_id}")
                return deleted
            return 0
        except Exception as e:
            logger.exception(f"Failed to clear cache for creator {creator_id}: {e}")
            return 0
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform Redis health check"""
        try:
            client = await self.get_client()
            
            # Test basic operations
            test_key = "health_check_test"
            test_value = "ok"
            
            await client.set(test_key, test_value, ex=10)
            retrieved_value = await client.get(test_key)
            await client.delete(test_key)
            
            # Get Redis info
            info = await client.info()
            
            return {
                "status": "healthy" if retrieved_value == test_value else "unhealthy",
                "connected_clients": info.get("connected_clients", 0),
                "used_memory": info.get("used_memory_human", "unknown"),
                "redis_version": info.get("redis_version", "unknown"),
                "uptime_in_seconds": info.get("uptime_in_seconds", 0)
            }
        except Exception as e:
            logger.exception(f"Redis health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e)
            }


class CacheManager:
    """High-level cache manager with common caching patterns"""
    
    def __init__(self, redis_client: RedisClient):
        self.redis = redis_client
    
    def generate_cache_key(self, *args, **kwargs) -> str:
        """Generate deterministic cache key from arguments"""
        # Create a string representation of all arguments
        key_parts = []
        
        # Add positional arguments
        for arg in args:
            if isinstance(arg, (dict, list)):
                key_parts.append(json.dumps(arg, sort_keys=True))
            else:
                key_parts.append(str(arg))
        
        # Add keyword arguments (sorted for consistency)
        for k, v in sorted(kwargs.items()):
            if isinstance(v, (dict, list)):
                key_parts.append(f"{k}:{json.dumps(v, sort_keys=True)}")
            else:
                key_parts.append(f"{k}:{v}")
        
        # Create hash of the combined key
        key_string = "|".join(key_parts)
        return hashlib.sha256(key_string.encode()).hexdigest()[:16]
    
    def _build_search_cache_key(
        self, 
        query: str, 
        model_version: str, 
        filters: Dict[str, Any]
    ) -> str:
        """
        Build cache key for search results
        
        Args:
            query: Search query
            model_version: Model version identifier
            filters: Search filters
            
        Returns:
            Generated cache key
        """
        # Normalize query
        normalized_query = query.lower().strip()
        
        # Create filters hash
        filters_str = json.dumps(filters, sort_keys=True)
        filters_hash = hashlib.sha256(filters_str.encode()).hexdigest()[:8]
        
        # Create cache key
        query_hash = hashlib.sha256(normalized_query.encode()).hexdigest()[:16]
        return f"search:{query_hash}:{model_version}:{filters_hash}"
    
    async def cache_search_results(
        self, 
        creator_id: str, 
        query: str, 
        model_version: str,
        filters: Dict[str, Any],
        results: List[Dict[str, Any]],
        ttl: int = 3600
    ) -> bool:
        """Cache search results with structured key"""
        # Generate cache key using helper method
        cache_key = self._build_search_cache_key(query, model_version, filters)
        
        # Cache the results
        cache_data = {
            "query": query,
            "results": results,
            "timestamp": datetime.utcnow().isoformat(),
            "model_version": model_version,
            "filters": filters
        }
        
        return await self.redis.set(creator_id, cache_key, cache_data, ttl)
    
    async def get_cached_search_results(
        self, 
        creator_id: str, 
        query: str, 
        model_version: str,
        filters: Dict[str, Any]
    ) -> Optional[List[Dict[str, Any]]]:
        """Get cached search results"""
        # Generate cache key using helper method
        cache_key = self._build_search_cache_key(query, model_version, filters)
        
        cached_data = await self.redis.get(creator_id, cache_key)
        if cached_data:
            return cached_data.get("results")
        
        return None
    
    async def cache_document_metadata(
        self, 
        creator_id: str, 
        document_id: str, 
        metadata: Dict[str, Any],
        ttl: int = 1800  # 30 minutes
    ) -> bool:
        """Cache document metadata"""
        cache_key = f"doc_meta:{document_id}"
        return await self.redis.set(creator_id, cache_key, metadata, ttl)
    
    async def get_cached_document_metadata(
        self, 
        creator_id: str, 
        document_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get cached document metadata"""
        cache_key = f"doc_meta:{document_id}"
        return await self.redis.get(creator_id, cache_key)
    
    async def cache_conversation_context(
        self, 
        creator_id: str, 
        conversation_id: str, 
        context: Dict[str, Any],
        ttl: int = 1800  # 30 minutes
    ) -> bool:
        """Cache conversation context"""
        cache_key = f"conv_ctx:{conversation_id}"
        return await self.redis.set(creator_id, cache_key, context, ttl)
    
    async def get_cached_conversation_context(
        self, 
        creator_id: str, 
        conversation_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get cached conversation context"""
        cache_key = f"conv_ctx:{conversation_id}"
        return await self.redis.get(creator_id, cache_key)
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform cache manager health check.
        
        Returns:
            Dictionary with health status information
        """
        try:
            # Delegate to Redis client health check
            redis_health = await self.redis.health_check()
            
            return {
                "status": "healthy" if redis_health.get("status") == "healthy" else "unhealthy",
                "redis_connected": redis_health.get("connected", False),
                "memory_usage": redis_health.get("memory_usage", "unknown"),
                "cache_manager": "operational",
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Cache manager health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "cache_manager": "error",
                "timestamp": datetime.utcnow().isoformat()
            }


# Global Redis client instance
_redis_client: Optional[RedisClient] = None
_cache_manager: Optional[CacheManager] = None


def get_redis_client() -> RedisClient:
    """Get global Redis client instance"""
    global _redis_client
    if _redis_client is None:
        _redis_client = RedisClient()
    return _redis_client


def get_cache_manager() -> CacheManager:
    """Get global cache manager instance"""
    global _cache_manager
    if _cache_manager is None:
        _cache_manager = CacheManager(get_redis_client())
    return _cache_manager


# Cache stampede prevention: in-memory locks per cache key
_cache_locks: Dict[str, asyncio.Lock] = {}
_locks_lock = asyncio.Lock()


async def _get_cache_lock(cache_key: str) -> asyncio.Lock:
    """Get or create a lock for a specific cache key to prevent cache stampede"""
    async with _locks_lock:
        if cache_key not in _cache_locks:
            _cache_locks[cache_key] = asyncio.Lock()
        return _cache_locks[cache_key]


def cache_result(ttl: Optional[int] = None, key_prefix: str = ""):
    """
    Decorator for caching function results (supports both async and sync functions)
    
    Args:
        ttl: Time to live in seconds (uses RedisClient.default_ttl if None)
        key_prefix: Prefix for cache key
    """
    def decorator(func):
        is_async = asyncio.iscoroutinefunction(func)
        
        if is_async:
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                # Extract creator_id and generate cache key
                creator_id, cache_key = _extract_cache_info(func, key_prefix, *args, **kwargs)
                if not creator_id:
                    return await func(*args, **kwargs)
                
                redis_client = None
                try:
                    redis_client = get_redis_client()
                    
                    # Use default TTL if not specified
                    effective_ttl = ttl if ttl is not None else redis_client.default_ttl
                    
                    # Try to get from cache first - the get method now properly handles None values
                    cache_exists = await redis_client.exists(creator_id, cache_key)
                    if cache_exists:
                        cached_result = await redis_client.get(creator_id, cache_key)
                        logger.debug(f"Cache hit for function {func.__name__}")
                        return cached_result
                    
                    # Prevent cache stampede by using per-key locks
                    cache_lock = await _get_cache_lock(cache_key)
                    async with cache_lock:
                        # Double-check cache after acquiring lock
                        cache_exists = await redis_client.exists(creator_id, cache_key)
                        if cache_exists:
                            cached_result = await redis_client.get(creator_id, cache_key)
                            logger.debug(f"Cache hit after lock for function {func.__name__}")
                            return cached_result
                        
                        # Execute function
                        result = await func(*args, **kwargs)
                        
                        # Cache result
                        if redis_client is not None:
                            await redis_client.set(creator_id, cache_key, result, effective_ttl)
                            logger.debug(f"Cached result for function {func.__name__}")
                        
                        return result
                        
                except Exception as cache_error:
                    logger.warning(f"Cache operation failed for {func.__name__}: {cache_error}")
                    # Execute function without caching on error
                    return await func(*args, **kwargs)
            
            return async_wrapper
        else:
            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                # Extract creator_id and generate cache key
                creator_id, cache_key = _extract_cache_info(func, key_prefix, *args, **kwargs)
                if not creator_id:
                    return func(*args, **kwargs)
                
                # For sync functions, we can't use async Redis operations
                # So we just execute the function without caching
                logger.warning(f"Sync function {func.__name__} cannot use async Redis cache")
                return func(*args, **kwargs)
            return sync_wrapper
    return decorator


def _extract_cache_info(func, key_prefix: str, *args, **kwargs):
    """
    Extract creator_id and generate cache key from function arguments
    
    Returns:
        Tuple of (creator_id, cache_key)
    """
    try:
        # Use inspect to properly bind arguments and extract creator_id
        sig = inspect.signature(func)
        bound_args = sig.bind(*args, **kwargs)
        bound_args.apply_defaults()
        
        # Extract creator_id from bound arguments
        creator_id = bound_args.arguments.get('creator_id')
        if not creator_id:
            return None, None
        
        # Create cache key from bound arguments, excluding self, cls, and creator_id
        cache_args = {}
        for param_name, param_value in bound_args.arguments.items():
            if param_name not in ('self', 'cls', 'creator_id'):
                cache_args[param_name] = param_value
        
        # Generate cache key
        cache_manager = get_cache_manager()
        func_key = f"{key_prefix}{func.__name__}" if key_prefix else func.__name__
        cache_key = f"{func_key}:{cache_manager.generate_cache_key(**cache_args)}"
        
        return creator_id, cache_key
        
    except Exception as e:
        logger.warning(f"Failed to extract cache info for {func.__name__}: {e}")
        return None, None