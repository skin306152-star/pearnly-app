#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/integration/test_recon_primitives_safety_net.py · REFACTOR-WC

对账原语安全网 · 纯加测试不改业务 · 给 A/B 拆 vat_excel 当保险。

锁定 vat_excel_export 的配对底层原语 —— 金额求和 / 金额容差比较 / 发票号与税号
normalize / 税号编辑距离。这些是 `_build_recon_pairs` 判「两条记录是否同一笔」的地基:
normalize 写坏 → 真匹配变孤儿(漏报)或误配(错报);容差写坏 → 金额误判。
本文件直接测原语(比端到端 `test_recon_matching_safety_net` 更细 · 出错能定位到具体 helper)。
全部纯函数(0 DB · 0 网络)→ CI 真跑不 skip。

覆盖维度(对应 loop「对账 · 金额对 / 不误配」· 原语层):
  1. 金额求和 — 报告行总额 = 净额 + VAT(缺净额降级 report_amount)· 发票总额取 total_amount
  2. 金额容差 — _eq_amount 默认 0.01 · 自定义容差 · None 降级 0
  3. normalize — 发票号折大小写/标点 · 税号取数字位
  4. 模糊距离 — tax_id_fuzzy_distance:同号 0 · 逐位差计数
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def _load():
    try:
        from services.vat import vat_excel_export as mod
    except Exception as e:  # pragma: no cover - import 环境问题才触发
        raise unittest.SkipTest(f"vat_excel_export 不可 import:{e}")
    return mod


class ReportTotalDerivationTest(unittest.TestCase):
    """报告行总额 = 净额 + VAT · 缺净额降级 report_amount · 发票总额取 total_amount"""

    def setUp(self) -> None:
        self.m = _load()

    def test_rep_total_is_net_plus_vat(self) -> None:
        self.assertEqual(
            self.m._get_rep_total({"report_amount_pre_vat": 100.0, "report_vat_amount": 7.0}),
            107.0,
        )

    def test_rep_total_falls_back_to_report_amount(self) -> None:
        # 没拆净额/VAT 时 · 用 report_amount 兜底(+ 0 VAT)
        self.assertEqual(self.m._get_rep_total({"report_amount": 50.0}), 50.0)

    def test_rep_total_empty_is_zero(self) -> None:
        self.assertEqual(self.m._get_rep_total({}), 0.0)

    def test_inv_total_reads_total_amount(self) -> None:
        self.assertEqual(self.m._get_inv_total({"total_amount": 107.0}), 107.0)

    def test_inv_total_missing_or_garbage_is_zero(self) -> None:
        # 缺字段 / 非数字 → 0(不抛 · 让配对把它当孤儿而非崩)
        self.assertEqual(self.m._get_inv_total({}), 0.0)
        self.assertEqual(self.m._get_inv_total({"total_amount": "abc"}), 0.0)


class AmountToleranceTest(unittest.TestCase):
    """_eq_amount · 默认容差 0.01 · 可自定义 · None 降级 0"""

    def setUp(self) -> None:
        self.m = _load()

    def test_within_default_tolerance(self) -> None:
        # 差 0.005 < 0.01 → 相等(吸收 OCR 末位舍入抖动)
        self.assertTrue(self.m._eq_amount(100.0, 100.005))

    def test_outside_default_tolerance(self) -> None:
        # 差 0.02 > 0.01 → 不等(真金额差不放过)
        self.assertFalse(self.m._eq_amount(100.0, 100.02))

    def test_custom_tolerance(self) -> None:
        self.assertTrue(self.m._eq_amount(100.0, 100.5, 1.0))
        self.assertFalse(self.m._eq_amount(100.0, 101.5, 1.0))

    def test_none_coerced_to_zero(self) -> None:
        # 文档化降级:None 当 0 · None==None 视相等 · None vs 0 相等
        self.assertTrue(self.m._eq_amount(None, None))
        self.assertTrue(self.m._eq_amount(None, 0))
        self.assertFalse(self.m._eq_amount(None, 5.0))


class NormalizeInvoiceNoTest(unittest.TestCase):
    """normalize_invoice_no · 折大小写 + 去空白/标点(同号不同写法视为一致)"""

    def setUp(self) -> None:
        self.m = _load()

    def test_folds_case_whitespace_punctuation(self) -> None:
        self.assertEqual(self.m.normalize_invoice_no(" INV-001 "), "inv001")

    def test_different_writings_normalize_equal(self) -> None:
        self.assertEqual(
            self.m.normalize_invoice_no("INV-001"),
            self.m.normalize_invoice_no("inv001"),
        )

    def test_empty_and_none(self) -> None:
        self.assertEqual(self.m.normalize_invoice_no(""), "")
        self.assertEqual(self.m.normalize_invoice_no(None), "")


class NormalizeTaxIdTest(unittest.TestCase):
    """normalize_tax_id · 取数字位(去横线/空格/字母)"""

    def setUp(self) -> None:
        self.m = _load()

    def test_strips_dashes(self) -> None:
        self.assertEqual(self.m.normalize_tax_id("0-1055-51234-56-7"), "0105551234567")

    def test_strips_letters(self) -> None:
        self.assertEqual(self.m.normalize_tax_id("TH0105551234567"), "0105551234567")


class TaxIdFuzzyDistanceTest(unittest.TestCase):
    """tax_id_fuzzy_distance · 同号 0 · 逐位差计数(供 ≤2 疑似匹配判定)"""

    def setUp(self) -> None:
        self.m = _load()

    def test_identical_is_zero(self) -> None:
        self.assertEqual(self.m.tax_id_fuzzy_distance("0105551234567", "0105551234567"), 0)

    def test_one_digit_off_is_one(self) -> None:
        self.assertEqual(self.m.tax_id_fuzzy_distance("0105551234567", "0105551234568"), 1)

    def test_two_digits_off_is_two(self) -> None:
        self.assertEqual(self.m.tax_id_fuzzy_distance("0105551234567", "0105551234500"), 2)


if __name__ == "__main__":
    unittest.main(verbosity=2)
