# -*- coding: utf-8 -*-
"""qwen 档两臂编排:触发器、升级臂合流、日期确定性换算、与直读主路的接线。

全程 mock 网关,不打真网。守的是"什么时候该花贵模型"这条判据——它错一边是漏读,
错另一边是每张票都按 60 倍单价烧钱。
"""

import unittest
from unittest import mock

from services.ai_gateway.tasks import ProviderOutcome
from services.ocr import direct_read as dr
from services.ocr import engine_policy as ep
from services.ocr import escalation_budget
from services.ocr import qwen_direct as qd

# 真实泰国税号(公开注册信息):校验位合法,改一位就该被 mod-11 抓住。
_TAX_OK = "0105535134278"
_TAX_OK_2 = "0105546015062"
_TAX_BAD = "0105535134271"

_FIELDS_CLEAN = {
    "seller_tax": _TAX_OK,
    "buyer_tax": _TAX_OK_2,
    "invoice_number": "INV-20260811",
    "date": "11/06/2569",
    "subtotal": "65.42",
    "vat": "4.58",
    "total_amount": "70.00",
    "cash": "100.00",
    "change": "30.00",
    "currency": None,
}
_TRANSCRIPT = (
    "ใบกำกับภาษี INV-20260811 เลขประจำตัวผู้เสียภาษี 0105535134278 "
    "ผู้ซื้อ 0105546015062 วันที่ 11/06/2569 รวม 65.42 ภาษี 4.58 สุทธิ 70.00"
)
# 落地校验吃的是 pack 过的转写(编排里整页只 pack 一次,两处比对复用同一个串)。
_PACKED = qd.pack_text(_TRANSCRIPT)


class TriggerTests(unittest.TestCase):
    def test_clean_read_needs_no_escalation(self):
        self.assertEqual(qd.evaluate_triggers(_FIELDS_CLEAN, _PACKED), [])

    def test_subtotal_plus_vat_must_equal_total(self):
        fields = {**_FIELDS_CLEAN, "total_amount": "71.00", "cash": None, "change": None}
        self.assertIn("math_sv", qd.evaluate_triggers(fields, _PACKED))

    def test_cash_minus_change_must_equal_total(self):
        fields = {**_FIELDS_CLEAN, "change": "25.00"}
        self.assertIn("math_cash", qd.evaluate_triggers(fields, _PACKED))

    def test_missing_total_triggers(self):
        fields = {**_FIELDS_CLEAN, "total_amount": None}
        self.assertIn("no_total", qd.evaluate_triggers(fields, _PACKED))

    def test_real_tax_ids_pass_mod11(self):
        for tax in (_TAX_OK, _TAX_OK_2):
            fields = {**_FIELDS_CLEAN, "seller_tax": tax, "buyer_tax": tax}
            triggers = qd.evaluate_triggers(fields, None)
            self.assertNotIn("badsum_seller_tax", triggers)
            self.assertNotIn("badsum_buyer_tax", triggers)

    def test_one_wrong_digit_fails_mod11(self):
        fields = {**_FIELDS_CLEAN, "seller_tax": _TAX_BAD}
        self.assertIn("badsum_seller_tax", qd.evaluate_triggers(fields, None))

    def test_missing_tax_id_is_not_a_checksum_failure(self):
        fields = {**_FIELDS_CLEAN, "seller_tax": None, "buyer_tax": "null"}
        triggers = qd.evaluate_triggers(fields, _PACKED)
        self.assertNotIn("badsum_seller_tax", triggers)
        self.assertNotIn("badsum_buyer_tax", triggers)

    def test_all_zero_tax_is_placeholder_not_misread(self):
        # 票面印全零税号=散客占位:刷洗成缺失,不触发 mod-11 升级更不许整页回落
        # (2026-08-12 生产实测一页因此白花 ฿1.11 走 Vision 回落)
        fields = qd._scrub_placeholder_taxes(
            {**_FIELDS_CLEAN, "buyer_tax": "0000000000000", "seller_tax": "0-0000-00000-00-0"}
        )
        self.assertIsNone(fields["buyer_tax"])
        self.assertIsNone(fields["seller_tax"])
        self.assertNotIn("badsum_buyer_tax", qd.evaluate_triggers(fields, None))

    def test_grounding_ignores_spaces_and_hyphens(self):
        fields = {**_FIELDS_CLEAN, "seller_tax": "0-1055-35134-27-8"}
        self.assertEqual(qd.evaluate_triggers(fields, _PACKED), [])

    def test_field_absent_from_transcript_triggers(self):
        fields = {**_FIELDS_CLEAN, "invoice_number": "INV-99999999"}
        self.assertIn("unground_invoice_number", qd.evaluate_triggers(fields, _PACKED))

    def test_transcript_unavailable_skips_grounding(self):
        fields = {**_FIELDS_CLEAN, "invoice_number": "INV-99999999"}
        self.assertEqual(qd.evaluate_triggers(fields, None), [])


