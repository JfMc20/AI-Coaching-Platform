---
inclusion: always
---

# Security Implementation Patterns

## Authentication & Authorization

### JWT Token Management
Implement comprehensive JWT token handling with RS256 algorithm:

```python
from jose import jwt, JWTError
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
import logging

logger = logging.getLogger(__name__)

class JWTManager:
    """Manages JWT token creation, validation, and rotation."""
    
    def __init__(self, private_key_path: str, public_key_path: str):
        self.algorithm = "RS256"
        self.access_token_expire_minutes = 15
        self.refresh_token_expire_days = 30
        self.issuer = "coaching-platform-auth"
        self.audience = "coaching-platform"
        
        # Load RSA keys
        self.private_key = self._load_private_key(private_key_path)
        self.public_key = self._load_public_key(public_key_path)
    
    def _load_private_key(self, key_path: str):
        """Load RSA private key for token signing."""
        try:
            with open(key_path, 'rb') as key_file:
                private_key = serialization.load_pem_private_key(
                    key_file.read(),
                    password=None  # Use environment variable in production
                )
            return private_key
        except Exception as e:
            logger.exception(f"Failed to load private key: {e}")
            raise SecurityError("Failed to load signing key")
    
    def _load_public_key(self, key_path: str):
        """Load RSA public key for token verification."""
        try:
            with open(key_path, 'rb') as key_file:
                public_key = serialization.load_pem_public_key(key_file.read())
            return public_key
        except Exception as e:
            logger.exception(f"Failed to load public key: {e}")
            raise SecurityError("Failed to load verification key")
    
    def create_access_token(
        self, 
        creator_id: str, 
        permissions: List[str],
        subscription_tier: str = "free"
    ) -> str:
        """Create JWT access token with creator claims."""
        
        now = datetime.utcnow()
        expire = now + timedelta(minutes=self.access_token_expire_minutes)
        
        claims = {
            "sub": creator_id,
            "iat": now,
            "exp": expire,
            "aud": self.audience,
            "iss": self.issuer,
            "creator_id": creator_id,
            "tenant_id": creator_id,  # For multi-tenancy
            "permissions": permissions,
            "subscription_tier": subscription_tier,
            "token_type": "access"
        }
        
        try:
            token = jwt.encode(
                claims, 
                self.private_key, 
                algorithm=self.algorithm
            )
            
            logger.info(f"Created access token for creator {creator_id}")
            return token
            
        except Exception as e:
            logger.exception(f"Failed to create access token: {e}")
            raise SecurityError("Token creation failed")
    
    def create_refresh_token(self, creator_id: str) -> str:
        """Create JWT refresh token for token renewal."""
        
        now = datetime.utcnow()
        expire = now + timedelta(days=self.refresh_token_expire_days)
        
        claims = {
            "sub": creator_id,
            "iat": now,
            "exp": expire,
            "aud": self.audience,
            "iss": self.issuer,
            "creator_id": creator_id,
            "token_type": "refresh"
        }
        
        try:
            token = jwt.encode(
                claims,
                self.private_key,
                algorithm=self.algorithm
            )
            
            logger.info(f"Created refresh token for creator {creator_id}")
            return token
            
        except Exception as e:
            logger.exception(f"Failed to create refresh token: {e}")
            raise SecurityError("Refresh token creation failed")
    
    def verify_token(self, token: str) -> Dict[str, Any]:
        """Verify and decode JWT token."""
        
        try:
            payload = jwt.decode(
                token,
                self.public_key,
                algorithms=[self.algorithm],
                audience=self.audience,
                issuer=self.issuer
            )
            
            # Additional validation
            if not payload.get("creator_id"):
                raise SecurityError("Invalid token: missing creator_id")
            
            return payload
            
        except jwt.ExpiredSignatureError:
            raise SecurityError("Token has expired")
        except jwt.JWTClaimsError as e:
            raise SecurityError(f"Invalid token claims: {str(e)}")
        except JWTError as e:
            raise SecurityError(f"Invalid token: {str(e)}")
    
    def refresh_access_token(self, refresh_token: str) -> str:
        """Create new access token from valid refresh token."""
        
        try:
            payload = self.verify_token(refresh_token)
            
            if payload.get("token_type") != "refresh":
                raise SecurityError("Invalid token type for refresh")
            
            creator_id = payload["creator_id"]
            
            # Get current permissions from database
            permissions = await self._get_creator_permissions(creator_id)
            subscription_tier = await self._get_subscription_tier(creator_id)
            
            return self.create_access_token(
                creator_id, permissions, subscription_tier
            )
            
        except Exception as e:
            logger.exception(f"Token refresh failed: {e}")
            raise SecurityError("Token refresh failed")
```

