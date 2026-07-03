# -*- coding: utf-8 -*-
"""anthropic provider 契约守门:JSON 解析 / 缓存 token 合并 / 标准 error_kind / 提示缓存开关。

不打真网络(patch httpx.post);验 provider 与 aistudio/vertex/selfhost 同契约(ProviderOutcome)。
"""

import unittest
from unittest.mock import patch

from services.ai_gateway.providers import anthropic
from services.ai_gateway.tasks import ProviderOutcome


class _Resp:
    def __init__(self, status, body):
        self.status_code = status
        self._body = body

    def json(self):
        return self._body


def _ok_body(text, usage):
    return {"content": [{"type": "text", "text": text}], "usage": usage}


class TestAnthropicProvider(unittest.TestCase):
    def setUp(self):
        self._env = patch.dict("os.environ", {"ANTHROPIC_API_KEY": "sk-test"})
        self._env.start()

    def tearDown(self):
        self._env.stop()

    def test_json_ok_folds_cache_tokens_into_input(self):
        usage = {
            "input_tokens": 100,
            "cache_creation_input_tokens": 20,
            "cache_read_input_tokens": 1800,
            "output_tokens": 30,
        }
        with patch("httpx.post", return_value=_Resp(200, _ok_body('{"kind":"reply"}', usage))):
            oc = anthropic.text_to_json("prompt", tier="best")
        self.assertTrue(oc.ok)
        self.assertEqual(oc.data, {"kind": "reply"})
        self.assertEqual(oc.input_tokens, 1920)  # 100 + 20 + 1800 合并计费
        self.assertEqual(oc.output_tokens, 30)

    def test_missing_key_is_auth_not_raise(self):
        with patch.dict("os.environ", {"ANTHROPIC_API_KEY": ""}):
            oc = anthropic.text_to_json("p")
        self.assertFalse(oc.ok)
        self.assertEqual(oc.error_kind, "auth")

    def test_http_429_maps_quota(self):
        with patch("httpx.post", return_value=_Resp(429, {})):
            oc = anthropic.text_to_json("p")
        self.assertEqual(oc.error_kind, "quota")

    def test_bad_json_returns_parse_with_raw(self):
        with patch("httpx.post", return_value=_Resp(200, _ok_body("not json", {}))):
            oc = anthropic.text_to_json("p", max_retries=0)
        self.assertFalse(oc.ok)
        self.assertEqual(oc.error_kind, "parse")
        self.assertEqual(oc.raw, "not json")

    def test_cache_control_only_when_system_and_cached(self):
        seen = {}

        def _cap(url, headers=None, json=None, timeout=None):
            seen["payload"] = json
            return _Resp(200, _ok_body('{"kind":"reply"}', {"input_tokens": 1, "output_tokens": 1}))

        with patch("httpx.post", _cap):
            anthropic.text_to_json("body", system="stable prefix", cache_system=True)
        sysblk = seen["payload"]["system"][0]
        self.assertEqual(sysblk["cache_control"], {"type": "ephemeral"})
        self.assertEqual(sysblk["text"], "stable prefix")

    def test_no_cache_control_when_disabled(self):
        seen = {}

        def _cap(url, headers=None, json=None, timeout=None):
            seen["payload"] = json
            return _Resp(200, _ok_body('{"kind":"reply"}', {"input_tokens": 1, "output_tokens": 1}))

        with patch("httpx.post", _cap):
            anthropic.text_to_json("body", system="prefix", cache_system=False)
        self.assertNotIn("cache_control", seen["payload"]["system"][0])

    def test_action_unsupported_falls_back(self):
        oc = anthropic.text_to_action("p", tools=[])
        self.assertIsInstance(oc, ProviderOutcome)
        self.assertEqual(oc.error_kind, "unsupported")

    def test_model_tier_maps_env_override(self):
        with patch.dict("os.environ", {"ANTHROPIC_BEST_MODEL": "claude-sonnet-5-custom"}):
            self.assertEqual(anthropic._model("best"), "claude-sonnet-5-custom")


if __name__ == "__main__":
    unittest.main()
