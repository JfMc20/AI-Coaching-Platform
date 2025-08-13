#!/usr/bin/env python3
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
        
        print("\n📊 Performance Report")
        print("=" * 50)
        
        for benchmark in benchmarks:
            name = benchmark.get("name", "Unknown")
            stats = benchmark.get("stats", {})
            mean = stats.get("mean", 0)
            stddev = stats.get("stddev", 0)
            min_time = stats.get("min", 0)
            max_time = stats.get("max", 0)
            
            print(f"\n🔍 {name}")
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
