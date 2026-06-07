# -*- coding: utf-8 -*-
"""FEFO 批次分配守门测试(POS 项目 · PO-A3)。

锁定:按效期升序(SQL ORDER BY 已排)依次扣减到满足需求 · 不足时返回缺口 shortfall。
"""

import unittest
from decimal import Decimal

from services.inventory import fefo


class FakeCursor:
    def __init__(self, rows):
        self.calls = []
        self._rows = rows

    def execute(self, sql, params=None):
        self.calls.append((sql, params))

    def fetchall(self):
        return self._rows


def _rows(*pairs):
    # (batch_id, qty) · expiry 由 SQL 排序(此处按给定顺序模拟已排序结果)
    return [{"batch_id": b, "qty_on_hand": Decimal(str(q)), "expiry_date": None} for b, q in pairs]


class FefoTests(unittest.TestCase):
    def test_query_orders_by_expiry_asc(self):
        cur = FakeCursor(_rows(("b1", 5)))
        fefo.select_batches_for_outflow(
            cur, tenant_id="t", workspace_client_id=9, product_id="p", warehouse_id=1, qty_needed=1
        )
        self.assertIn("ORDER BY b.expiry_date ASC NULLS LAST", cur.calls[0][0])
        self.assertIn("s.qty_on_hand > 0", cur.calls[0][0])

    def test_allocates_from_earliest_until_satisfied(self):
        cur = FakeCursor(_rows(("near", 3), ("far", 10)))
        out = fefo.select_batches_for_outflow(
            cur, tenant_id="t", workspace_client_id=9, product_id="p", warehouse_id=1, qty_needed=7
        )
        self.assertEqual(
            out["allocations"],
            [
                {"batch_id": "near", "qty": Decimal("3")},
                {"batch_id": "far", "qty": Decimal("4")},
            ],
        )
        self.assertEqual(out["shortfall"], Decimal("0"))

    def test_stops_when_satisfied_within_first_batch(self):
        cur = FakeCursor(_rows(("near", 10), ("far", 10)))
        out = fefo.select_batches_for_outflow(
            cur, tenant_id="t", workspace_client_id=9, product_id="p", warehouse_id=1, qty_needed=4
        )
        self.assertEqual(out["allocations"], [{"batch_id": "near", "qty": Decimal("4")}])

    def test_shortfall_when_not_enough(self):
        cur = FakeCursor(_rows(("near", 2)))
        out = fefo.select_batches_for_outflow(
            cur, tenant_id="t", workspace_client_id=9, product_id="p", warehouse_id=1, qty_needed=5
        )
        self.assertEqual(out["allocations"], [{"batch_id": "near", "qty": Decimal("2")}])
        self.assertEqual(out["shortfall"], Decimal("3"))


if __name__ == "__main__":
    unittest.main()
