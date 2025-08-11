"""
Tests for Redis caching functionality
Tests multi-tenant caching, session storage, and message queuing
"""

import pytest
import asyncio
import os
import uuid
from typing import AsyncGenerator, Set
from datetime import datetime, timedelta

# Configure pytest-asyncio for all tests in this module
pytestmark = pytest.mark.asyncio

# Import the caching modules
from shared.cache.redis_client import RedisClient, CacheManager, get_redis_client, get_cache_manager
from shared.cache.session_store import SessionStore, get_session_store
from shared.cache.message_queue import MessageQueue, get_message_queue
from shared.cache.health_checks import RedisHealthChecker, get_redis_health_checker


# Test Redis configuration
TEST_REDIS_URL = os.getenv("TEST_REDIS_URL", "redis://localhost:6379/15")  # Use DB 15 for tests


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
def unique_tenant_id() -> str:
    """Generate a unique tenant ID for each test to avoid conflicts"""
    return f"test_tenant_{uuid.uuid4().hex[:8]}"


@pytest.fixture(scope="session")
async def redis_client() -> AsyncGenerator[RedisClient, None]:
    """Create Redis client for testing with connectivity check"""
    client = RedisClient(redis_url=TEST_REDIS_URL, default_ttl=60)
    
    # Check Redis connectivity before running tests
    try:
        redis_conn = await client.get_client()
        await redis_conn.ping()
        print(f"✅ Redis connection successful at {TEST_REDIS_URL}")
    except Exception as e:
        pytest.skip(f"Redis is not available at {TEST_REDIS_URL}: {e}")
    
    yield client
    await client.close()


@pytest.fixture(scope="session")
async def cache_manager(redis_client: RedisClient) -> CacheManager:
    """Create cache manager for testing"""
    return CacheManager(redis_client)


@pytest.fixture(scope="session")
async def session_store(redis_client: RedisClient) -> SessionStore:
    """Create session store for testing"""
    return SessionStore(redis_client, default_ttl=300)  # 5 minutes for tests


@pytest.fixture(scope="session")
async def message_queue(redis_client: RedisClient) -> MessageQueue:
    """Create message queue for testing"""
    return MessageQueue(redis_client, stream_prefix="test_queue")


@pytest.fixture(scope="session")
async def health_checker(redis_client: RedisClient, session_store: SessionStore, message_queue: MessageQueue) -> RedisHealthChecker:
    """Create health checker for testing"""
    return RedisHealthChecker(redis_client, session_store, message_queue)


@pytest.fixture(autouse=True)
async def cleanup_redis(redis_client: RedisClient):
    """Clean up Redis after each test using selective key deletion"""
    test_keys: Set[str] = set()
    
    # Store original methods to track keys
    original_set = redis_client.set
    original_increment = redis_client.increment
    
    async def tracked_set(creator_id: str, key: str, *args, **kwargs):
        namespaced_key = redis_client._get_namespaced_key(creator_id, key)
        test_keys.add(namespaced_key)
        return await original_set(creator_id, key, *args, **kwargs)
    
    async def tracked_increment(creator_id: str, key: str, *args, **kwargs):
        namespaced_key = redis_client._get_namespaced_key(creator_id, key)
        test_keys.add(namespaced_key)
        return await original_increment(creator_id, key, *args, **kwargs)
    
    # Monkey patch to track keys
    redis_client.set = tracked_set
    redis_client.increment = tracked_increment
    
    try:
        yield
    finally:
        # Restore original methods
        redis_client.set = original_set
        redis_client.increment = original_increment
        
        # Clean up only the keys created during this test
        if test_keys:
            client = await redis_client.get_client()
            try:
                # Use UNLINK for non-blocking deletion if available
                await client.unlink(*test_keys)
            except AttributeError:
                # Fallback to DELETE if UNLINK is not available
                await client.delete(*test_keys)


