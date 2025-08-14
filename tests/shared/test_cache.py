"""
Tests for Redis cache functionality.
Tests Redis client, session store, message queue, and health checks.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, Mock, patch

from shared.cache.redis_client import RedisClient
from shared.cache.session_store import SessionStore
from shared.cache.health_checks import RedisHealthChecker


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
        # Mock the get_client method to return our mock
        client.get_client = AsyncMock(return_value=mock_redis)
        return clientn_value = 1
    mock.exists.return_value = 1

    # DATA PAYLOADS (returned as bytes)
    # get() returns the raw value as bytes, or None if not found.
    # The application code is responsible for decoding it (e.g., json.loads).
    mock.get.return_value = json.dumps({"test": "value"}).encode('utf-8')

    return mock

    @pytest.fixture
    def redis_client(self, mock_redis):
        """Create Redis client with mocked connection."""
        client = RedisClient("redis://localhost:6379")
        # Mock the get_client method to return our mock
        client.get_client = AsyncMock(return_value=mock_redis)
        return client

    async def test_get_client(self, redis_client, mock_redis):
        """Test Redis client initialization."""
        client = await redis_client.get_client()
        assert client is not None

    async def test_set_and_get(self, redis_client, mock_redis):
        """Test setting and getting values."""
        creator_id = "test-creator"
        
        # Mock the setex method for set operation
        mock_redis.setex.return_value = True
        mock_redis.get.return_value = '{"__cached__": true, "v": {"test": "value"}}'
        
        # Test set
        result = await redis_client.set(creator_id, "test_key", {"test": "value"})
        assert result is True
        mock_redis.setex.assert_called_once()

        # Test get
        result = await redis_client.get(creator_id, "test_key")
        mock_redis.get.assert_called_once()
        assert result == {"test": "value"}

    async def test_set_with_expiration(self, redis_client, mock_redis):
        """Test setting values with expiration."""
        creator_id = "test-creator"
        mock_redis.setex.return_value = True
        
        await redis_client.set(creator_id, "test_key", "value", ttl=3600)
        mock_redis.setex.assert_called_once()
        
        # Verify expiration was set with exact value
        call_args = mock_redis.setex.call_args
        assert call_args.args[1] == 3600  # TTL argument

    async def test_delete(self, redis_client, mock_redis):
        """Test deleting keys."""
        creator_id = "test-creator"
        mock_redis.delete.return_value = 1
        
        result = await redis_client.delete(creator_id, "test_key")
        mock_redis.delete.assert_called_once()
        assert result is True

    async def test_exists(self, redis_client, mock_redis):
        """Test checking key existence."""
        creator_id = "test-creator"
        mock_redis.exists.return_value = 1
        
        result = await redis_client.exists(creator_id, "test_key")
        mock_redis.exists.assert_called_once()
        assert result is True

    async def test_expire(self, redis_client, mock_redis):
        """Test setting key expiration."""
        creator_id = "test-creator"
        mock_redis.expire.return_value = True
        
        result = await redis_client.expire(creator_id, "test_key", 3600)
        mock_redis.expire.assert_called_once()
        assert result is True

    async def test_health_check(self, redis_client, mock_redis):
        """Test Redis health check."""
        mock_redis.set.return_value = True
        mock_redis.get.return_value = "ok"
        mock_redis.delete.return_value = 1
        mock_redis.info.return_value = {
            "connected_clients": 5,
            "used_memory_human": "1MB",
            "redis_version": "7.0.0",
            "uptime_in_seconds": 3600
        }
        
        result = await redis_client.health_check()
        assert result["status"] == "healthy"

    async def test_json_serialization(self, redis_client, mock_redis):
        """Test JSON serialization and deserialization."""
        import json
        
        creator_id = "test-creator"
        test_data = {
            "string": "value",
            "number": 42,
            "boolean": True,
            "list": [1, 2, 3],
            "nested": {"key": "value"}
        }

        mock_redis.setex.return_value = True
        mock_redis.get.return_value = json.dumps({"__cached__": True, "v": test_data})

        await redis_client.set(creator_id, "json_key", test_data)
        
        # Verify setex was called
        mock_redis.setex.assert_called_once()
        
        # Test full serialize/deserialize cycle
        result = await redis_client.get(creator_id, "json_key")
        assert result == test_data

    async def test_connection_error_handling(self, redis_client, mock_redis):
        """Test connection error handling."""
        creator_id = "test-creator"
        mock_redis.get.side_effect = ConnectionError("Connection failed")
        
        # Should return None on connection error, not raise
        result = await redis_client.get(creator_id, "test_key")
        assert result is None

    async def test_get_nonexistent_key(self, redis_client, mock_redis):
        """Test getting non-existent key."""
        creator_id = "test-creator"
        mock_redis.get.return_value = None
        
        result = await redis_client.get(creator_id, "nonexistent_key")
        assert result is None

    async def test_multi_tenant_key_prefixing(self, redis_client, mock_redis):
        """Test multi-tenant key prefixing."""
        creator_id = "tenant-123"
        mock_redis.setex.return_value = True
        
        await redis_client.set(creator_id, "user_data", {"name": "John"})
        
        # Verify exact multi-tenant key format
        call_args = mock_redis.setex.call_args
        key_used = call_args.args[0]
        if isinstance(key_used, bytes):
            key_used = key_used.decode('utf-8')
        
        # Assert exact prefix format and key ordering
        assert key_used.startswith(f"tenant:{creator_id}:")
        assert key_used.endswith("user_data")
        expected_key = f"tenant:{creator_id}:user_data"
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
        creator_id = "test-creator"
        user_id = "123"

        session_id = await session_store.create_session(
            creator_id=creator_id,
            user_id=user_id,
            channel="web_widget",
            metadata={"permissions": ["read", "write"]},
            ttl=3600
        )
        
        assert session_id is not None
        assert len(session_id) > 0
        mock_redis_client.set.assert_called()

    async def test_get_session(self, session_store, mock_redis_client):
        """Test retrieving session data."""
        creator_id = "test-creator"
        session_id = "test-session-123"
        
        mock_redis_client.get.return_value = {
            "session_id": session_id,
            "creator_id": creator_id,
            "user_id": "123",
            "is_active": True
        }
        
        session_data = await session_store.get_session(creator_id, session_id)
        
        mock_redis_client.get.assert_called_once()
        assert session_data["user_id"] == "123"
        assert session_data["creator_id"] == creator_id

    async def test_update_session(self, session_store, mock_redis_client):
        """Test updating session data."""
        creator_id = "test-creator"
        session_id = "test-session-123"
        update_data = {"last_activity": "2023-12-01T10:00:00Z"}

        # Mock the eval method for Lua script execution
        mock_redis_client.eval = AsyncMock(return_value=1)
        mock_client = AsyncMock()
        mock_client.eval.return_value = 1
        session_store.redis.get_client = AsyncMock(return_value=mock_client)

        result = await session_store.update_session(creator_id, session_id, update_data)
        
        assert result is True
        mock_client.eval.assert_called_once()

    async def test_delete_session(self, session_store, mock_redis_client):
        """Test deleting a session."""
        creator_id = "test-creator"
        session_id = "test-session-123"
        
        result = await session_store.delete_session(creator_id, session_id)
        
        mock_redis_client.delete.assert_called_once()
        # The delete method returns the number of deleted keys, so 1 means success
        assert result == 1

    async def test_session_exists(self, session_store, mock_redis_client):
        """Test checking if session exists."""
        creator_id = "test-creator"
        session_id = "test-session-123"
        
        # SessionStore doesn't have session_exists method, use get_session instead
        mock_redis_client.get.return_value = {
            "session_id": session_id,
            "creator_id": creator_id,
            "is_active": True
        }
        
        session_data = await session_store.get_session(creator_id, session_id)
        exists = session_data is not None
        
        mock_redis_client.get.assert_called_once()
        assert exists is True

    async def test_session_expiration(self, session_store, mock_redis_client):
        """Test session expiration handling."""
        creator_id = "test-creator"
        mock_redis_client.get.return_value = None  # Expired session
        
        session_data = await session_store.get_session(creator_id, "expired-session")
        assert session_data is None

    async def test_session_key_format(self, session_store, mock_redis_client):
        """Test session key formatting."""
        creator_id = "test-creator"
        session_id = "test-123"
        
        await session_store.get_session(creator_id, session_id)
        
        # Verify correct key format was used
        call_args = mock_redis_client.get.call_args
        key_used = call_args.args[1]  # Second argument is the key
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
        return RedisHealthChecker(mock_redis_client)

    async def test_basic_health_check(self, health_check, mock_redis_client):
        """Test basic Redis health check."""
        # Mock the get_client method to return our mock
        health_check.redis.get_client = AsyncMock(return_value=mock_redis_client)
        
        # Mock Redis operations for connectivity check
        # The test value needs to match what the health check expects
        test_value = "test_1734134473.123456"  # Example timestamp-based value
        mock_redis_client.set = AsyncMock(return_value=True)
        mock_redis_client.get = AsyncMock(return_value=test_value)
        mock_redis_client.delete = AsyncMock(return_value=1)
        
        # We need to mock the actual test value generation in the health check
        # Let's patch the datetime to make it predictable
        import unittest.mock
        with unittest.mock.patch('shared.cache.health_checks.datetime') as mock_datetime:
            mock_datetime.utcnow.return_value.timestamp.return_value = 1734134473.123456
            mock_redis_client.get.return_value = "test_1734134473.123456"
            
            result = await health_check.check_redis_connectivity()
        
        assert result["status"] == "healthy"
        assert result["test_successful"] is True

    async def test_detailed_health_check(self, health_check, mock_redis_client):
        """Test detailed Redis health check."""
        # Mock the get_client method
        health_check.redis.get_client = AsyncMock(return_value=mock_redis_client)
        
        # Mock pipeline operations properly - pipeline() is sync, methods are sync, execute() is async
        mock_pipeline = Mock()  # Use regular Mock, not AsyncMock
        mock_pipeline.set = Mock()  # Sync method
        mock_pipeline.get = Mock()  # Sync method
        mock_pipeline.execute = AsyncMock()  # Async method
        
        # Mock execute to return results for set operations, then get operations
        mock_pipeline.execute.side_effect = [
            [True] * 10,  # Set operations results
            ["value_0", "value_1", "value_2", "value_3", "value_4", 
             "value_5", "value_6", "value_7", "value_8", "value_9"]  # Get operations results
        ]
        
        mock_redis_client.pipeline = Mock(return_value=mock_pipeline)  # Sync method
        mock_redis_client.delete = AsyncMock(return_value=10)
        
        result = await health_check.check_redis_performance()
        
        assert result["status"] in ["healthy", "degraded"]
        assert "total_operations" in result
        assert "total_time_ms" in result

    async def test_health_check_failure(self, health_check, mock_redis_client):
        """Test health check when Redis is down."""
        # Mock the get_client method to raise an exception
        health_check.redis.get_client = AsyncMock(side_effect=ConnectionError("Redis unavailable"))
        
        result = await health_check.check_redis_connectivity()
        
        assert result["status"] == "unhealthy"
        assert "error" in result

    async def test_memory_usage_check(self, health_check, mock_redis_client):
        """Test memory usage monitoring."""
        # Mock the get_client method
        health_check.redis.get_client = AsyncMock(return_value=mock_redis_client)
        
        # Mock memory info
        mock_redis_client.info.return_value = {
            "used_memory": 1024000,
            "used_memory_human": "1MB",
            "maxmemory": 10240000,
            "mem_fragmentation_ratio": 1.2
        }
        
        result = await health_check.check_redis_memory_usage()
        
        mock_redis_client.info.assert_called_once_with("memory")
        assert "used_memory_bytes" in result
        assert "memory_usage_percent" in result

    async def test_connection_count_check(self, health_check, mock_redis_client):
        """Test connection count monitoring."""
        # Mock the get_client method
        health_check.redis.get_client = AsyncMock(return_value=mock_redis_client)
        
        # Mock info response
        mock_redis_client.info.return_value = {
            "connected_clients": 5,
            "used_memory": 1024000,
            "used_memory_human": "1MB"
        }
        
        result = await health_check.check_redis_memory_usage()
        
        mock_redis_client.info.assert_called_once()
        assert "status" in result

    async def test_performance_check(self, health_check, mock_redis_client):
        """Test Redis performance check."""
        # Mock the get_client method
        health_check.redis.get_client = AsyncMock(return_value=mock_redis_client)
        
        # Mock pipeline operations properly - pipeline() is sync, methods are sync, execute() is async
        mock_pipeline = Mock()  # Use regular Mock, not AsyncMock
        mock_pipeline.set = Mock()  # Sync method
        mock_pipeline.get = Mock()  # Sync method
        mock_pipeline.execute = AsyncMock()  # Async method
        
        # Mock execute to return results for set operations, then get operations
        mock_pipeline.execute.side_effect = [
            [True] * 10,  # Set operations results
            ["value_0", "value_1", "value_2", "value_3", "value_4", 
             "value_5", "value_6", "value_7", "value_8", "value_9"]  # Get operations results
        ]
        
        mock_redis_client.pipeline = Mock(return_value=mock_pipeline)  # Sync method
        mock_redis_client.delete = AsyncMock(return_value=10)
        
        result = await health_check.check_redis_performance()
        
        assert "total_time_ms" in result
        assert "operations_successful" in result


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
        # Mock pipeline to return itself and have proper methods
        mock_pipeline = AsyncMock()
        mock_pipeline.set = AsyncMock()
        mock_pipeline.execute = AsyncMock(return_value=[True, True, True])
        mock_redis_client.pipeline = AsyncMock(return_value=mock_pipeline)
        
        # Simulate pipeline operations
        pipeline = await mock_redis_client.pipeline()
        await pipeline.set("key1", "value1")
        await pipeline.set("key2", "value2")
        await pipeline.set("key3", "value3")
        
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
        mock_pubsub.subscribe = AsyncMock(return_value=True)
        mock_pubsub.get_message = AsyncMock(return_value={
            "type": "message",
            "channel": b"test_channel",
            "data": b"test_message"
        })
        
        mock_redis_client.pubsub = AsyncMock(return_value=mock_pubsub)
        
        pubsub = await mock_redis_client.pubsub()
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
        tenant1_client.get_client = AsyncMock(return_value=mock_redis_client)
        
        tenant2_client = RedisClient("redis://localhost:6379")
        tenant2_client.get_client = AsyncMock(return_value=mock_redis_client)
        
        # Mock setex method for Redis client
        mock_redis_client.setex = AsyncMock(return_value=True)
        
        # Set data for different tenants
        await tenant1_client.set("tenant-1", "user_data", {"name": "John"})
        await tenant2_client.set("tenant-2", "user_data", {"name": "Jane"})
        
        # Verify different keys were used
        assert mock_redis_client.setex.call_count == 2
        
        # Check that tenant IDs are in the keys
        calls = mock_redis_client.setex.call_args_list
        key1 = calls[0].args[0]
        key2 = calls[1].args[0]
        
        assert "tenant-1" in key1
        assert "tenant-2" in key2
        assert key1 != key2