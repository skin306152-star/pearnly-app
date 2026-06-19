# -*- coding: utf-8 -*-
"""调整金额命令不被记成新支出:「ปรับยอดเป็น 150」(无引用/无 active)→ 安全网问回复记录,不入账;
「ค่าปรับ 150」(罚款)仍正常记。走真实 line_correct_flow.route(只 patch 边界 IO)。"""

import unittest
from unittest import mock

from services.line_binding import line_expense as le


class _CM:
    def __enter__(self):
        return object()

    def __exit__(self, *a):
        return False


def _run(text):
    from core import db, workspace_context
    from services.expense import conversation
    from services.line_binding import line_chat_memory, line_client, line_reply
    from services.purchase import intake as intake_svc

    out = {"record": [], "say": []}
    with (
        mock.patch.object(db, "get_cursor_rls", return_value=_CM()),
        mock.patch.object(line_chat_memory, "recent", return_value=[]),
        mock.patch.object(line_chat_memory, "note"),
        mock.patch.object(intake_svc, "line_expense_gate_open", return_value=True),
        mock.patch.object(workspace_context, "default_workspace_id", return_value="WS1"),
        mock.patch.object(conversation, "peek_pending", return_value=None),
        mock.patch.object(conversation, "pop_pending", return_value=None),
        mock.patch.object(line_client, "t_line", side_effect=lambda lang, key, **k: key),
        mock.patch.object(
            line_reply,
            "reply_text_context",
            side_effect=lambda rt, body, **k: out["say"].append(body),
        ),
        mock.patch.object(
            le, "_do_record", side_effect=lambda *a, **k: out["record"].append(a) or True
        ),
    ):
        out["ret"] = le.handle_expense_text({"tenant_id": "T1", "id": "u"}, "rt", "U1", text, "th")
    return out


class AdjustAmountRouteTests(unittest.TestCase):
    def test_adjust_not_recorded_asks_reply(self):
        out = _run("ปรับยอดเป็น 150")
        self.assertTrue(out["ret"])
        self.assertEqual(out["record"], [])  # 不记成新支出
        self.assertIn("line_need_reply_record", out["say"])

    def test_fine_expense_still_records(self):
        out = _run("ค่าปรับ 150")
        self.assertTrue(out["ret"])
        self.assertEqual(len(out["record"]), 1)  # 罚款正常记


if __name__ == "__main__":
    unittest.main()