class TestRedisClient:
    """Test Redis client functionality"""
    
    async def test_basic_operations(self, redis_client: RedisClient, unique_tenant_id: str):
        """Test basic Redis operations with multi-tenant support"""
        creator_id = unique_tenant_id
        key = "test_key"
        value = {"data": "test_value", "number": 42}
        
        # Test set
        success = await redis_client.set(creator_id, key, value, ttl=60)
        assert success is True
        
        # Test get
        retrieved_value = await redis_client.get(creator_id, key)
        assert retrieved_value == value
        
        # Test exists
        exists = await redis_client.exists(creator_id, key)
        assert exists is True
        
        # Test delete
        deleted = await redis_client.delete(creator_id, key)
        assert deleted is True
        
        # Verify deletion
        retrieved_after_delete = await redis_client.get(creator_id, key)
        assert retrieved_after_delete is None
    
    async def test_multi_tenant_isolation(self, redis_client: RedisClient, unique_tenant_id: str):
        """Test that different creators can't access each other's data"""
        creator1 = f"{unique_tenant_id}_1"
        creator2 = f"{unique_tenant_id}_2"
        key = "shared_key"
        value1 = "value_for_creator_1"
        value2 = "value_for_creator_2"
        
        # Set values for both creators
        await redis_client.set(creator1, key, value1)
        await redis_client.set(creator2, key, value2)
        
        # Verify isolation
        retrieved1 = await redis_client.get(creator1, key)
        retrieved2 = await redis_client.get(creator2, key)
        
        assert retrieved1 == value1
        assert retrieved2 == value2
        assert retrieved1 != retrieved2
    
    async def test_ttl_functionality(self, redis_client: RedisClient, unique_tenant_id: str):
        """Test TTL (Time To Live) functionality"""
        creator_id = unique_tenant_id
        key = "ttl_test_key"
        value = "ttl_test_value"
        ttl = 2  # 2 seconds
        
        # Set with TTL
        await redis_client.set(creator_id, key, value, ttl=ttl)
        
        # Verify key exists
        assert await redis_client.exists(creator_id, key) is True
        
        # Check TTL
        remaining_ttl = await redis_client.get_ttl(creator_id, key)
        assert 0 < remaining_ttl <= ttl
        
        # Wait for expiration
        await asyncio.sleep(ttl + 0.5)
        
        # Verify key expired
        assert await redis_client.exists(creator_id, key) is False
        assert await redis_client.get(creator_id, key) is None
    
    async def test_increment_operations(self, redis_client: RedisClient, unique_tenant_id: str):
        """Test increment operations"""
        creator_id = unique_tenant_id
        key = "counter_key"
        
        # Increment non-existent key
        result = await redis_client.increment(creator_id, key, 1)
        assert result == 1
        
        # Increment existing key
        result = await redis_client.increment(creator_id, key, 5)
        assert result == 6
        
        # Verify value
        value = await redis_client.get(creator_id, key)
        assert int(value) == 6
    
    async def test_pattern_matching(self, redis_client: RedisClient, unique_tenant_id: str):
        """Test pattern matching for keys"""
        creator_id = unique_tenant_id
        
        # Set multiple keys
        await redis_client.set(creator_id, "user:1", "user_1_data")
        await redis_client.set(creator_id, "user:2", "user_2_data")
        await redis_client.set(creator_id, "session:1", "session_1_data")
        
        # Get keys matching pattern
        user_keys = await redis_client.get_keys_pattern(creator_id, "user:*")
        session_keys = await redis_client.get_keys_pattern(creator_id, "session:*")
        
        assert len(user_keys) == 2
        assert len(session_keys) == 1
        assert "user:1" in user_keys
        assert "user:2" in user_keys
        assert "session:1" in session_keys
    
    async def test_clear_tenant_cache(self, redis_client: RedisClient, unique_tenant_id: str):
        """Test clearing all cache for a tenant"""
        creator_id = unique_tenant_id
        
        # Set multiple keys
        await redis_client.set(creator_id, "key1", "value1")
        await redis_client.set(creator_id, "key2", "value2")
        await redis_client.set(creator_id, "key3", "value3")
        
        # Verify keys exist
        assert await redis_client.exists(creator_id, "key1") is True
        assert await redis_client.exists(creator_id, "key2") is True
        assert await redis_client.exists(creator_id, "key3") is True
        
        # Clear tenant cache
        cleared_count = await redis_client.clear_tenant_cache(creator_id)
        assert cleared_count == 3
        
        # Verify keys are gone
        assert await redis_client.exists(creator_id, "key1") is False
        assert await redis_client.exists(creator_id, "key2") is False
        assert await redis_client.exists(creator_id, "key3") is False


