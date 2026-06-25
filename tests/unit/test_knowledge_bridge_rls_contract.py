# -*- coding: utf-8 -*-
"""B8 RLS 契约:knowledge_bridge 去重/规则查询走带租户上下文的 RLS 游标(REFACTOR-B8 wave2)。

ocr_history / client_rules 是 wave3 表(尚未 enroll);本桥的查询先穿 tenant+user 上下文,
wave3 给这两张表 apply RLS 后隔离自动闭合。锁定:不回退裸 get_cursor。
"""

import unittest
from contextlib import contextmanager
from unittest import mock

from core import db  # noqa: F401
from services.exceptions import knowledge_bridge as kb


class _Cur:
    def execute(self, *a, **k):
        pass

    def fetchone(self):
        return None

    def fetchall(self):
        return []


def _capture():
    calls = []

    @contextmanager
    def fake(*args, **kwargs):
        calls.append(kwargs)
        yield _Cur()

    return calls, fake


def _no_bare():
    return mock.patch("core.db.get_cursor", side_effect=AssertionError("must use get_cursor_rls"))


class KnowledgeBridgeRlsContract(unittest.TestCase):
    def test_exact_dup_lookup_threads_context(self):
        calls, fake = _capture()
        find_exact, _ = kb.make_dedup_lookups(
            user_id="u1", tenant_id="ten-1", exclude_history_id="h0", seller_name="ACME"
        )
        with mock.patch("core.db.get_cursor_rls", fake), _no_bare():
            find_exact(None, "INV-1")
        self.assertEqual(calls[0].get("tenant_id"), "ten-1")
        self.assertEqual(calls[0].get("user_id"), "u1")

    def test_suspected_dup_lookup_threads_context(self):
        calls, fake = _capture()
        _, find_suspected = kb.make_dedup_lookups(
            user_id="u1", tenant_id="ten-1", exclude_history_id="h0", seller_name="ACME"
        )
        with mock.patch("core.db.get_cursor_rls", fake), _no_bare():
            find_suspected(None, 100.0, None)
        self.assertEqual(calls[0].get("tenant_id"), "ten-1")
        self.assertEqual(calls[0].get("user_id"), "u1")

    def test_resolve_workspace_threads_context(self):
        calls, fake = _capture()
        with mock.patch("core.db.get_cursor_rls", fake), _no_bare():
            kb._resolve_workspace_client_id("u1", "ten-1", "h1")
        self.assertEqual(calls[0].get("tenant_id"), "ten-1")
        self.assertEqual(calls[0].get("user_id"), "u1")


if __name__ == "__main__":
    unittest.main()
