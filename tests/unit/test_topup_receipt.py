# -*- coding: utf-8 -*-
"""单测 · build_topup_receipt_pdf(充值凭证 · 泰式 ใบเสร็จรับเงิน/ใบกำกับภาษี · 2026-06-28)

锁:① 合法 PDF 字节 ② 任意 lang 都能出(文档本身 TH/EN 固定双语)
③ 状态如实映射(approved→ชำระแล้ว/已收款 · rejected→ถูกปฏิเสธ · 其余→รอตรวจสอบ)
④ 泰文金额大写正确 ⑤ 缺字段不崩。版式靠人工对版 + E2E。
"""

import unittest

from services.billing.topup_receipt import (
    build_topup_receipt_pdf,
    baht_text,
    _status_th,
)

_R = {
    "id": 123,
    "amount_thb": 1000.0,
    "payer_name": "Somchai",
    "note": "promptpay",
    "status": "approved",
    "created_at": "2026-06-28 09:44",
    "reviewed_at": "2026-06-28 10:00",
}


class TopupReceiptTests(unittest.TestCase):
    def test_valid_pdf_all_langs(self):
        for lang in ("zh", "en", "th", "ja"):
            data = build_topup_receipt_pdf(lang=lang, tenant_name="ACME", receipt=_R)
            self.assertEqual(data[:4], b"%PDF", lang)
            self.assertGreater(len(data), 1000, lang)

    def test_unknown_lang_still_renders(self):
        data = build_topup_receipt_pdf(lang="xx", tenant_name="ACME", receipt=_R)
        self.assertEqual(data[:4], b"%PDF")

    def test_status_th_honest(self):
        self.assertEqual(_status_th("approved"), ("ชำระแล้ว", True))
        self.assertEqual(_status_th("rejected"), ("ถูกปฏิเสธ", False))
        self.assertEqual(_status_th("pending"), ("รอตรวจสอบ", False))
        self.assertEqual(_status_th(""), ("รอตรวจสอบ", False))  # 缺省按待审核
        self.assertEqual(_status_th("APPROVED"), ("ชำระแล้ว", True))  # 大小写容错

    def test_baht_text(self):
        self.assertEqual(baht_text(100), "หนึ่งร้อยบาทถ้วน")
        self.assertEqual(baht_text(21), "ยี่สิบเอ็ดบาทถ้วน")
        self.assertEqual(baht_text(0), "ศูนย์บาทถ้วน")
        self.assertEqual(baht_text(1234.50), "หนึ่งพันสองร้อยสามสิบสี่บาทห้าสิบสตางค์")

    def test_pending_receipt_no_paid_date(self):
        # 待审核没有收款时间 · 不崩(reviewed_at 为空)
        r = dict(_R, status="pending", reviewed_at="")
        data = build_topup_receipt_pdf(lang="th", tenant_name="บริษัท", receipt=r)
        self.assertEqual(data[:4], b"%PDF")

    def test_missing_fields_tolerated(self):
        data = build_topup_receipt_pdf(lang="en", tenant_name="", receipt={"id": 1})
        self.assertEqual(data[:4], b"%PDF")


if __name__ == "__main__":
    unittest.main()
