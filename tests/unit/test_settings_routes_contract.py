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


if __name__ == "__main__":
    unittest.main()
