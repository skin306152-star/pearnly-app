# -*- coding: utf-8 -*-
"""PO-6a 守门:银行对账 v1 会话按套账隔离(rollout-safe)。

证明:给 workspace_client_id → 写入/读路径带套账过滤(含 IS NULL 未归属行);
不给(None)→ 旧行为(SQL 不含套账过滤)。只验 SQL/参数,不触真库。
"""

import unittest
from contextlib import contextmanager
from unittest import mock

from core import db  # noqa: F401 — 先初始化 dal,避免直引子模块循环 import
from services.recon import bank_recon_v1_store as store


class _Cur:
    def __init__(self):
        self.calls = []

    def execute(self, sql, params=None):
        self.calls.append((sql, list(params) if params is not None else None))

    def fetchone(self):
        return {"id": "s1", "user_id": "u1"}

    def fetchall(self):
        return []

    @property
    def sql(self):
        return " ".join(s for s, _ in self.calls)

    @property
    def params(self):
        out = []
        for _, p in self.calls:
            if p:
                out.extend(p)
        return out


@contextmanager
def _fake(cur):
    yield cur


def _run(fn, **kw):
    cur = _Cur()
    # B8 RLS:bank_recon store 改走 get_cursor_rls(穿 user/tenant 上下文)· 同 patch 两游标
    cm = lambda *a, **k: _fake(cur)  # noqa: E731
    with mock.patch("core.db.get_cursor", cm), mock.patch("core.db.get_cursor_rls", cm):
        fn(**kw)
    return cur


class BankReconV1WorkspaceTests(unittest.TestCase):
    def test_create_writes_workspace(self):
        cur = _run(
            store.create_bank_recon_session,
            user_id="u1",
            bank_code="KBANK",
            filename="f.pdf",
            pages=1,
            workspace_client_id=7,
        )
        self.assertIn("workspace_client_id", cur.sql)
        self.assertIn(7, cur.params)

    def test_list_filters_by_workspace(self):
        cur = _run(store.list_bank_recon_sessions, user_id="u1", workspace_client_id=7)
        self.assertIn("workspace_client_id = %s OR workspace_client_id IS NULL", cur.sql)
        self.assertIn(7, cur.params)

    def test_list_without_workspace_no_filter(self):
        cur = _run(store.list_bank_recon_sessions, user_id="u1")
        self.assertNotIn("workspace_client_id = %s", cur.sql)

    def test_get_filters_by_workspace(self):
        cur = _run(
            store.get_bank_recon_session, user_id="u1", session_id="s1", workspace_client_id=3
        )
        self.assertIn("workspace_client_id = %s OR workspace_client_id IS NULL", cur.sql)
        self.assertIn(3, cur.params)

    def test_delete_filters_by_workspace(self):
        cur = _run(
            store.delete_bank_recon_session, user_id="u1", session_id="s1", workspace_client_id=5
        )
        self.assertIn("workspace_client_id = %s OR workspace_client_id IS NULL", cur.sql)
        self.assertIn(5, cur.params)


if __name__ == "__main__":
    unittest.main()
