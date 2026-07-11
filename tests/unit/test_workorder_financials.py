# -*- coding: utf-8 -*-
"""G1a 月度报表:影子科目余额 → BS/PL/TB 纯变换 + reconcile R6 接线 + package 交付物。

护栏:只喂内存影子 payload,零库、零 journal_vouchers。断言会计恒等式(资产=负债+权益)、
PL 净利润链、TB 借=贷、账龄/折旧 not_wired 四态诚实、闸关无 r6 键/无交付物。
"""

import tempfile
import unittest
from decimal import Decimal
from pathlib import Path

from services.accounting import workorder_financials, workorder_shadow_adapter
from services.workorder.steps import financials_report, package, reconcile

from tests.unit.test_workorder_shadow_draft import FakeStore, _two_purchase_store  # noqa: F401


def _shadow_payload(*, purchases, sales_amount, output_vat, period="2569-05"):
    result = workorder_shadow_adapter.build_shadow(
        purchase_entries=purchases,
        sales_amount=sales_amount,
        output_vat=output_vat,
        period=period,
    )
    return result.as_gate_payload()


class BuildFinancialsTests(unittest.TestCase):
    def _golden(self):
        # 单张进项票金标缩比:验恒等式与链条,不依赖真库。
        return _shadow_payload(
            purchases=[{"net": Decimal("1000"), "vat": Decimal("70"), "grand": Decimal("1070")}],
            sales_amount=Decimal("5000"),
            output_vat=Decimal("350"),
        )

    def test_balance_sheet_identity_holds(self):
        fin = workorder_financials.build_financials(self._golden(), period="2569-05")
        bs = fin["balance_sheet"]
        self.assertTrue(bs["balanced"])
        self.assertEqual(Decimal(bs["diff"]), Decimal("0"))
        self.assertEqual(
            Decimal(bs["asset_total"]),
            Decimal(bs["liability_total"]) + Decimal(bs["equity_total"]),
        )

    def test_pnl_net_profit_is_revenue_minus_expense(self):
        fin = workorder_financials.build_financials(self._golden(), period="2569-05")
        pnl = fin["profit_loss"]
        self.assertEqual(
            Decimal(pnl["net_profit"]),
            Decimal(pnl["revenue_total"]) - Decimal(pnl["expense_total"]),
        )
        # 收入 5000 − 费用(净进项)1000 = 4000。
        self.assertEqual(Decimal(pnl["revenue_total"]), Decimal("5000"))
        self.assertEqual(Decimal(pnl["expense_total"]), Decimal("1000"))
        self.assertEqual(Decimal(pnl["net_profit"]), Decimal("4000"))

    def test_trial_balance_debit_equals_credit(self):
        fin = workorder_financials.build_financials(self._golden(), period="2569-05")
        tb = fin["trial_balance"]
        self.assertTrue(tb["balanced"])
        self.assertEqual(Decimal(tb["debit"]), Decimal(tb["credit"]))

    def test_aging_and_depreciation_are_not_wired_not_fake_zero(self):
        fin = workorder_financials.build_financials(self._golden(), period="2569-05")
        self.assertEqual(fin["ar_ap_aging"]["source"], "not_wired")
        self.assertEqual(fin["depreciation"]["source"], "not_wired")
        # 诚实降级不得给出金额字段冒充真值。
        self.assertNotIn("amount", fin["ar_ap_aging"])
        self.assertNotIn("total", fin["depreciation"])

    def test_all_amounts_are_fixed_point_strings_no_float(self):
        fin = workorder_financials.build_financials(self._golden(), period="2569-05")
        self.assertIsInstance(fin["balance_sheet"]["asset_total"], str)
        for row in fin["trial_balance"]["rows"]:
            self.assertIsInstance(row["debit"], str)
            self.assertIsInstance(row["credit"], str)

    def test_returns_none_when_no_accounts(self):
        self.assertIsNone(workorder_financials.build_financials({"note": "skipped"}))
        self.assertIsNone(workorder_financials.build_financials({"accounts": []}))

    def test_non_preset_code_goes_unclassified_not_silently_dropped(self):
        payload = {
            "accounts": [
                {"code": "9999", "name": "学习记忆码", "debit": "100", "credit": "0"},
                {"code": "1130", "name": "应收账款", "debit": "100", "credit": "0"},
            ],
            "trial_balance": {"debit": "200", "credit": "100"},
        }
        fin = workorder_financials.build_financials(payload)
        codes = [u["code"] for u in fin["unclassified_accounts"]]
        self.assertIn("9999", codes)


