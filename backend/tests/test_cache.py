"""测试缓存功能"""

import time
from app.cache import cache_get, cache_set, cache_delete


class TestCache:
    def test_set_and_get(self):
        cache_delete()
        cache_set("test_key", {"data": 123}, ttl_seconds=60)
        result = cache_get("test_key")
        assert result == {"data": 123}

    def test_expiration(self):
        cache_delete()
        cache_set("expire_key", "value", ttl_seconds=1)
        time.sleep(1.1)
        assert cache_get("expire_key") is None

    def test_missing_key(self):
        cache_delete()
        assert cache_get("nonexistent") is None

    def test_delete_all(self):
        cache_set("a", 1, ttl_seconds=60)
        cache_set("b", 2, ttl_seconds=60)
        count = cache_delete()
        assert count >= 2
        assert cache_get("a") is None

    def test_delete_pattern(self):
        cache_delete()
        cache_set("topics:weibo", 1, ttl_seconds=60)
        cache_set("topics:zhihu", 2, ttl_seconds=60)
        cache_set("stats", 3, ttl_seconds=60)
        deleted = cache_delete("topics")
        assert deleted == 2
        assert cache_get("stats") == 3
