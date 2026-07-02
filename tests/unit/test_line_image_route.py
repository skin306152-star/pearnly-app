# -*- coding: utf-8 -*-
"""LINE 图片意图接线层(services/ocr/line_image_route)· LI-2 守门。

铁三条:① 闸关/无意图/任何故障 → Directive 默认值(现状代码逐字节不变的契约面);
② push 终端只出确认卡绝不真推;③ 计费口径与终端无关(nothing 也扣)。全 mock 零真实 IO。
"""

import asyncio
import unittest
from unittest.mock import MagicMock, patch

from services.agent.image_intent import ImageRoute
from services.ocr import line_image_route as r

_USER = {"id": "u-1", "tenant_id": "t-1"}
_EXEC_KW = dict(
    user=_USER,
    ws=84,
    tid="t-1",
    line_user_id="Uabc",
    lang="th",
    quote={"page_count": 1},
    result={"confidence": "high", "elapsed_ms": 5},
    pages=[{"fields": {"invoice_number": "INV-1", "seller_name": "ร้าน A", "total_amount": 100}}],
    cost_thb=0.1,
    filename="a.jpg",
    file_bytes=b"x" * 2048,
    file_hash="h1",
    quote_token="q",
)


def _run(coro):
    return asyncio.run(coro)


class TestIntercept(unittest.TestCase):
    def test_flag_off_returns_inert_directive(self):
        # 闸关 = 现状契约面:handled None · 不覆盖套账 · 不跳记账段。
        with patch("core.feature_flags.agent_image_enabled_for", return_value=False):
            d = _run(r.intercept(_USER, 84, "t-1", "Uabc", "th", {}, {}, [], 0, "a", b"", "h", ""))
        self.assertIsNone(d.handled)
        self.assertIsNone(d.ws)
        self.assertFalse(d.skip_ingest)

    def test_any_crash_is_inert(self):
        # 意图层的任何故障都不许挡记账主路。
        with patch.object(r, "decide", side_effect=RuntimeError("boom")):
            d = _run(r.intercept(_USER, 84, "t-1", "Uabc", "th", {}, {}, [], 0, "a", b"", "h", ""))
        self.assertIsNone(d.handled)

    def test_pending_push_flows_to_confirm_card(self):
        # 话先图后(只推):决策 push → 载体行 + 确认卡,handled=True。
        with (
            patch("core.feature_flags.agent_image_enabled_for", return_value=True),
            patch("core.feature_flags.agent_push_enabled_for", return_value=True),
            patch(
                "services.line_binding.line_intent_store.take_intent",
                return_value={"goals": ["push"]},
            ),
            patch.object(r, "_insert_carrier", return_value="hid-1") as ins,
            patch.object(r, "_send_push_card", return_value=True) as card,
            patch.object(r, "_charge_async") as charge,
            patch.object(r, "_note"),
        ):
            d = _run(
                r.intercept(
                    _USER,
                    84,
                    "t-1",
                    "Uabc",
                    "th",
                    {},
                    {"confidence": "high"},
                    [],
                    0,
                    "a",
                    b"",
                    "h",
                    "",
                )
            )
        self.assertIs(d.handled, True)
        ins.assert_called_once()
        card.assert_called_once()
        charge.assert_called_once()  # 拍板口径:扣(hid 载体行)


