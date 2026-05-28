# -*- coding: utf-8 -*-
"""
REFACTOR-WA-B1 守门测试 · services/importer/coerce.py
(2026-05-29 从 template_learning 抽出 6 个值coercion 叶子原语 · 纯搬家 0 逻辑改)

锁定:
  1. coerce 导出 6 原语 · 行为不变(金额千分位/括号负 · 泰历日期 −543 · 形状判定)。
  2. template_learning 从 coerce 单一来源 re-import 同一对象(tl.to_float is coerce.to_float)·
     防两处各拷一份漂移(下游 bank_recon_v2/stmt_review/推断层都经 tl.X 调)。
  3. coerce 是叶子(不 import 本包其它模块)· 防循环。
"""

import unittest
from datetime import date

from services.importer import coerce
from services.importer import template_learning as tl


class ImporterCoerceContractTests(unittest.TestCase):
    def test_exports_six_primitives(self):
        for name in ("_norm", "hit", "to_float", "parse_date", "is_date_like", "is_amount_like"):
            self.assertTrue(callable(getattr(coerce, name, None)), f"missing: {name}")

    def test_to_float_formats(self):
        self.assertEqual(coerce.to_float("1,234.50"), 1234.5)
        self.assertEqual(coerce.to_float("(5)"), -5.0)
        self.assertEqual(coerce.to_float("-3"), -3.0)
        self.assertEqual(coerce.to_float(None), 0.0)
        self.assertEqual(coerce.to_float("-"), 0.0)

    def test_parse_date_incl_thai_calendar(self):
        self.assertEqual(coerce.parse_date("2024-01-15"), date(2024, 1, 15))
        # 泰历 2567 → 西历 2024
        self.assertEqual(coerce.parse_date("2567-01-15"), date(2024, 1, 15))
        self.assertIsNone(coerce.parse_date(""))
        self.assertIsNone(coerce.parse_date("not-a-date"))

    def test_shape_helpers_and_hit_and_norm(self):
        self.assertTrue(coerce.is_date_like("2024-01-15"))
        self.assertFalse(coerce.is_date_like("xyz"))
        self.assertTrue(coerce.is_amount_like("100"))
        self.assertFalse(coerce.is_amount_like(""))
        self.assertTrue(coerce.hit("Date", ["date"]))
        self.assertFalse(coerce.hit("Description", ["dr"]))  # 短 ASCII 整词防误命中
        self.assertEqual(coerce._norm("  A   B "), "a b")

    def test_template_learning_reexports_single_source(self):
        for name in ("_norm", "hit", "to_float", "parse_date", "is_date_like", "is_amount_like"):
            self.assertIs(getattr(tl, name), getattr(coerce, name), f"{name} not single-source")

    def test_coerce_is_leaf_no_intra_package_import(self):
        import inspect

        src = inspect.getsource(coerce)
        self.assertNotIn("from services.importer", src)
        self.assertNotIn("import template_learning", src)


if __name__ == "__main__":
    unittest.main()
