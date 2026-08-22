# -*- coding: utf-8 -*-
"""services/line_dms/login_tickets.py 一次性登录票据 DAL 行为。

全 FakeCursor mock(不打真库)。覆盖:明文不落库 / 只消费一次 / 过期返 None /
TTL 60s 上限 / 核销是原子 DELETE RETURNING。
"""

import hashlib
import unittest
from datetime import datetime, timedelta, timezone
from unittest import mock

from core import db  # noqa: F401 · 先完成 db import,避免 re-export partial-init
from services.line_dms import login_tickets as lt


class _CM:
    def __init__(self, cur):
        self.cur = cur

    def __enter__(self):
        return self.cur

    def __exit__(self, *a):
        return False


def _patch(cur):
    def factory(*a, **k):
        return _CM(cur)

    return mock.patch.multiple("core.db", get_cursor=factory)


class FakeTicketCursor:
    """有状态票据 fake:INSERT 存 (hash → 行);DELETE RETURNING 只对未过期行
    返回并删行(模拟 expires_at > now()),过期/无行返 None 且不删。"""

    def __init__(self):
        self.now = datetime.now(timezone.utc)
        self.rows = {}
        self.calls = []
        self._ret = None

    def advance(self, seconds: float):
        self.now += timedelta(seconds=seconds)

    def execute(self, sql, params=None):
        self.calls.append((sql, params))
        if "INSERT INTO line_dms_login_tickets" in sql:
            ticket_hash, tenant_id, user_id, ttl = params
            expires_at = self.now + timedelta(seconds=ttl)
            self.rows[ticket_hash] = {
                "tenant_id": tenant_id,
                "user_id": user_id,
                "expires_at": expires_at,
            }
            self._ret = {"ticket_hash": ticket_hash, "expires_at": expires_at}
        elif "WHERE expires_at <= now()" in sql:
            self.rows = {key: row for key, row in self.rows.items() if row["expires_at"] > self.now}
            self._ret = None
        elif "DELETE FROM line_dms_login_tickets" in sql:
            row = self.rows.get(params[0])
            if row and row["expires_at"] > self.now:
                self.rows.pop(params[0])
                self._ret = {"tenant_id": row["tenant_id"], "user_id": row["user_id"]}
            else:
                self._ret = None

    def fetchone(self):
        return self._ret

    def all_sql(self):
        return " ".join(sql for sql, _ in self.calls)

    def all_params(self):
        return [p for _, p in self.calls if p]


class IssueTicketTests(unittest.TestCase):
    def test_plaintext_never_persisted(self):
        """明文只返调用方一次:所有 SQL 参数/假库键里只有 SHA256 哈希。"""
        cur = FakeTicketCursor()
        with _patch(cur):
            out = lt.issue_login_ticket("t1", "u1")
        ticket = out["ticket"]
        digest = hashlib.sha256(ticket.encode("utf-8")).hexdigest()
        flat = [v for params in cur.all_params() for v in params]
        self.assertIn(digest, flat)
        self.assertNotIn(ticket, flat)
        self.assertEqual(set(cur.rows), {digest})
        self.assertNotIn(ticket, cur.all_sql())

    def test_tickets_unique(self):
        cur = FakeTicketCursor()
        with _patch(cur):
            a = lt.issue_login_ticket("t1", "u1")["ticket"]
            b = lt.issue_login_ticket("t1", "u1")["ticket"]
        self.assertNotEqual(a, b)
        self.assertEqual(len(cur.rows), 2)


class TtlCapTests(unittest.TestCase):
    def test_ttl_capped_at_max(self):
        """ttl_seconds=3600 → 到期时间被夹到 60s 上限。"""
        cur = FakeTicketCursor()
        with _patch(cur):
            before = datetime.now(timezone.utc)
            out = lt.issue_login_ticket("t1", "u1", ttl_seconds=3600)
            after = datetime.now(timezone.utc)
        exp = datetime.fromisoformat(out["expires_at"])
        self.assertLessEqual((exp - after).total_seconds(), lt.MAX_TICKET_TTL_SECONDS)
        self.assertGreater((exp - before).total_seconds(), 0)

    def test_short_ttl_honored(self):
        cur = FakeTicketCursor()
        with _patch(cur):
            before = datetime.now(timezone.utc)
            out = lt.issue_login_ticket("t1", "u1", ttl_seconds=5)
        delta = (datetime.fromisoformat(out["expires_at"]) - before).total_seconds()
        self.assertGreaterEqual(delta, 5)
        self.assertLess(delta, 7)

    def test_default_ttl_is_max(self):
        cur = FakeTicketCursor()
        with _patch(cur):
            before = datetime.now(timezone.utc)
            out = lt.issue_login_ticket("t1", "u1")
        delta = (datetime.fromisoformat(out["expires_at"]) - before).total_seconds()
        self.assertGreaterEqual(delta, lt.MAX_TICKET_TTL_SECONDS)
        self.assertLess(delta, lt.MAX_TICKET_TTL_SECONDS + 2)


