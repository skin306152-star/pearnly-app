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
  5. 登录路径(/api/login)独立强限流:低阈值、按不可伪造 IP 分桶、换 Authorization 绕不过(防爆破)。

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

    @app.post("/api/login")
    def login():
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

    def test_login_strict_limit_independent_of_global(self) -> None:
        # 全局放宽到 600 · 登录仍卡在 LOGIN_RATE_LIMIT_PER_MIN=3 → 证明登录走独立强限流
        with patch.dict(os.environ, {"RATE_LIMIT_PER_MIN": "600", "LOGIN_RATE_LIMIT_PER_MIN": "3"}):
            client = TestClient(_build_app())
            hdr = {"CF-Connecting-IP": "9.9.9.9"}
            for _ in range(3):
                self.assertEqual(client.post("/api/login", headers=hdr).status_code, 200)
            self.assertEqual(client.post("/api/login", headers=hdr).status_code, 429)

    def test_login_forged_authorization_does_not_bypass(self) -> None:
        # 攻击者每次换 Authorization 想绕过 → 登录按不可伪造的 IP 分桶 · 照样被挡
        with patch.dict(os.environ, {"RATE_LIMIT_PER_MIN": "600", "LOGIN_RATE_LIMIT_PER_MIN": "3"}):
            client = TestClient(_build_app())
            ip = {"CF-Connecting-IP": "8.8.8.8"}
            for i in range(3):
                r = client.post("/api/login", headers={**ip, "Authorization": f"Bearer forged{i}"})
                self.assertEqual(r.status_code, 200)
            blocked = client.post(
                "/api/login", headers={**ip, "Authorization": "Bearer forged_new"}
            )
            self.assertEqual(blocked.status_code, 429)

    def test_login_distinct_ip_counted_separately(self) -> None:
        with patch.dict(os.environ, {"RATE_LIMIT_PER_MIN": "600", "LOGIN_RATE_LIMIT_PER_MIN": "2"}):
            client = TestClient(_build_app())
            for _ in range(2):
                client.post("/api/login", headers={"CF-Connecting-IP": "1.2.3.4"})
            self.assertEqual(
                client.post("/api/login", headers={"CF-Connecting-IP": "1.2.3.4"}).status_code, 429
            )
            self.assertEqual(
                client.post("/api/login", headers={"CF-Connecting-IP": "5.6.7.8"}).status_code, 200
            )


if __name__ == "__main__":
    unittest.main()
