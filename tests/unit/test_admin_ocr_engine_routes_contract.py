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
            ("GET", "/api/admin/ocr-engine/costs"),
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
        self.assertEqual(body["policy"]["mode"], "economy")  # 现役档(2026-07-22 起)
        self.assertIn("invoice", body["options"]["tasks"])
        self.assertEqual(body["options"]["plan_modes"], ["direct35", "economy", "selfhost", "qwen"])

    def test_selfhost_mode_accepted(self):
        # 自部署档可作全局模式落库(校验走 MODES 派生,后端无需特判)
        with (
            mock.patch.object(mod.store, "set_setting") as m_set,
            mock.patch.object(mod, "_log_op"),
            mock.patch.object(mod.store, "get_setting", return_value=None),
        ):
            r = self.client.post("/api/admin/ocr-engine", json={"mode": "selfhost"})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(m_set.call_args[0][1]["mode"], "selfhost")

    def test_bad_mode_400(self):
        r = self.client.post("/api/admin/ocr-engine", json={"mode": "gpt99"})
        self.assertEqual(r.status_code, 400)

    # PARTIAL_MODES 机制测试:2026-08-12 qwen 补齐 document_type 后集合清空,机制保留给
    # 未来的能力未齐档 —— 用 patch 造一个 partial 档(选真实档名 selfhost,先过 MODES 校验)
    # 钉死三个口(全局/套餐/任务)都挡、账号灰度放行。
    def test_partial_mode_rejected_as_global(self):
        with (
            mock.patch.object(mod, "PARTIAL_MODES", frozenset({"selfhost"})),
            mock.patch.object(mod.store, "set_setting") as m_set,
        ):
            r = self.client.post("/api/admin/ocr-engine", json={"mode": "selfhost"})
        self.assertEqual(r.status_code, 400)
        self.assertTrue(r.json()["detail"].startswith("ocr_engine.partial_mode_account_only"))
        m_set.assert_not_called()  # 挡住 = 一个字节都没落库

    def test_partial_mode_rejected_as_plan_default(self):
        with (
            mock.patch.object(mod, "PARTIAL_MODES", frozenset({"selfhost"})),
            mock.patch.object(mod.store, "set_setting") as m_set,
        ):
            r = self.client.post(
                "/api/admin/ocr-engine",
                json={"mode": "auto", "defaults_by_plan": {"L": "selfhost"}},
            )
        self.assertEqual(r.status_code, 400)
        self.assertTrue(r.json()["detail"].startswith("ocr_engine.partial_mode_account_only"))
        m_set.assert_not_called()

    def test_partial_mode_rejected_as_task_override(self):
        # 任务级覆写=该 task 全量切档,与全局同风险面(欠账 B6 补上的第三个口)
        with (
            mock.patch.object(mod, "PARTIAL_MODES", frozenset({"selfhost"})),
            mock.patch.object(mod.store, "set_setting") as m_set,
        ):
            r = self.client.post(
                "/api/admin/ocr-engine",
                json={"mode": "economy", "overrides_by_task": {"invoice": "selfhost"}},
            )
        self.assertEqual(r.status_code, 400)
        self.assertTrue(r.json()["detail"].startswith("ocr_engine.partial_mode_account_only"))
        m_set.assert_not_called()

    def test_partial_mode_allowed_as_account_gray_release(self):
        with (
            mock.patch.object(mod, "PARTIAL_MODES", frozenset({"selfhost"})),
            mock.patch.object(mod.store, "set_setting") as m_set,
            mock.patch.object(mod, "_log_op"),
            mock.patch.object(mod.store, "get_setting", return_value=None),
        ):
            r = self.client.post(
                "/api/admin/ocr-engine",
                json={"mode": "economy", "overrides_by_account": {"Gray@Pearnly.com": "selfhost"}},
            )
        self.assertEqual(r.status_code, 200)
        saved = m_set.call_args[0][1]
        self.assertEqual(saved["overrides_by_account"], {"gray@pearnly.com": "selfhost"})

    def test_qwen_unlocked_as_global_mode(self):
        # 解锁实锤:document_type 补齐 + 金标复测过门后,qwen 可当全局档(全局切由 Zihao 拍板)
        with (
            mock.patch.object(mod.store, "set_setting") as m_set,
            mock.patch.object(mod, "_log_op"),
            mock.patch.object(mod.store, "get_setting", return_value=None),
        ):
            r = self.client.post("/api/admin/ocr-engine", json={"mode": "qwen"})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(m_set.call_args[0][1]["mode"], "qwen")

    def test_partial_modes_exposed_to_frontend(self):
        # 卡片上的「只能按账号灰度」提示照这个清单画,写死在前端就会跟后端漂;当前为空
        with mock.patch.object(mod.store, "get_setting", return_value=None):
            r = self.client.get("/api/admin/ocr-engine")
        self.assertEqual(r.json()["options"]["partial_modes"], [])

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

    def test_account_override_saved_lowercased(self):
        with (
            mock.patch.object(mod.store, "set_setting") as m_set,
            mock.patch.object(mod, "_log_op"),
            mock.patch.object(mod.store, "get_setting", return_value=None),
        ):
            r = self.client.post(
                "/api/admin/ocr-engine",
                json={
                    "mode": "economy",
                    "overrides_by_account": {"Zihao@Example.com": "qwen", "x@y.com": ""},
                },
            )
        self.assertEqual(r.status_code, 200)
        self.assertEqual(
            m_set.call_args[0][1]["overrides_by_account"], {"zihao@example.com": "qwen"}
        )

    def test_account_override_kept_when_body_omits_it(self):
        # 旧版前端不发这个键:保存一次策略页不许把按人开的灰度悄悄关掉
        stored = {"mode": "economy", "overrides_by_account": {"zihao@example.com": "qwen"}}
        with (
            mock.patch.object(mod.store, "set_setting") as m_set,
            mock.patch.object(mod, "_log_op"),
            mock.patch.object(mod.store, "get_setting", return_value={"value": stored}),
        ):
            r = self.client.post("/api/admin/ocr-engine", json={"mode": "economy"})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(
            m_set.call_args[0][1]["overrides_by_account"], {"zihao@example.com": "qwen"}
        )

    def test_bad_account_key_and_mode_400(self):
        r = self.client.post(
            "/api/admin/ocr-engine",
            json={"mode": "economy", "overrides_by_account": {"not-an-email": "qwen"}},
        )
        self.assertEqual(r.status_code, 400)
        r = self.client.post(
            "/api/admin/ocr-engine",
            json={"mode": "economy", "overrides_by_account": {"a@b.com": "gpt99"}},
        )
        self.assertEqual(r.status_code, 400)

    def test_costs_route_returns_attribution_envelope(self):
        payload = {
            "days": 7,
            "rows": [{"entry_point": "bank_recon", "cost_per_page": 2.2}],
            "unattributed": {"calls": 3, "cost_thb": 0.5},
            "generated_at": "2026-08-11T00:00:00+00:00",
            # 售价参考线由后端单源下发(pricing.PDF_TIER1_PRICE_V21),前端不再硬编
            "price_thb_per_page": 1.5,
        }
        with mock.patch.object(mod, "get_cost_by_entry_point", return_value=payload) as m_costs:
            r = self.client.get("/api/admin/ocr-engine/costs?days=30")
        self.assertEqual(r.status_code, 200)
        m_costs.assert_called_once_with(days=30)
        self.assertEqual(r.json(), payload)
        self.assertEqual(r.json()["price_thb_per_page"], 1.5)

    def test_costs_route_days_bounds_enforced(self):
        for bad in ("0", "91"):
            r = self.client.get(f"/api/admin/ocr-engine/costs?days={bad}")
            self.assertEqual(r.status_code, 422, f"days={bad} 应被拒")

    def test_costs_route_requires_super_admin(self):
        with mock.patch.object(
            route_helpers, "get_current_user_from_request", return_value={"is_super_admin": False}
        ):
            r = self.client.get("/api/admin/ocr-engine/costs")
        self.assertEqual(r.status_code, 403)


if __name__ == "__main__":
    unittest.main()