class _RecordingCursor:
    """只记录 SQL 的空 cursor(ensure 走 CREATE/ALTER/POLICY,无返回行)。"""

    def __init__(self):
        self.sql = []

    def execute(self, stmt, params=None):
        self.sql.append(stmt)

    def fetchone(self):
        return None


class EnsureTableDdlTests(unittest.TestCase):
    """ensure 幂等 DDL 契约:五字段 + expires_at 索引 + apply_tenant_rls 惯例。"""

    def _ensure_sql(self):
        cur = _RecordingCursor()
        with _patch(cur):
            lt.ensure_table()
        return " ".join(cur.sql)

    def test_ddl_contract(self):
        ddl = lt._DDL
        self.assertIn("CREATE TABLE IF NOT EXISTS line_dms_login_tickets", ddl)
        self.assertIn("ticket_hash text PRIMARY KEY", ddl)
        self.assertIn("tenant_id uuid NOT NULL", ddl)
        self.assertIn("user_id uuid NOT NULL", ddl)
        self.assertIn("expires_at timestamptz NOT NULL", ddl)
        self.assertIn("created_at timestamptz NOT NULL DEFAULT now()", ddl)

    def test_ensure_creates_index_on_expires_at(self):
        sql = self._ensure_sql()
        self.assertIn("CREATE INDEX IF NOT EXISTS idx_line_dms_login_tickets_expires_at", sql)
        self.assertIn("ON line_dms_login_tickets (expires_at)", sql)

    def test_ensure_applies_tenant_rls(self):
        sql = self._ensure_sql()
        self.assertIn("ALTER TABLE line_dms_login_tickets ENABLE ROW LEVEL SECURITY", sql)
        self.assertIn("CREATE POLICY tenant_isolation ON line_dms_login_tickets", sql)


class ConsumeTicketTests(unittest.TestCase):
    def test_consume_once(self):
        """首次核销返回身份并删行,第二次必返 None。"""
        cur = FakeTicketCursor()
        with _patch(cur):
            out = lt.issue_login_ticket("t1", "u9")
            first = lt.consume_login_ticket(out["ticket"])
            second = lt.consume_login_ticket(out["ticket"])
        self.assertEqual(first, {"tenant_id": "t1", "user_id": "u9"})
        self.assertIsNone(second)
        self.assertEqual(cur.rows, {})

    def test_expired_returns_none(self):
        cur = FakeTicketCursor()
        with _patch(cur):
            out = lt.issue_login_ticket("t1", "u1", ttl_seconds=lt.MAX_TICKET_TTL_SECONDS)
            cur.advance(lt.MAX_TICKET_TTL_SECONDS + 1)
            self.assertIsNone(lt.consume_login_ticket(out["ticket"]))

    def test_dead_on_arrival_never_consumable(self):
        """负 TTL 夹到 0 → 出生即过期,核销必返 None。"""
        cur = FakeTicketCursor()
        with _patch(cur):
            out = lt.issue_login_ticket("t1", "u1", ttl_seconds=-1)
            self.assertIsNone(lt.consume_login_ticket(out["ticket"]))

    def test_issue_cleans_expired_rows(self):
        cur = FakeTicketCursor()
        with _patch(cur):
            old = lt.issue_login_ticket("t1", "u1", ttl_seconds=1)
            cur.advance(2)
            fresh = lt.issue_login_ticket("t1", "u2")
        self.assertNotIn(hashlib.sha256(old["ticket"].encode()).hexdigest(), cur.rows)
        self.assertIn(hashlib.sha256(fresh["ticket"].encode()).hexdigest(), cur.rows)

    def test_unknown_ticket_none(self):
        with _patch(FakeTicketCursor()):
            self.assertIsNone(lt.consume_login_ticket("never-issued"))

    def test_blank_skips_db(self):
        cur = FakeTicketCursor()
        with _patch(cur):
            self.assertIsNone(lt.consume_login_ticket(""))
            self.assertIsNone(lt.consume_login_ticket(None))
            self.assertIsNone(lt.consume_login_ticket("   "))
        self.assertEqual(cur.calls, [])

    def test_consume_is_atomic_delete_returning(self):
        """核销走单句 DELETE ... RETURNING(过期判断在 SQL 里),不先读后删。"""
        cur = FakeTicketCursor()
        with _patch(cur):
            out = lt.issue_login_ticket("t1", "u1")
            lt.consume_login_ticket(out["ticket"])
        sql = cur.all_sql()
        self.assertIn("DELETE FROM line_dms_login_tickets", sql)
        self.assertIn("RETURNING tenant_id, user_id", sql)
        self.assertIn("expires_at > now()", sql)
        self.assertNotIn("SELECT", sql)


if __name__ == "__main__":
    unittest.main()
