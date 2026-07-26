# -*- coding: utf-8 -*-
"""管家大脑层(services/steward/planner.py · B2-M1)。

覆盖硬闸机器面(闭集工具名 / args 清洗 / 出口护栏)+ fail-closed 降级(超时/异常/坏形状)。
零 DB 零网络:ask_model 是注入点,测试直接 patch(照 test_front_desk_interpret 先例)。
"""

from __future__ import annotations

import unittest
from unittest import mock

from services.ai_gateway.tasks import ProviderOutcome
from services.steward import planner, registry


def _outcome(data):
    return ProviderOutcome(ok=True, data=data, model="test-model")


class ParsePlanTests(unittest.TestCase):
    """枚举外工具名 / 编造结构 各被收敛成安全值,不悄悄采信。"""

    def test_out_of_enum_tool_becomes_out_of_scope(self):
        out = planner.parse_plan({"tool": "delete_everything", "args": {"x": 1}})
        self.assertEqual(out["tool"], registry.OUT_OF_SCOPE)
        self.assertEqual(out["args"], {})  # 超范围时参数一并丢,不留残料

    def test_known_tool_passes_through_with_clean_args(self):
        out = planner.parse_plan(
            {"tool": registry.CLIENT_STATUS, "args": {"client_name": " Sister ", "period": "6月"}}
        )
        self.assertEqual(out["tool"], registry.CLIENT_STATUS)
        self.assertEqual(out["args"], {"client_name": "Sister", "period": "6月"})

    def test_nested_and_empty_args_dropped(self):
        out = planner.parse_plan(
            {"tool": registry.WORKORDER_LIST, "args": {"a": {"n": 1}, "b": [], "c": "  ", "d": 3}}
        )
        self.assertEqual(out["args"], {"d": "3"})

    def test_non_dict_args_ignored(self):
        out = planner.parse_plan({"tool": registry.MATRIX_OVERVIEW, "args": "period=6"})
        self.assertEqual(out["args"], {})

    def test_insane_message_dropped_by_reply_guard(self):
        out = planner.parse_plan({"tool": registry.OUT_OF_SCOPE, "message": "1" * 40})
        self.assertEqual(out["message"], "")  # 复读循环不原样发给用户

    def test_sane_message_kept(self):
        out = planner.parse_plan({"tool": "nope", "message": "这个我做不了"})
        self.assertEqual(out["message"], "这个我做不了")

    def test_non_dict_is_bad_shape(self):
        self.assertTrue(planner.parse_plan(["not", "a", "dict"])["bad_shape"])

    def test_missing_fields_default_to_out_of_scope(self):
        out = planner.parse_plan({})
        self.assertEqual(out["tool"], registry.OUT_OF_SCOPE)
        self.assertFalse(out["bad_shape"])


class PromptTests(unittest.TestCase):
    def test_prompt_carries_closed_set_and_no_number_rule(self):
        prompt = planner.build_prompt("本期谁缺料")
        for name in registry.ALL_NAMES:
            self.assertIn(name, prompt)
        self.assertIn("out_of_scope", prompt)
        self.assertIn("不要在 message 里写数字", prompt)
        self.assertIn("本期谁缺料", prompt)

    def test_history_block_only_when_present(self):
        self.assertNotIn("最近几轮对话", planner.build_prompt("x"))
        with_history = planner.build_prompt("x", [{"role": "user", "text": "上一句"}])
        self.assertIn("上一句", with_history)


class DegradeTests(unittest.TestCase):
    """大脑不可用 → degraded 信封,绝不上抛(手点路径零共享故障面)。"""

    def _plan(self, ask):
        with mock.patch.object(planner, "ask_model", ask):
            return planner.plan("本期谁缺料", tenant_id="t-1", trace_id="s-1")

    def test_timeout_degrades(self):
        out = self._plan(lambda *a, **k: ProviderOutcome(ok=False, error_kind="timeout"))
        self.assertTrue(out["degraded"])
        self.assertEqual(out["reason"], "brain_timeout")
        self.assertEqual(out["tool"], registry.OUT_OF_SCOPE)

    def test_provider_error_degrades(self):
        out = self._plan(lambda *a, **k: ProviderOutcome(ok=False, error_kind="provider"))
        self.assertTrue(out["degraded"])
        self.assertEqual(out["reason"], "brain_error")

    def test_exception_degrades_not_raises(self):
        def boom(*a, **k):
            raise RuntimeError("network")

        out = self._plan(boom)
        self.assertTrue(out["degraded"])
        self.assertEqual(out["reason"], "brain_error")

    def test_bad_shape_degrades(self):
        out = self._plan(lambda *a, **k: _outcome("not json"))
        self.assertTrue(out["degraded"])
        self.assertEqual(out["reason"], "bad_output")

    def test_happy_path(self):
        out = self._plan(
            lambda *a, **k: _outcome({"tool": registry.MATRIX_OVERVIEW, "args": {"period": "6月"}})
        )
        self.assertFalse(out["degraded"])
        self.assertEqual(out["tool"], registry.MATRIX_OVERVIEW)
        self.assertEqual(out["args"], {"period": "6月"})


if __name__ == "__main__":
    unittest.main()
