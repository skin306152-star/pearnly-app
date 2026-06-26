# -*- coding: utf-8 -*-
"""REFACTOR-D2 · services/email_ingest/store.py 行为/契约覆盖

补行为测试(既有 test_email_ingest_store_contract.py 只验 re-export/可调用):
- get_email_account: 返回 dict / None / 异常吞
- get_email_account_safe: 剥 password_enc · has_password 标志
- upsert_email_account: interval_min 兜底 (非 5/15/60 → 15) · 有/无 password 两条 SQL 分支
- delete_email_account: rowcount 语义
- list_enabled_email_accounts: 列表 / 空
- update_email_account_status: success+fetched / success no-fetch / failure 三分支
- insert_email_ingest_log / list_email_ingest_logs
- is_email_uid_seen / mark_email_uid_seen: 截断 subject[:500]/sender[:200]

风格:patch("core.db.get_cursor") 给假游标 · 验返回结构 / SQL / 边界 / 异常吞。
"""

import sys
import types
import unittest
from pathlib import Path
from unittest.mock import patch

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

if "psycopg2" not in sys.modules:
    _pg = types.ModuleType("psycopg2")
    _pg.connect = lambda *a, **k: (_ for _ in ()).throw(RuntimeError("stub"))
    _pg.Error = Exception
    _pg.OperationalError = Exception
    _pg.extras = types.ModuleType("psycopg2.extras")
    _pg.extras.RealDictCursor = object
    _pg.extras.DictCursor = object
    _pg.extras.execute_values = lambda *a, **k: None
    _pg.extras.Json = lambda x: x
    _pg.pool = types.ModuleType("psycopg2.pool")

    class _StubPool:
        def __init__(self, *a, **k):
            pass

        def getconn(self):
            raise RuntimeError("stub")

        def putconn(self, *a, **k):
            pass

        def closeall(self):
            pass

    _pg.pool.ThreadedConnectionPool = _StubPool
    _pg.pool.SimpleConnectionPool = _StubPool
    _pg.sql = types.ModuleType("psycopg2.sql")
    _pg.sql.SQL = lambda s: s
    _pg.sql.Identifier = lambda s: s
    sys.modules["psycopg2"] = _pg
    sys.modules["psycopg2.extras"] = _pg.extras
    sys.modules["psycopg2.pool"] = _pg.pool
    sys.modules["psycopg2.sql"] = _pg.sql

from core import db  # noqa: E402
from services.email_ingest import store  # noqa: E402


class _FakeCursor:
    """记录所有 execute · 按队列返 fetchone/fetchall · 可设 rowcount。"""

    def __init__(self, one_seq=None, all_seq=None, rowcount=0):
        self.one_seq = list(one_seq or [])
        self.all_seq = list(all_seq or [])
        self.rowcount = rowcount
        self.executed = []

    def execute(self, sql, params=None):
        self.executed.append((sql, params))

    def fetchone(self):
        return self.one_seq.pop(0) if self.one_seq else None

    def fetchall(self):
        return self.all_seq.pop(0) if self.all_seq else []


class _CM:
    def __init__(self, cur):
        self.cur = cur

    def __enter__(self):
        return self.cur

    def __exit__(self, *a):
        return False


class _ExplodingCursor:
    def execute(self, *a, **k):
        raise RuntimeError("DB outage")

    def fetchone(self):
        return None

    def fetchall(self):
        return []


def _patch(cur):
    # 迁移期 store 混用 get_cursor(裸 owner)/get_cursor_rls(穿 user)→ 双挂同一 fake。
    from tests.unit._cursor_patch import patch_both

    return patch_both(factory=lambda *a, **k: _CM(cur))


class GetEmailAccountTests(unittest.TestCase):
    def test_returns_dict(self):
        cur = _FakeCursor(one_seq=[{"id": "a1", "user_id": "u1", "password_enc": b"x"}])
        with _patch(cur):
            r = store.get_email_account("u1")
        self.assertEqual(r["id"], "a1")
        # str(user_id) 传给 SQL
        self.assertEqual(cur.executed[0][1], ("u1",))

    def test_returns_none_when_no_row(self):
        with _patch(_FakeCursor(one_seq=[None])):
            self.assertIsNone(store.get_email_account("u1"))

    def test_exception_returns_none(self):
        with _patch(_ExplodingCursor()):
            self.assertIsNone(store.get_email_account("u1"))


