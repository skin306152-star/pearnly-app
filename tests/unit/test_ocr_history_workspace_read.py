# -*- coding: utf-8 -*-
"""PO-4 守门:ocr_history 读侧按套账隔离。

证明:
  1. 给 workspace_client_id → 每个读 SQL 都带 workspace_client_id 过滤子句 + 参数;
  2. 不给(None)→ 旧行为(SQL 不含 workspace_client_id 过滤、不多塞参数);
  3. rollout-safe:过滤子句含 `IS NULL`(尚未归属套账的行保持可见,不丢)。

只验 SQL 拼接 + 参数,不触真库(mock get_cursor)。不用 pytest(见 memory)。
"""

import datetime as _dt
import unittest
from contextlib import contextmanager
from unittest import mock

from core import db  # noqa: F401 — 先全量初始化 db/dal_reexports,避免直引子模块的循环 import
from services.ocr_history import store as queries


class _CaptureCursor:
    """记录每次 execute 的 (sql, params);fetchone/fetchall 给可控返回。"""

    def __init__(self):
        self.calls = []
        self._count_then_rows = True

    def execute(self, sql, params=None):
        self.calls.append((sql, list(params) if params is not None else None))

    def fetchone(self):
        # list_ocr_history 先 COUNT;detail/pdf/hash/dup 取单行
        return {"c": 0, "id": "h1", "pdf_storage_path": None}

    def fetchall(self):
        return []

    @property
    def all_sql(self):
        return " ".join(sql for sql, _ in self.calls)

    @property
    def all_params(self):
        flat = []
        for _, p in self.calls:
            if p:
                flat.extend(p)
        return flat


@contextmanager
def _fake_cursor(cur):
    yield cur


def _run(fn, **kwargs):
    # B8 RLS:ocr_history 已 enroll · 读 DAL 走 get_cursor_rls · 同 patch 两游标。
    cur = _CaptureCursor()
    factory = lambda *a, **k: _fake_cursor(cur)  # noqa: E731
    with (
        mock.patch("core.db.get_cursor", factory),
        mock.patch("core.db.get_cursor_rls", factory),
    ):
        fn(**kwargs)
    return cur


class WorkspaceReadFilterTests(unittest.TestCase):
    def test_list_with_workspace_adds_filter_and_param(self):
        cur = _run(
            queries.list_ocr_history,
            user_id="u1",
            retention_days=90,
            tenant_id="t1",
            workspace_client_id=7,
        )
        self.assertIn("workspace_client_id", cur.all_sql)
        self.assertIn("IS NULL", cur.all_sql)  # rollout-safe
        self.assertIn(7, cur.all_params)

    def test_list_without_workspace_no_filter(self):
        cur = _run(
            queries.list_ocr_history,
            user_id="u1",
            retention_days=90,
            tenant_id="t1",
        )
        # 不传套账 → SQL 不含 workspace 过滤(向后兼容)
        self.assertNotIn("workspace_client_id = %s", cur.all_sql)

    def test_detail_with_workspace_adds_filter(self):
        cur = _run(
            queries.get_ocr_history_detail,
            user_id="u1",
            record_id="r1",
            tenant_id="t1",
            workspace_client_id=9,
        )
        self.assertIn("workspace_client_id = %s", cur.all_sql)
        self.assertIn(9, cur.all_params)

    def test_pdf_info_with_workspace_adds_filter(self):
        cur = _run(
            queries.get_history_pdf_info,
            user_id="u1",
            record_id="r1",
            tenant_id="t1",
            workspace_client_id=3,
        )
        self.assertIn("workspace_client_id = %s", cur.all_sql)
        self.assertIn(3, cur.all_params)

    def test_find_by_hash_with_workspace_adds_filter(self):
        cur = _run(
            queries.find_ocr_by_hash,
            user_id="u1",
            file_hash="abc",
            tenant_id="t1",
            workspace_client_id=5,
        )
        self.assertIn("workspace_client_id = %s", cur.all_sql)
        self.assertIn(5, cur.all_params)

    def test_check_duplicate_with_workspace_adds_filter(self):
        # 第 1 层(invoice_no 命中分支)带过滤
        cur = _run(
            queries.check_duplicate_invoice,
            user_id="u1",
            invoice_no="INV-1",
            invoice_date=_dt.date(2026, 5, 1),
            seller_name="S",
            total_amount=100.0,
            workspace_client_id=11,
        )
        self.assertIn("workspace_client_id = %s", cur.all_sql)
        self.assertIn(11, cur.all_params)

    def test_check_duplicate_without_workspace_no_filter(self):
        cur = _run(
            queries.check_duplicate_invoice,
            user_id="u1",
            invoice_no="INV-1",
            invoice_date=_dt.date(2026, 5, 1),
            seller_name="S",
            total_amount=100.0,
        )
        self.assertNotIn("workspace_client_id", cur.all_sql)


if __name__ == "__main__":
    unittest.main()
