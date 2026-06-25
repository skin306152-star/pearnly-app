# -*- coding: utf-8 -*-
"""B8 RLS 契约:会计 posting_failures 后台 worker 走正确的 RLS 游标(REFACTOR-B8)。

claim_due 跨租户认领 → 必须 bypass=True(否则 force RLS 下被 policy 过滤,队列瘫痪)。
retry_one 单行重过账 → 必须带该行 tenant + workspace 上下文(否则写 journal_* 被 WITH CHECK 拒)。
"""

import unittest
from contextlib import contextmanager
from unittest import mock

from services.accounting import posting_failures


class _Cur:
    def __init__(self):
        self.rows = []

    def execute(self, *a, **k):
        pass

    def fetchall(self):
        return self.rows


class PostingFailuresRlsContractTests(unittest.TestCase):
    def test_claim_due_uses_bypass_cursor(self):
        calls = {}

        @contextmanager
        def fake_rls(*args, **kwargs):
            calls.update(kwargs)
            yield _Cur()

        with (
            mock.patch("core.db.get_cursor_rls", fake_rls),
            mock.patch("core.db.get_cursor", side_effect=AssertionError("must use get_cursor_rls")),
        ):
            posting_failures.claim_due(limit=5)

        self.assertTrue(calls.get("bypass"), "claim_due 必须 bypass=True 跨租户认领")

    def test_retry_one_sets_row_tenant_context(self):
        calls = {}

        @contextmanager
        def fake_rls(*args, **kwargs):
            calls.update(kwargs)
            yield _Cur()

        row = {
            "id": 1,
            "tenant_id": "t-abc",
            "workspace_client_id": 7,
            "source_type": "purchase",
            "source_id": "9",
        }
        with (
            mock.patch("core.db.get_cursor_rls", fake_rls),
            mock.patch("core.db.get_cursor", side_effect=AssertionError("must use get_cursor_rls")),
            mock.patch("services.modules.store.is_enabled", return_value=False),
        ):
            posting_failures.retry_one(row)

        self.assertEqual(calls.get("tenant_id"), "t-abc")
        self.assertEqual(calls.get("workspace_client_id"), 7)
        self.assertNotIn("bypass", calls, "retry_one 不该 bypass · 须按行 tenant 隔离")


if __name__ == "__main__":
    unittest.main()
