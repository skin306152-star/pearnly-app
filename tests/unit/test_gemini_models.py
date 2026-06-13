# -*- coding: utf-8 -*-
"""中心化 Gemini 模型选择 + 兜底升级 helper 的单测。

锁住:env 可配、[主→兜底] 顺序、主失败/不可接受时升级、关闭兜底(OCR_FALLBACK_MODEL='')、
全部失败返回 None。这是『3.5-flash 兜底铺到所有 OCR 入口』的共享地基。
"""

import os
import unittest

from services.ocr import gemini_models as gm


class GeminiModelsTests(unittest.TestCase):
    def setUp(self):
        self._saved = {
            k: os.environ.get(k)
            for k in (
                "OCR_FLASH_MODEL",
                "OCR_FLASHLITE_MODEL",
                "OCR_FALLBACK_MODEL",
                "OCR_ESCALATE_MODEL",
            )
        }
        for k in self._saved:
            os.environ.pop(k, None)

    def tearDown(self):
        for k, v in self._saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v

    def test_defaults(self):
        self.assertEqual(gm.flash(), "gemini-2.5-flash")
        self.assertEqual(gm.flash_lite(), "gemini-2.5-flash-lite")
        self.assertEqual(gm.fallback(), "gemini-3.5-flash")

    def test_env_override(self):
        os.environ["OCR_FLASH_MODEL"] = "gemini-x"
        os.environ["OCR_FALLBACK_MODEL"] = "gemini-y"
        self.assertEqual(gm.flash(), "gemini-x")
        self.assertEqual(gm.fallback(), "gemini-y")

    def test_models_with_fallback_order_and_dedup(self):
        self.assertEqual(gm.models_with_fallback(), ["gemini-2.5-flash", "gemini-3.5-flash"])
        # primary == fallback → 不重复
        os.environ["OCR_FALLBACK_MODEL"] = "gemini-2.5-flash"
        self.assertEqual(gm.models_with_fallback(), ["gemini-2.5-flash"])

    def test_fallback_disabled(self):
        os.environ["OCR_FALLBACK_MODEL"] = ""
        self.assertEqual(gm.fallback(), "")
        self.assertEqual(gm.models_with_fallback(), ["gemini-2.5-flash"])

    def test_escalate_defaults_to_fallback(self):
        # image-first 升级臂默认 = fallback(3.5-flash),不另起档位。
        self.assertEqual(gm.escalate(), "gemini-3.5-flash")

    def test_escalate_explicit_env_overrides(self):
        os.environ["OCR_ESCALATE_MODEL"] = "gemini-z"
        self.assertEqual(gm.escalate(), "gemini-z")

    def test_escalate_follows_fallback_when_unset(self):
        os.environ["OCR_FALLBACK_MODEL"] = "gemini-fb"
        self.assertEqual(gm.escalate(), "gemini-fb")

    def test_try_escalates_on_primary_failure(self):
        tried = []

        def call(m):
            tried.append(m)
            if m == "gemini-2.5-flash":
                raise ValueError("truncated JSON")
            return {"ok": True, "model": m}

        r = gm.try_with_fallback(call, label="t")
        self.assertEqual(r, {"ok": True, "model": "gemini-3.5-flash"})
        self.assertEqual(tried, ["gemini-2.5-flash", "gemini-3.5-flash"])

    def test_try_escalates_on_unacceptable_result(self):
        # 主模型返回空 → 视为不可接受 → 升级
        def call(m):
            return [] if m == "gemini-2.5-flash" else [1, 2, 3]

        r = gm.try_with_fallback(call, label="t")
        self.assertEqual(r, [1, 2, 3])

    def test_try_all_fail_returns_none(self):
        def call(m):
            raise RuntimeError("boom")

        self.assertIsNone(gm.try_with_fallback(call, label="t"))

    def test_primary_success_no_escalation(self):
        tried = []

        def call(m):
            tried.append(m)
            return {"ok": True}

        gm.try_with_fallback(call, label="t")
        self.assertEqual(tried, ["gemini-2.5-flash"])  # 兜底未被调用


if __name__ == "__main__":
    unittest.main()
