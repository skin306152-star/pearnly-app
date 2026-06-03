#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/integration/test_request_context_middleware.py · REFACTOR-WA-B6

域:services/observability/request_context.py · 纯 ASGI 请求上下文中间件。

锁定不变量:
  1. 响应头总带 X-Request-ID。
  2. 入站带 X-Request-ID → 沿用同值(跨服务串联)。
  3. 未带 → 生成且响应头非空。
  4. request_id 在路由 handler 内可见(纯 ASGI 同 task · contextvar 传播)。
  5. 请求结束后上下文复位(不泄漏到下一请求)。

无 DB · 用最小 FastAPI app 挂中间件 · CI 必跑不 skip。
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from fastapi import FastAPI  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from services.observability import log_context  # noqa: E402
from services.observability.request_context import RequestContextMiddleware  # noqa: E402


def _build_client() -> TestClient:
    app = FastAPI()
    app.add_middleware(RequestContextMiddleware)

    @app.get("/probe")
    def probe():
        # handler 内读 contextvar:验证中间件绑定对 handler 可见
        return {"seen": log_context.current()["request_id"]}

    return TestClient(app)


class RequestContextMiddlewareTest(unittest.TestCase):
    def setUp(self) -> None:
        self.client = _build_client()

    def test_response_always_has_request_id_header(self) -> None:
        resp = self.client.get("/probe")
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.headers.get("x-request-id"))

    def test_incoming_request_id_is_reused(self) -> None:
        resp = self.client.get("/probe", headers={"X-Request-ID": "trace-abc"})
        self.assertEqual(resp.headers.get("x-request-id"), "trace-abc")
        self.assertEqual(resp.json()["seen"], "trace-abc")

    def test_generated_id_visible_in_handler(self) -> None:
        resp = self.client.get("/probe")
        generated = resp.headers.get("x-request-id")
        self.assertTrue(generated)
        self.assertEqual(resp.json()["seen"], generated)

    def test_context_reset_after_request(self) -> None:
        self.client.get("/probe", headers={"X-Request-ID": "leak-check"})
        # 请求外(测试线程上下文)不应残留上次 request_id
        self.assertIsNone(log_context.current()["request_id"])


if __name__ == "__main__":
    unittest.main()