class TestCacheManager:
    """Test cache manager functionality"""
    
    async def test_cache_key_generation(self, cache_manager: CacheManager):
        """Test deterministic cache key generation"""
        # Same arguments should produce same key
        key1 = cache_manager.generate_cache_key("arg1", "arg2", param1="value1", param2="value2")
        key2 = cache_manager.generate_cache_key("arg1", "arg2", param1="value1", param2="value2")
        assert key1 == key2
        
        # Different arguments should produce different keys
        key3 = cache_manager.generate_cache_key("arg1", "arg3", param1="value1", param2="value2")
        assert key1 != key3
        
        # Order of kwargs shouldn't matter
        key4 = cache_manager.generate_cache_key("arg1", "arg2", param2="value2", param1="value1")
        assert key1 == key4
    
    async def test_search_results_caching(self, cache_manager: CacheManager, unique_tenant_id: str):
        """Test search results caching"""
        creator_id = unique_tenant_id
        query = "test query"
        model_version = "v1.0"
        filters = {"type": "document", "date_range": "last_week"}
        results = [{"id": "doc1", "score": 0.9}, {"id": "doc2", "score": 0.8}]
        
        # Cache search results
        success = await cache_manager.cache_search_results(
            creator_id, query, model_version, filters, results, ttl=60
        )
        assert success is True
        
        # Retrieve cached results
        cached_results = await cache_manager.get_cached_search_results(
            creator_id, query, model_version, filters
        )
        assert cached_results == results
        
        # Different query should not return cached results
        cached_results_different = await cache_manager.get_cached_search_results(
            creator_id, "different query", model_version, filters
        )
        assert cached_results_different is None
    
    async def test_document_metadata_caching(self, cache_manager: CacheManager, unique_tenant_id: str):
        """Test document metadata caching"""
        creator_id = unique_tenant_id
        document_id = "doc123"
        metadata = {
            "title": "Test Document",
            "pages": 10,
            "size": 1024000,
            "processed_at": datetime.utcnow().isoformat()
        }
        
        # Cache metadata
        success = await cache_manager.cache_document_metadata(creator_id, document_id, metadata)
        assert success is True
        
        # Retrieve metadata
        cached_metadata = await cache_manager.get_cached_document_metadata(creator_id, document_id)
        assert cached_metadata == metadata
        
        # Different document should not return cached metadata
        cached_metadata_different = await cache_manager.get_cached_document_metadata(
            creator_id, "different_doc"
        )
        assert cached_metadata_different is None
    
    async def test_conversation_context_caching(self, cache_manager: CacheManager, unique_tenant_id: str):
        """Test conversation context caching"""
        creator_id = unique_tenant_id
        conversation_id = "conv123"
        context = {
            "recent_messages": ["Hello", "How can I help?"],
            "user_preferences": {"language": "en"},
            "session_data": {"started_at": datetime.utcnow().isoformat()}
        }
        
        # Cache context
        success = await cache_manager.cache_conversation_context(creator_id, conversation_id, context)
        assert success is True
        
        # Retrieve context
        cached_context = await cache_manager.get_cached_conversation_context(creator_id, conversation_id)
        assert cached_context == context


