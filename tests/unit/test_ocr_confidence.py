# -*- coding: utf-8 -*-
"""REFACTOR-WA 覆盖 · services/ocr/confidence.py 行为/边界

confidence.py 是 pipeline.py 触发器用的纯只读 helper(无 DB / 无副作用):
  - find_field_min_word_conf:取与字段值重叠的 L1 词里最低置信度(抓 Vision 单字误读)
  - check_field_in_l1_text:字段值是否真出现在 L1 文本(抓 L2 幻觉)
本测覆盖:归一化(空白/逗号/大小写)· MIN_OVERLAP_CHARS 边界 · 双向子串匹配 ·
多词取 min · 空值/过短早返 · 幻觉(不在文本)判定。0 逻辑改 · 只加测试。
"""

import unittest

from services.ocr.confidence import (
    find_field_min_word_conf,
    check_field_in_l1_text,
    MIN_OVERLAP_CHARS,
    _normalize,
)
from services.ocr.schemas import Page, Word
from services.ocr.schemas_layer1 import BoundingBox, Paragraph, Block


def _bbox():
    return BoundingBox(vertices=[(0, 0), (1, 0), (1, 1), (0, 1)])


def _word(text, conf):
    return Word(text=text, confidence=conf, bbox=_bbox())


def _page(words, full_text=""):
    """构造一个单 block / 单 paragraph 的 Page · 词表为 words。"""
    para = Paragraph(
        text=" ".join(w.text for w in words), confidence=1.0, bbox=_bbox(), words=words
    )
    block = Block(text=para.text, confidence=1.0, bbox=_bbox(), paragraphs=[para])
    return Page(
        page_number=1,
        width=100,
        height=100,
        full_text=full_text or para.text,
        avg_confidence=1.0,
        blocks=[block],
    )


class NormalizeTests(unittest.TestCase):
    def test_strips_whitespace_and_commas_and_lowercases(self):
        self.assertEqual(_normalize("AB, 12\t34"), "ab1234")

    def test_empty(self):
        self.assertEqual(_normalize(""), "")


class FindFieldMinWordConfTests(unittest.TestCase):
    def test_empty_value_returns_none(self):
        page = _page([_word("INV12345", 0.9)])
        self.assertIsNone(find_field_min_word_conf(page, ""))

    def test_value_shorter_than_threshold_returns_none(self):
        page = _page([_word("INV12345", 0.9)])
        # "ab" normalizes to len 2 < MIN_OVERLAP_CHARS → 不可靠匹配 · None
        self.assertLess(2, MIN_OVERLAP_CHARS + 1)
        self.assertIsNone(find_field_min_word_conf(page, "ab"))

    def test_no_matching_word_returns_none(self):
        page = _page([_word("HELLO", 0.9), _word("WORLD", 0.8)])
        self.assertIsNone(find_field_min_word_conf(page, "INV98765"))

    def test_exact_match_returns_word_conf(self):
        page = _page([_word("INV12345", 0.73)])
        self.assertAlmostEqual(find_field_min_word_conf(page, "INV12345"), 0.73)

    def test_takes_min_across_multiple_matches(self):
        # 字段值是两个词的子串方向匹配 · 取最低置信度
        page = _page([_word("INV12345", 0.91), _word("INV12345", 0.42)])
        self.assertAlmostEqual(find_field_min_word_conf(page, "INV12345"), 0.42)

    def test_field_value_substring_of_word(self):
        # word_norm 包含 val_norm(val 较短但 >= 阈值)
        page = _page([_word("PREFIX-INV12345-SUFFIX", 0.5)])
        self.assertAlmostEqual(find_field_min_word_conf(page, "INV12345"), 0.5)

    def test_word_substring_of_field_value(self):
        # val_norm 包含 word_norm · overlap = len(word_norm) 须 >= 阈值
        page = _page([_word("12345", 0.6)])
        self.assertAlmostEqual(find_field_min_word_conf(page, "INV-12345"), 0.6)

    def test_normalization_ignores_commas_and_case(self):
        page = _page([_word("1,234,567", 0.55)])
        self.assertAlmostEqual(find_field_min_word_conf(page, "1234567"), 0.55)

    def test_overlap_below_threshold_not_matched(self):
        # word "12" (len 2) 是 "123456" 子串但 overlap=2 < 阈值 → 不计
        page = _page([_word("12", 0.3)])
        self.assertIsNone(find_field_min_word_conf(page, "123456"))

    def test_blank_word_skipped(self):
        page = _page([_word("   ", 0.1), _word("INV12345", 0.8)])
        self.assertAlmostEqual(find_field_min_word_conf(page, "INV12345"), 0.8)


class CheckFieldInL1TextTests(unittest.TestCase):
    def test_empty_value_is_true(self):
        page = _page([_word("X", 0.9)], full_text="anything")
        self.assertTrue(check_field_in_l1_text(page, ""))

    def test_short_value_is_true(self):
        page = _page([_word("X", 0.9)], full_text="abc")
        self.assertTrue(check_field_in_l1_text(page, "ab"))

    def test_present_value_true(self):
        page = _page([], full_text="Invoice INV12345 dated")
        self.assertTrue(check_field_in_l1_text(page, "INV12345"))

    def test_present_after_normalization(self):
        page = _page([], full_text="total 1,234,567 baht")
        self.assertTrue(check_field_in_l1_text(page, "1234567"))

    def test_absent_value_false_hallucination(self):
        page = _page([], full_text="Invoice INV12345 dated")
        self.assertFalse(check_field_in_l1_text(page, "INV99999"))

    def test_none_full_text_treated_as_empty(self):
        page = Page(
            page_number=1,
            width=10,
            height=10,
            full_text="",
            avg_confidence=0.0,
            blocks=[],
        )
        self.assertFalse(check_field_in_l1_text(page, "INV12345"))


if __name__ == "__main__":
    unittest.main()
