# -*- coding: utf-8 -*-
"""binding_state must revoke only the exact (tenant, OA, LINE user) scope."""

import unittest
from unittest import mock

from services.line_dms import binding_state


class _Cur:
    def __init__(self):
        self.calls = []
        self._row = None

    def execute(self, sql, params=None):
        self.calls.append((sql, params))

    def fetchone(self):
        return self._row

    def all_sql(self):
        return " ".join(c[0] for c in self.calls)


class InvalidateScopeTests(unittest.TestCase):
    def test_delete_is_scoped_to_tenant_channel_and_line(self):
        cur = _Cur()
        binding_state.invalidate(cur, "L1", "u1", "dms_b", "t1")
        sql = cur.all_sql()
        self.assertIn(
            "DELETE FROM dms_line_sessions WHERE tenant_id=%s AND channel_key=%s "
            "AND line_user_id=%s",
            sql,
        )
        self.assertIn(
            "DELETE FROM line_dms_login_tickets WHERE tenant_id=%s AND user_id=%s "
            "AND channel_key=%s",
            sql,
        )
        self.assertEqual(cur.calls[0][1], ("t1", "dms_b", "L1"))
        self.assertEqual(cur.calls[1][1], ("t1", "u1", "dms_b"))

    def test_unknown_channel_never_normalizes_to_legacy_delete(self):
        cur = _Cur()
        binding_state.invalidate(cur, "L1", "u1", "nope", "t1")
        # Unknown keys fail closed to the legacy OA, never to another OA's rows.
        self.assertEqual(cur.calls[0][1], ("t1", "dms", "L1"))


class LockScopeTests(unittest.TestCase):
    def test_lock_scope_checks_the_same_channel_under_the_lock(self):
        cur = _Cur()
        cur._row = {"id": "epoch"}
        binding = {
            "id": "epoch",
            "line_user_id": "L1",
            "tenant_id": "t1",
            "user_id": "u1",
            "channel_key": "dms_a",
        }
        with mock.patch("services.line_dms.binding_guard.snapshot", return_value=binding):
            binding_state.lock_scope(cur, "L1", "dms_a")
        self.assertIn("channel_key=%s", cur.all_sql())
        self.assertEqual(cur.calls[0][1], ("dms-binding:dms_a:L1",))


if __name__ == "__main__":
    unittest.main()
