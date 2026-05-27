# -*- coding: utf-8 -*-
"""B1 相 1 守门:insert_ocr_history 兼容写入 workspace_client_id。

证明(非强制·带不上 NULL·不碰买方):
  1. 传合法 workspace_client_id → 写入 INSERT;
  2. 不传 → 仍按旧逻辑成功(workspace 列 NULL);
  3. workspace_client_id 与 client_id(买方)是不同列,互不影响;
  4. workspace 校验不过(非本租户)→ 写 NULL,不报错、不拦上传。
"""

import unittest
from contextlib import contextmanager
from unittest import mock

import db


class _FakeCursor:
    def __init__(self, workspace_valid=True, client_valid=True):
        self.calls = []
        self._last_sql = ""
        self.workspace_valid = workspace_valid
        self.client_valid = client_valid

    def execute(self, sql, params=None):
        self.calls.append((sql, params))
        self._last_sql = sql

    def fetchone(self):
        s = self._last_sql
        if "INSERT INTO ocr_history" in s:
            return {"id": "hist-1"}
        if "FROM workspace_clients" in s:
            return {"id": 1} if self.workspace_valid else None
        if "FROM clients" in s:
            return {"id": 1} if self.client_valid else None
        return None

    @property
    def insert_params(self):
        for sql, params in self.calls:
            if "INSERT INTO ocr_history" in sql:
                return params
        return None


def _run_insert(cur, **kwargs):
    @contextmanager
    def _fake_get_cursor(commit=False):
        yield cur

    with (
        mock.patch("db.get_cursor", _fake_get_cursor),
        mock.patch(
            "services.ocr_history.store._extract_summary_fields",  # REFACTOR-B2 · 随 insert 搬到 store
            return_value={
                "invoice_no": "INV1",
                "invoice_date": "2026-05-26",
                "seller_name": "S",
                "total_amount": "1",
            },
        ),
    ):
        base = dict(
            user_id="u1",
            filename="f.pdf",
            page_count=1,
            pages=[{}],
            confidence="high",
            elapsed_ms=10,
            tenant_id="t1",
        )
        base.update(kwargs)
        return db.insert_ocr_history(**base)


class InsertWorkspaceTests(unittest.TestCase):
    def test_pass_valid_workspace_is_written(self):
        cur = _FakeCursor(workspace_valid=True)
        hid = _run_insert(cur, workspace_client_id=7)
        self.assertEqual(hid, "hist-1")
        # 约定:INSERT tuple 末位=safe_workspace_client_id,倒二=safe_client_id
        self.assertEqual(cur.insert_params[-1], 7)

    def test_no_workspace_still_succeeds_null(self):
        cur = _FakeCursor()
        hid = _run_insert(cur)  # 不传 workspace_client_id
        self.assertEqual(hid, "hist-1")  # 旧逻辑照常成功
        self.assertIsNone(cur.insert_params[-1])  # workspace 列 NULL

    def test_does_not_affect_buyer_client_id(self):
        cur = _FakeCursor(workspace_valid=True, client_valid=True)
        _run_insert(cur, client_id=55, workspace_client_id=7)
        # 买方=倒二位=55,workspace=末位=7,互不串
        self.assertEqual(cur.insert_params[-2], 55)
        self.assertEqual(cur.insert_params[-1], 7)

    def test_invalid_workspace_writes_null_not_error(self):
        cur = _FakeCursor(workspace_valid=False)  # 非本租户 → 校验不过
        hid = _run_insert(cur, workspace_client_id=999)
        self.assertEqual(hid, "hist-1")  # 不报错、不拦上传
        self.assertIsNone(cur.insert_params[-1])  # 写 NULL


if __name__ == "__main__":
    unittest.main()
