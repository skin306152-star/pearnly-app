# -*- coding: utf-8 -*-
"""
REFACTOR-B1 守门测试 · LINE 绑定 + 偏好语言路由从 app.py 抽到 line_binding_routes.py。

锁定(防搬迁回归):
  1. router 注册 4 条路由 path+method 契约不变(/api/line/binding 同时有 GET + DELETE)
  2. app.py include_router 真挂上全部 4 条
  3. /api/line/webhook 仍留 app.py(勿碰)· /api/me/needs_email 也仍在 app(未搬)
"""

import unittest

from line_binding_routes import router

EXPECTED = {
    ("POST", "/api/line/binding-code"),
    ("GET", "/api/line/binding"),
    ("DELETE", "/api/line/binding"),
    ("POST", "/api/me/lang"),
}


class LineBindingRoutesContractTests(unittest.TestCase):
    def test_router_registers_expected_routes(self):
        got = set()
        for r in router.routes:
            for m in getattr(r, "methods", set()) or set():
                if m in ("GET", "POST", "PUT", "DELETE"):
                    got.add((m, r.path))
        self.assertEqual(got, EXPECTED)

    def test_app_includes_line_binding_router(self):
        import app

        paths = {r.path for r in app.app.routes if hasattr(r, "path")}
        for _m, p in EXPECTED:
            self.assertIn(p, paths, f"line-binding route missing from app: {p}")

    def test_webhook_and_needs_email_stay_in_app(self):
        """/api/line/webhook(勿碰)+ /api/me/needs_email(未搬)仍挂在 app · 防误搬"""
        import app

        paths = {r.path for r in app.app.routes if hasattr(r, "path")}
        self.assertIn("/api/line/webhook", paths)
        self.assertIn("/api/me/needs_email", paths)


if __name__ == "__main__":
    unittest.main()
