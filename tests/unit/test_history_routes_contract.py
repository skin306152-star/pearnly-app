# -*- coding: utf-8 -*-
"""
REFACTOR-B1 守门测试 · OCR 历史 10 路由从 app.py 抽到 history_routes.py(步骤 B)。

锁定(防搬迁回归):
  1. router 注册的 10 个路由 path+method 契约不变(含 v1 别名 · 防丢路由 / 改 URL)
  2. app.py 通过 include_router 真挂上了
  3. _check_history_access 复用 route_helpers._plan_permissions(单一来源)
  4. _async_run_exception_checks / _parse_money 复用 exception_checks(单一来源 · 步骤 A 搬出)
  5. model 字段契约(HistoryUpdateRequest / HistoryBatchDeleteRequest)
"""

import unittest

from services.exceptions import exception_checks
from core import route_helpers
from routes import history_routes
from routes.history_routes import (
    HistoryBatchDeleteRequest,
    HistoryUpdateRequest,
    _check_history_access,
    router,
)


class HistoryRoutesContractTests(unittest.TestCase):
    def test_router_registers_expected_routes(self):
        """路由 path+method 契约 · 防搬迁丢路由 / 改 URL"""
        got = set()
        for r in router.routes:
            for m in getattr(r, "methods", set()) or set():
                got.add((m, r.path))
        expected = {
            ("GET", "/api/history"),
            ("GET", "/api/history/{record_id}"),
            ("PUT", "/api/history/{record_id}"),
            ("DELETE", "/api/history/{record_id}"),
            ("GET", "/api/history/{record_id}/pdf"),
            ("GET", "/api/history/{record_id}/page/{page}.png"),
            ("POST", "/api/history/batch-delete"),
            ("GET", "/api/v1/history"),
            ("GET", "/api/v1/history/{record_id}"),
            ("PUT", "/api/v1/history/{record_id}"),
            ("DELETE", "/api/v1/history/{record_id}"),
            ("POST", "/api/history/{history_id}/assign_client"),
        }
        self.assertEqual(got, expected)
        self.assertEqual(len(router.routes), 12)

    def test_app_includes_history_router(self):
        """防 include_router 漏挂 · app 必须能路由到 history"""
        import app

        paths = {r.path for r in app.app.routes if hasattr(r, "path")}
        for p in ("/api/history", "/api/history/{record_id}", "/api/v1/history"):
            self.assertIn(p, paths)

    def test_check_history_access_uses_plan_permissions(self):
        """_check_history_access 依赖 route_helpers._plan_permissions · 单一来源"""
        self.assertIs(
            _check_history_access.__globals__["_plan_permissions"], route_helpers._plan_permissions
        )
        # 扁平化:can_view_history=True → 返回保留天数 int(不抛)
        self.assertIsInstance(_check_history_access({"id": "u1", "plan": "free"}), int)

    def test_exception_chain_single_source(self):
        """history PUT 重跑规则用的就是 exception_checks 的同一份对象 · 单一来源"""
        self.assertIs(
            history_routes._async_run_exception_checks,
            exception_checks._async_run_exception_checks,
        )
        self.assertIs(history_routes._parse_money, exception_checks._parse_money)

    def test_model_fields(self):
        """model 字段契约"""
        self.assertEqual(set(HistoryUpdateRequest.model_fields.keys()), {"pages"})
        self.assertEqual(set(HistoryBatchDeleteRequest.model_fields.keys()), {"ids"})


if __name__ == "__main__":
    unittest.main()
