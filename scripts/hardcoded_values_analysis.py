#!/usr/bin/env python3
"""
Hardcoded values analysis script.
Identifies hardcoded URLs, API keys, passwords, and other values that should be configurable.
"""

import os
import re
import ast
from pathlib import Path
from typing import Dict, List, Set, Tuple, Any
import argparse


class HardcodedValuesAnalyzer:
    """Analyzer for hardcoded values in the codebase."""
    
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
        self.hardcoded_values: Dict[str, List[Dict[str, Any]]] = {
            "urls": [],
            "api_keys": [],
            "passwords": [],
            "database_connections": [],
            "ip_addresses": [],
            "ports": [],
            "secrets": [],
            "file_paths": [],
            "email_addresses": []
        }
        
        # Patterns to detect hardcoded values
        self.patterns = {
            "urls": [
                r'https?://[^\s\'"]+',
                r'ftp://[^\s\'"]+',
                r'ws://[^\s\'"]+',
                r'wss://[^\s\'"]+',
            ],
            "api_keys": [
                r'["\'](?:api[_-]?key|apikey)["\']:\s*["\'][^"\']{20,}["\']',
                r'["\'](?:access[_-]?token|accesstoken)["\']:\s*["\'][^"\']{20,}["\']',
                r'["\'](?:secret[_-]?key|secretkey)["\']:\s*["\'][^"\']{20,}["\']',
            ],
            "passwords": [
                r'["\'](?:password|passwd|pwd)["\']:\s*["\'][^"\']+["\']',
                r'password\s*=\s*["\'][^"\']+["\']',
                r'passwd\s*=\s*["\'][^"\']+["\']',
            ],
            "database_connections": [
                r'postgresql://[^\s\'"]+',
                r'mysql://[^\s\'"]+',
                r'mongodb://[^\s\'"]+',
                r'redis://[^\s\'"]+',
                r'sqlite:///[^\s\'"]+',
            ],
            "ip_addresses": [
                r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b',
                r'\b(?:[0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}\b',  # IPv6
            ],
            "ports": [
                r':(\d{4,5})\b',  # Port numbers (4-5 digits)
            ],
            "secrets": [
                r'["\'](?:secret|token|key)["\']:\s*["\'][^"\']{16,}["\']',
                r'(?:SECRET|TOKEN|KEY)\s*=\s*["\'][^"\']{16,}["\']',
            ],
            "file_paths": [
                r'["\'](?:/[^/\s"\']+)+["\']',  # Absolute paths
                r'["\'](?:\./[^/\s"\']+)+["\']',  # Relative paths starting with ./
            ],
            "email_addresses": [
                r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            ]
        }
        
        # Values to ignore (common false positives)
        self.ignore_patterns = {
            "urls": [
                r'https?://localhost',
                r'https?://127\.0\.0\.1',
                r'https?://example\.com',
                r'https?://test\.com',
                r'https?://.*\.test',
                r'http://test',
            ],
            "ip_addresses": [
                r'127\.0\.0\.1',
                r'0\.0\.0\.0',
                r'255\.255\.255\.255',
            ],
            "file_paths": [
                r'"/tmp/',
                r'"/var/',
                r'"/usr/',
                r'"/etc/',
                r'"\./',
                r'"\.\.',
            ],
            "email_addresses": [
                r'.*@example\.com',
                r'.*@test\.com',
                r'test@.*',
                r'admin@.*',
                r'user@.*',
            ]
        }
    
    def should_ignore_value(self, category: str, value: str) -> bool:
        """Check if a value should be ignored based on ignore patterns."""
        if category not in self.ignore_patterns:
            return False
        
        for pattern in self.ignore_patterns[category]:
            if re.search(pattern, value, re.IGNORECASE):
                return True
        
        return False
    
    def mask_sensitive_value(self, category: str, value: str) -> str:
        """Mask sensitive values to prevent credential exposure in reports."""
        # Categories that require masking for security
        sensitive_categories = {"api_keys", "secrets", "passwords", "database_connections"}
        
        if category not in sensitive_categories:
            return value
        
        # Don't mask very short values (likely not real credentials)
        if len(value) < 8:
            return value
        
        # For very long values, show first 4 and last 4 characters
        if len(value) > 16:
            masked_middle = '*' * (len(value) - 8)
            return f"{value[:4]}{masked_middle}{value[-4:]}"
        
        # For shorter values, show first 2 and last 2 characters
        elif len(value) > 8:
            masked_middle = '*' * (len(value) - 4)
            return f"{value[:2]}{masked_middle}{value[-2:]}"
        
        # For short values, mask most of it but preserve some structure
        else:
            return f"{value[0]}{'*' * (len(value) - 2)}{value[-1]}"
    
    def analyze_file(self, file_path: Path) -> None:
        """Analyze a single file for hardcoded values."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Skip binary files and very large files
            if len(content) > 1024 * 1024:  # 1MB limit
                return
            
            for category, patterns in self.patterns.items():
                for pattern in patterns:
                    matches = re.finditer(pattern, content, re.IGNORECASE)
                    
                    for match in matches:
                        value = match.group(0)
                        
                        # Skip if should be ignored
                        if self.should_ignore_value(category, value):
                            continue
                        
                        # Get line number
                        line_number = content[:match.start()].count('\n') + 1
                        
                        # Get surrounding context
                        lines = content.split('\n')
                        context_start = max(0, line_number - 2)
                        context_end = min(len(lines), line_number + 1)
                        context = lines[context_start:context_end]
                        
                        # Mask sensitive values for security
                        masked_value = self.mask_sensitive_value(category, value)
                        
                        self.hardcoded_values[category].append({
                            "file": str(file_path.relative_to(self.project_root)),
                            "line": line_number,
                            "value": masked_value,
                            "original_length": len(value),
                            "context": context,
                            "pattern": pattern
                        })
                        
        except (UnicodeDecodeError, PermissionError, OSError):
            pass
    
    def find_files_to_analyze(self) -> List[Path]:
        """Find files to analyze for hardcoded values."""
        extensions = {'.py', '.js', '.ts', '.yml', '.yaml', '.json', '.env', '.conf', '.cfg', '.ini'}
        exclude_dirs = {'.git', '__pycache__', '.pytest_cache', 'node_modules', '.venv', 'venv', 'build', 'dist'}
        
        files = []
        for file_path in self.project_root.rglob("*"):
            if not file_path.is_file():
                continue
            
            # Skip excluded directories
            if any(excluded in file_path.parts for excluded in exclude_dirs):
                continue
            
            # Include files with relevant extensions
            if file_path.suffix.lower() in extensions:
                files.append(file_path)
            
            # Include files without extensions that might be config files
            elif not file_path.suffix and file_path.name.lower() in {
                'dockerfile', 'makefile', 'readme', 'license', 'changelog'
            }:
                files.append(file_path)
        
        return files
    
    def analyze_project(self) -> None:
        """Analyze the entire project for hardcoded values."""
        print("🔍 Finding files to analyze...")
        files = self.find_files_to_analyze()
        print(f"📁 Found {len(files)} files to analyze")
        
        print("🔍 Analyzing files for hardcoded values...")
        for file_path in files:
            self.analyze_file(file_path)
    
    def get_statistics(self) -> Dict[str, int]:
        """Get statistics about found hardcoded values."""
        stats = {}
        for category, values in self.hardcoded_values.items():
            stats[category] = len(values)
        return stats
    
    def generate_report(self) -> str:
        """Generate a comprehensive report of hardcoded values."""
        report = []
        report.append("# Hardcoded Values Analysis Report")
        report.append(f"Generated on: {os.popen('date').read().strip()}")
        report.append("")
        
        # Summary
        stats = self.get_statistics()
        total_issues = sum(stats.values())
        
        report.append("## Summary")
        report.append(f"- **Total hardcoded values found**: {total_issues}")
        report.append("")
        
        for category, count in stats.items():
            if count > 0:
                report.append(f"- **{category.replace('_', ' ').title()}**: {count}")
        report.append("")
        
        # Detailed findings
        for category, values in self.hardcoded_values.items():
            if not values:
                continue
            
            report.append(f"## {category.replace('_', ' ').title()}")
            report.append("")
            
            # Group by file
            files_dict = {}
            for item in values:
                file_path = item["file"]
                if file_path not in files_dict:
                    files_dict[file_path] = []
                files_dict[file_path].append(item)
            
            for file_path, items in sorted(files_dict.items()):
                report.append(f"### {file_path}")
                report.append("")
                
                for item in items:
                    # Show masked value with original length info for sensitive categories
                    value_display = item['value']
                    if 'original_length' in item and item['original_length'] != len(item['value']):
                        value_display = f"{item['value']} (original length: {item['original_length']})"
                    
                    report.append(f"**Line {item['line']}**: `{value_display}`")
                    report.append("")
                    report.append("```")
                    for i, context_line in enumerate(item['context']):
                        line_num = item['line'] - len(item['context']) + i + 1
                        marker = ">>> " if line_num == item['line'] else "    "
                        report.append(f"{marker}{context_line}")
                    report.append("```")
                    report.append("")
        
        # Recommendations
        report.append("## Recommendations")
        report.append("")
        
        if stats.get("urls", 0) > 0:
            report.append("### URLs")
            report.append("- Move hardcoded URLs to environment variables")
            report.append("- Use centralized configuration in `shared/config/env_constants.py`")
            report.append("- Consider using service discovery for internal services")
            report.append("")
        
        if stats.get("api_keys", 0) > 0 or stats.get("secrets", 0) > 0:
            report.append("### API Keys and Secrets")
            report.append("- **CRITICAL**: Never commit API keys or secrets to version control")
            report.append("- Use environment variables or secret management systems")
            report.append("- Consider using HashiCorp Vault or similar solutions")
            report.append("- Rotate any exposed keys immediately")
            report.append("")
        
        if stats.get("passwords", 0) > 0:
            report.append("### Passwords")
            report.append("- **CRITICAL**: Remove hardcoded passwords immediately")
            report.append("- Use environment variables for database passwords")
            report.append("- Implement proper password hashing for user passwords")
            report.append("- Use secure password generation for system accounts")
            report.append("")
        
        if stats.get("database_connections", 0) > 0:
            report.append("### Database Connections")
            report.append("- Move connection strings to environment variables")
            report.append("- Use connection pooling and proper credential management")
            report.append("- Consider using database connection libraries that support env vars")
            report.append("")
        
        if stats.get("ip_addresses", 0) > 0:
            report.append("### IP Addresses")
            report.append("- Replace hardcoded IPs with hostnames when possible")
            report.append("- Use environment variables for configurable IPs")
            report.append("- Consider using service discovery for dynamic IPs")
            report.append("")
        
        if stats.get("ports", 0) > 0:
            report.append("### Port Numbers")
            report.append("- Move port configurations to environment variables")
            report.append("- Use standard ports when possible")
            report.append("- Document port usage and conflicts")
            report.append("")
        
        if stats.get("file_paths", 0) > 0:
            report.append("### File Paths")
            report.append("- Use relative paths when possible")
            report.append("- Make file paths configurable via environment variables")
            report.append("- Use proper path joining methods (os.path.join, pathlib)")
            report.append("")
        
        if stats.get("email_addresses", 0) > 0:
            report.append("### Email Addresses")
            report.append("- Move email configurations to environment variables")
            report.append("- Use proper email validation")
            report.append("- Consider using email templates and configuration")
            report.append("")
        
        # Security considerations
        report.append("## Security Considerations")
        report.append("")
        report.append("1. **Immediate Actions Required**:")
        
        critical_categories = ["api_keys", "passwords", "secrets"]
        critical_found = any(stats.get(cat, 0) > 0 for cat in critical_categories)
        
        if critical_found:
            report.append("   - 🚨 **CRITICAL**: Rotate any exposed API keys, passwords, or secrets")
            report.append("   - Review git history for exposed credentials")
            report.append("   - Implement secret scanning in CI/CD pipeline")
        else:
            report.append("   - ✅ No critical security issues found")
        
        report.append("")
        report.append("2. **Best Practices**:")
        report.append("   - Use environment variables for all configuration")
        report.append("   - Implement proper secret management")
        report.append("   - Add pre-commit hooks to prevent credential commits")
        report.append("   - Regular security audits and scanning")
        report.append("")
        
        return "\n".join(report)
    
    def run_analysis(self, check_only: bool = False) -> bool:
        """Run the complete hardcoded values analysis."""
        print("🚀 Starting hardcoded values analysis...")
        print("=" * 60)
        
        self.analyze_project()
        
        stats = self.get_statistics()
        total_issues = sum(stats.values())
        
        # Check for critical security issues
        critical_categories = ["api_keys", "passwords", "secrets"]
        critical_issues = sum(stats.get(cat, 0) for cat in critical_categories)
        
        if check_only:
            if critical_issues > 0:
                print(f"🚨 CRITICAL: Found {critical_issues} potential security issues")
                return False
            elif total_issues > 0:
                print(f"⚠️  Found {total_issues} hardcoded values that should be configurable")
                return False
            else:
                print("✅ No hardcoded values found")
                return True
        
        # Generate and save report
        report = self.generate_report()
        report_file = self.project_root / "hardcoded_values_report.md"
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        
        print(f"📊 Hardcoded values report saved to: {report_file}")
        print("=" * 60)
        print("✅ Hardcoded values analysis completed!")
        
        # Print summary
        print(f"\n📈 Summary:")
        print(f"   - Total issues: {total_issues}")
        if critical_issues > 0:
            print(f"   - 🚨 Critical security issues: {critical_issues}")
        
        for category, count in stats.items():
            if count > 0:
                print(f"   - {category.replace('_', ' ').title()}: {count}")
        
        return critical_issues == 0


def main():
    """Main function to run the hardcoded values analysis."""
    parser = argparse.ArgumentParser(description="Analyze hardcoded values in the project")
    parser.add_argument(
        "--project-root",
        default=".",
        help="Path to project root directory"
    )
    parser.add_argument(
        "--check-only",
        action="store_true",
        help="Only check for issues, don't generate report"
    )
    parser.add_argument(
        "--critical-only",
        action="store_true",
        help="Only report critical security issues"
    )
    
    args = parser.parse_args()
    
    analyzer = HardcodedValuesAnalyzer(args.project_root)
    success = analyzer.run_analysis(args.check_only)
    
    if args.check_only:
        exit_code = 0 if success else 1
        if args.critical_only:
            # Only fail on critical security issues
            stats = analyzer.get_statistics()
            critical_issues = sum(stats.get(cat, 0) for cat in ["api_keys", "passwords", "secrets"])
            exit_code = 0 if critical_issues == 0 else 1
        
        exit(exit_code)


if __name__ == "__main__":
    main()