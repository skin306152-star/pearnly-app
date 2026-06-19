# -*- coding: utf-8 -*-
"""批量撤销:范围识别 + 逐笔执行(草稿删/已入账 void/已结期跳过) + 确认卡 + 路由优先级。"""

import unittest
from unittest import mock

from services.expense import line_bulk_undo as b


class _CM:
    def __enter__(self):
        return object()

    def __exit__(self, *a):
        return False


class DetectTests(unittest.TestCase):
    def test_count_scope(self):
        for t in ("取消刚发的三条", "撤最近3笔", "cancel last 3", "ยกเลิก 3 รายการล่าสุด"):
            self.assertEqual(b.detect_bulk_undo(t), {"scope": "count", "n": 3}, t)

    def test_all_scope(self):
        for t in ("全部取消", "今天全部", "ยกเลิกทั้งหมด", "清空今天"):
            self.assertEqual(b.detect_bulk_undo(t), {"scope": "all"}, t)

    def test_not_bulk(self):
        for t in ("取消", "算了", "撤上一笔", "取消7-11买的咖啡", "ยกเลิก", ""):
            self.assertIsNone(b.detect_bulk_undo(t), t)


def _doc(status, total):
    return {"doc": {"status": status, "grand_total": total}}


class ExecuteTests(unittest.TestCase):
    def _run(self, docs_by_id, void_side=None):
        from services.purchase import docs as docs_svc
        from services.purchase import posting

        with (
            mock.patch("services.expense.line_bulk_undo.db.get_cursor_rls", return_value=_CM()),
            mock.patch.object(
                docs_svc, "get_doc", side_effect=lambda cur, **k: docs_by_id.get(k["doc_id"])
            ),
            mock.patch.object(docs_svc, "delete_doc") as deleted,
            mock.patch.object(
                posting, "void_doc", side_effect=void_side or (lambda cur, **k: {})
            ) as voided,
        ):
            undone, skipped = b._execute({"id": "u"}, "T1", 1, list(docs_by_id.keys()))
        return undone, skipped, deleted, voided

    def test_all_posted_voided(self):
        docs = {"a": _doc("posted", "10"), "c": _doc("posted", "30"), "d": _doc("posted", "5")}
        undone, skipped, deleted, voided = self._run(docs)
        self.assertEqual(len(undone), 3)
        self.assertEqual(skipped, 0)
        self.assertEqual(voided.call_count, 3)
        deleted.assert_not_called()

    def test_draft_and_posted_mix(self):
        docs = {"a": _doc("draft", "10"), "b": _doc("posted", "20")}
        undone, skipped, deleted, voided = self._run(docs)
        self.assertEqual(len(undone), 2)
        deleted.assert_called_once()
        voided.assert_called_once()

    def test_closed_period_skipped_honestly(self):
        from core.pos_api import PosError

        docs = {"a": _doc("posted", "10"), "b": _doc("posted", "20")}

        def void_side(cur, **k):
            if k["doc_id"] == "b":
                raise PosError("acct.period_closed", 409)
            return {}

        undone, skipped, _, _ = self._run(docs, void_side=void_side)
        self.assertEqual(len(undone), 1)  # a 撤掉
        self.assertEqual(skipped, 1)  # b 已结期跳过(不破账)


class RouteTests(unittest.TestCase):
    def test_no_scope_returns_false(self):
        self.assertFalse(b.route({}, "rt", "U1", "取消", "th", "T1", 1, {}))

    def test_recent_builds_confirm_card(self):
        from services.line_binding import line_action_nonce as nonce
        from services.line_binding import line_reply
        from services.purchase import line_docs

        sent = []
        with (
            mock.patch("services.expense.line_bulk_undo.db.get_cursor_rls", return_value=_CM()),
            mock.patch.object(
                line_docs,
                "find_recent_line_docs",
                return_value=[
                    {
                        "id": "a",
                        "grand_total": "10",
                        "doc_date": "2026-06-19",
                        "supplier_name": "7-11",
                    }
                ],
            ),
            mock.patch.object(nonce, "mint", return_value="tok"),
            mock.patch.object(
                line_reply,
                "reply_messages_context",
                side_effect=lambda rt, msgs, **k: sent.append(msgs),
            ),
        ):
            out = b.route({}, "rt", "U1", "撤最近3笔", "th", "T1", 1, {})
        self.assertTrue(out)
        self.assertEqual(sent[0][0]["type"], "flex")

    def test_empty_says_nothing(self):
        from services.line_binding import line_reply
        from services.purchase import line_docs

        said = []
        with (
            mock.patch("services.expense.line_bulk_undo.db.get_cursor_rls", return_value=_CM()),
            mock.patch.object(line_docs, "find_today_line_docs", return_value=[]),
            mock.patch.object(
                line_reply,
                "reply_text_context",
                side_effect=lambda rt, body, **k: said.append(body),
            ),
        ):
            out = b.route({}, "rt", "U1", "全部取消", "th", "T1", 1, {})
        self.assertTrue(out)
        self.assertIn(b._t("th")["nothing"], said)


