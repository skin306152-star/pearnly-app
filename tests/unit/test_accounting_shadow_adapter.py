# -*- coding: utf-8 -*-
"""影子底稿适配器单测(F1 · services/accounting/workorder_shadow_adapter.py)。

纯函数:已裁进项分录 + 聚合销项 → 建议分录/科目余额/试算平衡。覆盖:每张进项票分录金额
= 票面反解值(手算核对 3 张)、销项 R4 分录、VAT 结转 R9 方向、进/销项税经结转对冲归零、
整体试算平衡 Σ借=Σ贷 diff≤0.01、费用无科目回落 expense_default 标 category_unmapped、空输入。
护栏:本模块只经 rules + coa_preset 出分录,不碰 posting/vouchers(架构层 grep 佐证)。
"""

import unittest
from decimal import Decimal

from services.accounting import coa_preset, workorder_shadow_adapter as adapter


def _pe(net, vat, grand):
    return {"net": Decimal(net), "vat": Decimal(vat), "grand": Decimal(grand)}


def _rows(result, source):
    return [e for e in result.entries if e["source"] == source]


def _amt(rows, code, dr_cr):
    hit = [Decimal(e["amount"]) for e in rows if e["account_code"] == code and e["dr_cr"] == dr_cr]
    return hit[0] if hit else None


CODE_EXPENSE = coa_preset.ROLE_DEFAULTS["expense_default"]  # 5290
CODE_INPUT_VAT = coa_preset.ROLE_DEFAULTS["input_vat"]  # 1140
CODE_AP = coa_preset.ROLE_DEFAULTS["ap"]  # 2010
CODE_AR = coa_preset.ROLE_DEFAULTS["ar"]  # 1130
CODE_SALES = coa_preset.ROLE_DEFAULTS["sales_revenue"]  # 4010
CODE_OUTPUT_VAT = coa_preset.ROLE_DEFAULTS["output_vat"]  # 2030
CODE_VAT_PAYABLE = coa_preset.ROLE_DEFAULTS["vat_payable"]  # 2040
CODE_VAT_RECEIVABLE = coa_preset.ROLE_DEFAULTS["vat_receivable"]  # 1160


class PerInvoiceHandCalcTests(unittest.TestCase):
    """逐张进项票分录金额 = 票面反解值(手算核对 3 张:借[净]+借[进项税]=贷[应付])。"""

    def test_three_invoices_entries_match_face_value(self):
        entries = [
            _pe("1000.00", "70.00", "1070.00"),
            _pe("200.00", "14.00", "214.00"),
            _pe("58128.57", "4069.05", "62197.62"),
        ]
        r = adapter.build_shadow(
            purchase_entries=entries, sales_amount=Decimal("0"), output_vat=Decimal("0")
        )
        # 票 #1:借 费用 1000 / 借 进项税 70 / 贷 应付 1070
        rows1 = _rows(r, "进项票 #1")
        self.assertEqual(_amt(rows1, CODE_EXPENSE, "debit"), Decimal("1000.00"))
        self.assertEqual(_amt(rows1, CODE_INPUT_VAT, "debit"), Decimal("70.00"))
        self.assertEqual(_amt(rows1, CODE_AP, "credit"), Decimal("1070.00"))
        # 票 #2:借 费用 200 / 借 进项税 14 / 贷 应付 214
        rows2 = _rows(r, "进项票 #2")
        self.assertEqual(_amt(rows2, CODE_EXPENSE, "debit"), Decimal("200.00"))
        self.assertEqual(_amt(rows2, CODE_INPUT_VAT, "debit"), Decimal("14.00"))
        self.assertEqual(_amt(rows2, CODE_AP, "credit"), Decimal("214.00"))
        # 票 #3(折扣淡票修正后):借 费用 58128.57 / 借 进项税 4069.05 / 贷 应付 62197.62
        rows3 = _rows(r, "进项票 #3")
        self.assertEqual(_amt(rows3, CODE_EXPENSE, "debit"), Decimal("58128.57"))
        self.assertEqual(_amt(rows3, CODE_INPUT_VAT, "debit"), Decimal("4069.05"))
        self.assertEqual(_amt(rows3, CODE_AP, "credit"), Decimal("62197.62"))

    def test_ocr_purchase_net_lands_in_expense_default(self):
        r = adapter.build_shadow(
            purchase_entries=[_pe("1000.00", "70.00", "1070.00")],
            sales_amount=Decimal("0"),
            output_vat=Decimal("0"),
        )
        # OCR 票无行级商品/科目 → 净额落 expense_default(5290,杂项费用),这是 rules 直接给的已配
        # role,不虚报 category_unmapped(该扣分点专留给 expense:{category_id} 无静态配的场景)。
        rows = _rows(r, "进项票 #1")
        self.assertEqual(_amt(rows, CODE_EXPENSE, "debit"), Decimal("1000.00"))
        self.assertNotIn("category_unmapped", r.uncertainties)


