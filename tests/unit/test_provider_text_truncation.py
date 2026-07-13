# -*- coding: utf-8 -*-
"""AI 网关 provider 层:resp.text 快取器截断异常收敛,不许穿透网关。

病根:google-generativeai/google-genai 的 `.text` 快取器在 candidates 为空(典型:
finish_reason=MAX_TOKENS 截断)时抛 ValueError,不是 AttributeError —— hasattr/getattr
挡不住,异常穿透网关砸到 30+ 调用方。K1c 真调实锤(services/fileconv/ocr_bridge.py)
先在桥侧临时兜住;这里收敛回网关契约本身:
  aistudio —— 截断单独识别,直接 error_kind='parse' 且不重试(截断是确定性的);
  vertex   —— 同款异常只收敛为空串(不细分截断),走既有 empty/parse 路。
"""

import unittest
from unittest import mock

from services.ai_gateway.providers import aistudio, vertex

_TRUNCATION_MSG = (
    "Invalid operation: The `response.text` quick accessor requires the response "
    "to contain a valid `Part`, but none were returned. The candidate's "
    "[finish_reason](https://ai.google.dev/api/generate-content#finishreason) is 2."
)


class _Candidate:
    def __init__(self, finish_reason):
        self.finish_reason = finish_reason


class _RaisingResp:
    """`.text` 是 property,访问即抛 —— 复刻 SDK 快取器在 candidates 为空/截断时的真实行为。"""

    def __init__(self, finish_reason=None, message=_TRUNCATION_MSG):
        self.candidates = [_Candidate(finish_reason)] if finish_reason is not None else []
        self.usage_metadata = None
        self._message = message

    @property
    def text(self):
        raise ValueError(self._message)


class _FakeGenModel:
    """google-generativeai GenerativeModel 的最小同形桩。"""

    def __init__(self, resp):
        self._resp = resp
        self.calls = 0

    def generate_content(self, *_a, **_kw):
        self.calls += 1
        return self._resp


class _FakeVertexModels:
    def __init__(self, resp):
        self._resp = resp

    def generate_content(self, **_kw):
        return self._resp


class _FakeVertexClient:
    def __init__(self, resp):
        self.models = _FakeVertexModels(resp)


class AistudioTruncationTests(unittest.TestCase):
    """finish_reason=MAX_TOKENS(2)→ error_kind='parse',一次到位不白烧重试预算。"""

    def test_text_to_json_max_tokens_is_parse_no_retry(self):
        fake_model = _FakeGenModel(_RaisingResp(finish_reason=2))
        with mock.patch.object(aistudio, "_model", return_value=fake_model):
            outcome = aistudio.text_to_json("prompt", api_key="k", max_retries=3)
        self.assertFalse(outcome.ok)
        self.assertEqual(outcome.error_kind, "parse")
        self.assertEqual(fake_model.calls, 1)  # 截断不重试

    def test_text_to_text_max_tokens_is_parse(self):
        fake_model = _FakeGenModel(_RaisingResp(finish_reason=2))
        with (
            mock.patch("google.generativeai.configure"),
            mock.patch("google.generativeai.GenerativeModel", return_value=fake_model),
        ):
            outcome = aistudio.text_to_text("prompt", api_key="k")
        self.assertFalse(outcome.ok)
        self.assertEqual(outcome.error_kind, "parse")

    def test_non_truncation_value_error_does_not_raise(self):
        """candidates 为空、无 finish_reason 的 ValueError → 不算截断,走既有 empty 重试路,
        最终收敛为结构化失败,不炸给调用方。"""
        fake_model = _FakeGenModel(_RaisingResp(finish_reason=None, message="some other glitch"))
        with mock.patch.object(aistudio, "_model", return_value=fake_model):
            outcome = aistudio.text_to_json("prompt", api_key="k", max_retries=1)
        self.assertFalse(outcome.ok)
        self.assertEqual(outcome.error_kind, "parse")
        self.assertEqual(fake_model.calls, 2)  # empty 路正常重试(与截断路径的区别)


class VertexTruncationTests(unittest.TestCase):
    """vertex 侧同款异常只收敛为空串(不做截断细分),但一样不许穿透。"""

    def test_gen_json_text_raise_does_not_propagate(self):
        fake_client = _FakeVertexClient(_RaisingResp(finish_reason=2))
        with mock.patch.object(vertex, "_client", return_value=fake_client):
            outcome = vertex.text_to_json("prompt")
        self.assertFalse(outcome.ok)
        self.assertEqual(outcome.error_kind, "parse")

    def test_text_to_text_raise_does_not_propagate(self):
        fake_client = _FakeVertexClient(_RaisingResp(finish_reason=2))
        with mock.patch.object(vertex, "_client", return_value=fake_client):
            outcome = vertex.text_to_text("prompt")
        self.assertFalse(outcome.ok)
        self.assertEqual(outcome.error_kind, "parse")


if __name__ == "__main__":
    unittest.main()
