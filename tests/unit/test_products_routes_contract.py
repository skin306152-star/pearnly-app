# -*- coding: utf-8 -*-
"""销项 PO-2 · 商品主数据守门测试(路由契约 + DAL 行为)。

锁定:
  1. router 注册 6 条路由(list/create/lookup/get/update/delete)· path+method 契约
  2. app.py include_router 真挂上
  3. DAL 每条语句都按 tenant_id 隔离 + 全参数化(占位符,值不入 SQL 串)
  4. 软删走 is_active=FALSE 不物删;lookup 键经白名单(拒未知键防注入)
"""

import unittest
from decimal import Decimal

from routes.products_routes import router
from services.sales import products as dal

EXPECTED = {
    ("GET", "/api/sales/products"),
    ("POST", "/api/sales/products"),
    ("GET", "/api/sales/products/lookup"),
    ("POST", "/api/sales/products/import"),
    ("GET", "/api/sales/products/{product_id}"),
    ("PATCH", "/api/sales/products/{product_id}"),
    ("DELETE", "/api/sales/products/{product_id}"),
}

ROW = {
    "id": "11111111-1111-1111-1111-111111111111",
    "tenant_id": "t-1",
    "code": "P01",
    "barcode": None,
    "qr_payload": None,
    "name_th": "น้ำ",
    "name_en": None,
    "name_zh": None,
    "unit": None,
    "unit_price": Decimal("50.00"),
    "vat_applicable": True,
    "image_url": None,
    "category_id": None,
    "is_active": True,
    "created_at": None,
    "updated_at": None,
}


class FakeCursor:
    def __init__(self, fetchone=None, fetchall=None, rowcount=1):
        self.calls = []
        self._fetchone = fetchone
        self._fetchall = fetchall or []
        self.rowcount = rowcount

    def execute(self, sql, params=None):
        self.calls.append((sql, params))

    def fetchone(self):
        return self._fetchone

    def fetchall(self):
        return self._fetchall

    @property
    def last_sql(self):
        return self.calls[-1][0]

    @property
    def last_params(self):
        return self.calls[-1][1]


class ProductsRoutesContractTests(unittest.TestCase):
    def test_router_registers_expected_routes(self):
        got = set()
        for r in router.routes:
            for m in getattr(r, "methods", set()) or set():
                if m in ("GET", "POST", "PATCH", "DELETE"):
                    got.add((m, r.path))
        self.assertEqual(got, EXPECTED)

    def test_app_includes_products_router(self):
        import app

        paths = {r.path for r in app.app.routes if hasattr(r, "path")}
        for _m, p in EXPECTED:
            self.assertIn(p, paths, f"products route missing from app: {p}")


class ProductsDalTenantIsolationTests(unittest.TestCase):
    def test_every_statement_scopes_to_tenant(self):
        for fn in (
            lambda c: dal.get_product(c, tenant_id="t-1", product_id="p"),
            lambda c: dal.list_products(c, tenant_id="t-1"),
            lambda c: dal.list_products(c, tenant_id="t-1", include_inactive=True, query="x"),
            lambda c: dal.update_product(c, tenant_id="t-1", product_id="p", fields={"unit": "ea"}),
            lambda c: dal.deactivate_product(c, tenant_id="t-1", product_id="p"),
            lambda c: dal.find_by(c, tenant_id="t-1", key="code", value="P01"),
        ):
            cur = FakeCursor(fetchone=ROW)
            fn(cur)
            self.assertTrue(cur.calls, "statement must execute")
            self.assertIn("tenant_id = %s", cur.last_sql)
            self.assertIn("t-1", cur.last_params)

    def test_create_inserts_tenant_and_parameterizes(self):
        cur = FakeCursor(fetchone=ROW)
        dal.create_product(cur, tenant_id="t-1", fields={"name_th": "น้ำ", "unit_price": 50})
        self.assertIn("INSERT INTO products", cur.last_sql)
        self.assertIn("RETURNING", cur.last_sql)
        self.assertEqual(cur.last_params[0], "t-1")
        # 金额走 Decimal(不 float)
        self.assertIn(Decimal("50"), cur.last_params)
        # 值经占位符(不把业务值拼进 SQL 串)
        self.assertNotIn("น้ำ", cur.last_sql)

    def test_list_active_filter_toggles(self):
        cur = FakeCursor(fetchall=[ROW])
        dal.list_products(cur, tenant_id="t-1")
        self.assertIn("is_active = TRUE", cur.last_sql)
        cur2 = FakeCursor(fetchall=[ROW])
        dal.list_products(cur2, tenant_id="t-1", include_inactive=True)
        self.assertNotIn("is_active = TRUE", cur2.last_sql)

    def test_deactivate_is_soft_delete(self):
        cur = FakeCursor(rowcount=1)
        ok = dal.deactivate_product(cur, tenant_id="t-1", product_id="p")
        self.assertTrue(ok)
        self.assertIn("is_active = FALSE", cur.last_sql)
        self.assertNotIn("DELETE", cur.last_sql)

    def test_lookup_rejects_unknown_key(self):
        cur = FakeCursor(fetchone=ROW)
        self.assertIsNone(dal.find_by(cur, tenant_id="t-1", key="evil; DROP", value="x"))
        self.assertFalse(cur.calls, "unknown lookup key must not hit the DB")

    def test_lookup_uses_qr_payload_column(self):
        cur = FakeCursor(fetchone=ROW)
        dal.find_by(cur, tenant_id="t-1", key="qr", value="Q1")
        self.assertIn("qr_payload = %s", cur.last_sql)


if __name__ == "__main__":
    unittest.main()
