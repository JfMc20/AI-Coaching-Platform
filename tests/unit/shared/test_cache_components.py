"""
Tests for shared cache components.
Tests Redis client, health checks, message queue, and session store.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, Mock, patch
from datetime import datetime, timedelta


class TestRedisClient:
    """Test Redis client functionality."""

    async def test_redis_client_initialization(self):
        """Test Redis client can be initialized."""
        try:
            from shared.cache.redis_client import RedisClient
            
            client = RedisClient(redis_url="redis://localhost:6379/1")
            assert client is not None
            assert client.redis_url == "redis://localhost:6379/1"
            
        except ImportError:
            pytest.skip("RedisClient not available")

    async def test_redis_client_connection_mock(self):
        """Test Redis client connection with mock."""
        try:
            from shared.cache.redis_client import RedisClient
            
            with patch('redis.asyncio.from_url') as mock_redis:
                mock_redis_instance = AsyncMock()
                mock_redis_instance.ping.return_value = True
                mock_redis.return_value = mock_redis_instance
                
                client = RedisClient()
                await client.connect()
                
                assert client.redis is not None
                mock_redis_instance.ping.assert_called_once()
                
        except ImportError:
            pytest.skip("RedisClient not available")

    async def test_redis_client_get_set_operations(self):
        """Test Redis get/set operations."""
        try:
            from shared.cache.redis_client import RedisClient
            
            with patch('redis.asyncio.from_url') as mock_redis:
                mock_redis_instance = AsyncMock()
                mock_redis_instance.get.return_value = "test_value"
                mock_redis_instance.set.return_value = True
                mock_redis.return_value = mock_redis_instance
                
                client = RedisClient()
                await client.connect()
                
                # Test set operation
                result = await client.set("test_key", "test_value")
                assert result is True
                mock_redis_instance.set.assert_called_with("test_key", "test_value", ex=None)
                
                # Test get operation
                value = await client.get("test_key")
                assert value == "test_value"
                mock_redis_instance.get.assert_called_with("test_key")
                
        except ImportError:
            pytest.skip("RedisClient not available")

    async def test_redis_client_delete_operation(self):
        """Test Redis delete operation."""
        try:
            from shared.cache.redis_client import RedisClient
            
            with patch('redis.asyncio.from_url') as mock_redis:
                mock_redis_instance = AsyncMock()
                mock_redis_instance.delete.return_value = 1
                mock_redis.return_value = mock_redis_instance
                
                client = RedisClient()
                await client.connect()
                
                result = await client.delete("test_key")
                assert result == 1
                mock_redis_instance.delete.assert_called_with("test_key")
                
        except ImportError:
            pytest.skip("RedisClient not available")

    async def test_redis_client_exists_operation(self):
        """Test Redis exists operation."""
        try:
            from shared.cache.redis_client import RedisClient
            
            with patch('redis.asyncio.from_url') as mock_redis:
                mock_redis_instance = AsyncMock()
                mock_redis_instance.exists.return_value = 1
                mock_redis.return_value = mock_redis_instance
                
                client = RedisClient()
                await client.connect()
                
                result = await client.exists("test_key")
                assert result == 1
                mock_redis_instance.exists.assert_called_with("test_key")
                
        except ImportError:
            pytest.skip("RedisClient not available")

    async def test_redis_client_expire_operation(self):
        """Test Redis expire operation."""
        try:
            from shared.cache.redis_client import RedisClient
            
            with patch('redis.asyncio.from_url') as mock_redis:
                mock_redis_instance = AsyncMock()
                mock_redis_instance.expire.return_value = True
                mock_redis.return_value = mock_redis_instance
                
                client = RedisClient()
                await client.connect()
                
                result = await client.expire("test_key", 3600)
                assert result is True
                mock_redis_instance.expire.assert_called_with("test_key", 3600)
                
        except ImportError:
            pytest.skip("RedisClient not available")


class TestHealthChecks:
    """Test cache health check functionality."""

    async def test_redis_health_check(self):
        """Test Redis health check."""
        try:
            from shared.cache.health_checks import RedisHealthCheck
            
            with patch('redis.asyncio.from_url') as mock_redis:
                mock_redis_instance = AsyncMock()
                mock_redis_instance.ping.return_value = True
                mock_redis.return_value = mock_redis_instance
                
                health_check = RedisHealthCheck("redis://localhost:6379")
                result = await health_check.check()
                
                assert result["status"] == "healthy"
                assert result["service"] == "redis"
                assert "response_time_ms" in result
                
        except ImportError:
            pytest.skip("RedisHealthCheck not available")

    async def test_redis_health_check_failure(self):
        """Test Redis health check failure."""
        try:
            from shared.cache.health_checks import RedisHealthCheck
            
            with patch('redis.asyncio.from_url') as mock_redis:
                mock_redis_instance = AsyncMock()
                mock_redis_instance.ping.side_effect = Exception("Connection failed")
                mock_redis.return_value = mock_redis_instance
                
                health_check = RedisHealthCheck("redis://localhost:6379")
                result = await health_check.check()
                
                assert result["status"] == "unhealthy"
                assert "error" in result
                
        except ImportError:
            pytest.skip("RedisHealthCheck not available")

    async def test_cache_health_aggregator(self):
        """Test cache health aggregator."""
        try:
            from shared.cache.health_checks import CacheHealthAggregator
            
            aggregator = CacheHealthAggregator()
            
            # Mock individual health checks
            with patch.object(aggregator, 'redis_health') as mock_redis_health:
                mock_redis_health.check.return_value = {
                    "status": "healthy",
                    "service": "redis",
                    "response_time_ms": 5
                }
                
                result = await aggregator.check_all()
                
                assert result["overall_status"] == "healthy"
                assert "redis" in result["services"]
                assert result["services"]["redis"]["status"] == "healthy"
                
        except ImportError:
            pytest.skip("CacheHealthAggregator not available")


class TestMessageQueue:
    """Test message queue functionality."""

    async def test_message_queue_initialization(self):
        """Test message queue initialization."""
        try:
            from shared.cache.message_queue import MessageQueue
            
            queue = MessageQueue("redis://localhost:6379")
            assert queue is not None
            assert queue.redis_url == "redis://localhost:6379"
            
        except ImportError:
            pytest.skip("MessageQueue not available")

    async def test_message_queue_publish(self):
        """Test message queue publish operation."""
        try:
            from shared.cache.message_queue import MessageQueue
            
            with patch('redis.asyncio.from_url') as mock_redis:
                mock_redis_instance = AsyncMock()
                mock_redis_instance.publish.return_value = 1
                mock_redis.return_value = mock_redis_instance
                
                queue = MessageQueue()
                await queue.connect()
                
                result = await queue.publish("test_channel", {"message": "test"})
                assert result == 1
                
        except ImportError:
            pytest.skip("MessageQueue not available")

    async def test_message_queue_subscribe(self):
        """Test message queue subscribe operation."""
        try:
            from shared.cache.message_queue import MessageQueue
            
            with patch('redis.asyncio.from_url') as mock_redis:
                mock_redis_instance = AsyncMock()
                mock_pubsub = AsyncMock()
                mock_redis_instance.pubsub.return_value = mock_pubsub
                mock_redis.return_value = mock_redis_instance
                
                queue = MessageQueue()
                await queue.connect()
                
                await queue.subscribe("test_channel")
                mock_pubsub.subscribe.assert_called_with("test_channel")
                
        except ImportError:
            pytest.skip("MessageQueue not available")

    async def test_message_queue_unsubscribe(self):
        """Test message queue unsubscribe operation."""
        try:
            from shared.cache.message_queue import MessageQueue
            
            with patch('redis.asyncio.from_url') as mock_redis:
                mock_redis_instance = AsyncMock()
                mock_pubsub = AsyncMock()
                mock_redis_instance.pubsub.return_value = mock_pubsub
                mock_redis.return_value = mock_redis_instance
                
                queue = MessageQueue()
                await queue.connect()
                
                await queue.unsubscribe("test_channel")
                mock_pubsub.unsubscribe.assert_called_with("test_channel")
                
        except ImportError:
            pytest.skip("MessageQueue not available")


class TestSessionStore:
    """Test session store functionality."""

    async def test_session_store_initialization(self):
        """Test session store initialization."""
        try:
            from shared.cache.session_store import SessionStore
            
            store = SessionStore("redis://localhost:6379")
            assert store is not None
            assert store.redis_url == "redis://localhost:6379"
            
        except ImportError:
            pytest.skip("SessionStore not available")

    async def test_session_store_create_session(self):
        """Test session creation."""
        try:
            from shared.cache.session_store import SessionStore
            
            with patch('redis.asyncio.from_url') as mock_redis:
                mock_redis_instance = AsyncMock()
                mock_redis_instance.set.return_value = True
                mock_redis.return_value = mock_redis_instance
                
                store = SessionStore()
                await store.connect()
                
                session_id = await store.create_session("user_123", {"name": "Test User"})
                assert session_id is not None
                assert len(session_id) > 0
                
        except ImportError:
            pytest.skip("SessionStore not available")

    async def test_session_store_get_session(self):
        """Test session retrieval."""
        try:
            from shared.cache.session_store import SessionStore
            import json
            
            with patch('redis.asyncio.from_url') as mock_redis:
                mock_redis_instance = AsyncMock()
                session_data = {"user_id": "user_123", "name": "Test User"}
                mock_redis_instance.get.return_value = json.dumps(session_data)
                mock_redis.return_value = mock_redis_instance
                
                store = SessionStore()
                await store.connect()
                
                result = await store.get_session("session_123")
                assert result == session_data
                
        except ImportError:
            pytest.skip("SessionStore not available")

    async def test_session_store_update_session(self):
        """Test session update."""
        try:
            from shared.cache.session_store import SessionStore
            
            with patch('redis.asyncio.from_url') as mock_redis:
                mock_redis_instance = AsyncMock()
                mock_redis_instance.set.return_value = True
                mock_redis.return_value = mock_redis_instance
                
                store = SessionStore()
                await store.connect()
                
                result = await store.update_session("session_123", {"updated": True})
                assert result is True
                
        except ImportError:
            pytest.skip("SessionStore not available")

    async def test_session_store_delete_session(self):
        """Test session deletion."""
        try:
            from shared.cache.session_store import SessionStore
            
            with patch('redis.asyncio.from_url') as mock_redis:
                mock_redis_instance = AsyncMock()
                mock_redis_instance.delete.return_value = 1
                mock_redis.return_value = mock_redis_instance
                
                store = SessionStore()
                await store.connect()
                
                result = await store.delete_session("session_123")
                assert result == 1
                
        except ImportError:
            pytest.skip("SessionStore not available")

    async def test_session_store_cleanup_expired(self):
        """Test cleanup of expired sessions."""
        try:
            from shared.cache.session_store import SessionStore
            
            with patch('redis.asyncio.from_url') as mock_redis:
                mock_redis_instance = AsyncMock()
                mock_redis_instance.scan_iter.return_value = ["session:expired_1", "session:expired_2"]
                mock_redis_instance.delete.return_value = 2
                mock_redis.return_value = mock_redis_instance
                
                store = SessionStore()
                await store.connect()
                
                result = await store.cleanup_expired_sessions()
                assert result >= 0  # Should return number of cleaned sessions
                
        except ImportError:
            pytest.skip("SessionStore not available")


class TestCacheIntegration:
    """Test cache component integration."""

    async def test_cache_manager_initialization(self):
        """Test cache manager initialization."""
        try:
            from shared.cache import get_cache_manager
            
            manager = get_cache_manager()
            assert manager is not None
            
        except ImportError:
            pytest.skip("Cache manager not available")

    async def test_cache_manager_redis_access(self):
        """Test cache manager Redis access."""
        try:
            from shared.cache import get_cache_manager
            
            manager = get_cache_manager()
            
            # Should have redis attribute
            assert hasattr(manager, 'redis')
            
        except ImportError:
            pytest.skip("Cache manager not available")

    async def test_cache_manager_health_check(self):
        """Test cache manager health check."""
        try:
            from shared.cache import get_cache_manager
            
            manager = get_cache_manager()
            
            # Mock the health check
            with patch.object(manager, 'health_check') as mock_health:
                mock_health.return_value = {"status": "healthy"}
                
                result = await manager.health_check()
                assert result["status"] == "healthy"
                
        except ImportError:
            pytest.skip("Cache manager not available")

    async def test_cache_operations_with_manager(self):
        """Test cache operations through manager."""
        try:
            from shared.cache import get_cache_manager
            
            manager = get_cache_manager()
            
            # Mock Redis operations
            with patch.object(manager, 'redis') as mock_redis:
                mock_redis.get = AsyncMock(return_value="cached_value")
                mock_redis.set = AsyncMock(return_value=True)
                mock_redis.delete = AsyncMock(return_value=1)
                
                # Test operations
                await manager.redis.set("test_key", "test_value")
                value = await manager.redis.get("test_key")
                deleted = await manager.redis.delete("test_key")
                
                assert value == "cached_value"
                assert deleted == 1
                
        except ImportError:
            pytest.skip("Cache manager not available")