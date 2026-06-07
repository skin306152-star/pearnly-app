# -*- coding: utf-8 -*-
"""餐厅 POS 纯逻辑守门(不连库):埋单算价 + KOT 状态派生 + 总览状态机 + AA 分单。餐厅 POS · PO-R2/R3。

钉死:服务费 + 合并 VAT 单次取整对齐定稿稿(小计 440 → 服务费 44 → 含 VAT 31.66 → 应收 484);
整单态从行 kitchen_status 派生;总览 free/seat/cook/bill 派生;AA 均摊。
"""

from __future__ import annotations

import unittest
from datetime import datetime, timezone
from decimal import Decimal

from services.pos.restaurant import checkout as co
from services.pos.restaurant import tables as tbl
from services.pos.restaurant.kitchen import derive_status

# 定稿稿 A2 桌账单(VAT 价内):合计 440 → +服务费 10% 44 → 应收 484 · 含 VAT 31.66。
UI_LINES = [
    {
        "product_id": "p1",
        "qty": 1,
        "unit_price": "120.00",
        "line_discount": 0,
        "vat_applicable": True,
    },
    {
        "product_id": "p2",
        "qty": 1,
        "unit_price": "180.00",
        "line_discount": 0,
        "vat_applicable": True,
    },
    {
        "product_id": "p3",
        "qty": 2,
        "unit_price": "10.00",
        "line_discount": 0,
        "vat_applicable": True,
    },
    {
        "product_id": "p4",
        "qty": 2,
        "unit_price": "15.00",
        "line_discount": 0,
        "vat_applicable": True,
    },
    {
        "product_id": "p5",
        "qty": 1,
        "unit_price": "90.00",
        "line_discount": 0,
        "vat_applicable": True,
    },
]


class CheckoutComputeTests(unittest.TestCase):
    def test_matches_concept_bill_vat_inclusive(self):
        c = co._compute(UI_LINES, service_rate="10", price_includes_vat=True, header_discount=None)
        self.assertEqual(c["subtotal"], Decimal("440.00"))
        self.assertEqual(c["service_charge"], Decimal("44.00"))
        self.assertEqual(c["vat_amount"], Decimal("31.66"))
        self.assertEqual(c["grand_total"], Decimal("484.00"))

    def test_vat_exclusive_adds_on_top(self):
        c = co._compute(UI_LINES, service_rate="10", price_includes_vat=False, header_discount=None)
        # 价外:服务费 44,VAT = (440+44)*7% = 33.88,应收 = 484 + 33.88
        self.assertEqual(c["service_charge"], Decimal("44.00"))
        self.assertEqual(c["vat_amount"], Decimal("33.88"))
        self.assertEqual(c["grand_total"], Decimal("517.88"))

    def test_no_service_charge(self):
        c = co._compute(UI_LINES, service_rate="0", price_includes_vat=True, header_discount=None)
        self.assertEqual(c["service_charge"], Decimal("0.00"))
        self.assertEqual(c["grand_total"], Decimal("440.00"))
        self.assertEqual(c["vat_amount"], Decimal("28.79"))  # 440×7/107=28.785 → HALF_UP

    def test_header_discount_lowers_service_base(self):
        # 整单 40 折扣 → 菜品净额 400 → 服务费 40 → billed 440 → 价内
        c = co._compute(
            UI_LINES,
            service_rate="10",
            price_includes_vat=True,
            header_discount={"type": "amount", "value": "40"},
        )
        self.assertEqual(c["service_charge"], Decimal("40.00"))
        self.assertEqual(c["grand_total"], Decimal("440.00"))


class SplitTests(unittest.TestCase):
    def test_aa_even_split(self):
        s = co._split(Decimal("484.00"), 4)
        self.assertEqual(s, {"ways": 4, "per_share": "121.00"})

    def test_no_split_for_one_or_none(self):
        self.assertIsNone(co._split(Decimal("484.00"), 1))
        self.assertIsNone(co._split(Decimal("484.00"), None))


class DeriveStatusTests(unittest.TestCase):
    def test_states(self):
        self.assertEqual(derive_status({}), "void")
        self.assertEqual(derive_status({"void": 3}), "void")
        self.assertEqual(derive_status({"pending": 2}), "new")
        self.assertEqual(derive_status({"pending": 1, "cooking": 1}), "cooking")
        self.assertEqual(derive_status({"done": 2}), "done")
        self.assertEqual(derive_status({"done": 1, "void": 1}), "done")


class OverviewStatusTests(unittest.TestCase):
    def _table(self, **kw):
        base = {
            "id": 1,
            "name": "A2",
            "area_id": 1,
            "seats": 4,
            "session_id": None,
            "session_status": None,
            "party_size": None,
            "opened_at": datetime.now(timezone.utc),
        }
        base.update(kw)
        return base

    def test_free_when_no_session(self):
        v = tbl._overview_table(self._table(), {})
        self.assertEqual(v["status"], "free")
        self.assertEqual(v["amount"], "0.00")

    def test_bill_when_billing(self):
        t = self._table(session_id="s1", session_status="billing", party_size=4)
        v = tbl._overview_table(t, {"s1": {"amount": Decimal("680"), "cooking": True}})
        self.assertEqual(v["status"], "bill")  # billing 优先于在制

    def test_cook_when_active_kitchen(self):
        t = self._table(session_id="s1", session_status="open", party_size=2)
        v = tbl._overview_table(t, {"s1": {"amount": Decimal("320"), "cooking": True}})
        self.assertEqual(v["status"], "cook")
        self.assertEqual(v["amount"], "320.00")

    def test_seat_when_open_idle(self):
        t = self._table(session_id="s1", session_status="open", party_size=3)
        v = tbl._overview_table(t, {"s1": {"amount": Decimal("540"), "cooking": False}})
        self.assertEqual(v["status"], "seat")


if __name__ == "__main__":
    unittest.main()