class GetEmailAccountSafeTests(unittest.TestCase):
    def test_strips_password_and_sets_flag_true(self):
        cur = _FakeCursor(one_seq=[{"id": "a1", "password_enc": b"secret"}])
        with _patch(cur):
            r = store.get_email_account_safe("u1")
        self.assertNotIn("password_enc", r)
        self.assertTrue(r["has_password"])

    def test_no_password_flag_false(self):
        cur = _FakeCursor(one_seq=[{"id": "a1", "password_enc": None}])
        with _patch(cur):
            r = store.get_email_account_safe("u1")
        self.assertFalse(r["has_password"])

    def test_none_passthrough(self):
        with _patch(_FakeCursor(one_seq=[None])):
            self.assertIsNone(store.get_email_account_safe("u1"))


class UpsertEmailAccountTests(unittest.TestCase):
    def test_interval_min_invalid_falls_back_to_15(self):
        cur = _FakeCursor(one_seq=[{"id": "new1"}])
        with _patch(cur):
            store.upsert_email_account(
                "u1", "a@b.com", "imap.x", 993, True, b"pw", interval_min=999
            )
        # interval_min 是 INSERT 参数的最后一个值
        self.assertIn(15, cur.executed[0][1])
        self.assertNotIn(999, cur.executed[0][1])

    def test_interval_min_valid_kept(self):
        cur = _FakeCursor(one_seq=[{"id": "new1"}])
        with _patch(cur):
            store.upsert_email_account("u1", "a@b.com", "imap.x", 993, True, b"pw", interval_min=60)
        self.assertIn(60, cur.executed[0][1])

    def test_with_password_includes_password_in_sql(self):
        cur = _FakeCursor(one_seq=[{"id": "n1"}])
        with _patch(cur):
            rid = store.upsert_email_account("u1", "a@b.com", "h", 993, True, b"pw")
        self.assertEqual(rid, "n1")
        self.assertIn(b"pw", cur.executed[0][1])

    def test_without_password_uses_no_password_sql(self):
        cur = _FakeCursor(one_seq=[{"id": "n2"}])
        with _patch(cur):
            store.upsert_email_account("u1", "a@b.com", "h", 993, True, None)
        # 无密码分支 SQL 用 ''::bytea · password_enc 不在参数里
        self.assertIn("'::bytea", cur.executed[0][0])

    def test_returns_none_when_no_row(self):
        with _patch(_FakeCursor(one_seq=[None])):
            self.assertIsNone(store.upsert_email_account("u1", "a@b.com", "h", 993, True, b"pw"))

    def test_exception_returns_none(self):
        with _patch(_ExplodingCursor()):
            self.assertIsNone(store.upsert_email_account("u1", "a@b.com", "h", 993, True, b"pw"))


class DeleteEmailAccountTests(unittest.TestCase):
    def test_returns_true_when_rowcount_positive(self):
        with _patch(_FakeCursor(rowcount=1)):
            self.assertTrue(store.delete_email_account("u1"))

    def test_returns_false_when_no_rows(self):
        with _patch(_FakeCursor(rowcount=0)):
            self.assertFalse(store.delete_email_account("u1"))

    def test_exception_returns_false(self):
        with _patch(_ExplodingCursor()):
            self.assertFalse(store.delete_email_account("u1"))


class ListEnabledEmailAccountsTests(unittest.TestCase):
    def test_returns_rows(self):
        cur = _FakeCursor(all_seq=[[{"id": "a"}, {"id": "b"}]])
        with _patch(cur):
            rows = store.list_enabled_email_accounts()
        self.assertEqual(len(rows), 2)
        self.assertIn("enabled = TRUE", cur.executed[0][0])

    def test_exception_returns_empty(self):
        with _patch(_ExplodingCursor()):
            self.assertEqual(store.list_enabled_email_accounts(), [])


