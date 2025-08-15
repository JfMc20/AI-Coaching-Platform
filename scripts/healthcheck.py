#!/usr/bin/env python3
"""
Health check script for Docker containers.
This script performs a basic HTTP health check on the service.
"""

import sys
import urllib.request
import urllib.error
import json
import logging
import os

# Configure logging
logging.basicConfig(
    level=logging.WARNING,  # Reduced logging for health checks
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def check_health(url: str, timeout: int = 5) -> bool:
    """
    Perform HTTP health check.
    
    Args:
        url: Health check URL
        timeout: Request timeout in seconds
        
    Returns:
        True if health check passes
    """
    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:
            if response.status == 200:
                # Try to parse JSON response
                try:
                    data = json.loads(response.read().decode('utf-8'))
                    status = data.get('status', '').lower()
                    
                    if status in ['healthy', 'ok', 'ready']:
                        return True
                    else:
                        logger.warning(f"Unhealthy status: {status}")
                        return False
                        
                except json.JSONDecodeError:
                    # If not JSON, assume 200 status means healthy
                    return True
            else:
                logger.warning(f"HTTP {response.status} from {url}")
                return False
                
    except urllib.error.URLError as e:
        logger.warning(f"Health check failed: {e}")
        return False
    except Exception as e:
        logger.warning(f"Unexpected error during health check: {e}")
        return False


def main():
    """Main health check function."""
    # Get port from environment or use default
    port = os.getenv('PORT', '8001')
    
    # Health check URL
    health_url = f"http://localhost:{port}/health"
    
    # Perform health check
    if check_health(health_url):
        logger.debug(f"Health check passed for {health_url}")
        sys.exit(0)
    else:
        logger.error(f"Health check failed for {health_url}")
        sys.exit(1)


if __name__ == "__main__":
    main()