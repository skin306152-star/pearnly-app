# -*- coding: utf-8 -*-
"""Vertex per-model 区域路由:gemini-2.5-* 只在 global 端点存在(asia-se1 返 404,实测),
必须自动落 global;3.5 与 embedding 留就近区域,不被 2.5 的路由牵连(否则知识库换区/延迟劣化)。"""

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


if __name__ == "__main__":
    unittest.main(verbosity=2)
