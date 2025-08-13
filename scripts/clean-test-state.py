#!/usr/bin/env python3
"""
Test state cleanup script.
Ensures a clean state before running tests by cleaning up containers, volumes, and networks.
"""

import subprocess
import sys
import time
import argparse


def run_command(command: list, ignore_errors: bool = False) -> bool:
    """Run a command and return success status."""
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=not ignore_errors)
        if result.returncode != 0 and not ignore_errors:
            print(f"❌ Command failed: {' '.join(command)}")
            print(f"   Error: {result.stderr}")
            return False
        return True
    except subprocess.SubprocessError as e:
        if not ignore_errors:
            print(f"❌ Command execution failed: {e}")
        return False


def stop_test_containers(compose_file: str) -> bool:
    """Stop and remove test containers."""
    print("🛑 Stopping test containers...")
    
    # docker-compose down already removes containers and volumes, so rm command is redundant
    cmd = ["docker-compose", "-f", compose_file, "down", "-v", "--remove-orphans"]
    
    return run_command(cmd, ignore_errors=True)


def clean_test_volumes() -> bool:
    """Clean up test-related volumes."""
    print("🧹 Cleaning test volumes...")
    
    # Get list of volumes
    result = subprocess.run(["docker", "volume", "ls", "-q"], capture_output=True, text=True)
    if result.returncode != 0:
        print("⚠️  Could not list Docker volumes")
        return False
    
    volumes = result.stdout.strip().split('\n') if result.stdout.strip() else []
    test_volumes = [v for v in volumes if 'test' in v.lower()]
    
    if not test_volumes:
        print("✅ No test volumes to clean")
        return True
    
    print(f"🗑️  Removing {len(test_volumes)} test volumes...")
    for volume in test_volumes:
        run_command(["docker", "volume", "rm", volume], ignore_errors=True)
    
    return True


def clean_test_networks() -> bool:
    """Clean up test-related networks."""
    print("🌐 Cleaning test networks...")
    
    # Get list of networks
    result = subprocess.run(["docker", "network", "ls", "--format", "{{.Name}}"], capture_output=True, text=True)
    if result.returncode != 0:
        print("⚠️  Could not list Docker networks")
        return False
    
    networks = result.stdout.strip().split('\n') if result.stdout.strip() else []
    test_networks = [n for n in networks if 'test' in n.lower() and n not in ['bridge', 'host', 'none']]
    
    if not test_networks:
        print("✅ No test networks to clean")
        return True
    
    print(f"🗑️  Removing {len(test_networks)} test networks...")
    for network in test_networks:
        run_command(["docker", "network", "rm", network], ignore_errors=True)
    
    return True


def clean_dangling_resources() -> bool:
    """Clean up dangling Docker resources."""
    print("🧹 Cleaning dangling Docker resources...")
    
    commands = [
        ["docker", "system", "prune", "-f"],
        ["docker", "volume", "prune", "-f"],
        ["docker", "network", "prune", "-f"]
    ]
    
    success = True
    for cmd in commands:
        if not run_command(cmd, ignore_errors=True):
            success = False
    
    return success


def clean_test_directories() -> bool:
    """Clean up test output directories."""
    print("📁 Cleaning test directories...")
    
    import shutil
    from pathlib import Path
    
    directories_to_clean = [
        "test-results",
        "coverage",
        "htmlcov",
        ".pytest_cache",
        "logs"
    ]
    
    for dir_name in directories_to_clean:
        dir_path = Path(dir_name)
        if dir_path.exists():
            try:
                if dir_path.is_dir():
                    shutil.rmtree(dir_path)
                else:
                    dir_path.unlink()
                print(f"🗑️  Removed {dir_name}")
            except Exception as e:
                print(f"⚠️  Could not remove {dir_name}: {e}")
    
    # Recreate essential directories
    essential_dirs = ["test-results", "coverage", "logs"]
    for dir_name in essential_dirs:
        Path(dir_name).mkdir(exist_ok=True)
    
    return True


def wait_for_cleanup(seconds: int = 5) -> None:
    """Wait for cleanup operations to complete."""
    print(f"⏳ Waiting {seconds} seconds for cleanup to complete...")
    time.sleep(seconds)


def main():
    """Main cleanup function."""
    parser = argparse.ArgumentParser(description="Clean test state")
    parser.add_argument("--compose-file", default="docker-compose.test.yml", help="Docker Compose file")
    parser.add_argument("--skip-containers", action="store_true", help="Skip container cleanup")
    parser.add_argument("--skip-volumes", action="store_true", help="Skip volume cleanup")
    parser.add_argument("--skip-networks", action="store_true", help="Skip network cleanup")
    parser.add_argument("--skip-directories", action="store_true", help="Skip directory cleanup")
    parser.add_argument("--wait", type=int, default=5, help="Wait time after cleanup")
    parser.add_argument("--allow-partial", action="store_true", help="Allow partial failures without non-zero exit code")
    
    args = parser.parse_args()
    
    print("🧹 Starting test state cleanup...")
    print("=" * 50)
    
    cleanup_steps = []
    
    if not args.skip_containers:
        cleanup_steps.append(("Containers", lambda: stop_test_containers(args.compose_file)))
    
    if not args.skip_volumes:
        cleanup_steps.append(("Volumes", clean_test_volumes))
    
    if not args.skip_networks:
        cleanup_steps.append(("Networks", clean_test_networks))
    
    if not args.skip_directories:
        cleanup_steps.append(("Directories", clean_test_directories))
    
    # Always clean dangling resources
    cleanup_steps.append(("Dangling Resources", clean_dangling_resources))
    
    # Execute cleanup steps
    success_count = 0
    failed_steps = []
    
    for step_name, step_func in cleanup_steps:
        try:
            if step_func():
                print(f"✅ {step_name} cleanup: SUCCESS")
                success_count += 1
            else:
                print(f"⚠️  {step_name} cleanup: PARTIAL")
                failed_steps.append(step_name)
        except Exception as e:
            print(f"❌ {step_name} cleanup: FAILED ({e})")
            failed_steps.append(step_name)
    
    # Wait for cleanup to complete
    if args.wait > 0:
        wait_for_cleanup(args.wait)
    
    print("=" * 50)
    print(f"📊 Cleanup Summary: {success_count}/{len(cleanup_steps)} steps completed successfully")
    
    if success_count == len(cleanup_steps):
        print("🎉 Test state cleanup completed successfully!")
        return True
    else:
        if failed_steps:
            print(f"⚠️  Test state cleanup completed with failures in: {', '.join(failed_steps)}")
        else:
            print("⚠️  Test state cleanup completed with warnings")
        
        # Return False for failures unless --allow-partial is specified
        return args.allow_partial


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)