class PrintedDateTests(unittest.TestCase):
    def test_buddhist_printed_date_becomes_gregorian_iso(self):
        self.assertEqual(qd.printed_date_to_iso("11/06/2569"), "2026-06-11")

    def test_gregorian_and_iso_printed_dates(self):
        self.assertEqual(qd.printed_date_to_iso("11/06/2026"), "2026-06-11")
        self.assertEqual(qd.printed_date_to_iso("2026-06-11"), "2026-06-11")

    def test_thai_month_name(self):
        self.assertEqual(qd.printed_date_to_iso("11 มิ.ย. 2569"), "2026-06-11")

    def test_english_month_name(self):
        self.assertEqual(qd.printed_date_to_iso("11 Jun 2026"), "2026-06-11")

    def test_unreadable_date_stays_none(self):
        self.assertIsNone(qd.printed_date_to_iso("ไม่ทราบ"))
        self.assertIsNone(qd.printed_date_to_iso(""))

    def test_printed_date_kept_verbatim_in_date_raw(self):
        out = qd.to_invoice_fields(_FIELDS_CLEAN)
        self.assertEqual(out["date_raw"], "11/06/2569")
        self.assertEqual(out["date"], "2026-06-11")
        self.assertEqual(out["cash_amount"], "100.00")
        self.assertIsNone(out["currency"])


class DocumentTypeTests(unittest.TestCase):
    """document_type 是贷记单硬闸与 ABB 分类的判据(PARTIAL_MODES 解锁条件):
    合法值必须透传,幻觉值必须落 schema 默认,升级臂不许把读取臂的判型清空。"""

    def test_valid_document_type_passes_through(self):
        out = qd.to_invoice_fields({**_FIELDS_CLEAN, "document_type": "credit_note"})
        self.assertEqual(out["document_type"], "credit_note")

    def test_case_and_whitespace_normalized(self):
        out = qd.to_invoice_fields({**_FIELDS_CLEAN, "document_type": " Simplified_Tax_Invoice "})
        self.assertEqual(out["document_type"], "simplified_tax_invoice")

    def test_missing_or_invented_type_falls_to_schema_default(self):
        for bad in (None, "", "null", "ใบกำกับภาษี", "invoice"):
            out = qd.to_invoice_fields({**_FIELDS_CLEAN, "document_type": bad})
            self.assertNotIn("document_type", out)

    def test_both_arm_prompts_ask_for_document_type(self):
        from services.ocr import qwen_prompts

        self.assertIn("document_type", qwen_prompts.FLASH_V25)
        self.assertIn("document_type", qwen_prompts.MAX_V3)


def _json_outcome(data, model="qwen3.7-flash"):
    return ProviderOutcome(ok=True, data=data, model=model, input_tokens=10, output_tokens=5)


def _run_page(read_outcome, escalate_outcome=None, transcript=_TRANSCRIPT):
    """跑一页编排,返回 (结果, 打过的档位序列)。档位序列是"有没有花贵模型"的唯一硬证据。"""
    calls = []

    def _json(prompt, images, **kw):
        calls.append(kw.get("tier"))
        if kw.get("tier") == "flash":
            return read_outcome
        return escalate_outcome or ProviderOutcome(ok=False, error_kind="parse")

    def _text(prompt, images, **kw):
        if transcript is None:
            return ProviderOutcome(ok=False, error_kind="timeout")
        return ProviderOutcome(ok=True, data=transcript, model="qwen-vl-ocr")

    with (
        mock.patch("services.ai_gateway.transport.multimodal_to_json", side_effect=_json),
        mock.patch("services.ai_gateway.transport.multimodal_to_text", side_effect=_text),
    ):
        return qd.read_invoice_page(b"png", "image/png", 1, None), calls


