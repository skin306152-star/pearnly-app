# -*- coding: utf-8 -*-
"""OCR 引擎策略超管路由契约 + 校验守门。

锁定:
  1. router path+method 契约(防丢路由 / 改 URL)
  2. app.py include_router 真挂上
  3. 非超管 403;超管读到合并默认值
  4. 写侧校验:坏 mode/坏套餐档/坏 task 一律 400 不落库;好值落库 + 审计
"""

import unittest
from unittest import mock

from fastapi import FastAPI
from fastapi.testclient import TestClient

from core import route_helpers
from routes import admin_ocr_engine_routes as mod
from routes.admin_ocr_engine_routes import router


class RoutesContractTests(unittest.TestCase):
    def test_router_registers_expected_routes(self):
        got = set()
        for r in router.routes:
            for m in getattr(r, "methods", set()) or set():
                if m in ("GET", "POST", "PUT", "DELETE", "PATCH"):
                    got.add((m, r.path))
        expected = {
            ("GET", "/api/admin/ocr-engine"),
            ("POST", "/api/admin/ocr-engine"),
            ("GET", "/api/admin/ocr-engine/metrics"),
        }
        self.assertEqual(got, expected)

    def test_app_includes_router(self):
        import app

        paths = {r.path for r in app.app.routes if hasattr(r, "path")}
        self.assertIn("/api/admin/ocr-engine", paths)

    def test_super_admin_guard_single_source(self):
        self.assertIs(mod._require_super_admin, route_helpers._require_super_admin)


class PolicyRouteTests(unittest.TestCase):
    def setUp(self):
        self.app = FastAPI()
        self.app.include_router(router)
        self.client = TestClient(self.app)
        self._su = mock.patch.object(
            route_helpers,
            "get_current_user_from_request",
            return_value={"id": "earn", "is_super_admin": True, "tenant_id": None},
        )
        self._su.start()
        self.addCleanup(self._su.stop)

    def test_non_super_admin_403(self):
        with mock.patch.object(
            route_helpers, "get_current_user_from_request", return_value={"is_super_admin": False}
        ):
            r = self.client.get("/api/admin/ocr-engine")
        self.assertEqual(r.status_code, 403)

    def test_get_merges_defaults(self):
        with mock.patch.object(mod.store, "get_setting", return_value=None):
            r = self.client.get("/api/admin/ocr-engine")
        self.assertEqual(r.status_code, 200)
        body = r.json()
        self.assertEqual(body["policy"]["mode"], "direct35")
        self.assertIn("invoice", body["options"]["tasks"])
        self.assertEqual(body["options"]["plan_modes"], ["direct35", "economy"])

    def test_bad_mode_400(self):
        r = self.client.post("/api/admin/ocr-engine", json={"mode": "gpt99"})
        self.assertEqual(r.status_code, 400)

    def test_bad_plan_mode_400(self):
        r = self.client.post(
            "/api/admin/ocr-engine",
            json={"mode": "auto", "defaults_by_plan": {"none": "auto"}},
        )
        self.assertEqual(r.status_code, 400)

    def test_bad_task_400(self):
        r = self.client.post(
            "/api/admin/ocr-engine",
            json={"mode": "direct35", "overrides_by_task": {"hack": "economy"}},
        )
        self.assertEqual(r.status_code, 400)

    def test_valid_policy_saved_with_audit(self):
        with (
            mock.patch.object(mod.store, "set_setting") as m_set,
            mock.patch.object(mod, "_log_op") as m_log,
            mock.patch.object(mod.store, "get_setting", return_value=None),
        ):
            r = self.client.post(
                "/api/admin/ocr-engine",
                json={
                    "mode": "auto",
                    "defaults_by_plan": {"none": "economy", "L": "direct35"},
                    "overrides_by_task": {"id_card": "direct35", "invoice": ""},
                },
            )
        self.assertEqual(r.status_code, 200)
        m_set.assert_called_once()
        args = m_set.call_args[0]
        self.assertEqual(args[0], "ocr_engine_policy")
        self.assertEqual(args[1]["mode"], "auto")
        self.assertEqual(args[1]["defaults_by_plan"]["none"], "economy")
        # 空覆写(跟全局)不落库;显式覆写保留
        self.assertEqual(args[1]["overrides_by_task"], {"id_card": "direct35"})
        self.assertTrue(args[2])
        m_log.assert_called_once()

    def test_metrics_route_ok(self):
        with mock.patch.object(
            mod, "get_ocr_engine_metrics", return_value={"days": 7}
        ) as m_metrics:
            r = self.client.get("/api/admin/ocr-engine/metrics?days=7")
        self.assertEqual(r.status_code, 200)
        m_metrics.assert_called_once_with(days=7)


if __name__ == "__main__":
    unittest.main()