class ReconcileR6WiringTests(unittest.TestCase):
    def setUp(self):
        self._prev = reconcile._shadow_draft_enabled
        self.addCleanup(setattr, reconcile, "_shadow_draft_enabled", self._prev)

    def _ctx(self, store):
        from services.workorder.engine import StepContext

        return StepContext(cur=None, tenant_id="t-1", work_order_id="wo-1", store=store, data={})

    def test_gate_off_has_no_r6_financials_key(self):
        reconcile._shadow_draft_enabled = lambda ctx: False
        out = reconcile.run(self._ctx(_two_purchase_store()))
        self.assertEqual(out.status, "ok")
        self.assertNotIn("r6_financials", out.payload["gates"])

    def test_gate_on_produces_balanced_financials(self):
        reconcile._shadow_draft_enabled = lambda ctx: True
        out = reconcile.run(self._ctx(_two_purchase_store()))
        fin = out.payload["gates"]["r6_financials"]
        self.assertTrue(fin["balance_sheet"]["balanced"])
        self.assertTrue(fin["trial_balance"]["balanced"])
        self.assertEqual(fin["ar_ap_aging"]["source"], "not_wired")
        # 报表不扰动 R1/R2 税额。
        self.assertEqual(Decimal(out.payload["output_vat_total"]), Decimal("60114.61"))

    def test_period_fetch_failure_isolated(self):
        # ctx.cur=None → _shadow_period 返 None,报表仍产出(period 只是标签)。
        reconcile._shadow_draft_enabled = lambda ctx: True
        out = reconcile.run(self._ctx(_two_purchase_store()))
        self.assertIsNone(out.payload["gates"]["r6_financials"]["period"])


class PackageFinancialsDeliverableTests(unittest.TestCase):
    def _numbers_with_gate(self):
        fin = workorder_financials.build_financials(
            _shadow_payload(
                purchases=[
                    {"net": Decimal("1000"), "vat": Decimal("70"), "grand": Decimal("1070")}
                ],
                sales_amount=Decimal("5000"),
                output_vat=Decimal("350"),
            ),
            period="2569-05",
        )
        return {"period": "2569-05", "gates": {"r6_financials": fin}}

    def test_build_emits_deliverable_when_gate_present(self):
        with tempfile.TemporaryDirectory() as tmp:
            kinds = financials_report.build(Path(tmp), self._numbers_with_gate())
            self.assertIn(financials_report.KIND_FINANCIALS, kinds)
            path, snap = kinds[financials_report.KIND_FINANCIALS]
            md = Path(path).read_text(encoding="utf-8")
            self.assertIn("资产负债表", md)
            self.assertIn("损益表", md)
            self.assertIn("试算平衡", md)
            self.assertIn("not_wired", md)
            self.assertTrue(snap["bs_balanced"])
            self.assertTrue(snap["tb_balanced"])
            self.assertEqual(snap["ar_ap_aging_source"], "not_wired")

    def test_build_returns_empty_when_gate_absent(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(financials_report.build(Path(tmp), {"gates": {}}), {})
            self.assertFalse(list(Path(tmp).iterdir()))

    def test_package_run_does_not_touch_journal_vouchers(self):
        # 护栏:financials 交付物在场,package 渲染不 import/触碰法定表(源码级证)。
        import services.workorder.steps.financials_report as mod

        src = Path(mod.__file__).read_text(encoding="utf-8")
        self.assertNotIn("journal_voucher", src)
        self.assertNotIn("journal_line", src)


if __name__ == "__main__":
    unittest.main()