### Password Security
Implement secure password handling with bcrypt:

```python
from passlib.context import CryptContext
from passlib.hash import bcrypt
import secrets
import re
from typing import Optional

class PasswordManager:
    """Manages password hashing, verification, and validation."""
    
    def __init__(self):
        self.pwd_context = CryptContext(
            schemes=["bcrypt"],
            deprecated="auto",
            bcrypt__rounds=12  # Minimum 12 rounds for security
        )
        self.min_length = 8
        self.max_length = 128
    
    def hash_password(self, password: str) -> str:
        """Hash password using bcrypt with salt."""
        
        self.validate_password_strength(password)
        
        try:
            hashed = self.pwd_context.hash(password)
            return hashed
        except Exception as e:
            logger.exception(f"Password hashing failed: {e}")
            raise SecurityError("Password hashing failed")
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify password against hash."""
        
        try:
            return self.pwd_context.verify(plain_password, hashed_password)
        except Exception as e:
            logger.exception(f"Password verification failed: {e}")
            return False
    
    def validate_password_strength(self, password: str) -> None:
        """Validate password meets security requirements."""
        
        if len(password) < self.min_length:
            raise ValidationError(f"Password must be at least {self.min_length} characters")
        
        if len(password) > self.max_length:
            raise ValidationError(f"Password must be no more than {self.max_length} characters")
        
        # Check for required character types
        if not re.search(r'[A-Z]', password):
            raise ValidationError("Password must contain at least one uppercase letter")
        
        if not re.search(r'[a-z]', password):
            raise ValidationError("Password must contain at least one lowercase letter")
        
        if not re.search(r'\d', password):
            raise ValidationError("Password must contain at least one digit")
        
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            raise ValidationError("Password must contain at least one special character")
        
        # Check for common weak patterns
        weak_patterns = [
            r'(.)\1{2,}',  # Repeated characters (aaa, 111)
            r'(012|123|234|345|456|567|678|789|890)',  # Sequential numbers
            r'(abc|bcd|cde|def|efg|fgh|ghi|hij|ijk|jkl|klm|lmn|mno|nop|opq|pqr|qrs|rst|stu|tuv|uvw|vwx|wxy|xyz)',  # Sequential letters
        ]
        
        for pattern in weak_patterns:
            if re.search(pattern, password.lower()):
                raise ValidationError("Password contains weak patterns")
    
    def generate_secure_password(self, length: int = 16) -> str:
        """Generate cryptographically secure password."""
        
        if length < self.min_length:
            length = self.min_length
        
        # Character sets
        uppercase = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        lowercase = "abcdefghijklmnopqrstuvwxyz"
        digits = "0123456789"
        special = "!@#$%^&*(),.?\":{}|<>"
        
        # Ensure at least one character from each set
        password = [
            secrets.choice(uppercase),
            secrets.choice(lowercase),
            secrets.choice(digits),
            secrets.choice(special)
        ]
        
        # Fill remaining length with random characters
        all_chars = uppercase + lowercase + digits + special
        for _ in range(length - 4):
            password.append(secrets.choice(all_chars))
        
        # Shuffle the password
        secrets.SystemRandom().shuffle(password)
        
        return ''.join(password)
```

## Input Validation & Sanitization

### Comprehensive Input Validation
Implement multi-layer input validation and sanitization:

