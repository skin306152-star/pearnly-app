#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/unit/test_mrerp_business_friendly.py

Unit tests for services.erp.mrerp_business_friendly's 4-language lookup
catalog (P1-A §3.9, Zihao 2026-05-18 拍板: th/en/zh/zh_TW).
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from services.erp.mrerp_business_friendly import (  # noqa: E402
    SUPPORTED_LANGS,
    get_friendly,
    primary_friendly,
    translate_reasons,
)


class CatalogShapeTests(unittest.TestCase):

    def test_four_langs_supported(self):
        self.assertEqual(set(SUPPORTED_LANGS), {"th", "en", "zh", "zh_TW"})

    def test_every_return_value_covers_every_lang(self):
        for sample in (
            "ERR_INVOICE_NO_TOO_LONG",
            "ไม่พบข้อมูลรหัสลูกค้า",
            "totally unknown reason",
            "",
            None,
        ):
            translations = get_friendly(sample)
            self.assertEqual(
                set(translations.keys()),
                set(SUPPORTED_LANGS),
                f"missing lang keys for sample={sample!r}",
            )


class ErrCodeLookupTests(unittest.TestCase):

    def test_err_invoice_no_too_long(self):
        out = get_friendly("ERR_INVOICE_NO_TOO_LONG")
        self.assertIn("18", out["en"])
        self.assertIn("18", out["zh"])
        self.assertIn("18", out["zh_TW"])
        self.assertIn("18", out["th"])

    def test_err_customer_code_too_long(self):
        out = get_friendly("ERR_CUSTOMER_CODE_TOO_LONG")
        self.assertIn("20", out["en"])
        self.assertIn("Customer code", out["en"])

    def test_err_negative_amount(self):
        out = get_friendly("ERR_NEGATIVE_AMOUNT")
        self.assertIn("Negative", out["en"])
        self.assertIn("红字", out["zh"])
        self.assertIn("紅字", out["zh_TW"])

    def test_err_tax_rate_invalid(self):
        out = get_friendly("ERR_TAX_RATE_INVALID")
        self.assertIn("vat_7", out["en"])
        self.assertIn("vat_7", out["zh"])

    def test_err_date_future(self):
        out = get_friendly("ERR_DATE_FUTURE")
        self.assertIn("30", out["en"])
        self.assertIn("30", out["zh"])

    def test_warn_date_near_future(self):
        out = get_friendly("WARN_DATE_NEAR_FUTURE")
        self.assertIn("7", out["en"])


class ThaiSubstringLookupTests(unittest.TestCase):
    """The MR.ERP `หมายเหตุ` column writes these strings verbatim."""

    def test_customer_not_found(self):
        out = get_friendly("ไม่พบข้อมูลรหัสลูกค้า")
        self.assertIn("Customer code not found", out["en"])
        self.assertIn("找不到客户码", out["zh"])
        self.assertIn("找不到客戶碼", out["zh_TW"])

    def test_customer_bill_not_found_prefers_specific_match(self):
        # The (บิล) suffix is a separate, more-specific catalog entry; it
        # must NOT silently fall through to the plain 'customer not found'.
        out = get_friendly("ไม่พบข้อมูลรหัสลูกค้า (บิล)")
        self.assertIn("billing code not found", out["en"].lower())

    def test_product_not_found(self):
        out = get_friendly("ไม่พบข้อมูลรหัสสินค้า")
        self.assertIn("Product code not found", out["en"])

    def test_salesman_not_found(self):
        out = get_friendly("ไม่พบข้อมูลพนักงานขาย")
        self.assertIn("Salesman not found", out["en"])

    def test_invoice_no_too_long_from_server(self):
        out = get_friendly("เลขที่ต้องไม่เกิน 18 ตัวอักษร")
        self.assertIn("18", out["en"])
        self.assertIn("Invoice number exceeds", out["en"])

    def test_duplicate_invoice_number(self):
        out = get_friendly("เลขที่ดังกล่าวมีอยู่ในระบบแล้ว")
        # v118.34.24 (Zihao 2026-05-19 拍板 · 问题 1) · friendly 文案
        # 从干巴巴 "already exists" 改成行动指引 ·
        # 新文案: "already pushed ... duplicates aren't allowed ... edit the bill"
        self.assertIn("already pushed", out["en"])
        self.assertIn("MR.ERP", out["en"])
        self.assertIn("推送过", out["zh"])
        self.assertIn("不能重复推", out["zh"])


class UnknownReasonTests(unittest.TestCase):

    def test_unknown_echoes_raw(self):
        raw = "this is completely unknown text"
        out = get_friendly(raw)
        for k in SUPPORTED_LANGS:
            self.assertEqual(out[k], raw)

    def test_empty_returns_empty_strings(self):
        for empty in ("", None):
            out = get_friendly(empty)
            for k in SUPPORTED_LANGS:
                self.assertEqual(out[k], "")


class TranslateReasonsTests(unittest.TestCase):

    def test_parallel_list(self):
        raws = [
            "ERR_INVOICE_NO_TOO_LONG",
            "ไม่พบข้อมูลรหัสลูกค้า",
        ]
        out = translate_reasons(raws)
        self.assertEqual(len(out), 2)
        self.assertIn("18", out[0]["en"])
        self.assertIn("Customer code not found", out[1]["en"])

    def test_empty_list(self):
        self.assertEqual(translate_reasons([]), [])
        self.assertEqual(translate_reasons(None), [])


class PrimaryFriendlyTests(unittest.TestCase):

    def test_primary_picks_chosen_lang(self):
        self.assertIn("18", primary_friendly("ERR_INVOICE_NO_TOO_LONG", "zh"))
        self.assertIn("18", primary_friendly("ERR_INVOICE_NO_TOO_LONG", "en"))

    def test_unknown_lang_falls_back_to_english(self):
        # If a future caller passes an unsupported lang, we should still
        # return something usable (English).
        out = primary_friendly("ERR_DATE_FUTURE", lang="fr")
        self.assertIn("30", out)


if __name__ == "__main__":
    unittest.main(verbosity=2)
