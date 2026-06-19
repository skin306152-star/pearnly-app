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
    from services.purchase import correct, docs, posting

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
        mock.patch.object(correct, "discard_doc") as discard_doc,
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
    return sent, discard_doc, void


class ReplyUndoTests(unittest.TestCase):
    def test_cancel_on_draft_discards(self):
        # 对草稿回「取消/删除」→ 软删丢弃(discard_doc·status=discarded)+ 终态卡(discarded),不 void。
        sent, discard_doc, void = _run("draft")
        discard_doc.assert_called_once()
        void.assert_not_called()
        self.assertEqual(sent[0]["state"], "discarded")
        self.assertEqual(sent[0]["amount"], "100")

    def test_cancel_on_posted_voids(self):
        # 已入账 → void + 终态卡(voided·含金额 + 查看记录)。
        sent, discard_doc, void = _run("posted")
        void.assert_called_once()
        discard_doc.assert_not_called()
        self.assertEqual(sent[0]["state"], "voided")
        self.assertEqual(sent[0]["amount"], "100")


def _pool(**kw):
    sent = {}
    from services.line_binding import line_client, line_reply

    with (
        mock.patch.object(line_client, "t_line", side_effect=lambda lang, key, **k: key),
        mock.patch.object(
            line_reply,
            "reply_messages_context",
            side_effect=lambda rt, msgs, **k: sent.update(m=msgs),
        ),
    ):
        qa.reply_pool("rt", kw.pop("kind", "unknown"), "hi", "th", **kw)
    return sent["m"][0]


class ReplyPoolOverrideTests(unittest.TestCase):
    def test_override_body_used_with_quick_reply(self):
        # P3A-2:自然语气正文直接采用,跳过模板;Quick Reply「记一笔/查账」钩子照常带上。
        msg = _pool(override_body="สบายดีไหมคะ มีอะไรให้ช่วยบันทึกบอกได้เลยค่ะ")
        self.assertEqual(msg["text"], "สบายดีไหมคะ มีอะไรให้ช่วยบันทึกบอกได้เลยค่ะ")
        self.assertEqual(len(msg["quickReply"]["items"]), 2)

    def test_out_of_scope_and_unknown_fall_to_pool(self):
        # P3A-2b:override_body=None 时 out_of_scope/unknown 落 replies 轮选池(非旧单模板)。
        from services.expense import replies

        for kind in ("out_of_scope", "unknown"):
            msg = _pool(kind=kind, override_body=None)
            self.assertIn(msg["text"], replies._POOLS[kind]["th"])
            self.assertIn("quickReply", msg)

    def test_guidance_kind_still_template(self):
        # 引导类目仍走模板查表(greeting → line_greeting),零回归。
        msg = _pool(kind="greeting", override_body=None)
        self.assertEqual(msg["text"], "line_greeting")


class MaybeBareUndoTests(unittest.TestCase):
    """裸「取消/删除」(无引用·非批量)→ 撤最近一笔(find_last_posted);批量/引用 → 让位。"""

    def _bare(self, text, *, quoted=None, last=None, bulk_ret=None):
        from core import db
        from services.expense import line_bulk_undo
        from services.line_binding import line_client, line_message_refs

        calls = {}
        with (
            mock.patch.object(db, "get_cursor_rls", return_value=_CM()),
            mock.patch.object(line_bulk_undo, "detect_bulk_undo", return_value=bulk_ret),
            mock.patch.object(line_message_refs, "find_last_posted", return_value=last),
            mock.patch.object(
                qa, "_undo_resolved", side_effect=lambda *a, **k: calls.setdefault("undo", a)
            ),
            mock.patch.object(line_client, "t_line", side_effect=lambda lang, key, **k: key),
            mock.patch.object(
                qa.line_reply,
                "reply_text_context",
                side_effect=lambda *a, **k: calls.setdefault("say", a),
            ),
        ):
            res = qa.maybe_bare_undo(
                {"id": "u"}, "rt", "U1", text, "th", "t", 1, quoted, {"quote_token": "q"}
            )
        return res, calls

    def test_bare_cancel_undoes_last(self):
        res, calls = self._bare("ยกเลิก", last={"id": "D9", "grand_total": "70"})
        self.assertTrue(res)
        self.assertEqual(calls["undo"][5], "D9")  # _undo_resolved(... doc_id=D9)

    def test_bare_delete_undoes_last(self):
        res, calls = self._bare("ลบ", last={"id": "D9", "grand_total": "70"})
        self.assertTrue(res)
        self.assertEqual(calls["undo"][5], "D9")

    def test_bare_cancel_no_record_says_none(self):
        res, calls = self._bare("ยกเลิก", last=None)
        self.assertTrue(res)
        self.assertNotIn("undo", calls)  # ★不撤、不新建
        self.assertEqual(calls["say"][1], "exp_undo_none")

    def test_quoted_cancel_not_bare(self):
        res, calls = self._bare("ยกเลิก", quoted="m1")
        self.assertFalse(res)  # 引用某卡 → 交 try_void_quoted
        self.assertEqual(calls, {})

    def test_bulk_cancel_not_bare(self):
        res, calls = self._bare("取消最近3笔", bulk_ret={"scope": "recent", "n": 3})
        self.assertFalse(res)  # 批量 → 交 line_bulk_undo
        self.assertEqual(calls, {})

    def test_non_cancel_text_not_bare(self):
        res, _ = self._bare("กาแฟ 70")  # 普通记账 → 不接管
        self.assertFalse(res)


if __name__ == "__main__":
    unittest.main()
