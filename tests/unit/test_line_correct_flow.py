# -*- coding: utf-8 -*-
"""LINE 改错多轮会话态机(line_correct_flow · P1E-2 二轮):字段澄清 → 收新值 → 确认。

锁:① 答字段名续接问新值;② 收新值(含全角冒号/前缀/裸值)→ 出确认;③ 多行金额引导详情页;
④ pending 态分发优先。真库改账(_apply)由 line_correct 测试 + 真账号 E2E 守。
"""

import contextlib
import unittest
from decimal import Decimal
from unittest import mock

from services.expense import line_correct, line_correct_flow as flow


class _Ctx:
    def __init__(self, cur):
        self._cur = cur

    def __enter__(self):
        return self._cur

    def __exit__(self, *a):
        return False


class StripAndExtractTests(unittest.TestCase):
    def test_strip_prefix_variants(self):
        self.assertEqual(flow._strip_prefix("แก้ร้านค้าเป็น 7-11"), "7-11")
        self.assertEqual(flow._strip_prefix("แก้ร้านค้าเป็น:7-11"), "7-11")  # 全角冒号已 normalize
        self.assertEqual(flow._strip_prefix("卖家改成 7-11"), "7-11")
        self.assertEqual(flow._strip_prefix("7-11"), "7-11")  # 裸值原样

    def test_extract_value(self):
        self.assertEqual(flow._extract_value("90", "amount"), Decimal("90"))
        self.assertEqual(flow._extract_value("แก้จำนวนเงินเป็น 90", "amount"), Decimal("90"))
        self.assertEqual(flow._extract_value("ไม่ใช่ตัวเลข", "amount"), None)
        self.assertEqual(flow._extract_value("711", "seller"), "711")

    def test_extract_payment_normalizes(self):
        # 付款方式按归一表子串匹配:「改成现金」→ cash、พร้อมเพย์ → promptpay;认不出 → None。
        self.assertEqual(flow._extract_value("改成现金", "payment"), "cash")
        self.assertEqual(flow._extract_value("พร้อมเพย์", "payment"), "promptpay")
        self.assertEqual(flow._extract_value("不知道", "payment"), None)


class _FlowBase(unittest.TestCase):
    @contextlib.contextmanager
    def _patches(self, *, pend, detail=None, sent=None, saved=None):
        from services.expense import conversation
        from services.purchase import docs as docs_svc

        with (
            mock.patch.object(flow.db, "get_cursor_rls", return_value=_Ctx(object())),
            mock.patch.object(conversation, "peek_pending", return_value=pend),
            mock.patch.object(
                conversation, "save_pending", side_effect=lambda *a, **k: saved.update(k)
            ),
            mock.patch.object(conversation, "clear_pending"),
            mock.patch.object(docs_svc, "get_doc", return_value=detail),
            mock.patch.object(
                flow.line_reply,
                "reply_text_context",
                side_effect=lambda tok, body, **k: sent.append(body),
            ),
        ):
            yield


class ClarifyAnswerTests(_FlowBase):
    def test_field_answer_advances_to_value(self):
        # 验收 #7:已问「改哪个字段」→ 用户答「วันที่」→ 存 correctval + 问新日期(不再退「请回复记录」)。
        sent, saved = [], {}
        pend = {"missing": "correctclar:1:D1"}
        with self._patches(pend=pend, detail={"doc": {}, "lines": [{}]}, sent=sent, saved=saved):
            res = flow.try_correction_state({}, "tok", "U1", "วันที่", "t", 1, "th")
        self.assertTrue(res)
        self.assertTrue(saved["missing"].startswith("correctval:1:D1:date"))
        self.assertTrue(sent)

    def test_unrecognized_field_reasks(self):
        sent, saved = [], {}
        with self._patches(pend={"missing": "correctclar:1:D1"}, sent=sent, saved=saved):
            res = flow.try_correction_state({}, "tok", "U1", "อะไรนะ", "t", 1, "th")
        self.assertTrue(res)
        self.assertEqual(saved, {})  # 没听出字段 → 不进 correctval,重问


