# -*- coding: utf-8 -*-
"""换模型 A/B 实弹工具的两把纯判据守门(不打网络、不碰语料)。

这两个函数是"无人工真值也能判谁读错"的全部依据,判据本身错了整轮对照就是废的。
"""

from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

_MOD = Path(__file__).resolve().parents[2] / "scripts" / "_model_ab_livefire.py"
_spec = importlib.util.spec_from_file_location("_model_ab_livefire", _MOD)
mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(mod)


class TaxIdChecksumTests(unittest.TestCase):
    def test_real_tax_ids_pass(self):
        # 真值语料里的商户税号(_vision_ablation_corpus/real 人工核对过)
        for tax_id in ("0105535134278", "0107561000013", "0105567178203"):
            self.assertTrue(mod.taxid_valid(tax_id), tax_id)

    def test_single_digit_typo_fails(self):
        self.assertFalse(mod.taxid_valid("0105535134279"))

    def test_wrong_length_or_empty_fails(self):
        for bad in ("", None, "12345", "010553513427800"):
            self.assertFalse(mod.taxid_valid(bad))

    def test_separators_tolerated(self):
        self.assertTrue(mod.taxid_valid("0-1055-35134-27-8"))


class MoneySelfConsistencyTests(unittest.TestCase):
    def test_balanced_receipt_ok(self):
        self.assertTrue(
            mod.money_self_consistent({"subtotal": "65.42", "vat": "4.58", "total_amount": "70.00"})
        )

    def test_off_by_one_digit_caught(self):
        self.assertFalse(
            mod.money_self_consistent(
                {"subtotal": "654.20", "vat": "4.58", "total_amount": "70.00"}
            )
        )

    def test_missing_field_is_unknown_not_wrong(self):
        self.assertIsNone(mod.money_self_consistent({"subtotal": "65.42", "total_amount": "70.00"}))

    def test_thousands_separator_parsed(self):
        self.assertTrue(
            mod.money_self_consistent(
                {"subtotal": "3,268.22", "vat": "228.78", "total_amount": "3,497.00"}
            )
        )

    def test_two_cent_rounding_tolerated(self):
        self.assertTrue(
            mod.money_self_consistent({"subtotal": "65.42", "vat": "4.60", "total_amount": "70.00"})
        )


if __name__ == "__main__":
    unittest.main()
