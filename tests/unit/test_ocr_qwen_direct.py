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

# 现金票形态:收银机简式票无 subtotal/vat 结构,cash−change=total 自洽 ——
# F19 病灶:旧谓词 _money_consistent 因 sub/vat 缺失判 False,现金票 68% 仍打转写臂。
_CASH_RECEIPT = {**_FIELDS_CLEAN, "subtotal": None, "vat": None}


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
        # 票面印全零税号=散客占位:原地刷洗成缺失,不触发 mod-11 升级更不许整页回落
        # (2026-08-12 生产实测一页因此白花 ฿1.11 走 Vision 回落)
        fields = {**_FIELDS_CLEAN, "buyer_tax": "0000000000000", "seller_tax": "0-0000-00000-00-0"}
        qd._scrub_placeholder_taxes(fields)
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

    def test_read_prompt_carries_thai_month_abbreviation_table(self):
        # F18 防回退:泰文缩写月份表必须留在读取臂提示词(พ.ค.=5月 误读成 ม.ค.=1月 病灶);
        # 口径与 id_card_extract 同表,且带 "เม.ย.=04 不是 05" 的显式注记
        self.assertIn("ม.ค.=01", qd._READ_PROMPT)
        self.assertIn("พ.ค.=05", qd._READ_PROMPT)
        self.assertIn("เม.ย. is month 04 (April), NOT 05", qd._READ_PROMPT)

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
    """跑一页编排,返回 (结果, 打过的档位序列)。档位序列是"有没有花贵模型"的唯一硬证据;
    转写臂也进序列("transcribe" 标记)——惰性转写(F14)后,转写是否被跳过必须看得见。"""
    calls = []

    def _json(prompt, images, **kw):
        calls.append(kw.get("tier"))
        if kw.get("tier") == "flash":
            return read_outcome
        return escalate_outcome or ProviderOutcome(ok=False, error_kind="parse")

    def _text(prompt, images, **kw):
        calls.append("transcribe")
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
        self.assertEqual(calls, ["flash", "transcribe", "escalate"])
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


class MoneyGateTests(unittest.TestCase):
    """金额闸(F13):钱面自洽时纯文本差异(unground_*)不升级 —— 升级臂贵且慢,金额一致
    说明入账数没问题,单号/日期差一个字不影响记账;金额不一致或读不出才是真冲突。

    判据=subtotal/vat/total 三件 Decimal 解析成功且 subtotal+vat≈total(容差 0.01)。
    """

    def test_text_diff_with_consistent_money_does_not_escalate(self):
        # 金额自洽(65.42+4.58=70.00)+ 单号文本差异 → 不升级,保留读取臂读数
        unground = {**_FIELDS_CLEAN, "invoice_number": "INV-99999999"}
        result, calls = self._run(_json_outcome(unground))
        self.assertEqual(calls, ["flash"])  # 升级臂一次没打
        self.assertEqual(result.escalate_model, "")
        self.assertEqual(result.triggers, [])  # 文本差异被金额闸滤掉,不再交人审
        self.assertEqual(result.data["total_amount"], "70.00")

    def test_money_mismatch_still_escalates(self):
        # total 差 0.10(超出 0.05 勾稽容差)→ math_sv 触发 → 转写照打,unground_* 也升;
        # 金额不自洽 → 闸不滤 → 升级臂裁决。0.02 档的差在勾稽容差内,不再值得 max 仲裁
        # (是否打转写由惰性转写谓词管,见 LazyTranscribeTests)。
        broken = {**_FIELDS_CLEAN, "invoice_number": "INV-99999999", "total_amount": "70.10"}
        result, calls = self._run(
            _json_outcome(broken), _json_outcome(dict(_FIELDS_CLEAN), model="qwen3.8-max")
        )
        self.assertEqual(calls, ["flash", "transcribe", "escalate"])
        self.assertEqual(result.escalate_model, "qwen3.8-max")

    def test_money_parse_failure_escalates_conservatively(self):
        # 金额缺失 → no_total 是 det 触发器 → 转写照打并升级(宁多花一次,不放过可能读错的金额)
        broken = {**_FIELDS_CLEAN, "invoice_number": "INV-99999999", "total_amount": None}
        result, calls = self._run(
            _json_outcome(broken), _json_outcome(dict(_FIELDS_CLEAN), model="qwen3.8-max")
        )
        self.assertEqual(calls, ["flash", "transcribe", "escalate"])
        self.assertEqual(result.escalate_model, "qwen3.8-max")

    def test_switch_off_restores_old_behavior(self):
        # OCR_ESCALATE_MONEY_GATE=0 → 金额一致也照旧升级(回滚开关);此时惰性转写的
        # 跳过条件不成立(gate 关着,unground_* 不会被滤掉),转写照打 —— 两个开关各自诚实。
        unground = {**_FIELDS_CLEAN, "invoice_number": "INV-99999999"}
        with mock.patch.dict("os.environ", {"OCR_ESCALATE_MONEY_GATE": "0"}):
            result, calls = self._run(
                _json_outcome(unground), _json_outcome(dict(_FIELDS_CLEAN), model="qwen3.8-max")
            )
        self.assertEqual(calls, ["flash", "transcribe", "escalate"])
        self.assertEqual(result.escalate_model, "qwen3.8-max")
        self.assertIn("unground_invoice_number", result.triggers)

    def test_gate_only_filters_text_diff_keeps_money_math_trigger(self):
        # math_sv 是真钱面冲突,金额闸不许拦它
        broken = {**_FIELDS_CLEAN, "total_amount": "71.00", "cash": None, "change": None}
        triggers = qd.evaluate_triggers(broken, _PACKED)
        self.assertIn("math_sv", triggers)
        self.assertIn("math_sv", qd._apply_money_gate(broken, triggers))

    def _run(self, read_outcome, escalate_outcome=None):
        return _run_page(read_outcome, escalate_outcome)


