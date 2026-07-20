# -*- coding: utf-8 -*-
"""折扣回填必须留痕留人(A-1 · 2026-07-20)。

`sanity.infer_missing_discount` 会把「小计+VAT−总额」的差额当成漏抓的折扣回填进发票。
回填改的是票面钱字段,而回填后 `_check_amount_math` 与 sanity 硬闸**自动放行**——
本文件顶部的 TriggersGoQuietTests 就是这条事实的现场:同一张票,回填前 triggers 报
amount math fail(会引出 L3 视觉复读),回填后 triggers 为空。

差额的真身可能是选错列或漏读一位,被包装成折扣后就再没人看得见。所以:改写可以自动,
消警必须留人。两条读数链(Vision 路 page_runner / 直读路 direct_read)同口径,工单侧
给它专属 flag_reason —— 此前是靠回填文案里的「折」字撞进 classify._MATH_HINTS 才被拦,
文案改一个字就静默失守,而且人看到的是「票面自身不自洽」(实际三个数是平的)。
"""

from __future__ import annotations

import unittest
from unittest import mock

from services.ai_gateway.tasks import ProviderOutcome
from services.ocr import direct_read, page_runner
from services.ocr.sanity import DISCOUNT_INFERRED_PREFIX, infer_missing_discount
from services.ocr.schemas import Layer1Result, Layer2PageResult, Page, ThaiInvoice
from services.workorder import verdict
from services.workorder.steps import classify

# f003 真案(prod 落库原样):小计 5210 + VAT 354.90 = 5564.90,票面合计 5424.90,差 140;
# 且 (5210−140)×7% = 354.90 —— 双重勾稽成立,回填条件命中。
_MISREAD = {
    "document_type": "tax_invoice",
    "invoice_number": "INV2026030003",
    "subtotal": "5210.00",
    "vat": "354.90",
    "total_amount": "5424.90",
}

# L1 全文必须印着这些数字。夹具若只放 "x",会另触发「值不在票面文本里」类 trigger 把 L3
# 引出来,测的就不是折扣回填这条路了(2026-07-20 复现时踩过)。
_FULL_TEXT = (
    "ใบกำกับภาษี / TAX INVOICE\n"
    "เลขที่ INV2026030003\n"
    "รวมเป็นเงิน 5,210.00\n"
    "ส่วนลด 140.00\n"
    "ภาษีมูลค่าเพิ่ม 7% 354.90\n"
    "จำนวนเงินรวมทั้งสิ้น 5,424.90\n"
)
_PAGE = Page(
    page_number=1, width=10, height=10, full_text=_FULL_TEXT, avg_confidence=0.97, blocks=[]
)


class _FakeProvider:
    """同 tests/unit/test_direct_read.py:每次调用同稿(双读若开,两读一致不制造分歧)。"""

    def __init__(self, outcome):
        self._outcome = outcome
        self.calls = 0

    def multimodal_to_json(self, prompt, images, **kw):
        self.calls += 1
        return self._outcome


def _fake_l1(image_bytes, page_number):
    return Layer1Result(pages=[_PAGE], page_count=1, elapsed_ms=1)


def _fake_l2(l1_page, **kw):
    return Layer2PageResult(page_number=1, invoice=ThaiInvoice(**_MISREAD))


def _l3_must_not_run(**kw):
    raise AssertionError("L3 不该被调用:回填已让 triggers 转静,这里要验的是留人而非复读")


class TriggersGoQuietTests(unittest.TestCase):
    """回填把闸从响改成不响 —— 这是本类问题的病根,先把它钉成断言。"""

    def test_backfill_silences_the_amount_math_trigger(self):
        before = ThaiInvoice(**_MISREAD)
        self.assertTrue(
            any(
                "amount math fail" in t for t in page_runner._evaluate_triggers(_PAGE, before, None)
            )
        )
        after = ThaiInvoice(**_MISREAD)
        note = infer_missing_discount(after)
        self.assertIsNotNone(note)
        self.assertEqual(after.discount, "140.00")
        self.assertEqual(page_runner._evaluate_triggers(_PAGE, after, None), [])


