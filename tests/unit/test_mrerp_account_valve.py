# -*- coding: utf-8 -*-
"""科目安全阀 · 纯单测(无网络)。

Zihao 定:科目匹配现有则用,匹配不上退回用户(不静默硬建)。反应层(report 报科目未匹配→归
ERR_ACCOUNT_NEEDS_REVIEW)工作即生效;主动层(提供科目表)才启用,不误挡。"""

import unittest

from services.erp.mrerp_http.account_valve import (
    ACCOUNT_REVIEW_CODE,
    account_gate,
    configured_account_overrides,
    missing_from_chart,
    tag_account_review,
)


class TestReactiveTag(unittest.TestCase):
    def test_account_note_prepends_review_code(self):
        # 泰文:找不到科目码
        out = tag_account_review(["ไม่พบรหัสบัญชี 9999-99"])
        self.assertEqual(out[0], ACCOUNT_REVIEW_CODE)
        self.assertIn("ไม่พบรหัสบัญชี 9999-99", out)

    def test_non_account_note_unchanged(self):
        out = tag_account_review(["ลูกค้าซ้ำ"])
        self.assertNotIn(ACCOUNT_REVIEW_CODE, out)

    def test_idempotent(self):
        once = tag_account_review(["ไม่พบบัญชี"])
        twice = tag_account_review(once)
        self.assertEqual(once.count(ACCOUNT_REVIEW_CODE), 1)
        self.assertEqual(twice.count(ACCOUNT_REVIEW_CODE), 1)

    def test_account_word_without_notfound_is_not_review(self):
        # 只提"科目"没有"找不到"信号 → 不算科目问题
        self.assertNotIn(ACCOUNT_REVIEW_CODE, tag_account_review(["บันทึกบัญชีสำเร็จ"]))


class TestProactiveChart(unittest.TestCase):
    def test_missing_from_chart_dormant_without_chart(self):
        self.assertEqual(missing_from_chart(["9999-99"], {}), [])

    def test_missing_from_chart_flags_absent(self):
        m = {"_mrerp_accounts": ["1111-01", "2110-01"]}
        self.assertEqual(missing_from_chart(["1111-01", "9999-99"], m), ["9999-99"])

    def test_configured_overrides_extracts_account_values(self):
        m = {
            "_mrerp_receipt_account_bank": "1112-01",
            "_mrerp_supplier_account": "2110-01",
            "_mrerp_product_acc_rev": "4110-01",
            "_mrerp_customer_area": "สุพรรณ",  # 非科目键 → 不收
            "clients": [],
        }
        got = set(configured_account_overrides(m))
        self.assertEqual(got, {"1112-01", "2110-01", "4110-01"})

    def test_account_gate_dormant_without_chart(self):
        m = {"_mrerp_supplier_account": "9999-99"}  # 没给科目表 → 休眠
        self.assertEqual(account_gate(m), [])

    def test_account_gate_flags_bad_override_when_chart_present(self):
        m = {"_mrerp_accounts": ["1112-01"], "_mrerp_supplier_account": "9999-99"}
        self.assertEqual(account_gate(m), ["9999-99"])

    def test_account_gate_passes_when_all_in_chart(self):
        m = {"_mrerp_accounts": ["1112-01", "2110-01"], "_mrerp_supplier_account": "2110-01"}
        self.assertEqual(account_gate(m), [])


class TestAdapterGateWiring(unittest.TestCase):
    """主动闸接进 upload_invoice_batch:在任何网络前挡下(gate 位于 provision/prepare 之前)。"""

    def _adapter(self):
        from services.erp.mrerp_http.adapter import MrErpHttpAdapter

        return MrErpHttpAdapter(
            login_url="https://x",
            username="u",
            password="p",
            doc_type="sales_cash",
            serialize_sessions=False,
        )

    def test_bad_account_with_chart_fails_before_network(self):
        h = {"id": "x", "client_id": 1, "invoice_date": "2026-07-01", "total_amount": "100"}
        m = {
            "_mrerp_accounts": ["1112-01"],
            "_mrerp_receipt_account_bank": "9999-99",
            "clients": [],
        }
        with self._adapter() as a:  # 无网络(__enter__ 只建 session 对象)
            res = a.upload_invoice_batch([h], m)
        self.assertEqual(len(res.success), 0)
        self.assertEqual(len(res.failed), 1)
        self.assertIn(ACCOUNT_REVIEW_CODE, res.failed[0].reasons)


if __name__ == "__main__":
    unittest.main()
