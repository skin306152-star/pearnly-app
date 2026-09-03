# -*- coding: utf-8 -*-
"""POS 成本可见性：授权后端投影，未授权不查询也不下发。"""

import unittest
from decimal import Decimal
from pathlib import Path
import re
from unittest.mock import patch

from services.inventory import queries as inventory_queries
from services.pos import catalog


class FakeCursor:
    def __init__(self, *, rows=None, ones=None):
        self.calls = []
        self._rows = list(rows or [])
        self._ones = list(ones or [])

    def execute(self, sql, params=None):
        self.calls.append((sql, params))

    def fetchall(self):
        return self._rows

    def fetchone(self):
        return self._ones.pop(0) if self._ones else None


def product_row():
    return {
        "id": "00000000-0000-0000-0000-000000000001",
        "name_th": "น้ำ",
        "name_en": "Water",
        "name_zh": "水",
        "category_id": 1,
        "barcode": "8850000000001",
        "base_unit": "瓶",
        "image_url": None,
        "vat_applicable": True,
        "track_batch": False,
        "is_weighed": False,
        "unit_price": Decimal("10.00"),
    }


class AverageCostsByProductTests(unittest.TestCase):
    def test_uses_inventory_cost_precedence_and_tenant_scope(self):
        pid = "00000000-0000-0000-0000-000000000001"
        cur = FakeCursor(rows=[{"product_id": pid, "avg_cost": Decimal("6.25")}])

        result = inventory_queries.average_costs_by_product(
            cur,
            tenant_id="tenant-1",
            workspace_client_id=9,
            product_ids=[pid],
        )

        self.assertEqual(result, {pid: Decimal("6.25")})
        sql, params = cur.calls[0]
        self.assertIn("COALESCE(b.avg_cost, w.wac, p.default_cost)", sql)
        self.assertIn("AVG(unit_cost)", sql)
        self.assertIn("SUM(qty_delta * unit_cost) / NULLIF(SUM(qty_delta), 0)", sql)
        self.assertIn("txn_type = 'purchase_in'", sql)
        self.assertIn("p.tenant_id = %s AND p.workspace_client_id = %s", sql)
        self.assertEqual(params, ("tenant-1", 9, "tenant-1", 9, "tenant-1", 9, [pid]))

    def test_empty_product_list_skips_query(self):
        cur = FakeCursor()
        result = inventory_queries.average_costs_by_product(
            cur, tenant_id="tenant-1", workspace_client_id=9, product_ids=[]
        )
        self.assertEqual(result, {})
        self.assertEqual(cur.calls, [])


class CatalogCostVisibilityTests(unittest.TestCase):
    @patch("services.pos.catalog.inv_queries.average_costs_by_product")
    @patch("services.pos.catalog.caps_svc.operator_caps")
    @patch("services.pos.catalog._stock_by_product")
    @patch("services.pos.catalog._units_by_product")
    def test_authorized_list_includes_average_cost(
        self, units_by_product, stock_by_product, operator_caps, average_costs
    ):
        row = product_row()
        cur = FakeCursor(rows=[row])
        units_by_product.return_value = {}
        stock_by_product.return_value = {"qty": {}, "near": set()}
        operator_caps.return_value = {"cost_visible": True}
        average_costs.return_value = {row["id"]: Decimal("6.25")}

        out = catalog.list_products(
            cur,
            tenant_id="tenant-1",
            workspace_client_id=9,
            operator={"role": "cashier", "cashier_id": "cashier-1"},
        )

        self.assertEqual(out["items"][0]["avg_cost"], "6.25")
        average_costs.assert_called_once_with(
            cur,
            tenant_id="tenant-1",
            workspace_client_id=9,
            product_ids=[row["id"]],
        )

    @patch("services.pos.catalog.inv_queries.average_costs_by_product")
    @patch("services.pos.catalog.caps_svc.operator_caps")
    @patch("services.pos.catalog._stock_by_product")
    @patch("services.pos.catalog._units_by_product")
    def test_unauthorized_list_neither_queries_nor_exposes_cost(
        self, units_by_product, stock_by_product, operator_caps, average_costs
    ):
        cur = FakeCursor(rows=[product_row()])
        units_by_product.return_value = {}
        stock_by_product.return_value = {"qty": {}, "near": set()}
        operator_caps.return_value = {"cost_visible": False}

        out = catalog.list_products(
            cur,
            tenant_id="tenant-1",
            workspace_client_id=9,
            operator={"role": "cashier", "cashier_id": "cashier-1"},
        )

        self.assertIsNone(out["items"][0]["avg_cost"])
        average_costs.assert_not_called()

    @patch("services.pos.catalog.inv_queries.average_costs_by_product")
    @patch("services.pos.catalog.caps_svc.operator_caps")
    @patch("services.pos.catalog._stock_by_product")
    @patch("services.pos.catalog._units_by_product")
    def test_authorized_barcode_lookup_includes_average_cost(
        self, units_by_product, stock_by_product, operator_caps, average_costs
    ):
        row = product_row()
        cur = FakeCursor(ones=[None, row])
        units_by_product.return_value = {}
        stock_by_product.return_value = {"qty": {}, "near": set()}
        operator_caps.return_value = {"cost_visible": True}
        average_costs.return_value = {row["id"]: Decimal("6.25")}

        item = catalog.product_by_barcode(
            cur,
            tenant_id="tenant-1",
            workspace_client_id=9,
            code=row["barcode"],
            operator={"role": "cashier", "cashier_id": "cashier-1"},
        )

        self.assertEqual(item["avg_cost"], "6.25")
        self.assertEqual(item["matched_unit"], "瓶")

    @patch("services.pos.catalog.inv_queries.average_costs_by_product")
    @patch("services.pos.catalog.caps_svc.operator_caps")
    @patch("services.pos.catalog._stock_by_product")
    @patch("services.pos.catalog._units_by_product")
    def test_unauthorized_barcode_lookup_does_not_query_cost(
        self, units_by_product, stock_by_product, operator_caps, average_costs
    ):
        row = product_row()
        cur = FakeCursor(ones=[None, row])
        units_by_product.return_value = {}
        stock_by_product.return_value = {"qty": {}, "near": set()}
        operator_caps.return_value = {"cost_visible": False}

        item = catalog.product_by_barcode(
            cur,
            tenant_id="tenant-1",
            workspace_client_id=9,
            code=row["barcode"],
            operator={"role": "cashier", "cashier_id": "cashier-1"},
        )

        self.assertIsNone(item["avg_cost"])
        average_costs.assert_not_called()

    def test_routes_forward_authenticated_operator(self):
        source = Path("routes/pos_sales_routes.py").read_text(encoding="utf-8")
        for call in ("bootstrap", "list_products", "product_by_barcode"):
            self.assertRegex(
                source,
                re.compile(rf"catalog\.{call}\([^)]*operator=user", re.DOTALL),
            )


if __name__ == "__main__":
    unittest.main()