class OrchestrationTests(unittest.TestCase):
    def _run(self, read_outcome, escalate_outcome=None, transcript=_TRANSCRIPT):
        return _run_page(read_outcome, escalate_outcome, transcript)

    def test_clean_page_stops_at_read_arm(self):
        result, calls = self._run(_json_outcome(dict(_FIELDS_CLEAN)))
        self.assertEqual(result.triggers, [])
        self.assertEqual(result.escalate_model, "")
        self.assertEqual(calls, ["flash"])
        self.assertEqual(result.data["total_amount"], "70.00")

    def test_broken_math_escalates_and_takes_the_new_read(self):
        broken = {**_FIELDS_CLEAN, "total_amount": "700.00", "cash": None, "change": None}
        fixed = {**_FIELDS_CLEAN, "cash": None, "change": None}
        result, calls = self._run(_json_outcome(broken), _json_outcome(fixed, model="qwen3.8-max"))
        self.assertIn("math_sv", result.triggers)
        self.assertEqual(calls, ["flash", "escalate"])
        self.assertEqual(result.escalate_model, "qwen3.8-max")
        self.assertEqual(result.data["total_amount"], "70.00")

    def test_ungrounded_id_from_escalate_arm_keeps_read_arm_value(self):
        broken = {**_FIELDS_CLEAN, "total_amount": "700.00"}
        invented = {**_FIELDS_CLEAN, "invoice_number": "TAX-INV-0001"}
        result, _ = self._run(_json_outcome(broken), _json_outcome(invented, model="qwen3.8-max"))
        self.assertEqual(result.data["invoice_number"], "INV-20260811")

    def test_escalate_failure_keeps_read_arm_result(self):
        broken = {**_FIELDS_CLEAN, "total_amount": "700.00"}
        result, _ = self._run(_json_outcome(broken), ProviderOutcome(ok=False, error_kind="quota"))
        self.assertEqual(result.escalate_model, "")
        self.assertEqual(result.data["total_amount"], "700.00")

    def test_read_arm_failure_falls_back_to_vision(self):
        with self.assertRaises(dr.DirectReadFallback):
            self._run(ProviderOutcome(ok=False, error_kind="timeout"))

    def test_escalate_without_document_type_keeps_read_arm_classification(self):
        broken = {**_FIELDS_CLEAN, "total_amount": "700.00", "document_type": "credit_note"}
        fixed = {**_FIELDS_CLEAN}  # 升级臂修好钱数但没出 document_type
        result, _ = self._run(_json_outcome(broken), _json_outcome(fixed, model="qwen3.8-max"))
        self.assertEqual(result.data["document_type"], "credit_note")

    def test_escalate_with_valid_document_type_wins(self):
        broken = {**_FIELDS_CLEAN, "total_amount": "700.00", "document_type": "receipt"}
        fixed = {**_FIELDS_CLEAN, "document_type": "simplified_tax_invoice"}
        result, _ = self._run(_json_outcome(broken), _json_outcome(fixed, model="qwen3.8-max"))
        self.assertEqual(result.data["document_type"], "simplified_tax_invoice")


