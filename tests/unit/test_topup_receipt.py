# -*- coding: utf-8 -*-
"""单测 · build_topup_receipt_pdf(充值凭证 PDF · 2026-06-28)

锁:① 合法 PDF 字节 ② 四语言都能出 ③ 状态如实映射(approved→已到账 等)
④ 金额/公司不崩。版式靠人工 + E2E,这里守不回归崩。
"""

import unittest

from services.billing.topup_receipt import build_topup_receipt_pdf, _t, _status_label

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
            self.assertTrue(data[:4] == b"%PDF", lang)
            self.assertGreater(len(data), 1000, lang)

    def test_unknown_lang_falls_back(self):
        data = build_topup_receipt_pdf(lang="xx", tenant_name="ACME", receipt=_R)
        self.assertEqual(data[:4], b"%PDF")

    def test_status_label_honest(self):
        self.assertEqual(_status_label("zh", "approved"), "已到账")
        self.assertEqual(_status_label("zh", "pending"), "待审核")
        self.assertEqual(_status_label("zh", "rejected"), "已驳回")
        self.assertEqual(_status_label("zh", ""), "待审核")  # 缺省按待审核

    def test_pending_receipt_no_credited_row(self):
        # 待审核没有到账时间 · 不崩(reviewed_at 为空)
        r = dict(_R, status="pending", reviewed_at="")
        data = build_topup_receipt_pdf(lang="th", tenant_name="บริษัท", receipt=r)
        self.assertEqual(data[:4], b"%PDF")

    def test_missing_fields_tolerated(self):
        data = build_topup_receipt_pdf(lang="en", tenant_name="", receipt={"id": 1})
        self.assertEqual(data[:4], b"%PDF")

    def test_title_localized(self):
        self.assertEqual(_t("zh", "title"), "充值凭证")
        self.assertEqual(_t("en", "title"), "Top-up Receipt")
        self.assertNotEqual(_t("th", "title"), _t("ja", "title"))


if __name__ == "__main__":
    unittest.main()