class TestExecuteTerminals(unittest.TestCase):
    def test_nothing_charges_and_notifies(self):
        with (
            patch.object(r, "_charge_async") as charge,
            patch.object(r, "_notify") as notify,
            patch.object(r, "_note"),
        ):
            out = _run(r.execute(ImageRoute("nothing"), **_EXEC_KW))
        self.assertIs(out, True)
        self.assertIsNone(charge.call_args.args[2])  # history_id=None,费照扣
        notify.assert_called_once()

    def test_record_and_archive_continue_legacy(self):
        for term in ("record", "archive_only"):
            out = _run(r.execute(ImageRoute(term), **_EXEC_KW))
            self.assertIsNone(out, term)

    def test_dropped_push_tells_user(self):
        with patch.object(r, "_notify") as notify:
            out = _run(r.execute(ImageRoute("record", dropped_push=True), **_EXEC_KW))
        self.assertIsNone(out)
        notify.assert_called_once()

    def test_push_never_executes_push(self):
        # 确认卡 ≠ 执行:整条 push 终端不许出现真推送调用。
        with (
            patch.object(r, "_insert_carrier", return_value="hid-9"),
            patch.object(r, "_charge_async"),
            patch.object(r, "_note"),
            patch("services.agent.push_confirm.send_confirm_card", return_value=True) as card,
            patch("services.agent.push_confirm._execute_push") as never,
            patch.object(
                r.db,
                "list_erp_endpoints",
                return_value=[{"id": "e1", "name": "MR.ERP", "enabled": True}],
            ),
        ):
            out = _run(r.execute(ImageRoute("push"), **_EXEC_KW))
        self.assertIs(out, True)
        card.assert_called_once()
        never.assert_not_called()
        self.assertEqual(card.call_args.args[1], "")  # 异步语境:无 reply_token 走 push 消息

    def test_push_without_endpoint_is_honest(self):
        with (
            patch.object(r, "_insert_carrier", return_value="hid-9"),
            patch.object(r, "_charge_async"),
            patch.object(r, "_note"),
            patch.object(r, "_notify") as notify,
            patch.object(r.db, "list_erp_endpoints", return_value=[]),
        ):
            out = _run(r.execute(ImageRoute("push"), **_EXEC_KW))
        self.assertIs(out, True)  # 载体行留下(识别记录),诚实告知没端点
        notify.assert_called_once()

    def test_carrier_failure_falls_back_to_legacy(self):
        # 载体写不进 → 别吞图:回现状管线保住记账/识别记录。
        with patch.object(r, "_insert_carrier", return_value=None):
            out = _run(r.execute(ImageRoute("push"), **_EXEC_KW))
        self.assertIsNone(out)

    def test_both_with_expense_open_continues_legacy(self):
        cur = MagicMock()
        cm = MagicMock()
        cm.__enter__ = MagicMock(return_value=cur)
        cm.__exit__ = MagicMock(return_value=False)
        with (
            patch.object(r, "_insert_carrier", return_value="hid-2"),
            patch.object(r, "_send_push_card", return_value=True) as card,
            patch.object(r, "_charge_async") as charge,
            patch.object(r.db, "get_cursor_rls", return_value=cm),
            patch("services.purchase.intake.line_expense_gate_open", return_value=True),
        ):
            out = _run(r.execute(ImageRoute("both"), **_EXEC_KW))
        self.assertIsNone(out)  # 继续记账路(计费在那边,只收一次)
        card.assert_called_once()
        charge.assert_not_called()

    def test_both_with_expense_closed_degrades_to_push(self):
        cur = MagicMock()
        cm = MagicMock()
        cm.__enter__ = MagicMock(return_value=cur)
        cm.__exit__ = MagicMock(return_value=False)
        with (
            patch.object(r, "_insert_carrier", return_value="hid-3"),
            patch.object(r, "_send_push_card", return_value=True),
            patch.object(r, "_charge_async") as charge,
            patch.object(r, "_note"),
            patch.object(r.db, "get_cursor_rls", return_value=cm),
            patch("services.purchase.intake.line_expense_gate_open", return_value=False),
        ):
            out = _run(r.execute(ImageRoute("both"), **_EXEC_KW))
        self.assertIs(out, True)
        charge.assert_called_once()


class TestNotInvoiceGuidance(unittest.TestCase):
    """非票据靶向引导:银行对账单认出来指去对账,别再"不像票据"死胡同(真机探针)。"""

    def test_bank_statement_gets_targeted_guidance(self):
        pages = [{"fields": {"document_type": "bank_statement", "is_not_invoice": "true"}}]
        out = r.not_invoice_guidance(pages, "zh")
        self.assertIn("银行对账", out)
        self.assertIn("กระทบยอด", r.not_invoice_guidance(pages, "th"))

    def test_statement_keyword_in_notes_detected(self):
        # 真机探针:费用 OCR 路对流水页只给 document_type=other,真信号在 notes/页原文。
        pages = [
            {
                "fields": {
                    "document_type": "other",
                    "is_not_invoice": "true",
                    "notes": "รายการเดินบัญชีเงินฝากออมทรัพย์ 01/01/2026",
                }
            }
        ]
        self.assertIn("银行对账", r.not_invoice_guidance(pages, "zh"))
        pages2 = [{"fields": {"document_type": "other"}, "text": "STATEMENT OF ACCOUNT ..."}]
        self.assertIn("Bank Reconciliation", r.not_invoice_guidance(pages2, "en"))

    def test_other_non_invoice_falls_back(self):
        self.assertIsNone(r.not_invoice_guidance([{"fields": {"document_type": "photo"}}], "zh"))
        self.assertIsNone(r.not_invoice_guidance([], "zh"))
        self.assertIsNone(r.not_invoice_guidance(None, "zh"))
        self.assertIsNone(r.not_invoice_guidance([{"fields": None}, None], "zh"))

    def test_id_card_gets_dms_guidance(self):
        # 无意图发身份证:靶向指路"先说建 DMS 客户再发"(与对账单同模式同挂点)。
        pages = [{"fields": {"document_type": "id_card", "is_not_invoice": "true"}}]
        self.assertIn("DMS", r.not_invoice_guidance(pages, "zh"))
        pages2 = [
            {
                "fields": {"document_type": "other", "notes": "บัตรประจำตัวประชาชน Thai ID"},
            }
        ]
        self.assertIn("DMS", r.not_invoice_guidance(pages2, "th"))


