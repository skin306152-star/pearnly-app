# -*- coding: utf-8 -*-
"""跨轮锚点 store(services/line_binding/line_anchor_store)契约。

mock 游标验 SQL:upsert 覆盖刷 TTL、过期不返、表缺失自愈重试、
读写故障一律吞掉退现状(锚点层不许挡对话主路)。
"""

import unittest
from unittest.mock import MagicMock, patch

from services.line_binding import line_anchor_store as s


def _cm(cur):
    cm = MagicMock()
    cm.__enter__ = MagicMock(return_value=cur)
    cm.__exit__ = MagicMock(return_value=False)
    return cm


class TestAnchorStore(unittest.TestCase):
    def test_set_upserts_with_ttl(self):
        cur = MagicMock()
        with (
            patch.object(s, "ensure_table"),
            patch("core.db.get_cursor_rls", return_value=_cm(cur)),
        ):
            s.set_anchors("t-1", "Uabc", {"last_history_id": "h9"})
        sql = cur.execute.call_args.args[0]
        self.assertIn("ON CONFLICT (tenant_id, line_user_id) DO UPDATE", sql)
        self.assertEqual(cur.execute.call_args.args[1][-1], s.DEFAULT_TTL_MINUTES)

    def test_get_filters_expired(self):
        cur = MagicMock()
        cur.fetchone.return_value = {"anchors": {"last_history_id": "h9"}}
        with patch("core.db.get_cursor_rls", return_value=_cm(cur)):
            out = s.get_anchors("t-1", "Uabc")
        self.assertEqual(out, {"last_history_id": "h9"})
        self.assertIn("expires_at > now()", cur.execute.call_args.args[0])

    def test_get_none_returns_empty(self):
        cur = MagicMock()
        cur.fetchone.return_value = None
        with patch("core.db.get_cursor_rls", return_value=_cm(cur)):
            self.assertEqual(s.get_anchors("t-1", "Uabc"), {})

    def test_missing_table_self_heals(self):
        cur = MagicMock()
        cur.execute.side_effect = [
            Exception('relation "line_agent_anchors" does not exist'),
            None,
        ]
        with (
            patch("core.db.get_cursor_rls", return_value=_cm(cur)),
            patch.object(s, "ensure_table") as ensure,
        ):
            s.set_anchors("t-1", "Uabc", {"last_history_id": "h9"})
        ensure.assert_called_once()
        self.assertEqual(cur.execute.call_count, 2)

    def test_failures_are_swallowed(self):
        with patch("core.db.get_cursor_rls", side_effect=RuntimeError("db down")):
            self.assertEqual(s.get_anchors("t-1", "Uabc"), {})
            s.set_anchors("t-1", "Uabc", {"last_history_id": "h9"})  # 不抛即过


if __name__ == "__main__":
    unittest.main()
