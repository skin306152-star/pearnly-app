# -*- coding: utf-8 -*-
"""发票号格式一致性检测单测 · 钉住"同批不一致揪异常、不误杀"的行为。

回归锚:SINCERE.pdf 三票 IV69100179 / IV69100189 / IV69/00199 —— 前两张无斜杠、
第三张有斜杠,至少一张读错却满置信度溜过。此测试把"该揪出第三张"钉死,防再回归。
"""

import unittest

from services.ocr.invoice_no import (
    format_signature,
    format_warnings_for_groups,
    inconsistent_in_batch,
    inconsistent_indices,
)


class FormatSignatureTests(unittest.TestCase):
    def test_letters_digits_separators(self):
        self.assertEqual(format_signature("IV69/00199"), "AA99/99999")
        self.assertEqual(format_signature("IV69100179"), "AA99999999")
        self.assertEqual(format_signature(" iv-1 "), "AA-9")
        self.assertEqual(format_signature(None), "")


class InconsistentIndicesTests(unittest.TestCase):
    def test_sincere_batch_flags_the_odd_slash(self):
        # 多数派无斜杠 → 揪出有斜杠的第三张(下标 2)
        nums = ["IV69100179", "IV69100189", "IV69/00199"]
        self.assertEqual(inconsistent_indices(nums), [2])

    def test_all_same_format_no_flag(self):
        self.assertEqual(inconsistent_indices(["A/1", "B/2", "C/3"]), [])

    def test_two_items_tie_no_guess(self):
        # 只有两张且格式各异 → 无法判谁错,不误杀
        self.assertEqual(inconsistent_indices(["IV1", "IV/2"]), [])

    def test_single_or_empty_no_flag(self):
        self.assertEqual(inconsistent_indices(["IV1"]), [])
        self.assertEqual(inconsistent_indices([]), [])

    def test_blanks_skipped(self):
        # 空号不参与格式裁定(缺号是另一回事)→ 剩两张非空且各异 = 平票不判
        self.assertEqual(inconsistent_indices(["IV69100179", "", "IV69/00199"]), [])

    def test_majority_needs_over_half(self):
        # 4 张:2 无斜杠 + 2 各自不同 → 无严格过半多数派,不乱判
        self.assertEqual(inconsistent_indices(["AA9", "AA9", "A/9", "9-9"]), [])

    def test_clear_majority_three_vs_one(self):
        nums = ["INV99", "INV98", "INV97", "IN/96"]
        self.assertEqual(inconsistent_indices(nums), [3])


class InconsistentInBatchTests(unittest.TestCase):
    def test_same_seller_flags_odd(self):
        nums = ["IV69100179", "IV69100189", "IV69/00199"]
        sellers = ["0105546015062"] * 3
        self.assertEqual(inconsistent_in_batch(nums, sellers), [2])

    def test_two_sellers_each_consistent_no_flag(self):
        # 卖家A两张无斜杠 + 卖家B两张带斜杠 · 各组内自洽 → 不跨卖家误杀
        nums = ["IV1", "IV2", "RR/1", "RR/2"]
        sellers = ["0105546015062", "0105546015062", "0999999999999", "0999999999999"]
        self.assertEqual(inconsistent_in_batch(nums, sellers), [])

    def test_seller_tax_format_agnostic(self):
        # 卖家税号带不带横线视为同一卖家
        nums = ["IV99", "IV98", "I/97"]
        sellers = ["0-1055-46015-06-2", "0105546015062", "0105546015062"]
        self.assertEqual(inconsistent_in_batch(nums, sellers), [2])

    def test_missing_sellers_falls_back(self):
        nums = ["IV99", "IV98", "I/97"]
        self.assertEqual(inconsistent_in_batch(nums, None), [2])

    def test_unknown_seller_each_isolated(self):
        # 无税号的票各自成组 → 永不被裁(无法判孤票)
        nums = ["IV99", "IV98", "I/97"]
        self.assertEqual(inconsistent_in_batch(nums, ["", "", ""]), [])


class FormatWarningsForGroupsTests(unittest.TestCase):
    def _grp(self, no, tax):
        return {"invoice_fields": {"invoice_number": no, "seller_tax": tax}}

    def test_sincere_three_invoices_flags_odd(self):
        groups = [
            self._grp("IV69100179", "0105546015062"),
            self._grp("IV69100189", "0105546015062"),
            self._grp("IV69/00199", "0105546015062"),
        ]
        out = format_warnings_for_groups(groups)
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0]["invoice_index"], 3)
        self.assertEqual(out[0]["invoice_number"], "IV69/00199")
        self.assertEqual(out[0]["reason"], "invoice_number_format_inconsistent")

    def test_consistent_batch_no_warning(self):
        groups = [
            self._grp("IV69100179", "0105546015062"),
            self._grp("IV69100189", "0105546015062"),
            self._grp("IV69100199", "0105546015062"),
        ]
        self.assertEqual(format_warnings_for_groups(groups), [])

    def test_empty_or_single_no_warning(self):
        self.assertEqual(format_warnings_for_groups([]), [])
        self.assertEqual(format_warnings_for_groups([self._grp("IV1", "0105546015062")]), [])


if __name__ == "__main__":
    unittest.main()