class EscalationBudgetTests(unittest.TestCase):
    """跑批级回落配额:升级臂是读取臂约 60 倍单价,跑批必须封顶,且封顶不许把触发理由吞掉。"""

    def _run_with_budget(self, limit):
        broken = {**_FIELDS_CLEAN, "total_amount": "700.00", "cash": None, "change": None}
        fixed = {**_FIELDS_CLEAN, "cash": None, "change": None}
        token = escalation_budget.set_budget(escalation_budget.new_budget(limit))
        try:
            return _run_page(
                _json_outcome(dict(broken)), _json_outcome(dict(fixed), model="qwen3.8-max")
            )
        finally:
            escalation_budget.reset_budget(token)

    def test_exhausted_budget_skips_the_expensive_arm(self):
        result, calls = self._run_with_budget(0)
        self.assertEqual(calls, ["flash"])  # 贵模型一次没打
        self.assertEqual(result.escalate_model, "")
        self.assertEqual(result.escalate_tokens, (0, 0))
        self.assertEqual(result.data["total_amount"], "700.00")  # 保留读取臂读数,不丢页

    def test_exhausted_budget_still_records_triggers(self):
        # 不升级 ≠ 当作读对了:触发理由照常带回 trigger_reasons,该页仍走人审
        result, _ = self._run_with_budget(0)
        self.assertIn("math_sv", result.triggers)

    def test_budget_available_escalates_and_consumes_one(self):
        result, calls = self._run_with_budget(1)
        self.assertEqual(calls, ["flash", "escalate"])
        self.assertEqual(result.escalate_model, "qwen3.8-max")

    def test_no_budget_set_means_unlimited(self):
        # 单张 OCR / 主站散单没有跑批配额,行为必须与配额上线前逐字节一致
        broken = {**_FIELDS_CLEAN, "total_amount": "700.00", "cash": None, "change": None}
        result, calls = _run_page(
            _json_outcome(broken), _json_outcome(dict(_FIELDS_CLEAN), model="qwen3.8-max")
        )
        self.assertEqual(calls, ["flash", "escalate"])
        self.assertEqual(result.escalate_model, "qwen3.8-max")


class DirectReadWiringTests(unittest.TestCase):
    """qwen 档在直读主路上的接线:发票页走编排,升级臂记进 L3 观测位,触发器进 trigger_reasons。"""

    def _read_page(self, read_fields, escalate=None):
        def _json(prompt, images, **kw):
            if kw.get("tier") == "flash":
                return _json_outcome(dict(read_fields))
            return escalate or ProviderOutcome(ok=False, error_kind="parse")

        def _text(prompt, images, **kw):
            return ProviderOutcome(ok=True, data=_TRANSCRIPT, model="qwen-vl-ocr")

        cfg = {**ep.DEFAULT_CONFIG, "mode": "qwen"}
        with (
            mock.patch.dict("os.environ", {"OCR_ENGINE_MODE": ""}),
            mock.patch.object(ep, "load_config", return_value=cfg),
            mock.patch("services.ai_gateway.transport.multimodal_to_json", side_effect=_json),
            mock.patch("services.ai_gateway.transport.multimodal_to_text", side_effect=_text),
        ):
            with ep.engine_context("invoice") as mode:
                self.assertEqual(mode, "qwen")
                return dr.read_page(b"png", 1, "invoice", None)

    def test_clean_page_reads_through_qwen_orchestration(self):
        page = self._read_page(_FIELDS_CLEAN)
        self.assertEqual(page.layer_chain, ["ID"])
        self.assertEqual(page.trigger_reasons, [])
        self.assertEqual(page.invoice.total_amount, "70.00")
        self.assertEqual(page.invoice.date, "2026-06-11")
        self.assertEqual(page.layer2_model, "qwen3.7-flash")

    def test_escalated_page_records_second_arm_in_l3_slots(self):
        broken = {**_FIELDS_CLEAN, "invoice_number": "INV-99999999"}
        page = self._read_page(
            broken, escalate=_json_outcome(dict(_FIELDS_CLEAN), model="qwen3.8-max")
        )
        self.assertEqual(page.layer_chain, ["ID", "ID_ESC"])
        self.assertIn("unground_invoice_number", page.trigger_reasons)
        self.assertEqual(page.layer3_model, "qwen3.8-max")
        self.assertTrue(page.layer3_input_tokens or page.layer3_output_tokens)

    def test_long_table_stays_on_the_escalate_arm(self):
        # 轻档读长表会整页读崩 —— qwen 档的银行/总账页必须落升级臂
        with mock.patch.object(ep, "active_mode", return_value="qwen"):
            self.assertEqual(dr._tier_for("bank_statement"), "escalate")
            self.assertEqual(dr._tier_for("general_ledger"), "escalate")
            self.assertEqual(dr._tier_for("invoice"), "flash_lite")
        self.assertEqual(dr._tier_for("bank_statement"), "flash_lite")


if __name__ == "__main__":
    unittest.main()
