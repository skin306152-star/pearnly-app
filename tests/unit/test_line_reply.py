# -*- coding: utf-8 -*-
"""LINE 统一回复出口(P1C):quoteToken 注入 / 无 token fallback / 截断 / bot 记忆 / push。"""

import unittest
from unittest import mock

from services.line_binding import line_reply


class _Spy:
    def __init__(self):
        self.reply = []
        self.push = []
        self.notes = []
        self.loading = []

    def install(self):
        from services.line_binding import line_client

        return (
            mock.patch.object(
                line_client,
                "reply_messages",
                side_effect=lambda rt, msgs: self.reply.append((rt, msgs)) or True,
            ),
            mock.patch.object(
                line_client,
                "push_messages",
                side_effect=lambda uid, msgs: self.push.append((uid, msgs)) or True,
            ),
            mock.patch.object(
                line_client,
                "start_loading",
                side_effect=lambda uid, *a, **k: self.loading.append(uid) or True,
            ),
        )


def _run(fn):
    spy = _Spy()
    patches = spy.install()
    note = mock.patch(
        "services.line_binding.line_chat_memory.note",
        side_effect=lambda **kw: spy.notes.append(kw),
    )
    with patches[0], patches[1], patches[2], note:
        fn()
    return spy


class ReplyContextTests(unittest.TestCase):
    def test_quote_injected_on_first_text(self):
        spy = _run(
            lambda: line_reply.reply_text_context(
                "rt", "hi", quote_token="QT", line_user_id="U1", tenant_id="t"
            )
        )
        rt, msgs = spy.reply[0]
        self.assertEqual(rt, "rt")
        self.assertEqual(msgs[0]["quoteToken"], "QT")

    def test_no_quote_token_still_replies(self):
        # quoteToken 缺失 → 正常回复,不抛错,消息不带 quoteToken。
        spy = _run(lambda: line_reply.reply_text_context("rt", "hi"))
        _, msgs = spy.reply[0]
        self.assertNotIn("quoteToken", msgs[0])

    def test_text_truncated(self):
        spy = _run(lambda: line_reply.reply_text_context("rt", "x" * 9000))
        _, msgs = spy.reply[0]
        self.assertEqual(len(msgs[0]["text"]), 5000)

    def test_records_bot_memory(self):
        spy = _run(
            lambda: line_reply.reply_text_context("rt", "done", line_user_id="U1", tenant_id="t")
        )
        self.assertEqual(spy.notes[0]["role"], "bot")
        self.assertEqual(spy.notes[0]["content"], "done")

    def test_record_skipped_without_ids(self):
        spy = _run(lambda: line_reply.reply_text_context("rt", "hi"))
        self.assertEqual(spy.notes, [])

    def test_quote_only_first_text_in_list(self):
        msgs_in = [
            {"type": "text", "text": "a"},
            {"type": "text", "text": "b"},
        ]
        spy = _run(lambda: line_reply.reply_messages_context("rt", msgs_in, quote_token="QT"))
        _, msgs = spy.reply[0]
        self.assertEqual(msgs[0]["quoteToken"], "QT")
        self.assertNotIn("quoteToken", msgs[1])

    def test_push_path_quotes_and_records(self):
        spy = _run(
            lambda: line_reply.push_text_context("U1", "card", quote_token="IMG", tenant_id="t")
        )
        uid, msgs = spy.push[0]
        self.assertEqual(uid, "U1")
        self.assertEqual(msgs[0]["quoteToken"], "IMG")
        self.assertEqual(spy.notes[0]["content"], "card")

    def test_begin_loading_best_effort(self):
        spy = _run(lambda: line_reply.begin_loading("U1"))
        self.assertEqual(spy.loading, ["U1"])

    def test_begin_loading_no_user_noop(self):
        spy = _run(lambda: line_reply.begin_loading(None))
        self.assertEqual(spy.loading, [])


if __name__ == "__main__":
    unittest.main()
