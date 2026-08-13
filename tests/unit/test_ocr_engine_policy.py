# -*- coding: utf-8 -*-
"""OCR 引擎策略层守门:mode 决策 + 请求级模型覆写 + 成本按实际模型计价。

纯逻辑,platform_settings 全 mock,不连 DB。fail-safe 是钱路要求:
配置读不到必须回落当下现役档(2026-07-22 起 economy),绝不因配置故障停摆或乱换档。
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
    def test_default_is_economy(self):
        with mock.patch.dict("os.environ", _ENV_CLEAR):
            self.assertEqual(ep.resolve_mode("invoice", config=ep.DEFAULT_CONFIG), "economy")

    def test_env_beats_config(self):
        with mock.patch.dict("os.environ", {**_ENV_CLEAR, "OCR_ENGINE_MODE": "economy"}):
            cfg = {**ep.DEFAULT_CONFIG, "mode": "selfhost"}
            self.assertEqual(ep.resolve_mode("invoice", config=cfg), "economy")

    def test_task_override_beats_global(self):
        with mock.patch.dict("os.environ", _ENV_CLEAR):
            cfg = {
                **ep.DEFAULT_CONFIG,
                "mode": "selfhost",
                "overrides_by_task": {"id_card": "economy"},
            }
            self.assertEqual(ep.resolve_mode("id_card", config=cfg), "economy")
            self.assertEqual(ep.resolve_mode("invoice", config=cfg), "selfhost")

    def test_direct35_context_leaves_env_alone(self):
        with mock.patch.dict("os.environ", _ENV_CLEAR):
            cfg = {**ep.DEFAULT_CONFIG, "mode": "direct35"}
            with mock.patch.object(ep, "load_config", return_value=cfg):
                with ep.engine_context("invoice") as mode:
                    self.assertEqual(mode, "direct35")
                    self.assertEqual(gemini_models.flash_lite(), "gemini-3.5-flash")

    def test_auto_resolves_by_plan(self):
        with mock.patch.dict("os.environ", _ENV_CLEAR):
            cfg = {
                **ep.DEFAULT_CONFIG,
                "mode": "auto",
                "defaults_by_plan": {"none": "economy", "L": "selfhost", "exempt": "selfhost"},
            }
            self.assertEqual(ep.resolve_mode("invoice", config=cfg), "economy")
            self.assertEqual(ep.resolve_mode("invoice", plan_code="L", config=cfg), "selfhost")
            self.assertEqual(ep.resolve_mode("invoice", is_exempt=True, config=cfg), "selfhost")

    def test_unsupported_task_falls_back_regardless_of_how_mode_was_chosen(self):
        # 能力盲区注册表是常驻绊线:登记的 (mode, task) 不管档怎么选上都回 fail-safe——
        # 功能不能被档位切坏。注册表当前为空,这里灌一条假登记验机制本身。
        with mock.patch.dict("os.environ", _ENV_CLEAR):
            with mock.patch.object(
                ep, "MODE_UNSUPPORTED_TASKS", {"qwen": frozenset({"vat_report"})}
            ):
                by_global = {**ep.DEFAULT_CONFIG, "mode": "qwen"}
                self.assertEqual(ep.resolve_mode("vat_report", config=by_global), "economy")
                self.assertEqual(ep.resolve_mode("invoice", config=by_global), "qwen")
                by_task = {**ep.DEFAULT_CONFIG, "overrides_by_task": {"vat_report": "qwen"}}
                self.assertEqual(ep.resolve_mode("vat_report", config=by_task), "economy")

    def test_vat_report_back_on_qwen_after_pdf_part_fix(self):
        # 2026-08-13 根因修复(http_common:PDF 逐页转图再进 image_url)后,
        # vat_report 车道重新接 qwen,不再被盲区注册表劫回现役档。
        with mock.patch.dict("os.environ", _ENV_CLEAR):
            cfg = {**ep.DEFAULT_CONFIG, "mode": "qwen"}
            self.assertEqual(ep.resolve_mode("vat_report", config=cfg), "qwen")

    def test_retired_account_key_ignored_on_load(self):
        # 账号灰度 2026-08-13 退役:存量配置里的 overrides_by_account 不炸、不生效,
        # 合并结果里没有这个键(写侧下次保存自然剥离,不跑迁移脚本)。
        legacy = {
            "mode": "economy",
            "overrides_by_task": {"bank_statement": "direct35"},
            "overrides_by_account": {"skin306152@gmail.com": "qwen"},
        }
        with mock.patch(
            "services.platform_settings.store.get_setting", return_value={"value": legacy}
        ):
            cfg = ep.load_config()
        self.assertNotIn("overrides_by_account", cfg)
        with mock.patch.dict("os.environ", _ENV_CLEAR):
            self.assertEqual(ep.resolve_mode("invoice", config=cfg), "economy")

    def test_invalid_mode_falls_back(self):
        with mock.patch.dict("os.environ", _ENV_CLEAR):
            cfg = {**ep.DEFAULT_CONFIG, "mode": "gpt99"}
            self.assertEqual(ep.resolve_mode("invoice", config=cfg), "economy")

    def test_direct35_is_passthrough_not_a_model_tier(self):
        # A 档的定义是「空覆写 = 跟 env 走」(c32f85f7 建档本意),不是某个模型的高精档。
        self.assertEqual(ep.MODE_MODEL_MAPS["direct35"], {})
        self.assertIn("direct35", ep.CONCRETE_MODES)

    def test_bank_statement_pinned_off_global_mode(self):
        # 银行不跟全局:真料实测断点 3.5=2 / 3.6=7 / 3.1-lite=40,长表不许落轻量档。
        with mock.patch.dict("os.environ", _ENV_CLEAR):
            for global_mode in ("economy", "selfhost"):
                cfg = {**ep.DEFAULT_CONFIG, "mode": global_mode}
                self.assertEqual(ep.resolve_mode("bank_statement", config=cfg), "direct35")
            self.assertEqual(ep.resolve_mode("invoice", config=cfg), "selfhost")

    def test_bank_reads_with_env_default_not_lite(self):
        with mock.patch.dict("os.environ", _ENV_CLEAR):
            with mock.patch.object(ep, "load_config", return_value=dict(ep.DEFAULT_CONFIG)):
                with ep.engine_context("bank_statement") as mode:
                    self.assertEqual(mode, "direct35")
                    self.assertEqual(gemini_models.flash_lite(), "gemini-3.5-flash")

    def test_load_config_failsafe_on_store_error(self):
        with mock.patch(
            "services.platform_settings.store.get_setting", side_effect=RuntimeError("db down")
        ):
            cfg = ep.load_config()
        self.assertEqual(cfg["mode"], "economy")


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

    def test_default_context_is_economy(self):
        with mock.patch.dict("os.environ", _ENV_CLEAR):
            with mock.patch.object(ep, "load_config", return_value=dict(ep.DEFAULT_CONFIG)):
                with ep.engine_context("invoice") as mode:
                    self.assertEqual(mode, "economy")
                    self.assertEqual(gemini_models.flash_lite(), "gemini-3.1-flash-lite")

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

    def test_qwen_pins_backend_and_leaves_gemini_tiers_alone(self):
        from services.ai_gateway import backends

        with mock.patch.dict("os.environ", _ENV_CLEAR):
            cfg = {**ep.DEFAULT_CONFIG, "mode": "qwen"}
            with mock.patch.object(ep, "load_config", return_value=cfg):
                with ep.engine_context("invoice") as mode:
                    self.assertEqual(mode, "qwen")
                    self.assertEqual(backends.override_backend(), "qwen")
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
        # economy 现役 L2 = 3.1-flash-lite,按其单价计($0.25/$1.50)不套高精档
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

    def test_qwen_arms_priced_apart(self):
        # 读取臂与升级臂差 60x/46x:两臂共用一个价就把 qwen 档的账算飞了
        with mock.patch.dict("os.environ", _ENV_CLEAR):
            thb = c._compute_total_cost(
                [
                    _page(
                        ["ID", "ID_ESC"],
                        l2i=1_000_000,
                        l2o=1_000_000,
                        l3i=1_000_000,
                        l3o=1_000_000,
                        l2_model="qwen3.7-flash",
                        l3_model="qwen3.8-max",
                    )
                ]
            )
        self.assertAlmostEqual(thb, (0.03 + 0.13 + 2.00 + 6.00) * 35.0, places=4)

    def test_qwen_transcription_model_priced(self):
        with mock.patch.dict("os.environ", _ENV_CLEAR):
            self.assertEqual(c.price_per_m_usd("qwen-vl-ocr-2025-11-20"), (0.072, 0.164))

    def test_missing_recorded_model_falls_back_to_env_tier(self):
        # 旧结果/直调层函数没记模型 → 按当前档位计(默认 3.5)
        with mock.patch.dict("os.environ", _ENV_CLEAR):
            thb = c._compute_total_cost([_page(["text", "L2"], l2i=1_000_000, l2o=1_000_000)])
        self.assertAlmostEqual(thb, (1.50 + 9.00) * 35.0, places=4)


if __name__ == "__main__":
    unittest.main(verbosity=2)