class PostbackTests(unittest.TestCase):
    def test_cancel_says_nothing_undone(self):
        from services.line_binding import line_action_nonce as nonce
        from services.line_binding import line_postback, line_reply

        said = []
        with (
            mock.patch("services.expense.line_bulk_undo.db.get_cursor_rls", return_value=_CM()),
            mock.patch.object(nonce, "consume", return_value={"status": "ok"}),
            mock.patch.object(
                line_reply,
                "reply_text_context",
                side_effect=lambda rt, body, **k: said.append(body),
            ),
        ):
            b.handle_postback(
                {"tenant_id": "T1", "line_user_id": "U1"},
                "rt",
                line_postback.ACTION_BULK_CANCEL,
                "tok",
                "zh",
            )
        self.assertIn(b._t("zh")["cancelled"], said)

    def test_confirm_executes_and_summarizes(self):
        from services.line_binding import line_action_nonce as nonce
        from services.line_binding import line_postback, line_reply

        sent = []
        with (
            mock.patch("services.expense.line_bulk_undo.db.get_cursor_rls", return_value=_CM()),
            mock.patch.object(
                nonce,
                "consume",
                return_value={
                    "status": "ok",
                    "action_ref": "bulkundo:a,b",
                    "workspace_client_id": 1,
                },
            ),
            mock.patch.object(b, "_execute", return_value=([{"grand_total": "10"}], 0)) as ex,
            mock.patch.object(
                line_reply,
                "reply_messages_context",
                side_effect=lambda rt, msgs, **k: sent.append(msgs),
            ),
        ):
            b.handle_postback(
                {"tenant_id": "T1", "id": "u", "line_user_id": "U1"},
                "rt",
                line_postback.ACTION_BULK_UNDO,
                "tok",
                "zh",
            )
        ex.assert_called_once()
        self.assertEqual(ex.call_args[0][3], ["a", "b"])  # 解析出的 id 列表
        self.assertEqual(sent[0][0]["type"], "flex")

    def test_used_token_no_double_undo(self):
        from services.line_binding import line_action_nonce as nonce
        from services.line_binding import line_postback, line_reply

        with (
            mock.patch("services.expense.line_bulk_undo.db.get_cursor_rls", return_value=_CM()),
            mock.patch.object(nonce, "consume", return_value={"status": "used"}),
            mock.patch.object(b, "_execute") as ex,
            mock.patch.object(line_reply, "reply_text_context"),
        ):
            b.handle_postback(
                {"tenant_id": "T1", "line_user_id": "U1"},
                "rt",
                line_postback.ACTION_BULK_UNDO,
                "tok",
                "zh",
            )
        ex.assert_not_called()


class RouteOrderingTests(unittest.TestCase):
    """bulk 命中先于 correction;bulk 不命中时裸「取消」仍走改错取消。"""

    def test_bulk_wins_over_correction(self):
        from services.expense import line_correct_flow as flow

        with (
            mock.patch.object(flow.line_bulk_undo, "route", return_value=True),
            mock.patch.object(flow, "try_correction_state") as tcs,
        ):
            out = flow.route({}, "rt", "U1", "取消刚发的三条", "th", "T1", 1, None, {})
        self.assertTrue(out)
        tcs.assert_not_called()

    def test_bare_cancel_falls_to_correction(self):
        from services.expense import line_correct_flow as flow

        with (
            mock.patch.object(flow.line_bulk_undo, "route", return_value=False),
            mock.patch.object(flow, "try_correction_state", return_value=True) as tcs,
        ):
            out = flow.route({}, "rt", "U1", "取消", "th", "T1", 1, None, {})
        self.assertTrue(out)
        tcs.assert_called_once()


if __name__ == "__main__":
    unittest.main()
