"""Common validation functions"""

import re
from urllib.parse import urlparse


def validate_email(email: str) -> bool:
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def validate_url(url: str) -> bool:
    """Validate URL format"""
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except Exception:
        return False


def validate_domain(domain: str) -> bool:
    """Validate domain format"""
    if not domain or len(domain) > 253:
        return False
    
    # Remove protocol if present
    if domain.startswith(('http://', 'https://')):
        domain = urlparse(domain).netloc
    
    # Basic domain pattern
    pattern = r'^[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$'
    return bool(re.match(pattern, domain))


def validate_hex_color(color: str) -> bool:
    """Validate hex color format"""
    if not color.startswith('#') or len(color) != 7:
        return False
    try:
        int(color[1:], 16)
        return True
    except ValueError:
        return False