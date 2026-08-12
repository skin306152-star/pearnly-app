# -*- coding: utf-8 -*-
"""services/ai_gateway/logging.py::log_call → ai_usage 落库接线契约。

锁定:① tenant/task/cost 等参数原样传给 log_ai_usage;② store 层抛异常不影响
log_call 正常返回(记账绝不能打断 AI 调用主路径);③ ai_usage_store 导入失败时同样不抛。
"""

import unittest
from unittest import mock

from services.ai_gateway import logging as ai_log
from services.ai_gateway import tasks as T
from services.cost.usage_context import usage_context


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


class AttributionWiringTests(unittest.TestCase):
    """归因上下文(入口/单据/页数)在落账点被读进 ai_usage —— 断了这根线,
    面板就只剩「未归因」一行,逐入口成本重新变成瞎子。"""

    def test_usage_context_flows_into_ai_usage(self):
        with mock.patch("services.cost.ai_usage_store.log_ai_usage") as m:
            with usage_context("bank_recon", doc_type="bank_statement", pages=18):
                ai_log.log_call(_result())
        kw = m.call_args.kwargs
        self.assertEqual(kw["entry_point"], "bank_recon")
        self.assertEqual(kw["doc_type"], "bank_statement")
        self.assertEqual(kw["pages"], 18)

    def test_pages_recorded_once_per_request(self):
        # 一份 18 页对账单会落多行(逐页/逐层各一次调用):页数只记第一行,
        # 否则 SUM(pages) 变 18×行数,每页成本被稀释成假的便宜
        with mock.patch("services.cost.ai_usage_store.log_ai_usage") as m:
            with usage_context("bank_recon", doc_type="bank_statement", pages=18):
                for _ in range(5):
                    ai_log.log_call(_result())
        pages = [c.kwargs["pages"] for c in m.call_args_list]
        self.assertEqual(pages, [18, None, None, None, None])
        # 入口/单据是每行都带的,分组不能漏
        self.assertTrue(all(c.kwargs["entry_point"] == "bank_recon" for c in m.call_args_list))

    def test_no_context_passes_none(self):
        with mock.patch("services.cost.ai_usage_store.log_ai_usage") as m:
            ai_log.log_call(_result())
        kw = m.call_args.kwargs
        self.assertIsNone(kw["entry_point"])
        self.assertIsNone(kw["doc_type"])
        self.assertIsNone(kw["pages"])

    def test_failed_write_restores_pages_for_next_row(self):
        # 第一行落账失败(store 返 False)→ 页数还回槽 → 第二行把分母补上
        with mock.patch(
            "services.cost.ai_usage_store.log_ai_usage", side_effect=[False, True]
        ) as m:
            with usage_context("bank_recon", doc_type="bank_statement", pages=18):
                ai_log.log_call(_result())
                ai_log.log_call(_result())
        self.assertEqual([c.kwargs["pages"] for c in m.call_args_list], [18, 18])


if __name__ == "__main__":
    unittest.main()
