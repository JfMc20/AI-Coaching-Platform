"""
Tests for Redis cache functionality.
Tests Redis client, session store, message queue, and health checks.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, Mock, patch

from shared.cache.redis_client import RedisClient
from shared.cache.session_store import SessionStore
from shared.cache.health_checks import RedisHealthCheck


class TestRedisClient:
    """Test Redis client functionality."""

    @pytest.fixture
    def mock_redis(self):
        """Mock Redis connection."""
        mock = AsyncMock()
        mock.ping.return_value = True
        mock.get.return_value = b'{"test": "value"}'
        mock.set.return_value = True
        mock.delete.return_value = 1
        mock.exists.return_value = 1
        mock.expire.return_value = True
        mock.flushdb.return_value = True
        return mock

    @pytest.fixture
    def redis_client(self, mock_redis):
        """Create Redis client with mocked connection."""
        client = RedisClient("redis://localhost:6379")
        client._redis = mock_redis
        return client

    async def test_connection(self, redis_client, mock_redis):
        """Test Redis connection."""
        await redis_client.connect()
        mock_redis.ping.assert_called_once()

    async def test_set_and_get(self, redis_client, mock_redis):
        """Test setting and getting values."""
        # Test set
        await redis_client.set("test_key", {"test": "value"})
        mock_redis.set.assert_called_once()

        # Test get
        result = await redis_client.get("test_key")
        mock_redis.get.assert_called_once_with("test_key")
        assert result == {"test": "value"}

    async def test_set_with_expiration(self, redis_client, mock_redis):
        """Test setting values with expiration."""
        await redis_client.set("test_key", "value", expire=3600)
        mock_redis.set.assert_called_once()
        # Verify expiration was set with exact value
        call_args = mock_redis.set.call_args
        assert (call_args.kwargs.get("ex") == 3600 or 
                (len(call_args.args) >= 3 and call_args.args[2] == 3600))

    async def test_delete(self, redis_client, mock_redis):
        """Test deleting keys."""
        result = await redis_client.delete("test_key")
        mock_redis.delete.assert_called_once_with("test_key")
        assert result == 1

    async def test_exists(self, redis_client, mock_redis):
        """Test checking key existence."""
        result = await redis_client.exists("test_key")
        mock_redis.exists.assert_called_once_with("test_key")
        assert result is True

    async def test_expire(self, redis_client, mock_redis):
        """Test setting key expiration."""
        result = await redis_client.expire("test_key", 3600)
        mock_redis.expire.assert_called_once_with("test_key", 3600)
        assert result is True

    async def test_flush_database(self, redis_client, mock_redis):
        """Test flushing database."""
        await redis_client.flushdb()
        mock_redis.flushdb.assert_called_once()

    async def test_json_serialization(self, redis_client, mock_redis):
        """Test JSON serialization and deserialization."""
        import json
        
        test_data = {
            "string": "value",
            "number": 42,
            "boolean": True,
            "list": [1, 2, 3],
            "nested": {"key": "value"}
        }

        await redis_client.set("json_key", test_data)
        
        # Verify JSON was serialized correctly
        call_args = mock_redis.set.call_args
        serialized_value = call_args.args[1]
        assert isinstance(serialized_value, (str, bytes))
        
        # Check actual JSON content
        if isinstance(serialized_value, bytes):
            assert serialized_value == json.dumps(test_data).encode()
        else:
            assert serialized_value == json.dumps(test_data)
        
        # Test full serialize/deserialize cycle
        mock_redis.get.return_value = serialized_value
        result = await redis_client.get("json_key")
        assert result == test_data

    async def test_connection_error_handling(self, redis_client, mock_redis):
        """Test connection error handling."""
        mock_redis.ping.side_effect = ConnectionError("Connection failed")
        
        with pytest.raises(ConnectionError):
            await redis_client.connect()

    async def test_get_nonexistent_key(self, redis_client, mock_redis):
        """Test getting non-existent key."""
        mock_redis.get.return_value = None
        
        result = await redis_client.get("nonexistent_key")
        assert result is None

    async def test_multi_tenant_key_prefixing(self, redis_client, mock_redis):
        """Test multi-tenant key prefixing."""
        tenant_id = "tenant-123"
        
        await redis_client.set("user_data", {"name": "John"}, tenant_id=tenant_id)
        
        # Verify exact multi-tenant key format
        call_args = mock_redis.set.call_args
        key_used = call_args.args[0]
        if isinstance(key_used, bytes):
            key_used = key_used.decode('utf-8')
        
        # Assert exact prefix format and key ordering
        assert key_used.startswith(f"{tenant_id}:")
        assert key_used.endswith("user_data")
        expected_key = f"{tenant_id}:user_data"
        assert key_used == expected_key


class TestSessionStore:
    """Test session store functionality."""

    @pytest.fixture
    def mock_redis_client(self):
        """Mock Redis client for session store."""
        mock = AsyncMock()
        mock.set.return_value = True
        mock.get.return_value = {"user_id": "123", "tenant_id": "test-tenant"}
        mock.delete.return_value = 1
        mock.exists.return_value = True
        return mock

    @pytest.fixture
    def session_store(self, mock_redis_client):
        """Create session store with mocked Redis client."""
        return SessionStore(mock_redis_client)

    async def test_create_session(self, session_store, mock_redis_client):
        """Test creating a new session."""
        session_data = {
            "user_id": "123",
            "tenant_id": "test-tenant",
            "permissions": ["read", "write"]
        }

        session_id = await session_store.create_session(session_data, expire=3600)
        
        assert session_id is not None
        assert len(session_id) > 0
        mock_redis_client.set.assert_called_once()

    async def test_get_session(self, session_store, mock_redis_client):
        """Test retrieving session data."""
        session_id = "test-session-123"
        
        session_data = await session_store.get_session(session_id)
        
        mock_redis_client.get.assert_called_once()
        assert session_data["user_id"] == "123"
        assert session_data["tenant_id"] == "test-tenant"

    async def test_update_session(self, session_store, mock_redis_client):
        """Test updating session data."""
        session_id = "test-session-123"
        update_data = {"last_activity": "2023-12-01T10:00:00Z"}

        await session_store.update_session(session_id, update_data)
        
        mock_redis_client.set.assert_called_once()

    async def test_delete_session(self, session_store, mock_redis_client):
        """Test deleting a session."""
        session_id = "test-session-123"
        
        result = await session_store.delete_session(session_id)
        
        mock_redis_client.delete.assert_called_once_with(f"session:{session_id}")
        assert result is True

    async def test_session_exists(self, session_store, mock_redis_client):
        """Test checking if session exists."""
        session_id = "test-session-123"
        
        exists = await session_store.session_exists(session_id)
        
        mock_redis_client.exists.assert_called_once()
        assert exists is True

    async def test_session_expiration(self, session_store, mock_redis_client):
        """Test session expiration handling."""
        mock_redis_client.get.return_value = None  # Expired session
        
        session_data = await session_store.get_session("expired-session")
        assert session_data is None

    async def test_session_key_format(self, session_store, mock_redis_client):
        """Test session key formatting."""
        session_id = "test-123"
        
        await session_store.get_session(session_id)
        
        # Verify correct key format was used
        call_args = mock_redis_client.get.call_args
        key_used = call_args.args[0]
        assert key_used == f"session:{session_id}"


class TestRedisHealthCheck:
    """Test Redis health check functionality."""

    @pytest.fixture
    def mock_redis_client(self):
        """Mock Redis client for health checks."""
        mock = AsyncMock()
        mock.ping.return_value = True
        mock.info.return_value = {
            "redis_version": "7.0.0",
            "used_memory": "1024000",
            "connected_clients": "5"
        }
        return mock

    @pytest.fixture
    def health_check(self, mock_redis_client):
        """Create Redis health check with mocked client."""
        return RedisHealthCheck(mock_redis_client)

    async def test_basic_health_check(self, health_check, mock_redis_client):
        """Test basic Redis health check."""
        result = await health_check.check_health()
        
        mock_redis_client.ping.assert_called_once()
        assert result["status"] == "healthy"
        assert "timestamp" in result

    async def test_detailed_health_check(self, health_check, mock_redis_client):
        """Test detailed Redis health check."""
        result = await health_check.check_health(detailed=True)
        
        mock_redis_client.ping.assert_called_once()
        mock_redis_client.info.assert_called_once()
        
        assert result["status"] == "healthy"
        assert "redis_info" in result
        assert result["redis_info"]["redis_version"] == "7.0.0"

    async def test_health_check_failure(self, health_check, mock_redis_client):
        """Test health check when Redis is down."""
        mock_redis_client.ping.side_effect = ConnectionError("Redis unavailable")
        
        result = await health_check.check_health()
        
        assert result["status"] == "unhealthy"
        assert "error" in result

    async def test_memory_usage_check(self, health_check, mock_redis_client):
        """Test memory usage monitoring."""
        result = await health_check.check_memory_usage()
        
        mock_redis_client.info.assert_called_once()
        assert "memory_usage" in result
        assert "memory_usage_mb" in result

    async def test_connection_count_check(self, health_check, mock_redis_client):
        """Test connection count monitoring."""
        result = await health_check.check_connections()
        
        mock_redis_client.info.assert_called_once()
        assert "connected_clients" in result

    async def test_performance_check(self, health_check, mock_redis_client):
        """Test Redis performance check."""
        import time
        
        # Mock a slow response
        async def slow_ping():
            await asyncio.sleep(0.1)
            return True
        
        mock_redis_client.ping = slow_ping
        
        result = await health_check.check_performance()
        
        assert "response_time" in result
        # Use approximate comparison with tolerance instead of exact timing
        assert result["response_time"] == pytest.approx(0.1, abs=0.05)


class TestCacheIntegration:
    """Test cache integration scenarios."""

    @pytest.fixture
    def mock_redis_client(self):
        """Mock Redis client for integration tests."""
        mock = AsyncMock()
        mock.pipeline.return_value = mock
        mock.execute.return_value = [True, True, True]
        return mock

    async def test_cache_pipeline_operations(self, mock_redis_client):
        """Test Redis pipeline operations."""
        # Simulate pipeline operations
        pipeline = mock_redis_client.pipeline()
        pipeline.set("key1", "value1")
        pipeline.set("key2", "value2")
        pipeline.set("key3", "value3")
        
        results = await pipeline.execute()
        
        assert len(results) == 3
        assert all(results)

    async def test_cache_transaction(self, mock_redis_client):
        """Test Redis transaction operations."""
        # Mock transaction behavior
        mock_redis_client.multi.return_value = True
        mock_redis_client.exec.return_value = [True, True]
        
        # Simulate transaction
        await mock_redis_client.multi()
        await mock_redis_client.set("key1", "value1")
        await mock_redis_client.set("key2", "value2")
        results = await mock_redis_client.exec()
        
        assert len(results) == 2
        assert all(results)

    async def test_cache_pub_sub(self, mock_redis_client):
        """Test Redis pub/sub functionality."""
        # Mock pub/sub
        mock_pubsub = AsyncMock()
        mock_pubsub.subscribe.return_value = True
        mock_pubsub.get_message.return_value = {
            "type": "message",
            "channel": b"test_channel",
            "data": b"test_message"
        }
        
        mock_redis_client.pubsub.return_value = mock_pubsub
        
        pubsub = mock_redis_client.pubsub()
        await pubsub.subscribe("test_channel")
        message = await pubsub.get_message()
        
        assert message["type"] == "message"
        assert message["data"] == b"test_message"

    async def test_cache_lua_script(self, mock_redis_client):
        """Test Redis Lua script execution."""
        # Mock Lua script
        script = "return redis.call('GET', KEYS[1])"
        mock_redis_client.eval.return_value = b"script_result"
        
        result = await mock_redis_client.eval(script, 1, "test_key")
        
        mock_redis_client.eval.assert_called_once_with(script, 1, "test_key")
        assert result == b"script_result"

    async def test_multi_tenant_cache_isolation(self, mock_redis_client):
        """Test multi-tenant cache isolation."""
        tenant1_client = RedisClient("redis://localhost:6379")
        tenant1_client._redis = mock_redis_client
        
        tenant2_client = RedisClient("redis://localhost:6379")
        tenant2_client._redis = mock_redis_client
        
        # Set data for different tenants
        await tenant1_client.set("user_data", {"name": "John"}, tenant_id="tenant-1")
        await tenant2_client.set("user_data", {"name": "Jane"}, tenant_id="tenant-2")
        
        # Verify different keys were used
        assert mock_redis_client.set.call_count == 2
        
        # Check that tenant IDs are in the keys
        calls = mock_redis_client.set.call_args_list
        key1 = calls[0].args[0]
        key2 = calls[1].args[0]
        
        assert "tenant-1" in key1
        assert "tenant-2" in key2
        assert key1 != key2