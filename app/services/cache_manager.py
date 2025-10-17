from cachetools import TTLCache
from typing import Any, Optional
from app.config import settings

class CacheManager:
    def __init__(self):
        self.cache = TTLCache(maxsize=settings.CACHE_MAXSIZE, ttl=settings.CACHE_TTL)
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        return self.cache.get(key)
    
    def set(self, key: str, value: Any) -> None:
        """Set value in cache"""
        self.cache[key] = value
    
    def clear(self) -> None:
        """Clear all cache"""
        self.cache.clear()

# Global cache instance
cache_manager = CacheManager()