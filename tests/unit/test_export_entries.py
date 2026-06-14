# -*- coding: utf-8 -*-
"""source_id 反查分录摘要(export.entries.summarize_voucher)· 纯函数(阶段二)。

锁:无凭证→"未记账"占位;有凭证→借/贷拆分 + "码 名 金额"文本 + 状态中文标签。
"""

import unittest
from decimal import Decimal

from services.export.entries import summarize_voucher


class SummarizeVoucherTests(unittest.TestCase):
    def test_none_voucher_not_posted(self):
        out = summarize_voucher(None)
        self.assertFalse(out["posted"])
        self.assertEqual(out["status_label"], "未记账")
        self.assertEqual(out["debit"], [])
        self.assertEqual(out["debit_text"], "")
        self.assertEqual(out["voucher_no"], "")

    def test_posted_voucher_splits_debit_credit(self):
        v = {
            "voucher_no": "JV2606-0001",
            "status": "posted",
            "lines": [
                {"dr_cr": "debit", "account_code": "5000", "account_name": "采购", "amount": "250"},
                {
                    "dr_cr": "credit",
                    "account_code": "2100",
                    "account_name": "应付",
                    "amount": "250",
                },
            ],
        }
        out = summarize_voucher(v)
        self.assertTrue(out["posted"])
        self.assertEqual(out["voucher_no"], "JV2606-0001")
        self.assertEqual(out["status_label"], "已过账")
        self.assertEqual(len(out["debit"]), 1)
        self.assertEqual(out["debit"][0]["amount"], Decimal("250"))
        self.assertEqual(out["debit_text"], "5000 采购 250")
        self.assertEqual(out["credit_text"], "2100 应付 250")

    def test_pending_review_label(self):
        out = summarize_voucher({"voucher_no": "JV1", "status": "pending_review", "lines": []})
        self.assertFalse(out["posted"])
        self.assertEqual(out["status_label"], "待复核")

    def test_account_label_falls_back_to_code_or_id(self):
        v = {
            "status": "posted",
            "lines": [{"dr_cr": "debit", "account_code": "5000", "amount": "1"}],
        }
        out = summarize_voucher(v)
        self.assertEqual(out["debit_text"], "5000 1")


if __name__ == "__main__":
    unittest.main()
