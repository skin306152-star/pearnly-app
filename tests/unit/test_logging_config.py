#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/unit/test_logging_config.py · REFACTOR-WA-B6

域:services/observability/logging_config.py · 结构化日志配置。

锁定不变量:
  1. JsonFormatter 输出合法单行 JSON · 含 level/logger/msg + 全部上下文字段。
  2. JsonFormatter 反映当前 contextvar(request_id 等随请求变化)。
  3. 异常记录带 exc 栈字段。
  4. configure_logging 只挂一个 handler 且带 ContextFilter(幂等 · 防双写)。
"""

from __future__ import annotations

import json
import logging
import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.observability import log_context  # noqa: E402
from services.observability.logging_config import (  # noqa: E402
    JsonFormatter,
    configure_logging,
)


def _record(msg="hello", exc_info=None) -> logging.LogRecord:
    rec = logging.LogRecord("svc", logging.INFO, __file__, 1, msg, None, exc_info)
    log_context.ContextFilter().filter(rec)  # 模拟 handler filter 注入上下文
    return rec


class JsonFormatterTest(unittest.TestCase):
    def tearDown(self) -> None:
        for name in log_context.FIELDS:
            log_context._VARS[name].set(None)

    def test_emits_valid_json_with_all_fields(self) -> None:
        out = JsonFormatter().format(_record("boot"))
        parsed = json.loads(out)
        self.assertEqual(parsed["level"], "INFO")
        self.assertEqual(parsed["logger"], "svc")
        self.assertEqual(parsed["msg"], "boot")
        for field in log_context.FIELDS:
            self.assertIn(field, parsed)
            self.assertEqual(parsed[field], "-")

    def test_reflects_bound_context(self) -> None:
        log_context.bind(request_id="req-42", tenant_id="t7")
        parsed = json.loads(JsonFormatter().format(_record()))
        self.assertEqual(parsed["request_id"], "req-42")
        self.assertEqual(parsed["tenant_id"], "t7")
        self.assertEqual(parsed["user_id"], "-")

    def test_includes_exception_stack(self) -> None:
        try:
            raise ValueError("boom")
        except ValueError:
            parsed = json.loads(JsonFormatter().format(_record("failed", sys.exc_info())))
        self.assertIn("exc", parsed)
        self.assertIn("ValueError", parsed["exc"])


class ConfigureLoggingTest(unittest.TestCase):
    def setUp(self) -> None:
        self._saved = logging.getLogger().handlers[:]

    def tearDown(self) -> None:
        root = logging.getLogger()
        root.handlers.clear()
        root.handlers.extend(self._saved)

    def test_single_handler_with_context_filter(self) -> None:
        configure_logging()
        configure_logging()  # 幂等:重复调用不应叠加 handler
        handlers = logging.getLogger().handlers
        self.assertEqual(len(handlers), 1)
        self.assertTrue(any(isinstance(f, log_context.ContextFilter) for f in handlers[0].filters))


if __name__ == "__main__":
    unittest.main()
