# -*- coding: utf-8 -*-
"""
REFACTOR-D1 守门测试 · recon_routes.py(对账核心 router · 银行 / 收入 GL-VAT / 通用)。

补缺(本模块此前无专属路由契约测试 · 仅有行为测试 · 8 硬门槛 #4 补齐):
  1. router 注册的 24 条路由 path+method 契约不变(防丢路由 / 改 URL)
  2. router 前缀 = /api/recon(防搬迁误改前缀)
  3. app.py 通过 include_router 真挂上了全部 24 条(防漏挂)
  4. 三大对账族(bank-v2 / gl-vat / 通用 task)各自的核心 run / tasks / export 都在(防整族丢失)
"""

import unittest

from routes.recon_routes import router

EXPECTED = {
    # 通用对账(销项税 task)
    ("GET", "/api/recon/progress/{pid}"),
    ("POST", "/api/recon/task"),
    ("POST", "/api/recon/run/{task_id}"),
    ("POST", "/api/recon/batch_process"),
    ("GET", "/api/recon/result/{task_id}"),
    ("POST", "/api/recon/row/{row_id}/analyze"),
    ("POST", "/api/recon/row/{row_id}/action"),
    ("PATCH", "/api/recon/row/{row_id}/field"),
    ("GET", "/api/recon/tasks"),
    ("POST", "/api/recon/tasks/batch_delete"),
    ("DELETE", "/api/recon/task/{task_id}"),
    ("GET", "/api/recon/export/{task_id}"),
    # 收入对账 GL-VAT
    ("POST", "/api/recon/gl-vat/run"),
    ("GET", "/api/recon/gl-vat/tasks"),
    ("GET", "/api/recon/gl-vat/{task_id}"),
    ("GET", "/api/recon/gl-vat/{task_id}/export"),
    ("DELETE", "/api/recon/gl-vat/{task_id}"),
    ("POST", "/api/recon/gl-vat/tasks/batch_delete"),
    # 银行对账 bank-v2
    ("POST", "/api/recon/bank-v2/run"),
    ("GET", "/api/recon/bank-v2/tasks"),
    ("GET", "/api/recon/bank-v2/{task_id}"),
    ("GET", "/api/recon/bank-v2/{task_id}/export"),
    ("DELETE", "/api/recon/bank-v2/{task_id}"),
    ("POST", "/api/recon/bank-v2/tasks/batch_delete"),
}


class ReconRoutesContractTests(unittest.TestCase):
    def test_router_registers_expected_routes(self):
        """24 条路由 path+method 契约 · 防搬迁丢路由 / 改 URL"""
        got = set()
        for r in router.routes:
            for m in getattr(r, "methods", set()) or set():
                if m in ("GET", "POST", "PUT", "DELETE", "PATCH"):
                    got.add((m, r.path))
        self.assertEqual(got, EXPECTED)

    def test_router_prefix(self):
        """前缀 /api/recon 固定"""
        self.assertEqual(router.prefix, "/api/recon")

    def test_app_includes_recon_router(self):
        """防 include_router 漏挂 · app 必须能路由到全部 24 条"""
        import app

        paths = {r.path for r in app.app.routes if hasattr(r, "path")}
        for _m, p in EXPECTED:
            self.assertIn(p, paths, f"recon route missing from app: {p}")

    def test_three_recon_families_each_have_run_entry(self):
        """三大对账族各自的提交入口都在(防整族被误删):
        通用 POST /task · GL-VAT POST /gl-vat/run · 银行 POST /bank-v2/run。"""
        post_paths = {
            r.path
            for r in router.routes
            if hasattr(r, "path") and "POST" in (getattr(r, "methods", set()) or set())
        }
        self.assertIn("/api/recon/task", post_paths)
        self.assertIn("/api/recon/gl-vat/run", post_paths)
        self.assertIn("/api/recon/bank-v2/run", post_paths)


if __name__ == "__main__":
    unittest.main()
