# -*- coding: utf-8 -*-
"""services/ai_gateway/logging.py::log_call → ai_usage 落库接线契约。

锁定:① tenant/task/cost 等参数原样传给 log_ai_usage;② store 层抛异常不影响
log_call 正常返回(记账绝不能打断 AI 调用主路径);③ ai_usage_store 导入失败时同样不抛。
"""

import unittest
from unittest import mock

from services.ai_gateway import logging as ai_log
from services.ai_gateway import tasks as T


def _result(**overrides):
    kw = dict(
        ok=True,
        task="line_text_understand",
        schema_version="1",
        data={"x": 1},
        provider="fake",
        model="fake-model",
        error_kind=None,
        latency_ms=88,
        input_tokens=10,
        output_tokens=4,
        cost_thb=0.5,
    )
    kw.update(overrides)
    return T.AiResult(**kw)


class RecordUsageWiringTests(unittest.TestCase):
    def test_forwards_params_to_ai_usage_store(self):
        with mock.patch("services.cost.ai_usage_store.log_ai_usage") as m:
            ai_log.log_call(_result(), tenant_id="T1", user_id="U1", trace_id="TR1", text="secret")
        m.assert_called_once()
        kw = m.call_args.kwargs
        self.assertEqual(kw["tenant_id"], "T1")
        self.assertEqual(kw["user_id"], "U1")
        self.assertEqual(kw["trace_id"], "TR1")
        self.assertEqual(kw["task"], "line_text_understand")
        self.assertEqual(kw["model"], "fake-model")
        self.assertEqual(kw["provider"], "fake")
        self.assertEqual(kw["cost_thb"], 0.5)
        self.assertEqual(kw["status"], "ok")

    def test_error_status_mapped(self):
        with mock.patch("services.cost.ai_usage_store.log_ai_usage") as m:
            ai_log.log_call(_result(ok=False, error_kind="timeout"))
        self.assertEqual(m.call_args.kwargs["status"], "error")
        self.assertEqual(m.call_args.kwargs["error_kind"], "timeout")

    def test_store_exception_does_not_break_log_call(self):
        with mock.patch(
            "services.cost.ai_usage_store.log_ai_usage", side_effect=RuntimeError("db down")
        ):
            ai_log.log_call(_result())  # 不抛即通过

    def test_import_failure_does_not_break_log_call(self):
        with mock.patch.dict("sys.modules", {"services.cost.ai_usage_store": None}):
            ai_log.log_call(_result())  # 模块导入失败也不抛


if __name__ == "__main__":
    unittest.main()
