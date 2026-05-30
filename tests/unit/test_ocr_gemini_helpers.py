#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/unit/test_ocr_gemini_helpers.py · REFACTOR-WA-COV4

域:services/ocr/layer2_structure.py + layer3_fallback.py 的两个纯 helper(此前 0 测试)
    · _parse_json(text)                解析 Gemini 回的发票字段 JSON(剥 markdown 围栏 · 非 dict 抛)
    · _classify_gemini_exception(e)    把 SDK 异常分类成 auth/quota/transient/generic 错(驱动重试/退费)

为啥要这些测试(OCR 热路径安全网 · 0 逻辑改只加测):
  - _parse_json 解析错 → 发票字段错 → 扣费/数据错。锁:干净 JSON / ```json 围栏 / 无语言围栏 /
    无换行围栏 / 非 dict(list/scalar)抛 JSONDecodeError / 非法 JSON 抛。
  - _classify_gemini_exception 决定「这次失败要不要重试 / 要不要退费」:auth(403/密钥)不重试 ·
    quota(429)· transient(超时/5xx/连接)可重试 · 其余 generic。分类错 = 错误的重试/退费决策。
    锁:四类分支 + 优先级(auth > quota > transient)+ 按消息和类型名双重嗅探。
  两 layer 是同逻辑独立副本(各自异常类 Layer2*/Layer3*)· 参数化覆盖两边防其中一份漂移。

纯逻辑 · 无 DB / 无 genai 网络(异常对象本地造)· CI 必跑不 skip。
依据 2026-05-30 实读两模块真实实现(R39 教训:先 Read 再写测)。
"""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.ocr import layer2_structure as l2  # noqa: E402
from services.ocr import layer3_fallback as l3  # noqa: E402

# (模块, base, auth, quota, transient) · 参数化覆盖两 layer
_LAYERS = [
    (l2, l2.Layer2Error, l2.Layer2AuthError, l2.Layer2QuotaError, l2.Layer2TransientError),
    (l3, l3.Layer3Error, l3.Layer3AuthError, l3.Layer3QuotaError, l3.Layer3TransientError),
]


# 造类型名匹配用的假异常(分类器嗅 type(e).__name__)
class PermissionDenied(Exception):
    pass


class ResourceExhausted(Exception):
    pass


class DeadlineExceeded(Exception):
    pass


class ParseJsonTest(unittest.TestCase):
    def test_clean_object(self) -> None:
        for mod, *_ in _LAYERS:
            with self.subTest(mod=mod.__name__):
                self.assertEqual(mod._parse_json('{"a": 1, "b": "x"}'), {"a": 1, "b": "x"})

    def test_strips_json_fence(self) -> None:
        for mod, *_ in _LAYERS:
            with self.subTest(mod=mod.__name__):
                self.assertEqual(mod._parse_json('```json\n{"a": 1}\n```'), {"a": 1})

    def test_strips_bare_fence(self) -> None:
        for mod, *_ in _LAYERS:
            with self.subTest(mod=mod.__name__):
                self.assertEqual(mod._parse_json('```\n{"a": 1}\n```'), {"a": 1})

    def test_fence_without_newline(self) -> None:
        # "```{...}```" · 无换行分支:s=s[3:] 再剥尾 ```
        for mod, *_ in _LAYERS:
            with self.subTest(mod=mod.__name__):
                self.assertEqual(mod._parse_json('```{"a": 1}```'), {"a": 1})

    def test_leading_trailing_whitespace(self) -> None:
        for mod, *_ in _LAYERS:
            with self.subTest(mod=mod.__name__):
                self.assertEqual(mod._parse_json('  \n {"a": 1}  \n '), {"a": 1})

    def test_non_dict_list_raises(self) -> None:
        for mod, *_ in _LAYERS:
            with self.subTest(mod=mod.__name__):
                with self.assertRaises(json.JSONDecodeError):
                    mod._parse_json("[1, 2, 3]")

    def test_non_dict_scalar_raises(self) -> None:
        for mod, *_ in _LAYERS:
            with self.subTest(mod=mod.__name__):
                with self.assertRaises(json.JSONDecodeError):
                    mod._parse_json("42")

    def test_invalid_json_raises(self) -> None:
        for mod, *_ in _LAYERS:
            with self.subTest(mod=mod.__name__):
                with self.assertRaises(json.JSONDecodeError):
                    mod._parse_json("not json at all")


class ClassifyExceptionTest(unittest.TestCase):
    def test_auth_by_message_and_typename(self) -> None:
        for mod, _base, auth, _q, _t in _LAYERS:
            with self.subTest(mod=mod.__name__):
                self.assertIsInstance(mod._classify_gemini_exception(Exception("HTTP 403")), auth)
                self.assertIsInstance(
                    mod._classify_gemini_exception(Exception("API key not valid")), auth
                )
                self.assertIsInstance(mod._classify_gemini_exception(PermissionDenied("x")), auth)

    def test_quota_by_message_and_typename(self) -> None:
        for mod, _base, _a, quota, _t in _LAYERS:
            with self.subTest(mod=mod.__name__):
                self.assertIsInstance(mod._classify_gemini_exception(Exception("HTTP 429")), quota)
                self.assertIsInstance(
                    mod._classify_gemini_exception(Exception("quota exceeded")), quota
                )
                self.assertIsInstance(mod._classify_gemini_exception(ResourceExhausted("x")), quota)

    def test_transient_by_message_and_typename(self) -> None:
        for mod, _base, _a, _q, transient in _LAYERS:
            with self.subTest(mod=mod.__name__):
                self.assertIsInstance(
                    mod._classify_gemini_exception(Exception("request timeout")), transient
                )
                self.assertIsInstance(
                    mod._classify_gemini_exception(Exception("HTTP 503 unavailable")), transient
                )
                self.assertIsInstance(
                    mod._classify_gemini_exception(DeadlineExceeded("x")), transient
                )

    def test_generic_fallback_is_exact_base(self) -> None:
        for mod, base, auth, quota, transient in _LAYERS:
            with self.subTest(mod=mod.__name__):
                res = mod._classify_gemini_exception(Exception("something weird happened"))
                # 恰是基类 · 不是任何子类(避免 isinstance(base) 对子类也 True 的误判)
                self.assertIs(type(res), base)
                self.assertNotIsInstance(res, (auth, quota, transient))

    def test_precedence_auth_over_quota(self) -> None:
        # 同时含 403 与 429 → auth 先判(分类器顺序:auth → quota → transient)
        for mod, _base, auth, _q, _t in _LAYERS:
            with self.subTest(mod=mod.__name__):
                self.assertIsInstance(
                    mod._classify_gemini_exception(Exception("403 and 429 both")), auth
                )

    def test_returns_not_raises_and_keeps_message(self) -> None:
        for mod, *_ in _LAYERS:
            with self.subTest(mod=mod.__name__):
                res = mod._classify_gemini_exception(Exception("boom detail"))
                self.assertIsInstance(res, Exception)
                self.assertIn("boom detail", str(res))


if __name__ == "__main__":
    unittest.main(verbosity=2)
