#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/unit/test_ocr_triggers_contract.py · REFACTOR-WA-OCRSPLIT P-B

锁 P-B 纯搬家(L3 触发/置信纯逻辑 pipeline → triggers)0 逻辑改:
  1. pipeline re-export 的 5 常量 + 5 函数与 triggers 同一对象(assertIs)。
  2. triggers 是 leaf(不 import pipeline)。
  3. 触发/置信口径不变(功能锁·duck-typed 输入):
     _check_amount_math / _bucket_confidence / _count_invoice_no_candidates /
     _evaluate_triggers(is_not_invoice 短路 + 缺字段触发)。

纯逻辑 · SimpleNamespace 鸭子类型(不构造 pydantic)· 无 DB/genai。CI 必跑不 skip。
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path
from types import SimpleNamespace

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.ocr import pipeline as p  # noqa: E402
from services.ocr import triggers as t  # noqa: E402

_NAMES = (
    "CONFIDENCE_THRESHOLD",
    "AMOUNT_TOLERANCE_THB",
    "CRITICAL_FIELDS",
    "CONFIDENCE_AUTO_THRESHOLD",
    "CONFIDENCE_REVIEW_THRESHOLD",
    "_aggregate_page_confidence",
    "_bucket_confidence",
    "_check_amount_math",
    "_count_invoice_no_candidates",
    "_evaluate_triggers",
)


def _inv(**kw):
    base = dict(
        is_not_invoice=False,
        invoice_number="",
        total_amount="",
        seller_tax="",
        subtotal="",
        vat="",
        date_raw="",
        date="",
        additional_invoices=[],
    )
    base.update(kw)
    return SimpleNamespace(**base)


class TriggersContractTest(unittest.TestCase):
    def test_reexport_single_source(self) -> None:
        for n in _NAMES:
            self.assertIs(getattr(p, n), getattr(t, n), f"{n} re-export 漂移")

    def test_module_is_leaf(self) -> None:
        self.assertIsNone(getattr(t, "pipeline", None))

    def test_check_amount_math(self) -> None:
        self.assertIsNone(t._check_amount_math(_inv(subtotal="100", vat="7", total_amount="107")))
        r = t._check_amount_math(_inv(subtotal="100", vat="7", total_amount="200"))
        self.assertIsInstance(r, str)
        self.assertIn("amount math fail", r)
        # 缺字段 → None(不误触发)
        self.assertIsNone(t._check_amount_math(_inv(subtotal="100")))

    def test_bucket_confidence(self) -> None:
        self.assertEqual(t._bucket_confidence(0.99, False), "auto")
        self.assertEqual(t._bucket_confidence(0.95, False), "yellow_confirm")
        self.assertEqual(t._bucket_confidence(0.80, False), "needs_review")
        self.assertEqual(t._bucket_confidence(0.99, True), "needs_review")

    def test_count_invoice_no_candidates(self) -> None:
        n = t._count_invoice_no_candidates("foo IV69/00179 bar IV69/00189 baz", "IV69/00179")
        self.assertEqual(n, 2)
        self.assertEqual(t._count_invoice_no_candidates("", "IV69/00179"), 0)
        # 纯字母发票号 → 不数(防过度匹配)
        self.assertEqual(t._count_invoice_no_candidates("ABC ABC", "ABC"), 0)

    def test_evaluate_triggers_not_invoice_shortcircuit(self) -> None:
        page = SimpleNamespace(full_text="", blocks=[], avg_confidence=0.9)
        self.assertEqual(t._evaluate_triggers(page, _inv(is_not_invoice=True)), [])

    def test_evaluate_triggers_missing_fields(self) -> None:
        page = SimpleNamespace(full_text="", blocks=[], avg_confidence=0.9)
        out = t._evaluate_triggers(page, _inv())  # 全空字段
        self.assertIn("invoice_number missing", out)
        self.assertIn("total_amount missing", out)


if __name__ == "__main__":
    unittest.main(verbosity=2)
