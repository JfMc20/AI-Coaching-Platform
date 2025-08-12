#!/usr/bin/env python3
"""
Dedicated health check script for Docker containers.
Provides robust health checking with proper error handling and logging.
"""

import os
import sys
import urllib.request
import urllib.error
from typing import Optional


def get_health_check_url() -> str:
    """Get health check URL from environment variables"""
    port = os.environ.get('PORT', '8000')
    host = os.environ.get('HEALTH_CHECK_HOST', 'localhost')
    path = os.environ.get('HEALTH_CHECK_PATH', '/health')
    
    return f"http://{host}:{port}{path}"


def perform_health_check(url: str, timeout: int = 5) -> bool:
    """
    Perform health check HTTP request
    
    Args:
        url: Health check endpoint URL
        timeout: Request timeout in seconds
        
    Returns:
        True if health check passes (2xx response), False otherwise
    """
    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:
            status_code = response.getcode()
            
            # Accept any 2xx status code as healthy
            if 200 <= status_code < 300:
                return True
            else:
                print(f"Health check failed: HTTP {status_code}", file=sys.stderr)
                return False
                
    except urllib.error.HTTPError as e:
        print(f"Health check failed: HTTP {e.code} - {e.reason}", file=sys.stderr)
        return False
        
    except urllib.error.URLError as e:
        print(f"Health check failed: Connection error - {e.reason}", file=sys.stderr)
        return False
        
    except Exception as e:
        print(f"Health check failed: Unexpected error - {e}", file=sys.stderr)
        return False


def main() -> None:
    """Main health check entry point"""
    try:
        url = get_health_check_url()
        
        # Perform health check
        if perform_health_check(url):
            print(f"Health check passed: {url}")
            sys.exit(0)
        else:
            print(f"Health check failed: {url}", file=sys.stderr)
            sys.exit(1)
            
    except Exception as e:
        print(f"Health check script error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()