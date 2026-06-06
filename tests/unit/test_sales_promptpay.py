# -*- coding: utf-8 -*-
"""销项 §L1 · PromptPay 付款 payload + QR 守门(EMVCo 格式 / CRC / 代理分类)。"""

import unittest

from services.sales import promptpay as pp


class PromptPayPayloadTests(unittest.TestCase):
    def test_static_payload_structure(self):
        """无金额 = 静态码:Point of Initiation = 11,含 AID 与 THB 国别。"""
        s = pp.build_payload("0899999999")
        self.assertTrue(s.startswith("000201010211"))  # 格式指示 01 + POI 11
        self.assertIn("0016A000000677010111", s)  # PromptPay AID
        self.assertIn("5802TH", s)
        self.assertIn("5303764", s)  # THB

    def test_dynamic_payload_has_amount_and_poi_12(self):
        s = pp.build_payload("0899999999", "100.00")
        self.assertIn("010212", s)  # POI 动态
        self.assertIn("5406100.00", s)  # 金额字段 tag 54 len 6

    def test_crc_is_self_consistent(self):
        s = pp.build_payload("0812345678", "42.50")
        self.assertEqual(pp._crc16(s[:-4]), s[-4:])
        self.assertEqual(len(s[-4:]), 4)

    def test_proxy_mobile(self):
        tag, target = pp._proxy("0812345678")
        self.assertEqual(tag, "01")
        self.assertEqual(target, "0066812345678")

    def test_proxy_tax_or_national_id(self):
        tag, target = pp._proxy("0105551234567")
        self.assertEqual(tag, "02")
        self.assertEqual(target, "0105551234567")

    def test_proxy_ewallet(self):
        tag, target = pp._proxy("012345678901234")
        self.assertEqual(tag, "03")
        self.assertEqual(len(target), 15)

    def test_proxy_strips_non_digits(self):
        _, target = pp._proxy("081-234-5678")
        self.assertEqual(target, "0066812345678")

    def test_amount_formatted_two_decimals(self):
        # 金额 "21.00"(5 字符)→ EMV 字段 tag 54 + 长度 05 + 值。
        self.assertIn("540521.00", pp.build_payload("0812345678", 21))

    def test_qr_png_bytes(self):
        png = pp.build_qr_png("0899999999", "100.00")
        self.assertTrue(png.startswith(b"\x89PNG\r\n\x1a\n"))
        self.assertGreater(len(png), 100)


if __name__ == "__main__":
    unittest.main()
