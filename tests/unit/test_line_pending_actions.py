# -*- coding: utf-8 -*-
"""泛用确认检查点 store(services/line_binding/line_pending_actions)· 状态机 §3 契约。

与 line_pending_intents 同范式:upsert 覆盖、take=DELETE RETURNING 单发单用、
过期不返、表缺失自愈、take 故障吞掉返 None(检查点层不许挡正常消息)。
"""

import unittest
from unittest.mock import MagicMock, patch

from services.line_binding import line_pending_actions as s


def _cm(cur):
    cm = MagicMock()
    cm.__enter__ = MagicMock(return_value=cur)
    cm.__exit__ = MagicMock(return_value=False)
    return cm


class TestPendingActions(unittest.TestCase):
    def test_set_upserts_with_ttl(self):
        cur = MagicMock()
        with (
            patch.object(s, "ensure_table"),
            patch("core.db.get_cursor_rls", return_value=_cm(cur)),
        ):
            s.set_action("t-1", "Uabc", {"tool": "dms_push", "endpoint_id": "e1"})
        sql = cur.execute.call_args.args[0]
        self.assertIn("ON CONFLICT (tenant_id, line_user_id) DO UPDATE", sql)
        self.assertEqual(cur.execute.call_args.args[1][-1], s.DEFAULT_TTL_MINUTES)

    def test_take_is_delete_returning(self):
        cur = MagicMock()
        cur.fetchone.return_value = {"action": {"tool": "dms_push"}, "alive": True}
        with patch("core.db.get_cursor_rls", return_value=_cm(cur)):
            out = s.take_action("t-1", "Uabc")
        self.assertEqual(out, {"tool": "dms_push"})
        sql = cur.execute.call_args.args[0]
        self.assertIn("DELETE FROM line_pending_actions", sql)
        self.assertIn("RETURNING", sql)

    def test_take_expired_returns_none(self):
        cur = MagicMock()
        cur.fetchone.return_value = {"action": {"tool": "dms_push"}, "alive": False}
        with patch("core.db.get_cursor_rls", return_value=_cm(cur)):
            self.assertIsNone(s.take_action("t-1", "Uabc"))

    def test_missing_table_self_heals(self):
        cur = MagicMock()
        cur.execute.side_effect = [
            Exception('relation "line_pending_actions" does not exist'),
            None,
        ]
        with (
            patch("core.db.get_cursor_rls", return_value=_cm(cur)),
            patch.object(s, "ensure_table") as ensure,
        ):
            s.set_action("t-1", "Uabc", {"tool": "dms_push"})
        ensure.assert_called_once()

    def test_take_failure_is_swallowed(self):
        with patch("core.db.get_cursor_rls", side_effect=RuntimeError("db down")):
            self.assertIsNone(s.take_action("t-1", "Uabc"))


if __name__ == "__main__":
    unittest.main()
