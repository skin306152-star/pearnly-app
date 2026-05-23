# -*- coding: utf-8 -*-
"""
REFACTOR-B1 守门测试 · 异常处理路由从 app.py 抽到 exceptions_routes.py。

锁定(防搬迁回归):
  1. router 注册的 8 个路由 path+method 契约不变(防丢路由 / 改 URL)
  2. app.py 通过 include_router 真挂上了(防漏挂)
  3. 死代码 ExceptionResolvePayload 已不再存在于两处(防搬迁时悄悄带回)
"""

import unittest

from exceptions_routes import router


class ExceptionsRoutesContractTests(unittest.TestCase):
    def test_router_registers_expected_routes(self):
        """路由 path+method 契约 · 防搬迁丢路由 / 改 URL"""
        got = set()
        for r in router.routes:
            for m in getattr(r, "methods", set()) or set():
                if m in ("GET", "POST", "PATCH", "DELETE"):
                    got.add((m, r.path))
        expected = {
            ("GET", "/api/exceptions/list"),
            ("GET", "/api/exceptions/stats"),
            ("GET", "/api/exceptions/{exception_id}"),
            ("POST", "/api/exceptions/{exception_id}/resolve"),
            ("POST", "/api/exceptions/{exception_id}/ignore"),
            ("POST", "/api/exceptions/batch"),
            ("GET", "/api/exception-whitelist"),
            ("DELETE", "/api/exception-whitelist/{wl_id}"),
        }
        self.assertEqual(got, expected)

    def test_app_includes_exceptions_router(self):
        """防 include_router 漏挂 · app 必须能路由到 exceptions"""
        import app

        paths = {r.path for r in app.app.routes if hasattr(r, "path")}
        self.assertIn("/api/exceptions/list", paths)
        self.assertIn("/api/exception-whitelist", paths)
        self.assertIn("/api/exceptions/batch", paths)

    def test_dead_payload_not_resurrected(self):
        """ExceptionResolvePayload 是死代码 · 搬迁时已删 · 两处都不该有"""
        import app
        import exceptions_routes

        self.assertFalse(hasattr(exceptions_routes, "ExceptionResolvePayload"))
        self.assertFalse(hasattr(app, "ExceptionResolvePayload"))


if __name__ == "__main__":
    unittest.main()