```python
import bleach
import re
import html
from urllib.parse import urlparse
from typing import Any, Dict, List, Optional
import magic

class InputValidator:
    """Comprehensive input validation and sanitization."""
    
    def __init__(self):
        self.allowed_html_tags = ['p', 'br', 'strong', 'em', 'u', 'ol', 'ul', 'li', 'h1', 'h2', 'h3']
        self.allowed_html_attributes = {
            '*': ['class'],
            'a': ['href', 'title'],
            'img': ['src', 'alt', 'width', 'height']
        }
        self.max_text_length = 10000
        self.max_filename_length = 255
    
    def sanitize_html(self, content: str) -> str:
        """Sanitize HTML content to prevent XSS."""
        
        if not content:
            return ""
        
        # Remove potentially dangerous content
        cleaned = bleach.clean(
            content,
            tags=self.allowed_html_tags,
            attributes=self.allowed_html_attributes,
            strip=True,
            strip_comments=True
        )
        
        # Additional XSS protection
        cleaned = html.escape(cleaned, quote=False)
        
        return cleaned
    
    def sanitize_filename(self, filename: str) -> str:
        """Sanitize filename to prevent path traversal and injection."""
        
        if not filename:
            raise ValidationError("Filename cannot be empty")
        
        # Remove path separators and dangerous characters
        sanitized = re.sub(r'[<>:"/\\|?*\x00-\x1f]', '_', filename)
        
        # Remove multiple dots (path traversal)
        sanitized = re.sub(r'\.\.+', '.', sanitized)
        
        # Remove leading/trailing dots and spaces
        sanitized = sanitized.strip('. ')
        
        # Limit length
        if len(sanitized) > self.max_filename_length:
            name, ext = sanitized.rsplit('.', 1) if '.' in sanitized else (sanitized, '')
            max_name_length = self.max_filename_length - len(ext) - 1 if ext else self.max_filename_length
            sanitized = name[:max_name_length] + ('.' + ext if ext else '')
        
        # Ensure not empty after sanitization
        if not sanitized or sanitized in ['.', '..']:
            sanitized = f"file_{secrets.token_hex(8)}"
        
        return sanitized
    
    def validate_email(self, email: str) -> str:
        """Validate and normalize email address."""
        
        if not email:
            raise ValidationError("Email is required")
        
        # Basic format validation
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email):
            raise ValidationError("Invalid email format")
        
        # Length validation
        if len(email) > 254:
            raise ValidationError("Email address too long")
        
        # Normalize
        email = email.lower().strip()
        
        # Check for suspicious patterns
        suspicious_patterns = [
            r'\.{2,}',  # Multiple consecutive dots
            r'^\.|\.$',  # Leading or trailing dots
            r'@.*@',  # Multiple @ symbols
        ]
        
        for pattern in suspicious_patterns:
            if re.search(pattern, email):
                raise ValidationError("Invalid email format")
        
        return email
    
    def validate_url(self, url: str, allowed_schemes: List[str] = None) -> str:
        """Validate URL and check for malicious content."""
        
        if not url:
            raise ValidationError("URL is required")
        
        allowed_schemes = allowed_schemes or ['http', 'https']
        
        try:
            parsed = urlparse(url)
            
            # Check scheme
            if parsed.scheme not in allowed_schemes:
                raise ValidationError(f"URL scheme must be one of: {', '.join(allowed_schemes)}")
            
            # Check for localhost/private IPs in production
            if parsed.hostname:
                if parsed.hostname in ['localhost', '127.0.0.1', '0.0.0.0']:
                    raise ValidationError("Localhost URLs not allowed")
                
                # Check for private IP ranges
                if self._is_private_ip(parsed.hostname):
                    raise ValidationError("Private IP addresses not allowed")
            
            # Length validation
            if len(url) > 2048:
                raise ValidationError("URL too long")
            
            return url
            
        except Exception as e:
            raise ValidationError(f"Invalid URL: {str(e)}")
    
    def validate_domain(self, domain: str) -> str:
        """Validate domain name format."""
        
        if not domain:
            raise ValidationError("Domain is required")
        
        # Domain format validation
        domain_pattern = r'^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*$'
        
        if not re.match(domain_pattern, domain):
            raise ValidationError("Invalid domain format")
        
        # Length validation
        if len(domain) > 253:
            raise ValidationError("Domain name too long")
        
        # Normalize
        domain = domain.lower().strip()
        
        # Check for suspicious patterns
        if domain.startswith('-') or domain.endswith('-'):
            raise ValidationError("Domain cannot start or end with hyphen")
        
        return domain
    
    def validate_file_upload(self, file_content: bytes, filename: str, allowed_types: List[str]) -> Dict[str, Any]:
        """Validate uploaded file content and metadata."""
        
        if not file_content:
            raise ValidationError("File content is empty")
        
        if len(file_content) > 50 * 1024 * 1024:  # 50MB limit
            raise ValidationError("File too large (max 50MB)")
        
        # Sanitize filename
        safe_filename = self.sanitize_filename(filename)
        
        # Detect MIME type from content
        try:
            detected_mime = magic.from_buffer(file_content, mime=True)
        except Exception:
            detected_mime = "application/octet-stream"
        
        # Validate against allowed types
        if detected_mime not in allowed_types:
            raise ValidationError(f"File type {detected_mime} not allowed")
        
        # Check for embedded threats (basic)
        if self._contains_malicious_patterns(file_content):
            raise ValidationError("File contains potentially malicious content")
        
        return {
            "original_filename": filename,
            "safe_filename": safe_filename,
            "mime_type": detected_mime,
            "size_bytes": len(file_content),
            "validation_passed": True
        }
    
    def _is_private_ip(self, hostname: str) -> bool:
        """Check if hostname is a private IP address."""
        
        import ipaddress
        
        try:
            ip = ipaddress.ip_address(hostname)
            return ip.is_private
        except ValueError:
            return False  # Not an IP address
    
    def _contains_malicious_patterns(self, content: bytes) -> bool:
        """Basic check for malicious patterns in file content."""
        
        # Convert to string for pattern matching (first 1KB only)
        try:
            text_content = content[:1024].decode('utf-8', errors='ignore').lower()
        except Exception:
            return False
        
        # Suspicious patterns
        malicious_patterns = [
            r'<script[^>]*>',
            r'javascript:',
            r'vbscript:',
            r'on\w+\s*=',
            r'eval\s*\(',
            r'exec\s*\(',
            r'system\s*\(',
            r'shell_exec\s*\(',
        ]
        
        for pattern in malicious_patterns:
            if re.search(pattern, text_content):
                return True
        
        return False
```

