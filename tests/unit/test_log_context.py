#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/unit/test_log_context.py · REFACTOR-WA-B6

域:services/observability/log_context.py · 全链路日志上下文。

锁定不变量:
  1. bind 仅覆盖显式传入的非 None 字段 · 其余保持原值。
  2. reset 精确还原 bind 设置的字段。
  3. current 反映当前快照 · 未绑定为 None。
  4. ContextFilter 把上下文塞进 LogRecord · 未绑定填 '-'(绝不漏字段)。
"""

from __future__ import annotations

import logging
import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.observability import log_context  # noqa: E402


class BindResetTest(unittest.TestCase):
    def tearDown(self) -> None:
        # 防 contextvar 在测试间泄漏
        for name in log_context.FIELDS:
            log_context._VARS[name].set(None)

    def test_bind_only_sets_passed_fields(self) -> None:
        log_context.bind(request_id="r1")
        snap = log_context.current()
        self.assertEqual(snap["request_id"], "r1")
        self.assertIsNone(snap["user_id"])
        self.assertIsNone(snap["tenant_id"])

    def test_bind_coerces_to_str(self) -> None:
        log_context.bind(tenant_id=12345)
        self.assertEqual(log_context.current()["tenant_id"], "12345")

    def test_reset_restores_previous(self) -> None:
        tokens = log_context.bind(request_id="outer")
        inner = log_context.bind(request_id="inner")
        self.assertEqual(log_context.current()["request_id"], "inner")
        log_context.reset(inner)
        self.assertEqual(log_context.current()["request_id"], "outer")
        log_context.reset(tokens)
        self.assertIsNone(log_context.current()["request_id"])


class ContextFilterTest(unittest.TestCase):
    def tearDown(self) -> None:
        for name in log_context.FIELDS:
            log_context._VARS[name].set(None)

    def _record(self) -> logging.LogRecord:
        return logging.LogRecord("t", logging.INFO, __file__, 1, "msg", None, None)

    def test_unbound_fields_filled_with_dash(self) -> None:
        rec = self._record()
        self.assertTrue(log_context.ContextFilter().filter(rec))
        for name in log_context.FIELDS:
            self.assertEqual(getattr(rec, name), "-")

    def test_bound_fields_propagate_to_record(self) -> None:
        log_context.bind(request_id="abc", user_id="u9", tenant_id="t3")
        rec = self._record()
        log_context.ContextFilter().filter(rec)
        self.assertEqual(rec.request_id, "abc")
        self.assertEqual(rec.user_id, "u9")
        self.assertEqual(rec.tenant_id, "t3")


if __name__ == "__main__":
    unittest.main()
