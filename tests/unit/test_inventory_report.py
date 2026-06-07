# -*- coding: utf-8 -*-
"""库存报表聚合纯逻辑守门测试(POS 项目 · C1)。

不连库:进销存装配 + 周转率/周转天数派生(含平均库存为 0 不除零)、近效期分桶形状、量/钱
字符串化。真聚合 SQL(笛卡尔积防护)由 _e2e_c1 真库覆盖。"""

import unittest
from datetime import date
from decimal import Decimal

from services.inventory import reports


class _Cur:
    def __init__(self, scripted):
        self._scripted = list(scripted)
        self._cur = None
        self.queries = []

    def execute(self, sql, params=None):
        self.queries.append((sql, params))
        self._cur = self._scripted.pop(0)

    def fetchone(self):
        return self._cur[0]

    def fetchall(self):
        return self._cur[1]


class FormatTests(unittest.TestCase):
    def test_money_qty(self):
        self.assertEqual(reports._money(Decimal("840")), "840.00")
        self.assertEqual(reports._qty("30"), "30.000")
        self.assertEqual(reports._qty(None), "0.000")


class MovementTests(unittest.TestCase):
    def _row(self, opening, qin, qout, sold, closing):
        return {
            "product_id": "p1",
            "name_th": "ยา",
            "name_en": "Med",
            "name_zh": "药",
            "base_unit": "粒",
            "opening": opening,
            "qin": qin,
            "qout": qout,
            "sold": sold,
            "closing": closing,
        }

    def test_balance_and_turnover_derivation(self):
        # 期初 100,入 50,出 30,售 28,期末 120;平均库存=(100+120)/2=110;周转=28/110=0.2545→0.25
        cur = _Cur([(None, [self._row(100, 50, 30, 28, 120)]), ({}, None)])
        out = reports.inventory_report(
            cur,
            tenant_id="t",
            workspace_client_id=9,
            date_from=date(2026, 6, 1),
            date_to=date(2026, 6, 7),
        )
        m = out["movement"][0]
        self.assertEqual(m["opening"], "100.000")
        self.assertEqual(m["out"], "30.000")
        self.assertEqual(m["closing"], "120.000")
        self.assertEqual(m["turnover_ratio"], "0.25")
        self.assertEqual(m["name"], {"th": "ยา", "en": "Med", "zh": "药"})
        self.assertEqual(out["period"], {"from": "2026-06-01", "to": "2026-06-07"})

    def test_zero_avg_balance_no_divide(self):
        # 期初 0、期末 0 → 平均库存 0 → 周转率/天数 None(不除零)
        cur = _Cur([(None, [self._row(0, 0, 0, 0, 0)]), ({}, None)])
        out = reports.inventory_report(
            cur,
            tenant_id="t",
            workspace_client_id=9,
            date_from=date(2026, 6, 1),
            date_to=date(2026, 6, 7),
        )
        m = out["movement"][0]
        self.assertIsNone(m["turnover_ratio"])
        self.assertIsNone(m["days_on_hand"])


class NearExpiryTests(unittest.TestCase):
    def test_buckets_and_value(self):
        summary = {
            "expired_batches": 1,
            "expired_qty": Decimal("5"),
            "d7_batches": 2,
            "d7_qty": Decimal("12"),
            "window_batches": 4,
            "window_qty": Decimal("30"),
            "value_at_risk": Decimal("840"),
        }
        cur = _Cur([(None, []), (summary, None)])
        out = reports.inventory_report(
            cur,
            tenant_id="t",
            workspace_client_id=9,
            date_from=date(2026, 6, 1),
            date_to=date(2026, 6, 7),
            near_expiry_days=30,
        )
        ne = out["near_expiry"]
        self.assertEqual(ne["value_at_risk"], "840.00")
        labels = [b["label"] for b in ne["buckets"]]
        self.assertEqual(labels, ["expired", "le_7d", "le_30d"])
        self.assertEqual(ne["buckets"][0], {"label": "expired", "batches": 1, "qty": "5.000"})


if __name__ == "__main__":
    unittest.main()
