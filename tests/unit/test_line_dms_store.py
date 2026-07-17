# -*- coding: utf-8 -*-
"""services/line_dms/store.py DAL 行为(DL-1 · B4 绑定 + B6 会话)。

全 FakeCursor mock(不打真库 · 不发任何 LINE 消息)。绑定/绑定码走 get_cursor(owner),
会话态走 get_cursor_rls(tenant),两者都 patch 成同一 fake。
"""

import unittest
from unittest import mock

from core import db  # noqa: F401 · 先完成 db import,避免 re-export partial-init
from services.line_dms import store


class FakeDT:
    def isoformat(self):
        return "2026-07-17T00:00:00+00:00"


class FakeCursor:
    def __init__(self, fetchone=None, fetchone_seq=None, rowcount=0):
        self.calls = []
        self._fetchone = fetchone
        self._seq = list(fetchone_seq) if fetchone_seq is not None else None
        self.rowcount = rowcount

    def execute(self, sql, params=None):
        self.calls.append((sql, params))

    def fetchone(self):
        if self._seq is not None:
            return self._seq.pop(0) if self._seq else None
        return self._fetchone

    def all_sql(self):
        return " ".join(c[0] for c in self.calls)

    @property
    def last_params(self):
        return self.calls[-1][1] if self.calls else None


class _CM:
    def __init__(self, cur):
        self.cur = cur

    def __enter__(self):
        return self.cur

    def __exit__(self, *a):
        return False


def _patch_via_db(cur):
    """把 get_cursor 与 get_cursor_rls 同时指向同一 fake(store 两者混用)。"""

    def factory(*a, **k):
        return _CM(cur)

    return mock.patch.multiple("core.db", get_cursor=factory, get_cursor_rls=factory)


class GenerateBindCodeTests(unittest.TestCase):
    def test_invalidates_old_and_inserts(self):
        cur = FakeCursor(fetchone={"code": "123456", "expires_at": FakeDT()})
        with _patch_via_db(cur):
            out = store.generate_bind_code("t1", "u1", ttl_minutes=10)
        self.assertEqual(out["code"], "123456")
        self.assertEqual(out["expires_at"], "2026-07-17T00:00:00+00:00")
        sql = cur.all_sql()
        self.assertIn("UPDATE line_dms_binding_codes", sql)
        self.assertIn("INSERT INTO line_dms_binding_codes", sql)

    def test_no_row_none(self):
        with _patch_via_db(FakeCursor(fetchone=None)):
            self.assertIsNone(store.generate_bind_code("t1", "u1"))


class ConsumeBindCodeTests(unittest.TestCase):
    def test_bad_format_skips_db(self):
        with _patch_via_db(FakeCursor(fetchone={"tenant_id": "t", "user_id": "u"})):
            self.assertIsNone(store.consume_bind_code("12345"))  # 5 位
            self.assertIsNone(store.consume_bind_code("abcdef"))

    def test_valid_returns_identity(self):
        cur = FakeCursor(fetchone={"tenant_id": "t9", "user_id": "u9"})
        with _patch_via_db(cur):
            out = store.consume_bind_code("654321")
        self.assertEqual(out, {"tenant_id": "t9", "user_id": "u9"})
        self.assertIn("used_at IS NULL", cur.all_sql())
        self.assertIn("expires_at > now()", cur.all_sql())

    def test_expired_or_used_none(self):
        with _patch_via_db(FakeCursor(fetchone=None)):
            self.assertIsNone(store.consume_bind_code("654321"))


