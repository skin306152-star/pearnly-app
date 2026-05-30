#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/integration/test_erp_matching_safety_net.py · REFACTOR-WC

ERP 名称匹配核心安全网 · 纯加测试不改业务 · 给 A 拆 mrerp_*_sync 当保险。

锁定 services/erp/_matching —— 公司名/商品名归一 + Levenshtein 距离/比率 + fuzzy_match。
这是 customer_sync 与 product_sync 的 L2/L3 查找层共用地基:归一写坏 → 真客户/商品
匹配不上(漏)或错配(错买方/错商品码 · 红线)。

现有 test_mrerp_*_sync 的 fuzzy 路径要真 sandbox 凭据 + Playwright → CI 默认 skip,
盖不到这层纯函数。A mrerp mixin 拆分两度翻车已转覆盖优先 —— 本文件把最底层焊死
(0 凭据 · 0 浏览器 · 0 DB · CI 真跑不 skip),拆分把 matching helper 搬串立刻红。

覆盖维度(对应 loop「给 A 新拆模块补集成测试 / 不误配」):
  1. normalize_company_name — 去法人后缀(Co./Ltd.)+ NFKC 全角归一 + 标点折空格 + casefold
  2. normalize_item_name — 不去法人后缀(商品名保留全词)· 与 company 的关键区别
  3. levenshtein / levenshtein_ratio — 距离与相似比率边界(空串语义)
  4. fuzzy_match — 阈值过滤 + 平局取首 + 跳 None + 空输入 None
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
        from services.erp import _matching
    except Exception as e:  # pragma: no cover - import 环境问题才触发
        raise unittest.SkipTest(f"services.erp._matching 不可 import:{e}")
    return _matching


class NormalizeCompanyNameTest(unittest.TestCase):
    """normalize_company_name · 去法人后缀 + NFKC + 标点折空格 + casefold"""

    def setUp(self) -> None:
        self.m = _load()

    def test_strips_english_legal_suffix(self) -> None:
        self.assertEqual(self.m.normalize_company_name("Skin Trading Co., Ltd."), "skin trading")

    def test_strips_repeated_double_suffix(self) -> None:
        # 'XYZ Co., Ltd. Company' → 反复剥到 'xyz'
        self.assertEqual(self.m.normalize_company_name("XYZ Co., Ltd. Company"), "xyz")

    def test_nfkc_unifies_fullwidth(self) -> None:
        # 全角字母数字 NFKC 归一 + casefold → 半角小写
        self.assertEqual(self.m.normalize_company_name("ＡＢＣ１２３"), "abc123")

    def test_punctuation_collapses_to_space(self) -> None:
        # 'T-Net' → 't net'(标点折空格 · 不直接删 · 与 'tnet' 仍可区分)
        self.assertEqual(self.m.normalize_company_name("T-Net"), "t net")
        self.assertNotEqual(
            self.m.normalize_company_name("T-Net"), self.m.normalize_company_name("TNet")
        )

    def test_empty_and_none(self) -> None:
        self.assertEqual(self.m.normalize_company_name(""), "")
        self.assertEqual(self.m.normalize_company_name(None), "")


class NormalizeItemNameTest(unittest.TestCase):
    """normalize_item_name · 不去法人后缀(与 company 的关键区别)"""

    def setUp(self) -> None:
        self.m = _load()

    def test_does_not_strip_legal_suffix(self) -> None:
        # 商品名保留 co/ltd(后缀对商品无意义 · 不剥)
        self.assertEqual(self.m.normalize_item_name("Widget Co., Ltd."), "widget co ltd")

    def test_company_strips_but_item_keeps_suffix(self) -> None:
        # 同输入:company 剥后缀 → 'acme'·item 留 → 'acme co ltd'· 二者必须不同
        company = self.m.normalize_company_name("Acme Co., Ltd.")
        item = self.m.normalize_item_name("Acme Co., Ltd.")
        self.assertEqual(company, "acme")
        self.assertNotEqual(company, item)

    def test_empty_and_none(self) -> None:
        self.assertEqual(self.m.normalize_item_name(""), "")
        self.assertEqual(self.m.normalize_item_name(None), "")


class LevenshteinTest(unittest.TestCase):
    """levenshtein / levenshtein_ratio · 距离与相似比率"""

    def setUp(self) -> None:
        self.m = _load()

    def test_identical_distance_zero(self) -> None:
        self.assertEqual(self.m.levenshtein("abc", "abc"), 0)

    def test_single_edits(self) -> None:
        self.assertEqual(self.m.levenshtein("abc", "abd"), 1)  # 替换
        self.assertEqual(self.m.levenshtein("abc", "abcd"), 1)  # 插入
        self.assertEqual(self.m.levenshtein("abc", "ab"), 1)  # 删除

    def test_distance_against_empty(self) -> None:
        self.assertEqual(self.m.levenshtein("abc", ""), 3)
        self.assertEqual(self.m.levenshtein("", "abc"), 3)

    def test_ratio_both_empty_is_one(self) -> None:
        self.assertEqual(self.m.levenshtein_ratio("", ""), 1.0)

    def test_ratio_one_empty_is_zero(self) -> None:
        self.assertEqual(self.m.levenshtein_ratio("a", ""), 0.0)

    def test_ratio_identical_is_one(self) -> None:
        self.assertEqual(self.m.levenshtein_ratio("skin", "skin"), 1.0)

    def test_ratio_one_edit_in_four(self) -> None:
        # 4 字符差 1 → 1 - 1/4 = 0.75
        self.assertAlmostEqual(self.m.levenshtein_ratio("abcd", "abce"), 0.75)


class FuzzyMatchTest(unittest.TestCase):
    """fuzzy_match · 阈值过滤 + 平局取首 + 跳 None + 空输入 None"""

    def setUp(self) -> None:
        self.m = _load()

    def test_best_above_threshold(self) -> None:
        out = self.m.fuzzy_match("skin trading", ["acme", "skin tradng", "skin trading co"], 0.8)
        self.assertIsNotNone(out)
        self.assertEqual(out[0], "skin tradng")
        self.assertGreaterEqual(out[1], 0.8)

    def test_none_when_all_below_threshold(self) -> None:
        self.assertIsNone(self.m.fuzzy_match("zzz", ["acme", "widget"], 0.8))

    def test_tie_goes_to_first_candidate(self) -> None:
        # 'ax' 与 'ay' 对 'ab' 比率相同 → 取首个 'ax'(严格大于才替换)
        out = self.m.fuzzy_match("ab", ["ax", "ay"], 0.4)
        self.assertEqual(out[0], "ax")

    def test_skips_none_candidates(self) -> None:
        out = self.m.fuzzy_match("acme", [None, "acme"], 0.9)
        self.assertEqual(out, ("acme", 1.0))

    def test_empty_query_or_candidates_returns_none(self) -> None:
        self.assertIsNone(self.m.fuzzy_match("", ["acme"], 0.5))
        self.assertIsNone(self.m.fuzzy_match("acme", [], 0.5))


if __name__ == "__main__":
    unittest.main(verbosity=2)
