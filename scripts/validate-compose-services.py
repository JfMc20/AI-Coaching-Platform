#!/usr/bin/env python3
"""
Docker Compose services validation script.
Validates that required services exist in docker-compose files.
"""

import sys
import yaml
import argparse
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('logs/compose-validation.log', mode='a')
    ]
)
logger = logging.getLogger(__name__)


def load_compose_file(compose_file: str) -> dict:
    """Load and parse docker-compose file."""
    try:
        with open(compose_file, 'r') as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        logger.error(f"Docker Compose file not found: {compose_file}")
        print(f"❌ Docker Compose file not found: {compose_file}")
        return None
    except yaml.YAMLError as e:
        logger.error(f"Error parsing Docker Compose file: {e}")
        print(f"❌ Error parsing Docker Compose file: {e}")
        return None


def validate_services(compose_data: dict, required_services: list) -> bool:
    """Validate that required services exist in compose data."""
    if not compose_data or 'services' not in compose_data:
        logger.error("No services section found in Docker Compose file")
        print("❌ No services section found in Docker Compose file")
        return False
    
    available_services = set(compose_data['services'].keys())
    required_services_set = set(required_services)
    missing_services = required_services_set - available_services
    
    if missing_services:
        logger.error(f"Missing required services: {', '.join(missing_services)}")
        logger.info(f"Available services: {', '.join(sorted(available_services))}")
        print(f"❌ Missing required services: {', '.join(missing_services)}")
        print(f"📋 Available services: {', '.join(sorted(available_services))}")
        return False
    
    logger.info(f"All required services found: {', '.join(required_services)}")
    print(f"✅ All required services found: {', '.join(required_services)}")
    return True


def validate_service_health_checks(compose_data: dict, services: list) -> bool:
    """Validate that services have health checks configured."""
    issues = []
    services_cfg = compose_data.get('services', {})
    
    for service_name in services:
        if service_name not in services_cfg:
            issue = f"Service '{service_name}' is not defined in services configuration"
            issues.append(issue)
            logger.warning(issue)
            continue
            
        service_config = services_cfg.get(service_name, {})
        
        if 'healthcheck' not in service_config:
            issue = f"Service '{service_name}' has no health check configured"
            issues.append(issue)
            logger.warning(issue)
        else:
            healthcheck = service_config['healthcheck']
            if 'test' not in healthcheck:
                issue = f"Service '{service_name}' health check has no test command"
                issues.append(issue)
                logger.warning(issue)
    
    if issues:
        logger.warning(f"Health check issues found: {len(issues)} issues")
        print("⚠️  Health check issues found:")
        for issue in issues:
            print(f"   - {issue}")
        return False
    
    logger.info("All services have proper health checks")
    print("✅ All services have proper health checks")
    return True


def validate_service_dependencies(compose_data: dict, services: list) -> bool:
    """Validate service dependencies are properly configured."""
    issues = []
    services_cfg = compose_data.get('services', {})
    
    for service_name in services:
        if service_name not in services_cfg:
            issue = f"Service '{service_name}' is not defined in services configuration"
            issues.append(issue)
            logger.warning(issue)
            continue
            
        service_config = services_cfg.get(service_name, {})
        
        if 'depends_on' in service_config:
            depends_on = service_config['depends_on']
            
            # Handle both list and dict formats
            if isinstance(depends_on, dict):
                dependencies = list(depends_on.keys())
            else:
                dependencies = depends_on
            
            # Check if dependencies exist
            for dep in dependencies:
                if dep not in services_cfg:
                    issue = f"Service '{service_name}' depends on non-existent service '{dep}'"
                    issues.append(issue)
                    logger.error(issue)
    
    if issues:
        logger.error(f"Dependency issues found: {len(issues)} issues")
        print("❌ Dependency issues found:")
        for issue in issues:
            print(f"   - {issue}")
        return False
    
    logger.info("All service dependencies are valid")
    print("✅ All service dependencies are valid")
    return True


def validate_network_configuration(compose_data: dict) -> bool:
    """Validate network configuration."""
    services = compose_data.get('services', {})
    networks_defined = compose_data.get('networks', {})
    
    # Check if services reference networks that exist
    issues = []
    
    for service_name, service_config in services.items():
        if 'networks' in service_config:
            service_networks = service_config['networks']
            if isinstance(service_networks, list):
                for network in service_networks:
                    if network not in networks_defined:
                        issue = f"Service '{service_name}' references undefined network '{network}'"
                        issues.append(issue)
                        logger.error(issue)
    
    if issues:
        logger.error(f"Network configuration issues found: {len(issues)} issues")
        print("❌ Network configuration issues:")
        for issue in issues:
            print(f"   - {issue}")
        return False
    
    logger.info("Network configuration is valid")
    print("✅ Network configuration is valid")
    return True


def main():
    """Main validation function."""
    parser = argparse.ArgumentParser(description="Validate Docker Compose services")
    parser.add_argument("compose_file", help="Path to docker-compose file")
    parser.add_argument("--services", nargs="+", required=True, help="Required services to validate")
    parser.add_argument("--check-health", action="store_true", help="Check health check configuration")
    parser.add_argument("--check-deps", action="store_true", help="Check service dependencies")
    parser.add_argument("--check-networks", action="store_true", help="Check network configuration")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging")
    
    args = parser.parse_args()
    
    # Set logging level based on verbosity
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Ensure logs directory exists
    Path('logs').mkdir(exist_ok=True)
    
    logger.info(f"Starting validation of Docker Compose file: {args.compose_file}")
    logger.info(f"Required services: {', '.join(args.services)}")
    
    print(f"🔍 Validating Docker Compose file: {args.compose_file}")
    print(f"📋 Required services: {', '.join(args.services)}")
    print("=" * 60)
    
    # Load compose file
    compose_data = load_compose_file(args.compose_file)
    if not compose_data:
        logger.error("Failed to load compose file")
        return False
    
    # Run validations with error handling
    validations = []
    
    try:
        validations.append(("Service Existence", validate_services(compose_data, args.services)))
    except Exception as e:
        logger.exception(f"Service existence validation failed: {e}")
        validations.append(("Service Existence", False))
    
    if args.check_health:
        try:
            validations.append(("Health Checks", validate_service_health_checks(compose_data, args.services)))
        except Exception as e:
            logger.exception(f"Health check validation failed: {e}")
            validations.append(("Health Checks", False))
    
    if args.check_deps:
        try:
            validations.append(("Dependencies", validate_service_dependencies(compose_data, args.services)))
        except Exception as e:
            logger.exception(f"Dependency validation failed: {e}")
            validations.append(("Dependencies", False))
    
    if args.check_networks:
        try:
            validations.append(("Networks", validate_network_configuration(compose_data)))
        except Exception as e:
            logger.exception(f"Network validation failed: {e}")
            validations.append(("Networks", False))
    
    # Summary
    print("=" * 60)
    print("📊 Validation Summary:")
    
    all_passed = True
    for check_name, passed in validations:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"   {check_name}: {status}")
        logger.info(f"Validation {check_name}: {'PASSED' if passed else 'FAILED'}")
        if not passed:
            all_passed = False
    
    if all_passed:
        logger.info("All validations passed successfully")
        print("🎉 All validations passed!")
        return True
    else:
        logger.error("Some validations failed")
        print("❌ Some validations failed!")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)