# -*- coding: utf-8 -*-
"""
REFACTOR-B1 守门测试 · 操作/审计日志 4 路由从 app.py 抽到 admin_logs_routes.py。

锁定(防搬迁回归):
  1. router 注册的 4 个路由 path+method 契约不变(防丢路由 / 改 URL / 改 method)
  2. app.py 通过 include_router 真挂上了(防漏挂)
  3. /api/admin/logs* 复用 route_helpers._require_super_admin 单一来源(防超管闸丢失)
  4. /api/me/access_log* 用 auth.get_current_user_from_request 单一来源(防鉴权失踪)
  5. 同区相邻的 /api/admin/users.csv(属 admin users 组)仍留 app.py(防误搬)
"""

import unittest

import admin_logs_routes
import route_helpers
from admin_logs_routes import router


class AdminLogsRoutesContractTests(unittest.TestCase):
    def test_router_registers_expected_routes(self):
        """路由 path+method 契约 · 防搬迁丢路由 / 改 URL / 改 method"""
        got = set()
        for r in router.routes:
            for m in getattr(r, "methods", set()) or set():
                if m in ("GET", "POST", "PUT", "DELETE", "PATCH"):
                    got.add((m, r.path))
        expected = {
            ("GET", "/api/admin/logs"),
            ("GET", "/api/admin/logs.csv"),
            ("GET", "/api/me/access_log"),
            ("GET", "/api/me/access_log.csv"),
        }
        self.assertEqual(got, expected)

    def test_app_includes_admin_logs_router(self):
        """防 include_router 漏挂 · app 必须能路由到操作/审计日志"""
        import app

        paths = {r.path for r in app.app.routes if hasattr(r, "path")}
        self.assertIn("/api/admin/logs", paths)
        self.assertIn("/api/admin/logs.csv", paths)
        self.assertIn("/api/me/access_log", paths)
        self.assertIn("/api/me/access_log.csv", paths)

    def test_super_admin_guard_single_source(self):
        """/api/admin/logs* 复用 route_helpers._require_super_admin 单一来源"""
        self.assertIs(
            admin_logs_routes._require_super_admin,
            route_helpers._require_super_admin,
        )

    def test_auth_dependency_single_source(self):
        """/api/me/access_log* 用 auth.get_current_user_from_request 单一来源"""
        import auth

        self.assertIs(
            admin_logs_routes.get_current_user_from_request,
            auth.get_current_user_from_request,
        )

    def test_users_csv_not_in_admin_logs_router(self):
        """/api/admin/users.csv 属 admin users 组 · 不能跑进 admin_logs_router。
        REFACTOR-B1(2026-05-25):users.csv 已随 admin users 组抽到 admin_users_routes.py ·
        仍经 include 挂在 app 上 · 但绝不属于 admin_logs(操作/审计日志)组。"""
        import app

        paths = {r.path for r in app.app.routes if hasattr(r, "path")}
        self.assertIn("/api/admin/users.csv", paths)  # 仍挂载(经 admin_users_router)
        log_paths = {r.path for r in router.routes if hasattr(r, "path")}
        self.assertNotIn("/api/admin/users.csv", log_paths)  # 不在 admin_logs 组


if __name__ == "__main__":
    unittest.main()
