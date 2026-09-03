# -*- coding: utf-8 -*-
"""商品参考成本的权限、存取与销售成本兜底。"""

import unittest
from decimal import Decimal
from types import SimpleNamespace

from fastapi import HTTPException

from routes import products_routes
from services.authz.resolver import Authz
from services.inventory import costing


def _request(*permissions):
    authz = Authz(role_key="custom:test", permissions=frozenset(permissions))
    state = SimpleNamespace(_authz_snapshot=("u1", authz))
    return SimpleNamespace(state=state)


class ProductCostPermissionTests(unittest.TestCase):
    def test_output_masks_reference_cost_without_permission(self):
        row = {"id": "p1", "default_cost": Decimal("12.50")}
        self.assertIsNone(products_routes._out(row, cost_visible=False)["default_cost"])
        self.assertEqual(products_routes._out(row, cost_visible=True)["default_cost"], 12.5)

    def test_unauthorized_explicit_cost_write_is_rejected(self):
        req = products_routes.ProductUpdate(default_cost=12.5)
        with self.assertRaises(HTTPException) as caught:
            products_routes._guard_cost_write(req, _request("sales.product.manage"))
        self.assertEqual(caught.exception.status_code, 403)
        self.assertEqual(caught.exception.detail, "authz.forbidden")

    def test_ordinary_product_edit_without_cost_is_allowed(self):
        req = products_routes.ProductUpdate(name_th="น้ำ")
        products_routes._guard_cost_write(req, _request("sales.product.manage"))

    def test_authorized_zero_cost_is_kept_as_a_real_value(self):
        req = products_routes.ProductCreate(name_th="ของแถม", default_cost=0)
        products_routes._guard_cost_write(req, _request("sales.product.manage", "field.cost.view"))
        self.assertEqual(req.default_cost, 0)


class _Cursor:
    def __init__(self, row):
        self.row = row
        self.calls = []

    def execute(self, sql, params):
        self.calls.append((sql, params))

    def fetchone(self):
        return self.row


class ReferenceCostQueryTests(unittest.TestCase):
    def test_query_is_tenant_and_workspace_scoped(self):
        cur = _Cursor({"default_cost": Decimal("8.75")})
        value = costing.product_reference_cost(
            cur, tenant_id="t1", workspace_client_id=9, product_id="p1"
        )
        sql, params = cur.calls[0]
        self.assertIn("tenant_id = %s", sql)
        self.assertIn("workspace_client_id = %s", sql)
        self.assertEqual(params, ("t1", 9, "p1"))
        self.assertEqual(value, Decimal("8.75"))

    def test_missing_reference_cost_stays_unknown(self):
        cur = _Cursor({"default_cost": None})
        value = costing.product_reference_cost(
            cur, tenant_id="t1", workspace_client_id=9, product_id="p1"
        )
        self.assertIsNone(value)


if __name__ == "__main__":
    unittest.main()
