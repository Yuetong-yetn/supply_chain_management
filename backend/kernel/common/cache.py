"""TTL 缓存。"""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass
from typing import Any

from kernel.common.config import get_settings


@dataclass
class CacheItem:
    value: Any
    expires_at: float


class TTLCache:
    def __init__(self, default_ttl: int):
        self.default_ttl = default_ttl
        self._data: dict[str, CacheItem] = {}
        self._lock = threading.Lock()

    def get(self, key: str) -> Any | None:
        with self._lock:
            item = self._data.get(key)
            if not item:
                return None
            if item.expires_at < time.time():
                self._data.pop(key, None)
                return None
            return item.value

    def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        with self._lock:
            self._data[key] = CacheItem(
                value=value,
                expires_at=time.time() + (ttl or self.default_ttl),
            )

    def delete_prefix(self, prefix: str) -> None:
        with self._lock:
            for key in list(self._data):
                if key.startswith(prefix):
                    self._data.pop(key, None)

    def clear(self) -> None:
        with self._lock:
            self._data.clear()


cache = TTLCache(default_ttl=get_settings().cache_ttl_seconds)


def invalidate_business_cache() -> None:
    for prefix in ("analytics:", "inventory:", "recommendation:", "distributed:"):
        cache.delete_prefix(prefix)
