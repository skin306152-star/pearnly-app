# -*- coding: utf-8 -*-
"""
REFACTOR-WA-B1 守门测试 · services/error_handlers.py
(2026-05-29 从 app.py 全局异常 handler 抽出 · 纯搬家 0 逻辑改)

锁定:
  1. handle_unhandled_exception 是 coroutine · 返 500 + 稳定脱敏体 server.internal_error
     (P0-03:不回传异常类型/text/traceback · 内部诊断走超管接口)。
  2. _record_500 抛错也不影响返回(服务端记录尽力而为 · 不能因记录失败再 500)。
  3. app.py 全局 handler 委托同一来源(app.handle_unhandled_exception is 本模块对象)·
     且仍注册 @app.exception_handler(Exception)。
  4. 复用 route_helpers._record_500 单一来源。
"""

import asyncio
import inspect
import json
import unittest
from unittest import mock

from services import error_handlers


class _FakeURL:
    path = "/api/whatever"


class _FakeRequest:
    url = _FakeURL()
    method = "POST"


class ErrorHandlersContractTests(unittest.TestCase):
    def test_is_coroutine(self):
        self.assertTrue(inspect.iscoroutinefunction(error_handlers.handle_unhandled_exception))

    def test_returns_500_with_stable_sanitized_body(self):
        resp = asyncio.run(
            error_handlers.handle_unhandled_exception(_FakeRequest(), RuntimeError("boom-secret"))
        )
        self.assertEqual(resp.status_code, 500)
        body = json.loads(bytes(resp.body).decode("utf-8"))
        self.assertEqual(body, {"detail": "server.internal_error"})
        # 脱敏:不得回传异常文本
        self.assertNotIn("boom-secret", bytes(resp.body).decode("utf-8"))

    def test_record_500_failure_does_not_break_response(self):
        with mock.patch.object(
            error_handlers, "_record_500", side_effect=RuntimeError("record fail")
        ):
            resp = asyncio.run(
                error_handlers.handle_unhandled_exception(_FakeRequest(), ValueError("x"))
            )
        self.assertEqual(resp.status_code, 500)

    def test_app_delegates_single_source(self):
        import app

        self.assertIs(app.handle_unhandled_exception, error_handlers.handle_unhandled_exception)

    def test_reuses_route_helpers_record_500(self):
        from core import route_helpers

        self.assertIs(error_handlers._record_500, route_helpers._record_500)


if __name__ == "__main__":
    unittest.main()
