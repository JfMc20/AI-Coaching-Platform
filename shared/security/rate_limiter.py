"""
Rate Limiting Implementation for Multi-Tenant Platform

Implements sophisticated rate limiting with Redis backend for scalability
and multi-tenant isolation following security patterns.
"""

import time
import logging
from typing import Dict, Optional, Tuple, Any
from enum import Enum

from shared.cache import get_cache_manager
from shared.exceptions.base import BaseServiceException

logger = logging.getLogger(__name__)


class RateLimitType(str, Enum):
    """Rate limit types for different contexts"""
    PER_IP = "ip"
    PER_USER = "user"
    PER_CREATOR = "creator"
    PER_ENDPOINT = "endpoint"
    GLOBAL = "global"


class RateLimitError(BaseServiceException):
    """Rate limit exceeded error"""
    def __init__(self, message: str = "Rate limit exceeded", retry_after: int = 60):
        super().__init__(message)
        self.error_code = "RATE_LIMIT_EXCEEDED"
        self.status_code = 429
        self.retry_after = retry_after


class RateLimiter:
    """
    Advanced rate limiting with Redis backend and multi-tenant support
    
    Uses sliding window algorithm with burst protection and tenant isolation.
    """
    
    def __init__(self, cache_manager=None):
        """
        Initialize rate limiter
        
        Args:
            cache_manager: Cache manager for Redis operations
        """
        self.cache_manager = cache_manager or get_cache_manager()
        
        # Default rate limits by endpoint type
        self.default_limits = {
            "auth": {"requests": 10, "window": 300, "burst": 20},      # 10/5min, burst 20
            "upload": {"requests": 5, "window": 60, "burst": 10},      # 5/min, burst 10
            "chat": {"requests": 100, "window": 60, "burst": 150},     # 100/min, burst 150
            "search": {"requests": 50, "window": 60, "burst": 75},     # 50/min, burst 75
            "document": {"requests": 20, "window": 300, "burst": 30},  # 20/5min, burst 30
            "default": {"requests": 30, "window": 60, "burst": 45}     # 30/min, burst 45
        }
    
    async def check_rate_limit(
        self,
        identifier: str,
        endpoint_type: str,
        limit_type: RateLimitType = RateLimitType.PER_USER,
        custom_limits: Optional[Dict[str, int]] = None
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Check rate limit using sliding window algorithm
        
        Args:
            identifier: Unique identifier (user_id, ip, creator_id, etc.)
            endpoint_type: Type of endpoint (auth, chat, upload, etc.)
            limit_type: Type of rate limiting to apply
            custom_limits: Override default limits
            
        Returns:
            Tuple of (allowed: bool, info: dict)
        """
        limits = custom_limits or self.default_limits.get(endpoint_type, self.default_limits["default"])
        
        # Create tenant-isolated key
        key = f"rate_limit:{limit_type.value}:{endpoint_type}:{identifier}"
        current_time = time.time()
        window_start = current_time - limits["window"]
        
        try:
            # Get Redis client
            redis_client = await self.cache_manager.redis.get_client()
            
            # Use Redis pipeline for atomic operations
            pipe = redis_client.pipeline()
            
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
            
            # Check burst limit if configured
            if allowed and limits.get("burst") and current_requests >= limits.get("burst", limits["requests"]):
                # Implement burst protection with shorter window
                burst_window = 10  # 10 seconds
                burst_key = f"{key}:burst"
                burst_start = current_time - burst_window
                
                burst_pipe = redis_client.pipeline()
                burst_pipe.zremrangebyscore(burst_key, 0, burst_start)
                burst_pipe.zcard(burst_key)
                burst_pipe.zadd(burst_key, {str(current_time): current_time})
                burst_pipe.expire(burst_key, burst_window)
                
                burst_results = await burst_pipe.execute()
                burst_requests = burst_results[1]
                
                # Allow max 20% of burst limit in 10 seconds
                burst_threshold = max(1, limits.get("burst", limits["requests"]) // 5)
                if burst_requests > burst_threshold:
                    allowed = False
            
            # Calculate reset time
            reset_time = int(current_time + limits["window"])
            
            info = {
                "allowed": allowed,
                "current_requests": current_requests,
                "limit": limits["requests"],
                "window_seconds": limits["window"],
                "reset_time": reset_time,
                "retry_after": limits["window"] if not allowed else 0,
                "burst_limit": limits.get("burst"),
                "endpoint_type": endpoint_type,
                "limit_type": limit_type.value
            }
            
            return allowed, info
            
        except Exception as e:
            logger.exception(f"Rate limiting error for {identifier}: {e}")
            
            # Fail open by default (configurable)
            return True, {
                "error": "Rate limiting service unavailable",
                "fail_mode": "open",
                "allowed": True
            }
    
    async def get_rate_limit_status(
        self,
        identifier: str,
        endpoint_type: str,
        limit_type: RateLimitType = RateLimitType.PER_USER
    ) -> Dict[str, Any]:
        """
        Get current rate limit status without incrementing counter
        
        Args:
            identifier: Unique identifier
            endpoint_type: Type of endpoint
            limit_type: Type of rate limiting
            
        Returns:
            Current rate limit status
        """
        limits = self.default_limits.get(endpoint_type, self.default_limits["default"])
        key = f"rate_limit:{limit_type.value}:{endpoint_type}:{identifier}"
        current_time = time.time()
        window_start = current_time - limits["window"]
        
        try:
            redis_client = await self.cache_manager.redis.get_client()
            
            # Clean and count without incrementing
            pipe = redis_client.pipeline()
            pipe.zremrangebyscore(key, 0, window_start)
            pipe.zcard(key)
            
            results = await pipe.execute()
            current_requests = results[1]
            
            return {
                "current_requests": current_requests,
                "limit": limits["requests"],
                "window_seconds": limits["window"],
                "remaining": max(0, limits["requests"] - current_requests),
                "reset_time": int(current_time + limits["window"]),
                "burst_limit": limits.get("burst")
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
        """
        Reset rate limit for identifier (admin function)
        
        Args:
            identifier: Unique identifier
            endpoint_type: Type of endpoint
            limit_type: Type of rate limiting
            
        Returns:
            True if reset successful
        """
        key = f"rate_limit:{limit_type.value}:{endpoint_type}:{identifier}"
        
        try:
            redis_client = await self.cache_manager.redis.get_client()
            await redis_client.delete(key)
            await redis_client.delete(f"{key}:burst")
            
            logger.info(f"Reset rate limit for {identifier} on {endpoint_type}")
            return True
            
        except Exception as e:
            logger.exception(f"Rate limit reset error: {e}")
            return False
    
    def get_limits_for_endpoint(self, endpoint_type: str) -> Dict[str, int]:
        """
        Get configured limits for endpoint type
        
        Args:
            endpoint_type: Type of endpoint
            
        Returns:
            Limit configuration
        """
        return self.default_limits.get(endpoint_type, self.default_limits["default"])
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Check rate limiter health
        
        Returns:
            Health status
        """
        try:
            # Test Redis connectivity
            redis_client = await self.cache_manager.redis.get_client()
            await redis_client.ping()
            
            return {
                "status": "healthy",
                "redis_connected": True,
                "default_limits": self.default_limits
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "redis_connected": False,
                "error": str(e)
            }


# Global rate limiter instance
_rate_limiter: Optional[RateLimiter] = None


def get_rate_limiter() -> RateLimiter:
    """Get global rate limiter instance (lazy initialization)"""
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = RateLimiter()
    return _rate_limiter


# FastAPI dependency for rate limiting
async def check_rate_limit_dependency(
    request,
    endpoint_type: str = "default",
    limit_type: RateLimitType = RateLimitType.PER_IP
):
    """
    FastAPI dependency for rate limiting
    
    Args:
        request: FastAPI request object
        endpoint_type: Type of endpoint
        limit_type: Type of rate limiting
        
    Raises:
        RateLimitError: If rate limit exceeded
    """
    # Get identifier based on limit type
    if limit_type == RateLimitType.PER_IP:
        identifier = request.client.host
    elif limit_type == RateLimitType.PER_USER:
        # Extract from JWT token if available
        identifier = getattr(request.state, 'creator_id', request.client.host)
    else:
        identifier = request.client.host
    
    rate_limiter = get_rate_limiter()
    allowed, info = await rate_limiter.check_rate_limit(identifier, endpoint_type, limit_type)
    
    if not allowed:
        raise RateLimitError(
            f"Rate limit exceeded for {endpoint_type}",
            retry_after=info.get("retry_after", 60)
        )