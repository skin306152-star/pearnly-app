# -*- coding: utf-8 -*-
"""线 B 批6 · 替代收据 PDF 生成 + 签名 token 鉴权(doc 14 §7)。"""

import os
import unittest
from decimal import Decimal
from unittest import mock

from services.expense import receipt_pdf, receipt_token


class PdfTests(unittest.TestCase):
    def test_builds_valid_pdf_bytes(self):
        pdf = receipt_pdf.build_receipt_pdf(
            {
                "business_name": "บริษัท ทดสอบ จำกัด",
                "doc_date": "2026-06-15",
                "vendor_name": "ร้านกาแฟ",
                "amount": Decimal("135.00"),
                "category": "ค่าอาหารและรับรอง",
                "expense_type": "goods",
                "note": "กาแฟ 3 แก้ว",
            }
        )
        self.assertTrue(pdf.startswith(b"%PDF"))
        self.assertGreater(len(pdf), 800)

    def test_handles_empty_fields(self):
        pdf = receipt_pdf.build_receipt_pdf({})
        self.assertTrue(pdf.startswith(b"%PDF"))


class TokenTests(unittest.TestCase):
    def setUp(self):
        self.env = mock.patch.dict(
            os.environ, {"JWT_SECRET": "test-secret-key-1234567890"}, clear=False
        )
        self.env.start()

    def tearDown(self):
        self.env.stop()

    def test_sign_verify_roundtrip(self):
        tok = receipt_token.sign(draft_id="d1", tenant_id="t1", ws=7, now_ts=1000)
        payload = receipt_token.verify(tok, now_ts=2000)
        self.assertEqual(payload["d"], "d1")
        self.assertEqual(payload["t"], "t1")
        self.assertEqual(payload["w"], 7)

    def test_expired_rejected(self):
        tok = receipt_token.sign(draft_id="d1", tenant_id="t1", ws=7, now_ts=1000)
        far = 1000 + receipt_token.TTL_SECONDS + 10
        self.assertIsNone(receipt_token.verify(tok, now_ts=far))

    def test_tampered_rejected(self):
        tok = receipt_token.sign(draft_id="d1", tenant_id="t1", ws=7, now_ts=1000)
        raw, sig = tok.split(".", 1)
        forged = raw + "." + ("0" * len(sig))
        self.assertIsNone(receipt_token.verify(forged, now_ts=1500))

    def test_garbage_rejected(self):
        self.assertIsNone(receipt_token.verify("notatoken", now_ts=1500))


if __name__ == "__main__":
    unittest.main()
