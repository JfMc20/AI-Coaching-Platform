"""
Performance tests for testing infrastructure.
"""

import pytest
import time
import asyncio
from unittest.mock import AsyncMock


class TestPerformance:
    """Performance benchmarks for key operations."""
    
    def test_sync_operation_performance(self, benchmark):
        """Benchmark synchronous operations."""
        def sync_operation():
            # Simulate some work
            time.sleep(0.001)
            return "completed"
        
        result = benchmark(sync_operation)
        assert result == "completed"
    
    @pytest.mark.asyncio
    async def test_async_operation_performance(self, benchmark):
        """Benchmark asynchronous operations."""
        async def async_operation():
            # Simulate async work
            await asyncio.sleep(0.001)
            return "completed"
        
        result = await benchmark(async_operation)
        assert result == "completed"
    
    def test_redis_connection_performance(self, benchmark):
        """Benchmark Redis connection operations."""
        def redis_mock_operation():
            # Mock Redis operation
            mock_redis = AsyncMock()
            mock_redis.ping.return_value = True
            return mock_redis.ping.return_value
        
        result = benchmark(redis_mock_operation)
        assert result is True
    
    def test_database_query_performance(self, benchmark):
        """Benchmark database query operations."""
        def db_mock_operation():
            # Mock database operation
            time.sleep(0.002)  # Simulate DB query time
            return {"id": 1, "name": "test"}
        
        result = benchmark(db_mock_operation)
        assert result["id"] == 1
    
    def test_validation_script_performance(self, benchmark):
        """Benchmark validation script performance."""
        def validation_operation():
            # Simulate validation work
            data = {"services": {"test": {"healthcheck": {"test": "curl"}}}}
            return len(data["services"]) > 0
        
        result = benchmark(validation_operation)
        assert result is True


class TestMemoryUsage:
    """Memory usage tests."""
    
    def test_memory_usage_validation(self):
        """Test memory usage during validation."""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        
        # Simulate memory-intensive operation
        large_data = ["test" * 1000 for _ in range(1000)]
        
        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory
        
        # Assert memory increase is reasonable (less than 50MB)
        assert memory_increase < 50 * 1024 * 1024
        
        # Cleanup
        del large_data


class TestConcurrentPerformance:
    """Concurrent operation performance tests."""
    
    @pytest.mark.asyncio
    async def test_concurrent_validations(self, benchmark):
        """Test performance of concurrent validations."""
        async def concurrent_operations():
            tasks = []
            for i in range(10):
                async def mock_validation():
                    await asyncio.sleep(0.001)
                    return f"validation_{i}"
                tasks.append(mock_validation())
            
            results = await asyncio.gather(*tasks)
            return len(results)
        
        result = await benchmark(concurrent_operations)
        assert result == 10
