# -*- coding: utf-8 -*-
"""客户税号错录守护闸金标测试。核心金标 = 真实 SM 案例(2026-07-16 内测暴露):
登记 0105567178230,票上反复出现 0105567178203(相邻换位 03↔30),整批 direction_ambiguous。"""

from __future__ import annotations

import unittest

from services.workorder.taxid_guard import suspect_registered_typo

_SM_REGISTERED = "0105567178230"  # 敲反的(登记)
_SM_REAL = "0105567178203"  # 票上真税号
_SUPPLIER = "0125549007435"  # 卖方(MC Winner),噪声


class SuspectRegisteredTypoTests(unittest.TestCase):
    def test_sm_golden_transposition_detected(self):
        # 66 张进项票买方都是真税号 + 各自卖方税号当噪声。
        docs = [_SM_REAL] * 20 + [_SUPPLIER] * 20 + [None, "", "  "]
        s = suspect_registered_typo(_SM_REGISTERED, docs)
        self.assertIsNotNone(s)
        self.assertEqual(s.suspected, _SM_REAL)
        self.assertEqual(s.registered, _SM_REGISTERED)
        self.assertEqual(s.distance, 1)  # 换位算一步
        self.assertEqual(s.kind, "transposition")
        self.assertEqual(s.doc_count, 20)

    def test_no_suspicion_when_registered_matches(self):
        # 登记税号正确、锚得上一堆票 → 不打扰。
        docs = [_SM_REAL] * 20 + [_SUPPLIER] * 5
        self.assertIsNone(suspect_registered_typo(_SM_REAL, docs))

    def test_single_registered_hit_still_flags(self):
        # 个别票凑巧命中登记税号(OCR 读花),不该因 1 张命中就闭嘴。
        docs = [_SM_REGISTERED] + [_SM_REAL] * 10
        s = suspect_registered_typo(_SM_REGISTERED, docs)
        self.assertIsNotNone(s)
        self.assertEqual(s.suspected, _SM_REAL)

    def test_below_support_threshold_no_flag(self):
        # 候选只出现在 2 张票(< 3)→ 证据不足,不猜。
        docs = [_SM_REAL, _SM_REAL, _SUPPLIER]
        self.assertIsNone(suspect_registered_typo(_SM_REGISTERED, docs))

    def test_far_taxid_not_flagged(self):
        # 完全不同的税号(距离远)即便高频也不误报。
        docs = ["9999999999999"] * 30
        self.assertIsNone(suspect_registered_typo(_SM_REGISTERED, docs))

    def test_substitution_single_digit(self):
        reg = "0105567178203"
        wrong_on_docs = "0105567178204"  # 末位 3→4 单字错
        s = suspect_registered_typo(reg, [wrong_on_docs] * 5)
        self.assertIsNotNone(s)
        self.assertEqual(s.kind, "substitution")
        self.assertEqual(s.distance, 1)

    def test_dirty_inputs_cleaned(self):
        docs = ["0105-5671-782-03"] * 4  # 带横线
        s = suspect_registered_typo("0105567178230", docs)
        self.assertIsNotNone(s)
        self.assertEqual(s.suspected, _SM_REAL)

    def test_invalid_registered_returns_none(self):
        self.assertIsNone(suspect_registered_typo("123", [_SM_REAL] * 5))
        self.assertIsNone(suspect_registered_typo(None, [_SM_REAL] * 5))

    def test_picks_most_supported_candidate(self):
        # 两个近似候选,取支持度高的。
        near1 = "0105567178203"  # 换位,20 张
        near2 = "0105567178231"  # 末位 0→1,5 张
        docs = [near1] * 20 + [near2] * 5
        s = suspect_registered_typo("0105567178230", docs)
        self.assertEqual(s.suspected, near1)


if __name__ == "__main__":
    unittest.main()
