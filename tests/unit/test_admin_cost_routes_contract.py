# -*- coding: utf-8 -*-
"""
REFACTOR-B1 守门测试 · 超管成本/收入/监控 11 路由从 app.py 抽到 admin_cost_routes.py
(2026-07-09 补 ai-usage 只读端点)。

锁定(防搬迁回归):
  1. router 注册的 11 个路由 path+method 契约不变(防丢路由 / 改 URL / 改 method)
  2. app.py 通过 include_router 真挂上了(防漏挂)
  3. 全部路由复用 route_helpers._require_super_admin 单一来源(防超管闸丢失)
  4. ai-usage 端点:非超管 403 · 超管读到两个聚合读函数的结果 + 独立口径 note
"""

import unittest
from unittest import mock

from fastapi import FastAPI
from fastapi.testclient import TestClient

from routes import admin_cost_routes
from core import route_helpers
from routes.admin_cost_routes import router


class AdminCostRoutesContractTests(unittest.TestCase):
    def test_router_registers_expected_routes(self):
        """路由 path+method 契约 · 防搬迁丢路由 / 改 URL / 改 method"""
        got = set()
        for r in router.routes:
            for m in getattr(r, "methods", set()) or set():
                if m in ("GET", "POST", "PUT", "DELETE", "PATCH"):
                    got.add((m, r.path))
        expected = {
            ("GET", "/api/admin/cost/overview"),
            ("GET", "/api/admin/cost/debug"),
            ("GET", "/api/admin/cost/by_user"),
            ("GET", "/api/admin/cost/daily_trend"),
            ("GET", "/api/admin/cost/ai-usage"),
            ("GET", "/api/admin/credits/overview"),
            ("GET", "/api/admin/credits/tenants"),
            ("GET", "/api/admin/credits/daily_trend"),
            ("GET", "/api/admin/monitoring/overview"),
            ("GET", "/api/admin/credits/export"),
            ("GET", "/api/admin/cost/export"),
        }
        self.assertEqual(got, expected)

    def test_app_includes_admin_cost_router(self):
        """防 include_router 漏挂 · app 必须能路由到成本/收入/监控"""
        import app

        paths = {r.path for r in app.app.routes if hasattr(r, "path")}
        self.assertIn("/api/admin/cost/overview", paths)
        self.assertIn("/api/admin/credits/export", paths)
        self.assertIn("/api/admin/monitoring/overview", paths)

    def test_super_admin_guard_single_source(self):
        """全部路由复用 route_helpers._require_super_admin 单一来源(防超管闸丢失)"""
        self.assertIs(
            admin_cost_routes._require_super_admin,
            route_helpers._require_super_admin,
        )


class AiUsageEndpointTests(unittest.TestCase):
    def setUp(self):
        self.app = FastAPI()
        self.app.include_router(router)
        self.client = TestClient(self.app)

    def test_non_super_admin_403(self):
        with mock.patch.object(
            route_helpers, "get_current_user_from_request", return_value={"is_super_admin": False}
        ):
            r = self.client.get("/api/admin/cost/ai-usage")
        self.assertEqual(r.status_code, 403)

    def test_super_admin_reads_both_aggregations(self):
        with (
            mock.patch.object(
                route_helpers,
                "get_current_user_from_request",
                return_value={"id": "earn", "is_super_admin": True, "tenant_id": None},
            ),
            mock.patch(
                "services.cost.ai_usage_store.get_usage_by_task",
                return_value=[{"task": "line_text_understand", "calls": 1, "cost_thb": 0.1}],
            ) as m_task,
            mock.patch(
                "services.cost.ai_usage_store.get_usage_daily_trend",
                return_value=[{"day": "2026-07-09", "cost_thb": 0.1, "calls": 1}],
            ) as m_trend,
        ):
            r = self.client.get("/api/admin/cost/ai-usage")
        self.assertEqual(r.status_code, 200)
        body = r.json()
        self.assertIn("note", body)
        self.assertEqual(body["by_task"][0]["task"], "line_text_understand")
        self.assertEqual(body["daily_trend"][0]["day"], "2026-07-09")
        m_task.assert_called_once_with(days=30)
        m_trend.assert_called_once_with(days=30)


if __name__ == "__main__":
    unittest.main()
