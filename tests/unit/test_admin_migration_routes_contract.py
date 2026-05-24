# -*- coding: utf-8 -*-
"""
REFACTOR-B1 守门测试 · 超管迁移/RLS 7 路由从 app.py 抽到 admin_migration_routes.py。

锁定(防搬迁回归):
  1. router 注册的 7 个路由 path+method 契约不变(防丢路由 / 改 URL / 改 method)
  2. app.py 通过 include_router 真挂上了(防漏挂)
  3. 全部路由复用 route_helpers._require_super_admin 单一来源(防超管闸丢失)
"""

import unittest

import admin_migration_routes
import route_helpers
from admin_migration_routes import router


class AdminMigrationRoutesContractTests(unittest.TestCase):
    def test_router_registers_expected_routes(self):
        """路由 path+method 契约 · 防搬迁丢路由 / 改 URL / 改 method"""
        got = set()
        for r in router.routes:
            for m in getattr(r, "methods", set()) or set():
                if m in ("GET", "POST", "PUT", "DELETE", "PATCH"):
                    got.add((m, r.path))
        expected = {
            ("POST", "/api/admin/migration/dry_run"),
            ("POST", "/api/admin/migration/execute"),
            ("GET", "/api/admin/migration/orphan_list"),
            ("POST", "/api/admin/migration/fix_orphans"),
            ("GET", "/api/admin/rls/status"),
            ("POST", "/api/admin/rls/run_tests"),
            ("POST", "/api/admin/migration/backfill_tenant_ids"),
        }
        self.assertEqual(got, expected)

    def test_app_includes_admin_migration_router(self):
        """防 include_router 漏挂 · app 必须能路由到迁移/RLS"""
        import app

        paths = {r.path for r in app.app.routes if hasattr(r, "path")}
        self.assertIn("/api/admin/migration/dry_run", paths)
        self.assertIn("/api/admin/rls/status", paths)
        self.assertIn("/api/admin/migration/backfill_tenant_ids", paths)

    def test_super_admin_guard_single_source(self):
        """全部路由复用 route_helpers._require_super_admin 单一来源(防超管闸丢失)"""
        self.assertIs(
            admin_migration_routes._require_super_admin,
            route_helpers._require_super_admin,
        )


if __name__ == "__main__":
    unittest.main()
