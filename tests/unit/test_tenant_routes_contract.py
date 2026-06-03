# -*- coding: utf-8 -*-
"""
REFACTOR-B1 守门测试 · 租户管理 6 路由 + 3 model 从 app.py 抽到 tenant_routes.py。

锁定(防搬迁回归):
  1. router 注册的 6 个路由 path+method 契约不变(防丢路由 / 改 URL / 改 method)
  2. app.py 通过 include_router 真挂上了(防漏挂)
  3. 5 个 admin 路由复用 route_helpers._require_super_admin 单一来源(防超管闸丢失)
  4. 3 个 tenant model 字段 + 校验契约不变
  5. 中间夹的 /api/history/{id}/assign_client(属 history 组)仍留在 app.py(防误搬)
"""

import unittest

from core import route_helpers
from routes import tenant_routes
from routes.tenant_routes import (
    AdminCreateTenantRequest,
    AdminUpdateTenantQuotaRequest,
    AdminUpdateTenantStatusRequest,
    router,
)


class TenantRoutesContractTests(unittest.TestCase):
    def test_router_registers_expected_routes(self):
        """路由 path+method 契约 · 防搬迁丢路由 / 改 URL / 改 method"""
        got = set()
        for r in router.routes:
            for m in getattr(r, "methods", set()) or set():
                if m in ("GET", "POST", "PUT", "DELETE", "PATCH"):
                    got.add((m, r.path))
        expected = {
            ("GET", "/api/admin/tenants"),
            ("POST", "/api/admin/tenants"),
            ("PATCH", "/api/admin/tenants/{tenant_id}/quota"),
            ("PATCH", "/api/admin/tenants/{tenant_id}/status"),
            ("GET", "/api/admin/tenants/{tenant_id}/summary"),
            ("GET", "/api/me/tenant-usage"),
        }
        self.assertEqual(got, expected)

    def test_app_includes_tenant_router(self):
        """防 include_router 漏挂 · app 必须能路由到租户管理"""
        import app

        paths = {r.path for r in app.app.routes if hasattr(r, "path")}
        self.assertIn("/api/admin/tenants", paths)
        self.assertIn("/api/admin/tenants/{tenant_id}/summary", paths)
        self.assertIn("/api/me/tenant-usage", paths)

    def test_super_admin_guard_single_source(self):
        """admin 路由复用 route_helpers._require_super_admin 单一来源(防超管闸丢失)"""
        self.assertIs(
            tenant_routes._require_super_admin,
            route_helpers._require_super_admin,
        )

    def test_tenant_model_fields(self):
        """3 个 model 字段 + 校验契约不变"""
        c = AdminCreateTenantRequest(name="acme")
        self.assertEqual(c.tenant_type, "shared_api")
        self.assertEqual(c.monthly_quota, 100)
        self.assertIsNone(c.notes)
        with self.assertRaises(Exception):
            AdminUpdateTenantQuotaRequest(monthly_quota=-1)  # ge=0
        with self.assertRaises(Exception):
            AdminUpdateTenantStatusRequest(status="bogus")  # pattern

    def test_shared_models_single_source(self):
        """admin user quota/status 路由复用的 2 model 是 tenant_routes 的(单一来源)。
        REFACTOR-B1(2026-05-25):该 2 路由随 admin 组搬到 admin_users_routes · 断言跟到新消费者。"""
        from routes import admin_users_routes

        self.assertIs(
            admin_users_routes.AdminUpdateTenantQuotaRequest, AdminUpdateTenantQuotaRequest
        )
        self.assertIs(
            admin_users_routes.AdminUpdateTenantStatusRequest, AdminUpdateTenantStatusRequest
        )

    def test_assign_client_not_in_tenant_router(self):
        """history 路由 assign_client 不能跑进 tenant_routes。
        REFACTOR-B1(2026-05-25):assign_client 已并入 history_routes(属 history 组)·
        仍经 include 挂在 app 上 · 但绝不属于 tenant 组。"""
        import app

        paths = {r.path for r in app.app.routes if hasattr(r, "path")}
        self.assertIn("/api/history/{history_id}/assign_client", paths)  # 仍挂载(经 history_router)
        tenant_paths = {r.path for r in router.routes if hasattr(r, "path")}
        self.assertNotIn("/api/history/{history_id}/assign_client", tenant_paths)


if __name__ == "__main__":
    unittest.main()
