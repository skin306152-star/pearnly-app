# -*- coding: utf-8 -*-
"""模型路由总表契约:全车道(大脑/OCR 两档/embedding)最终模型+区域逐行锁死。

治"改 OCR 把大脑搞坏"这类连坐:区域路由按模型名前缀生效(vertex),车道却按业务划分。
任何改动牵动别的车道路由 → 本套断言红;有意改路由必须同 PR 更新 EXPECTED_DEFAULT_ROUTES。

env 清场必须真删除键而不是设空串:OCR_FALLBACK_MODEL="" 是合法语义(关闭兜底),
设空串会把"默认态"测成"兜底关闭态"。
"""

from __future__ import annotations

import os
import unittest
from contextlib import contextmanager
from unittest import mock

from services.ai_gateway import backends
from services.ai_gateway import routing_matrix as rm
from services.ocr import engine_policy as ep


@contextmanager
def scrubbed_env(**extra):
    """ROUTE_ENV_VARS 全删除(extra 指定的除外);patch.dict 退出时整体还原。"""
    with mock.patch.dict("os.environ", extra):
        for v in rm.ROUTE_ENV_VARS:
            if v not in extra:
                os.environ.pop(v, None)
        yield


class RoutingMatrixContractTests(unittest.TestCase):
    def test_default_routes_match_declared_table(self):
        # 全表逐行相等:车道增删、模型变更、区域漂移任一都会在这炸出来
        with scrubbed_env():
            self.assertEqual(dict(rm.resolve_routes()), rm.EXPECTED_DEFAULT_ROUTES)

    def test_default_backend_is_declared(self):
        with scrubbed_env():
            self.assertEqual(backends.active_backend(), rm.DEFAULT_BACKEND)

    def test_ocr_model_env_knobs_leave_brain_untouched(self):
        with scrubbed_env(
            OCR_FLASH_MODEL="gemini-9.9-test",
            OCR_FLASHLITE_MODEL="gemini-9.9-test",
            OCR_FALLBACK_MODEL="gemini-9.9-test",
            OCR_ESCALATE_MODEL="gemini-9.9-test",
        ):
            routes = rm.resolve_routes()
        self.assertEqual(routes["agent.brain"], rm.EXPECTED_DEFAULT_ROUTES["agent.brain"])

    def test_taxops_brain_model_env_moves_only_verdict_lane(self):
        # 工单大脑车道独立旋钮:改它不许连坐对话大脑/OCR 任何档,反向亦然
        with scrubbed_env(TAXOPS_BRAIN_MODEL="gpt-9.9-test"):
            diff = rm.diff_from_defaults(rm.resolve_routes())
        self.assertEqual(set(diff), {"taxops.verdict"})
        exp, act = diff["taxops.verdict"]
        self.assertEqual(act.model, "gpt-9.9-test")
        self.assertEqual(act.backend, "openai")
        self.assertEqual(exp.backend, "openai")

    def test_agent_brain_env_leaves_taxops_verdict_untouched(self):
        with scrubbed_env(AGENT_BRAIN_MODEL="gemini-9.9-test"):
            routes = rm.resolve_routes()
        self.assertEqual(routes["taxops.verdict"], rm.EXPECTED_DEFAULT_ROUTES["taxops.verdict"])

    def test_taxops_intent_model_env_moves_only_intent_lane(self):
        # 前门意图车道独立旋钮:改它只动 taxops.intent,不许连坐裁决/对话/OCR 任何档
        with scrubbed_env(TAXOPS_INTENT_MODEL="gpt-9.9-test"):
            diff = rm.diff_from_defaults(rm.resolve_routes())
        self.assertEqual(set(diff), {"taxops.intent"})
        exp, act = diff["taxops.intent"]
        self.assertEqual(act.model, "gpt-9.9-test")
        self.assertEqual(act.backend, "openai")
        self.assertEqual(exp.backend, "openai")

    def test_verdict_and_agent_env_leave_taxops_intent_untouched(self):
        # 反向隔离:改裁决大脑档 / 对话大脑档都不许挪前门意图车道
        with scrubbed_env(TAXOPS_BRAIN_MODEL="gpt-9.9-test", AGENT_BRAIN_MODEL="gemini-9.9-test"):
            routes = rm.resolve_routes()
        self.assertEqual(routes["taxops.intent"], rm.EXPECTED_DEFAULT_ROUTES["taxops.intent"])

    def test_vertex_location_env_does_not_move_brain(self):
        # VERTEX_LOCATION 只该挪非 global-only 模型(3.5/embedding);大脑(2.5 前缀)不动
        with scrubbed_env(VERTEX_LOCATION="us-central1"):
            routes = rm.resolve_routes()
        self.assertEqual(routes["agent.brain"].vertex_location, "global")
        self.assertEqual(routes["ocr.direct35.flash"].vertex_location, "us-central1")
        self.assertEqual(routes["knowledge.embedding"].vertex_location, "us-central1")

    def test_vertex_location_25_also_moves_brain_documented_coupling(self):
        # ★已知连坐(如实锁死,不是背书):VERTEX_LOCATION_25 按模型名前缀生效,
        # 大脑同为 2.5/3.1 前缀会被一起挪。谁改这条前缀规则或给大脑解耦区域,
        # 必须让本断言随之更新——这正是"改 OCR 牵动大脑"要显式过审的地方。
        with scrubbed_env(VERTEX_LOCATION_25="asia-southeast1"):
            routes = rm.resolve_routes()
        self.assertEqual(routes["agent.brain"].vertex_location, "asia-southeast1")
        self.assertEqual(routes["ocr.economy.flash_lite"].vertex_location, "asia-southeast1")

    def test_mode_maps_touch_ocr_tiers_only(self):
        # engine_policy 的档位覆写永远只许碰 OCR 四档;谁往里塞 brain/embedding 直接红
        for mode, mapping in ep.MODE_MODEL_MAPS.items():
            self.assertLessEqual(
                set(mapping),
                {"flash", "flash_lite", "fallback", "escalate"},
                f"mode {mode!r} 覆写了非 OCR 档位: {sorted(mapping)}",
            )

    def test_selfhost_lanes_use_selfhost_backend(self):
        # 自部署档:四档统一走 selfhost 后端、无 Vertex 区域;env 未配 → 占位名(不虚记 Gemini 名)
        with scrubbed_env():
            routes = rm.resolve_routes()
        for tier in ("flash", "flash_lite", "fallback", "escalate"):
            r = routes[f"ocr.selfhost.{tier}"]
            self.assertEqual(r.backend, "selfhost")
            self.assertEqual(r.vertex_location, "")
            self.assertEqual(r.model, "(unset)")

    def test_selfhost_model_env_reflected(self):
        # 运维填 SELFHOST_OCR_MODEL(Gemma4 等)→ 总表如实显真名,与默认(unset)偏离(冒烟可见)
        with scrubbed_env(SELFHOST_OCR_MODEL="google/gemma-4-27b"):
            routes = rm.resolve_routes()
            diff = rm.diff_from_defaults(routes)
        self.assertEqual(routes["ocr.selfhost.flash"].model, "google/gemma-4-27b")
        self.assertIn("ocr.selfhost.flash", diff)

    def test_resolve_does_not_leak_override_context(self):
        from services.ocr import gemini_models

        with scrubbed_env():
            before = gemini_models.flash_lite()
            rm.resolve_routes()
            self.assertEqual(gemini_models.flash_lite(), before)


class DiffFromDefaultsTests(unittest.TestCase):
    def test_no_env_no_diff(self):
        with scrubbed_env():
            self.assertEqual(rm.diff_from_defaults(rm.resolve_routes()), {})

    def test_env_override_reported_per_lane(self):
        with scrubbed_env(AGENT_BRAIN_MODEL="gemini-3.1-flash-lite"):
            diff = rm.diff_from_defaults(rm.resolve_routes())
        self.assertEqual(set(diff), {"agent.brain"})
        exp, act = diff["agent.brain"]
        self.assertEqual(exp.model, "gemini-2.5-flash")
        self.assertEqual(act.model, "gemini-3.1-flash-lite")


if __name__ == "__main__":
    unittest.main(verbosity=2)
