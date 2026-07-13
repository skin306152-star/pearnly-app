# -*- coding: utf-8 -*-
"""客户 LINE 群绑定 store(services/line_binding/line_client_group)· LN-1 契约。

mock 游标验 SQL 契约:条件 upsert 一群一客户(别家行 RETURNING 无行 → conflict)、
自愈重跑不炸、故障返 None 不炸 webhook、四语文案齐全 th 兜底。
"""

import unittest
from unittest.mock import MagicMock, patch

from services.line_binding import line_client_group as s


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
        apply_rls.assert_called_with(cur, "line_client_groups")
        self.assertEqual(apply_rls.call_count, 2)


class BindGroupTests(unittest.TestCase):
    def test_fresh_bind_returns_ok(self):
        cur = MagicMock()
        cur.fetchone.return_value = {"line_group_id": "G-1"}
        with patch("core.db.get_cursor", return_value=_cm(cur)):
            self.assertEqual(s.bind_group("t-1", 84, "G-1", bound_by="U-1"), "ok")
        sql = cur.execute.call_args.args[0]
        self.assertIn("ON CONFLICT (line_group_id) DO UPDATE", sql)
        self.assertIn("RETURNING line_group_id", sql)

    def test_group_owned_by_other_client_returns_conflict(self):
        """一群一客户:PK 撞行且 (tenant, client) 不同 → 条件 upsert WHERE 不中 → 无行。"""
        cur = MagicMock()
        cur.fetchone.return_value = None
        with patch("core.db.get_cursor", return_value=_cm(cur)):
            self.assertEqual(s.bind_group("t-2", 91, "G-1"), "conflict")

    def test_empty_group_id_rejected_without_db(self):
        with patch("core.db.get_cursor") as g:
            self.assertIsNone(s.bind_group("t-1", 84, ""))
        g.assert_not_called()

    def test_db_failure_returns_none(self):
        with patch("core.db.get_cursor", side_effect=RuntimeError("db down")):
            self.assertIsNone(s.bind_group("t-1", 84, "G-1"))


class GetGroupTests(unittest.TestCase):
    def test_found_returns_row(self):
        cur = MagicMock()
        cur.fetchone.return_value = {
            "line_group_id": "G-1",
            "tenant_id": "t-1",
            "workspace_client_id": 84,
            "bound_by_line_user": "U-1",
            "bound_at": None,
        }
        with patch("core.db.get_cursor", return_value=_cm(cur)):
            out = s.get_group("G-1")
        self.assertEqual(out["workspace_client_id"], 84)

    def test_missing_returns_none(self):
        cur = MagicMock()
        cur.fetchone.return_value = None
        with patch("core.db.get_cursor", return_value=_cm(cur)):
            self.assertIsNone(s.get_group("G-404"))

    def test_empty_group_id_returns_none_without_db(self):
        with patch("core.db.get_cursor") as g:
            self.assertIsNone(s.get_group(""))
            self.assertIsNone(s.get_group(None))
        g.assert_not_called()

    def test_missing_table_self_heals(self):
        cur = MagicMock()
        cur.execute.side_effect = [
            Exception('relation "line_client_groups" does not exist'),
            None,
        ]
        cur.fetchone.return_value = None
        with (
            patch("core.db.get_cursor", return_value=_cm(cur)),
            patch.object(s, "ensure_table") as ensure,
        ):
            s.get_group("G-1")
        ensure.assert_called_once()

    def test_db_failure_returns_none(self):
        with patch("core.db.get_cursor", side_effect=RuntimeError("db down")):
            self.assertIsNone(s.get_group("G-1"))


class CopyTests(unittest.TestCase):
    def test_bound_copy_four_languages_with_client_name(self):
        for lang in ("th", "en", "zh", "ja"):
            self.assertIn("Sister Makeup", s.group_bound_text(lang, "Sister Makeup"))

    def test_conflict_copy_four_languages(self):
        for lang in ("th", "en", "zh", "ja"):
            self.assertTrue(s.group_conflict_text(lang))

    def test_unknown_lang_falls_back_to_thai(self):
        self.assertEqual(s.group_conflict_text("fr"), s.group_conflict_text("th"))
        self.assertEqual(s.group_bound_text(None, "X"), s.group_bound_text("th", "X"))


if __name__ == "__main__":
    unittest.main()
