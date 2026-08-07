# -*- coding: utf-8 -*-
"""明细行归组双轨(services/stockcard/grouping.py)。"""

from __future__ import annotations

import unittest

from services.stockcard import grouping


class GroupKeyTests(unittest.TestCase):
    def test_product_id_wins_over_description(self):
        key = grouping.group_key(product_id="abc-123", description="随便写点什么")
        self.assertEqual(key, "p:abc-123")

    def test_falls_back_to_cleaned_name_when_no_product(self):
        key = grouping.group_key(product_id=None, description="  Coffee   Bean  ")
        self.assertEqual(key, "n:Coffee Bean")

    def test_two_lines_with_same_cleaned_name_land_in_same_group(self):
        k1 = grouping.group_key(product_id=None, description="TW Coffee Bean")
        k2 = grouping.group_key(product_id=None, description="Coffee   Bean")
        self.assertEqual(k1, k2)

    def test_unreadable_name_has_no_group(self):
        self.assertIsNone(grouping.group_key(product_id=None, description="???"))

    def test_empty_description_has_no_group(self):
        self.assertIsNone(grouping.group_key(product_id=None, description=""))

    def test_different_names_land_in_different_groups(self):
        k1 = grouping.group_key(product_id=None, description="ผ้าไหม")
        k2 = grouping.group_key(product_id=None, description="ผ้าฝ้าย")
        self.assertNotEqual(k1, k2)


class KeyRoundTripTests(unittest.TestCase):
    def test_is_product_key(self):
        self.assertTrue(grouping.is_product_key("p:123"))
        self.assertFalse(grouping.is_product_key("n:abc"))

    def test_key_product_id_extracts_id(self):
        self.assertEqual(grouping.key_product_id("p:abc-123"), "abc-123")
        self.assertIsNone(grouping.key_product_id("n:abc"))

    def test_key_name_extracts_name(self):
        self.assertEqual(grouping.key_name("n:Coffee Bean"), "Coffee Bean")
        self.assertIsNone(grouping.key_name("p:abc"))


if __name__ == "__main__":
    unittest.main()
