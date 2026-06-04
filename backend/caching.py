"""
Rate Limiting & Caching - Performance optimization and API protection.
"""
from __future__ import annotations
from typing import Optional, Any
from datetime import datetime, timedelta
import json
import hashlib
import logging
from functools import wraps
import time

import redis
from fastapi import Request
from starlette.responses import Response

logger = logging.getLogger(__name__)

# Redis client for caching and rate limiting
try:
    redis_client = redis.Redis(host='redis', port=6379, db=0, decode_responses=True)
    redis_client.ping()
    logger.info("Connected to Redis")
    REDIS_AVAILABLE = True
except:
    logger.warning("Redis unavailable - caching disabled")
    REDIS_AVAILABLE = False
    redis_client = None


class CacheManager:
    """Manage application-level caching."""
    
    @staticmethod
    def get(key: str) -> Optional[Any]:
        """Get value from cache."""
        if not REDIS_AVAILABLE:
            return None
        
        try:
            value = redis_client.get(key)
            if value:
                logger.debug(f"Cache HIT: {key}")
                return json.loads(value)
            logger.debug(f"Cache MISS: {key}")
            return None
        except Exception as e:
            logger.error(f"Cache get error: {e}")
            return None
    
    @staticmethod
    def set(key: str, value: Any, expire_seconds: int = 3600) -> bool:
        """Set value in cache."""
        if not REDIS_AVAILABLE:
            return False
        
        try:
            redis_client.setex(key, expire_seconds, json.dumps(value))
            logger.debug(f"Cache SET: {key} (expires in {expire_seconds}s)")
            return True
        except Exception as e:
            logger.error(f"Cache set error: {e}")
            return False
    
    @staticmethod
    def invalidate(pattern: str):
        """Invalidate cache entries matching pattern."""
        if not REDIS_AVAILABLE:
            return
        
        try:
            keys = redis_client.keys(pattern)
            if keys:
                redis_client.delete(*keys)
                logger.info(f"Invalidated {len(keys)} cache entries: {pattern}")
        except Exception as e:
            logger.error(f"Cache invalidate error: {e}")
    
    @staticmethod
    def cache_result(expire_seconds: int = 3600):
        """Decorator to cache function results."""
        def decorator(func):
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                # Generate cache key
                key_parts = [func.__name__]
                key_parts.extend(str(arg) for arg in args if arg)
                key_parts.extend(f"{k}={v}" for k, v in kwargs.items())
                cache_key = hashlib.md5("|".join(key_parts).encode()).hexdigest()
                
                # Try cache
                cached = CacheManager.get(cache_key)
                if cached is not None:
                    return cached
                
                # Call function
                result = await func(*args, **kwargs)
                
                # Cache result
                CacheManager.set(cache_key, result, expire_seconds)
                
                return result
            
            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                key_parts = [func.__name__]
                key_parts.extend(str(arg) for arg in args if arg)
                key_parts.extend(f"{k}={v}" for k, v in kwargs.items())
                cache_key = hashlib.md5("|".join(key_parts).encode()).hexdigest()
                
                cached = CacheManager.get(cache_key)
                if cached is not None:
                    return cached
                
                result = func(*args, **kwargs)
                CacheManager.set(cache_key, result, expire_seconds)
                
                return result
            
            import inspect
            if inspect.iscoroutinefunction(func):
                return async_wrapper
            return sync_wrapper
        
        return decorator


class RateLimiter:
    """API rate limiting by user."""
    
    @staticmethod
    def check_rate_limit(user_id: str, max_requests: int = 100, window_seconds: int = 3600) -> tuple[bool, dict]:
        """
        Check if user has exceeded rate limit.
        
        Args:
            user_id: User identifier
            max_requests: Maximum requests allowed
            window_seconds: Time window for rate limit
            
        Returns:
            (allowed, info_dict)
        """
        if not REDIS_AVAILABLE:
            return True, {"rate_limit": "unavailable"}
        
        try:
            key = f"rate_limit:{user_id}"
            current = redis_client.incr(key)
            
            if current == 1:
                redis_client.expire(key, window_seconds)
            
            allowed = current <= max_requests
            
            if not allowed:
                logger.warning(f"Rate limit exceeded for user {user_id}: {current}/{max_requests}")
            
            return allowed, {
                "requests_remaining": max(0, max_requests - current),
                "reset_in": redis_client.ttl(key),
                "limit": max_requests
            }
        except Exception as e:
            logger.error(f"Rate limit check error: {e}")
            return True, {"error": str(e)}
    
    @staticmethod
    async def rate_limit_middleware(request: Request, call_next) -> Response:
        """FastAPI middleware for rate limiting."""
        # Get user from request (placeholder)
        user_id = request.headers.get("x-user-id", "anonymous")
        
        allowed, info = RateLimiter.check_rate_limit(user_id)
        
        if not allowed:
            return Response(
                status_code=429,
                content=json.dumps({"error": "Rate limit exceeded", "info": info}),
                media_type="application/json"
            )
        
        response = await call_next(request)
        response.headers.update({
            "X-RateLimit-Limit": str(info.get("limit", "")),
            "X-RateLimit-Remaining": str(info.get("requests_remaining", ""))
        })
        
        return response


class BenchmarkCache:
    """Cache benchmark results for performance."""
    
    @staticmethod
    def get_cached_benchmark() -> Optional[dict]:
        """Get cached benchmark results."""
        return CacheManager.get("benchmark_results")
    
    @staticmethod
    def cache_benchmark(results: dict, expire_hours: int = 1):
        """Cache benchmark results."""
        CacheManager.set("benchmark_results", results, expire_hours * 3600)
        logger.info("Benchmark results cached")
    
    @staticmethod
    def invalidate_benchmark():
        """Invalidate cached benchmark."""
        CacheManager.invalidate("benchmark_results")


# Cache strategies for different endpoints
CACHE_STRATEGIES = {
    "/health": {"expire": 60},  # 1 minute
    "/analytics/accuracy": {"expire": 3600},  # 1 hour
    "/analysis/history": {"expire": 300},  # 5 minutes
    "/dashboard": {"expire": 1800},  # 30 minutes
}


def get_cache_strategy(endpoint: str) -> dict:
    """Get cache strategy for endpoint."""
    return CACHE_STRATEGIES.get(endpoint, {"expire": 0})