class TestSessionStore:
    """Test session store functionality"""
    
    async def test_session_lifecycle(self, session_store: SessionStore, unique_tenant_id: str):
        """Test complete session lifecycle"""
        creator_id = unique_tenant_id
        user_id = "test_user"
        channel = "web_widget"
        metadata = {"ip": "127.0.0.1", "user_agent": "Test Browser"}
        
        # Create session
        session_id = await session_store.create_session(
            creator_id=creator_id,
            user_id=user_id,
            channel=channel,
            metadata=metadata,
            ttl=300
        )
        assert session_id is not None
        
        # Get session
        session_data = await session_store.get_session(creator_id, session_id)
        assert session_data is not None
        assert session_data["creator_id"] == creator_id
        assert session_data["user_id"] == user_id
        assert session_data["channel"] == channel
        assert session_data["metadata"] == metadata
        assert session_data["is_active"] is True
        
        # Update session
        updates = {"last_page": "/dashboard", "score": 85}
        success = await session_store.update_session(creator_id, session_id, updates)
        assert success is True
        
        # Verify updates
        updated_session = await session_store.get_session(creator_id, session_id)
        assert updated_session["last_page"] == "/dashboard"
        assert updated_session["score"] == 85
        
        # End session
        success = await session_store.end_session(creator_id, session_id)
        assert success is True
        
        # Verify session is inactive
        ended_session = await session_store.get_session(creator_id, session_id)
        assert ended_session is None  # Inactive sessions are not returned by get_session
        
        # Delete session
        success = await session_store.delete_session(creator_id, session_id)
        assert success is True
    
    async def test_anonymous_sessions(self, session_store: SessionStore, unique_tenant_id: str):
        """Test anonymous sessions (without user_id)"""
        creator_id = unique_tenant_id
        
        # Create anonymous session
        session_id = await session_store.create_session(
            creator_id=creator_id,
            user_id=None,
            channel="web_widget"
        )
        assert session_id is not None
        
        # Get session
        session_data = await session_store.get_session(creator_id, session_id)
        assert session_data is not None
        assert session_data["user_id"] is None
        assert session_data["creator_id"] == creator_id
    
    async def test_user_multiple_sessions(self, session_store: SessionStore, unique_tenant_id: str):
        """Test user with multiple active sessions"""
        creator_id = unique_tenant_id
        user_id = "test_user"
        
        # Create multiple sessions for same user
        session1 = await session_store.create_session(creator_id, user_id, "web_widget")
        session2 = await session_store.create_session(creator_id, user_id, "mobile_app")
        
        # Get user sessions
        user_sessions = await session_store.get_user_sessions(creator_id, user_id)
        assert len(user_sessions) == 2
        
        session_ids = [s["session_id"] for s in user_sessions]
        assert session1 in session_ids
        assert session2 in session_ids
    
    async def test_session_stats(self, session_store: SessionStore, unique_tenant_id: str):
        """Test session statistics"""
        creator_id = unique_tenant_id
        
        # Create multiple sessions
        await session_store.create_session(creator_id, "user1", "web_widget")
        await session_store.create_session(creator_id, "user2", "web_widget")
        await session_store.create_session(creator_id, "user3", "mobile_app")
        
        # Get stats
        stats = await session_store.get_session_stats(creator_id)
        
        assert stats["total_sessions"] == 3
        assert stats["active_sessions"] == 3
        assert stats["inactive_sessions"] == 0
        assert stats["channels"]["web_widget"] == 2
        assert stats["channels"]["mobile_app"] == 1


class TestMessageQueue:
    """Test message queue functionality"""
    
    async def test_queue_lifecycle(self, message_queue: MessageQueue, unique_tenant_id: str):
        """Test message queue lifecycle"""
        creator_id = unique_tenant_id
        queue_name = "test_queue"
        
        # Create stream
        success = await message_queue.create_stream(creator_id, queue_name)
        assert success is True
        
        # Send message
        message_id = await message_queue.send_message(
            creator_id=creator_id,
            queue_name=queue_name,
            message_type="test_message",
            data={"content": "Hello, World!", "priority": "high"},
            priority="high"
        )
        assert message_id is not None
        
        # Get queue info
        queue_info = await message_queue.get_queue_info(creator_id, queue_name)
        assert queue_info["length"] >= 1
        
        # Purge queue
        success = await message_queue.purge_queue(creator_id, queue_name)
        assert success is True
        
        # Verify queue is empty
        queue_info_after = await message_queue.get_queue_info(creator_id, queue_name)
        assert queue_info_after["length"] == 0
    
    async def test_message_processing(self, message_queue: MessageQueue, unique_tenant_id: str):
        """Test message processing with consumer"""
        creator_id = unique_tenant_id
        queue_name = f"processing_test_queue_{uuid.uuid4().hex[:8]}"
        processed_messages = []
        consumer_exited = asyncio.Future()
        
        # Message handler
        async def message_handler(message_data):
            processed_messages.append(message_data)
            return True  # Acknowledge message
        
        # Enhanced consumer wrapper that handles graceful shutdown
        async def graceful_consumer():
            try:
                await message_queue.consume_messages(
                    creator_id=creator_id,
                    queue_name=queue_name,
                    handler=message_handler,
                    batch_size=5,
                    block_time=100
                )
            except asyncio.CancelledError:
                # Perform graceful shutdown - acknowledge any outstanding messages
                # This would be implemented in the actual consume_messages method
                pass
            finally:
                # Signal that consumer has exited cleanly
                if not consumer_exited.done():
                    consumer_exited.set_result(True)
        
        # Create stream and send messages
        await message_queue.create_stream(creator_id, queue_name)
        
        # Send test messages
        for i in range(3):
            await message_queue.send_message(
                creator_id=creator_id,
                queue_name=queue_name,
                message_type="test_message",
                data={"index": i, "content": f"Message {i}"}
            )
        
        # Start consumer
        consumer_task = asyncio.create_task(graceful_consumer())
        
        # Let consumer process messages
        await asyncio.sleep(2)
        
        # Stop consumer gracefully
        await message_queue.stop_all_consumers()
        
        # Wait for consumer to exit cleanly or timeout
        try:
            await asyncio.wait_for(consumer_exited, timeout=5.0)
        except asyncio.TimeoutError:
            # If graceful shutdown times out, cancel the task
            consumer_task.cancel()
            try:
                await consumer_task
            except asyncio.CancelledError:
                pass
        
        # Verify messages were processed
        assert len(processed_messages) == 3
        
        # Verify message content
        indices = [msg["data"]["index"] for msg in processed_messages]
        assert set(indices) == {0, 1, 2}