class VisionPathTests(unittest.TestCase):
    def _run(self):
        with (
            mock.patch.object(page_runner, "_l1_extract_image", _fake_l1),
            mock.patch.object(page_runner, "_l2_extract_page", _fake_l2),
            mock.patch.object(page_runner, "_l3_refine_page", _l3_must_not_run),
        ):
            return page_runner._process_one_page(
                b"\xff\xd8fakejpeg",
                page_number=1,
                api_key=None,
                enable_layer3=True,
                fallback_to_layer2_on_layer3_error=True,
            )

    def test_backfilled_page_is_left_for_a_human(self):
        pr = self._run()
        self.assertEqual(pr.invoice.discount, "140.00")
        self.assertTrue(pr.needs_manual_review)
        self.assertEqual(pr.confidence_band, "needs_review")

    def test_backfill_note_is_carried_with_a_machine_readable_prefix(self):
        pr = self._run()
        notes = [w for w in pr.validation_warnings if w.startswith(DISCOUNT_INFERRED_PREFIX)]
        self.assertEqual(len(notes), 1, pr.validation_warnings)
        self.assertIn("140.00", notes[0])


class DirectReadPathTests(unittest.TestCase):
    """直读路走 _invoice_hard_gates:回填后硬闸不再抛回落,置信只降 0.05 压不到 needs_review。"""

    def test_hard_gates_pass_but_emit_the_prefixed_note(self):
        inv = ThaiInvoice(**_MISREAD)
        notes = direct_read._invoice_hard_gates(inv, 1)
        self.assertEqual(inv.discount, "140.00")
        self.assertTrue(any(n.startswith(DISCOUNT_INFERRED_PREFIX) for n in notes), notes)

    def test_read_page_leaves_the_backfilled_invoice_for_a_human(self):
        """整条 read_page 的出场结论 —— 只验 notes 等于没验留人(band 才是下游读的那位)。"""
        outcome = ProviderOutcome(ok=True, data=dict(_MISREAD, is_not_invoice=False), model="m")
        with mock.patch(
            "services.ai_gateway.backends.get_provider", return_value=_FakeProvider(outcome)
        ):
            pr = direct_read.read_page(b"\xff\xd8fakejpeg", page_number=1, document_type="invoice")
        self.assertEqual(pr.invoice.discount, "140.00")
        self.assertTrue(pr.needs_manual_review)
        self.assertEqual(pr.confidence_band, "needs_review")


class WorkorderGateReasonTests(unittest.TestCase):
    def test_backfill_gets_its_own_flag_reason(self):
        fields = {
            "_validation_warnings": [f"{DISCOUNT_INFERRED_PREFIX} 票面折扣 140.00 未被提取,…"],
            "_needs_review": True,
            "_confidence_band": "needs_review",
        }
        self.assertEqual(classify._gate_reason(fields), "discount_inferred")

    def test_real_math_failure_still_reads_as_math_failure(self):
        fields = {
            "_validation_warnings": ["amount math fail: 小计 100 + vat 7 != total 200"],
            "_needs_review": True,
        }
        self.assertEqual(classify._gate_reason(fields), "amount_math_fail")


class VerdictPolicyTests(unittest.TestCase):
    def test_policy_names_the_amount_and_offers_no_safe_default(self):
        hint = verdict.hint(flag_reason="discount_inferred", ocr_read={"discount": "140.00"})
        self.assertEqual(hint["narrative_key"], "verdict_discount_inferred")
        self.assertEqual(hint["params"], {"discount": "140.00"})
        self.assertEqual(hint["severity"], verdict.SEV_CRIT)
        # 批量「全部按建议处理」不许替人认下系统自己补的数字。
        self.assertIsNone(hint["suggested_decision"])


class MoneySnapshotTests(unittest.TestCase):
    def test_discount_rides_along_in_the_money_snapshot(self):
        from services.workorder.steps import ocr_snapshots

        snap = ocr_snapshots.money_fields({"subtotal": "5210.00", "discount": "140.00"})
        self.assertEqual(snap["discount"], "140.00")


if __name__ == "__main__":
    unittest.main(verbosity=2)