class TestPreCardSanity(unittest.TestCase):
    """出卡前防呆预检:注定推不过的票不给确认按钮,直接四语人话+留存指引。"""

    def test_implausible_date_blocks_card_with_honest_text(self):
        sent = {}
        with (
            patch.object(r, "_notify", side_effect=lambda *a: sent.setdefault("text", a[2])),
            patch.object(r.db, "list_erp_endpoints") as eps,
        ):
            ok = r._send_push_card(
                _USER,
                84,
                "t-1",
                "Uabc",
                "zh",
                "hid-9",
                ImageRoute("push"),
                [{"fields": {"date": "1970-01-01", "seller_name": "SISTER MAKEUP"}}],
                "q",
            )
        self.assertFalse(ok)
        eps.assert_not_called()  # 预检命中 → 连端点都不该去解析
        self.assertIn("2000", sent["text"])  # 人话文案而非裸码
        self.assertNotIn("date_implausible", sent["text"])

    def test_clean_fields_pass_preflight(self):
        with (
            patch.object(r.db, "list_erp_endpoints", return_value=[]),
            patch.object(r, "_notify") as notify,
        ):
            ok = r._send_push_card(
                _USER,
                84,
                "t-1",
                "Uabc",
                "zh",
                "hid-9",
                ImageRoute("push"),
                [{"fields": {"date": "2026-01-17", "seller_name": "SISTER MAKEUP"}}],
                "q",
            )
        self.assertFalse(ok)  # 无端点 → 走 _NO_ENDPOINT 老路(预检不拦干净票)
        notify.assert_called_once()


class TestCacheShortcut(unittest.TestCase):
    """缓存快路让位契约(真机第一轮踩到:先说目的再重发同图,被 dup 短路吞掉意图)。"""

    _ARGS = (_USER, "Uabc", "h1", 84, "th", "q")

    def test_pending_intent_yields_to_full_pipeline(self):
        # 有活意图 → 整段快路让位(不查 dup 不读缓存),让意图分流吃到这张图。
        with (
            patch.object(r, "_intent_pending", return_value=True),
            patch("services.ocr.line_image_fastpath.early_dup_short_circuit") as dup,
            patch("services.ocr.entrypoints.get_cached_history") as cached,
        ):
            self.assertFalse(r.cache_shortcut(*self._ARGS))
        dup.assert_not_called()
        cached.assert_not_called()

    def test_no_intent_keeps_legacy_shortcuts(self):
        # 无意图 = 搬家前行为:dup 命中 → True;仅缓存命中 → 重建卡 + True;都没有 → False。
        with patch.object(r, "_intent_pending", return_value=False):
            with patch(
                "services.ocr.line_image_fastpath.early_dup_short_circuit", return_value=True
            ):
                self.assertTrue(r.cache_shortcut(*self._ARGS))
            with (
                patch(
                    "services.ocr.line_image_fastpath.early_dup_short_circuit",
                    return_value=False,
                ),
                patch("services.ocr.entrypoints.get_cached_history", return_value={"id": "c1"}),
                patch("services.ocr.line_image_fastpath.handle_ocr_cache_hit") as hit,
            ):
                self.assertTrue(r.cache_shortcut(*self._ARGS))
                hit.assert_called_once()
            with (
                patch(
                    "services.ocr.line_image_fastpath.early_dup_short_circuit",
                    return_value=False,
                ),
                patch("services.ocr.entrypoints.get_cached_history", return_value=None),
            ):
                self.assertFalse(r.cache_shortcut(*self._ARGS))

    def test_intent_pending_is_fail_safe_and_gated(self):
        # 闸关 → 不碰 store;peek 崩 → False(快路照旧),意图层故障不许改主路行为。
        with patch("core.feature_flags.agent_image_enabled_for", return_value=False):
            with patch("services.line_binding.line_intent_store.peek_intent") as peek:
                self.assertFalse(r._intent_pending(_USER, "Uabc"))
            peek.assert_not_called()
        with (
            patch("core.feature_flags.agent_image_enabled_for", return_value=True),
            patch(
                "services.line_binding.line_intent_store.peek_intent",
                side_effect=RuntimeError("db down"),
            ),
        ):
            self.assertFalse(r._intent_pending(_USER, "Uabc"))


