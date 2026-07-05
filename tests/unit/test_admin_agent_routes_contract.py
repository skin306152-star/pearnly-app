# -*- coding: utf-8 -*-
"""对话 Agent 观测超管路由契约。

锁定:
  1. router path+method 契约(防丢路由 / 改 URL)
  2. app.py include_router 真挂上
  3. 非超管 403;超管拿到 health+funnel 两块聚合
"""

import unittest
from unittest import mock

from fastapi import FastAPI
from fastapi.testclient import TestClient

from core import route_helpers
from routes import admin_agent_routes as mod
from routes.admin_agent_routes import router


class RoutesContractTests(unittest.TestCase):
    def test_router_registers_expected_routes(self):
        got = set()
        for r in router.routes:
            for m in getattr(r, "methods", set()) or set():
                if m in ("GET", "POST", "PUT", "DELETE", "PATCH"):
                    got.add((m, r.path))
        self.assertEqual(got, {("GET", "/api/admin/agent/overview")})

    def test_app_includes_router(self):
        import app

        paths = {r.path for r in app.app.routes if hasattr(r, "path")}
        self.assertIn("/api/admin/agent/overview", paths)

    def test_super_admin_guard_single_source(self):
        self.assertIs(mod._require_super_admin, route_helpers._require_super_admin)


class OverviewRouteTests(unittest.TestCase):
    def setUp(self):
        self.app = FastAPI()
        self.app.include_router(router)
        self.client = TestClient(self.app)

    def test_non_super_admin_403(self):
        with mock.patch.object(
            route_helpers, "get_current_user_from_request", return_value={"is_super_admin": False}
        ):
            r = self.client.get("/api/admin/agent/overview")
        self.assertEqual(r.status_code, 403)

    def test_overview_aggregates_health_and_funnel(self):
        health = {"hours": 24, "total": 3, "crash_rate": 0.0, "degraded_rate": 0.0}
        funnel = {"days": 7, "follows": 5, "binds": 2, "agent_used": 2, "recorded": 1}
        with (
            mock.patch.object(
                route_helpers,
                "get_current_user_from_request",
                return_value={"id": "earn", "is_super_admin": True, "tenant_id": None},
            ),
            mock.patch.object(mod.turn_log, "stats", return_value=health) as st,
            mock.patch.object(mod.line_funnel, "funnel_stats", return_value=funnel) as fu,
        ):
            r = self.client.get("/api/admin/agent/overview?hours=48&days=14")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json(), {"health": health, "funnel": funnel})
        st.assert_called_once_with(hours=48)
        fu.assert_called_once_with(days=14)


if __name__ == "__main__":
    unittest.main()
