# -*- coding: utf-8 -*-
"""
REFACTOR-D1 守门测试 · report_routes.py(v109 报告 / 模板导出 router)。

补缺(本模块此前 0 测试覆盖 · 8 硬门槛 #4「每拆一个模块必带守门测试」补齐):
  1. router 注册的 4 条路由 path+method 契约不变(防丢路由 / 改 URL)
  2. router 前缀 = /api/reports(防搬迁误改前缀)
  3. app.py 通过 include_router 真挂上了全部 4 条(防漏挂)
"""

import unittest

from report_routes import router

EXPECTED = {
    ("GET", "/api/reports/templates"),
    ("POST", "/api/reports/export"),
    ("GET", "/api/reports/clients/{client_id}/export"),
    ("POST", "/api/reports/history/batch_export"),
}


class ReportRoutesContractTests(unittest.TestCase):
    def test_router_registers_expected_routes(self):
        """4 条路由 path+method 契约 · 防搬迁丢路由 / 改 URL"""
        got = set()
        for r in router.routes:
            for m in getattr(r, "methods", set()) or set():
                if m in ("GET", "POST", "PUT", "DELETE", "PATCH"):
                    got.add((m, r.path))
        self.assertEqual(got, EXPECTED)

    def test_router_prefix(self):
        """前缀 /api/reports 固定 · 防误改导致前端全 404"""
        self.assertEqual(router.prefix, "/api/reports")

    def test_app_includes_report_router(self):
        """防 include_router 漏挂 · app 必须能路由到全部 4 条"""
        import app

        paths = {r.path for r in app.app.routes if hasattr(r, "path")}
        for _m, p in EXPECTED:
            self.assertIn(p, paths, f"report route missing from app: {p}")


if __name__ == "__main__":
    unittest.main()
