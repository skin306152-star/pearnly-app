#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/unit/test_importer_gl_inference_behavior.py · REFACTOR-WA-COV3

域:services/importer/gl_inference.py 的【行为分支】(现有 contract 测只盖 1 happy + 1 negative)

为啥要这些测试(GL 总账列推断 = 对账正确性关键 · 0 逻辑改只加测):
  GL 没有余额链做数学校验 → 全靠"表头词命中 + 数据形状"判定哪列是 借/贷/金额/日期。
  判错 = 总账对账读反借贷/认错钱列 → 用户账目错。本文件锁实际分支行为:
    - _map_gl_by_header:全列映射 + elif 优先级(date 先)+ 空格跳过 + 同类不覆盖。
    - _fill_gl_by_shape:无表头时按形状补 date / 2 钱列→debit,credit / 1 钱列→amount。
    - infer_gl_col_map:high(表头强命中 borrow+lend 或 amount · signal≥3 · 形状 OK)/
      medium(signal≥2 + 形状 OK)/ low(缺 date 或钱列 → 默认 no-header)。
    - validate_gl_shape:正例(True+rate)/ 缺 date / 缺钱列 / 行数不足 → (False,0)。

纯逻辑 · 无 DB / 无外部 · 行 fixture 驱动 · CI 必跑不 skip。
依据 2026-05-30 实读 gl_inference.py 真实实现(R39 教训:先 Read 再写测 · 期望值由代码推导 + 运行核对)。
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.importer import gl_inference as gl  # noqa: E402


class MapGlByHeaderTest(unittest.TestCase):
    def test_maps_all_columns(self) -> None:
        cm = gl._map_gl_by_header(
            ["Date", "Doc No", "Description", "Debit", "Credit", "Account", "Balance"]
        )
        self.assertEqual(cm["date"], 0)
        self.assertEqual(cm["doc_no"], 1)
        self.assertEqual(cm["description"], 2)
        self.assertEqual(cm["debit"], 3)
        self.assertEqual(cm["credit"], 4)
        self.assertEqual(cm["account"], 5)
        self.assertEqual(cm["balance"], 6)

    def test_thai_headers(self) -> None:
        cm = gl._map_gl_by_header(["วันที่", "เดบิต", "เครดิต"])
        self.assertEqual(cm, {"date": 0, "debit": 1, "credit": 2})

    def test_empty_cells_skipped(self) -> None:
        cm = gl._map_gl_by_header(["", "Date", "   "])
        self.assertEqual(cm, {"date": 1})

    def test_duplicate_header_does_not_overwrite(self) -> None:
        # 第二个 date 同义词不覆盖首个(elif "date" not in cm 守门)
        cm = gl._map_gl_by_header(["Date", "วันที่"])
        self.assertEqual(cm["date"], 0)
        self.assertNotIn(1, cm.values())


class FillGlByShapeTest(unittest.TestCase):
    def test_fills_date_and_two_money_cols(self) -> None:
        raw = [
            ["c0", "c1", "c2"],
            ["2024-01-01", "100", "200"],
            ["2024-01-02", "50", "60"],
            ["2024-01-03", "10", "20"],
        ]
        cm: dict = {}
        gl._fill_gl_by_shape(raw, 0, cm)
        self.assertEqual(cm.get("date"), 0)
        self.assertEqual(cm.get("debit"), 1)
        self.assertEqual(cm.get("credit"), 2)

    def test_single_money_col_becomes_amount(self) -> None:
        raw = [
            ["c0", "c1"],
            ["2024-01-01", "100"],
            ["2024-01-02", "50"],
            ["2024-01-03", "10"],
        ]
        cm: dict = {}
        gl._fill_gl_by_shape(raw, 0, cm)
        self.assertEqual(cm.get("date"), 0)
        self.assertEqual(cm.get("amount"), 1)
        self.assertNotIn("debit", cm)

    def test_no_fill_when_below_threshold(self) -> None:
        # 只有 2 个数据行 → date-like/amount-like 命中 <3 → 不补
        raw = [["c0", "c1"], ["2024-01-01", "100"], ["2024-01-02", "50"]]
        cm: dict = {}
        gl._fill_gl_by_shape(raw, 0, cm)
        self.assertEqual(cm, {})


class InferGlColMapTest(unittest.TestCase):
    def _body(self):
        return [
            ["2024-01-02", "100", "0"],
            ["2024-01-03", "0", "50"],
            ["2024-01-04", "20", "0"],
        ]

    def test_high_confidence_clear_debit_credit(self) -> None:
        rows = [["วันที่", "เดบิต", "เครดิต"], *self._body()]
        idx, cm, conf, _r = gl.infer_gl_col_map(rows)
        self.assertEqual(idx, 0)
        self.assertEqual(conf, "high")
        self.assertEqual(cm.get("debit"), 1)
        self.assertEqual(cm.get("credit"), 2)

    def test_medium_confidence_date_plus_amount(self) -> None:
        # date + amount 两列(header_signal=2)· 形状 OK 但非 strong(signal<3)→ medium
        rows = [
            ["Date", "Amount"],
            ["2024-01-02", "100"],
            ["2024-01-03", "50"],
            ["2024-01-04", "20"],
        ]
        idx, cm, conf, _r = gl.infer_gl_col_map(rows)
        self.assertEqual(idx, 0)
        self.assertEqual(conf, "medium")
        self.assertEqual(cm.get("date"), 0)
        self.assertEqual(cm.get("amount"), 1)

    def test_no_gl_header_returns_low_default(self) -> None:
        rows = [["foo", "bar"], ["x", "y"], ["a", "b"]]
        idx, cm, conf, reasons = gl.infer_gl_col_map(rows)
        self.assertEqual(idx, -1)
        self.assertEqual(cm, {})
        self.assertEqual(conf, "low")
        self.assertEqual(reasons, ["no gl header found"])


class ValidateGlShapeTest(unittest.TestCase):
    def _good_rows(self):
        return [
            ["Date", "Debit", "Credit"],
            ["2024-01-02", "100", "0"],
            ["2024-01-03", "0", "50"],
            ["2024-01-04", "20", "0"],
            ["2024-01-05", "0", "30"],
        ]

    def test_valid_shape_true_with_rate(self) -> None:
        ok, rate = gl.validate_gl_shape(self._good_rows(), 0, {"date": 0, "debit": 1, "credit": 2})
        self.assertTrue(ok)
        self.assertGreater(rate, 0.0)
        self.assertLessEqual(rate, 1.0)

    def test_missing_date_false(self) -> None:
        ok, rate = gl.validate_gl_shape(self._good_rows(), 0, {"debit": 1, "credit": 2})
        self.assertFalse(ok)
        self.assertEqual(rate, 0.0)

    def test_missing_money_false(self) -> None:
        ok, rate = gl.validate_gl_shape(self._good_rows(), 0, {"date": 0})
        self.assertFalse(ok)
        self.assertEqual(rate, 0.0)

    def test_too_few_rows_false(self) -> None:
        rows = [["Date", "Debit", "Credit"], ["2024-01-02", "100", "0"]]  # 1 数据行 < min 3
        ok, rate = gl.validate_gl_shape(rows, 0, {"date": 0, "debit": 1, "credit": 2})
        self.assertFalse(ok)
        self.assertEqual(rate, 0.0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
