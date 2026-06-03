# -*- coding: utf-8 -*-
"""
REFACTOR-B1 守门测试 · 超管用户/员工管理 15 路由从 app.py 抽到 admin_users_routes.py。

锁定(防搬迁回归):
  1. router 注册的 15 个路由 path+method 契约不变(防丢路由 / 改 URL)
  2. app.py 通过 include_router 真挂上了(含 users.csv)
  3. _require_super_admin / _log_op 复用 route_helpers(单一来源)
  4. 复用 model 单一来源:AdminUpdateTenantQuota/Status from tenant_routes ·
     EmployeeToggleRequest from team_routes(不在本模块重复定义)
  5. 本模块自有 model 字段契约(AdminCreateUserRequest / CascadeDeleteRequest)
"""

import unittest

from core import route_helpers
from routes import tenant_routes
from routes import team_routes
from routes import admin_users_routes
from routes.admin_users_routes import (
    AdminCreateUserRequest,
    CascadeDeleteRequest,
    router,
)


class AdminUsersRoutesContractTests(unittest.TestCase):
    def test_router_registers_expected_routes(self):
        """路由 path+method 契约 · 防搬迁丢路由 / 改 URL"""
        got = set()
        for r in router.routes:
            for m in getattr(r, "methods", set()) or set():
                got.add((m, r.path))
        expected = {
            ("GET", "/api/admin/users"),
            ("GET", "/api/admin/employees"),
            ("POST", "/api/admin/users"),
            ("GET", "/api/admin/users/{user_id}"),
            ("PATCH", "/api/admin/users/{user_id}/quota"),
            ("PATCH", "/api/admin/users/{user_id}/status"),
            ("POST", "/api/admin/users/{user_id}/delete"),
            ("POST", "/api/admin/users/{user_id}/reset-password"),
            ("GET", "/api/admin/users/{user_id}/logs"),
            ("GET", "/api/admin/users.csv"),
            ("PATCH", "/api/admin/employees/{employee_id}/active"),
            ("POST", "/api/admin/employees/{employee_id}/reset-password"),
            ("DELETE", "/api/admin/employees/{employee_id}"),
            ("GET", "/api/admin/users/{user_id}/cascade-preview"),
            ("POST", "/api/admin/users/{user_id}/cascade-delete"),
        }
        self.assertEqual(got, expected)
        self.assertEqual(len(router.routes), 15)

    def test_app_includes_admin_users_router(self):
        """防 include_router 漏挂 · app 必须能路由到超管用户/员工(含 users.csv)"""
        import app

        paths = {r.path for r in app.app.routes if hasattr(r, "path")}
        for p in (
            "/api/admin/users",
            "/api/admin/employees",
            "/api/admin/users.csv",
            "/api/admin/users/{user_id}/cascade-delete",
        ):
            self.assertIn(p, paths)

    def test_helpers_single_source(self):
        """_require_super_admin / _log_op 复用 route_helpers · 单一来源"""
        g = admin_users_routes.__dict__
        self.assertIs(g["_require_super_admin"], route_helpers._require_super_admin)
        self.assertIs(g["_log_op"], route_helpers._log_op)

    def test_reused_models_single_source(self):
        """复用 model 单一来源 · 不在本模块重复定义"""
        self.assertIs(
            admin_users_routes.AdminUpdateTenantQuotaRequest,
            tenant_routes.AdminUpdateTenantQuotaRequest,
        )
        self.assertIs(
            admin_users_routes.AdminUpdateTenantStatusRequest,
            tenant_routes.AdminUpdateTenantStatusRequest,
        )
        self.assertIs(admin_users_routes.EmployeeToggleRequest, team_routes.EmployeeToggleRequest)

    def test_own_model_fields(self):
        """本模块自有 model 字段契约"""
        m = AdminCreateUserRequest(username="abc", password="secret1", company_name="X")
        self.assertEqual(m.tenant_type, "shared_api")
        self.assertEqual(m.monthly_quota, 100)
        self.assertEqual(
            set(CascadeDeleteRequest.model_fields.keys()),
            {"confirm_password", "confirm_username"},
        )


if __name__ == "__main__":
    unittest.main()
