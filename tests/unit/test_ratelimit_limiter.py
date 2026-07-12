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
from unittest import mock
import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.ratelimit.limiter import FixedWindowLimiter  # noqa: E402
from services.ratelimit.middleware import RateLimitMiddleware  # noqa: E402


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


class _RecordingLimiter:
    def __init__(self, allowed=True):
        self.calls = []
        self.allowed = allowed

    def check(self, key, limit, window):
        self.calls.append((key, limit, window))
        return self.allowed, 0 if self.allowed else 37


class PosAuthRateLimitTest(unittest.IsolatedAsyncioTestCase):
    async def _keys_for(self, path, authorization=None):
        async def app(scope, receive, send):
            return None

        with mock.patch.dict(
            os.environ,
            {
                "RATE_LIMIT_ENABLED": "true",
                "RATE_LIMIT_PER_MIN": "600",
                "POS_BIND_RATE_LIMIT_PER_MIN": "7",
                "POS_PIN_RATE_LIMIT_PER_MIN": "8",
            },
            clear=False,
        ):
            middleware = RateLimitMiddleware(app)
        recorder = _RecordingLimiter()
        middleware.limiter = recorder
        headers = []
        if authorization:
            headers.append((b"authorization", authorization.encode()))
        scope = {
            "type": "http",
            "path": path,
            "headers": headers,
            "client": ("203.0.113.8", 1234),
        }
        await middleware(scope, None, None)
        return recorder.calls

    async def test_pin_has_dedicated_source_and_path_bucket(self):
        calls = await self._keys_for("/api/pos/auth/pin", "Bearer attacker-a")
        self.assertIn(("pos-auth:/api/pos/auth/pin:203.0.113.8", 8, 60), calls)

    async def test_bind_has_dedicated_source_and_path_bucket(self):
        calls = await self._keys_for("/api/pos/bind", "Bearer attacker-a")
        self.assertIn(("pos-auth:/api/pos/bind:203.0.113.8", 7, 60), calls)

    async def test_forged_authorization_does_not_change_pos_auth_bucket(self):
        first = await self._keys_for("/api/pos/auth/pin", "Bearer attacker-a")
        second = await self._keys_for("/api/pos/auth/pin", "Bearer attacker-b")
        self.assertEqual(first[0][0], second[0][0])

    async def test_pos_auth_rejection_uses_pos_error_envelope(self):
        sent = []

        async def app(scope, receive, send):
            self.fail("rate-limited request reached application")

        middleware = RateLimitMiddleware(app)
        middleware.limiter = _RecordingLimiter(allowed=False)
        middleware.pos_pin_limit = 8
        scope = {
            "type": "http",
            "path": "/api/pos/auth/pin",
            "headers": [],
            "client": ("203.0.113.8", 1234),
        }

        async def send(message):
            sent.append(message)

        await middleware(scope, None, send)
        self.assertEqual(sent[0]["status"], 429)
        body = __import__("json").loads(sent[1]["body"])
        self.assertFalse(body["ok"])
        self.assertEqual(body["error"]["code"], "pos.too_many_requests")

    async def test_rotating_forwarded_headers_cannot_bypass_peer_bucket(self):
        reached = 0
        statuses = []

        async def app(scope, receive, send):
            nonlocal reached
            reached += 1

        middleware = RateLimitMiddleware(app)
        middleware.pos_pin_limit = 1
        middleware.limit = 0
        for index in range(11):
            scope = {
                "type": "http",
                "path": "/api/pos/auth/pin",
                "headers": [(b"cf-connecting-ip", f"198.51.100.{index}".encode())],
                "client": ("203.0.113.8", 1234),
            }

            async def send(message):
                if message["type"] == "http.response.start":
                    statuses.append(message["status"])

            await middleware(scope, None, send)
        self.assertEqual(reached, 10)
        self.assertEqual(statuses, [429])

    async def test_global_bucket_still_uses_pos_envelope_on_pos_path(self):
        sent = []

        async def app(scope, receive, send):
            self.fail("rate-limited request reached application")

        middleware = RateLimitMiddleware(app)
        middleware.pos_pin_limit = 0
        middleware.limiter = _RecordingLimiter(allowed=False)
        scope = {
            "type": "http",
            "path": "/api/pos/auth/pin",
            "headers": [],
            "client": ("203.0.113.8", 1234),
        }

        async def send(message):
            sent.append(message)

        await middleware(scope, None, send)
        body = __import__("json").loads(sent[1]["body"])
        self.assertEqual(body["error"]["code"], "pos.too_many_requests")


if __name__ == "__main__":
    unittest.main()
