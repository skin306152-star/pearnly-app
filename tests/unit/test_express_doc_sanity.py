# -*- coding: utf-8 -*-
"""Express 单据防呆体检单测(纯函数 · 无网络 · 无 DB)。

钉死五道防呆闸命中规范 reason、正常票放行、空信号不误伤。对应全语料真机暴露的
陷阱票(26 外币 / 30 贷项 / 27 押金 / 24 未来日期 / 25 倒签 / 19 税号非法)。
"""

from __future__ import annotations

import sys
import unittest
from datetime import date
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.erp.express_push.doc_sanity import check_document  # noqa: E402

TODAY = date(2026, 6, 24)
VENDOR_TAX = "0107561000013"
CUSTOMER_TAX = "0105551234567"


def _fields(**over):
    f = {
        "seller_tax": VENDOR_TAX,
        "buyer_tax": CUSTOMER_TAX,
        "document_type": "tax_invoice",
        "currency": "",
        "notes": "",
        "category": "",
        "items": [{"name": "เหล็กเส้น SD40"}],
    }
    f.update(over)
    return f


def _hist(invoice_date="2025-12-01"):
    return {"invoice_date": invoice_date}


class CleanPassTests(unittest.TestCase):
    def test_normal_purchase_passes(self):
        self.assertIsNone(check_document(_fields(), _hist(), "purchase", today=TODAY))

    def test_normal_sales_passes(self):
        self.assertIsNone(check_document(_fields(), _hist(), "sales", today=TODAY))

    def test_thb_currency_passes(self):
        self.assertIsNone(check_document(_fields(currency="THB"), _hist(), "purchase", today=TODAY))

    def test_empty_tax_not_flagged(self):
        # 空税号是另一道闸(置信/缺字段)的事 · 这里不误伤。
        self.assertIsNone(check_document(_fields(seller_tax=""), _hist(), "purchase", today=TODAY))


class CurrencyTests(unittest.TestCase):
    def test_usd_blocked(self):
        r = check_document(_fields(currency="USD"), _hist(), "purchase", today=TODAY)
        self.assertEqual(r, "currency_not_thb:usd")

    def test_currency_wins_over_other_flags(self):
        # 外币最严重 · 即便又有坏税号也先报币种。
        r = check_document(
            _fields(currency="EUR", seller_tax="123"), _hist(), "purchase", today=TODAY
        )
        self.assertEqual(r, "currency_not_thb:eur")


class CurrencyMarkerTests(unittest.TestCase):
    """currency 字段空时的外币记号兜底(对抗票 15:currency=None 但票号 INV-USD-0007)。"""

    def test_usd_in_invoice_number_blocked(self):
        r = check_document(_fields(invoice_number="INV-USD-0007"), _hist(), "purchase", today=TODAY)
        self.assertEqual(r, "currency_not_thb:usd")

    def test_dollar_symbol_next_to_amount_blocked(self):
        r = check_document(_fields(notes="Total $400.00 net 30"), _hist(), "purchase", today=TODAY)
        self.assertEqual(r, "currency_not_thb:symbol")

    def test_thai_dollar_word_blocked(self):
        r = check_document(_fields(notes="ชำระเป็นดอลลาร์สหรัฐ"), _hist(), "purchase", today=TODAY)
        self.assertEqual(r, "currency_not_thb:th-marker")

    def test_explicit_thb_skips_marker_probe(self):
        # currency=THB 已确认泰铢 → 记号兜底不跑(票号带 USD 也不误伤)。
        self.assertIsNone(
            check_document(
                _fields(currency="THB", invoice_number="INV-USD-0007"),
                _hist(),
                "purchase",
                today=TODAY,
            )
        )

    def test_plain_invoice_number_passes(self):
        self.assertIsNone(
            check_document(_fields(invoice_number="IV69/00179"), _hist(), "purchase", today=TODAY)
        )


