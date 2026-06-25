# -*- coding: utf-8 -*-
"""Express V1 安全明细抽取 + 对账闸单测(确定性纯函数 · 无 DB/网络)。

钉死:行合计≈税前额才采信(ok);缺品名/金额→incomplete;无行→empty;对不上→mismatch;
逐行四舍五入容差吸收;缺数量默认 1、缺单价由金额反推。绝不为"好看"采信不自洽明细。
"""

from __future__ import annotations

import sys
import unittest
from decimal import Decimal
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.erp.express_push.common import (  # noqa: E402
    ITEM_MODE_DIRECT,
    ITEM_MODE_NONSTOCK,
    ITEMS_EMPTY,
    ITEMS_INCOMPLETE,
    ITEMS_MISMATCH,
    ITEMS_OK,
    extract_line_items,
    sanitize_push_meta,
)


def _fields(items):
    return {"items": items}


class SanitizePushMetaTests(unittest.TestCase):
    def test_keeps_whitelisted_and_drops_unknown(self):
        m = sanitize_push_meta({
            "companion_version": "1.1.13",
            "doc_type": "sales",
            "created_customer": 1,
            "tables_written": ["ARTRN", "STCRD", "ISVAT"],
            "evil": "x" * 9999,  # 非白名单 → 丢
        })
        self.assertEqual(m["companion_version"], "1.1.13")
        self.assertIs(m["created_customer"], True)
        self.assertEqual(m["tables_written"], ["ARTRN", "STCRD", "ISVAT"])
        self.assertNotIn("evil", m)

    def test_non_dict_returns_empty(self):
        self.assertEqual(sanitize_push_meta("nope"), {})
        self.assertEqual(sanitize_push_meta(None), {})

    def test_str_value_length_capped(self):
        m = sanitize_push_meta({"account_dir": "z" * 500})
        self.assertLessEqual(len(m["account_dir"]), 200)


class ExtractLineItemsTests(unittest.TestCase):
    def test_ok_lines_sum_to_base(self):
        # 油品票样:5 行,合计 = 税前额 3141.12。
        items = [
            {"name": "58AUTOMAT(10/1L)", "qty": "1", "price": "170.00", "subtotal": "170.00"},
            {"name": "58หัวเชื้อดีเซล", "qty": "7", "price": "33.00", "subtotal": "231.00"},
            {"name": "58น้ำกลั่น", "qty": "7", "price": "10.00", "subtotal": "70.00"},
            {"name": "58PERFORMA SEMI", "qty": "1", "price": "625.00", "subtotal": "625.00"},
            {"name": "58PTT V-120D", "qty": "4", "price": "511.78", "subtotal": "2045.12"},
        ]
        r = extract_line_items(_fields(items), Decimal("3141.12"))
        self.assertEqual(r["status"], ITEMS_OK)
        self.assertEqual(len(r["items"]), 5)
        self.assertEqual(r["line_sum"], "3141.12")
        self.assertEqual(r["items"][0]["name"], "58AUTOMAT(10/1L)")
        self.assertEqual(r["items"][0]["amount"], "170.00")

    def test_empty_no_items(self):
        self.assertEqual(extract_line_items({}, Decimal("100"))["status"], ITEMS_EMPTY)
        self.assertEqual(extract_line_items(_fields([]), Decimal("100"))["status"], ITEMS_EMPTY)

    def test_incomplete_line_missing_amount(self):
        items = [
            {"name": "A", "qty": "1", "price": "50", "subtotal": "50"},
            {"name": "B"},  # 无金额、无数量单价 → 整组不可信
        ]
        r = extract_line_items(_fields(items), Decimal("50"))
        self.assertEqual(r["status"], ITEMS_INCOMPLETE)

    def test_incomplete_line_missing_name(self):
        items = [{"name": "", "qty": "1", "price": "50", "subtotal": "50"}]
        self.assertEqual(
            extract_line_items(_fields(items), Decimal("50"))["status"], ITEMS_INCOMPLETE
        )

    def test_mismatch_sum_far_from_base(self):
        items = [{"name": "A", "qty": "1", "price": "50", "subtotal": "50"}]
        r = extract_line_items(_fields(items), Decimal("999.00"))
        self.assertEqual(r["status"], ITEMS_MISMATCH)
        self.assertEqual(r["line_sum"], "50.00")

    def test_rounding_within_tolerance_is_ok(self):
        # 行合计 100.40 vs 税前 100.00 → 差 0.40 < 1.00 容差 → ok。
        items = [
            {"name": "A", "qty": "3", "price": "33.47", "subtotal": "100.40"},
        ]
        r = extract_line_items(_fields(items), Decimal("100.00"))
        self.assertEqual(r["status"], ITEMS_OK)

    def test_missing_qty_defaults_one(self):
        items = [{"name": "A", "price": "100", "subtotal": "100"}]
        r = extract_line_items(_fields(items), Decimal("100"))
        self.assertEqual(r["status"], ITEMS_OK)
        self.assertEqual(r["items"][0]["qty"], "1.00")

    def test_amount_from_qty_times_price_when_subtotal_missing(self):
        items = [{"name": "A", "qty": "4", "price": "25"}]
        r = extract_line_items(_fields(items), Decimal("100"))
        self.assertEqual(r["status"], ITEMS_OK)
        self.assertEqual(r["items"][0]["amount"], "100.00")

    def test_unit_price_back_derived_when_missing(self):
        items = [{"name": "A", "qty": "4", "subtotal": "100"}]
        r = extract_line_items(_fields(items), Decimal("100"))
        self.assertEqual(r["items"][0]["unit_price"], "25.00")

    def test_item_mode_default_nonstock(self):
        # V2 默认每行带 item_mode=non_stock_item(companion 据此匹配/建非库存主档)。
        items = [{"name": "A", "qty": "1", "price": "100", "subtotal": "100"}]
        r = extract_line_items(_fields(items), Decimal("100"))
        self.assertEqual(r["items"][0]["item_mode"], ITEM_MODE_NONSTOCK)

    def test_item_mode_override(self):
        items = [{"name": "A", "qty": "1", "price": "100", "subtotal": "100"}]
        r = extract_line_items(_fields(items), Decimal("100"), item_mode=ITEM_MODE_DIRECT)
        self.assertEqual(r["items"][0]["item_mode"], ITEM_MODE_DIRECT)

    def test_comma_amounts_parsed(self):
        items = [{"name": "A", "qty": "1", "price": "1,234.00", "subtotal": "1,234.00"}]
        r = extract_line_items(_fields(items), Decimal("1234.00"))
        self.assertEqual(r["status"], ITEMS_OK)
        self.assertEqual(r["items"][0]["amount"], "1234.00")


if __name__ == "__main__":
    unittest.main(verbosity=2)
