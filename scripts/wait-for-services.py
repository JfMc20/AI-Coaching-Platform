#!/usr/bin/env python3
"""
Wait-for script to ensure dependent services are ready before starting application.
This replaces Docker Compose health check conditions which are not reliable.
"""

import sys
import time
import urllib.request
import urllib.error
import socket
import argparse
import logging
from typing import List, Dict, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ServiceWaiter:
    """Utility class to wait for services to become available"""
    
    def __init__(self, timeout: int = 300, interval: int = 5):
        """
        Initialize service waiter
        
        Args:
            timeout: Maximum time to wait in seconds (default: 5 minutes)
            interval: Check interval in seconds (default: 5 seconds)
        """
        self.timeout = timeout
        self.interval = interval
    
    def check_tcp_port(self, host: str, port: int, timeout: int = 5) -> bool:
        """
        Check if a TCP port is open and accepting connections
        
        Args:
            host: Hostname or IP address
            port: Port number
            timeout: Connection timeout in seconds
            
        Returns:
            True if port is open, False otherwise
        """
        try:
            with socket.create_connection((host, port), timeout=timeout):
                return True
        except (socket.error, OSError) as e:
            logger.debug(f"TCP check failed for {host}:{port}: {e}")
            return False
    
    def check_service(self, url: str, expected_status: int = 200) -> bool:
        """
        Check if a service is available and healthy
        
        Args:
            url: Service health check URL or tcp://host:port for TCP checks
            expected_status: Expected HTTP status code
            
        Returns:
            True if service is healthy, False otherwise
        """
        # Handle TCP port checks
        if url.startswith('tcp://'):
            tcp_url = url[6:]  # Remove 'tcp://' prefix
            if ':' in tcp_url:
                host, port_str = tcp_url.rsplit(':', 1)
                try:
                    port = int(port_str)
                    return self.check_tcp_port(host, port)
                except ValueError:
                    logger.error(f"Invalid port in TCP URL: {url}")
                    return False
            else:
                logger.error(f"Invalid TCP URL format: {url}")
                return False
        
        # Handle HTTP/HTTPS checks
        try:
            with urllib.request.urlopen(url, timeout=10) as response:
                return response.getcode() == expected_status
        except (urllib.error.URLError, urllib.error.HTTPError, OSError) as e:
            logger.debug(f"Service check failed for {url}: {e}")
            return False
    
    def wait_for_service(self, name: str, url: str, expected_status: int = 200) -> bool:
        """
        Wait for a single service to become available
        
        Args:
            name: Service name for logging
            url: Service health check URL or tcp://host:port for TCP checks
            expected_status: Expected HTTP status code
            
        Returns:
            True if service becomes available, False if timeout
        """
        check_type = "TCP port" if url.startswith('tcp://') else "HTTP endpoint"
        logger.info(f"Waiting for {name} ({check_type}) at {url}")
        
        start_time = time.time()
        while time.time() - start_time < self.timeout:
            if self.check_service(url, expected_status):
                logger.info(f"OK {name} is ready")
                return True
            
            logger.debug(f"WAITING {name} not ready yet, retrying in {self.interval}s...")
            time.sleep(self.interval)
        
        logger.error(f"ERROR Timeout waiting for {name} after {self.timeout}s")
        return False
    
    def wait_for_services(self, services: List[Dict[str, str]]) -> bool:
        """
        Wait for multiple services to become available
        
        Args:
            services: List of service configurations with 'name' and 'url' keys
            
        Returns:
            True if all services become available, False otherwise
        """
        logger.info(f"Waiting for {len(services)} services to become ready...")
        
        for service in services:
            name = service['name']
            url = service['url']
            expected_status = service.get('status', 200)
            
            if not self.wait_for_service(name, url, expected_status):
                return False
        
        logger.info("SUCCESS All services are ready!")
        return True


def parse_service_spec(spec: str) -> Dict[str, str]:
    """
    Parse service specification string
    
    Format: name:url[:status]
    Examples: 
        - postgres:http://postgres:5432/health:200
        - ollama:tcp://ollama:11434
        - redis:tcp://redis:6379
    
    Args:
        spec: Service specification string
        
    Returns:
        Dictionary with service configuration
    """
    parts = spec.split(':')
    if len(parts) < 3:  # name:protocol:host or name:protocol:host:port
        raise ValueError(f"Invalid service spec: {spec}. Expected format: name:url[:status] or name:tcp://host:port")
    
    name = parts[0]
    
    # Handle TCP format: name:tcp://host:port
    if parts[1] == 'tcp' and parts[2].startswith('//'):
        url = ':'.join(parts[1:])  # Reconstruct tcp://host:port
        status = 200  # Default status for TCP checks (not used)
    else:
        # Handle HTTP format: name:http://host:port/path[:status]
        # Reconstruct URL (may contain colons)
        url = ':'.join(parts[1:-1]) if len(parts) > 2 and parts[-1].isdigit() else ':'.join(parts[1:])
        status = int(parts[-1]) if len(parts) > 2 and parts[-1].isdigit() else 200
    
    return {
        'name': name,
        'url': url,
        'status': status
    }


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Wait for services to become available before starting application"
    )
    
    parser.add_argument(
        'services',
        nargs='+',
        help='Service specifications in format name:url[:status]'
    )
    
    parser.add_argument(
        '--timeout',
        type=int,
        default=300,
        help='Maximum time to wait in seconds (default: 300)'
    )
    
    parser.add_argument(
        '--interval',
        type=int,
        default=5,
        help='Check interval in seconds (default: 5)'
    )
    
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Parse service specifications
    try:
        service_configs = [parse_service_spec(spec) for spec in args.services]
    except ValueError as e:
        logger.error(f"Error parsing service specifications: {e}")
        sys.exit(1)
    
    # Wait for services
    waiter = ServiceWaiter(timeout=args.timeout, interval=args.interval)
    
    if waiter.wait_for_services(service_configs):
        logger.info("All services are ready. Starting application...")
        sys.exit(0)
    else:
        logger.error("Some services failed to become ready. Exiting...")
        sys.exit(1)


if __name__ == '__main__':
    main()