class LazyTranscribeTests(unittest.TestCase):
    """惰性转写(F14,F19 谓词泛化):转写臂唯一消费方是 unground_* 落地校验 —— 跳过判据 =
    fields-only 确定性触发器(math_*/badsum_*/no_total)评估为空:det 空 = 转写产出必被
    丢弃(纯文本差异要么被金额闸滤掉、要么钱面勾稽已自洽到无升级必要,现金票即此类)。
    det 非空(金额对不上/读不出)→ 照打转写:金额不自洽时闸不滤 unground_*,升级证据
    要靠它增补,且升级臂要夹转写重读,保守不走捷径。
    跳过条件还挂 _money_gate_enabled():gate 关着时 unground_* 照旧升级,转写必须有。"""

    def test_fields_only_triggers_empty_skips_transcribe_arm(self):
        # det 空(金额自洽 + 税号合法)→ 转写臂零调用,unground_* 无从产生,不升级
        unground = {**_FIELDS_CLEAN, "invoice_number": "INV-99999999"}
        result, calls = self._run(_json_outcome(unground))
        self.assertEqual(calls, ["flash"])  # 无 "transcribe" 标记 = 转写臂一次没打
        self.assertEqual(result.triggers, [])
        self.assertEqual(result.escalate_model, "")
        self.assertEqual(result.data["total_amount"], "70.00")

    def test_cash_receipt_skips_transcribe_arm(self):
        # F19 病灶:现金票 subtotal/vat 空 → 旧谓词 _money_consistent 判 False,68% 仍打转写;
        # 泛化后 cash−change=total 自洽 + 税号合法 → det 空 → 零转写
        result, calls = self._run(_json_outcome(dict(_CASH_RECEIPT)))
        self.assertEqual(calls, ["flash"])
        self.assertEqual(result.triggers, [])
        self.assertEqual(result.escalate_model, "")

    def test_badsum_deterministic_trigger_transcribes(self):
        # badsum_* 是 det 触发器(只看字段的 mod-11):非空 → 照打转写,升级证据不留死角
        bad_tax = {**_FIELDS_CLEAN, "seller_tax": _TAX_BAD}
        result, calls = self._run(
            _json_outcome(bad_tax), _json_outcome(dict(_FIELDS_CLEAN), model="qwen3.8-max")
        )
        self.assertEqual(calls, ["flash", "transcribe", "escalate"])
        self.assertEqual(result.escalate_model, "qwen3.8-max")
        self.assertIn("badsum_seller_tax", result.triggers)

    def test_math_mismatch_transcribes_and_escalates(self):
        # total 差 0.10(超出 0.05 勾稽容差)→ math_sv 触发 → 照打转写并升级
        broken = {**_FIELDS_CLEAN, "invoice_number": "INV-99999999", "total_amount": "70.10"}
        result, calls = self._run(
            _json_outcome(broken), _json_outcome(dict(_FIELDS_CLEAN), model="qwen3.8-max")
        )
        self.assertEqual(calls, ["flash", "transcribe", "escalate"])
        self.assertIn("unground_invoice_number", result.triggers)

    def test_cash_receipt_math_break_still_transcribes(self):
        # 现金票找零对不上 → math_cash 是 det 触发器 → 照打转写(现金票跳过只限自洽票)
        broken = {**_CASH_RECEIPT, "change": "25.00"}
        result, calls = self._run(
            _json_outcome(broken), _json_outcome(dict(_FIELDS_CLEAN), model="qwen3.8-max")
        )
        self.assertIn("transcribe", calls)
        self.assertIn("math_cash", result.triggers)
        self.assertEqual(result.escalate_model, "qwen3.8-max")

    def test_no_total_still_transcribes(self):
        # 金额缺失 → no_total 是 det 触发器 → 照打转写并升级
        broken = {**_FIELDS_CLEAN, "total_amount": None}
        result, calls = self._run(
            _json_outcome(broken), _json_outcome(dict(_FIELDS_CLEAN), model="qwen3.8-max")
        )
        self.assertIn("transcribe", calls)
        self.assertEqual(result.escalate_model, "qwen3.8-max")

    def test_unparseable_subtotal_with_clean_math_skips(self):
        # subtotal 不可解但其余字段全自洽 → det 空 → 零转写(解析失败的保守升级只挂在
        # det 触发器上:no_total / 超容差勾稽才值得 max 档仲裁)
        unparseable = {**_FIELDS_CLEAN, "subtotal": "not-a-number"}
        result, calls = self._run(_json_outcome(unparseable))
        self.assertEqual(calls, ["flash"])
        self.assertEqual(result.escalate_model, "")
        self.assertEqual(result.triggers, [])

    def test_lazy_switch_off_restores_always_transcribe(self):
        # OCR_LAZY_TRANSCRIBE=0 → det 空也照打转写(串行,不恢复 F3 并行);
        # 闸还开着,文本差异仍被滤掉 → 不升级,但转写臂确实打了
        unground = {**_FIELDS_CLEAN, "invoice_number": "INV-99999999"}
        with mock.patch.dict("os.environ", {"OCR_LAZY_TRANSCRIBE": "0"}):
            result, calls = self._run(_json_outcome(unground))
        self.assertEqual(calls, ["flash", "transcribe"])
        self.assertEqual(result.escalate_model, "")
        self.assertEqual(result.triggers, [])

    def _run(self, read_outcome, escalate_outcome=None):
        return _run_page(read_outcome, escalate_outcome)


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
        self.assertEqual(calls, ["flash", "transcribe"])  # 贵模型一次没打,转写臂不受配额管
        self.assertEqual(result.escalate_model, "")
        self.assertEqual(result.escalate_tokens, (0, 0))
        self.assertEqual(result.data["total_amount"], "700.00")  # 保留读取臂读数,不丢页

    def test_exhausted_budget_still_records_triggers(self):
        # 不升级 ≠ 当作读对了:触发理由照常带回 trigger_reasons,该页仍走人审
        result, _ = self._run_with_budget(0)
        self.assertIn("math_sv", result.triggers)

    def test_budget_available_escalates_and_consumes_one(self):
        result, calls = self._run_with_budget(1)
        self.assertEqual(calls, ["flash", "transcribe", "escalate"])
        self.assertEqual(result.escalate_model, "qwen3.8-max")

    def test_no_budget_set_means_unlimited(self):
        # 单张 OCR / 主站散单没有跑批配额,行为必须与配额上线前逐字节一致
        broken = {**_FIELDS_CLEAN, "total_amount": "700.00", "cash": None, "change": None}
        result, calls = _run_page(
            _json_outcome(broken), _json_outcome(dict(_FIELDS_CLEAN), model="qwen3.8-max")
        )
        self.assertEqual(calls, ["flash", "transcribe", "escalate"])
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
        # 金额闸生效后,纯文本差异不再升级 → 本测试必须同时带钱面冲突才能走到升级臂;
        # 0.10 差超出勾稽容差 → math_sv 触发 → 转写照打,unground_* 一并进升级判断
        broken = {**_FIELDS_CLEAN, "invoice_number": "INV-99999999", "total_amount": "70.10"}
        page = self._read_page(
            broken, escalate=_json_outcome(dict(_FIELDS_CLEAN), model="qwen3.8-max")
        )
        self.assertEqual(page.layer_chain, ["ID", "ID_ESC"])
        self.assertIn("unground_invoice_number", page.trigger_reasons)
        self.assertEqual(page.layer3_model, "qwen3.8-max")
        self.assertTrue(page.layer3_input_tokens or page.layer3_output_tokens)

    def test_long_table_uses_flash_arm_with_max_as_escalate_fallback(self):
        # 2026-08-13 档位调整:qwen 长表 flash 先读,max 留升级兜底(单页成本 ฿1.15→฿0.024)
        with mock.patch.object(ep, "active_mode", return_value="qwen"):
            self.assertEqual(dr._tier_for("bank_statement"), "flash")
            self.assertEqual(dr._tier_for("general_ledger"), "flash")
            self.assertEqual(dr._tier_for("invoice"), "flash_lite")
        self.assertEqual(dr._tier_for("bank_statement"), "flash_lite")


if __name__ == "__main__":
    unittest.main()
