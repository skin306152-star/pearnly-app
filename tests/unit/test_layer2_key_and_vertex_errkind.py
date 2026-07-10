# -*- coding: utf-8 -*-
"""C-1 §6 回落路收编网关:L2 密钥语义随后端(aistudio 认 key / vertex 走 SA)+ vertex
error_kind 的 quota/auth 分类边界(403+配额不得误归 auth 让可重试错 fail-fast)。"""

from __future__ import annotations

import os
import unittest
from unittest import mock

from services.ai_gateway.providers import vertex
from services.ocr import layer2_structure as l2
from services.ocr.layer2_gemini import Layer2AuthError


class _Err(Exception):
    def __init__(self, msg, code=None):
        super().__init__(msg)
        self.code = code


class ResolveGeminiKeyTests(unittest.TestCase):
    def setUp(self):
        # 清掉环境密钥,单独控制后端。
        self._env = mock.patch.dict(
            os.environ, {"GOOGLE_API_KEY": "", "GEMINI_API_KEY": ""}, clear=False
        )
        self._env.start()
        os.environ.pop("GOOGLE_API_KEY", None)
        os.environ.pop("GEMINI_API_KEY", None)
        self.addCleanup(self._env.stop)

    def test_aistudio_without_key_raises_auth(self):
        with mock.patch("services.ai_gateway.backends.is_aistudio", return_value=True):
            with self.assertRaises(Layer2AuthError):
                l2._resolve_gemini_key(None)

    def test_vertex_without_key_returns_none_not_raise(self):
        # vertex 走服务账号,无 env key 也不该炸(正是回落票被误判 auth 全灭的根因)。
        with mock.patch("services.ai_gateway.backends.is_aistudio", return_value=False):
            self.assertIsNone(l2._resolve_gemini_key(None))

    def test_explicit_key_is_stripped_and_returned(self):
        with mock.patch("services.ai_gateway.backends.is_aistudio", return_value=True):
            self.assertEqual(l2._resolve_gemini_key("  sk-abc  "), "sk-abc")


class VertexErrorKindTests(unittest.TestCase):
    def test_403_with_quota_keyword_is_quota_not_auth(self):
        self.assertEqual(vertex._error_kind(_Err("RESOURCE_EXHAUSTED: quota", code=403)), "quota")

    def test_429_is_quota(self):
        self.assertEqual(vertex._error_kind(_Err("too many requests", code=429)), "quota")

    def test_pure_permission_denied_stays_auth(self):
        self.assertEqual(vertex._error_kind(_Err("permission denied", code=403)), "auth")

    def test_401_is_auth(self):
        self.assertEqual(vertex._error_kind(_Err("unauthenticated", code=401)), "auth")

    def test_5xx_is_timeout(self):
        self.assertEqual(vertex._error_kind(_Err("service unavailable", code=503)), "timeout")


if __name__ == "__main__":
    unittest.main()
