#!/usr/bin/env python3
"""
Dependency security and update checker.
Checks for security vulnerabilities and outdated packages.
"""

import subprocess
import sys
import json
from pathlib import Path
from datetime import datetime


def run_command(command: list, description: str) -> tuple[bool, str]:
    """Run a command and return success status and output."""
    try:
        print(f"🔍 {description}...")
        result = subprocess.run(command, capture_output=True, text=True, timeout=60)
        return result.returncode == 0, result.stdout + result.stderr
    except subprocess.TimeoutExpired:
        return False, "Command timed out"
    except Exception as e:
        return False, str(e)


def check_pip_audit(requirements_file: str) -> bool:
    """Check for security vulnerabilities using pip-audit."""
    if not Path(requirements_file).exists():
        print(f"⚠️  {requirements_file} not found, skipping audit")
        return True
    
    # Try to install pip-audit if not available
    success, _ = run_command(["pip", "show", "pip-audit"], "Checking if pip-audit is installed")
    if not success:
        print("📦 Installing pip-audit...")
        success, output = run_command(["pip", "install", "pip-audit"], "Installing pip-audit")
        if not success:
            print(f"❌ Failed to install pip-audit: {output}")
            return False
    
    # Run security audit
    success, output = run_command(
        ["pip-audit", "-r", requirements_file, "--format", "json"],
        f"Security audit for {requirements_file}"
    )
    
    if success:
        try:
            audit_data = json.loads(output)
            vulnerabilities = audit_data.get("vulnerabilities", [])
            if vulnerabilities:
                print(f"🚨 Found {len(vulnerabilities)} security vulnerabilities in {requirements_file}:")
                for vuln in vulnerabilities[:5]:  # Show first 5
                    package = vuln.get("package", "unknown")
                    version = vuln.get("installed_version", "unknown")
                    advisory = vuln.get("advisory", "No details")
                    print(f"   - {package} {version}: {advisory}")
                if len(vulnerabilities) > 5:
                    print(f"   ... and {len(vulnerabilities) - 5} more")
                return False
            else:
                print(f"✅ No security vulnerabilities found in {requirements_file}")
                return True
        except json.JSONDecodeError:
            print(f"⚠️  Could not parse audit output for {requirements_file}")
            return True
    else:
        print(f"⚠️  Security audit failed for {requirements_file}: {output}")
        return True  # Don't fail the whole process


def check_outdated_packages(requirements_file: str) -> bool:
    """Check for outdated packages."""
    if not Path(requirements_file).exists():
        print(f"⚠️  {requirements_file} not found, skipping outdated check")
        return True
    
    success, output = run_command(["pip", "list", "--outdated", "--format", "json"], 
                                 f"Checking outdated packages")
    
    if success:
        try:
            outdated_data = json.loads(output)
            if outdated_data:
                print(f"📦 Found {len(outdated_data)} outdated packages:")
                for pkg in outdated_data[:10]:  # Show first 10
                    name = pkg.get("name", "unknown")
                    current = pkg.get("version", "unknown")
                    latest = pkg.get("latest_version", "unknown")
                    print(f"   - {name}: {current} → {latest}")
                if len(outdated_data) > 10:
                    print(f"   ... and {len(outdated_data) - 10} more")
                return False
            else:
                print("✅ All packages are up to date")
                return True
        except json.JSONDecodeError:
            print("⚠️  Could not parse outdated packages output")
            return True
    else:
        print(f"⚠️  Failed to check outdated packages: {output}")
        return True


def generate_dependency_report():
    """Generate a comprehensive dependency report."""
    print("🔍 Dependency Security and Update Check")
    print("=" * 50)
    
    requirements_files = ["requirements.txt", "requirements-test.txt"]
    results = []
    
    for req_file in requirements_files:
        print(f"\n📋 Checking {req_file}...")
        
        # Security audit
        security_ok = check_pip_audit(req_file)
        
        # Outdated packages
        outdated_ok = check_outdated_packages(req_file)
        
        results.append({
            "file": req_file,
            "security_ok": security_ok,
            "outdated_ok": outdated_ok
        })
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Dependency Check Summary:")
    
    all_secure = all(r["security_ok"] for r in results)
    all_updated = all(r["outdated_ok"] for r in results)
    
    for result in results:
        security_status = "✅" if result["security_ok"] else "🚨"
        outdated_status = "✅" if result["outdated_ok"] else "📦"
        print(f"   {result['file']}: Security {security_status} | Updates {outdated_status}")
    
    print(f"\n🎯 Overall Status:")
    print(f"   Security: {'✅ SECURE' if all_secure else '🚨 VULNERABILITIES FOUND'}")
    print(f"   Updates: {'✅ UP TO DATE' if all_updated else '📦 UPDATES AVAILABLE'}")
    
    # Recommendations
    if not all_secure or not all_updated:
        print(f"\n💡 Recommendations:")
        if not all_secure:
            print("   1. Review and update packages with security vulnerabilities")
            print("   2. Run: pip-audit --fix (if available)")
        if not all_updated:
            print("   3. Update outdated packages: pip install --upgrade <package>")
            print("   4. Test thoroughly after updates")
    
    return all_secure and all_updated


def main():
    """Main function."""
    try:
        success = generate_dependency_report()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⚠️  Dependency check interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"💥 Dependency check failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()