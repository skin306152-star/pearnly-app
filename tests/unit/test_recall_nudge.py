# -*- coding: utf-8 -*-
"""掉线召回(recall · W4-2)契约。

花钱面铁五条:① 闸关零发送(文案 Zihao 过目后才放);② 每人每自然月最多一条
(台账去重);③ 从没扫过单的用户不算掉线不发;④ 14 天内有单的活跃用户不发;
⑤ idle 判定查询故障按活跃处理(宁少勿扰)。
"""

import unittest
from datetime import date
from unittest.mock import patch

import core.db  # noqa: F401  # 先于 notification 域导入,防 dal_reexports 单头循环
from services.notification import recall

_ROWS = [{"user_id": "u1", "line_user_id": "U1", "tenant_id": "t1", "preferred_lang": "th"}]


def _send(*, flag=True, dup=False, idle=True):
    pushed, logged = [], []
    with (
        patch("services.notification.proactive._bound_users", return_value=list(_ROWS)),
        patch("core.feature_flags.agent_recall_enabled_for", return_value=flag),
        patch("services.notification.store.already_sent", return_value=dup),
        patch.object(recall, "_idle", return_value=idle),
        patch("services.expense.line_lang.card_lang", return_value="th"),
        patch(
            "services.line_binding.line_reply.push_text_context",
            lambda luid, text, **k: pushed.append(text) or True,
        ),
        patch("services.notification.store.log_notification", lambda *a, **k: logged.append(a)),
    ):
        n = recall.send_recall_nudges(date(2026, 7, 20))
    return n, pushed, logged


class TestRecall(unittest.TestCase):
    def test_gate_closed_sends_nothing(self):
        n, pushed, _ = _send(flag=False)
        self.assertEqual((n, pushed), (0, []))

    def test_monthly_dedup(self):
        n, pushed, _ = _send(dup=True)
        self.assertEqual((n, pushed), (0, []))

    def test_active_user_not_nudged(self):
        n, pushed, _ = _send(idle=False)
        self.assertEqual((n, pushed), (0, []))

    def test_idle_user_gets_one_gentle_nudge(self):
        n, pushed, logged = _send()
        self.assertEqual(n, 1)
        self.assertIn(pushed[0], recall._COPY.values())
        self.assertEqual(logged[0][3], recall.TEMPLATE_CODE)
        self.assertEqual(logged[0][5], "2026-07")  # event_ref = 自然月,月度去重锚

    def test_idle_check_failure_treated_active(self):
        with patch("core.db.get_cursor_rls", side_effect=RuntimeError("db down")):
            self.assertFalse(recall._idle("u1", "t1"))


if __name__ == "__main__":
    unittest.main()
