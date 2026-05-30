#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/unit/test_ocr_pattern_memory_contract.py · REFACTOR-WA-OCRSPLIT P-C

锁 P-C 纯搬家(InvoicePatternMemory pipeline → pattern_memory)0 逻辑改:
  1. pipeline.InvoicePatternMemory / MIN_INSTANCES_BEFORE_FLAGGING 与 pattern_memory 同一对象(assertIs)。
  2. pattern_memory 是 leaf(不 import pipeline)。
  3. record / check_anomaly / _extract_pattern 行为口径不变(功能锁)。

纯逻辑 · 无 DB/genai。CI 必跑不 skip。
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.ocr import pipeline as p  # noqa: E402
from services.ocr import pattern_memory as m  # noqa: E402


class PatternMemoryContractTest(unittest.TestCase):
    def test_reexport_single_source(self) -> None:
        self.assertIs(p.InvoicePatternMemory, m.InvoicePatternMemory)
        self.assertIs(p.MIN_INSTANCES_BEFORE_FLAGGING, m.MIN_INSTANCES_BEFORE_FLAGGING)

    def test_module_is_leaf(self) -> None:
        self.assertIsNone(getattr(m, "pipeline", None))

    def test_extract_pattern(self) -> None:
        pm = m.InvoicePatternMemory
        self.assertEqual(pm._extract_pattern("INV2026030001"), "INV2026")
        self.assertEqual(pm._extract_pattern("IV69/00179"), "IV69")
        self.assertIsNone(pm._extract_pattern(""))

    def test_record_and_anomaly_baseline(self) -> None:
        pm = m.InvoicePatternMemory()
        # 同 seller 记录足量同前缀实例后,异前缀才会被判异常;不足基线不判
        pm.record("0105546015062", "IV69/00179")
        # 单实例(< MIN_INSTANCES_BEFORE_FLAGGING=2)→ 不判异常
        r1 = pm.check_anomaly("0105546015062", "ABC123")
        self.assertFalse(bool(r1))
        pm.record("0105546015062", "IV69/00180")
        # 达基线后,异前缀 → 判异常(返回真值);同前缀 → 不判
        self.assertFalse(bool(pm.check_anomaly("0105546015062", "IV69/00181")))
        self.assertTrue(bool(pm.check_anomaly("0105546015062", "XYZ999")))


if __name__ == "__main__":
    unittest.main(verbosity=2)
