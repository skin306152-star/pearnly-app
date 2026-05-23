#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/unit/test_mrerp_matching.py

Unit tests for services/erp/_matching.py: Levenshtein + Thai/English/
Chinese legal-suffix normalization (P1-B Phase 1).
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from services.erp._matching import (  # noqa: E402
    fuzzy_match,
    levenshtein,
    levenshtein_ratio,
    normalize_company_name,
    normalize_item_name,
)


class LevenshteinTests(unittest.TestCase):

    def test_identical_strings(self):
        self.assertEqual(levenshtein("abc", "abc"), 0)
        self.assertEqual(levenshtein("", ""), 0)

    def test_one_substitution(self):
        self.assertEqual(levenshtein("kitten", "sitten"), 1)

    def test_classic_example(self):
        self.assertEqual(levenshtein("kitten", "sitting"), 3)

    def test_insertion_deletion(self):
        self.assertEqual(levenshtein("abc", "abcd"), 1)
        self.assertEqual(levenshtein("abcd", "abc"), 1)

    def test_empty_vs_word(self):
        self.assertEqual(levenshtein("", "abc"), 3)
        self.assertEqual(levenshtein("abc", ""), 3)

    def test_ratio_identical(self):
        self.assertAlmostEqual(levenshtein_ratio("abc", "abc"), 1.0)

    def test_ratio_completely_different(self):
        # No characters overlap — distance = max(len) → ratio = 0.0
        self.assertAlmostEqual(levenshtein_ratio("abc", "xyz"), 0.0)

    def test_ratio_one_typo_in_short(self):
        # 1 char off out of 6 → 1 - 1/6 = 0.833...
        self.assertAlmostEqual(
            levenshtein_ratio("kitten", "sitten"),
            1 - 1 / 6,
        )

    def test_ratio_both_empty(self):
        self.assertEqual(levenshtein_ratio("", ""), 1.0)

    def test_ratio_one_empty(self):
        # max len = 3, distance = 3 → ratio = 0
        self.assertEqual(levenshtein_ratio("abc", ""), 0.0)


class CompanyNormalizationTests(unittest.TestCase):

    def test_strip_thai_company_prefix_suffix(self):
        # "บริษัท ABC จำกัด" → "abc"
        norm = normalize_company_name("บริษัท ABC จำกัด")
        # "บริษัท" is a prefix per Thai grammar but our stripper only
        # strips suffixes — at minimum "จำกัด" should be gone.
        self.assertNotIn("จำกัด", norm)
        self.assertIn("abc", norm)

    def test_strip_english_ltd(self):
        self.assertEqual(
            normalize_company_name("Skin Trading Co., Ltd."),
            "skin trading",
        )
        self.assertEqual(
            normalize_company_name("Skin Trading Co.,Ltd"),
            "skin trading",
        )
        self.assertEqual(
            normalize_company_name("Skin Trading Co Ltd"),
            "skin trading",
        )

    def test_strip_chinese_youxian_gongsi(self):
        # "丰华有限公司" → "丰华"
        out = normalize_company_name("丰华有限公司")
        self.assertEqual(out, "丰华")

    def test_casefold_unicode(self):
        # SS in German ß casefolds to ss; doesn't matter here but
        # confirms .casefold() is applied (vs lower()).
        self.assertEqual(
            normalize_company_name("STRASSE"),
            normalize_company_name("Straße"),
        )

    def test_collapse_punctuation_and_whitespace(self):
        self.assertEqual(
            normalize_company_name("Pearnly  ,  Inc."),
            "pearnly",
        )

    def test_handles_none_and_empty(self):
        self.assertEqual(normalize_company_name(None), "")
        self.assertEqual(normalize_company_name(""), "")
        self.assertEqual(normalize_company_name("   "), "")

    def test_repeated_suffix_strip(self):
        # "ABC Co., Ltd. Inc." should peel both ".Inc" and "Co.,Ltd."
        out = normalize_company_name("ABC Co., Ltd. Inc.")
        self.assertEqual(out, "abc")


class ItemNormalizationTests(unittest.TestCase):

    def test_basic(self):
        self.assertEqual(normalize_item_name("Coca-Cola 330ml"), "coca cola 330ml")

    def test_punctuation_collapse(self):
        self.assertEqual(normalize_item_name("Item / 1"), "item 1")

    def test_handles_none(self):
        self.assertEqual(normalize_item_name(None), "")


class FuzzyMatchTests(unittest.TestCase):

    def test_perfect_match(self):
        out = fuzzy_match("abc", ["xyz", "abc", "def"], threshold=0.5)
        self.assertEqual(out, ("abc", 1.0))

    def test_returns_best_above_threshold(self):
        # "skin trading" vs "skn trading" → 1 char diff out of 12 → 0.917
        out = fuzzy_match(
            "skin trading",
            ["pearnly", "skn trading", "abc"],
            threshold=0.85,
        )
        self.assertIsNotNone(out)
        self.assertEqual(out[0], "skn trading")
        self.assertGreater(out[1], 0.85)

    def test_below_threshold_returns_none(self):
        out = fuzzy_match("abc", ["xyz"], threshold=0.5)
        self.assertIsNone(out)

    def test_empty_inputs(self):
        self.assertIsNone(fuzzy_match("", ["abc"], 0.5))
        self.assertIsNone(fuzzy_match("abc", [], 0.5))


if __name__ == "__main__":
    unittest.main(verbosity=2)