class ValueAnswerTests(unittest.TestCase):
    """收新值 → 委托 line_correct._apply_or_confirm(风险三档/确认/执行在 line_correct 单测)。"""

    def _run(self, pend_missing, text):
        from services.expense import conversation

        cap, sent, saved = {}, [], {}
        with (
            mock.patch.object(flow.db, "get_cursor_rls", return_value=_Ctx(object())),
            mock.patch.object(conversation, "peek_pending", return_value={"missing": pend_missing}),
            mock.patch.object(
                conversation, "save_pending", side_effect=lambda *a, **k: saved.update(k)
            ),
            mock.patch.object(
                line_correct,
                "_apply_or_confirm",
                side_effect=lambda *a, **k: cap.update(doc_id=a[5], changes=a[6]) or True,
            ),
            mock.patch.object(
                flow.line_reply,
                "reply_text_context",
                side_effect=lambda tok, b, **k: sent.append(b),
            ),
        ):
            flow.try_correction_state({}, "tok", "U1", text, "t", 1, "th")
        return cap, sent, saved

    def test_seller_value_with_fullwidth_colon(self):
        # 验收 #5:已问新卖家 → 「แก้ร้านค้าเป็น:7-11」(全角冒号已归一)→ 委托改 vendor_name=7-11。
        cap, _, _ = self._run("correctval:1:D1:seller", "แก้ร้านค้าเป็น:7-11")
        self.assertEqual(cap["changes"], {"vendor_name": "7-11"})

    def test_bare_value_captured(self):
        cap, _, _ = self._run("correctval:1:D1:seller", "7-11")
        self.assertEqual(cap["changes"], {"vendor_name": "7-11"})

    def test_amount_value_delegates(self):
        cap, _, _ = self._run("correctval:1:D1:amount", "90")
        self.assertEqual(cap["changes"], {"amount": Decimal("90")})

    def test_date_year_first_parsed(self):
        # 验收 #1:2026/6/18 / 2026-06-18 → 2026-06-18。
        cap, _, _ = self._run("correctval:1:D1:date", "2026/6/18")
        self.assertEqual(cap["changes"], {"doc_date": "2026-06-18"})

    def test_payment_value_delegates(self):
        # 付款方式可直接改:已问新值 → 「改成现金」→ 委托 payment_method=cash(不再甩详情页)。
        cap, _, _ = self._run("correctval:1:D1:payment", "改成现金")
        self.assertEqual(cap["changes"], {"payment_method": "cash"})

    def test_field_switch_to_seller(self):
        # 验收 #3:等日期时用户改说卖家 → 切到卖家,不再问日期。
        cap, _, _ = self._run("correctval:1:D1:date", "แก้ร้านค้าเป็น 7-11")
        self.assertEqual(cap["changes"], {"vendor_name": "7-11"})

    def test_no_value_reasks_no_delegate(self):
        # 没给真值(否定/指代填充)→ 不委托执行,存待值态再问。
        cap, _, saved = self._run("correctval:1:D1:seller", "ไม่ใช่คนนี้")
        self.assertEqual(cap, {})
        self.assertTrue(saved["missing"].startswith("correctval:1:D1:seller"))


class DispatchTests(_FlowBase):
    def test_no_pending_returns_false(self):
        with self._patches(pend=None, sent=[], saved={}):
            self.assertFalse(flow.try_correction_state({}, "tok", "U1", "hi", "t", 1, "th"))

    def test_confirm_pending_delegates_to_try_confirm(self):
        with (
            mock.patch.object(flow.db, "get_cursor_rls", return_value=_Ctx(object())),
            mock.patch.object(
                line_correct.conversation,
                "peek_pending",
                return_value={"missing": "correct:1:D1:amount"},
            ),
            mock.patch.object(line_correct, "try_confirm", return_value=True) as tc,
        ):
            res = flow.try_correction_state({}, "tok", "U1", "ใช่", "t", 1, "th")
        self.assertTrue(res)
        tc.assert_called_once()


