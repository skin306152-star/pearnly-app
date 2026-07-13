# -*- coding: utf-8 -*-
"""收料暂存池 store(services/line_binding/line_intake_store)· LN-1 契约。

mock 游标验 SQL 契约:插行幂等(ON CONFLICT line_message_id DO NOTHING · 重投返 False
不双记)、读侧 WHERE 带 tenant_id(应用层 WHERE + RLS 双证)、suggested_period 取最近
未归档工单(status 词 import workorder.engine 不手打)、故障返安全值不炸 webhook。
"""

import unittest
from unittest.mock import MagicMock, patch

from services.line_binding import line_intake_store as s
from services.workorder import engine


def _cm(cur):
    cm = MagicMock()
    cm.__enter__ = MagicMock(return_value=cur)
    cm.__exit__ = MagicMock(return_value=False)
    return cm


class EnsureTableTests(unittest.TestCase):
    def test_idempotent_rerun_does_not_raise(self):
        cur = MagicMock()
        with (
            patch("core.db.get_cursor", return_value=_cm(cur)),
            patch("core.rls.apply_tenant_rls") as apply_rls,
        ):
            s.ensure_table()
            s.ensure_table()
        apply_rls.assert_called_with(cur, "client_intake_staging")
        self.assertEqual(apply_rls.call_count, 2)


class InsertStagingTests(unittest.TestCase):
    def _insert(self, cur):
        with patch("core.db.get_cursor_rls", return_value=_cm(cur)) as g:
            out = s.insert_staging(
                "t-1",
                84,
                line_message_id="mid-1",
                file_path="/x/a.jpg",
                sha256="deadbeef",
                source=s.SOURCE_DM,
                sender_line_user_id="U-1",
                suggested_period="2026-06",
            )
        return out, g

    def test_new_row_returns_true(self):
        cur = MagicMock()
        cur.fetchone.return_value = {"id": "row-1"}
        out, g = self._insert(cur)
        self.assertIs(out, True)
        g.assert_called_once_with("t-1", commit=True)
        sql = cur.execute.call_args.args[0]
        self.assertIn("ON CONFLICT (line_message_id) DO NOTHING", sql)

    def test_duplicate_message_id_returns_false(self):
        """同 message_id 重投 → CONFLICT 吞掉 → RETURNING 无行 → False(幂等不双记)。"""
        cur = MagicMock()
        cur.fetchone.return_value = None
        out, _ = self._insert(cur)
        self.assertIs(out, False)

    def test_db_failure_returns_none(self):
        with patch("core.db.get_cursor_rls", side_effect=RuntimeError("db down")):
            out = s.insert_staging(
                "t-1", 84, line_message_id="m", file_path="p", sha256="h", source="dm"
            )
        self.assertIsNone(out)

    def test_missing_table_self_heals(self):
        cur = MagicMock()
        cur.execute.side_effect = [
            Exception('relation "client_intake_staging" does not exist'),
            None,
        ]
        cur.fetchone.return_value = {"id": "row-1"}
        with (
            patch("core.db.get_cursor_rls", return_value=_cm(cur)),
            patch.object(s, "ensure_table") as ensure,
        ):
            s.insert_staging("t-1", 84, line_message_id="m", file_path="p", sha256="h", source="dm")
        ensure.assert_called_once()


class ReadSideTests(unittest.TestCase):
    def test_list_staging_scopes_by_tenant_and_client(self):
        cur = MagicMock()
        cur.fetchall.return_value = [{"id": "r1"}, {"id": "r2"}]
        with patch("core.db.get_cursor_rls", return_value=_cm(cur)) as g:
            out = s.list_staging("t-1", 84, period="2026-06")
        self.assertEqual(len(out), 2)
        g.assert_called_once_with("t-1")
        sql = cur.execute.call_args.args[0]
        self.assertIn("WHERE tenant_id = %s AND workspace_client_id = %s", sql)

    def test_list_staging_period_none_lists_all(self):
        cur = MagicMock()
        cur.fetchall.return_value = []
        with patch("core.db.get_cursor_rls", return_value=_cm(cur)):
            s.list_staging("t-1", 84)
        params = cur.execute.call_args.args[1]
        self.assertIn(None, params)

    def test_list_staging_failure_returns_empty(self):
        with patch("core.db.get_cursor_rls", side_effect=RuntimeError("db down")):
            self.assertEqual(s.list_staging("t-1", 84), [])

    def test_count_pending_counts_pending_status_only(self):
        cur = MagicMock()
        cur.fetchone.return_value = {"n": 3}
        with patch("core.db.get_cursor_rls", return_value=_cm(cur)):
            self.assertEqual(s.count_pending("t-1", 84), 3)
        sql, params = cur.execute.call_args.args
        self.assertIn("AND status = %s", sql)
        self.assertIn(s.STATUS_PENDING, params)

    def test_count_pending_failure_returns_zero(self):
        with patch("core.db.get_cursor_rls", side_effect=RuntimeError("db down")):
            self.assertEqual(s.count_pending("t-1", 84), 0)


class SuggestedPeriodTests(unittest.TestCase):
    def test_latest_open_period_excludes_archived(self):
        cur = MagicMock()
        cur.fetchone.return_value = {"period": "2026-06"}
        with patch("core.db.get_cursor_rls", return_value=_cm(cur)):
            self.assertEqual(s.latest_open_period("t-1", 84), "2026-06")
        sql, params = cur.execute.call_args.args
        self.assertIn("status <> %s", sql)
        self.assertIn(engine.STATUS_ARCHIVE, params)

    def test_no_open_order_returns_none(self):
        cur = MagicMock()
        cur.fetchone.return_value = None
        with patch("core.db.get_cursor_rls", return_value=_cm(cur)):
            self.assertIsNone(s.latest_open_period("t-1", 84))

    def test_failure_returns_none(self):
        with patch("core.db.get_cursor_rls", side_effect=RuntimeError("db down")):
            self.assertIsNone(s.latest_open_period("t-1", 84))


class ClientDisplayNameTests(unittest.TestCase):
    def test_found_returns_name(self):
        cur = MagicMock()
        cur.fetchone.return_value = {"name": "Sister Makeup"}
        with patch("core.db.get_cursor_rls", return_value=_cm(cur)):
            self.assertEqual(s.client_display_name("t-1", 84), "Sister Makeup")
        sql = cur.execute.call_args.args[0]
        self.assertIn("WHERE id = %s AND tenant_id = %s", sql)

    def test_missing_or_failure_returns_none(self):
        cur = MagicMock()
        cur.fetchone.return_value = None
        with patch("core.db.get_cursor_rls", return_value=_cm(cur)):
            self.assertIsNone(s.client_display_name("t-1", 84))
        with patch("core.db.get_cursor_rls", side_effect=RuntimeError("db down")):
            self.assertIsNone(s.client_display_name("t-1", 84))


if __name__ == "__main__":
    unittest.main()
