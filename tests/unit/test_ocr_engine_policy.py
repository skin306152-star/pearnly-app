# -*- coding: utf-8 -*-
"""OCR 引擎策略层守门:mode 决策 + 请求级模型覆写 + 成本按实际模型计价。

纯逻辑,platform_settings 全 mock,不连 DB。fail-safe 是钱路要求:
配置读不到必须回落 direct35(现役稳定档),绝不因配置故障停摆或乱换档。
"""

from __future__ import annotations

import unittest
from types import SimpleNamespace
from unittest import mock

from services.ocr import cost as c
from services.ocr import engine_policy as ep
from services.ocr import gemini_models

_ENV_CLEAR = {
    "OCR_ENGINE_MODE": "",
    "OCR_FLASH_MODEL": "",
    "OCR_FLASHLITE_MODEL": "",
    "OCR_FALLBACK_MODEL": "",
    "OCR_ESCALATE_MODEL": "",
}


class ResolveModeTests(unittest.TestCase):
    def test_default_is_direct35(self):
        with mock.patch.dict("os.environ", _ENV_CLEAR):
            self.assertEqual(ep.resolve_mode("invoice", config=ep.DEFAULT_CONFIG), "direct35")

    def test_env_beats_config(self):
        with mock.patch.dict("os.environ", {**_ENV_CLEAR, "OCR_ENGINE_MODE": "economy"}):
            cfg = {**ep.DEFAULT_CONFIG, "mode": "direct35"}
            self.assertEqual(ep.resolve_mode("invoice", config=cfg), "economy")

    def test_task_override_beats_global(self):
        with mock.patch.dict("os.environ", _ENV_CLEAR):
            cfg = {
                **ep.DEFAULT_CONFIG,
                "mode": "economy",
                "overrides_by_task": {"id_card": "direct35"},
            }
            self.assertEqual(ep.resolve_mode("id_card", config=cfg), "direct35")
            self.assertEqual(ep.resolve_mode("invoice", config=cfg), "economy")

    def test_auto_resolves_by_plan(self):
        with mock.patch.dict("os.environ", _ENV_CLEAR):
            cfg = {
                **ep.DEFAULT_CONFIG,
                "mode": "auto",
                "defaults_by_plan": {"none": "economy", "L": "direct35", "exempt": "direct35"},
            }
            self.assertEqual(ep.resolve_mode("invoice", config=cfg), "economy")
            self.assertEqual(ep.resolve_mode("invoice", plan_code="L", config=cfg), "direct35")
            self.assertEqual(ep.resolve_mode("invoice", is_exempt=True, config=cfg), "direct35")

    def test_invalid_mode_falls_back(self):
        with mock.patch.dict("os.environ", _ENV_CLEAR):
            cfg = {**ep.DEFAULT_CONFIG, "mode": "gpt99"}
            self.assertEqual(ep.resolve_mode("invoice", config=cfg), "direct35")

    def test_load_config_failsafe_on_store_error(self):
        with mock.patch(
            "services.platform_settings.store.get_setting", side_effect=RuntimeError("db down")
        ):
            cfg = ep.load_config()
        self.assertEqual(cfg["mode"], "direct35")