## Rate Limiting & DDoS Protection

### Advanced Rate Limiting
Implement sophisticated rate limiting with Redis:

```python
import redis.asyncio as redis
import time
import json
from typing import Dict, Optional, Tuple
from enum import Enum

class RateLimitType(Enum):
    PER_IP = "ip"
    PER_USER = "user"
    PER_ENDPOINT = "endpoint"
    GLOBAL = "global"

class RateLimiter:
    """Advanced rate limiting with multiple strategies."""
    
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
        self.default_limits = {
            "auth": {"requests": 10, "window": 300, "burst": 20},  # 10/5min, burst 20
            "upload": {"requests": 5, "window": 60, "burst": 10},   # 5/min, burst 10
            "chat": {"requests": 100, "window": 60, "burst": 150}, # 100/min, burst 150
            "search": {"requests": 50, "window": 60, "burst": 75}   # 50/min, burst 75
        }
    
    async def check_rate_limit(
        self,
        identifier: str,
        endpoint_type: str,
        limit_type: RateLimitType = RateLimitType.PER_USER,
        custom_limits: Optional[Dict] = None
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Check rate limit using sliding window algorithm.
        
        Returns:
            Tuple of (allowed: bool, info: dict)
        """
        
        limits = custom_limits or self.default_limits.get(endpoint_type, {
            "requests": 30, "window": 60, "burst": 45
        })
        
        key = f"rate_limit:{limit_type.value}:{endpoint_type}:{identifier}"
        current_time = time.time()
        window_start = current_time - limits["window"]
        
        try:
            # Use Redis pipeline for atomic operations
            pipe = self.redis.pipeline()
            
            # Remove expired entries
            pipe.zremrangebyscore(key, 0, window_start)
            
            # Count current requests
            pipe.zcard(key)
            
            # Add current request
            pipe.zadd(key, {str(current_time): current_time})
            
            # Set expiration
            pipe.expire(key, limits["window"])
            
            results = await pipe.execute()
            current_requests = results[1]
            
            # Check against limits
            allowed = current_requests < limits["requests"]
            
            # Check burst limit
            if allowed and current_requests >= limits.get("burst", limits["requests"]):
                # Implement burst protection with shorter window
                burst_window = 10  # 10 seconds
                burst_key = f"{key}:burst"
                burst_start = current_time - burst_window
                
                burst_pipe = self.redis.pipeline()
                burst_pipe.zremrangebyscore(burst_key, 0, burst_start)
                burst_pipe.zcard(burst_key)
                burst_pipe.zadd(burst_key, {str(current_time): current_time})
                burst_pipe.expire(burst_key, burst_window)
                
                burst_results = await burst_pipe.execute()
                burst_requests = burst_results[1]
                
                if burst_requests > limits.get("burst", limits["requests"]) // 5:  # 20% of burst in 10s
                    allowed = False
            
            # Calculate reset time
            reset_time = int(current_time + limits["window"])
            
            info = {
                "allowed": allowed,
                "current_requests": current_requests,
                "limit": limits["requests"],
                "window_seconds": limits["window"],
                "reset_time": reset_time,
                "retry_after": limits["window"] if not allowed else 0
            }
            
            return allowed, info
            
        except Exception as e:
            logger.exception(f"Rate limiting error: {e}")
            # Fail open - allow request if rate limiting fails
            return True, {"error": "Rate limiting unavailable"}
    
    async def get_rate_limit_status(
        self,
        identifier: str,
        endpoint_type: str,
        limit_type: RateLimitType = RateLimitType.PER_USER
    ) -> Dict[str, Any]:
        """Get current rate limit status without incrementing."""
        
        limits = self.default_limits.get(endpoint_type, {
            "requests": 30, "window": 60
        })
        
        key = f"rate_limit:{limit_type.value}:{endpoint_type}:{identifier}"
        current_time = time.time()
        window_start = current_time - limits["window"]
        
        try:
            # Clean and count without incrementing
            pipe = self.redis.pipeline()
            pipe.zremrangebyscore(key, 0, window_start)
            pipe.zcard(key)
            
            results = await pipe.execute()
            current_requests = results[1]
            
            return {
                "current_requests": current_requests,
                "limit": limits["requests"],
                "window_seconds": limits["window"],
                "remaining": max(0, limits["requests"] - current_requests),
                "reset_time": int(current_time + limits["window"])
            }
            
        except Exception as e:
            logger.exception(f"Rate limit status error: {e}")
            return {"error": "Status unavailable"}
    
    async def reset_rate_limit(
        self,
        identifier: str,
        endpoint_type: str,
        limit_type: RateLimitType = RateLimitType.PER_USER
    ) -> bool:
        """Reset rate limit for identifier (admin function)."""
        
        key = f"rate_limit:{limit_type.value}:{endpoint_type}:{identifier}"
        
        try:
            await self.redis.delete(key)
            return True
        except Exception as e:
            logger.exception(f"Rate limit reset error: {e}")
            return False
```

