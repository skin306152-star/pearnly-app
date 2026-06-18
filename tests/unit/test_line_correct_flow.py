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


class ValueAnswerTests(_FlowBase):
    def test_seller_value_with_fullwidth_colon_confirms(self):
        # 验收 #5:已问新卖家 → 用户「แก้ร้านค้าเป็น:7-11」(全角冒号已归一)→ 存 correct: + 出确认。
        sent, saved = [], {}
        pend = {"missing": "correctval:1:D1:seller"}
        detail = {"doc": {"grand_total": "150"}, "supplier": {"name": "711"}, "lines": [{}]}
        with self._patches(pend=pend, detail=detail, sent=sent, saved=saved):
            res = flow.try_correction_state({}, "tok", "U1", "แก้ร้านค้าเป็น:7-11", "t", 1, "th")
        self.assertTrue(res)
        self.assertEqual(saved["missing"], "correct:1:D1:vendor_name")
        self.assertEqual(saved["draft"].vendor_name, "7-11")
        self.assertIn("711", sent[0])  # 确认含旧值
        self.assertIn("7-11", sent[0])  # 与新值

    def test_bare_value_captured(self):
        sent, saved = [], {}
        pend = {"missing": "correctval:1:D1:seller"}
        detail = {"doc": {}, "supplier": {"name": "711"}, "lines": [{}]}
        with self._patches(pend=pend, detail=detail, sent=sent, saved=saved):
            flow.try_correction_state({}, "tok", "U1", "7-11", "t", 1, "th")
        self.assertEqual(saved["draft"].vendor_name, "7-11")

    def test_amount_on_multiline_guides_detail(self):
        # 验收 #3:文本多项卡改行金额 → 引导详情页(多行不猜),不进确认。
        sent, saved = [], {}
        pend = {"missing": "correctval:1:D1:amount"}
        detail = {"doc": {}, "lines": [{}, {}, {}]}
        with self._patches(pend=pend, detail=detail, sent=sent, saved=saved):
            flow.try_correction_state({}, "tok", "U1", "90", "t", 1, "th")
        self.assertEqual(saved, {})  # 不存确认态
        self.assertIn("Pearnly", sent[0])  # 引导详情页


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


if __name__ == "__main__":
    unittest.main()
