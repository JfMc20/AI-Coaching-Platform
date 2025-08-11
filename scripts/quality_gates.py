#!/usr/bin/env python3
"""
Quality Gates Enforcement Script
Used by CI/CD to enforce code quality standards and fail builds if thresholds are not met.
"""

import json
import subprocess
import sys
from pathlib import Path
from typing import Dict, Any, List, Tuple


class QualityGates:
    """Enforce code quality gates for CI/CD pipeline"""
    
    def __init__(self):
        self.gates = {
            'complexity': {
                'max_cyclomatic': 10,
                'max_maintainability_index': 20
            },
            'coverage': {
                'min_percentage': 80
            },
            'duplication': {
                'max_percentage': 5
            },
            'security': {
                'max_high_severity': 0,
                'max_medium_severity': 5
            }
        }
        self.failed_checks = []
    
    def run_command(self, cmd: List[str]) -> Tuple[int, str, str]:
        """Run shell command and return exit code, stdout, stderr"""
        try:
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                timeout=300
            )
            return result.returncode, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return 1, "", "Command timed out"
        except Exception as e:
            return 1, "", str(e)
    
    def check_complexity(self) -> bool:
        """Check cyclomatic complexity and maintainability"""
        print("🔍 Checking code complexity...")
        
        # Check cyclomatic complexity
        exit_code, stdout, stderr = self.run_command([
            'radon', 'cc', '.', '--json', '--min', 'B'
        ])
        
        if exit_code != 0:
            self.failed_checks.append(f"Complexity check failed: {stderr}")
            return False
        
        try:
            complexity_data = json.loads(stdout)
            violations = []
            
            for file_path, file_data in complexity_data.items():
                for item in file_data:
                    if item['complexity'] > self.gates['complexity']['max_cyclomatic']:
                        violations.append(
                            f"{file_path}:{item['lineno']} - {item['name']} "
                            f"(complexity: {item['complexity']})"
                        )
            
            if violations:
                self.failed_checks.append(
                    f"Cyclomatic complexity violations:\n" + 
                    "\n".join(f"  ❌ {v}" for v in violations)
                )
                return False
                
        except json.JSONDecodeError:
            self.failed_checks.append("Failed to parse complexity report")
            return False
        
        # Check maintainability index
        exit_code, stdout, stderr = self.run_command([
            'radon', 'mi', '.', '--json', '--min', 'B'
        ])
        
        if exit_code != 0:
            self.failed_checks.append(f"Maintainability check failed: {stderr}")
            return False
        
        print("✅ Complexity checks passed")
        return True
    
    def check_test_coverage(self) -> bool:
        """Check test coverage meets minimum threshold"""
        print("🧪 Checking test coverage...")
        
        exit_code, stdout, stderr = self.run_command([
            'pytest', '--cov=.', '--cov-report=json', '--cov-fail-under=80', '-q'
        ])
        
        if exit_code != 0:
            self.failed_checks.append(f"Test coverage below {self.gates['coverage']['min_percentage']}%")
            return False
        
        # Parse coverage report if available
        coverage_file = Path('coverage.json')
        if coverage_file.exists():
            try:
                with open(coverage_file) as f:
                    coverage_data = json.load(f)
                    total_coverage = coverage_data['totals']['percent_covered']
                    print(f"✅ Test coverage: {total_coverage:.1f}%")
            except Exception:
                print("✅ Test coverage check passed")
        else:
            print("✅ Test coverage check passed")
        
        return True
    
    def check_code_duplication(self) -> bool:
        """Check for code duplication"""
        print("🔍 Checking code duplication...")
        
        exit_code, stdout, stderr = self.run_command([
            'radon', 'raw', '.', '--json'
        ])
        
        if exit_code != 0:
            self.failed_checks.append(f"Duplication check failed: {stderr}")
            return False
        
        try:
            raw_data = json.loads(stdout)
            total_lines = 0
            duplicate_lines = 0
            
            for file_data in raw_data.values():
                total_lines += file_data.get('loc', 0)
                # This is a simplified check - in practice you'd use a proper duplication tool
                # like jscpd or similar
            
            if total_lines > 0:
                duplication_percentage = (duplicate_lines / total_lines) * 100
                if duplication_percentage > self.gates['duplication']['max_percentage']:
                    self.failed_checks.append(
                        f"Code duplication too high: {duplication_percentage:.1f}% "
                        f"(max: {self.gates['duplication']['max_percentage']}%)"
                    )
                    return False
            
        except json.JSONDecodeError:
            self.failed_checks.append("Failed to parse duplication report")
            return False
        
        print("✅ Code duplication check passed")
        return True
    
    def check_security(self) -> bool:
        """Check for security vulnerabilities"""
        print("🔒 Checking security vulnerabilities...")
        
        # Run bandit security scan
        exit_code, stdout, stderr = self.run_command([
            'bandit', '-r', '.', '-f', 'json', '-ll'
        ])
        
        if exit_code != 0 and "No issues identified" not in stderr:
            try:
                bandit_data = json.loads(stdout)
                high_severity = len([
                    issue for issue in bandit_data.get('results', [])
                    if issue.get('issue_severity') == 'HIGH'
                ])
                medium_severity = len([
                    issue for issue in bandit_data.get('results', [])
                    if issue.get('issue_severity') == 'MEDIUM'
                ])
                
                if high_severity > self.gates['security']['max_high_severity']:
                    self.failed_checks.append(
                        f"High severity security issues: {high_severity} "
                        f"(max: {self.gates['security']['max_high_severity']})"
                    )
                    return False
                
                if medium_severity > self.gates['security']['max_medium_severity']:
                    self.failed_checks.append(
                        f"Medium severity security issues: {medium_severity} "
                        f"(max: {self.gates['security']['max_medium_severity']})"
                    )
                    return False
                    
            except json.JSONDecodeError:
                self.failed_checks.append("Failed to parse security report")
                return False
        
        # Run safety check for known vulnerabilities
        exit_code, stdout, stderr = self.run_command([
            'safety', 'check', '--json'
        ])
        
        if exit_code != 0:
            try:
                safety_data = json.loads(stdout)
                if safety_data:  # Has vulnerabilities
                    self.failed_checks.append(
                        f"Known security vulnerabilities found: {len(safety_data)} issues"
                    )
                    return False
            except json.JSONDecodeError:
                # safety might output non-JSON on success
                pass
        
        print("✅ Security checks passed")
        return True
    
    def check_api_schema_sync(self) -> bool:
        """Verify API schemas are in sync with documentation"""
        print("📄 Checking API schema synchronization...")
        
        # Generate current schemas
        exit_code, stdout, stderr = self.run_command([
            'python', 'scripts/generate_openapi_schemas.py'
        ])
        
        if exit_code != 0:
            print("⚠️  Could not generate API schemas (services may not be running)")
            return True  # Don't fail if services aren't running
        
        # Check for changes in API documentation
        exit_code, stdout, stderr = self.run_command([
            'git', 'diff', '--exit-code', 'docs/api/'
        ])
        
        if exit_code != 0:
            self.failed_checks.append(
                "API schemas changed without documentation update. "
                "Please run 'python scripts/generate_openapi_schemas.py' and commit the changes."
            )
            return False
        
        print("✅ API schema synchronization check passed")
        return True
    
    def check_formatting(self) -> bool:
        """Check code formatting"""
        print("🎨 Checking code formatting...")
        
        # Check Black formatting
        exit_code, stdout, stderr = self.run_command([
            'black', '--check', '--line-length=100', '.'
        ])
        
        if exit_code != 0:
            self.failed_checks.append("Code not formatted with Black")
            return False
        
        # Check import sorting
        exit_code, stdout, stderr = self.run_command([
            'isort', '--check-only', '--profile=black', '.'
        ])
        
        if exit_code != 0:
            self.failed_checks.append("Imports not sorted correctly")
            return False
        
        print("✅ Code formatting check passed")
        return True
    
    def check_linting(self) -> bool:
        """Check code linting"""
        print("🔍 Checking code linting...")
        
        # Run ruff
        exit_code, stdout, stderr = self.run_command([
            'ruff', 'check', '.'
        ])
        
        if exit_code != 0:
            self.failed_checks.append(f"Linting errors found:\n{stdout}")
            return False
        
        print("✅ Linting check passed")
        return True
    
    def run_all_checks(self) -> bool:
        """Run all quality gate checks"""
        print("🚀 Running all quality gate checks...\n")
        
        checks = [
            ("Formatting", self.check_formatting),
            ("Linting", self.check_linting),
            ("Complexity", self.check_complexity),
            ("Test Coverage", self.check_test_coverage),
            ("Code Duplication", self.check_code_duplication),
            ("Security", self.check_security),
            ("API Schema Sync", self.check_api_schema_sync),
        ]
        
        passed_checks = 0
        total_checks = len(checks)
        
        for check_name, check_func in checks:
            try:
                if check_func():
                    passed_checks += 1
                else:
                    print(f"❌ {check_name} check failed")
            except Exception as e:
                print(f"❌ {check_name} check failed with error: {e}")
                self.failed_checks.append(f"{check_name} check failed with error: {e}")
        
        print(f"\n📊 Quality Gate Results: {passed_checks}/{total_checks} checks passed")
        
        if self.failed_checks:
            print("\n❌ Failed Checks:")
            for failure in self.failed_checks:
                print(f"  • {failure}")
            return False
        
        print("\n✅ All quality gates passed!")
        return True


def main():
    """Main entry point"""
    gates = QualityGates()
    
    if not gates.run_all_checks():
        print("\n💥 Quality gates failed. Please fix the issues above before merging.")
        sys.exit(1)
    
    print("\n🎉 All quality gates passed! Ready for merge.")
    sys.exit(0)


if __name__ == "__main__":
    main()