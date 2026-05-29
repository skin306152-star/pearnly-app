# -*- coding: utf-8 -*-
"""
REFACTOR-WA-B1 守门测试 · services/importer/synonyms.py + gl_inference.py
(2026-05-29 R9 从 template_learning 抽出表头同义词词典 + GL 列推断 · 纯搬家 0 逻辑改)

锁定:
  1. synonyms 是纯数据叶子(无 import template_learning)· 10 个多语词典齐。
  2. gl_inference 叶子(只依赖 coerce/keys/synonyms · 不 import template_learning · 无循环)·
     导出 4 函数。
  3. **seam**:tl.infer_gl_col_map / _map_gl_by_header / _fill_gl_by_shape / validate_gl_shape
     与 gl_inference 同一对象(bank_recon_v2 `_tl.X` + probes + test_gl_template_integration 靠它)。
  4. tl.DATE_H 等同义词与 synonyms 同一对象(stmt 推断 + 外部共用单一来源)。
  5. infer_gl_col_map 行为:明确 GL 表头 → high 置信 + 正确列号;validate_gl_shape 缺钱列 → False。
"""

import unittest

from services.importer import synonyms, gl_inference, keys
from services.importer import template_learning as tl


class ImporterGlInferenceContractTests(unittest.TestCase):
    def test_synonyms_leaf_and_complete(self):
        self.assertIsNone(getattr(synonyms, "template_learning", None))
        for name in (
            "DATE_H",
            "DESC_H",
            "DEPOSIT_H",
            "WITHDRAWAL_H",
            "BALANCE_H",
            "AMOUNT_H",
            "GL_DEBIT_H",
            "GL_CREDIT_H",
            "GL_DOC_H",
            "GL_ACCOUNT_H",
        ):
            self.assertIsInstance(getattr(synonyms, name, None), set, f"missing dict {name}")

    def test_gl_inference_leaf_no_cycle(self):
        self.assertIsNone(getattr(gl_inference, "template_learning", None))
        for name in (
            "_map_gl_by_header",
            "_fill_gl_by_shape",
            "infer_gl_col_map",
            "validate_gl_shape",
        ):
            self.assertTrue(callable(getattr(gl_inference, name, None)), f"missing {name}")

    def test_seam_single_source(self):
        self.assertIs(tl.infer_gl_col_map, gl_inference.infer_gl_col_map)
        self.assertIs(tl._map_gl_by_header, gl_inference._map_gl_by_header)
        self.assertIs(tl._fill_gl_by_shape, gl_inference._fill_gl_by_shape)
        self.assertIs(tl.validate_gl_shape, gl_inference.validate_gl_shape)
        self.assertIs(tl.DATE_H, synonyms.DATE_H)
        self.assertIs(gl_inference._GL_KEYS, keys._GL_KEYS)

    def test_infer_gl_col_map_clear_header_high(self):
        rows = [
            ["Date", "Debit", "Credit"],
            ["2024-01-02", "100", "0"],
            ["2024-01-03", "0", "50"],
            ["2024-01-04", "20", "0"],
        ]
        idx, cm, conf, _r = gl_inference.infer_gl_col_map(rows)
        self.assertEqual(idx, 0)
        self.assertEqual(cm.get("date"), 0)
        self.assertEqual(cm.get("debit"), 1)
        self.assertEqual(cm.get("credit"), 2)
        self.assertEqual(conf, "high")

    def test_validate_gl_shape_requires_date_and_money(self):
        rows = [["Date", "Debit"], ["2024-01-02", "100"]]
        ok, _rate = gl_inference.validate_gl_shape(rows, 0, {"description": 0})  # 无 date/钱列
        self.assertFalse(ok)


if __name__ == "__main__":
    unittest.main()
