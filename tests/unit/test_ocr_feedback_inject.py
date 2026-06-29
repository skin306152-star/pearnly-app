# -*- coding: utf-8 -*-
"""反馈闭环 ② 消费侧注入 · context + maybe_block_for_text(无 DB)。

验:flag 关 / 无上下文 / 文本无税号 / 例库空 → 空串(prompt 不变);有例 → 拼块;
fetch 异常 → 空串(绝不抛)。"""

import unittest
from unittest import mock

from services.ocr.feedback import context, fewshot

_TEXT = "ใบกำกับภาษี ผู้ขาย เลขประจำตัวผู้เสียภาษี 0105556000001 รวม 100"


class ContextTests(unittest.TestCase):
    def test_default_none(self):
        self.assertIsNone(context.current())

    def test_set_and_reset(self):
        with context.ocr_request_context("u1", "t1"):
            self.assertEqual(context.current(), {"user_id": "u1", "tenant_id": "t1"})
        self.assertIsNone(context.current())


class MaybeBlockTests(unittest.TestCase):
    def _enable(self):
        return mock.patch.dict("os.environ", {"OCR_FEWSHOT_ENABLED": "1"})

    def test_flag_off_returns_empty(self):
        with context.ocr_request_context("u1", "t1"):
            self.assertEqual(fewshot.maybe_block_for_text(_TEXT), "")

    def test_no_context_returns_empty(self):
        with self._enable():
            self.assertEqual(fewshot.maybe_block_for_text(_TEXT), "")

    def test_no_tax_in_text_returns_empty(self):
        with self._enable(), context.ocr_request_context("u1", "t1"):
            self.assertEqual(fewshot.maybe_block_for_text("ไม่มีเลขภาษี total 100"), "")

    def test_empty_pool_returns_empty(self):
        with (
            self._enable(),
            context.ocr_request_context("u1", "t1"),
            mock.patch("services.ocr.feedback.store.fetch_examples", return_value=[]),
        ):
            self.assertEqual(fewshot.maybe_block_for_text(_TEXT), "")

    def test_examples_build_block(self):
        ex = [{"field_name": "invoice_number", "ai_value": "IV1", "corrected_value": "IV-001"}]
        with (
            self._enable(),
            context.ocr_request_context("u1", "t1"),
            mock.patch("services.ocr.feedback.store.fetch_examples", return_value=ex) as fx,
        ):
            block = fewshot.maybe_block_for_text(_TEXT)
        self.assertIn("IV-001", block)
        # 按文本里的税号取例
        self.assertEqual(fx.call_args[0][2], "0105556000001")

    def test_fetch_error_never_raises(self):
        with (
            self._enable(),
            context.ocr_request_context("u1", "t1"),
            mock.patch(
                "services.ocr.feedback.store.fetch_examples", side_effect=RuntimeError("db down")
            ),
        ):
            self.assertEqual(fewshot.maybe_block_for_text(_TEXT), "")


if __name__ == "__main__":
    unittest.main()