class TestHealthChecks:
    """Test Redis health check functionality"""
    
    async def test_connectivity_check(self, health_checker: RedisHealthChecker):
        """Test Redis connectivity check"""
        result = await health_checker.check_redis_connectivity()
        
        assert result["status"] == "healthy"
        assert result["test_successful"] is True
        assert result["error"] is None
    
    async def test_performance_check(self, health_checker: RedisHealthChecker):
        """Test Redis performance check"""
        result = await health_checker.check_redis_performance()
        
        assert result["status"] in ["healthy", "degraded"]
        assert result["total_operations"] == 30
        assert result["operations_successful"] is True
        assert result["total_time_ms"] > 0
    
    async def test_isolation_check(self, health_checker: RedisHealthChecker):
        """Test multi-tenant isolation check"""
        result = await health_checker.check_multi_tenant_isolation()
        
        assert result["status"] == "healthy"
        assert result["isolation_working"] is True
        assert result["creator1_value_correct"] is True
        assert result["creator2_value_correct"] is True
        assert result["values_isolated"] is True
    
    async def test_session_store_check(self, health_checker: RedisHealthChecker):
        """Test session store health check"""
        result = await health_checker.check_session_store()
        
        assert result["status"] == "healthy"
        assert result["session_creation"] is True
        assert result["session_retrieval"] is True
        assert result["session_update"] is True
        assert result["data_integrity"] is True
    
    async def test_message_queue_check(self, health_checker: RedisHealthChecker):
        """Test message queue health check"""
        result = await health_checker.check_message_queue()
        
        assert result["status"] == "healthy"
        assert result["stream_creation"] is True
        assert result["message_sending"] is True
        assert result["queue_info_retrieval"] is True
        assert result["message_count"] > 0
    
    async def test_comprehensive_health_check(self, health_checker: RedisHealthChecker):
        """Test comprehensive health check"""
        result = await health_checker.comprehensive_health_check()
        
        assert result["overall_status"] in ["healthy", "degraded", "unhealthy"]
        assert "timestamp" in result
        assert "total_check_time_ms" in result
        assert "checks" in result
        assert "summary" in result
        
        # Verify all checks are present
        checks = result["checks"]
        expected_checks = [
            "connectivity", "performance", "multi_tenant_isolation",
            "session_store", "message_queue", "memory_usage"
        ]
        
        for check_name in expected_checks:
            assert check_name in checks
            assert "status" in checks[check_name]
        
        # Verify summary
        summary = result["summary"]
        assert summary["total_checks"] == len(expected_checks)
        assert summary["healthy_checks"] + summary["degraded_checks"] + summary["unhealthy_checks"] == summary["total_checks"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])