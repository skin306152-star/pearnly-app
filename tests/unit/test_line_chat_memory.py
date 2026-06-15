# -*- coding: utf-8 -*-
"""LINE 短期对话记忆(PO-15):note/recent 行为 + 大脑 history 织进 prompt + best-effort 不抛。"""

import unittest
from unittest import mock

from services.expense import line_agent
from services.line_binding import line_chat_memory


class _CM:
    def __init__(self, cur):
        self._cur = cur

    def __enter__(self):
        return self._cur

    def __exit__(self, *a):
        return False


class NoteRecentTests(unittest.TestCase):
    def test_note_inserts_and_prunes(self):
        cur = mock.MagicMock()
        from core import db

        with mock.patch.object(db, "get_cursor_rls", return_value=_CM(cur)):
            line_chat_memory.note(line_user_id="U1", tenant_id="t", role="user", content="咖啡 65")
        sqls = " ".join(c.args[0] for c in cur.execute.call_args_list)
        self.assertIn("INSERT INTO line_chat_history", sqls)
        self.assertIn("DELETE FROM line_chat_history", sqls)  # 写后清 24h 前

    def test_note_skips_blank_and_bad_role(self):
        from core import db

        with mock.patch.object(db, "get_cursor_rls") as gc:
            line_chat_memory.note(line_user_id="U1", tenant_id="t", role="user", content="  ")
            line_chat_memory.note(line_user_id="U1", tenant_id="t", role="sys", content="x")
            line_chat_memory.note(line_user_id="", tenant_id="t", role="user", content="x")
        gc.assert_not_called()

    def test_note_best_effort_swallows(self):
        from core import db

        with mock.patch.object(db, "get_cursor_rls", side_effect=RuntimeError("boom")):
            line_chat_memory.note(
                line_user_id="U1", tenant_id="t", role="user", content="x"
            )  # 不抛

    def test_recent_chronological(self):
        cur = mock.MagicMock()
        # DB 返回时间倒序(最新在前),recent 应转成正序。
        cur.fetchall.return_value = [
            {"role": "bot", "content": "b2"},
            {"role": "user", "content": "u2"},
            {"role": "bot", "content": "b1"},
        ]
        from core import db

        with mock.patch.object(db, "get_cursor_rls", return_value=_CM(cur)):
            out = line_chat_memory.recent(line_user_id="U1", tenant_id="t")
        self.assertEqual([h["content"] for h in out], ["b1", "u2", "b2"])

    def test_recent_failure_returns_empty(self):
        from core import db

        with mock.patch.object(db, "get_cursor_rls", side_effect=RuntimeError("boom")):
            self.assertEqual(line_chat_memory.recent(line_user_id="U1", tenant_id="t"), [])


class HistoryPromptTests(unittest.TestCase):
    def test_history_block_renders_turns(self):
        block = line_agent._history_block(
            [{"role": "user", "content": "咖啡 65"}, {"role": "bot", "content": "✅ 已入账"}]
        )
        self.assertIn("user: 咖啡 65", block)
        self.assertIn("bot: ✅ 已入账", block)

    def test_history_block_empty(self):
        self.assertEqual(line_agent._history_block(None), "")
        self.assertEqual(line_agent._history_block([{"role": "user", "content": "  "}]), "")

    def test_understand_passes_history_into_prompt(self):
        captured = {}

        def _fake(text, *, api_key, model_name, max_retries, timeout, system_prompt_override):
            captured["prompt"] = system_prompt_override
            return ({"intent": "chat", "speech_act": "question", "reply": "ok"}, {})

        with mock.patch("services.ocr.layer2_gemini._call_gemini_with_retry", side_effect=_fake):
            with mock.patch("services.ocr.gemini_models.flash_lite", return_value="m"):
                out = line_agent.understand(
                    "为什么没识别出来",
                    api_key="k",
                    history=[{"role": "bot", "content": "票据识别:inbox"}],
                )
        self.assertEqual(out["intent"], "chat")
        self.assertIn("票据识别:inbox", captured["prompt"])  # 历史进了 prompt
        self.assertIn("context only", captured["prompt"])


if __name__ == "__main__":
    unittest.main()
