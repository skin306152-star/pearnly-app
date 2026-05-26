# -*- coding: utf-8 -*-
"""
REFACTOR-B1 守门测试 · 智能归档 + 重复发票检测设置 5 路由从 app.py 抽到 settings_routes.py。

锁定(防搬迁回归):
  1. router 注册的 5 个路由 path+method 契约不变(防丢路由 / 改 URL)
  2. app.py 通过 include_router 真挂上了(防漏挂)
  3. _check_archive_* 复用 route_helpers._plan_permissions(单一来源)· 扁平化下放行
  4. 3 个 payload model 字段契约不变
"""

import unittest

import route_helpers
from settings_routes import (
    ArchivePreviewRequest,
    ArchiveSettingsPayload,
    DupCheckSettingPayload,
    ErpPushModePayload,
    _check_archive_access,
    _check_archive_customize,
    router,
)


class SettingsRoutesContractTests(unittest.TestCase):
    def test_router_registers_expected_routes(self):
        """路由 path+method 契约 · 防搬迁丢路由 / 改 URL"""
        got = set()
        for r in router.routes:
            for m in getattr(r, "methods", set()) or set():
                if m in ("GET", "POST", "PUT"):
                    got.add((m, r.path))
        expected = {
            ("GET", "/api/archive/settings"),
            ("PUT", "/api/archive/settings"),
            ("POST", "/api/archive/rename-preview"),
            ("GET", "/api/settings/dup-check"),
            ("PUT", "/api/settings/dup-check"),
            # P1b · ERP 自动处理方式
            ("GET", "/api/settings/erp-push-mode"),
            ("PUT", "/api/settings/erp-push-mode"),
        }
        self.assertEqual(got, expected)

    def test_app_includes_settings_router(self):
        """防 include_router 漏挂 · app 必须能路由到 settings"""
        import app

        paths = {r.path for r in app.app.routes if hasattr(r, "path")}
        self.assertIn("/api/archive/settings", paths)
        self.assertIn("/api/settings/dup-check", paths)
        self.assertIn("/api/archive/rename-preview", paths)

    def test_archive_checks_use_plan_permissions(self):
        """_check_archive_* 依赖 route_helpers._plan_permissions · 扁平化下放行(不抛)"""
        self.assertIs(
            _check_archive_access.__globals__["_plan_permissions"],
            route_helpers._plan_permissions,
        )
        self.assertIsNone(_check_archive_access({"id": "u1", "plan": "free"}))
        self.assertIsNone(_check_archive_customize({"id": "u1", "plan": "free"}))

    def test_payload_model_fields(self):
        """3 个 payload model 字段契约 + 默认值"""
        a = ArchiveSettingsPayload()
        self.assertEqual(a.name_template, [])
        self.assertEqual(a.folder_strategy, "by_month_seller")
        p = ArchivePreviewRequest()
        self.assertEqual(p.merged_fields, {})
        self.assertIsNone(p.name_template)
        self.assertEqual(set(DupCheckSettingPayload.model_fields.keys()), {"enabled"})
        self.assertEqual(set(ErpPushModePayload.model_fields.keys()), {"mode"})

    def test_erp_push_mode_dal_validates(self):
        """P1b · get/set_erp_push_mode 默认 smart + 拒非法值(纯逻辑 · 不打 DB)"""
        import db

        self.assertEqual(db.ERP_PUSH_MODES, ("smart", "fixed", "ocr_only"))
        # 非法 mode → set 拒写(返 False)· 不触 DB
        self.assertFalse(db.set_erp_push_mode("u1", "garbage"))


if __name__ == "__main__":
    unittest.main()