class EngineContextTests(unittest.TestCase):
    def test_economy_overrides_models_and_restores(self):
        with mock.patch.dict("os.environ", _ENV_CLEAR):
            before = gemini_models.flash()
            cfg = {**ep.DEFAULT_CONFIG, "mode": "economy"}
            with mock.patch.object(ep, "load_config", return_value=cfg):
                with ep.engine_context("invoice") as mode:
                    self.assertEqual(mode, "economy")
                    self.assertEqual(ep.active_mode(), "economy")
                    # L2 读取臂 = 3.1-lite;兜底/升级臂 = 3.5;flash 档已弃,留 env 默认不覆写
                    self.assertEqual(gemini_models.flash_lite(), "gemini-3.1-flash-lite")
                    self.assertEqual(gemini_models.fallback(), "gemini-3.5-flash")
                    self.assertEqual(gemini_models.escalate(), "gemini-3.5-flash")
                    self.assertEqual(gemini_models.flash(), "gemini-3.5-flash")
            self.assertEqual(gemini_models.flash(), before)
            self.assertEqual(ep.active_mode(), "")

    def test_direct35_leaves_env_defaults(self):
        with mock.patch.dict("os.environ", _ENV_CLEAR):
            with mock.patch.object(ep, "load_config", return_value=dict(ep.DEFAULT_CONFIG)):
                with ep.engine_context("invoice") as mode:
                    self.assertEqual(mode, "direct35")
                    self.assertEqual(gemini_models.flash(), "gemini-3.5-flash")

    def test_selfhost_pins_backend_and_restores(self):
        from services.ai_gateway import backends

        with mock.patch.dict("os.environ", _ENV_CLEAR):
            self.assertIsNone(backends.override_backend())
            cfg = {**ep.DEFAULT_CONFIG, "mode": "selfhost"}
            with mock.patch.object(ep, "load_config", return_value=cfg):
                with ep.engine_context("invoice") as mode:
                    self.assertEqual(mode, "selfhost")
                    self.assertEqual(ep.active_mode(), "selfhost")
                    # 档钉后端 selfhost(直读/Vision shim 调 get_provider 才吃得到)
                    self.assertEqual(backends.override_backend(), "selfhost")
                    # 不动 Gemini 档位(空覆写)
                    self.assertEqual(gemini_models.flash(), "gemini-3.5-flash")
            self.assertIsNone(backends.override_backend())
            self.assertEqual(ep.active_mode(), "")

    def test_brain_not_affected_by_override(self):
        cfg = {**ep.DEFAULT_CONFIG, "mode": "economy"}
        with mock.patch.dict("os.environ", {**_ENV_CLEAR, "AGENT_BRAIN_MODEL": ""}):
            with mock.patch.object(ep, "load_config", return_value=cfg):
                with ep.engine_context("invoice"):
                    self.assertEqual(gemini_models.brain(), "gemini-2.5-flash")


def _page(chain, l2i=0, l2o=0, l3i=0, l3o=0, l2_model="", l3_model=""):
    return SimpleNamespace(
        layer_chain=chain,
        layer2_input_tokens=l2i,
        layer2_output_tokens=l2o,
        layer3_input_tokens=l3i,
        layer3_output_tokens=l3o,
        layer2_model=l2_model,
        layer3_model=l3_model,
    )


class CostByRecordedModelTests(unittest.TestCase):
    def test_l2_priced_by_recorded_model_not_env(self):
        # env 默认全 3.5,但页上记录实际用了 2.5-lite → 按 lite 单价计
        with mock.patch.dict("os.environ", _ENV_CLEAR):
            thb = c._compute_total_cost(
                [
                    _page(
                        ["text", "L2"],
                        l2i=1_000_000,
                        l2o=1_000_000,
                        l2_model="gemini-2.5-flash-lite",
                    )
                ]
            )
        self.assertAlmostEqual(thb, (0.10 + 0.40) * 35.0, places=4)

    def test_l2_economy_model_31_lite_priced(self):
        # economy 现役 L2 = 3.1-flash-lite,按其单价计($0.25/$1.50)不套 3.5
        with mock.patch.dict("os.environ", _ENV_CLEAR):
            thb = c._compute_total_cost(
                [
                    _page(
                        ["text", "L2"],
                        l2i=1_000_000,
                        l2o=1_000_000,
                        l2_model="gemini-3.1-flash-lite",
                    )
                ]
            )
        self.assertAlmostEqual(thb, (0.25 + 1.50) * 35.0, places=4)

    def test_l3_priced_by_recorded_model(self):
        with mock.patch.dict("os.environ", _ENV_CLEAR):
            thb = c._compute_total_cost(
                [
                    _page(
                        ["text", "L2", "L3"],
                        l3i=1_000_000,
                        l3o=1_000_000,
                        l2_model="gemini-2.5-flash-lite",
                        l3_model="gemini-3.5-flash",
                    )
                ]
            )
        self.assertAlmostEqual(thb, (1.50 + 9.00) * 35.0, places=4)

    def test_selfhost_model_zero_cost(self):
        # 自托管模型无 per-token 云成本 → 记 0(只付电费,不进此观测账本)
        with mock.patch.dict(
            "os.environ", {**_ENV_CLEAR, "SELFHOST_OCR_MODEL": "google/gemma-4-27b"}
        ):
            thb = c._compute_total_cost(
                [_page(["ID"], l2i=1_000_000, l2o=1_000_000, l2_model="google/gemma-4-27b")]
            )
        self.assertEqual(thb, 0.0)

    def test_missing_recorded_model_falls_back_to_env_tier(self):
        # 旧结果/直调层函数没记模型 → 按当前档位计(默认 3.5)
        with mock.patch.dict("os.environ", _ENV_CLEAR):
            thb = c._compute_total_cost([_page(["text", "L2"], l2i=1_000_000, l2o=1_000_000)])
        self.assertAlmostEqual(thb, (1.50 + 9.00) * 35.0, places=4)


if __name__ == "__main__":
    unittest.main(verbosity=2)
