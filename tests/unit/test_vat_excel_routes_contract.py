# -*- coding: utf-8 -*-
"""
REFACTOR-D1 守门测试 · vat_excel_routes.py(Excel 公式对账 router)。

补缺(本模块此前无专属路由契约测试 · 8 硬门槛 #4 补齐):
  1. router 注册的 8 条路由 path+method 契约不变(防丢路由 / 改 URL)
  2. router 前缀 = /api/vat_excel(防搬迁误改前缀)
  3. app.py 通过 include_router 真挂上了全部 8 条(防漏挂)
  4. /tasks/clear_old 与 /tasks/{task_id} 同为 DELETE 但不同 path(防静态段被动态段吞掉)
"""

import unittest

from routes.vat_excel_routes import router

EXPECTED = {
    ("GET", "/api/vat_excel/check"),
    ("POST", "/api/vat_excel/build"),
    ("GET", "/api/vat_excel/tasks"),
    ("GET", "/api/vat_excel/tasks/{task_id}"),
    ("DELETE", "/api/vat_excel/tasks/clear_old"),
    ("DELETE", "/api/vat_excel/tasks/{task_id}"),
    ("GET", "/api/vat_excel/tasks/{task_id}/download"),
    ("POST", "/api/vat_excel/tasks/{task_id}/regenerate"),
}


class VatExcelRoutesContractTests(unittest.TestCase):
    def test_router_registers_expected_routes(self):
        """8 条路由 path+method 契约 · 防搬迁丢路由 / 改 URL"""
        got = set()
        for r in router.routes:
            for m in getattr(r, "methods", set()) or set():
                if m in ("GET", "POST", "PUT", "DELETE", "PATCH"):
                    got.add((m, r.path))
        self.assertEqual(got, EXPECTED)

    def test_router_prefix(self):
        """前缀 /api/vat_excel 固定"""
        self.assertEqual(router.prefix, "/api/vat_excel")

    def test_clear_old_delete_declared_before_dynamic_task_id(self):
        """静态 DELETE /tasks/clear_old 必须排在同方法动态 DELETE /tasks/{task_id} 之前 ·
        否则 FastAPI 按声明序匹配会把 clear_old 当 task_id='clear_old' 删除。
        注意:必须只比同为 DELETE 的两条(/tasks/{task_id} 另有一条 GET · 方法不同不冲突)。"""
        delete_paths = [
            r.path
            for r in router.routes
            if hasattr(r, "path") and "DELETE" in (getattr(r, "methods", set()) or set())
        ]
        self.assertIn("/api/vat_excel/tasks/clear_old", delete_paths)
        self.assertIn("/api/vat_excel/tasks/{task_id}", delete_paths)
        self.assertLess(
            delete_paths.index("/api/vat_excel/tasks/clear_old"),
            delete_paths.index("/api/vat_excel/tasks/{task_id}"),
            "DELETE clear_old 必须先于 DELETE {task_id} 注册",
        )

    def test_app_includes_vat_excel_router(self):
        """防 include_router 漏挂 · app 必须能路由到全部 8 条"""
        import app

        paths = {r.path for r in app.app.routes if hasattr(r, "path")}
        for _m, p in EXPECTED:
            self.assertIn(p, paths, f"vat_excel route missing from app: {p}")


if __name__ == "__main__":
    unittest.main()
