# -*- coding: utf-8 -*-
"""
REFACTOR-WA-B1 守门测试 · vat_excel_routes 563→拆分(R22 · 2026-05-29)
非扣费任务路由(list/get/clear_old/delete)下沉 vat_excel_tasks_routes · 共享 _require_user/_user_key/
_tenant_user 下沉 vat_excel_helpers · vat_excel_routes include_router 聚合(承父 /api/vat_excel 前缀)。
扣费路由(build / regenerate)+ _save_excel_file 留 vat_excel_routes 不动(高敏·handlers 引用/测试 patch 锚点)。

锁定:① tasks 子路由含 4 条非扣费任务路由 ② helpers 单一来源(routes/tasks/helpers 同一对象)
③ _save_excel_file 仍在 vat_excel_routes(handlers import + 测试 patch 锚点不破)④ 无循环依赖。
全 8 条路由 path+method/前缀/DELETE 顺序/app 挂载 由既有 test_vat_excel_routes_contract 守。
"""

import unittest

from routes import vat_excel_routes
from routes import vat_excel_tasks_routes
from services.vat import vat_excel_helpers


def _paths(r):
    out = set()
    for route in r.routes:
        for m in getattr(route, "methods", None) or set():
            if m in ("GET", "POST", "PUT", "DELETE", "PATCH"):
                out.add((m, route.path))
    return out


class VatExcelSplitContractTests(unittest.TestCase):
    def test_tasks_subrouter_routes(self):
        # 子路由(无前缀 · 承父 /api/vat_excel)含 4 条非扣费任务路由
        self.assertEqual(
            _paths(vat_excel_tasks_routes.router),
            {
                ("GET", "/tasks"),
                ("GET", "/tasks/{task_id}"),
                ("DELETE", "/tasks/clear_old"),
                ("DELETE", "/tasks/{task_id}"),
            },
        )

    def test_helpers_single_source(self):
        for n in ("_require_user", "_user_key", "_tenant_user"):
            self.assertIs(getattr(vat_excel_routes, n), getattr(vat_excel_helpers, n), n)
        self.assertIs(vat_excel_tasks_routes._require_user, vat_excel_helpers._require_user)
        self.assertIs(vat_excel_tasks_routes._tenant_user, vat_excel_helpers._tenant_user)

    def test_save_excel_file_stays_on_routes(self):
        # handlers.py import + test_recon_handlers/test_salesvat patch 锚点 · 必须留在 vat_excel_routes
        self.assertTrue(callable(getattr(vat_excel_routes, "_save_excel_file", None)))

    def test_no_cycle(self):
        self.assertIsNone(getattr(vat_excel_helpers, "vat_excel_routes", None))
        self.assertIsNone(getattr(vat_excel_tasks_routes, "vat_excel_routes", None))


if __name__ == "__main__":
    unittest.main()
