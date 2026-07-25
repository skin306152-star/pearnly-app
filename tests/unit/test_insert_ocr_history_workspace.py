# -*- coding: utf-8 -*-
"""B1 相 1 守门:insert_ocr_history 兼容写入 workspace_client_id。

证明(非强制·带不上 NULL·不碰买方):
  1. 传合法 workspace_client_id → 写入 INSERT;
  2. 不传 → 仍按旧逻辑成功(workspace 列 NULL);
  3. workspace_client_id 与 client_id(买方)是不同列,互不影响;
  4. workspace 校验不过(非本租户)→ 写 NULL,不报错、不拦上传;
  5. posting_kind 原样透传(归一在 run_recognition_core,这层是纯 DAL)。

断言按**列名**定位参数(见 _insert_columns):早先按负下标锁位置,mutations.py 每加一列
(2026-07-25 加 posting_kind)全部断言整体位移一起变红。
"""

import re
import unittest
from contextlib import contextmanager
from unittest import mock

from core import db

# 列清单 + VALUES 占位符段:用来把位置参数按列名还原
_INSERT_RE = re.compile(
    r"INSERT INTO ocr_history\s*\((?P<cols>.*?)\)\s*VALUES\s*\((?P<vals>.*)\)\s*RETURNING",
    re.S,
)


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
    def insert_call(self):
        for sql, params in self.calls:
            if "INSERT INTO ocr_history" in sql:
                return sql, params
        return None


def _run_insert(cur, **kwargs):
    @contextmanager
    def _fake_get_cursor(*a, **k):
        yield cur

    with (
        mock.patch("core.db.get_cursor", _fake_get_cursor),
        mock.patch("core.db.get_cursor_rls", _fake_get_cursor),
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
    def _insert_columns(self, cur):
        """从 INSERT 语句解析列名顺序,和位置参数对上,返回 {列名: 实参}。"""
        call = cur.insert_call
        self.assertIsNotNone(call, "没抓到 INSERT INTO ocr_history")
        sql, params = call
        m = _INSERT_RE.search(sql)
        self.assertIsNotNone(m, "INSERT 语句的列清单 / VALUES 段没解析出来")
        columns = [c.strip() for c in m.group("cols").split(",") if c.strip()]
        # 列数 / 占位符数 / 实参数三者不等 → 按名字对齐本身就不成立,当场红,别静默错位
        self.assertEqual(len(columns), m.group("vals").count("%s"), "列数与 %s 占位符数不一致")
        self.assertEqual(len(columns), len(params), "列数与实参个数不一致")
        return dict(zip(columns, params))

    def test_pass_valid_workspace_is_written(self):
        cur = _FakeCursor(workspace_valid=True)
        hid = _run_insert(cur, workspace_client_id=7)
        self.assertEqual(hid, "hist-1")
        self.assertEqual(self._insert_columns(cur)["workspace_client_id"], 7)

    def test_no_workspace_still_succeeds_null(self):
        cur = _FakeCursor()
        hid = _run_insert(cur)  # 不传 workspace_client_id
        self.assertEqual(hid, "hist-1")  # 旧逻辑照常成功
        self.assertIsNone(self._insert_columns(cur)["workspace_client_id"])  # workspace 列 NULL

    def test_does_not_affect_buyer_client_id(self):
        cur = _FakeCursor(workspace_valid=True, client_valid=True)
        _run_insert(cur, client_id=55, workspace_client_id=7)
        cols = self._insert_columns(cur)
        # 买方与账套主体是两列,各归各位,互不串
        self.assertEqual(cols["client_id"], 55)
        self.assertEqual(cols["workspace_client_id"], 7)

    def test_invalid_workspace_writes_null_not_error(self):
        cur = _FakeCursor(workspace_valid=False)  # 非本租户 → 校验不过
        hid = _run_insert(cur, workspace_client_id=999)
        self.assertEqual(hid, "hist-1")  # 不报错、不拦上传
        self.assertIsNone(self._insert_columns(cur)["workspace_client_id"])  # 写 NULL

    def test_ai_raw_written_to_ai_raw_column(self):
        cur = _FakeCursor(workspace_valid=True)
        _run_insert(cur, ai_raw=[{"fields": {"invoice_number": "IV1"}}])
        # ai_raw 列 = 传入内容的 JSON 串(写一次留底)
        self.assertIn("IV1", self._insert_columns(cur)["ai_raw"])

    def test_ai_raw_defaults_to_pages(self):
        # 不传 ai_raw → 缺省取 pages(全 OCR 入口普适留底·非 NULL)
        cur = _FakeCursor()
        _run_insert(cur, pages=[{"fields": {"invoice_number": "IVX"}}])
        self.assertIn("IVX", self._insert_columns(cur)["ai_raw"])

    def test_staged_defaults_false(self):
        # staged 缺省 FALSE(存量 + LINE 等照旧即时可见)· 网页录入流才显式传 TRUE
        cur = _FakeCursor()
        _run_insert(cur)
        self.assertEqual(self._insert_columns(cur)["staged"], False)
        cur2 = _FakeCursor()
        _run_insert(cur2, staged=True)
        self.assertEqual(self._insert_columns(cur2)["staged"], True)

    def test_posting_kind_passed_through(self):
        # 这层不归一(DAL 依赖 ERP 适配器是层次倒挂)· 归一在 run_recognition_core 那唯一漏斗,
        # 脏值到不了这里;给什么存什么、不传存 NULL。
        cur = _FakeCursor()
        _run_insert(cur, posting_kind="stock")
        self.assertEqual(self._insert_columns(cur)["posting_kind"], "stock")

        cur_absent = _FakeCursor()
        _run_insert(cur_absent)  # 不传 → 没人声明过
        self.assertIsNone(self._insert_columns(cur_absent)["posting_kind"])


if __name__ == "__main__":
    unittest.main()
