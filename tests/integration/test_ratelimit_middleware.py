#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/integration/test_ratelimit_middleware.py · REFACTOR-WA-B5

域:services/ratelimit/middleware.py · 全局限流中间件(纯 ASGI)。

锁定不变量:
  1. limit 以内请求 200 · 超出返 429 + Retry-After。
  2. 豁免前缀(/api/health 等)永不限流。
  3. RATE_LIMIT_ENABLED=false → 完全放行。
  4. 不同来源 IP 各自计数(X-Forwarded-For 区分)。

无 DB · 最小 FastAPI app · CI 必跑不 skip。
"""

from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from fastapi import FastAPI  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from services.ratelimit.middleware import RateLimitMiddleware  # noqa: E402


def _build_app() -> FastAPI:
    app = FastAPI()
    app.add_middleware(RateLimitMiddleware)

    @app.get("/api/thing")
    def thing():
        return {"ok": True}

    @app.get("/api/health")
    def health():
        return {"ok": True}

    return app


class RateLimitMiddlewareTest(unittest.TestCase):
    def setUp(self) -> None:
        self.env = patch.dict(os.environ, {"RATE_LIMIT_ENABLED": "true", "RATE_LIMIT_PER_MIN": "3"})
        self.env.start()
        self.client = TestClient(_build_app())

    def tearDown(self) -> None:
        self.env.stop()

    def test_within_limit_then_429(self) -> None:
        for _ in range(3):
            self.assertEqual(self.client.get("/api/thing").status_code, 200)
        resp = self.client.get("/api/thing")
        self.assertEqual(resp.status_code, 429)
        self.assertTrue(resp.headers.get("retry-after"))
        self.assertEqual(resp.json()["error"], "too_many_requests")

    def test_exempt_path_never_limited(self) -> None:
        for _ in range(10):
            self.assertEqual(self.client.get("/api/health").status_code, 200)

    def test_disabled_passes_through(self) -> None:
        with patch.dict(os.environ, {"RATE_LIMIT_ENABLED": "false"}):
            client = TestClient(_build_app())
            for _ in range(10):
                self.assertEqual(client.get("/api/thing").status_code, 200)

    def test_distinct_ips_counted_separately(self) -> None:
        for _ in range(3):
            self.client.get("/api/thing", headers={"X-Forwarded-For": "1.1.1.1"})
        # 1.1.1.1 已满 → 429;2.2.2.2 仍放行
        self.assertEqual(
            self.client.get("/api/thing", headers={"X-Forwarded-For": "1.1.1.1"}).status_code,
            429,
        )
        self.assertEqual(
            self.client.get("/api/thing", headers={"X-Forwarded-For": "2.2.2.2"}).status_code,
            200,
        )


if __name__ == "__main__":
    unittest.main()
