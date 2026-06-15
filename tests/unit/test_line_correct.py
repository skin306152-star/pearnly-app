# -*- coding: utf-8 -*-
"""LINE 更正流程单测(PO-13):确认机制 + 冲销+重建数据 + auto_book 过账。

真库行为(连号/隔离/做账)由真账号 E2E 守;这里锁纯逻辑 + 编排顺序(mock svc)。
"""

import unittest
from unittest import mock

from services.expense import line_correct


class _Ctx:
    def __init__(self, cur):
        self._cur = cur

    def __enter__(self):
        return self._cur

    def __exit__(self, *a):
        return False


class AffirmativeParseTests(unittest.TestCase):
    def test_affirmative(self):
        self.assertTrue(line_correct._affirmative("是"))
        self.assertTrue(line_correct._affirmative("ใช่"))
        self.assertTrue(line_correct._affirmative("YES"))
        self.assertFalse(line_correct._affirmative("咖啡 70"))
        self.assertFalse(line_correct._affirmative(""))

    def test_parse(self):
        self.assertEqual(line_correct._parse("correct:D1:550"), ("D1", "550"))


class CorrectedDataTests(unittest.TestCase):
    def test_copies_and_changes_amount(self):
        detail = {
            "doc": {
                "doc_kind": "expense",
                "category_id": "c1",
                "payment_status": "paid",
                "doc_date": "2026-06-16",
            },
            "supplier": {"name": "ACME", "tax_id": "123"},
            "lines": [{"description": "coffee"}],
        }
        d = line_correct._corrected_data(detail, "550", "D1")
        self.assertEqual(d["supplier"]["name"], "ACME")
        self.assertEqual(d["category_id"], "c1")
        self.assertEqual(d["payment_status"], "paid")
        self.assertEqual(d["ocr_raw"]["corrected_from"], "D1")
        self.assertEqual(d["lines"][0]["unit_price"], "550")
        self.assertEqual(d["lines"][0]["description"], "coffee")


class ApplyTests(unittest.TestCase):
    def test_voids_creates_posts_when_autobook(self):
        from services.purchase import docs as docs_svc, posting as posting_svc
        from services.purchase import settings as settings_svc

        detail = {"doc": {"status": "posted", "doc_kind": "expense"}, "supplier": {}, "lines": []}
        calls = []
        with (
            mock.patch.object(docs_svc, "get_doc", return_value=detail),
            mock.patch.object(
                posting_svc, "void_doc", side_effect=lambda *a, **k: calls.append("void")
            ),
            mock.patch.object(settings_svc, "get_settings", return_value={"auto_book": True}),
            mock.patch.object(docs_svc, "create_doc", return_value={"doc": {"id": "new1"}}),
            mock.patch.object(
                posting_svc, "post_doc", side_effect=lambda *a, **k: calls.append("post")
            ),
        ):
            res = line_correct._apply(object(), {"id": "u"}, "t", 1, "D1", "550")
        self.assertEqual(res, {"new_id": "new1", "posted": True})
        self.assertEqual(calls, ["void", "post"])  # 先冲销后过账

    def test_draft_when_autobook_off(self):
        from services.purchase import docs as docs_svc, posting as posting_svc
        from services.purchase import settings as settings_svc

        detail = {"doc": {"status": "posted"}, "supplier": {}, "lines": []}
        with (
            mock.patch.object(docs_svc, "get_doc", return_value=detail),
            mock.patch.object(posting_svc, "void_doc"),
            mock.patch.object(settings_svc, "get_settings", return_value={"auto_book": False}),
            mock.patch.object(docs_svc, "create_doc", return_value={"doc": {"id": "n"}}),
            mock.patch.object(posting_svc, "post_doc") as post,
        ):
            res = line_correct._apply(object(), {"id": "u"}, "t", 1, "D1", "550")
        self.assertEqual(res["posted"], False)
        post.assert_not_called()

    def test_none_when_original_not_posted(self):
        from services.purchase import docs as docs_svc

        with mock.patch.object(docs_svc, "get_doc", return_value={"doc": {"status": "void"}}):
            self.assertIsNone(line_correct._apply(object(), {"id": "u"}, "t", 1, "D1", "550"))


class TryConfirmTests(unittest.TestCase):
    def test_ignores_amount_pending(self):
        # 待补金额 pending 不被更正流程吞(返 False · 交给补金额快路)。
        with (
            mock.patch.object(line_correct.db, "get_cursor_rls", return_value=_Ctx(object())),
            mock.patch.object(
                line_correct.conversation, "peek_pending", return_value={"missing": "amount"}
            ),
        ):
            out = line_correct.try_confirm({"id": "u"}, "tok", "U1", "咖啡 70", "t", 1, "zh")
        self.assertFalse(out)

    def test_executes_on_yes(self):
        applied = {}
        with (
            mock.patch.object(line_correct.db, "get_cursor_rls", return_value=_Ctx(object())),
            mock.patch.object(
                line_correct.conversation,
                "peek_pending",
                return_value={"missing": "correct:D1:550"},
            ),
            mock.patch.object(line_correct.conversation, "clear_pending"),
            mock.patch.object(
                line_correct,
                "_apply",
                side_effect=lambda c, bu, tid, ws, oid, amt: applied.update({"o": oid, "a": amt})
                or {"new_id": "n", "posted": True},
            ),
            mock.patch.object(line_correct.line_client, "reply_text"),
        ):
            out = line_correct.try_confirm({"id": "u"}, "tok", "U1", "是", "t", 1, "zh")
        self.assertTrue(out)
        self.assertEqual(applied, {"o": "D1", "a": "550"})

    def test_cancels_on_no(self):
        with (
            mock.patch.object(line_correct.db, "get_cursor_rls", return_value=_Ctx(object())),
            mock.patch.object(
                line_correct.conversation,
                "peek_pending",
                return_value={"missing": "correct:D1:550"},
            ),
            mock.patch.object(line_correct.conversation, "clear_pending") as clr,
            mock.patch.object(line_correct.line_client, "reply_text"),
            mock.patch.object(line_correct, "_apply") as ap,
        ):
            out = line_correct.try_confirm({"id": "u"}, "tok", "U1", "不用了", "t", 1, "zh")
        self.assertTrue(out)
        clr.assert_called_once()
        ap.assert_not_called()


if __name__ == "__main__":
    unittest.main()
