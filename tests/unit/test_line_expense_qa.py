# -*- coding: utf-8 -*-
"""LINE「取消/撤销」文字回复落地:草稿→丢弃、已入账→冲销,绝不死路(docs/smart-intake)。"""

import unittest
from unittest import mock

from services.line_binding import line_expense_qa as qa


class _CM:
    def __enter__(self):
        return object()

    def __exit__(self, *a):
        return False


def _run(status):
    sent = []
    from core import db
    from services.line_binding import line_card_actions, line_client, line_message_refs
    from services.purchase import docs, posting

    with (
        mock.patch.object(db, "get_cursor_rls", return_value=_CM()),
        mock.patch.object(
            line_message_refs,
            "resolve_target",
            return_value={"doc_id": "D1", "ws": 1, "error": None},
        ),
        mock.patch.object(
            docs, "get_doc", return_value={"doc": {"status": status, "grand_total": "100"}}
        ),
        mock.patch.object(docs, "delete_doc") as delete_doc,
        mock.patch.object(
            posting, "void_doc", return_value={"doc": {"grand_total": "100"}}
        ) as void,
        mock.patch.object(
            line_card_actions, "send_terminal", side_effect=lambda rt, **k: sent.append(k)
        ),
        mock.patch.object(line_client, "t_line", side_effect=lambda lang, key, **kw: key),
    ):
        qa.reply_undo(
            {"id": "u"},
            "rt",
            "th",
            "t",
            1,
            line_user_id="U1",
            quoted_message_id="m1",
            text="ยกเลิก",
        )
    return sent, delete_doc, void


class ReplyUndoTests(unittest.TestCase):
    def test_cancel_on_draft_discards(self):
        # 对草稿回「取消/删除」→ 丢弃(delete_doc)+ 终态卡(discarded),不调 void,不落死路。
        sent, delete_doc, void = _run("draft")
        delete_doc.assert_called_once()
        void.assert_not_called()
        self.assertEqual(sent[0]["state"], "discarded")
        self.assertEqual(sent[0]["amount"], "100")

    def test_cancel_on_posted_voids(self):
        # 已入账 → void + 终态卡(voided·含金额 + 查看记录)。
        sent, delete_doc, void = _run("posted")
        void.assert_called_once()
        delete_doc.assert_not_called()
        self.assertEqual(sent[0]["state"], "voided")
        self.assertEqual(sent[0]["amount"], "100")


if __name__ == "__main__":
    unittest.main()