class MaybeClarifyTests(unittest.TestCase):
    """引用澄清入口(P1E-2 收口):识别错了/字段=值 → 接管(澄清/直接改),绝不退化成 OCR 失败重拍。"""

    def _run(self, text, *, quoted="MID1", tgt=None, lines=None):
        from services.expense import conversation
        from services.line_binding import line_message_refs
        from services.purchase import docs as docs_svc

        tgt = tgt if tgt is not None else {"doc_id": "D1", "ws": 1, "error": None}
        detail = {
            "doc": {"status": "draft", "grand_total": "70.00"},
            "supplier": {"name": "711"},
            "lines": lines if lines is not None else [{}],
        }
        ctx = {"line_user_id": "U1", "tenant_id": "t", "quote_token": "q"}
        sent, applied = {}, []
        with (
            mock.patch.object(flow.db, "get_cursor_rls", return_value=_Ctx(object())),
            mock.patch.object(line_message_refs, "resolve_target", return_value=tgt),
            mock.patch.object(docs_svc, "get_doc", return_value=detail),
            mock.patch.object(conversation, "save_pending"),
            mock.patch.object(conversation, "clear_pending"),
            mock.patch.object(
                line_correct, "_apply_or_confirm", side_effect=lambda *a, **k: applied.append(a[6])
            ),
            mock.patch.object(
                flow.line_reply,
                "reply_text_context",
                side_effect=lambda tok, body, **k: sent.update(body=body) or True,
            ),
        ):
            res = flow.maybe_clarify_feedback({}, "tok", text, "th", 1, quoted, ctx)
        return res, sent.get("body", ""), applied

    def test_vague_quoted_clarifies_fields_in_input_lang(self):
        res, body, applied = self._run("这个你识别错了")
        self.assertTrue(res)
        self.assertIn("你想改金额", body)
        self.assertEqual(applied, [])

    def test_thai_vague_clarifies_in_thai(self):
        res, body, _ = self._run("อ่านผิด")
        self.assertTrue(res)
        self.assertIn("ต้องการแก้ส่วนไหน", body)

    def test_field_seller_asks_for_value(self):
        res, body, applied = self._run("卖家不对")
        self.assertTrue(res)
        self.assertIn("卖家", body)
        self.assertIn("改成", body)
        self.assertEqual(applied, [])

    def test_items_guides_detail_page(self):
        res, body, _ = self._run("明细错了")
        self.assertTrue(res)
        self.assertIn("详情页", body)

    def test_payment_asks_for_value(self):
        res, body, applied = self._run("付款方式不对")
        self.assertTrue(res)
        self.assertIn("付款方式", body)
        self.assertEqual(applied, [])

    def test_date_value_applies_directly(self):
        # 验收 #3:「วันที่เป็น 2026/6/18」一句给了字段+值 → 直接走风险三档(不再多问)。
        _, _, applied = self._run("วันที่เป็น 2026/6/18")
        self.assertEqual(applied, [{"doc_date": "2026-06-18"}])

    def test_seller_value_applies_directly(self):
        _, _, applied = self._run("ร้านค้าเป็น 7-11")
        self.assertEqual(applied, [{"vendor_name": "7-11"}])

    def test_concrete_edit_with_field_applies(self):
        # 「金额改成 70」点了字段 → 本层直接抽值执行,不再依赖大脑。
        _, _, applied = self._run("金额改成 70")
        self.assertEqual(applied, [{"amount": Decimal("70")}])

    def test_edit_without_field_defers_to_brain(self):
        # 「上一笔改成 200」没点字段 → 交大脑/edit 流定位目标(本层不接管)。
        res, _, applied = self._run("上一笔改成 200")
        self.assertFalse(res)
        self.assertEqual(applied, [])

    def test_unresolved_quote_guides_reply(self):
        res, body, _ = self._run(
            "识别错了", tgt={"doc_id": None, "ws": 1, "error": "ref_not_found"}
        )
        self.assertTrue(res)
        self.assertTrue(body)

    def test_no_quote_with_amount_passes_through(self):
        res, _, _ = self._run("买错了 50", quoted=None, tgt={"error": "ambiguous"})
        self.assertFalse(res)


class ControlIntentTests(_FlowBase):
    """会话态控制意图(P1E-2 收口):取消/删除/字段切换不串线、不掉回泛化指引。"""

    def test_cancel_intent_clears_at_confirm(self):
        # 验收 #1:确认待定时说「取消」→ 清 pending、回取消(不执行旧动作)。
        sent, saved = [], {}
        with self._patches(pend={"missing": "correct:1:D1:amount"}, sent=sent, saved=saved):
            res = flow.try_correction_state({}, "tok", "U1", "取消", "t", 1, "zh")
        self.assertTrue(res)
        self.assertTrue(sent)

    def test_field_switch_at_confirm_stage(self):
        # 验收 #2:确认待定(改金额)时改说「ร้านค้าเป็น 7-11」→ 切到卖家,不当否定取消。
        cap, sent = {}, []
        with (
            mock.patch.object(flow.db, "get_cursor_rls", return_value=_Ctx(object())),
            mock.patch.object(
                flow.conversation,
                "peek_pending",
                return_value={"missing": "correct:1:D1:amount"},
            ),
            mock.patch.object(flow.conversation, "save_pending"),
            mock.patch.object(
                line_correct,
                "_apply_or_confirm",
                side_effect=lambda *a, **k: cap.update(changes=a[6]) or True,
            ),
            mock.patch.object(
                flow.line_reply, "reply_text_context", side_effect=lambda *a, **k: sent.append(1)
            ),
        ):
            res = flow.try_correction_state({}, "tok", "U1", "ร้านค้าเป็น 7-11", "t", 1, "th")
        self.assertTrue(res)
        self.assertEqual(cap["changes"], {"vendor_name": "7-11"})

    def test_delete_intent_voids_draft(self):
        # 验收 #7:会话内说「删除」→ 作废目标草稿(delete_doc)。
        from services.purchase import docs as docs_svc

        deleted, sent = [], []
        with (
            mock.patch.object(flow.db, "get_cursor_rls", return_value=_Ctx(object())),
            mock.patch.object(
                flow.conversation,
                "peek_pending",
                return_value={"missing": "correctval:1:D1:seller"},
            ),
            mock.patch.object(flow.conversation, "clear_pending"),
            mock.patch.object(docs_svc, "get_doc", return_value={"doc": {"status": "draft"}}),
            mock.patch.object(
                docs_svc, "delete_doc", side_effect=lambda *a, **k: deleted.append(1)
            ),
            mock.patch.object(
                flow.line_reply, "reply_text_context", side_effect=lambda *a, **k: sent.append(1)
            ),
        ):
            res = flow.try_correction_state({}, "tok", "U1", "删除", "t", 1, "zh")
        self.assertTrue(res)
        self.assertEqual(deleted, [1])


if __name__ == "__main__":
    unittest.main()
