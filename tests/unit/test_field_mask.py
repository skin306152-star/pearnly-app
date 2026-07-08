# -*- coding: utf-8 -*-
"""敏感字段遮蔽守门(G4):cost_visible 读快照判定 + 库存读侧成本列遮蔽。

无 field.cost.view 码 → 均价/库存货值/近效期风险货值一律 None;有码原样。超管短路无快照=可见。
"""

import unittest
from datetime import date
from decimal import Decimal
from types import SimpleNamespace

from services.authz import field_mask
from services.authz.resolver import Authz
from services.inventory import queries, reports


def _req(authz):
    state = SimpleNamespace()
    if authz is not None:
        state._authz_snapshot = ("u1", authz)
    return SimpleNamespace(state=state)


class CostVisibleTests(unittest.TestCase):
    def test_visible_with_code(self):
        authz = Authz(role_key="accountant", permissions=frozenset({"field.cost.view"}))
        self.assertTrue(field_mask.cost_visible(_req(authz)))

    def test_hidden_without_code(self):
        authz = Authz(role_key="custom:floor", permissions=frozenset({"inv.report.view"}))
        self.assertFalse(field_mask.cost_visible(_req(authz)))

    def test_no_snapshot_means_super_admin_visible(self):
        self.assertTrue(field_mask.cost_visible(_req(None)))

    def test_mask_fields_helper(self):
        row = {"avg_cost": 9.5, "qty": 3}
        field_mask.mask_fields(row, ["avg_cost"], visible=False)
        self.assertIsNone(row["avg_cost"])
        self.assertEqual(row["qty"], 3)
        # visible=True 不动
        row2 = {"avg_cost": 9.5}
        field_mask.mask_fields(row2, ["avg_cost"], visible=True)
        self.assertEqual(row2["avg_cost"], 9.5)


class _FakeCursor:
    def __init__(self, alls):
        self._alls = list(alls)

    def execute(self, sql, params=None):
        pass

    def fetchall(self):
        return self._alls.pop(0) if self._alls else []

    def fetchone(self):
        return self._alls.pop(0) if self._alls else {}


def _prow(qty, avg_cost):
    return {
        "product_id": "p1",
        "name_th": "ยา",
        "name_en": None,
        "name_zh": None,
        "image_url": None,
        "barcode": None,
        "base_unit": "เม็ด",
        "min_stock": None,
        "default_cost": None,
        "track_batch": False,
        "qty_on_hand": Decimal(str(qty)),
        "avg_cost": Decimal(str(avg_cost)),
    }


class StockOverviewMaskTests(unittest.TestCase):
    def test_cost_columns_nulled_when_masked(self):
        cur = _FakeCursor([[_prow(10, 2)], []])
        out = queries.stock_overview(cur, tenant_id="t", workspace_client_id=9, mask_cost=True)
        self.assertIsNone(out["items"][0]["avg_cost"])
        self.assertIsNone(out["summary"]["stock_value"])
        # 非成本列照常
        self.assertEqual(out["items"][0]["qty_on_hand"], 10.0)
        self.assertEqual(out["summary"]["sku_count"], 1)

    def test_cost_columns_present_when_visible(self):
        cur = _FakeCursor([[_prow(10, 2)], []])
        out = queries.stock_overview(cur, tenant_id="t", workspace_client_id=9, mask_cost=False)
        self.assertEqual(out["items"][0]["avg_cost"], 2.0)
        self.assertEqual(out["summary"]["stock_value"], 20.0)


class InventoryReportMaskTests(unittest.TestCase):
    def _run(self, mask):
        cur = _FakeCursor([[], {"expired_batches": 0, "value_at_risk": Decimal("500")}])
        return reports.inventory_report(
            cur,
            tenant_id="t",
            workspace_client_id=9,
            date_from=date(2026, 6, 1),
            date_to=date(2026, 6, 7),
            mask_cost=mask,
        )

    def test_value_at_risk_masked(self):
        self.assertIsNone(self._run(True)["near_expiry"]["value_at_risk"])

    def test_value_at_risk_visible(self):
        self.assertEqual(self._run(False)["near_expiry"]["value_at_risk"], "500.00")


if __name__ == "__main__":
    unittest.main()
