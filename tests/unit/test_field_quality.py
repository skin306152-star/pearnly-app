# -*- coding: utf-8 -*-
"""字段卫生质量层(P2B):seller/date/tax/invoice/address 低置信判定 + dirty_fields。"""

import unittest
from datetime import date

from services.purchase import field_clean, field_quality as fq


class SellerStatusTests(unittest.TestCase):
    def test_clean_seller_ok(self):
        self.assertEqual(fq.seller_status("บางจาก"), "ok")
        self.assertEqual(fq.seller_status("7-Eleven"), "ok")

    def test_all_question_marks_unclear(self):
        self.assertEqual(fq.seller_status("?????????????"), "unclear")

    def test_mostly_garbled_unclear(self):
        self.assertEqual(fq.seller_status("TW ?????"), "unclear")

    def test_pure_digits_unclear(self):
        self.assertEqual(fq.seller_status("1780.00"), "unclear")

    def test_field_label_noise_unclear(self):
        self.assertEqual(fq.seller_status("Total"), "unclear")

    def test_absent_when_empty(self):
        self.assertEqual(fq.seller_status(""), "absent")
        self.assertEqual(fq.seller_status(None), "absent")


class DateStatusTests(unittest.TestCase):
    TODAY = date(2026, 6, 19)

    def test_normal_date_ok(self):
        self.assertEqual(fq.date_status("2026-06-18", self.TODAY), "ok")

    def test_future_suspect(self):
        self.assertEqual(fq.date_status("2026-06-20", self.TODAY), "suspect")

    def test_too_old_suspect(self):
        self.assertEqual(fq.date_status("2014-12-31", self.TODAY), "suspect")
        self.assertEqual(fq.date_status("2021-06-18", self.TODAY), "ok")  # 2021 在范围内

    def test_buddhist_not_converted_is_future_suspect(self):
        # 佛历 2569 没转(上游漏)→ 远未来 → suspect(不静默入账)。
        self.assertEqual(fq.date_status("2569-06-18", self.TODAY), "suspect")

    def test_malformed_suspect(self):
        self.assertEqual(fq.date_status("18/06/2026", self.TODAY), "suspect")
        self.assertEqual(fq.date_status("2026-13-40", self.TODAY), "suspect")

    def test_absent(self):
        self.assertEqual(fq.date_status("", self.TODAY), "absent")


class TaxInvoiceStatusTests(unittest.TestCase):
    def test_valid_tax(self):
        self.assertEqual(fq.tax_status("0107542000011"), "ok")

    def test_invalid_tax(self):
        self.assertEqual(fq.tax_status("13"), "invalid")
        self.assertEqual(fq.tax_status("12/06/26"), "invalid")

    def test_absent_tax(self):
        self.assertEqual(fq.tax_status(""), "absent")

    def test_invoice_ok_and_dirty(self):
        self.assertEqual(fq.invoice_status("IV69/00179"), "ok")
        self.assertEqual(fq.invoice_status("?????"), "dirty")
        self.assertEqual(fq.invoice_status(""), "absent")


class AddressGarbledTests(unittest.TestCase):
    def test_clean_address_kept(self):
        self.assertTrue(field_clean.clean_address("123 ถนนสุขุมวิท กรุงเทพ"))

    def test_garbled_address_blanked(self):
        self.assertEqual(field_clean.clean_address("???????????"), "")

    def test_is_garbled(self):
        self.assertTrue(field_clean.is_garbled("?????"))
        self.assertFalse(field_clean.is_garbled("บางจาก"))
        self.assertFalse(field_clean.is_garbled(""))  # 空 = 缺失,非乱码


class AssessTests(unittest.TestCase):
    TODAY = date(2026, 6, 19)

    def test_clean_receipt_no_dirty(self):
        out = fq.assess(
            {
                "seller_name": "บางจาก",
                "date": "2026-06-18",
                "seller_tax": "0107542000011",
                "invoice_number": "IV69/00179",
                "seller_addr": "123 ถนนสุขุมวิท",
            },
            today=self.TODAY,
        )
        self.assertEqual(out["dirty"], [])

    def test_garbled_receipt_lists_dirty(self):
        out = fq.assess(
            {
                "seller_name": "?????????",
                "date": "2021-06-18",  # 误读漂移但仍在范围 → 不算 suspect(由年份纠正层管)
                "seller_tax": "13",
                "invoice_number": "?????",
                "seller_addr": "???????",
            },
            today=self.TODAY,
        )
        self.assertIn("seller", out["dirty"])
        self.assertIn("tax_id", out["dirty"])
        self.assertIn("invoice", out["dirty"])
        self.assertIn("address", out["dirty"])

    def test_future_date_dirty(self):
        out = fq.assess({"date": "2027-01-01"}, today=self.TODAY)
        self.assertIn("date", out["dirty"])

    def test_absent_fields_not_dirty(self):
        # 本就没有的字段不进 dirty(不误报)。
        out = fq.assess({"seller_name": "บางจาก"}, today=self.TODAY)
        self.assertEqual(out["dirty"], [])


if __name__ == "__main__":
    unittest.main()
