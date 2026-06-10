# -*- coding: utf-8 -*-
"""
REFACTOR-B1 守门测试 · ERP 映射 12 路由从 app.py 抽到 erp_mappings_routes.py。

锁定(防搬迁回归 + 权限批2):
  1. router 注册的 12 个路由 path+method 契约不变(防丢路由 / 改 URL)
  2. app.py 通过 include_router 真挂上了(防漏挂)
  3. 权限批2:6 个写路由守门换统一执行点 require_perm(request, "settings.org.edit")·
     复用 services/authz/deps 同一份对象 · 旧门 _require_owner_or_super 不许复活
  4. 读路由仍用 auth.get_current_user_from_request 单一来源(防鉴权失踪)
  5. ErpProductMappingReq 字段契约不变
"""

import inspect
import unittest

from routes.erp_mappings_routes import ErpProductMappingReq, router


class ErpMappingsRoutesContractTests(unittest.TestCase):
    def test_router_registers_expected_routes(self):
        """路由 path+method 契约 · 防搬迁丢路由 / 改 URL"""
        got = set()
        for r in router.routes:
            for m in getattr(r, "methods", set()) or set():
                if m in ("GET", "POST", "PATCH", "DELETE"):
                    got.add((m, r.path))
        expected = {
            ("GET", "/api/erp/mappings/clients"),
            ("POST", "/api/erp/mappings/clients"),
            ("DELETE", "/api/erp/mappings/clients/{mapping_id}"),
            ("GET", "/api/erp/mappings/accounts"),
            ("POST", "/api/erp/mappings/accounts"),
            ("DELETE", "/api/erp/mappings/accounts/{mapping_id}"),
            ("GET", "/api/erp/mappings/taxes"),
            ("POST", "/api/erp/mappings/taxes"),
            ("DELETE", "/api/erp/mappings/taxes/{mapping_id}"),
            ("GET", "/api/erp/mappings/products"),
            ("POST", "/api/erp/mappings/products"),
            ("DELETE", "/api/erp/mappings/products/{mapping_id}"),
        }
        self.assertEqual(got, expected)

    def test_app_includes_erp_mappings_router(self):
        """防 include_router 漏挂 · app 必须能路由到 erp mappings"""
        import app

        paths = {r.path for r in app.app.routes if hasattr(r, "path")}
        self.assertIn("/api/erp/mappings/clients", paths)
        self.assertIn("/api/erp/mappings/products/{mapping_id}", paths)

    def test_write_routes_use_require_perm_settings_org_edit(self):
        """权限批2:6 个写路由(clients/accounts/taxes 的 POST+DELETE)守门统一执行点 ·
        require_perm 复用 services/authz/deps 同一份对象 · 码钉 settings.org.edit ·
        旧门 _require_owner_or_super 不许在本模块复活(products 写路由历史上就走普通鉴权)"""
        from routes import erp_mappings_routes
        from services.authz import deps

        self.assertIs(erp_mappings_routes.require_perm, deps.require_perm)
        self.assertFalse(hasattr(erp_mappings_routes, "_require_owner_or_super"))
        src = inspect.getsource(erp_mappings_routes)
        self.assertEqual(
            src.count('require_perm(request, "settings.org.edit")'),
            6,
            "写路由 require_perm(settings.org.edit) 接线数应为 6(clients/accounts/taxes 的 POST+DELETE)",
        )

    def test_read_routes_use_auth_single_source(self):
        """读路由仍用 auth.get_current_user_from_request 单一来源(防鉴权失踪)"""
        from core import auth
        from routes import erp_mappings_routes

        self.assertIs(
            erp_mappings_routes.get_current_user_from_request,
            auth.get_current_user_from_request,
        )

    def test_product_mapping_req_fields(self):
        """ErpProductMappingReq 字段契约 · erp_name/notes 可选默认 None"""
        self.assertEqual(
            set(ErpProductMappingReq.model_fields.keys()),
            {"erp_type", "item_name", "erp_code", "erp_name", "notes"},
        )
        m = ErpProductMappingReq(erp_type="xero", item_name="A", erp_code="X1")
        self.assertIsNone(m.erp_name)
        self.assertIsNone(m.notes)


if __name__ == "__main__":
    unittest.main()
