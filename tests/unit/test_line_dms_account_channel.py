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

    def test_unknown_stored_value_normalizes_to_legacy(self):
        cur = _Cur(row={"channel_key": "garbage"})
        with mock.patch("core.db.get_cursor", lambda *a, **k: _CM(cur)):
            self.assertEqual(account_channel.get_channel("t1"), "dms")

    def test_stored_channel_returned(self):
        cur = _Cur(row={"channel_key": "dms_a"})
        with mock.patch("core.db.get_cursor", lambda *a, **k: _CM(cur)):
            self.assertEqual(account_channel.get_channel("t1"), "dms_a")

    def test_empty_subject_defaults_without_query(self):
        self.assertEqual(account_channel.get_channel(""), "dms")


class SetChannelTests(unittest.TestCase):
    def test_invalid_channel_rejected(self):
        out = account_channel.set_channel("t1", "nope")
        self.assertEqual(out, {"error": "dms_channel.invalid_channel"})

    def test_missing_subject_rejected(self):
        out = account_channel.set_channel("", "dms_a")
        self.assertEqual(out, {"error": "dms_channel.missing_subject"})

    def test_same_channel_is_noop_and_keeps_bindings(self):
        with (
            mock.patch.object(account_channel, "get_channel", return_value="dms_a"),
            mock.patch("services.line_dms.store.unbind_by_user") as unbind,
            mock.patch("services.line_dms.store.void_bind_codes_for_user") as void,
        ):
            out = account_channel.set_channel("t1", "dms_a", actor_id="admin")
        self.assertEqual(out["changed"], False)
        unbind.assert_not_called()
        void.assert_not_called()

    def test_change_revokes_every_user_binding_and_pending_code(self):
        cur = _Cur()
        with (
            mock.patch.object(account_channel, "get_channel", return_value="dms"),
            mock.patch.object(account_channel, "_affected_user_ids", return_value=["u1", "u2"]),
            mock.patch("services.line_dms.store.unbind_by_user", return_value=True) as unbind,
            mock.patch(
                "services.line_dms.store.void_bind_codes_for_user", return_value=True
            ) as void,
            mock.patch("core.db.get_cursor", lambda *a, **k: _CM(cur)),
        ):
            out = account_channel.set_channel("t1", "dms_b", actor_id="admin")
        self.assertTrue(out["changed"])
        self.assertEqual(out["unbound"], 2)
        self.assertEqual(out["codes_voided"], 2)
        self.assertEqual(sorted(c.args[0] for c in unbind.call_args_list), ["u1", "u2"])
        sql = cur.all_sql()
        self.assertIn("INSERT INTO dms_account_line_channels", sql)
        self.assertIn("ON CONFLICT (subject_id) DO UPDATE", sql)


if __name__ == "__main__":
    unittest.main()
