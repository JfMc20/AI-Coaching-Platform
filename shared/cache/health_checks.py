"""
Redis health check utilities for MVP Coaching AI Platform
Provides comprehensive health monitoring for Redis services
"""

import asyncio
import logging
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from .redis_client import RedisClient, get_redis_client
from .session_store import SessionStore, get_session_store
from .message_queue import MessageQueue, get_message_queue

logger = logging.getLogger(__name__)


class RedisHealthChecker:
    """Comprehensive Redis health checker"""
    
    def __init__(
        self, 
        redis_client: Optional[RedisClient] = None,
        session_store: Optional[SessionStore] = None,
        message_queue: Optional[MessageQueue] = None
    ):
        """
        Initialize health checker
        
        Args:
            redis_client: Redis client instance
            session_store: Session store instance
            message_queue: Message queue instance
        """
        self.redis = redis_client or get_redis_client()
        self.session_store = session_store or get_session_store()
        self.message_queue = message_queue or get_message_queue()
    
    def _normalize_redis_value(self, value: Any) -> str:
        """
        Normalize Redis return value to string for comparison
        
        Args:
            value: Value from Redis (could be bytes or string)
            
        Returns:
            String representation of the value
        """
        if isinstance(value, bytes):
            return value.decode('utf-8')
        return str(value) if value is not None else None
    
    async def check_redis_connectivity(self) -> Dict[str, Any]:
        """Check basic Redis connectivity"""
        # Generate unique test key
        test_key = f"health_check_connectivity_{uuid.uuid4().hex}"
        test_value = f"test_{datetime.utcnow().timestamp()}"
        client = None
        
        try:
            client = await self.redis.get_client()
            
            # Set, get, and delete test key
            await client.set(test_key, test_value, ex=10)
            retrieved_value = await client.get(test_key)
            
            # Normalize the retrieved value for comparison
            normalized_value = self._normalize_redis_value(retrieved_value)
            success = normalized_value == test_value
            
            return {
                "status": "healthy" if success else "unhealthy",
                "test_successful": success,
                "response_time_ms": 0,  # Could add timing here
                "error": None
            }
        except Exception as e:
            logger.exception(f"Redis connectivity check failed: {e}")
            return {
                "status": "unhealthy",
                "test_successful": False,
                "response_time_ms": 0,
                "error": str(e)
            }
        finally:
            # Ensure cleanup always happens
            if client:
                try:
                    await client.delete(test_key)
                except Exception as cleanup_error:
                    logger.warning(f"Failed to cleanup test key {test_key}: {cleanup_error}")
    
    async def check_redis_performance(self) -> Dict[str, Any]:
        """Check Redis performance metrics"""
        # Generate unique test keys
        unique_id = uuid.uuid4().hex
        test_keys = [f"perf_test_{unique_id}_{i}" for i in range(10)]
        test_values = [f"value_{i}" for i in range(10)]
        client = None
        
        try:
            client = await self.redis.get_client()
            
            # Performance test: multiple operations
            start_time = datetime.utcnow()
            
            # Batch set
            pipe = client.pipeline()
            for key, value in zip(test_keys, test_values):
                pipe.set(key, value, ex=30)
            await pipe.execute()
            
            # Batch get
            pipe = client.pipeline()
            for key in test_keys:
                pipe.get(key)
            results = await pipe.execute()
            
            end_time = datetime.utcnow()
            total_time_ms = (end_time - start_time).total_seconds() * 1000
            
            # Verify results - normalize Redis values for comparison
            normalized_results = [self._normalize_redis_value(result) for result in results]
            success = all(result == expected for result, expected in zip(normalized_results, test_values))
            
            return {
                "status": "healthy" if success and total_time_ms < 1000 else "degraded",
                "total_operations": 30,  # 10 sets + 10 gets + 10 deletes
                "total_time_ms": total_time_ms,
                "avg_time_per_op_ms": total_time_ms / 30,
                "operations_successful": success,
                "error": None
            }
        except Exception as e:
            logger.exception(f"Redis performance check failed: {e}")
            return {
                "status": "unhealthy",
                "total_operations": 0,
                "total_time_ms": 0,
                "avg_time_per_op_ms": 0,
                "operations_successful": False,
                "error": str(e)
            }
        finally:
            # Ensure cleanup always happens
            if client and test_keys:
                try:
                    await client.delete(*test_keys)
                except TypeError:
                    # Fallback to deleting keys one by one if client doesn't support multiple keys
                    for key in test_keys:
                        try:
                            await client.delete(key)
                        except Exception as single_delete_error:
                            logger.warning(f"Failed to cleanup key {key}: {single_delete_error}")
                except Exception as cleanup_error:
                    logger.warning(f"Failed to cleanup performance test keys: {cleanup_error}")
    
    async def check_multi_tenant_isolation(self) -> Dict[str, Any]:
        """Check multi-tenant data isolation"""
        # Generate unique test identifiers
        unique_id = uuid.uuid4().hex
        creator1 = f"test_creator_1_{unique_id}"
        creator2 = f"test_creator_2_{unique_id}"
        test_key = f"isolation_test_{unique_id}"
        test_value1 = f"value_for_creator_1_{unique_id}"
        test_value2 = f"value_for_creator_2_{unique_id}"
        
        try:
            # Set values for both creators
            await self.redis.set(creator1, test_key, test_value1, 30)
            await self.redis.set(creator2, test_key, test_value2, 30)
            
            # Get values and verify isolation
            retrieved1 = await self.redis.get(creator1, test_key)
            retrieved2 = await self.redis.get(creator2, test_key)
            
            # Normalize values for comparison
            normalized1 = self._normalize_redis_value(retrieved1)
            normalized2 = self._normalize_redis_value(retrieved2)
            
            # Verify isolation
            isolation_working = (
                normalized1 == test_value1 and 
                normalized2 == test_value2 and 
                normalized1 != normalized2
            )
            
            return {
                "status": "healthy" if isolation_working else "unhealthy",
                "isolation_working": isolation_working,
                "creator1_value_correct": normalized1 == test_value1,
                "creator2_value_correct": normalized2 == test_value2,
                "values_isolated": normalized1 != normalized2,
                "error": None
            }
        except Exception as e:
            logger.exception(f"Multi-tenant isolation check failed: {e}")
            return {
                "status": "unhealthy",
                "isolation_working": False,
                "error": str(e)
            }
        finally:
            # Ensure cleanup always happens
            try:
                await self.redis.delete(creator1, test_key)
                await self.redis.delete(creator2, test_key)
            except Exception as cleanup_error:
                logger.warning(f"Failed to cleanup isolation test keys: {cleanup_error}")
    
    async def check_session_store(self) -> Dict[str, Any]:
        """Check session store functionality"""
        # Generate unique identifiers
        unique_id = uuid.uuid4().hex
        creator_id = f"test_creator_session_{unique_id}"
        user_id = f"test_user_{unique_id}"
        session_id = None
        
        try:
            # Create test session
            session_id = await self.session_store.create_session(
                creator_id=creator_id,
                user_id=user_id,
                channel="test_channel",
                metadata={"test": True, "unique_id": unique_id},
                ttl=60
            )
            
            if not session_id:
                return {
                    "status": "unhealthy",
                    "session_creation": False,
                    "error": "Failed to create session"
                }
            
            # Retrieve session
            session_data = await self.session_store.get_session(creator_id, session_id)
            
            # Update session
            update_success = await self.session_store.update_session(
                creator_id, session_id, {"test_update": True}
            )
            
            # Validate session data safely
            is_valid_session = (
                session_data is not None and 
                isinstance(session_data, dict) and
                session_data.get("creator_id") == creator_id and
                session_data.get("user_id") == user_id
            )
            
            success = is_valid_session and update_success
            
            return {
                "status": "healthy" if success else "unhealthy",
                "session_creation": session_id is not None,
                "session_retrieval": session_data is not None,
                "session_update": update_success,
                "data_integrity": bool(session_data and isinstance(session_data, dict) and session_data.get("creator_id") == creator_id),
                "error": None
            }
        except Exception as e:
            logger.exception(f"Session store check failed: {e}")
            return {
                "status": "unhealthy",
                "session_creation": False,
                "session_retrieval": False,
                "session_update": False,
                "data_integrity": False,
                "error": str(e)
            }
        finally:
            # Ensure cleanup always happens
            if session_id:
                try:
                    await self.session_store.delete_session(creator_id, session_id)
                except Exception as cleanup_error:
                    logger.warning(f"Failed to cleanup session {session_id}: {cleanup_error}")
    
    async def check_message_queue(self) -> Dict[str, Any]:
        """Check message queue functionality"""
        # Generate unique identifiers
        unique_id = uuid.uuid4().hex
        creator_id = f"test_creator_queue_{unique_id}"
        queue_name = f"test_queue_{unique_id}"
        
        try:
            # Create stream
            stream_created = await self.message_queue.create_stream(creator_id, queue_name)
            
            # Send test message
            message_id = await self.message_queue.send_message(
                creator_id=creator_id,
                queue_name=queue_name,
                message_type="test_message",
                data={"test": True, "timestamp": datetime.utcnow().isoformat(), "unique_id": unique_id}
            )
            
            # Get queue info and ensure it's valid
            queue_info = await self.message_queue.get_queue_info(creator_id, queue_name)
            queue_info = queue_info or {}  # Ensure it's a dict if None
            
            success = (
                stream_created and
                message_id is not None and
                queue_info.get("length", 0) > 0
            )
            
            return {
                "status": "healthy" if success else "unhealthy",
                "stream_creation": stream_created,
                "message_sending": message_id is not None,
                "queue_info_retrieval": bool(queue_info),
                "message_count": queue_info.get("length", 0),
                "error": None
            }
        except Exception as e:
            logger.exception(f"Message queue check failed: {e}")
            return {
                "status": "unhealthy",
                "stream_creation": False,
                "message_sending": False,
                "queue_info_retrieval": False,
                "message_count": 0,
                "error": str(e)
            }
        finally:
            # Ensure cleanup always happens
            try:
                await self.message_queue.purge_queue(creator_id, queue_name)
            except Exception as cleanup_error:
                logger.warning(f"Failed to cleanup queue {queue_name}: {cleanup_error}")
    
    async def check_redis_memory_usage(self) -> Dict[str, Any]:
        """Check Redis memory usage"""
        try:
            client = await self.redis.get_client()
            info = await client.info("memory")
            
            used_memory = info.get("used_memory", 0)
            used_memory_human = info.get("used_memory_human", "0B")
            max_memory = info.get("maxmemory", 0)
            
            # Calculate memory usage percentage
            memory_usage_percent = 0
            if max_memory > 0:
                memory_usage_percent = (used_memory / max_memory) * 100
            
            # Determine status based on memory usage
            if memory_usage_percent > 90:
                status = "critical"
            elif memory_usage_percent > 75:
                status = "warning"
            else:
                status = "healthy"
            
            return {
                "status": status,
                "used_memory_bytes": used_memory,
                "used_memory_human": used_memory_human,
                "max_memory_bytes": max_memory,
                "memory_usage_percent": memory_usage_percent,
                "fragmentation_ratio": info.get("mem_fragmentation_ratio", 0),
                "error": None
            }
        except Exception as e:
            logger.exception(f"Redis memory usage check failed: {e}")
            return {
                "status": "unhealthy",
                "used_memory_bytes": 0,
                "used_memory_human": "unknown",
                "max_memory_bytes": 0,
                "memory_usage_percent": 0,
                "fragmentation_ratio": 0,
                "error": str(e)
            }
    
    async def comprehensive_health_check(self) -> Dict[str, Any]:
        """Run comprehensive health check"""
        start_time = datetime.utcnow()
        
        # Run all health checks concurrently
        checks = await asyncio.gather(
            self.check_redis_connectivity(),
            self.check_redis_performance(),
            self.check_multi_tenant_isolation(),
            self.check_session_store(),
            self.check_message_queue(),
            self.check_redis_memory_usage(),
            return_exceptions=True
        )
        
        end_time = datetime.utcnow()
        total_time_ms = (end_time - start_time).total_seconds() * 1000
        
        # Process results
        connectivity, performance, isolation, sessions, queues, memory = checks
        
        # Handle any exceptions
        for i, check in enumerate(checks):
            if isinstance(check, Exception):
                logger.exception(f"Health check {i} failed with exception: {check}")
                checks[i] = {"status": "unhealthy", "error": str(check)}
        
        # Determine overall status
        statuses = [check.get("status", "unhealthy") for check in checks]
        if "unhealthy" in statuses:
            overall_status = "unhealthy"
        elif "critical" in statuses:
            overall_status = "critical"
        elif "warning" in statuses or "degraded" in statuses:
            overall_status = "degraded"
        else:
            overall_status = "healthy"
        
        return {
            "overall_status": overall_status,
            "timestamp": start_time.isoformat(),
            "total_check_time_ms": total_time_ms,
            "checks": {
                "connectivity": connectivity,
                "performance": performance,
                "multi_tenant_isolation": isolation,
                "session_store": sessions,
                "message_queue": queues,
                "memory_usage": memory
            },
            "summary": {
                "healthy_checks": statuses.count("healthy"),
                "degraded_checks": statuses.count("degraded") + statuses.count("warning"),
                "unhealthy_checks": statuses.count("unhealthy") + statuses.count("critical"),
                "total_checks": len(statuses)
            }
        }


# Global health checker instance
_health_checker: Optional[RedisHealthChecker] = None


def get_redis_health_checker() -> RedisHealthChecker:
    """Get global Redis health checker instance"""
    global _health_checker
    if _health_checker is None:
        _health_checker = RedisHealthChecker()
    return _health_checker


async def quick_health_check() -> Dict[str, Any]:
    """Quick health check for basic Redis functionality"""
    checker = get_redis_health_checker()
    return await checker.check_redis_connectivity()


async def full_health_check() -> Dict[str, Any]:
    """Full comprehensive health check"""
    checker = get_redis_health_checker()
    return await checker.comprehensive_health_check()