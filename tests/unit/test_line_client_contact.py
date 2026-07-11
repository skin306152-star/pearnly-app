# -*- coding: utf-8 -*-
"""客户 LINE 联系人 store(services/line_binding/line_client_contact)· D2-S2 契约。

mock 游标验 SQL 契约:ensure_table 幂等自愈重跑不炸、发码落行、码过期/不存在拒、
consume 是 DELETE RETURNING 单发单用、get_contact 的 WHERE 带 tenant_id(RLS 第二道防线
之外的应用层 WHERE 佐证)、跨 tenant 传参查不到。
"""

import unittest
from unittest.mock import MagicMock, patch

from services.line_binding import line_client_contact as s


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
            s.ensure_table()  # 重跑不炸
        apply_rls.assert_called_with(cur, "line_client_contacts", "line_client_bind_codes")
        self.assertEqual(apply_rls.call_count, 2)


class GenerateBindCodeTests(unittest.TestCase):
    def test_generate_returns_code_and_expiry(self):
        cur = MagicMock()
        cur.fetchone.return_value = {"code": "123456", "expires_at": _FakeTs()}
        with patch("core.db.get_cursor_rls", return_value=_cm(cur)):
            out = s.generate_client_bind_code("t-1", 84)
        self.assertEqual(out["code"], "123456")
        sqls = [c.args[0] for c in cur.execute.call_args_list]
        self.assertTrue(any("DELETE FROM line_client_bind_codes" in q for q in sqls))
        self.assertTrue(any("INSERT INTO line_client_bind_codes" in q for q in sqls))

    def test_generate_failure_returns_none(self):
        with patch("core.db.get_cursor_rls", side_effect=RuntimeError("db down")):
            self.assertIsNone(s.generate_client_bind_code("t-1", 84))


class _FakeTs:
    def isoformat(self):
        return "2026-07-11T00:00:00+00:00"


class PeekAndConsumeCodeTests(unittest.TestCase):
    def test_peek_reads_without_delete(self):
        cur = MagicMock()
        cur.fetchone.return_value = {"tenant_id": "t-1", "workspace_client_id": 84}
        with patch("core.db.get_cursor", return_value=_cm(cur)):
            out = s.peek_client_bind_code("123456")
        self.assertEqual(out, {"tenant_id": "t-1", "workspace_client_id": 84})
        sql = cur.execute.call_args.args[0]
        self.assertNotIn("DELETE", sql)
        self.assertIn("expires_at > now()", sql)

    def test_peek_rejects_malformed_code_without_touching_db(self):
        with patch("core.db.get_cursor") as g:
            self.assertIsNone(s.peek_client_bind_code("abc"))
            self.assertIsNone(s.peek_client_bind_code("12"))
            self.assertIsNone(s.peek_client_bind_code(""))
        g.assert_not_called()

    def test_peek_expired_or_missing_returns_none(self):
        cur = MagicMock()
        cur.fetchone.return_value = None
        with patch("core.db.get_cursor", return_value=_cm(cur)):
            self.assertIsNone(s.peek_client_bind_code("999999"))

    def test_consume_is_delete_returning(self):
        cur = MagicMock()
        cur.fetchone.return_value = {"tenant_id": "t-1", "workspace_client_id": 84}
        with patch("core.db.get_cursor", return_value=_cm(cur)):
            out = s.consume_client_bind_code("123456")
        self.assertEqual(out, {"tenant_id": "t-1", "workspace_client_id": 84})
        sql = cur.execute.call_args.args[0]
        self.assertIn("DELETE FROM line_client_bind_codes", sql)
        self.assertIn("RETURNING", sql)

    def test_consume_expired_returns_none(self):
        cur = MagicMock()
        cur.fetchone.return_value = None  # WHERE expires_at > now() 过滤掉了过期行
        with patch("core.db.get_cursor", return_value=_cm(cur)):
            self.assertIsNone(s.consume_client_bind_code("123456"))

    def test_missing_table_self_heals(self):
        cur = MagicMock()
        cur.execute.side_effect = [
            Exception('relation "line_client_bind_codes" does not exist'),
            None,
        ]
        cur.fetchone.return_value = {"tenant_id": "t-1", "workspace_client_id": 84}
        with (
            patch("core.db.get_cursor", return_value=_cm(cur)),
            patch.object(s, "ensure_table") as ensure,
        ):
            s.consume_client_bind_code("123456")
        ensure.assert_called_once()


class BindAndReadContactTests(unittest.TestCase):
    def test_bind_contact_upserts(self):
        cur = MagicMock()
        with patch("core.db.get_cursor_rls", return_value=_cm(cur)):
            ok = s.bind_contact("t-1", 84, "U-163", display_name="Sister Makeup")
        self.assertTrue(ok)
        sql = cur.execute.call_args.args[0]
        self.assertIn("ON CONFLICT (tenant_id, workspace_client_id) DO UPDATE", sql)

    def test_get_contact_where_scopes_by_tenant(self):
        """应用层 WHERE 双证之一:SQL 必须带 tenant_id 过滤(RLS 是第二道防线)。"""
        cur = MagicMock()
        cur.fetchone.return_value = None
        with patch("core.db.get_cursor_rls", return_value=_cm(cur)) as g:
            out = s.get_contact("t-wrong", 84)
        self.assertIsNone(out)
        g.assert_called_once_with("t-wrong")  # RLS 会话按这个 tenant 建上下文
        sql = cur.execute.call_args.args[0]
        self.assertIn("WHERE tenant_id = %s AND workspace_client_id = %s", sql)

    def test_get_contact_found(self):
        cur = MagicMock()
        cur.fetchone.return_value = {
            "tenant_id": "t-1",
            "workspace_client_id": 84,
            "line_user_id": "U-163",
            "preferred_lang": "th",
            "display_name": "Sister Makeup",
            "bound_at": None,
            "last_active_at": None,
        }
        with patch("core.db.get_cursor_rls", return_value=_cm(cur)):
            out = s.get_contact("t-1", 84)
        self.assertEqual(out["line_user_id"], "U-163")

    def test_list_contacts_by_line_user_multi_client(self):
        cur = MagicMock()
        cur.fetchall.return_value = [
            {"tenant_id": "t-1", "workspace_client_id": 84},
            {"tenant_id": "t-1", "workspace_client_id": 91},
        ]
        with patch("core.db.get_cursor", return_value=_cm(cur)):
            out = s.list_contacts_by_line_user("U-163")
        self.assertEqual(len(out), 2)

    def test_list_contacts_failure_returns_empty(self):
        with patch("core.db.get_cursor", side_effect=RuntimeError("db down")):
            self.assertEqual(s.list_contacts_by_line_user("U-163"), [])


class ClientBoundTextTests(unittest.TestCase):
    def test_four_languages_available(self):
        for lang in ("th", "en", "zh", "ja"):
            self.assertTrue(s.client_bound_text(lang))

    def test_unknown_lang_falls_back_to_thai(self):
        self.assertEqual(s.client_bound_text("fr"), s.client_bound_text("th"))
        self.assertEqual(s.client_bound_text(None), s.client_bound_text("th"))


if __name__ == "__main__":
    unittest.main()
