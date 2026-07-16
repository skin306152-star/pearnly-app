# -*- coding: utf-8 -*-
"""贵模型回落跑批级配额守门(services/ocr/escalation_budget.py + page_runner 闸 · R1 件三)。

锁定:①未设预算 = 无限(非跑批路径行为不变);②设了预算按次递减,扣光即拒;③page_runner
的 L3 视觉回落受预算闸 —— 配额用尽的页不再调贵模型,走既有诚实路径(needs_review),
且 _l3_refine_page 一次都不被调(验收4:第 11 次起不再花贵模型钱)。
"""

from __future__ import annotations

import unittest
from types import SimpleNamespace
from unittest import mock

from services.ocr import escalation_budget, page_runner
from services.ocr.schemas import Layer1Result, Layer2PageResult, Page, ThaiInvoice

_PAGE = Page(page_number=1, width=10, height=10, full_text="x", avg_confidence=1.0, blocks=[])
# sub+vat=total 自洽但 VAT 非净额 7% → 触发 L3(与 totals_rescue 用例同款触发形态)。
_MISREAD = ThaiInvoice(
    document_type="tax_invoice", subtotal="53129.00", vat="4060.05", total_amount="57189.05"
)


def _fake_l1(image_bytes, page_number):
    return Layer1Result(pages=[_PAGE], page_count=1, elapsed_ms=1)


def _fake_l2(l1_page, **kw):
    return Layer2PageResult(page_number=1, invoice=_MISREAD)


class BudgetCounterTests(unittest.TestCase):
    def test_unset_budget_is_unlimited(self):
        # 非跑批路径(未 set_budget):try_escalate 恒放行,升级行为逐字节不变。
        self.assertTrue(escalation_budget.try_escalate())
        self.assertTrue(escalation_budget.try_escalate())

    def test_budget_consumes_then_denies(self):
        budget = escalation_budget.new_budget(2)
        self.assertTrue(budget.try_consume())
        self.assertTrue(budget.try_consume())
        self.assertFalse(budget.try_consume())  # 扣光即拒
        self.assertEqual(budget.remaining, 0)

    def test_try_escalate_reads_context_budget(self):
        token = escalation_budget.set_budget(escalation_budget.new_budget(1))
        try:
            self.assertTrue(escalation_budget.try_escalate())
            self.assertFalse(escalation_budget.try_escalate())  # 用尽
        finally:
            escalation_budget.reset_budget(token)


class PageRunnerBudgetGateTests(unittest.TestCase):
    """page_runner L3 视觉回落受预算闸(验收4)。"""

    def _run_page(self, l3_recorder):
        return page_runner._process_one_page(
            b"\xff\xd8fakejpeg",
            page_number=1,
            api_key=None,
            enable_layer3=True,
            fallback_to_layer2_on_layer3_error=True,
        )

    def _l3(self, calls):
        def refine(**kw):
            calls.append(kw.get("model_name"))
            return SimpleNamespace(invoice=_MISREAD, input_tokens=1, output_tokens=1, elapsed_ms=1)

        return refine

    def test_l3_called_when_budget_available(self):
        calls: list = []
        token = escalation_budget.set_budget(escalation_budget.new_budget(1))
        try:
            with (
                mock.patch.object(page_runner, "_l1_extract_image", _fake_l1),
                mock.patch.object(page_runner, "_l2_extract_page", _fake_l2),
                mock.patch.object(page_runner, "_l3_refine_page", self._l3(calls)),
            ):
                pr = self._run_page(calls)
        finally:
            escalation_budget.reset_budget(token)
        self.assertEqual(len(calls), 1)  # 预算够 → 升贵模型读一次
        self.assertIn("L3", pr.layer_chain)

    def test_l3_skipped_when_budget_exhausted(self):
        # 预算=0(相当于跑批第 11 张):L3 一次都不调,走诚实路径(needs_review)。
        calls: list = []
        token = escalation_budget.set_budget(escalation_budget.new_budget(0))
        try:
            with (
                mock.patch.object(page_runner, "_l1_extract_image", _fake_l1),
                mock.patch.object(page_runner, "_l2_extract_page", _fake_l2),
                mock.patch.object(page_runner, "_l3_refine_page", self._l3(calls)),
            ):
                pr = self._run_page(calls)
        finally:
            escalation_budget.reset_budget(token)
        self.assertEqual(calls, [])  # 贵模型零调用
        self.assertEqual(pr.layer_chain[-1], "L3_skipped_budget")
        self.assertTrue(pr.needs_manual_review)


if __name__ == "__main__":
    unittest.main()
