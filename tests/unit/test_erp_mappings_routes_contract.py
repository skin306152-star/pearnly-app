# -*- coding: utf-8 -*-
"""
REFACTOR-B1 守门测试 · ERP 映射 12 路由从 app.py 抽到 erp_mappings_routes.py。

锁定(防搬迁回归):
  1. router 注册的 12 个路由 path+method 契约不变(防丢路由 / 改 URL)
  2. app.py 通过 include_router 真挂上了(防漏挂)
  3. _require_owner_or_super 复用 route_helpers 同一份对象(单一来源 · 不许各自拷贝)
  4. ErpProductMappingReq 字段契约不变
"""

import unittest

from erp_mappings_routes import ErpProductMappingReq, _require_owner_or_super, router


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

    def test_require_owner_or_super_single_source(self):
        """复用 route_helpers 同一份对象 · 不许各自拷贝漂移"""
        import route_helpers

        self.assertIs(_require_owner_or_super, route_helpers._require_owner_or_super)

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
