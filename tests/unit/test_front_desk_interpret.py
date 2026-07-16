# -*- coding: utf-8 -*-
"""前门大脑解析实装(services/front_desk/interpret.py · FD-0b)。

覆盖硬闸机器面(闭集意图/引用校验/期间规范/坏形状降级)+ fail-closed 降级路径(超时/异常/
闸关 → degraded)。零 DB 零网络:ask_model / fetch_clients 是注入点,测试直接 patch。
真调一次(OpenRouter)与 ai_usage 落库属人工验收,不进 CI(见交付报告)。
"""

from __future__ import annotations

import unittest
from datetime import date
from unittest import mock

from services.ai_gateway.tasks import ProviderOutcome
from services.front_desk import interpret

_TODAY = date(2026, 7, 16)
_CLIENTS = [{"id": "42", "name": "Sister Makeup"}, {"id": "7", "name": "62AHATAI"}]
_KNOWN_IDS = {"42", "7"}
_CLOSED = ("monthly_vat", "bank_match", "digitize", interpret.UNSUPPORTED)


def _outcome(data):
    return ProviderOutcome(ok=True, data=data, model="test-model")


class ParseOutputMechanicalTests(unittest.TestCase):
    """§验收②:枚举外意图 / 编造客户 id / 缺字段 各被拒(收敛成安全值,不采信编造)。"""

    def _parse(self, data):
        return interpret.parse_output(
            data, closed_intents=_CLOSED, known_ids=_KNOWN_IDS, today=_TODAY
        )

    def test_out_of_enum_intent_becomes_unsupported(self):
        out = self._parse({"intent": "file_annual_pnd50", "client_id": "42"})
        self.assertEqual(out["intent"], interpret.UNSUPPORTED)

    def test_fabricated_client_id_is_dropped(self):
        out = self._parse({"intent": "monthly_vat", "client_id": "99999"})
        self.assertEqual(out["intent"], "monthly_vat")
        self.assertIsNone(out["client_id"])  # 不在名录 → 置空(账套红线)

    def test_missing_fields_all_default_no_fabrication(self):
        out = self._parse({})
        self.assertEqual(out["intent"], interpret.UNSUPPORTED)
        self.assertIsNone(out["client_id"])
        self.assertIsNone(out["period"])
        self.assertFalse(out["bad_shape"])

    def test_valid_output_passes_through(self):
        out = self._parse({"intent": "bank_match", "client_id": "7", "period": "มิ.ย.69"})
        self.assertEqual(out["intent"], "bank_match")
        self.assertEqual(out["client_id"], "7")
        self.assertEqual(out["period"], "2026-06")

    def test_non_dict_is_bad_shape(self):
        out = self._parse(["not", "a", "dict"])
        self.assertTrue(out["bad_shape"])
        self.assertEqual(out["intent"], interpret.UNSUPPORTED)

    def test_workspace_client_id_alias_accepted(self):
        out = self._parse({"intent": "monthly_vat", "workspace_client_id": 42})
        self.assertEqual(out["client_id"], "42")


class ParsePeriodHintTests(unittest.TestCase):
    def test_buddhist_era_abbrev(self):
        self.assertEqual(interpret.parse_period_hint("ก.ค.69", _TODAY), "2026-07")

    def test_relative_and_bare_month(self):
        self.assertEqual(interpret.parse_period_hint("上个月", _TODAY), "2026-06")
        self.assertEqual(interpret.parse_period_hint("June", _TODAY), "2026-06")

    def test_iso_and_buddhist_iso(self):
        self.assertEqual(interpret.parse_period_hint("2026-05", _TODAY), "2026-05")
        self.assertEqual(interpret.parse_period_hint("2569-05", _TODAY), "2026-05")

    def test_unparseable_returns_none(self):
        self.assertIsNone(interpret.parse_period_hint("this period", _TODAY))
        self.assertIsNone(interpret.parse_period_hint(None, _TODAY))


class BuildPromptTests(unittest.TestCase):
    def test_prompt_carries_hard_rules_and_roster(self):
        p = interpret.build_prompt("ทำ vat", _CLIENTS, _CLOSED)
        self.assertIn("unsupported", p)
        self.assertIn("严禁编造", p)
        self.assertIn("42: Sister Makeup", p)
        self.assertIn("ทำ vat", p)

    def test_empty_roster_states_no_candidates(self):
        p = interpret.build_prompt("hi", [], _CLOSED)
        self.assertIn("client_id 一律 null", p)


class InterpretUtteranceTests(unittest.TestCase):
    """判卷 CLI 入口:显式名录 → {intent, client_id, period}。ask_model 注入,零真调。"""

    def _run(self, data):
        with mock.patch.object(interpret, "ask_model", return_value=_outcome(data)):
            return interpret.interpret_utterance(
                "ทำ vat ให้ SM มิ.ย.69",
                known_clients=_CLIENTS,
                closed_intents=_CLOSED,
                trace_id="exam:1",
                today=_TODAY,
            )

    def test_valid_suggestion(self):
        out = self._run({"intent": "monthly_vat", "client_id": "42", "period": "มิ.ย.69"})
        self.assertEqual(out, {"intent": "monthly_vat", "client_id": "42", "period": "2026-06"})

    def test_fabricated_client_dropped(self):
        out = self._run({"intent": "monthly_vat", "client_id": "does-not-exist"})
        self.assertIsNone(out["client_id"])

    def test_shape_is_exactly_three_keys(self):
        out = self._run({"intent": "unsupported"})
        self.assertEqual(set(out), {"intent", "client_id", "period"})


