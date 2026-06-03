#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/unit/test_ratelimit_limiter.py · REFACTOR-WA-B5

域:services/ratelimit/limiter.py · 固定窗口限流器。

锁定不变量:
  1. limit 以内放行 · 超出拒绝并给正的 retry_after。
  2. limit<=0 / window<=0 视为不限流(防误配锁死全站)。
  3. 不同 key 互不影响。
  4. reset 清空计数。
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.ratelimit.limiter import FixedWindowLimiter  # noqa: E402


class FixedWindowLimiterTest(unittest.TestCase):
    def setUp(self) -> None:
        self.limiter = FixedWindowLimiter()

    def test_allows_within_limit(self) -> None:
        for _ in range(5):
            allowed, retry = self.limiter.check("k", limit=5, window=60)
            self.assertTrue(allowed)
            self.assertEqual(retry, 0)

    def test_rejects_over_limit(self) -> None:
        for _ in range(3):
            self.limiter.check("k", limit=3, window=60)
        allowed, retry = self.limiter.check("k", limit=3, window=60)
        self.assertFalse(allowed)
        self.assertGreater(retry, 0)

    def test_zero_limit_means_unlimited(self) -> None:
        for _ in range(100):
            allowed, _ = self.limiter.check("k", limit=0, window=60)
            self.assertTrue(allowed)

    def test_keys_are_independent(self) -> None:
        for _ in range(3):
            self.limiter.check("a", limit=3, window=60)
        # a 已满 · b 仍应放行
        self.assertFalse(self.limiter.check("a", limit=3, window=60)[0])
        self.assertTrue(self.limiter.check("b", limit=3, window=60)[0])

    def test_reset_clears(self) -> None:
        for _ in range(3):
            self.limiter.check("k", limit=3, window=60)
        self.limiter.reset()
        self.assertTrue(self.limiter.check("k", limit=3, window=60)[0])


if __name__ == "__main__":
    unittest.main()
