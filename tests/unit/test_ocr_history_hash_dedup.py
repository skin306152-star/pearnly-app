# -*- coding: utf-8 -*-
"""文件哈希批量去重查询守门(services/ocr_history/hash_dedup.py · R2B)。

只验装配层:空哈希集早返 + 不触库、批量 SQL 用 ANY(%s) 且严格同账套过滤、行→dict 投影键
与单查一致、每 file_hash 一条(DISTINCT ON)。不触真库(mock get_cursor_rls)· 不用 pytest。
"""

import datetime as _dt
import unittest
from unittest import mock

from core import db  # noqa: F401 - 先初始化 db/dal,避免直引子模块的循环 import
from services.ocr_history import hash_dedup


class _Cur:
    def __init__(self, rows):
        self._rows = rows
        self.last_sql = None
        self.last_params = None

    def execute(self, sql, params=None):
        self.last_sql = sql
        self.last_params = list(params) if params is not None else None

    def fetchall(self):
        return self._rows


def _run(rows, **kwargs):
    cur = _Cur(rows)
    ctx = mock.MagicMock()
    ctx.__enter__.return_value = cur
    ctx.__exit__.return_value = False
    with mock.patch("core.db.get_cursor_rls", return_value=ctx):
        out = hash_dedup.find_ocr_by_hashes(**kwargs)
    return cur, out


def _row(file_hash):
    return {
        "id": "h-1",
        "filename": "f.pdf",
        "page_count": 1,
        "confidence": "high",
        "elapsed_ms": 10,
        "pages": [{"fields": {}}],
        "archive_name": None,
        "category_tag": None,
        "created_at": _dt.datetime(2026, 5, 1, 9, 0, 0),
        "file_hash": file_hash,
    }


class FindOcrByHashesTests(unittest.TestCase):
    def test_empty_hashes_short_circuits_without_db(self):
        with mock.patch("core.db.get_cursor_rls", side_effect=AssertionError("must not hit DB")):
            self.assertEqual(hash_dedup.find_ocr_by_hashes("u1", []), {})
            self.assertEqual(hash_dedup.find_ocr_by_hashes("u1", [None, ""]), {})

    def test_batch_any_query_strict_scoped_and_mapped(self):
        cur, out = _run(
            [_row("aaa"), _row("bbb")],
            user_id="u1",
            file_hashes=["aaa", "bbb"],
            tenant_id="t1",
            workspace_client_id=5,
            strict_workspace=True,
        )
        self.assertIn("file_hash = ANY(%s)", cur.last_sql)
        self.assertIn("workspace_client_id = %s", cur.last_sql)  # 严格同账套
        self.assertIn(["aaa", "bbb"], cur.last_params)
        self.assertIn(5, cur.last_params)
        # 每 hash 一条,投影键与单查一致(不含 file_hash)。
        self.assertEqual(set(out), {"aaa", "bbb"})
        self.assertEqual(out["aaa"]["filename"], "f.pdf")
        self.assertNotIn("file_hash", out["aaa"])

    def test_db_error_degrades_to_empty(self):
        with mock.patch("core.db.get_cursor_rls", side_effect=RuntimeError("db down")):
            self.assertEqual(hash_dedup.find_ocr_by_hashes("u1", ["x"], tenant_id="t1"), {})


if __name__ == "__main__":
    unittest.main()
