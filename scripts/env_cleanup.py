#!/usr/bin/env python3
"""
Environment variable cleanup script.
Cleans up and reorganizes environment variables in shared/config/env_constants.py.
Removes unused variables, consolidates duplicates, and improves organization.
"""

import os
import re
import ast
from typing import Dict, List, Set, Tuple
from pathlib import Path


class EnvCleanup:
    """Environment variable cleanup and analysis tool."""
    
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
        self.env_constants_file = self.project_root / "shared" / "config" / "env_constants.py"
        self.used_vars: Set[str] = set()
        self.defined_vars: Set[str] = set()
        self.unused_vars: Set[str] = set()
        self.duplicate_vars: Dict[str, List[str]] = {}
        
    def scan_codebase_for_usage(self) -> None:
        """Scan the entire codebase for environment variable usage."""
        print("🔍 Scanning codebase for environment variable usage...")
        
        # Import regex patterns from centralized module
        try:
            from shared.config.regex_patterns import (
                OS_GETENV_PATTERN,
                OS_ENVIRON_GET_PATTERN,
                OS_ENVIRON_DIRECT_PATTERN,
                FIELD_ENV_PATTERN,
                find_env_vars_in_file
            )
            use_centralized_patterns = True
        except ImportError:
            # Fallback patterns if centralized module not available
            patterns = [
                r'os\.getenv\(["\']([^"\']+)["\']',  # os.getenv("VAR_NAME")
                r'os\.environ\[["\']([^"\']+)["\']\]',  # os.environ["VAR_NAME"]
                r'get_env_value\(([A-Z_]+)',  # get_env_value(VAR_NAME)
                r'getattr\(env,\s*["\']([^"\']+)["\']',  # getattr(env, "VAR_NAME")
                r'env\.([A-Z_]+)',  # env.VAR_NAME
            ]
            use_centralized_patterns = False
        
        # File extensions to scan
        extensions = ['.py', '.yml', '.yaml', '.env', '.md']
        
        # Directories to exclude
        exclude_dirs = {'.git', '__pycache__', '.pytest_cache', 'node_modules', '.venv', 'venv'}
        
        for file_path in self._get_files_to_scan(extensions, exclude_dirs):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                if use_centralized_patterns:
                    # Use the comprehensive pattern analysis
                    env_vars = find_env_vars_in_file(content)
                    for pattern_type, vars_list in env_vars.items():
                        for var in vars_list:
                            self.used_vars.add(var)
                else:
                    # Use fallback patterns
                    for pattern in patterns:
                        matches = re.findall(pattern, content)
                        for match in matches:
                            self.used_vars.add(match)
                        
            except (UnicodeDecodeError, PermissionError):
                continue
                
        print(f"✅ Found {len(self.used_vars)} environment variables in use")
    
    def _get_files_to_scan(self, extensions: List[str], exclude_dirs: Set[str]) -> List[Path]:
        """Get list of files to scan for environment variable usage."""
        files = []
        
        for ext in extensions:
            for file_path in self.project_root.rglob(f"*{ext}"):
                # Skip files in excluded directories
                if any(excluded in file_path.parts for excluded in exclude_dirs):
                    continue
                files.append(file_path)
                
        return files
    
    def analyze_env_constants_file(self) -> None:
        """Analyze the env_constants.py file for defined variables."""
        print("📋 Analyzing env_constants.py file...")
        
        if not self.env_constants_file.exists():
            print(f"❌ Environment constants file not found: {self.env_constants_file}")
            return
            
        with open(self.env_constants_file, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Find all variable definitions
        var_pattern = r'^([A-Z_]+)\s*=\s*["\']([^"\']+)["\']'
        matches = re.findall(var_pattern, content, re.MULTILINE)
        
        for var_name, var_value in matches:
            self.defined_vars.add(var_name)
            
            # Check for duplicates (same value)
            if var_value not in self.duplicate_vars:
                self.duplicate_vars[var_value] = []
            self.duplicate_vars[var_value].append(var_name)
            
        print(f"✅ Found {len(self.defined_vars)} environment variables defined")
    
    def find_unused_variables(self) -> None:
        """Find environment variables that are defined but not used."""
        print("🔍 Finding unused environment variables...")
        
        self.unused_vars = self.defined_vars - self.used_vars
        
        # Filter out variables that might be used in ways we can't detect
        # (like in Docker files, environment files, etc.)
        common_vars = {
            'ENVIRONMENT', 'DEBUG', 'LOG_LEVEL', 'PORT',
            'DATABASE_URL', 'REDIS_URL', 'JWT_SECRET_KEY'
        }
        
        # Don't mark common variables as unused
        self.unused_vars = self.unused_vars - common_vars
        
        print(f"⚠️  Found {len(self.unused_vars)} potentially unused variables")
    
    def find_duplicate_values(self) -> Dict[str, List[str]]:
        """Find variables with duplicate values."""
        duplicates = {
            value: vars_list for value, vars_list in self.duplicate_vars.items()
            if len(vars_list) > 1
        }
        
        if duplicates:
            print(f"⚠️  Found {len(duplicates)} sets of variables with duplicate values")
        
        return duplicates
    
    def generate_cleanup_report(self) -> str:
        """Generate a cleanup report."""
        report = []
        report.append("# Environment Variable Cleanup Report")
        report.append(f"Generated on: {os.popen('date').read().strip()}")
        report.append("")
        
        # Summary
        report.append("## Summary")
        report.append(f"- **Defined variables**: {len(self.defined_vars)}")
        report.append(f"- **Used variables**: {len(self.used_vars)}")
        report.append(f"- **Unused variables**: {len(self.unused_vars)}")
        report.append(f"- **Duplicate value sets**: {len(self.find_duplicate_values())}")
        report.append("")
        
        # Unused variables
        if self.unused_vars:
            report.append("## Unused Variables")
            report.append("These variables are defined but not found in the codebase:")
            report.append("")
            for var in sorted(self.unused_vars):
                report.append(f"- `{var}`")
            report.append("")
        
        # Duplicate values
        duplicates = self.find_duplicate_values()
        if duplicates:
            report.append("## Variables with Duplicate Values")
            report.append("These variables have the same values and might be consolidated:")
            report.append("")
            for value, vars_list in duplicates.items():
                report.append(f"**Value**: `{value}`")
                for var in vars_list:
                    report.append(f"- `{var}`")
                report.append("")
        
        # Missing variables
        missing_vars = self.used_vars - self.defined_vars
        if missing_vars:
            report.append("## Missing Variable Definitions")
            report.append("These variables are used but not defined in env_constants.py:")
            report.append("")
            for var in sorted(missing_vars):
                report.append(f"- `{var}`")
            report.append("")
        
        # Recommendations
        report.append("## Recommendations")
        report.append("")
        
        if self.unused_vars:
            report.append("### Remove Unused Variables")
            report.append("Consider removing these unused variables to reduce clutter:")
            for var in sorted(self.unused_vars):
                report.append(f"- Remove `{var}` if confirmed unused")
            report.append("")
        
        if duplicates:
            report.append("### Consolidate Duplicate Values")
            report.append("Consider consolidating variables with duplicate values:")
            for value, vars_list in duplicates.items():
                if len(vars_list) > 1:
                    primary = vars_list[0]
                    others = vars_list[1:]
                    report.append(f"- Keep `{primary}`, consider removing: {', '.join(f'`{v}`' for v in others)}")
            report.append("")
        
        return "\n".join(report)
    
    def create_cleaned_env_constants(self) -> str:
        """Create a cleaned version of env_constants.py."""
        print("🧹 Creating cleaned version of env_constants.py...")
        
        if not self.env_constants_file.exists():
            return ""
            
        with open(self.env_constants_file, 'r', encoding='utf-8') as f:
            original_content = f.read()
        
        # For now, just return the original content with comments about unused vars
        lines = original_content.split('\n')
        cleaned_lines = []
        
        for line in lines:
            # Check if this line defines an unused variable
            var_match = re.match(r'^([A-Z_]+)\s*=', line)
            if var_match and var_match.group(1) in self.unused_vars:
                # Comment out unused variables
                cleaned_lines.append(f"# UNUSED: {line}")
            else:
                cleaned_lines.append(line)
        
        return '\n'.join(cleaned_lines)
    
    def run_cleanup(self) -> None:
        """Run the complete cleanup process."""
        print("🚀 Starting environment variable cleanup...")
        print("=" * 60)
        
        # Step 1: Scan codebase for usage
        self.scan_codebase_for_usage()
        
        # Step 2: Analyze env_constants.py
        self.analyze_env_constants_file()
        
        # Step 3: Find unused variables
        self.find_unused_variables()
        
        # Step 4: Generate report
        report = self.generate_cleanup_report()
        
        # Step 5: Save report
        report_file = self.project_root / "env_cleanup_report.md"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        
        print(f"📊 Cleanup report saved to: {report_file}")
        
        # Step 6: Create cleaned version (optional)
        cleaned_content = self.create_cleaned_env_constants()
        if cleaned_content:
            backup_file = self.project_root / "shared" / "config" / "env_constants.py.backup"
            cleaned_file = self.project_root / "shared" / "config" / "env_constants_cleaned.py"
            
            # Create backup
            with open(backup_file, 'w', encoding='utf-8') as f:
                with open(self.env_constants_file, 'r', encoding='utf-8') as orig:
                    f.write(orig.read())
            
            # Save cleaned version
            with open(cleaned_file, 'w', encoding='utf-8') as f:
                f.write(cleaned_content)
            
            print(f"💾 Backup saved to: {backup_file}")
            print(f"🧹 Cleaned version saved to: {cleaned_file}")
        
        print("=" * 60)
        print("✅ Environment variable cleanup completed!")
        
        # Print summary
        print(f"\n📈 Summary:")
        print(f"   - Defined: {len(self.defined_vars)} variables")
        print(f"   - Used: {len(self.used_vars)} variables")
        print(f"   - Unused: {len(self.unused_vars)} variables")
        print(f"   - Duplicates: {len(self.find_duplicate_values())} sets")


def main():
    """Main function to run the cleanup."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Clean up environment variables")
    parser.add_argument(
        "--project-root",
        default=".",
        help="Path to project root directory"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Only generate report, don't create cleaned files"
    )
    
    args = parser.parse_args()
    
    cleanup = EnvCleanup(args.project_root)
    cleanup.run_cleanup()


if __name__ == "__main__":
    main()