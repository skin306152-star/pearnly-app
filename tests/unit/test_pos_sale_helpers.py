# -*- coding: utf-8 -*-
"""POS 小票编排纯逻辑守门测试(POS 项目 · PO-B2)。

不连库的纯函数:整单折扣解析、金额字符串化、成交时间解析、幂等短路(client_uuid 命中返原结果
不再发号/扣库存)。重流程(发号/扣库存/落库)由 _e2e_po_b2 真库覆盖。"""

import unittest
from datetime import datetime, timezone
from decimal import Decimal

from services.pos import sale


class _Cur:
    def __init__(self, ones=None):
        self.calls = []
        self._ones = list(ones or [])

    def execute(self, sql, params=None):
        self.calls.append((sql, params))

    def fetchone(self):
        return self._ones.pop(0) if self._ones else None


class HelperTests(unittest.TestCase):
    def test_header_discount_modes(self):
        self.assertEqual(sale._header_discount({"type": "pct", "value": 10}), (0, 10))
        self.assertEqual(sale._header_discount({"type": "amount", "value": 5}), (5, 0))
        self.assertEqual(sale._header_discount({"type": "none", "value": 0}), (0, 0))
        self.assertEqual(sale._header_discount(None), (0, 0))

    def test_money_two_decimals(self):
        self.assertEqual(sale._money(Decimal("55")), "55.00")
        self.assertEqual(sale._money("3.6"), "3.60")
        self.assertEqual(sale._money(None), "0.00")

    def test_parse_sold_at(self):
        dt = sale._parse_sold_at("2026-06-07T07:32:00Z")
        self.assertEqual(dt.year, 2026)
        self.assertEqual(dt.tzinfo, timezone.utc)
        # 坏输入回退到现在(不抛)
        self.assertIsInstance(sale._parse_sold_at("garbage"), datetime)
        self.assertIsInstance(sale._parse_sold_at(None), datetime)

    def test_vat_rate_is_seven(self):
        self.assertEqual(sale.VAT_RATE, Decimal("7"))


class IdempotencyTests(unittest.TestCase):
    def test_dedup_short_circuits_without_numbering_or_stock(self):
        existing = {
            "id": "s1",
            "receipt_no": "RCP-T1-2026-00001",
            "grand_total": Decimal("55.00"),
            "vat_amount": Decimal("3.60"),
            "paid_total": Decimal("100.00"),
            "change_amount": Decimal("45.00"),
            "status": "completed",
        }
        cur = _Cur(ones=[existing])  # find_sale_by_client_uuid 命中
        out = sale.create_sale(
            cur,
            tenant_id="t",
            workspace_client_id=9,
            payload={
                "client_uuid": "cu-1",
                "lines": [{"product_id": "p", "qty": 1, "unit_price": 1}],
            },
        )
        self.assertTrue(out["deduped"])
        self.assertEqual(out["sale"]["receipt_no"], "RCP-T1-2026-00001")
        # 只查重一条 SQL · 没发号/没扣库存/没 INSERT
        self.assertEqual(len(cur.calls), 1)
        joined = " ".join(c[0] for c in cur.calls)
        self.assertNotIn("INSERT", joined)


if __name__ == "__main__":
    unittest.main()
