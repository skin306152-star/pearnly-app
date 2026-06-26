# -*- coding: utf-8 -*-
"""express 端点单例守门 · create_erp_endpoint 复用 + ensure_single_express_endpoint 自愈。

锁住:向导竞态/并发重复 POST 不再建第二条 express;启动期清理已存在的重复空壳并建唯一索引。
用假游标截 SQL,不依赖真实 DB。
"""

import unittest
from unittest import mock

from core import db  # noqa: F401 · 避免 partial-init 循环
from services.erp import push_store as store
from services.erp import push_schema


class SeqCursor:
    """支持按调用顺序吐 fetchall / fetchone 的假游标。"""

    def __init__(self, fetchall_seq=None, fetchone_seq=None):
        self.calls = []
        self._fa = list(fetchall_seq or [])
        self._fo = list(fetchone_seq or [])

    def execute(self, sql, params=None):
        self.calls.append((sql, params))

    def fetchall(self):
        return self._fa.pop(0) if self._fa else []

    def fetchone(self):
        return self._fo.pop(0) if self._fo else None

    def all_sql(self):
        return " ".join(c[0] for c in self.calls)


def _cm(cur):
    class CM:
        def __enter__(self_):
            return cur

        def __exit__(self_, *a):
            return False

    return CM()


class CreateExpressReuseTests(unittest.TestCase):
    def _patch(self, cur):
        from tests.unit._cursor_patch import patch_both

        return patch_both(factory=lambda *a, **k: _cm(cur))

    def test_reuse_existing_express(self):
        cur = SeqCursor(fetchone_seq=[{"id": "ex-existing"}])
        with self._patch(cur):
            rid = store.create_erp_endpoint("u1", "Express", "express", {"method": "dbf"})
        self.assertEqual(rid, "ex-existing")
        self.assertNotIn("INSERT INTO erp_endpoints", cur.all_sql())

    def test_insert_when_no_express(self):
        cur = SeqCursor(fetchone_seq=[None, {"id": "ex-new"}])
        with self._patch(cur):
            rid = store.create_erp_endpoint("u1", "Express", "express", {"method": "dbf"})
        self.assertEqual(rid, "ex-new")
        self.assertIn("INSERT INTO erp_endpoints", cur.all_sql())

    def test_webhook_never_reuses(self):
        cur = SeqCursor(fetchone_seq=[{"id": "wh1"}])
        with self._patch(cur):
            rid = store.create_erp_endpoint("u1", "Hook", "webhook", {"url": "x"})
        self.assertEqual(rid, "wh1")
        self.assertIn("INSERT INTO erp_endpoints", cur.all_sql())
        self.assertNotIn("adapter = 'express'", cur.all_sql())


class EnsureSingleExpressTests(unittest.TestCase):
    def _patch(self, cur):
        return mock.patch.object(push_schema.db, "get_cursor", lambda *a, **k: _cm(cur))

    def test_deletes_empty_dup_and_builds_index(self):
        cur = SeqCursor(
            fetchall_seq=[
                [{"user_id": "u1"}],  # 有 >1 express 的用户
                [{"id": "keep", "n_logs": 1}, {"id": "dead", "n_logs": 0}],  # 排序后逐条
            ],
            fetchone_seq=[None],  # 复查:无残留
        )
        with self._patch(cur):
            push_schema.ensure_single_express_endpoint()
        deletes = [c for c in cur.calls if c[0].startswith("DELETE FROM erp_endpoints")]
        self.assertEqual(len(deletes), 1)
        self.assertEqual(deletes[0][1], ("dead",))
        self.assertIn("CREATE UNIQUE INDEX", cur.all_sql())

    def test_keeps_both_when_both_have_logs_and_skips_index(self):
        cur = SeqCursor(
            fetchall_seq=[
                [{"user_id": "u1"}],
                [{"id": "a", "n_logs": 2}, {"id": "b", "n_logs": 1}],
            ],
            fetchone_seq=[{"?column?": 1}],  # 复查:仍有残留
        )
        with self._patch(cur):
            push_schema.ensure_single_express_endpoint()
        self.assertNotIn("DELETE FROM erp_endpoints", cur.all_sql())
        self.assertNotIn("CREATE UNIQUE INDEX", cur.all_sql())


if __name__ == "__main__":
    unittest.main()
