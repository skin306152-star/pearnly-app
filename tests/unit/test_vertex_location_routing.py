# -*- coding: utf-8 -*-
"""Vertex per-model 区域路由:gemini-2.5-* 与 gemini-3.1-* 只在 global 端点跑得通
(asia-se1 实测 2.5 返 404、3.1-lite 返空 JSON),必须自动落 global;3.5 与 embedding 留就近区域,
不被 global-only 档的路由牵连(否则知识库换区/延迟劣化)。"""

from __future__ import annotations

import unittest
from unittest import mock

from services.ai_gateway.providers import vertex

_CLEAR = {"VERTEX_LOCATION": "", "VERTEX_LOCATION_25": ""}


class LocationForModelTests(unittest.TestCase):
    def test_25_models_route_to_global(self):
        with mock.patch.dict("os.environ", _CLEAR):
            self.assertEqual(vertex._location_for_model("gemini-2.5-flash-lite"), "global")
            self.assertEqual(vertex._location_for_model("gemini-2.5-flash"), "global")

    def test_31_models_route_to_global(self):
        with mock.patch.dict("os.environ", _CLEAR):
            self.assertEqual(vertex._location_for_model("gemini-3.1-flash-lite"), "global")
            self.assertEqual(vertex._location_for_model("gemini-3.1-pro-preview"), "global")

    def test_35_and_embedding_stay_default_region(self):
        with mock.patch.dict("os.environ", _CLEAR):
            self.assertEqual(vertex._location_for_model("gemini-3.5-flash"), "asia-southeast1")
            self.assertEqual(vertex._location_for_model("gemini-embedding-001"), "asia-southeast1")

    def test_35_follows_vertex_location_env_25_does_not(self):
        with mock.patch.dict(
            "os.environ", {"VERTEX_LOCATION": "us-central1", "VERTEX_LOCATION_25": ""}
        ):
            self.assertEqual(vertex._location_for_model("gemini-3.5-flash"), "us-central1")
            self.assertEqual(vertex._location_for_model("gemini-2.5-flash-lite"), "global")

    def test_25_location_overridable(self):
        with mock.patch.dict("os.environ", {**_CLEAR, "VERTEX_LOCATION_25": "us-central1"}):
            self.assertEqual(vertex._location_for_model("gemini-2.5-flash-lite"), "us-central1")

    def test_empty_or_none_model_falls_to_default(self):
        with mock.patch.dict("os.environ", _CLEAR):
            self.assertEqual(vertex._location_for_model(""), "asia-southeast1")
            self.assertEqual(vertex._location_for_model(None), "asia-southeast1")


class StructuredVisionConfigTests(unittest.TestCase):
    def test_gemini_35_uses_minimal_thinking(self):
        config = vertex._config(
            0,
            8192,
            True,
            structured_vision_model="gemini-3.5-flash",
        )
        self.assertEqual(config.thinking_config.thinking_level.value, "MINIMAL")

    def test_gemini_25_disables_thinking_budget(self):
        config = vertex._config(
            0,
            8192,
            True,
            structured_vision_model="gemini-2.5-flash",
        )
        self.assertEqual(config.thinking_config.thinking_budget, 0)

    def test_text_json_config_does_not_override_thinking(self):
        config = vertex._config(0, 8192, True)
        self.assertIsNone(config.thinking_config)


if __name__ == "__main__":
    unittest.main(verbosity=2)
