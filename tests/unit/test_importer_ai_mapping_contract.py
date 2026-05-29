# -*- coding: utf-8 -*-
"""
REFACTOR-WA-B1 守门测试 · services/importer/keys.py + ai_mapping.py
(2026-05-29 从 template_learning 抽出 · 纯搬家 0 逻辑改 · 解 template_learning↔ai_mapping 循环)

锁定:
  1. keys 导出 _STMT_KEYS/_GL_KEYS/build_header_signature · 叶子(不 import template_learning)。
  2. ai_mapping 导出 ai_mapping_enabled/suggest_mapping_with_ai/_coerce_ai_cm ·
     叶子(只依赖 keys · 不 import template_learning · 防循环)。
  3. **patch seam**:template_learning.suggest_mapping_with_ai / ai_mapping_enabled 仍是
     template_learning 模块属性 · 且与 ai_mapping 同一对象(test_ai_mapping patch +
     bank_recon_v2 `_tl.suggest_mapping_with_ai` 都靠它)。
  4. build_header_signature / _GL_KEYS / _STMT_KEYS 在 keys / template_learning / ai_mapping 三处同一对象。
  5. suggest_mapping_with_ai 无 api_key / 关闭 → None;_coerce_ai_cm 缺 date 或钱列 → None。
"""

import inspect
import unittest

from services.importer import keys, ai_mapping
from services.importer import template_learning as tl


class ImporterKeysAiMappingContractTests(unittest.TestCase):
    def test_keys_exports_and_leaf(self):
        self.assertEqual(len(keys._STMT_KEYS), 6)
        self.assertIn("debit", keys._GL_KEYS)
        self.assertTrue(callable(keys.build_header_signature))
        # 叶子:没 import template_learning(否则它会是模块属性)· 防循环
        self.assertIsNone(getattr(keys, "template_learning", None))

    def test_ai_mapping_exports_and_leaf(self):
        for name in ("ai_mapping_enabled", "suggest_mapping_with_ai", "_coerce_ai_cm"):
            self.assertTrue(callable(getattr(ai_mapping, name, None)), f"missing {name}")
        # 防循环:绝不 import template_learning(否则它会是 ai_mapping 模块属性)
        self.assertIsNone(getattr(ai_mapping, "template_learning", None))

    def test_patch_seam_single_source(self):
        # template_learning 仍暴露这两个名(test_ai_mapping patch + bank_recon_v2 _tl. 靠它)
        self.assertIs(tl.suggest_mapping_with_ai, ai_mapping.suggest_mapping_with_ai)
        self.assertIs(tl.ai_mapping_enabled, ai_mapping.ai_mapping_enabled)

    def test_build_header_signature_single_source_three_ways(self):
        self.assertIs(tl.build_header_signature, keys.build_header_signature)
        self.assertIs(ai_mapping.build_header_signature, keys.build_header_signature)
        self.assertIs(tl._GL_KEYS, keys._GL_KEYS)
        self.assertIs(ai_mapping._STMT_KEYS, keys._STMT_KEYS)

    def test_suggest_returns_none_without_key(self):
        self.assertIsNone(
            ai_mapping.suggest_mapping_with_ai(
                "statement", "s", ["a", "b"], [["1", "2"]], api_key=""
            )
        )

    def test_coerce_ai_cm_requires_date_and_money(self):
        # 合法:date + amount
        self.assertEqual(
            ai_mapping._coerce_ai_cm({"date": 0, "amount": 1}, "statement", 3),
            {"date": 0, "amount": 1},
        )
        # 缺钱列 → None
        self.assertIsNone(ai_mapping._coerce_ai_cm({"date": 0, "description": 1}, "statement", 3))
        # 越界列号被剔除 → 仅剩 date 无钱列 → None
        self.assertIsNone(ai_mapping._coerce_ai_cm({"date": 0, "amount": 9}, "statement", 3))


if __name__ == "__main__":
    unittest.main()
