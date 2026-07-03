# -*- coding: utf-8 -*-
"""主动触达 v1(services/notification/proactive)守门。

push 是花钱面:窗口外不发/闸关不发/台账去重不重发/去重查询失败宁跳过/单户异常不连坐。
"""

import unittest
from datetime import date
from unittest.mock import MagicMock, patch

from services.notification import proactive


def _users(n=1):
    return [
        {"user_id": f"u{i}", "line_user_id": f"U{i}", "tenant_id": "t1", "preferred_lang": "th"}
        for i in range(n)
    ]


class TestSendDueNudges(unittest.TestCase):
    def setUp(self):
        patch.object(proactive, "_bound_users", return_value=_users()).start()
        patch("core.feature_flags.agent_proactive_enabled_for", return_value=True).start()
        patch.object(proactive, "_already_sent", return_value=False).start()
        patch("services.expense.line_lang.card_lang", return_value="th").start()
        self.push = patch(
            "services.line_binding.line_reply.push_text_context", return_value=True
        ).start()
        self.log = patch("services.notification.store.log_notification").start()
        self.addCleanup(patch.stopall)

    def test_outside_window_sends_nothing(self):
        self.assertEqual(proactive.send_due_nudges(date(2026, 7, 3)), 0)
        self.push.assert_not_called()

    def test_in_window_sends_once_with_period_and_ledger(self):
        self.assertEqual(proactive.send_due_nudges(date(2026, 7, 12)), 1)
        self.assertIn("2026-06", self.push.call_args.args[1])  # 期号=上一个自然月
        self.assertEqual(self.log.call_args.args[3], "tax_due_nudge")
        self.assertEqual(self.log.call_args.args[5], "2026-06")
        self.assertEqual(self.log.call_args.args[7], "sent")

    def test_january_period_rolls_to_previous_year(self):
        proactive.send_due_nudges(date(2026, 1, 10))
        self.assertIn("2025-12", self.push.call_args.args[1])

    def test_gate_off_sends_nothing(self):
        with patch("core.feature_flags.agent_proactive_enabled_for", return_value=False):
            self.assertEqual(proactive.send_due_nudges(date(2026, 7, 12)), 0)
        self.push.assert_not_called()

    def test_dedup_skips_already_sent(self):
        with patch.object(proactive, "_already_sent", return_value=True):
            self.assertEqual(proactive.send_due_nudges(date(2026, 7, 12)), 0)
        self.push.assert_not_called()

    def test_push_failure_logged_as_failed_not_counted(self):
        self.push.return_value = False
        self.assertEqual(proactive.send_due_nudges(date(2026, 7, 12)), 0)
        self.assertEqual(self.log.call_args.args[7], "failed")

    def test_one_user_crash_does_not_block_others(self):
        patch.object(proactive, "_bound_users", return_value=_users(2)).start()
        self.push.side_effect = [RuntimeError("net"), True]
        self.assertEqual(proactive.send_due_nudges(date(2026, 7, 12)), 1)


class TestAlreadySent(unittest.TestCase):
    def test_query_failure_returns_true(self):
        # 花钱面宁少勿重:台账查询失败按已发处理。
        with patch("core.db.get_cursor_rls", side_effect=RuntimeError("db down")):
            self.assertTrue(proactive._already_sent("u1", "t1", "2026-06"))


if __name__ == "__main__":
    unittest.main()
