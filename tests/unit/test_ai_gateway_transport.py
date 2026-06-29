# -*- coding: utf-8 -*-
"""网关统一 transport + 后端开关 契约测试。

锁住:① OCR_LLM_BACKEND 路由(默认 aistudio / vertex / selfhost / 未知回落)
     ② transport 4 形态把调用转发给 active provider 并回 ProviderOutcome + 计时日志
     ③ 无凭据时各 provider 收敛为标准 error_kind(不抛)
"""

import os
import unittest
from unittest import mock

from services.ai_gateway import backends, transport
from services.ai_gateway.tasks import ProviderOutcome


class TestBackendSwitch(unittest.TestCase):
    def _set(self, val):
        if val is None:
            os.environ.pop("OCR_LLM_BACKEND", None)
        else:
            os.environ["OCR_LLM_BACKEND"] = val

    def tearDown(self):
        self._set(None)

    def test_default_is_aistudio(self):
        self._set(None)
        self.assertEqual(backends.active_backend(), "aistudio")
        self.assertEqual(backends.get_provider().NAME, "aistudio")

    def test_env_vertex_and_selfhost(self):
        self._set("vertex")
        self.assertEqual(backends.get_provider().NAME, "vertex")
        self._set("selfhost")
        self.assertEqual(backends.get_provider().NAME, "selfhost")

    def test_unknown_falls_back_to_aistudio(self):
        self._set("nonsense")
        self.assertEqual(backends.active_backend(), "aistudio")
        self._set("VERTEX")  # 大小写不敏感
        self.assertEqual(backends.active_backend(), "vertex")


class _FakeProvider:
    NAME = "fake"
    last = {}

    @staticmethod
    def text_to_json(prompt, **kw):
        _FakeProvider.last = {"method": "text_to_json", "prompt": prompt, **kw}
        return ProviderOutcome(
            ok=True, data={"x": 1}, model="fake-m", input_tokens=3, output_tokens=4
        )

    @staticmethod
    def multimodal_to_json(prompt, images, **kw):
        _FakeProvider.last = {"method": "multimodal_to_json", "n_images": len(images), **kw}
        return ProviderOutcome(ok=True, data={"y": 2}, model="fake-m")

    @staticmethod
    def text_to_text(prompt, **kw):
        return ProviderOutcome(ok=True, data="hello", model="fake-m")

    @staticmethod
    def embed(texts, **kw):
        return ProviderOutcome(ok=True, data=[[0.1, 0.2]], model="fake-e")


class TestTransportRouting(unittest.TestCase):
    def setUp(self):
        self.p = mock.patch.object(backends, "get_provider", return_value=_FakeProvider)
        self.p.start()

    def tearDown(self):
        self.p.stop()

    def test_text_to_json_forwards_and_wraps(self):
        out = transport.text_to_json("hi", tier="flash_lite", api_key="k", temperature=0.3)
        self.assertTrue(out.ok)
        self.assertEqual(out.data, {"x": 1})
        self.assertEqual(_FakeProvider.last["tier"], "flash_lite")
        self.assertEqual(_FakeProvider.last["temperature"], 0.3)

    def test_multimodal_passes_images(self):
        out = transport.multimodal_to_json("p", [(b"img", "image/png")], tier="flash")
        self.assertTrue(out.ok)
        self.assertEqual(_FakeProvider.last["n_images"], 1)

    def test_text_and_embed(self):
        self.assertEqual(transport.text_to_text("p").data, "hello")
        self.assertEqual(transport.embed(["a"]).data, [[0.1, 0.2]])

    def test_non_outcome_return_is_defended(self):
        class Bad:
            NAME = "bad"

            @staticmethod
            def text_to_json(prompt, **kw):
                return "not an outcome"

        with mock.patch.object(backends, "get_provider", return_value=Bad):
            out = transport.text_to_json("hi", api_key="k")
            self.assertFalse(out.ok)
            self.assertEqual(out.error_kind, "provider")


class TestProviderNoCredentials(unittest.TestCase):
    def test_aistudio_no_key_is_auth(self):
        from services.ai_gateway.providers import aistudio

        self.assertEqual(aistudio.text_to_json("p", api_key=None).error_kind, "auth")
        self.assertEqual(
            aistudio.multimodal_to_json("p", [(b"x", "image/png")], api_key=None).error_kind, "auth"
        )

    def test_selfhost_no_url_is_auth(self):
        from services.ai_gateway.providers import selfhost

        with mock.patch.dict(os.environ, {"SELFHOST_OCR_URL": ""}, clear=False):
            self.assertEqual(selfhost.text_to_json("p").error_kind, "auth")


if __name__ == "__main__":
    unittest.main()
