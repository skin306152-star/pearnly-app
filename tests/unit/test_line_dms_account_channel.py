# -*- coding: utf-8 -*-
"""Per-account LINE OA assignment: default, validation and the change-OA revoke policy."""

from __future__ import annotations

import unittest
from unittest import mock

from services.line_dms import account_channel


class _CM:
    def __init__(self, cur):
        self.cur = cur

    def __enter__(self):
        return self.cur

    def __exit__(self, *a):
        return False


class _Cur:
    def __init__(self, row=None):
        self.row = row
        self.calls = []

    def execute(self, sql, params=None):
        self.calls.append((sql, params))

    def fetchone(self):
        return self.row

    def fetchall(self):
        return []

    def all_sql(self):
        return " ".join(c[0] for c in self.calls)


class SubjectTests(unittest.TestCase):
    def test_tenant_first(self):
        self.assertEqual(account_channel.subject_for("t1", "u1"), "t1")
        self.assertEqual(account_channel.subject_for(None, "u1"), "u1")
        self.assertEqual(account_channel.subject_for(None, None), "")


class GetChannelTests(unittest.TestCase):
    def test_missing_row_defaults_to_legacy(self):
        cur = _Cur(row=None)
        with mock.patch("core.db.get_cursor", lambda *a, **k: _CM(cur)):
            self.assertEqual(account_channel.get_channel("t1"), "dms")

    def test_unknown_stored_value_fails_closed(self):
        cur = _Cur(row={"channel_key": "garbage"})
        with mock.patch("core.db.get_cursor", lambda *a, **k: _CM(cur)):
            with self.assertRaises(account_channel.AccountChannelError) as caught:
                account_channel.get_channel("t1")
        self.assertEqual(caught.exception.code, "dms_channel.unknown_channel")

    def test_stored_channel_returned(self):
        cur = _Cur(row={"channel_key": "dms_a"})
        with mock.patch("core.db.get_cursor", lambda *a, **k: _CM(cur)):
            self.assertEqual(account_channel.get_channel("t1"), "dms_a")

    def test_db_error_fails_closed(self):
        with mock.patch("core.db.get_cursor", side_effect=RuntimeError("db down")):
            with self.assertRaises(account_channel.AccountChannelError) as caught:
                account_channel.get_channel("t1")
        self.assertEqual(caught.exception.code, "dms_channel.unavailable")

    def test_empty_subject_defaults_without_query(self):
        self.assertEqual(account_channel.get_channel(""), "dms")


class _ScriptedCur:
    """Route each SQL by substring to canned fetchone/fetchall/rowcount results."""

    def __init__(self, routes):
        self.routes = routes
        self.calls = []
        self._ret = None
        self.rowcount = 0

    def execute(self, sql, params=None):
        self.calls.append((sql, params))
        self._ret = None
        self.rowcount = 0
        for needle, response in self.routes.items():
            if needle in sql:
                if isinstance(response, dict) and (
                    "fetchone" in response or "rowcount" in response
                ):
                    self._ret = response.get("fetchone")
                    self.rowcount = response.get("rowcount", 0)
                else:
                    self._ret = response
                break

    def fetchone(self):
        return self._ret

    def fetchall(self):
        return self._ret if isinstance(self._ret, list) else []

    def all_sql(self):
        return " ".join(c[0] for c in self.calls)


class SetChannelTests(unittest.TestCase):
    def test_invalid_channel_rejected(self):
        out = account_channel.set_channel("t1", "nope")
        self.assertEqual(out, {"error": "dms_channel.invalid_channel"})

    def test_missing_subject_rejected(self):
        out = account_channel.set_channel("", "dms_a")
        self.assertEqual(out, {"error": "dms_channel.missing_subject"})

    def test_same_channel_is_noop_and_keeps_bindings(self):
        cur = _ScriptedCur(
            {"SELECT channel_key FROM dms_account_line_channels": {"channel_key": "dms_a"}}
        )
        with mock.patch("core.db.get_cursor", lambda *a, **k: _CM(cur)):
            out = account_channel.set_channel("t1", "dms_a", actor_id="admin")
        self.assertEqual(out["changed"], False)
        self.assertNotIn("DELETE FROM line_dms_bindings", cur.all_sql())
        self.assertIn("pg_advisory_xact_lock", cur.all_sql())

    def test_change_revokes_every_user_binding_and_pending_code(self):
        cur = _ScriptedCur(
            {
                "SELECT channel_key FROM dms_account_line_channels": {"channel_key": "dms"},
                "SELECT owner_user_id::text": {"owner_user_id": "owner"},
                "SELECT id::text AS id FROM users": [{"id": "u1"}],
                "SELECT line_user_id, channel_key, tenant_id::text": [
                    {"line_user_id": "L1", "channel_key": "dms", "tenant_id": "t1"}
                ],
                "UPDATE line_dms_binding_codes": {"rowcount": 1},
                "DELETE FROM line_dms_bindings": {"rowcount": 1},
            }
        )
        with (
            mock.patch("core.db.get_cursor", lambda *a, **k: _CM(cur)),
            mock.patch("services.line_dms.menu_sync.request_sync") as sync,
        ):
            out = account_channel.set_channel("t1", "dms_b", actor_id="admin")
        self.assertTrue(out["changed"])
        self.assertEqual(out["unbound"], 1)
        self.assertEqual(out["codes_voided"], 1)
        sql = cur.all_sql()
        self.assertIn("INSERT INTO dms_account_line_channels", sql)
        self.assertIn("ON CONFLICT (subject_id) DO UPDATE", sql)
        self.assertIn("pg_advisory_xact_lock", sql)
        self.assertIn("DELETE FROM dms_line_sessions", sql)
        self.assertIn("DELETE FROM line_dms_login_tickets", sql)
        sync.assert_called_once_with("L1", "dms")

    def test_change_rolls_back_and_reports_failure(self):
        cur = _ScriptedCur(
            {
                "SELECT channel_key FROM dms_account_line_channels": {"channel_key": "dms"},
                "SELECT owner_user_id::text": {"owner_user_id": "owner"},
                "SELECT id::text AS id FROM users": [{"id": "u1"}],
                "SELECT line_user_id, channel_key, tenant_id::text": [],
                "INSERT INTO dms_account_line_channels": RuntimeError("boom"),
            }
        )

        class _BoomCur(_ScriptedCur):
            def execute(self, sql, params=None):
                if "INSERT INTO dms_account_line_channels" in sql:
                    raise RuntimeError("boom")
                return super().execute(sql, params)

        boom = _BoomCur(cur.routes)
        with (
            mock.patch("core.db.get_cursor", lambda *a, **k: _CM(boom)),
            mock.patch("services.line_dms.menu_sync.request_sync") as sync,
        ):
            out = account_channel.set_channel("t1", "dms_b", actor_id="admin")
        self.assertEqual(out, {"error": "dms_channel.save_failed"})
        sync.assert_not_called()


if __name__ == "__main__":
    unittest.main()
