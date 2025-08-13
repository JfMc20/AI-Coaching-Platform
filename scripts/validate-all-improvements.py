#!/usr/bin/env python3
"""
Comprehensive validation script for all testing infrastructure improvements.
Validates that all optimizations and fixes are working correctly.
"""

import os
import sys
import asyncio
import subprocess
import yaml
import logging
from pathlib import Path
from typing import List, Dict, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ImprovementValidator:
    """Validates all testing infrastructure improvements."""
    
    def __init__(self):
        self.results = []
        self.workspace_root = Path.cwd()
        
    def add_result(self, test_name: str, passed: bool, details: str = ""):
        """Add a test result."""
        self.results.append({
            'test': test_name,
            'passed': passed,
            'details': details
        })
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} {test_name}")
        if details:
            print(f"    {details}")
    
    def validate_dockerfile_optimizations(self) -> bool:
        """Validate Dockerfile.test optimizations."""
        dockerfile_path = self.workspace_root / "Dockerfile.test"
        
        if not dockerfile_path.exists():
            self.add_result("Dockerfile.test exists", False, "File not found")
            return False
        
        content = dockerfile_path.read_text(encoding='utf-8')
        
        # Check for --no-install-recommends flag
        has_no_recommends = "--no-install-recommends" in content
        self.add_result("Dockerfile uses --no-install-recommends", has_no_recommends,
                       "Reduces image size by avoiding unnecessary packages")
        
        # Check for apt-get clean
        has_clean = "apt-get clean" in content
        self.add_result("Dockerfile includes apt-get clean", has_clean,
                       "Further reduces image size by cleaning package cache")
        
        return has_no_recommends and has_clean
    
    def validate_compose_logging(self) -> bool:
        """Validate compose services validation script logging."""
        script_path = self.workspace_root / "scripts" / "validate-compose-services.py"
        
        if not script_path.exists():
            self.add_result("Compose validation script exists", False, "File not found")
            return False
        
        content = script_path.read_text(encoding='utf-8')
        
        # Check for logging configuration
        has_logging = "import logging" in content and "logging.basicConfig" in content
        self.add_result("Compose validation has structured logging", has_logging,
                       "Enables better debugging and monitoring")
        
        # Check for try-except blocks
        has_error_handling = "try:" in content and "except Exception as e:" in content
        self.add_result("Compose validation has error handling", has_error_handling,
                       "Prevents script termination on individual validator failures")
        
        return has_logging and has_error_handling
    
    def validate_async_redis(self) -> bool:
        """Validate async Redis implementation."""
        script_path = self.workspace_root / "scripts" / "validate-test-setup.py"
        
        if not script_path.exists():
            self.add_result("Test setup validation script exists", False, "File not found")
            return False
        
        content = script_path.read_text(encoding='utf-8')
        
        # Check for async Redis import
        has_async_redis = "redis.asyncio" in content
        self.add_result("Uses async Redis client", has_async_redis,
                       "Prevents blocking the async event loop")
        
        # Check for proper connection cleanup
        has_cleanup = "finally:" in content and "await r.close()" in content
        self.add_result("Has proper Redis connection cleanup", has_cleanup,
                       "Prevents connection leaks")
        
        # Check for null value handling
        has_null_check = "if value is None:" in content
        self.add_result("Has Redis null value handling", has_null_check,
                       "Prevents AttributeError on None values")
        
        # Check for set operation verification
        has_set_verification = "set_result = await r.set" in content and "if not set_result:" in content
        self.add_result("Has Redis set operation verification", has_set_verification,
                       "Confirms Redis write operations succeed")
        
        # Check for value type normalization
        has_type_normalization = "isinstance(value, bytes)" in content and "normalized_value" in content
        self.add_result("Has Redis value type normalization", has_type_normalization,
                       "Handles both bytes and string values correctly")
        
        # Check for enhanced cleanup error handling
        has_cleanup_error_handling = "try:" in content and "delete_result" in content
        self.add_result("Has enhanced Redis cleanup error handling", has_cleanup_error_handling,
                       "Non-fatal cleanup with informative warnings")
        
        return has_async_redis and has_cleanup and has_null_check and has_set_verification and has_type_normalization
    
    def validate_sql_optimizations(self) -> bool:
        """Validate SQL cleanup function optimizations."""
        sql_path = self.workspace_root / "scripts" / "docker-entrypoint-initdb.d" / "03-setup-functions.sql"
        
        if not sql_path.exists():
            self.add_result("SQL setup functions file exists", False, "File not found")
            return False
        
        content = sql_path.read_text(encoding='utf-8')
        
        # Check for single TRUNCATE statement
        has_single_truncate = "TRUNCATE TABLE" in content and content.count("TRUNCATE TABLE") <= 2
        self.add_result("Uses optimized TRUNCATE statement", has_single_truncate,
                       "Single atomic operation instead of multiple statements")
        
        # Check for RESTART IDENTITY
        has_restart_identity = "RESTART IDENTITY" in content
        self.add_result("Uses RESTART IDENTITY for sequences", has_restart_identity,
                       "Resets sequences atomically with table truncation")
        
        return has_single_truncate and has_restart_identity
    
    def validate_cleanup_optimization(self) -> bool:
        """Validate Docker cleanup command optimization."""
        script_path = self.workspace_root / "scripts" / "clean-test-state.py"
        
        if not script_path.exists():
            self.add_result("Clean test state script exists", False, "File not found")
            return False
        
        content = script_path.read_text(encoding='utf-8')
        
        # Check that redundant rm command is removed
        has_single_command = content.count("docker-compose") < 5  # Should be minimal usage
        self.add_result("Uses optimized cleanup commands", has_single_command,
                       "Removed redundant docker-compose rm command")
        
        # Check for down command with proper flags
        has_proper_down = "down" in content and "-v" in content and "--remove-orphans" in content
        self.add_result("Uses proper docker-compose down flags", has_proper_down,
                       "Single command handles containers, volumes, and orphans")
        
        return has_single_command and has_proper_down
    
    def validate_github_workflow_optimizations(self) -> bool:
        """Validate GitHub workflow artifact upload optimizations."""
        workflow_path = self.workspace_root / ".github" / "workflows" / "test.yml"
        
        if not workflow_path.exists():
            self.add_result("GitHub workflow file exists", False, "File not found")
            return False
        
        content = workflow_path.read_text(encoding='utf-8')
        
        # Check for optimized artifact conditions
        always_count = content.count("if: always()")
        success_failure_count = content.count("if: success() || failure()")
        failure_only_count = content.count("if: failure()")
        
        # Should have minimal "always" conditions, more selective conditions
        has_optimized_conditions = success_failure_count > always_count
        self.add_result("Uses optimized artifact upload conditions", has_optimized_conditions,
                       f"success()||failure(): {success_failure_count}, always(): {always_count}, failure(): {failure_only_count}")
        
        # Check for GitHub Secrets usage
        has_secrets = "${{ secrets." in content
        self.add_result("Uses GitHub Secrets for sensitive data", has_secrets,
                       "Prevents hardcoded credentials in workflow")
        
        return has_optimized_conditions and has_secrets
    
    def validate_docker_compose_documentation(self) -> bool:
        """Validate Docker Compose configuration documentation."""
        compose_path = self.workspace_root / "docker-compose.test.yml"
        
        if not compose_path.exists():
            self.add_result("Docker Compose test file exists", False, "File not found")
            return False
        
        content = compose_path.read_text(encoding='utf-8')
        
        # Check for tmpfs documentation
        has_tmpfs_docs = "NOTE:" in content and "ephemeral" in content
        self.add_result("Has tmpfs configuration documentation", has_tmpfs_docs,
                       "Explains trade-offs and compatibility considerations")
        
        # Check for security warnings
        has_security_warnings = "WARNING:" in content and "durability" in content
        self.add_result("Has database durability warnings", has_security_warnings,
                       "Warns about unsafe settings for production")
        
        # Check for volume comments
        has_volume_docs = "Persistent volumes" in content or "Stores" in content
        self.add_result("Has volume documentation", has_volume_docs,
                       "Explains purpose of each volume")
        
        return has_tmpfs_docs and has_security_warnings and has_volume_docs
    
    async def run_functional_tests(self) -> bool:
        """Run functional tests to ensure improvements work."""
        print("\n🧪 Running functional tests...")
        
        # Test compose validation script using asyncio.to_thread
        try:
            result = await asyncio.to_thread(
                subprocess.run,
                [
                    "python", "scripts/validate-compose-services.py", 
                    "docker-compose.test.yml", 
                    "--services", "postgres-test", "redis-test",
                    "--check-health"
                ],
                capture_output=True, text=True, timeout=30
            )
            
            compose_validation_works = result.returncode == 0
            self.add_result("Compose validation script functional", compose_validation_works,
                           f"Exit code: {result.returncode}")
        except Exception as e:
            self.add_result("Compose validation script functional", False, str(e))
            compose_validation_works = False
        
        # Test cleanup script using asyncio.to_thread
        try:
            result = await asyncio.to_thread(
                subprocess.run,
                [
                    "python", "scripts/clean-test-state.py", 
                    "--skip-containers", "--skip-volumes", "--wait", "0"
                ],
                capture_output=True, text=True, timeout=30
            )
            
            cleanup_works = result.returncode == 0
            self.add_result("Cleanup script functional", cleanup_works,
                           f"Exit code: {result.returncode}")
        except Exception as e:
            self.add_result("Cleanup script functional", False, str(e))
            cleanup_works = False
        
        return compose_validation_works and cleanup_works
    
    async def run_all_validations(self) -> bool:
        """Run all validation checks."""
        print("🔍 Validating Testing Infrastructure Improvements")
        print("=" * 60)
        
        validations = [
            ("Dockerfile Optimizations", self.validate_dockerfile_optimizations()),
            ("Compose Logging", self.validate_compose_logging()),
            ("Async Redis", self.validate_async_redis()),
            ("SQL Optimizations", self.validate_sql_optimizations()),
            ("Cleanup Optimization", self.validate_cleanup_optimization()),
            ("GitHub Workflow", self.validate_github_workflow_optimizations()),
            ("Documentation", self.validate_docker_compose_documentation()),
        ]
        
        # Add functional tests
        functional_result = await self.run_functional_tests()
        validations.append(("Functional Tests", functional_result))
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 Validation Summary:")
        
        passed_count = sum(1 for _, passed in validations if passed)
        total_count = len(validations)
        
        for check_name, passed in validations:
            status = "✅ PASS" if passed else "❌ FAIL"
            print(f"   {check_name}: {status}")
        
        print(f"\n🎯 Overall Result: {passed_count}/{total_count} validations passed")
        
        if passed_count == total_count:
            print("🎉 All improvements validated successfully!")
            return True
        else:
            print("⚠️  Some validations failed - check details above")
            return False


async def main():
    """Main validation function."""
    validator = ImprovementValidator()
    success = await validator.run_all_validations()
    return success


if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⚠️  Validation interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"💥 Validation failed with error: {e}")
        sys.exit(1)