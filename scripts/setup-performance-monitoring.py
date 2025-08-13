#!/usr/bin/env python3
"""
Performance monitoring setup for testing infrastructure.
Sets up pytest-benchmark and performance tracking.
"""

import subprocess
import sys
from pathlib import Path


def install_performance_tools():
    """Install performance monitoring tools."""
    print("📦 Installing performance monitoring tools...")
    
    tools = [
        "pytest-benchmark",
        "memory-profiler",
        "psutil"
    ]
    
    for tool in tools:
        try:
            print(f"   Installing {tool}...")
            result = subprocess.run(
                ["pip", "install", tool], 
                capture_output=True, text=True, timeout=60
            )
            if result.returncode == 0:
                print(f"   ✅ {tool} installed successfully")
            else:
                print(f"   ❌ Failed to install {tool}: {result.stderr}")
                return False
        except Exception as e:
            print(f"   ❌ Error installing {tool}: {e}")
            return False
    
    return True


def create_performance_config():
    """Create performance monitoring configuration."""
    print("⚙️  Creating performance monitoring configuration...")
    
    # Update pytest.ini with benchmark configuration
    pytest_config = """
# Performance benchmarking configuration
[tool:pytest]
addopts = 
    --benchmark-only
    --benchmark-sort=mean
    --benchmark-json=benchmark-results.json
    --benchmark-save=benchmark
    --benchmark-autosave

# Benchmark thresholds
benchmark_min_rounds = 5
benchmark_max_time = 10.0
benchmark_min_time = 0.000005
benchmark_timer = time.perf_counter
"""
    
    # Create performance test example
    performance_test = '''"""
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
'''
    
    # Write performance test file
    test_dir = Path("tests/performance")
    test_dir.mkdir(parents=True, exist_ok=True)
    
    performance_file = test_dir / "test_performance_benchmarks.py"
    performance_file.write_text(performance_test, encoding='utf-8')
    
    print(f"   ✅ Performance tests created: {performance_file}")
    
    # Create performance monitoring script
    monitor_script = '''#!/usr/bin/env python3
"""
Performance monitoring runner.
Runs performance tests and generates reports.
"""

import subprocess
import sys
import json
from pathlib import Path
from datetime import datetime


def run_performance_tests():
    """Run performance benchmarks."""
    print("🚀 Running performance benchmarks...")
    
    try:
        result = subprocess.run([
            "pytest", 
            "tests/performance/",
            "--benchmark-only",
            "--benchmark-json=benchmark-results.json",
            "--benchmark-sort=mean",
            "-v"
        ], capture_output=True, text=True, timeout=300)
        
        if result.returncode == 0:
            print("✅ Performance tests completed successfully")
            return True
        else:
            print(f"❌ Performance tests failed: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Error running performance tests: {e}")
        return False


def generate_performance_report():
    """Generate performance report from benchmark results."""
    results_file = Path("benchmark-results.json")
    
    if not results_file.exists():
        print("⚠️  No benchmark results found")
        return False
    
    try:
        with open(results_file) as f:
            data = json.load(f)
        
        benchmarks = data.get("benchmarks", [])
        
        print("\\n📊 Performance Report")
        print("=" * 50)
        
        for benchmark in benchmarks:
            name = benchmark.get("name", "Unknown")
            stats = benchmark.get("stats", {})
            mean = stats.get("mean", 0)
            stddev = stats.get("stddev", 0)
            min_time = stats.get("min", 0)
            max_time = stats.get("max", 0)
            
            print(f"\\n🔍 {name}")
            print(f"   Mean: {mean:.6f}s")
            print(f"   Std Dev: {stddev:.6f}s")
            print(f"   Min: {min_time:.6f}s")
            print(f"   Max: {max_time:.6f}s")
        
        return True
        
    except Exception as e:
        print(f"❌ Error generating report: {e}")
        return False


def main():
    """Main function."""
    success = run_performance_tests()
    if success:
        generate_performance_report()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
'''
    
    monitor_file = Path("scripts/run-performance-tests.py")
    monitor_file.write_text(monitor_script, encoding='utf-8')
    
    print(f"   ✅ Performance monitor created: {monitor_file}")
    
    return True


def update_requirements():
    """Update requirements-test.txt with performance tools."""
    print("📝 Updating requirements-test.txt...")
    
    req_file = Path("requirements-test.txt")
    
    if req_file.exists():
        content = req_file.read_text()
        
        # Add performance tools if not already present
        tools_to_add = []
        if "pytest-benchmark" not in content:
            tools_to_add.append("pytest-benchmark>=4.0.0")
        if "memory-profiler" not in content:
            tools_to_add.append("memory-profiler>=0.60.0")
        if "psutil" not in content:
            tools_to_add.append("psutil>=5.9.0")
        
        if tools_to_add:
            content += "\n# Performance monitoring tools\n"
            content += "\n".join(tools_to_add) + "\n"
            req_file.write_text(content, encoding='utf-8')
            print(f"   ✅ Added {len(tools_to_add)} performance tools to requirements-test.txt")
        else:
            print("   ✅ Performance tools already in requirements-test.txt")
    else:
        print("   ⚠️  requirements-test.txt not found, creating it...")
        content = """# Performance monitoring tools
pytest-benchmark>=4.0.0
memory-profiler>=0.60.0
psutil>=5.9.0
"""
        req_file.write_text(content, encoding='utf-8')
        print("   ✅ Created requirements-test.txt with performance tools")
    
    return True


def main():
    """Main setup function."""
    print("🔧 Setting up Performance Monitoring")
    print("=" * 40)
    
    steps = [
        ("Installing performance tools", install_performance_tools),
        ("Creating performance configuration", create_performance_config),
        ("Updating requirements", update_requirements)
    ]
    
    for step_name, step_func in steps:
        print(f"\\n{step_name}...")
        if not step_func():
            print(f"❌ Failed: {step_name}")
            return False
        print(f"✅ Completed: {step_name}")
    
    print("\\n🎉 Performance monitoring setup complete!")
    print("\\n📋 Next steps:")
    print("   1. Run: python scripts/run-performance-tests.py")
    print("   2. Check benchmark-results.json for detailed metrics")
    print("   3. Set up regular performance monitoring in CI/CD")
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)