class InterpretRouteEnvelopeTests(unittest.TestCase):
    """路由入口:自取名录 → 降级信封。fetch_clients / ask_model 注入。"""

    def _interpret(self, data, clients=_CLIENTS):
        with (
            mock.patch.object(interpret, "fetch_clients", return_value=clients),
            mock.patch.object(
                interpret,
                "feature_flags",
                **{"pearnly_ai_front_desk_enabled_for.return_value": True},
            ),
            mock.patch.object(interpret, "ask_model", return_value=_outcome(data)),
        ):
            return interpret.interpret("ทำ vat", tenant_id="t-1", contract_id="c-1")

    def test_happy_path_maps_client_to_int(self):
        env = self._interpret({"intent": "monthly_vat", "client_id": "42", "period": "มิ.ย.69"})
        self.assertFalse(env["degraded"])
        self.assertEqual(env["intent"], "monthly_vat")
        self.assertEqual(env["client_suggestion"], 42)  # 字符串折回 workspace_client_id int
        self.assertEqual(env["period"], "2026-06")

    def test_unsupported_is_not_degraded(self):
        env = self._interpret({"intent": "unsupported"})
        self.assertFalse(env["degraded"])  # 诚实拒绝走 intent 字段,不是降级
        self.assertEqual(env["intent"], "unsupported")

    def test_envelope_shape_stable(self):
        env = self._interpret({"intent": "monthly_vat", "client_id": "42"})
        self.assertEqual(set(env), {"degraded", "intent", "client_suggestion", "period", "reason"})


class DegradePathTests(unittest.TestCase):
    """§验收③:超时/异常/闸关 → degraded=True。大脑故障被吞,绝不上抛(零共享故障面)。"""

    def test_timeout_degrades(self):
        to = ProviderOutcome(ok=False, error_kind="timeout", model="m")
        with (
            mock.patch.object(interpret, "fetch_clients", return_value=_CLIENTS),
            mock.patch.object(
                interpret,
                "feature_flags",
                **{"pearnly_ai_front_desk_enabled_for.return_value": True},
            ),
            mock.patch.object(interpret, "ask_model", return_value=to),
        ):
            env = interpret.interpret("x", tenant_id="t-1", contract_id="c-1")
        self.assertTrue(env["degraded"])
        self.assertEqual(env["reason"], interpret.DEGRADED_TIMEOUT)
        self.assertIsNone(env["intent"])
        self.assertIsNone(env["client_suggestion"])

    def test_brain_exception_is_contained(self):
        # ask_model 直接抛 → interpret 吞成 degraded,绝不冒泡(手动开单端点因此零共享故障面)
        with (
            mock.patch.object(interpret, "fetch_clients", return_value=_CLIENTS),
            mock.patch.object(
                interpret,
                "feature_flags",
                **{"pearnly_ai_front_desk_enabled_for.return_value": True},
            ),
            mock.patch.object(interpret, "ask_model", side_effect=RuntimeError("boom")),
        ):
            env = interpret.interpret("x", tenant_id="t-1", contract_id="c-1")
        self.assertTrue(env["degraded"])
        self.assertEqual(env["reason"], interpret.DEGRADED_BRAIN_ERROR)

    def test_client_fetch_failure_is_contained(self):
        # 名录读取炸(前置步骤)也只降级不上抛——证明大脑车道任何环节都不毒化请求
        with (
            mock.patch.object(interpret, "fetch_clients", side_effect=RuntimeError("db down")),
            mock.patch.object(
                interpret,
                "feature_flags",
                **{"pearnly_ai_front_desk_enabled_for.return_value": True},
            ),
        ):
            env = interpret.interpret("x", tenant_id="t-1", contract_id="c-1")
        self.assertTrue(env["degraded"])

    def test_flag_off_degrades_without_calling_brain(self):
        ask = mock.Mock()
        with (
            mock.patch.object(
                interpret,
                "feature_flags",
                **{"pearnly_ai_front_desk_enabled_for.return_value": False},
            ),
            mock.patch.object(interpret, "ask_model", ask),
        ):
            env = interpret.interpret("x", tenant_id="t-1", contract_id="c-1")
        self.assertTrue(env["degraded"])
        self.assertEqual(env["reason"], interpret.DEGRADED_FLAG_OFF)
        ask.assert_not_called()

    def test_bad_output_degrades(self):
        with (
            mock.patch.object(interpret, "fetch_clients", return_value=_CLIENTS),
            mock.patch.object(
                interpret,
                "feature_flags",
                **{"pearnly_ai_front_desk_enabled_for.return_value": True},
            ),
            mock.patch.object(interpret, "ask_model", return_value=_outcome("not-json-object")),
        ):
            env = interpret.interpret("x", tenant_id="t-1", contract_id="c-1")
        self.assertTrue(env["degraded"])
        self.assertEqual(env["reason"], interpret.DEGRADED_BAD_OUTPUT)


if __name__ == "__main__":
    unittest.main(verbosity=2)
