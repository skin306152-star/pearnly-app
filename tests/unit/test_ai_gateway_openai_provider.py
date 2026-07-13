# -*- coding: utf-8 -*-
"""openai provider 契约守门:四形态 / 截断收敛 / error_kind 分类 / store:false / 后端接线。

不打真网络(patch httpx.post);验与 aistudio/vertex/selfhost/anthropic 同契约(ProviderOutcome)。
重点锁截断路:finish_reason=length / 空 choices 必须一次收敛为 parse 且零重试
(aistudio 曾因空 candidates 裸取 resp.text 抛 ValueError 穿透网关的教训)。
"""

import os
import unittest
from unittest import mock
from unittest.mock import patch

from services.ai_gateway import backends
from services.ai_gateway.providers import openai
from services.ai_gateway.tasks import ProviderOutcome

_ENV = {
    "OPENAI_API_KEY": "sk-test",
    "OPENAI_FLASH_MODEL": "gpt-test-flash",
    "OPENAI_BEST_MODEL": "gpt-test-best",
}


class _Resp:
    def __init__(self, status, body=None, text=""):
        self.status_code = status
        self._body = body or {}
        self.text = text

    def json(self):
        return self._body


def _ok_body(content, *, finish="stop", usage=None):
    return {
        "choices": [{"message": {"content": content}, "finish_reason": finish}],
        "usage": usage or {"prompt_tokens": 10, "completion_tokens": 5},
    }


class _Capture:
    """替身 httpx.post:记录每次请求 payload 快照(provider 会原地改 payload,存引用会被改)。"""

    def __init__(self, responses):
        self.responses = list(responses)
        self.payloads = []

    def __call__(self, url, headers=None, json=None, timeout=None):
        self.payloads.append({k: v for k, v in json.items()})
        return self.responses.pop(0) if len(self.responses) > 1 else self.responses[0]


