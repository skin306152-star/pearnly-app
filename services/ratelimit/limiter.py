# -*- coding: utf-8 -*-
"""services/ratelimit/limiter.py · REFACTOR-WA-B5 · 进程内固定窗口限流器。

固定窗口计数:每个 key 在 window 秒内累计 count · 超 limit 拒绝并给 retry_after。
进程内(uvicorn 多 worker 各算各的 · 即有效阈值 ≈ limit×worker 数)· 这是粗粒度
DoS/滥用防护 · 不追求分布式精确;真分布式限流需 Redis(本期不引)。

线程安全:单锁保护 · 单 worker 内 asyncio 虽单线程 · 但 TestClient/线程场景仍加锁兜底。
内存有界:每次 check 顺带清理过期 key(惰性 GC)· key 数 = 活跃来源数。
"""

from __future__ import annotations

import threading
import time
from typing import Dict, Tuple


class FixedWindowLimiter:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        # key -> (window_start_monotonic, count)
        self._buckets: Dict[str, Tuple[float, int]] = {}
        self._last_gc = 0.0

    def check(self, key: str, limit: int, window: int) -> Tuple[bool, int]:
        """返回 (allowed, retry_after_seconds)。allowed=True 时 retry_after=0。

        limit<=0 视为不限流(allowed=True)· 防误配把全站锁死。
        """
        if limit <= 0 or window <= 0:
            return True, 0

        now = time.monotonic()
        with self._lock:
            self._maybe_gc(now, window)
            start, count = self._buckets.get(key, (now, 0))
            if now - start >= window:
                start, count = now, 0  # 窗口翻篇
            count += 1
            self._buckets[key] = (start, count)
            if count > limit:
                retry_after = max(1, int(window - (now - start)) + 1)
                return False, retry_after
            return True, 0

    def _maybe_gc(self, now: float, window: int) -> None:
        # 每 window 秒至多清一次 · 删掉已过期窗口的 key · O(n) 但低频
        if now - self._last_gc < window:
            return
        self._last_gc = now
        cutoff = now - window
        stale = [k for k, (start, _) in self._buckets.items() if start < cutoff]
        for k in stale:
            del self._buckets[k]

    def reset(self) -> None:
        """清空(测试用)。"""
        with self._lock:
            self._buckets.clear()
            self._last_gc = 0.0
