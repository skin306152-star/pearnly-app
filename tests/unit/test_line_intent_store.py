# -*- coding: utf-8 -*-
"""待决图片意图 store(services/line_binding/line_intent_store)· LI-2 契约。

mock 游标验 SQL 契约:upsert 覆盖、take=DELETE RETURNING 单发单用、过期不返、
表缺失自愈重试、take 故障吞掉返 None(意图层不许挡记账主路)。
"""

import unittest
from unittest.mock import MagicMock, patch

from services.line_binding import line_intent_store as s


def _cm(cur):
    cm = MagicMock()
    cm.__enter__ = MagicMock(return_value=cur)
    cm.__exit__ = MagicMock(return_value=False)
    return cm


class TestIntentStore(unittest.TestCase):
    def test_set_upserts_with_ttl(self):
        cur = MagicMock()
        with (
            patch.object(s, "ensure_table"),
            patch("core.db.get_cursor_rls", return_value=_cm(cur)),
        ):
            s.set_intent("t-1", "Uabc", {"goals": ["push"]}, workspace_client_id=84)
        sql = cur.execute.call_args.args[0]
        self.assertIn("ON CONFLICT (tenant_id, line_user_id) DO UPDATE", sql)
        params = cur.execute.call_args.args[1]
        self.assertEqual(params[-1], s.DEFAULT_TTL_MINUTES)

    def test_take_is_delete_returning(self):
        cur = MagicMock()
        cur.fetchone.return_value = {"intent": {"goals": ["push"]}, "alive": True}
        with patch("core.db.get_cursor_rls", return_value=_cm(cur)):
            out = s.take_intent("t-1", "Uabc")
        self.assertEqual(out, {"goals": ["push"]})
        self.assertIn("DELETE FROM line_pending_intents", cur.execute.call_args.args[0])
        self.assertIn("RETURNING", cur.execute.call_args.args[0])

    def test_take_expired_returns_none(self):
        cur = MagicMock()
        cur.fetchone.return_value = {"intent": {"goals": ["push"]}, "alive": False}
        with patch("core.db.get_cursor_rls", return_value=_cm(cur)):
            self.assertIsNone(s.take_intent("t-1", "Uabc"))

    def test_missing_table_self_heals(self):
        cur = MagicMock()
        cur.execute.side_effect = [
            Exception('relation "line_pending_intents" does not exist'),
            None,
        ]
        with (
            patch("core.db.get_cursor_rls", return_value=_cm(cur)),
            patch.object(s, "ensure_table") as ensure,
        ):
            s.set_intent("t-1", "Uabc", {"goals": ["record"]})
        ensure.assert_called_once()
        self.assertEqual(cur.execute.call_count, 2)

    def test_take_failure_is_swallowed(self):
        with patch("core.db.get_cursor_rls", side_effect=RuntimeError("db down")):
            self.assertIsNone(s.take_intent("t-1", "Uabc"))

    def test_peek_reads_without_delete(self):
        # peek 只看不取:缓存快路让位判断用,绝不消费意图(take 仍是唯一消费点)。
        cur = MagicMock()
        cur.fetchone.return_value = {"intent": {"goals": ["push"]}}
        with patch("core.db.get_cursor_rls", return_value=_cm(cur)):
            self.assertTrue(s.peek_intent("t-1", "Uabc"))
        sql = cur.execute.call_args.args[0]
        self.assertIn("SELECT intent FROM line_pending_intents", sql)  # peek=read_intent 推导
        self.assertNotIn("DELETE", sql)
        self.assertIn("expires_at > now()", sql)

    def test_peek_none_and_failure_return_false(self):
        cur = MagicMock()
        cur.fetchone.return_value = None
        with patch("core.db.get_cursor_rls", return_value=_cm(cur)):
            self.assertFalse(s.peek_intent("t-1", "Uabc"))
        with patch("core.db.get_cursor_rls", side_effect=RuntimeError("db down")):
            self.assertFalse(s.peek_intent("t-1", "Uabc"))


if __name__ == "__main__":
    unittest.main()