class SalesEntryTests(unittest.TestCase):
    """聚合销项 R4:借 应收 = 贷 收入 + 销项税。"""

    def test_sale_entries_split_revenue_and_output_vat(self):
        r = adapter.build_shadow(
            purchase_entries=[],
            sales_amount=Decimal("858780.16"),
            output_vat=Decimal("60114.61"),
        )
        rows = _rows(r, "聚合销项")
        self.assertEqual(_amt(rows, CODE_AR, "debit"), Decimal("918894.77"))
        self.assertEqual(_amt(rows, CODE_SALES, "credit"), Decimal("858780.16"))
        self.assertEqual(_amt(rows, CODE_OUTPUT_VAT, "credit"), Decimal("60114.61"))


class VatClosingTests(unittest.TestCase):
    """R9 结转方向:销>进=应交 vat_payable;进>销=留抵 vat_receivable。"""

    def test_payable_when_output_exceeds_input(self):
        r = adapter.build_shadow(
            purchase_entries=[_pe("1000.00", "70.00", "1070.00")],
            sales_amount=Decimal("5000.00"),
            output_vat=Decimal("350.00"),
        )
        rows = _rows(r, "VAT 结转")
        # 销项税 350 − 进项税 70 = 应交 280(贷 vat_payable)。
        self.assertEqual(_amt(rows, CODE_VAT_PAYABLE, "credit"), Decimal("280.00"))
        # 结转把两个税科目对冲:进项税(1140)借 70 后贷 70 → 净额 0;销项税(2030)贷 350 后借 350 → 0。
        by_code = {a["code"]: a for a in r.accounts}
        self.assertEqual(Decimal(by_code[CODE_INPUT_VAT]["balance"]), Decimal("0"))
        self.assertEqual(Decimal(by_code[CODE_OUTPUT_VAT]["balance"]), Decimal("0"))

    def test_receivable_when_input_exceeds_output(self):
        r = adapter.build_shadow(
            purchase_entries=[_pe("1000.00", "70.00", "1070.00")],
            sales_amount=Decimal("0"),
            output_vat=Decimal("0"),
        )
        rows = _rows(r, "VAT 结转")
        # 无销项、进项税 70 → 全额留抵(借 vat_receivable 70)。
        self.assertEqual(_amt(rows, CODE_VAT_RECEIVABLE, "debit"), Decimal("70.00"))


class TrialBalanceTests(unittest.TestCase):
    """试算平衡金标:Σ借=Σ贷,balanced=True,diff≤0.01。"""

    def test_full_batch_balanced(self):
        entries = [
            _pe("1000.00", "70.00", "1070.00"),
            _pe("200.00", "14.00", "214.00"),
            _pe("58128.57", "4069.05", "62197.62"),
        ]
        r = adapter.build_shadow(
            purchase_entries=entries,
            sales_amount=Decimal("858780.16"),
            output_vat=Decimal("60114.61"),
        )
        tb = r.trial_balance
        self.assertTrue(tb["balanced"])
        self.assertLessEqual(Decimal(tb["diff"]), Decimal("0.01"))
        self.assertEqual(Decimal(tb["debit"]), Decimal(tb["credit"]))

    def test_empty_input_is_trivially_balanced(self):
        r = adapter.build_shadow(
            purchase_entries=[], sales_amount=Decimal("0"), output_vat=Decimal("0")
        )
        self.assertTrue(r.trial_balance["balanced"])
        self.assertEqual(Decimal(r.trial_balance["diff"]), Decimal("0"))
        self.assertEqual(r.entries, [])

    def test_gate_payload_shape_is_json_serializable(self):
        r = adapter.build_shadow(
            purchase_entries=[_pe("1000.00", "70.00", "1070.00")],
            sales_amount=Decimal("5000.00"),
            output_vat=Decimal("350.00"),
        )
        payload = r.as_gate_payload()
        for key in ("entries", "accounts", "trial_balance", "sources", "uncertainties"):
            self.assertIn(key, payload)
        # 全字符串金额(无 Decimal/float 漏进 JSON 面)。
        for e in payload["entries"]:
            self.assertIsInstance(e["amount"], str)
        self.assertIsInstance(payload["trial_balance"]["debit"], str)


if __name__ == "__main__":
    unittest.main()