class CreateBindingTests(unittest.TestCase):
    def test_conflict_line_bound_other_rejected(self):
        cur = FakeCursor(fetchone_seq=[{"user_id": "other"}])
        with _patch_via_db(cur):
            self.assertFalse(store.create_or_update_binding("t1", "u1", "L1"))
        self.assertNotIn("INSERT INTO line_dms_bindings", cur.all_sql())

    def test_happy_upserts(self):
        cur = FakeCursor(fetchone_seq=[None])
        with _patch_via_db(cur):
            self.assertTrue(
                store.create_or_update_binding("t1", "u1", "L1", display_name="Somchai")
            )
        sql = cur.all_sql()
        self.assertIn("DELETE FROM line_dms_bindings", sql)
        self.assertIn("ON CONFLICT (line_user_id) DO UPDATE", sql)


class GetBindingTests(unittest.TestCase):
    def test_by_user_returns_dict(self):
        cur = FakeCursor(fetchone={"line_user_id": "L1", "tenant_id": "t1", "display_name": "N"})
        with _patch_via_db(cur):
            out = store.get_binding_by_user("u1")
        self.assertEqual(out["line_user_id"], "L1")

    def test_by_line_user_normalizes_ids(self):
        cur = FakeCursor(fetchone={"tenant_id": "t1", "user_id": "u1", "display_name": "N"})
        with _patch_via_db(cur):
            out = store.get_binding_by_line_user("L1")
        self.assertEqual(out["tenant_id"], "t1")
        self.assertEqual(out["user_id"], "u1")
        self.assertEqual(out["line_user_id"], "L1")

    def test_by_line_user_empty_none(self):
        self.assertIsNone(store.get_binding_by_line_user(""))


class UnbindTests(unittest.TestCase):
    def test_unbind_by_line_user_rowcount(self):
        with _patch_via_db(FakeCursor(rowcount=1)):
            self.assertTrue(store.unbind_by_line_user("L1"))
        with _patch_via_db(FakeCursor(rowcount=0)):
            self.assertFalse(store.unbind_by_line_user("L1"))

    def test_unbind_by_user_true(self):
        with _patch_via_db(FakeCursor()):
            self.assertTrue(store.unbind_by_user("u1"))


class FakeSessionCursor:
    """有状态会话 fake:INSERT 存 ttl,SELECT 按 ttl>0(模拟 expires_at>now())返回。"""

    def __init__(self):
        self.rows = {}
        self._ret = None

    def execute(self, sql, params=None):
        if "INSERT INTO dms_line_sessions" in sql:
            tenant, line_user, state, payload_json, ttl = params
            import json

            self.rows[(tenant, line_user)] = {
                "state": state,
                "payload": json.loads(payload_json),
                "ttl": int(ttl),
            }
            self._ret = None
        elif "SELECT state, payload FROM dms_line_sessions" in sql:
            tenant, line_user = params
            r = self.rows.get((tenant, line_user))
            self._ret = (
                {"state": r["state"], "payload": r["payload"]} if r and r["ttl"] > 0 else None
            )
        elif "DELETE FROM dms_line_sessions" in sql:
            self.rows.pop((params[0], params[1]), None)
            self._ret = None

    def fetchone(self):
        return self._ret


class SessionTests(unittest.TestCase):
    def test_set_then_get_roundtrip(self):
        cur = FakeSessionCursor()
        with _patch_via_db(cur):
            store.set_session("t1", "L1", "await_id", {"step": 1}, ttl_minutes=30)
            out = store.get_session("t1", "L1")
        self.assertEqual(out["state"], "await_id")
        self.assertEqual(out["payload"], {"step": 1})

    def test_expired_get_returns_none(self):
        cur = FakeSessionCursor()
        with _patch_via_db(cur):
            store.set_session("t1", "L1", "await_id", {"step": 1}, ttl_minutes=0)  # 立即过期
            self.assertIsNone(store.get_session("t1", "L1"))

    def test_clear_removes(self):
        cur = FakeSessionCursor()
        with _patch_via_db(cur):
            store.set_session("t1", "L1", "s", {}, ttl_minutes=30)
            store.clear_session("t1", "L1")
            self.assertIsNone(store.get_session("t1", "L1"))


if __name__ == "__main__":
    unittest.main()