class TestOpenAiProvider(unittest.TestCase):
    def setUp(self):
        self._env = patch.dict(os.environ, _ENV)
        self._env.start()
        openai._NO_TEMP.clear()
        openai._LEGACY_MAX.clear()

    def tearDown(self):
        self._env.stop()

    def test_text_to_json_ok_with_store_false_and_json_mode(self):
        cap = _Capture([_Resp(200, _ok_body('{"kind":"reply"}'))])
        with patch("httpx.post", cap):
            oc = openai.text_to_json("prompt", tier="flash")
        self.assertTrue(oc.ok)
        self.assertEqual(oc.data, {"kind": "reply"})
        self.assertEqual((oc.input_tokens, oc.output_tokens), (10, 5))
        self.assertEqual(oc.model, "gpt-test-flash")
        p = cap.payloads[0]
        self.assertIs(p["store"], False)
        self.assertEqual(p["response_format"], {"type": "json_object"})
        self.assertEqual(p["max_completion_tokens"], 16384)

    def test_text_to_text_ok_with_system_message(self):
        cap = _Capture([_Resp(200, _ok_body("hello"))])
        with patch("httpx.post", cap):
            oc = openai.text_to_text("q", system="persona", tier="best")
        self.assertTrue(oc.ok)
        self.assertEqual(oc.data, "hello")
        self.assertEqual(oc.model, "gpt-test-best")
        msgs = cap.payloads[0]["messages"]
        self.assertEqual(msgs[0], {"role": "system", "content": "persona"})
        self.assertIs(cap.payloads[0]["store"], False)

    def test_multimodal_sends_image_data_uri(self):
        cap = _Capture([_Resp(200, _ok_body('{"total":9}'))])
        with patch("httpx.post", cap):
            oc = openai.multimodal_to_json("read it", [(b"\x89PNG", "image/png")])
        self.assertTrue(oc.ok)
        parts = cap.payloads[0]["messages"][0]["content"]
        self.assertEqual(parts[0], {"type": "text", "text": "read it"})
        self.assertTrue(parts[1]["image_url"]["url"].startswith("data:image/png;base64,"))

    def test_finish_reason_length_is_parse_without_retry(self):
        cap = _Capture([_Resp(200, _ok_body("truncat", finish="length"))])
        with patch("httpx.post", cap):
            oc = openai.text_to_json("p", max_retries=2)
        self.assertFalse(oc.ok)
        self.assertEqual(oc.error_kind, "parse")
        self.assertEqual(len(cap.payloads), 1)  # 截断是确定性的,重试是白烧钱

    def test_empty_choices_is_parse_without_retry(self):
        cap = _Capture([_Resp(200, {"choices": [], "usage": {}})])
        with patch("httpx.post", cap):
            oc = openai.text_to_json("p", max_retries=2)
        self.assertFalse(oc.ok)
        self.assertEqual(oc.error_kind, "parse")
        self.assertEqual(len(cap.payloads), 1)

    def test_bad_json_retries_then_parse_with_raw(self):
        cap = _Capture([_Resp(200, _ok_body("not json"))])
        with patch("httpx.post", cap):
            oc = openai.text_to_json("p", max_retries=1)
        self.assertEqual(oc.error_kind, "parse")
        self.assertEqual(oc.raw, "not json")
        self.assertEqual(len(cap.payloads), 2)  # 坏 JSON(非截断)按 selfhost 同款重试

    def test_missing_key_is_auth_without_network(self):
        cap = _Capture([_Resp(200, _ok_body("x"))])
        with patch.dict(os.environ, {"OPENAI_API_KEY": ""}):
            with patch("httpx.post", cap):
                oc = openai.text_to_json("p")
        self.assertEqual(oc.error_kind, "auth")
        self.assertEqual(cap.payloads, [])

    def test_missing_model_is_auth_without_network(self):
        cap = _Capture([_Resp(200, _ok_body("x"))])
        with patch.dict(os.environ, {"OPENAI_FLASH_MODEL": "", "OPENAI_BEST_MODEL": ""}):
            with patch("httpx.post", cap):
                oc = openai.text_to_json("p")
        self.assertEqual(oc.error_kind, "auth")
        self.assertEqual(cap.payloads, [])

    def test_http_status_maps_error_kinds(self):
        for status, kind in ((401, "auth"), (429, "quota"), (503, "timeout"), (418, "provider")):
            with self.subTest(status=status):
                with patch("httpx.post", return_value=_Resp(status, {}, text="err")):
                    self.assertEqual(openai.text_to_json("p").error_kind, kind)

    def test_temperature_rejected_400_is_stripped_and_memoized(self):
        cap = _Capture(
            [
                _Resp(400, {}, text="Unsupported value: 'temperature' does not support 0.0"),
                _Resp(200, _ok_body('{"kind":"reply"}')),
            ]
        )
        with patch("httpx.post", cap):
            oc = openai.text_to_json("p", temperature=0.0)
        self.assertTrue(oc.ok)
        self.assertIn("temperature", cap.payloads[0])
        self.assertNotIn("temperature", cap.payloads[1])
        self.assertIn("gpt-test-flash", openai._NO_TEMP)  # 已记忆,下次直接不带

    def test_legacy_endpoint_max_tokens_rename_and_memoized(self):
        cap = _Capture(
            [
                _Resp(400, {}, text="unknown parameter: max_completion_tokens"),
                _Resp(200, _ok_body('{"kind":"reply"}')),
            ]
        )
        with patch("httpx.post", cap):
            oc = openai.text_to_json("p")
        self.assertTrue(oc.ok)
        self.assertIn("max_completion_tokens", cap.payloads[0])
        self.assertEqual(cap.payloads[1]["max_tokens"], 16384)
        self.assertIn("gpt-test-flash", openai._LEGACY_MAX)

    def test_action_unsupported_falls_back(self):
        oc = openai.text_to_action("p", tools=[])
        self.assertIsInstance(oc, ProviderOutcome)
        self.assertEqual(oc.error_kind, "unsupported")

    def test_base_url_env_override(self):
        seen = {}

        def _cap(url, headers=None, json=None, timeout=None):
            seen["url"] = url
            return _Resp(200, _ok_body("hi"))

        with patch.dict(os.environ, {"OPENAI_BASE_URL": "https://proxy.example/v1/"}):
            with patch("httpx.post", _cap):
                openai.text_to_text("p")
        self.assertEqual(seen["url"], "https://proxy.example/v1/chat/completions")

    def test_embed_ok_sorted_by_index(self):
        body = {
            "data": [
                {"index": 1, "embedding": [0.3, 0.4]},
                {"index": 0, "embedding": [0.1, 0.2]},
            ]
        }
        with patch.dict(os.environ, {"OPENAI_EMBED_MODEL": "text-embed-test"}):
            with patch("httpx.post", return_value=_Resp(200, body)):
                oc = openai.embed(["a", "b"])
        self.assertTrue(oc.ok)
        self.assertEqual(oc.data, [[0.1, 0.2], [0.3, 0.4]])


class TestBackendWiring(unittest.TestCase):
    def test_valid_includes_openai(self):
        self.assertIn("openai", backends._VALID)

    def test_get_provider_openai(self):
        self.assertEqual(backends.get_provider("openai").NAME, "openai")

    def test_default_backend_unchanged(self):
        # 闸外零行为变化:env 不选 openai 时默认仍是 aistudio
        with mock.patch.dict(os.environ, {}, clear=False):
            os.environ.pop("OCR_LLM_BACKEND", None)
            self.assertEqual(backends.active_backend(), "aistudio")
            self.assertEqual(backends.get_provider().NAME, "aistudio")

    def test_env_openai_selects_provider(self):
        with mock.patch.dict(os.environ, {"OCR_LLM_BACKEND": "openai"}):
            self.assertEqual(backends.active_backend(), "openai")
            self.assertEqual(backends.get_provider().NAME, "openai")


if __name__ == "__main__":
    unittest.main()
