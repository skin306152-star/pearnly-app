# -*- coding: utf-8 -*-
"""PO-6b/6c/6d 守门:对账任务/异步 job 按套账隔离(rollout-safe)。

证明:v2/vat 任务 create 写 workspace_client_id、list/get 给套账时带过滤;
recon_jobs enqueue 把 workspace_client_id 写进 job 行(异步 worker 据此取套账)。
只验 SQL/参数,不触真库。
"""

import unittest
from contextlib import contextmanager
from unittest import mock

from core import db  # noqa: F401 — 先初始化 dal
from services.recon import bank_recon_v2_store as v2
from services.recon import vat_recon_tasks_store as vat
from services.recon_jobs import store as jobs


class _Cur:
    def __init__(self):
        self.calls = []

    def execute(self, sql, params=None):
        self.calls.append((sql, list(params) if params is not None else None))

    def fetchone(self):
        return {"id": "x1", "n": 0}

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


def _patch(target, cur):
    return mock.patch(target, lambda *a, **k: _fake(cur))


class V2WorkspaceTests(unittest.TestCase):
    def test_create_writes_workspace(self):
        cur = _Cur()
        with _patch("core.db.get_cursor", cur):
            v2.create_bank_recon_v2_task(
                "u1",
                "t1",
                "K",
                "1010",
                "",
                "",
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                [],
                {},
                workspace_client_id=7,
            )
        self.assertIn("workspace_client_id", cur.sql)
        self.assertIn(7, cur.params)

    def test_list_filters_workspace(self):
        cur = _Cur()
        with _patch("core.db.get_cursor", cur):
            v2.list_bank_recon_v2_tasks("u1", tenant_id="t1", workspace_client_id=7)
        self.assertIn("workspace_client_id = %s OR workspace_client_id IS NULL", cur.sql)
        self.assertIn(7, cur.params)


class VatWorkspaceTests(unittest.TestCase):
    def test_create_writes_workspace(self):
        cur = _Cur()
        with _patch("core.db.get_cursor", cur):
            vat.create_vat_recon_task(
                "t1",
                "u1",
                "ACME",
                "2026-05",
                1,
                1,
                1,
                0,
                0,
                1.0,
                None,
                None,
                workspace_client_id=9,
            )
        self.assertIn("workspace_client_id", cur.sql)
        self.assertIn(9, cur.params)

    def test_list_filters_workspace(self):
        cur = _Cur()
        with _patch("core.db.get_cursor", cur):
            vat.list_vat_recon_tasks("t1", "u1", workspace_client_id=9)
        self.assertIn("workspace_client_id = %s OR workspace_client_id IS NULL", cur.sql)
        self.assertIn(9, cur.params)


class ReconJobsWorkspaceTests(unittest.TestCase):
    def test_enqueue_persists_workspace_on_row(self):
        cur = _Cur()
        # recon_jobs/store 用 `from core.db import get_cursor`(模块级引用)→ patch 其本地名
        with _patch("services.recon_jobs.store.get_cursor", cur):
            jobs.enqueue("bank", "u1", "t1", {"a": 1}, [], job_id="j1", workspace_client_id=5)
        self.assertIn("workspace_client_id", cur.sql)
        self.assertIn(5, cur.params)
        # 占位符与参数数量一致(防 INSERT 列/值错位)
        self.assertEqual(cur.calls[0][0].count("%s"), len(cur.calls[0][1]))


if __name__ == "__main__":
    unittest.main()
