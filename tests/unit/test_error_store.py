#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/unit/test_error_store.py · REFACTOR-WA-B7

域:services/observability/error_store.py · 错误事件持久化。

锁定不变量:
  1. record_error 插入一条 · 带 B6 日志上下文(request_id/user_id/tenant_id)。
  2. record_error fail-open:DB 抛(表不存在/抖动)绝不冒泡(防拖垮异常处理)。
  3. list_recent_errors 返回行 · limit 收敛到 [1,500]。
  4. list_recent_errors fail-open:DB 抛 → 返回 []。

纯单测:mock db.get_cursor · 不连真库。
"""

from __future__ import annotations

import sys
import unittest
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import MagicMock, patch

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.observability import error_store, log_context  # noqa: E402


@contextmanager
def _cursor(fetch=None):
    cur = MagicMock()
    cur.fetchall.return_value = fetch or []
    yield cur


def _boom(*a, **k):
    raise RuntimeError('relation "error_events" does not exist')


class RecordErrorTest(unittest.TestCase):
    def tearDown(self) -> None:
        for name in log_context.FIELDS:
            log_context._VARS[name].set(None)

    def test_insert_carries_log_context(self) -> None:
        log_context.bind(request_id="r-1", user_id="u-2", tenant_id="t-3")
        captured = {}

        @contextmanager
        def _spy(*a, **k):
            cur = MagicMock()

            def _exec(sql, params):
                captured["sql"] = sql
                captured["params"] = params

            cur.execute.side_effect = _exec
            yield cur

        with patch.object(error_store.db, "get_cursor", _spy):
            error_store.record_error(message="boom", exc_type="ValueError", status_code=500)

        self.assertIn("INSERT INTO error_events", captured["sql"])
        p = captured["params"]
        self.assertIn("r-1", p)
        self.assertIn("u-2", p)
        self.assertIn("t-3", p)
        self.assertIn(500, p)

    def test_fail_open_on_db_error(self) -> None:
        with patch.object(error_store.db, "get_cursor", _boom):
            # 不抛即通过(异常处理器靠它 fail-open)
            error_store.record_error(message="x")


class ListRecentErrorsTest(unittest.TestCase):
    def test_returns_rows(self) -> None:
        rows = [{"id": 2, "message": "b"}, {"id": 1, "message": "a"}]
        with patch.object(error_store.db, "get_cursor", lambda *a, **k: _cursor(rows)):
            out = error_store.list_recent_errors(limit=10)
        self.assertEqual([r["id"] for r in out], [2, 1])

    def test_limit_clamped(self) -> None:
        captured = {}

        @contextmanager
        def _spy(*a, **k):
            cur = MagicMock()
            cur.execute.side_effect = lambda sql, params: captured.update(limit=params[0])
            cur.fetchall.return_value = []
            yield cur

        with patch.object(error_store.db, "get_cursor", _spy):
            error_store.list_recent_errors(limit=99999)
        self.assertEqual(captured["limit"], 500)

    def test_fail_open_returns_empty(self) -> None:
        with patch.object(error_store.db, "get_cursor", _boom):
            self.assertEqual(error_store.list_recent_errors(), [])


if __name__ == "__main__":
    unittest.main()