class TestDmsShortcut(unittest.TestCase):
    """DMS 绕过点(费用 OCR 之前):双闸都开 + 意图=dms 才接管;其余一律 None=现状。"""

    _ARGS = (_USER, "Uabc", "zh", b"img", "id.jpg", "q")

    def test_gates_off_returns_none_without_reading_intent(self):
        with (
            patch("core.feature_flags.agent_image_enabled_for", return_value=True),
            patch("core.feature_flags.agent_dms_enabled_for", return_value=False),
            patch("services.line_binding.line_intent_store.read_intent") as rd,
        ):
            self.assertIsNone(_run(r._dms_shortcut(*self._ARGS)))
        rd.assert_not_called()

    def test_non_dms_intent_returns_none_without_consuming(self):
        with (
            patch("core.feature_flags.agent_image_enabled_for", return_value=True),
            patch("core.feature_flags.agent_dms_enabled_for", return_value=True),
            patch(
                "services.line_binding.line_intent_store.read_intent",
                return_value={"goals": ["push"]},
            ),
            patch("services.line_binding.line_intent_store.take_intent") as take,
        ):
            self.assertIsNone(_run(r._dms_shortcut(*self._ARGS)))
        take.assert_not_called()  # 非 dms 意图留给 OCR 后的 decide 消费

    def test_dms_intent_takes_and_hands_off(self):
        with (
            patch("core.feature_flags.agent_image_enabled_for", return_value=True),
            patch("core.feature_flags.agent_dms_enabled_for", return_value=True),
            patch(
                "services.line_binding.line_intent_store.read_intent",
                return_value={"goals": ["dms"]},
            ),
            patch("services.line_binding.line_intent_store.take_intent") as take,
            patch("services.agent.dms_push.handle_id_card", return_value=True) as h,
        ):
            self.assertIs(_run(r._dms_shortcut(*self._ARGS)), True)
        take.assert_called_once()
        h.assert_called_once()

    def test_crash_falls_back_to_default_pipeline(self):
        with (
            patch("core.feature_flags.agent_image_enabled_for", return_value=True),
            patch("core.feature_flags.agent_dms_enabled_for", return_value=True),
            patch(
                "services.line_binding.line_intent_store.read_intent",
                side_effect=RuntimeError("db down"),
            ),
        ):
            self.assertIsNone(_run(r._dms_shortcut(*self._ARGS)))


class TestAskTerminal(unittest.TestCase):
    """歧义问询落地:存识别记录(不丢)+ 扣费 + 确定性反问(含重发闭环指引)。"""

    def test_ask_saves_carrier_charges_and_asks(self):
        sent = {}
        with (
            patch.object(r, "_insert_carrier", return_value="hid-a") as ins,
            patch.object(r, "_charge_async") as charge,
            patch.object(r, "_notify", side_effect=lambda *a: sent.setdefault("text", a[2])),
            patch.object(r, "_note"),
        ):
            out = _run(r.execute(ImageRoute("ask", say="大脑的问句"), **_EXEC_KW))
        self.assertIs(out, True)
        ins.assert_called_once()
        self.assertEqual(charge.call_args.args[2], "hid-a")
        # 问句必须是确定性文案(资金面不许用大脑生成文案),且带"回一句+重发"指引。
        self.assertNotIn("大脑的问句", sent["text"])
        self.assertIn("ส่งรูปนี้อีกครั้ง", sent["text"])  # _EXEC_KW lang=th


class TestBrainConsultWiring(unittest.TestCase):
    """歧义问大脑通电:没意图+低置信才问;大脑答只读终端生效,胡答/故障回 default。"""

    def _decide(self, brain_out, confidence="low"):
        with (
            patch("core.feature_flags.agent_image_enabled_for", return_value=True),
            patch("core.feature_flags.agent_push_enabled_for", return_value=False),
            patch("services.line_binding.line_intent_store.take_intent", return_value=None),
            patch("services.agent.image_brain.decide_image", return_value=brain_out) as brain,
        ):
            route = r.decide(
                _USER, 84, "t-1", "Uabc", {"confidence": confidence, "pages": []}, lang="zh"
            )
        return route, brain

    def test_low_confidence_consults_brain(self):
        route, brain = self._decide({"terminal": "nothing", "say": "x"})
        brain.assert_called_once()
        self.assertEqual(route.terminal, "nothing")

    def test_brain_ask_becomes_ask_route(self):
        route, _ = self._decide({"terminal": "ask", "say": "จะให้ทำอะไรคะ"})
        self.assertEqual(route.terminal, "ask")

    def test_brain_push_is_corrected_to_ask(self):
        # 钱路红线:大脑硬答 push 一律矫成 ask(不可逆动作必须来自用户原话)。
        route, _ = self._decide({"terminal": "push"})
        self.assertEqual(route.terminal, "ask")

    def test_high_confidence_never_consults(self):
        route, brain = self._decide({"terminal": "nothing"}, confidence="high")
        brain.assert_not_called()
        self.assertIsNone(route)  # default → None = 现状管线

    def test_brain_junk_falls_back_to_default(self):
        route, _ = self._decide(None)
        self.assertIsNone(route)


if __name__ == "__main__":
    unittest.main()