class UpdateEmailAccountStatusTests(unittest.TestCase):
    def test_success_fetched_increments_success_count(self):
        cur = _FakeCursor()
        with _patch(cur):
            store.update_email_account_status("a1", True, fetched_any=True)
        self.assertIn("success_count   = success_count + 1", cur.executed[0][0])
        self.assertIn("last_fetched_at = NOW()", cur.executed[0][0])

    def test_success_no_fetch_no_success_increment(self):
        cur = _FakeCursor()
        with _patch(cur):
            store.update_email_account_status("a1", True, fetched_any=False)
        self.assertNotIn("success_count", cur.executed[0][0])

    def test_failure_increments_failure_count_and_writes_error(self):
        cur = _FakeCursor()
        with _patch(cur):
            store.update_email_account_status("a1", False, error_msg="boom")
        self.assertIn("failure_count   = failure_count + 1", cur.executed[0][0])
        self.assertEqual(cur.executed[0][1], ("boom", "a1"))

    def test_exception_swallowed(self):
        with _patch(_ExplodingCursor()):
            store.update_email_account_status("a1", True)  # 不抛即通过


class InsertEmailIngestLogTests(unittest.TestCase):
    def test_returns_id_and_coerces_stats(self):
        cur = _FakeCursor(one_seq=[{"id": "log1"}])
        stats = {"status": "ok", "emails_scanned": "5", "error_details": [{"x": 1}]}
        with _patch(cur):
            rid = store.insert_email_ingest_log("a1", "u1", stats, trigger="manual")
        self.assertEqual(rid, "log1")
        params = cur.executed[0][1]
        self.assertEqual(params[0], "a1")
        self.assertEqual(params[3], 5)  # emails_scanned coerced to int
        self.assertEqual(params[-1], "manual")

    def test_missing_stats_default_zero(self):
        cur = _FakeCursor(one_seq=[{"id": "log2"}])
        with _patch(cur):
            store.insert_email_ingest_log("a1", "u1", {})
        params = cur.executed[0][1]
        self.assertEqual(params[3], 0)

    def test_exception_returns_none(self):
        with _patch(_ExplodingCursor()):
            self.assertIsNone(store.insert_email_ingest_log("a1", "u1", {}))


class ListEmailIngestLogsTests(unittest.TestCase):
    def test_returns_rows_with_limit(self):
        cur = _FakeCursor(all_seq=[[{"id": "1"}]])
        with _patch(cur):
            rows = store.list_email_ingest_logs("u1", limit=7)
        self.assertEqual(len(rows), 1)
        self.assertEqual(cur.executed[0][1], ("u1", 7))

    def test_exception_returns_empty(self):
        with _patch(_ExplodingCursor()):
            self.assertEqual(store.list_email_ingest_logs("u1"), [])


class IsEmailUidSeenTests(unittest.TestCase):
    def test_seen_true(self):
        with _patch(_FakeCursor(one_seq=[{"?column?": 1}])):
            self.assertTrue(store.is_email_uid_seen("a1", "uid1"))

    def test_not_seen_false(self):
        with _patch(_FakeCursor(one_seq=[None])):
            self.assertFalse(store.is_email_uid_seen("a1", "uid1"))

    def test_exception_false(self):
        with _patch(_ExplodingCursor()):
            self.assertFalse(store.is_email_uid_seen("a1", "uid1"))


class MarkEmailUidSeenTests(unittest.TestCase):
    def test_truncates_subject_and_sender(self):
        cur = _FakeCursor()
        with _patch(cur):
            ok = store.mark_email_uid_seen("a1", "uid1", "h1", "S" * 600, "X" * 300)
        self.assertTrue(ok)
        params = cur.executed[0][1]
        self.assertEqual(len(params[3]), 500)  # subject[:500]
        self.assertEqual(len(params[4]), 200)  # sender[:200]

    def test_none_subject_sender_become_empty(self):
        cur = _FakeCursor()
        with _patch(cur):
            store.mark_email_uid_seen("a1", "uid1", None, None, None)
        params = cur.executed[0][1]
        self.assertEqual(params[3], "")
        self.assertEqual(params[4], "")

    def test_exception_returns_false(self):
        with _patch(_ExplodingCursor()):
            self.assertFalse(store.mark_email_uid_seen("a1", "uid1", None, "s", "x"))


if __name__ == "__main__":
    unittest.main()