## Data Encryption & Protection

### Data Encryption at Rest
Implement field-level encryption for sensitive data:

```python
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import os
from typing import Optional, Union

class DataEncryption:
    """Handle encryption/decryption of sensitive data."""
    
    def __init__(self, encryption_key: Optional[str] = None):
        if encryption_key:
            self.key = encryption_key.encode()
        else:
            self.key = os.environ.get('ENCRYPTION_KEY', '').encode()
            
        if not self.key:
            # Generate key from password (use strong password in production)
            password = os.environ.get('ENCRYPTION_PASSWORD', 'default-dev-password').encode()
            salt = os.environ.get('ENCRYPTION_SALT', 'default-salt').encode()
            
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
            )
            self.key = base64.urlsafe_b64encode(kdf.derive(password))
        
        self.cipher = Fernet(self.key)
    
    def encrypt_field(self, data: Union[str, bytes]) -> str:
        """Encrypt sensitive field data."""
        
        if isinstance(data, str):
            data = data.encode('utf-8')
        
        try:
            encrypted = self.cipher.encrypt(data)
            return base64.urlsafe_b64encode(encrypted).decode('utf-8')
        except Exception as e:
            logger.exception(f"Encryption failed: {e}")
            raise SecurityError("Data encryption failed")
    
    def decrypt_field(self, encrypted_data: str) -> str:
        """Decrypt sensitive field data."""
        
        try:
            encrypted_bytes = base64.urlsafe_b64decode(encrypted_data.encode('utf-8'))
            decrypted = self.cipher.decrypt(encrypted_bytes)
            return decrypted.decode('utf-8')
        except Exception as e:
            logger.exception(f"Decryption failed: {e}")
            raise SecurityError("Data decryption failed")
    
    def encrypt_json(self, data: Dict[str, Any]) -> str:
        """Encrypt JSON data."""
        
        try:
            json_str = json.dumps(data, separators=(',', ':'))
            return self.encrypt_field(json_str)
        except Exception as e:
            logger.exception(f"JSON encryption failed: {e}")
            raise SecurityError("JSON encryption failed")
    
    def decrypt_json(self, encrypted_data: str) -> Dict[str, Any]:
        """Decrypt JSON data."""
        
        try:
            json_str = self.decrypt_field(encrypted_data)
            return json.loads(json_str)
        except Exception as e:
            logger.exception(f"JSON decryption failed: {e}")
            raise SecurityError("JSON decryption failed")
```

## Audit Logging & Security Monitoring

### Comprehensive Audit Logging
Implement detailed security audit logging:

