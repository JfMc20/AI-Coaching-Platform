#!/usr/bin/env python3
"""
Wait for services to be available before starting the application.
This script waits for database and Redis connections to be ready.
"""

import sys
import time
import socket
import logging
import argparse
from typing import Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def parse_service_url(service_url: str) -> Tuple[str, str, int]:
    """
    Parse service URL in format: name:tcp://host:port
    
    Args:
        service_url: Service URL string
        
    Returns:
        Tuple of (name, host, port)
    """
    try:
        if ":" not in service_url:
            raise ValueError(f"Invalid service URL format: {service_url}")
        
        name, url_part = service_url.split(":", 1)
        
        if not url_part.startswith("tcp://"):
            raise ValueError(f"Only TCP connections supported: {service_url}")
        
        url_part = url_part[6:]  # Remove 'tcp://'
        
        if ":" not in url_part:
            raise ValueError(f"Port not specified: {service_url}")
        
        host, port_str = url_part.split(":", 1)
        port = int(port_str)
        
        return name, host, port
        
    except (ValueError, IndexError) as e:
        logger.error(f"Failed to parse service URL '{service_url}': {e}")
        sys.exit(1)


def check_tcp_connection(host: str, port: int, timeout: float = 5.0) -> bool:
    """
    Check if TCP connection to host:port is available.
    
    Args:
        host: Target hostname
        port: Target port
        timeout: Connection timeout in seconds
        
    Returns:
        True if connection successful
    """
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except Exception as e:
        logger.debug(f"Connection check failed for {host}:{port}: {e}")
        return False


def wait_for_service(name: str, host: str, port: int, timeout: int = 60, verbose: bool = False) -> bool:
    """
    Wait for a service to become available.
    
    Args:
        name: Service name for logging
        host: Target hostname
        port: Target port
        timeout: Maximum time to wait in seconds
        verbose: Enable verbose logging
        
    Returns:
        True if service becomes available within timeout
    """
    start_time = time.time()
    
    if verbose:
        logger.info(f"Waiting for {name} at {host}:{port} (timeout: {timeout}s)")
    
    while True:
        if check_tcp_connection(host, port):
            elapsed = time.time() - start_time
            logger.info(f"✅ {name} is ready at {host}:{port} (took {elapsed:.1f}s)")
            return True
        
        elapsed = time.time() - start_time
        if elapsed >= timeout:
            logger.error(f"❌ Timeout waiting for {name} at {host}:{port} after {timeout}s")
            return False
        
        if verbose:
            logger.debug(f"⏳ {name} not ready yet... ({elapsed:.1f}s elapsed)")
        
        time.sleep(1)


def main():
    """Main function to wait for multiple services."""
    parser = argparse.ArgumentParser(
        description="Wait for services to be available",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python wait-for-services.py postgres:tcp://postgres:5432 redis:tcp://redis:6379
  python wait-for-services.py --timeout 120 --verbose db:tcp://localhost:5432
        """
    )
    
    parser.add_argument(
        "services",
        nargs="+",
        help="Services to wait for in format 'name:tcp://host:port'"
    )
    
    parser.add_argument(
        "--timeout",
        type=int,
        default=60,
        help="Timeout in seconds for each service (default: 60)"
    )
    
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    logger.info(f"🚀 Waiting for {len(args.services)} service(s) to be ready...")
    
    all_ready = True
    
    for service_url in args.services:
        name, host, port = parse_service_url(service_url)
        
        if not wait_for_service(name, host, port, args.timeout, args.verbose):
            all_ready = False
            # Continue checking other services instead of exiting immediately
    
    if all_ready:
        logger.info("🎉 All services are ready!")
        sys.exit(0)
    else:
        logger.error("❌ Some services failed to become ready")
        sys.exit(1)


if __name__ == "__main__":
    main()