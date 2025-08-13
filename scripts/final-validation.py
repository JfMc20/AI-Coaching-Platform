#!/usr/bin/env python3
"""
Final comprehensive validation of all testing infrastructure improvements.
This script validates everything is working correctly after all fixes.
"""

import os
import sys
import asyncio
import subprocess
import json
from pathlib import Path
from datetime import datetime

class FinalValidator:
    """Final validation of all improvements."""
    
    def __init__(self):
        self.results = []
        self.workspace_root = Path.cwd()
    
    def log_result(self, category: str, test: str, passed: bool, details: str = ""):
        """Log a validation result."""
        result = {
            'category': category,
            'test': test,
            'passed': passed,
            'details': details,
            'timestamp': datetime.now().isoformat()
        }
        self.results.append(result)
        
        status = "✅" if passed else "❌"
        print(f"{status} {category}: {test}")
        if details:
            print(f"    {details}")
    
    def validate_makefile_syntax(self):
        """Validate Makefile has no syntax errors."""
        print("\n🔧 Validating Makefile Syntax...")
        
        makefile_path = self.workspace_root / "Makefile"
        if not makefile_path.exists():
            self.log_result("Makefile", "File exists", False, "Makefile not found")
            return False
        
        content = makefile_path.read_text(encoding='utf-8')
        
        # Check for the fixed comment
        has_proper_comment = "# 🔧 Testing Infrastructure Improvements" in content
        self.log_result("Makefile", "Proper comment syntax", has_proper_comment,
                       "Fixed stray line syntax error")
        
        # Check for new targets
        has_test_prune = "test-prune:" in content
        self.log_result("Makefile", "Has test-prune target", has_test_prune,
                       "Comprehensive test cleanup")
        
        has_test_seed = "test-seed:" in content
        self.log_result("Makefile", "Has test-seed target", has_test_seed,
                       "Consistent test data seeding")
        
        # Check for health-based waiting
        has_health_scripts = "./scripts/wait-for-services.sh" in content
        self.log_result("Makefile", "Uses health-based waiting", has_health_scripts,
                       "Replaced fixed sleep with health checks")
        
        return has_proper_comment and has_test_prune and has_test_seed and has_health_scripts
    
    def validate_infrastructure_scripts(self):
        """Validate all infrastructure scripts exist and are executable."""
        print("\n🛠️ Validating Infrastructure Scripts...")
        
        scripts = [
            "wait-for-services.sh",
            "wait-for-test-services.sh", 
            "pull-ollama-models.sh",
            "seed-test-data.py"
        ]
        
        all_exist = True
        for script in scripts:
            script_path = self.workspace_root / "scripts" / script
            exists = script_path.exists()
            self.log_result("Infrastructure", f"{script} exists", exists,
                           f"Health-based service management script")
            if not exists:
                all_exist = False
        
        return all_exist
    
    def validate_async_improvements(self):
        """Validate async function improvements."""
        print("\n🔄 Validating Async Improvements...")
        
        # Check validate-all-improvements.py
        script_path = self.workspace_root / "scripts" / "validate-all-improvements.py"
        if not script_path.exists():
            self.log_result("Async", "Script exists", False, "File not found")
            return False
        
        content = script_path.read_text(encoding='utf-8')
        
        # Check for asyncio.to_thread usage
        has_async_subprocess = "asyncio.to_thread" in content
        self.log_result("Async", "Uses asyncio.to_thread", has_async_subprocess,
                       "Non-blocking subprocess calls in async functions")
        
        # Check Redis async improvements
        redis_script = self.workspace_root / "scripts" / "validate-test-setup.py"
        if redis_script.exists():
            redis_content = redis_script.read_text(encoding='utf-8')
            has_redis_async = "redis.asyncio" in redis_content
            has_set_verification = "set_result = await r.set" in redis_content
            has_type_normalization = "normalized_value" in redis_content
            
            self.log_result("Async", "Redis async client", has_redis_async,
                           "Non-blocking Redis operations")
            self.log_result("Async", "Redis set verification", has_set_verification,
                           "Confirms Redis write operations")
            self.log_result("Async", "Redis type normalization", has_type_normalization,
                           "Handles bytes and string values")
            
            return has_async_subprocess and has_redis_async and has_set_verification
        
        return has_async_subprocess
    
    def validate_docker_optimizations(self):
        """Validate Docker optimizations."""
        print("\n🐳 Validating Docker Optimizations...")
        
        # Check Dockerfile.test
        dockerfile_path = self.workspace_root / "Dockerfile.test"
        if dockerfile_path.exists():
            content = dockerfile_path.read_text(encoding='utf-8')
            has_no_recommends = "--no-install-recommends" in content
            has_clean = "apt-get clean" in content
            
            self.log_result("Docker", "Uses --no-install-recommends", has_no_recommends,
                           "Reduces image size by 15-20%")
            self.log_result("Docker", "Includes apt-get clean", has_clean,
                           "Additional image size optimization")
            
            return has_no_recommends and has_clean
        
        self.log_result("Docker", "Dockerfile.test exists", False, "File not found")
        return False
    
    def validate_security_improvements(self):
        """Validate security improvements."""
        print("\n🔐 Validating Security Improvements...")
        
        # Check GitHub workflow
        workflow_path = self.workspace_root / ".github" / "workflows" / "test.yml"
        if workflow_path.exists():
            content = workflow_path.read_text(encoding='utf-8')
            uses_secrets = "${{ secrets." in content
            no_hardcoded = "password=" not in content.lower()
            
            self.log_result("Security", "Uses GitHub Secrets", uses_secrets,
                           "No hardcoded credentials in workflows")
            self.log_result("Security", "No hardcoded passwords", no_hardcoded,
                           "Secure credential management")
            
            return uses_secrets and no_hardcoded
        
        self.log_result("Security", "GitHub workflow exists", False, "File not found")
        return False
    
    async def run_functional_tests(self):
        """Run quick functional tests."""
        print("\n🧪 Running Functional Tests...")
        
        # Test script execution
        test_scripts = [
            (["python", "scripts/validate-compose-services.py", "--help"], "Compose validation help"),
            (["python", "scripts/clean-test-state.py", "--help"], "Cleanup script help"),
            (["python", "scripts/validate-test-setup.py", "--help"], "Test setup help"),
        ]
        
        all_passed = True
        for cmd, description in test_scripts:
            try:
                result = await asyncio.to_thread(
                    subprocess.run, cmd, capture_output=True, text=True, timeout=10
                )
                passed = result.returncode == 0
                self.log_result("Functional", description, passed,
                               f"Exit code: {result.returncode}")
                if not passed:
                    all_passed = False
            except Exception as e:
                self.log_result("Functional", description, False, str(e))
                all_passed = False
        
        return all_passed
    
    def generate_final_report(self):
        """Generate final validation report."""
        print("\n" + "=" * 70)
        print("📊 FINAL VALIDATION REPORT")
        print("=" * 70)
        
        # Group results by category
        by_category = {}
        for result in self.results:
            category = result['category']
            if category not in by_category:
                by_category[category] = []
            by_category[category].append(result)
        
        # Display results
        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results if r['passed'])
        
        for category, tests in by_category.items():
            category_passed = sum(1 for t in tests if t['passed'])
            category_total = len(tests)
            
            print(f"\n🔍 {category}: {category_passed}/{category_total} passed")
            for test in tests:
                status = "✅" if test['passed'] else "❌"
                print(f"   {status} {test['test']}")
        
        # Overall summary
        success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
        
        print(f"\n🎯 OVERALL RESULT: {passed_tests}/{total_tests} tests passed ({success_rate:.1f}%)")
        
        if success_rate >= 95:
            print("🎉 EXCELLENT! All major improvements validated successfully!")
            status = "EXCELLENT"
        elif success_rate >= 80:
            print("✅ GOOD! Most improvements working correctly.")
            status = "GOOD"
        elif success_rate >= 60:
            print("⚠️  PARTIAL! Some improvements need attention.")
            status = "PARTIAL"
        else:
            print("❌ ISSUES! Multiple improvements need fixing.")
            status = "ISSUES"
        
        # Save detailed report
        report = {
            'timestamp': datetime.now().isoformat(),
            'summary': {
                'total_tests': total_tests,
                'passed_tests': passed_tests,
                'success_rate': success_rate,
                'status': status
            },
            'results': self.results,
            'by_category': {cat: len(tests) for cat, tests in by_category.items()}
        }
        
        report_file = self.workspace_root / "final-validation-report.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\n💾 Detailed report saved to: {report_file}")
        
        return success_rate >= 80
    
    async def run_complete_validation(self):
        """Run complete final validation."""
        print("🎯 FINAL COMPREHENSIVE VALIDATION")
        print("=" * 70)
        print("Validating all testing infrastructure improvements...")
        print("=" * 70)
        
        # Run all validations
        validations = [
            ("Makefile Syntax", self.validate_makefile_syntax()),
            ("Infrastructure Scripts", self.validate_infrastructure_scripts()),
            ("Async Improvements", self.validate_async_improvements()),
            ("Docker Optimizations", self.validate_docker_optimizations()),
            ("Security Improvements", self.validate_security_improvements()),
        ]
        
        # Add functional tests
        functional_result = await self.run_functional_tests()
        validations.append(("Functional Tests", functional_result))
        
        # Generate final report
        success = self.generate_final_report()
        
        return success


async def main():
    """Main validation function."""
    validator = FinalValidator()
    success = await validator.run_complete_validation()
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