class SameTaxTests(unittest.TestCase):
    """买卖方同税号 = 票面自己卖给自己(对抗票 12)· 方向判不出必转人工。"""

    def test_same_tax_blocked(self):
        r = check_document(
            _fields(seller_tax=VENDOR_TAX, buyer_tax=VENDOR_TAX), _hist(), "sales", today=TODAY
        )
        self.assertEqual(r, "seller_buyer_same_tax")

    def test_distinct_tax_passes(self):
        self.assertIsNone(check_document(_fields(), _hist(), "sales", today=TODAY))

    def test_one_side_missing_not_flagged(self):
        # 只读到一方税号 → 判不了同号 · 不误伤(缺字段是别的闸的事)。
        self.assertIsNone(check_document(_fields(buyer_tax=""), _hist(), "purchase", today=TODAY))


class FriendlyMapParityTests(unittest.TestCase):
    """doc_sanity 每个 reason 码在 MR.ERP 路由文案表都要有四语条目(防新增码漏文案)。"""

    def test_all_reason_codes_have_friendly_entries(self):
        from services.erp.mrerp_http.routing import _DOC_SANITY_FRIENDLY

        codes = (
            "currency_not_thb",
            "seller_buyer_same_tax",
            "credit_note",
            "deposit_receipt",
            "date_future",
            "date_reissued",
            "tax_id_invalid",
        )
        for code in codes:
            entry = _DOC_SANITY_FRIENDLY.get(code)
            self.assertIsNotNone(entry, f"missing friendly entry: {code}")
            for lang in ("th", "en", "zh", "ja"):
                self.assertTrue(entry.get(lang), f"missing {lang} text: {code}")


class CreditNoteTests(unittest.TestCase):
    def test_credit_note_doctype_blocked(self):
        r = check_document(_fields(document_type="credit_note"), _hist(), "purchase", today=TODAY)
        self.assertEqual(r, "credit_note")

    def test_credit_note_wording_blocked(self):
        r = check_document(
            _fields(notes="ใบลดหนี้ อ้างอิงใบกำกับเดิม"), _hist(), "purchase", today=TODAY
        )
        self.assertEqual(r, "credit_note")


class DepositTests(unittest.TestCase):
    def test_deposit_item_blocked(self):
        r = check_document(
            _fields(items=[{"name": "เงินมัดจำค่าสินค้า (10%)"}]),
            _hist(),
            "purchase",
            today=TODAY,
        )
        self.assertEqual(r, "deposit_receipt")

    def test_security_deposit_note_blocked(self):
        r = check_document(
            _fields(notes="เงินประกัน — ยังไม่ส่งมอบ"), _hist(), "purchase", today=TODAY
        )
        self.assertEqual(r, "deposit_receipt")


class DateTests(unittest.TestCase):
    def test_future_date_blocked(self):
        r = check_document(_fields(), _hist("2026-12-31"), "purchase", today=TODAY)
        self.assertEqual(r, "date_future")

    def test_past_date_passes(self):
        self.assertIsNone(check_document(_fields(), _hist("2015-12-31"), "purchase", today=TODAY))

    def test_reissue_note_blocked(self):
        r = check_document(
            _fields(notes="ออกใบแทน ณ วันที่ 2568"), _hist("2022-01-05"), "purchase", today=TODAY
        )
        self.assertEqual(r, "date_reissued")


class TaxIdTests(unittest.TestCase):
    def test_purchase_bad_seller_tax_blocked(self):
        r = check_document(_fields(seller_tax="01055560123"), _hist(), "purchase", today=TODAY)
        self.assertEqual(r, "tax_id_invalid")

    def test_sales_checks_buyer_tax(self):
        r = check_document(_fields(buyer_tax="12345"), _hist(), "sales", today=TODAY)
        self.assertEqual(r, "tax_id_invalid")

    def test_sales_ignores_bad_seller_tax(self):
        # 销项的卖方=自家(权威)· 不因自家税号位数判而误伤(对手方=买方才查)。
        self.assertIsNone(check_document(_fields(seller_tax="999"), _hist(), "sales", today=TODAY))


if __name__ == "__main__":
    unittest.main(verbosity=2)