```python
from datetime import datetime
from typing import Dict, Any, Optional
import json
import asyncio

class SecurityAuditLogger:
    """Log security events for monitoring and compliance."""
    
    def __init__(self, database, redis_client):
        self.db = database
        self.redis = redis_client
        self.log_retention_days = 90
    
    async def log_authentication_attempt(
        self,
        email: str,
        success: bool,
        ip_address: str,
        user_agent: str,
        failure_reason: Optional[str] = None
    ) -> None:
        """Log authentication attempts."""
        
        event = {
            "event_type": "authentication",
            "email": email,
            "success": success,
            "ip_address": ip_address,
            "user_agent": user_agent,
            "failure_reason": failure_reason,
            "timestamp": datetime.utcnow().isoformat(),
            "severity": "INFO" if success else "WARNING"
        }
        
        await self._write_audit_log(event)
        
        # Track failed attempts for brute force detection
        if not success:
            await self._track_failed_login(email, ip_address)
    
    async def log_authorization_failure(
        self,
        creator_id: str,
        resource: str,
        action: str,
        ip_address: str,
        required_permission: str
    ) -> None:
        """Log authorization failures."""
        
        event = {
            "event_type": "authorization_failure",
            "creator_id": creator_id,
            "resource": resource,
            "action": action,
            "required_permission": required_permission,
            "ip_address": ip_address,
            "timestamp": datetime.utcnow().isoformat(),
            "severity": "WARNING"
        }
        
        await self._write_audit_log(event)
    
    async def log_data_access(
        self,
        creator_id: str,
        resource_type: str,
        resource_id: str,
        action: str,
        ip_address: str,
        sensitive_data: bool = False
    ) -> None:
        """Log data access events."""
        
        event = {
            "event_type": "data_access",
            "creator_id": creator_id,
            "resource_type": resource_type,
            "resource_id": resource_id,
            "action": action,
            "ip_address": ip_address,
            "sensitive_data": sensitive_data,
            "timestamp": datetime.utcnow().isoformat(),
            "severity": "INFO" if not sensitive_data else "NOTICE"
        }
        
        await self._write_audit_log(event)
    
    async def log_security_event(
        self,
        event_type: str,
        creator_id: Optional[str],
        details: Dict[str, Any],
        severity: str = "WARNING"
    ) -> None:
        """Log general security events."""
        
        event = {
            "event_type": event_type,
            "creator_id": creator_id,
            "details": details,
            "timestamp": datetime.utcnow().isoformat(),
            "severity": severity
        }
        
        await self._write_audit_log(event)
    
    async def _write_audit_log(self, event: Dict[str, Any]) -> None:
        """Write audit log to database and cache."""
        
        try:
            # Write to database
            query = """
                INSERT INTO security_audit_logs 
                (event_type, creator_id, event_data, severity, created_at)
                VALUES ($1, $2, $3, $4, $5)
            """
            
            await self.db.execute(
                query,
                event["event_type"],
                event.get("creator_id"),
                json.dumps(event),
                event["severity"],
                datetime.utcnow()
            )
            
            # Cache recent events in Redis for real-time monitoring
            cache_key = f"security_events:{datetime.utcnow().strftime('%Y%m%d')}"
            await self.redis.lpush(cache_key, json.dumps(event))
            await self.redis.expire(cache_key, 86400)  # 24 hours
            
        except Exception as e:
            logger.exception(f"Failed to write audit log: {e}")
    
    async def _track_failed_login(self, email: str, ip_address: str) -> None:
        """Track failed login attempts for brute force detection."""
        
        # Track by email
        email_key = f"failed_logins:email:{email}"
        await self.redis.incr(email_key)
        await self.redis.expire(email_key, 3600)  # 1 hour
        
        # Track by IP
        ip_key = f"failed_logins:ip:{ip_address}"
        await self.redis.incr(ip_key)
        await self.redis.expire(ip_key, 3600)  # 1 hour
        
        # Check thresholds
        email_failures = await self.redis.get(email_key)
        ip_failures = await self.redis.get(ip_key)
        
        if int(email_failures or 0) >= 5:
            await self.log_security_event(
                "brute_force_email",
                None,
                {"email": email, "failures": email_failures},
                "CRITICAL"
            )
        
        if int(ip_failures or 0) >= 10:
            await self.log_security_event(
                "brute_force_ip",
                None,
                {"ip_address": ip_address, "failures": ip_failures},
                "CRITICAL"
            )
```