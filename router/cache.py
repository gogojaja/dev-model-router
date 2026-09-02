#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
结果缓存模块

支持相同输入复用缓存结果，降低重复调用成本。
"""

from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass, field
from typing import Optional, Dict, Any
from pathlib import Path


@dataclass
class CacheEntry:
    """缓存条目"""
    key: str
    value: Any
    created_at: float
    ttl: float = 3600.0  # 默认1小时

    @property
    def is_expired(self) -> bool:
        return time.time() - self.created_at > self.ttl


class ResultCache:
    """
    结果缓存

    Usage:
        cache = ResultCache()
        cache.set("task_key", result)
        cached = cache.get("task_key")
    """

    def __init__(self, ttl: float = 3600.0, max_size: int = 1000, storage_path: Optional[Path] = None):
        self.ttl = ttl
        self.max_size = max_size
        self.storage_path = storage_path
        self._cache: Dict[str, CacheEntry] = {}
        self._hits = 0
        self._misses = 0

    @staticmethod
    def make_key(task_description: str, **kwargs) -> str:
        """生成缓存键"""
        content = task_description + json.dumps(kwargs, sort_keys=True, default=str)
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    def get(self, key: str) -> Optional[Any]:
        """获取缓存"""
        entry = self._cache.get(key)
        if entry is None:
            self._misses += 1
            return None
        if entry.is_expired:
            del self._cache[key]
            self._misses += 1
            return None
        self._hits += 1
        return entry.value

    def set(self, key: str, value: Any, ttl: Optional[float] = None):
        """设置缓存"""
        if len(self._cache) >= self.max_size:
            self._evict()
        self._cache[key] = CacheEntry(
            key=key,
            value=value,
            created_at=time.time(),
            ttl=ttl or self.ttl,
        )

    def invalidate(self, key: str):
        """使缓存失效"""
        self._cache.pop(key, None)

    def clear(self):
        """清空缓存"""
        self._cache.clear()
        self._hits = 0
        self._misses = 0

    @property
    def hit_rate(self) -> float:
        total = self._hits + self._misses
        return self._hits / total if total > 0 else 0.0

    def _evict(self):
        """淘汰最老条目（O(1)：Python 3.7+ dict 保持插入顺序）"""
        if self._cache:
            self._cache.pop(next(iter(self._cache)))
