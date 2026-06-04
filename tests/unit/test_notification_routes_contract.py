# -*- coding: utf-8 -*-
"""
REFACTOR-B1 守门测试 · 通知规则路由从 app.py 抽到 notification_routes.py。

锁定三件事(防搬迁回归):
  1. router 注册的 6 个路由 path+method 契约不变(防丢路由 / 改 URL)
  2. app.py 通过 include_router 真挂上了(防漏挂)
  3. _validate_template_params 对 exception_high 无必填参数(金额阈值已并入金额上限客户规矩)
"""

import unittest

from routes.notification_routes import _validate_template_params, router


class NotificationRoutesContractTests(unittest.TestCase):
    def test_router_registers_expected_routes(self):
        """路由 path+method 契约 · 防搬迁丢路由 / 改 URL"""
        got = set()
        for r in router.routes:
            for m in getattr(r, "methods", set()) or set():
                if m in ("GET", "POST", "PATCH", "DELETE"):
                    got.add((m, r.path))
        expected = {
            ("GET", "/api/notifications/rules"),
            ("POST", "/api/notifications/rules"),
            ("PATCH", "/api/notifications/rules/{rule_id}"),
            ("DELETE", "/api/notifications/rules/{rule_id}"),
            ("POST", "/api/notifications/rules/{rule_id}/test"),
            ("GET", "/api/notifications/logs"),
        }
        self.assertEqual(got, expected)

    def test_app_includes_notification_router(self):
        """防 include_router 漏挂 · app 必须能路由到 notifications"""
        import app

        paths = {r.path for r in app.app.routes if hasattr(r, "path")}
        self.assertIn("/api/notifications/rules", paths)
        self.assertIn("/api/notifications/logs", paths)

    def test_validate_params_no_required(self):
        """通知模板无必填参数 · 空 params 直接通过(金额阈值已并入金额上限客户规矩)"""
        self.assertEqual(_validate_template_params({}), {})
        self.assertEqual(_validate_template_params(None), {})


if __name__ == "__main__":
    unittest.main()
