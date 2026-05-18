# -*- coding: utf-8 -*-
"""
services/erp/_master_data_cache.py

Tiny TTL-bounded LRU cache (P1-B Phase 1).

Why bespoke and not functools.lru_cache:
- We need TTL invalidation; lru_cache doesn't expire entries.
- We need explicit invalidate(key) to support write-through after an
  auto-create.

This isn't thread-safe by design — the master-data sync flow runs inside
a single Playwright session which is itself single-threaded. If a future
caller wants multi-thread safety, wrap in a lock at construction time.
"""

from __future__ import annotations

import time
from collections import OrderedDict
from dataclasses import dataclass
from typing import Any, Hashable, Optional


@dataclass(frozen=True)
class _Entry:
    value: Any
    expires_at: float


class TTLCache:
    """Bounded TTL cache.

    `max_size` evicts oldest (LRU) entries when full.
    `ttl_seconds` causes any get() of a stale entry to return None +
    purge the entry in passing.

    Per [mrerp-master-data-sync-design.md §6](../../docs/integrations/mrerp-master-data-sync-design.md):
    default size 1024, TTL 5 min.
    """

    def __init__(self, *, max_size: int = 1024, ttl_seconds: float = 300.0):
        if max_size < 1:
            raise ValueError("max_size must be >= 1")
        if ttl_seconds <= 0:
            raise ValueError("ttl_seconds must be > 0")
        self.max_size = int(max_size)
        self.ttl_seconds = float(ttl_seconds)
        self._store: "OrderedDict[Hashable, _Entry]" = OrderedDict()
        # Stats — handy for diagnostics; cheap to update.
        self.hits = 0
        self.misses = 0

    def __len__(self) -> int:
        return len(self._store)

    def get(self, key: Hashable) -> Optional[Any]:
        """Return the cached value or None if missing / expired."""
        entry = self._store.get(key)
        if entry is None:
            self.misses += 1
            return None
        now = time.monotonic()
        if entry.expires_at <= now:
            # Stale — drop and miss.
            del self._store[key]
            self.misses += 1
            return None
        # Move to most-recent end of the LRU.
        self._store.move_to_end(key)
        self.hits += 1
        return entry.value

    def set(self, key: Hashable, value: Any) -> None:
        """Insert or replace; evict oldest if full."""
        expires_at = time.monotonic() + self.ttl_seconds
        if key in self._store:
            del self._store[key]
        elif len(self._store) >= self.max_size:
            # popitem(last=False) drops the least-recently-used entry.
            self._store.popitem(last=False)
        self._store[key] = _Entry(value=value, expires_at=expires_at)

    def invalidate(self, key: Hashable) -> bool:
        """Drop one key. Returns True if it was present."""
        if key in self._store:
            del self._store[key]
            return True
        return False

    def clear(self) -> None:
        self._store.clear()
        self.hits = 0
        self.misses = 0
