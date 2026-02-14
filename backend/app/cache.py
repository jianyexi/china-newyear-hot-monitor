"""简单的内存缓存，带 TTL 过期"""

import time
import logging
from typing import Any

logger = logging.getLogger(__name__)

_cache: dict[str, tuple[Any, float]] = {}


def cache_get(key: str) -> Any | None:
    """获取缓存，过期返回 None"""
    if key in _cache:
        value, expires_at = _cache[key]
        if time.time() < expires_at:
            return value
        del _cache[key]
    return None


def cache_set(key: str, value: Any, ttl_seconds: int = 300) -> None:
    """设置缓存"""
    _cache[key] = (value, time.time() + ttl_seconds)


def cache_delete(pattern: str = "") -> int:
    """删除匹配的缓存 key"""
    if not pattern:
        count = len(_cache)
        _cache.clear()
        return count
    keys = [k for k in _cache if pattern in k]
    for k in keys:
        del _cache[k]
    return len(keys)
