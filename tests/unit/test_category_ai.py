# -*- coding: utf-8 -*-
"""图片路 LLM 兜底归类(PO-9):只在真实科目里选编号,不臆造;任何不确定 → (None, None)。"""

import unittest
from unittest import mock

from services.expense import category_ai

_TREE = [
    {
        "id": "p1",
        "name": "餐饮 & 招待",
        "children": [{"id": "c1", "name": "餐费"}, {"id": "c2", "name": "招待"}],
    },
    {"id": "p2", "name": "水电杂费", "children": [{"id": "c3", "name": "水费"}]},
]


def _suggest(choice, **kw):
    with mock.patch(
        "services.ocr.layer2_gemini._call_gemini_with_retry", return_value=({"choice": choice}, {})
    ):
        with mock.patch("services.ocr.gemini_models.flash", return_value="m"):
            return category_ai.suggest_category(
                "ร้านอาหารทะเล", "กุ้ง / ปลา", _TREE, api_key="k", **kw
            )


class SuggestTests(unittest.TestCase):
    def test_picks_mapped_subcategory(self):
        self.assertEqual(_suggest(1), ("p1", "c1"))  # 选项1 = 餐饮 > 餐费
        self.assertEqual(_suggest(3), ("p2", "c3"))  # 选项3 = 水电 > 水费

    def test_zero_means_none(self):
        self.assertEqual(_suggest(0), (None, None))

    def test_out_of_range_none(self):
        self.assertEqual(_suggest(99), (None, None))

    def test_no_key_skips_llm(self):
        # 无 key → 不调 LLM,直接 (None,None)。
        with mock.patch("services.ocr.layer2_gemini._call_gemini_with_retry") as called:
            self.assertEqual(
                category_ai.suggest_category("v", "i", _TREE, api_key=None), (None, None)
            )
            called.assert_not_called()

    def test_empty_tree_none(self):
        self.assertEqual(category_ai.suggest_category("v", "i", [], api_key="k"), (None, None))

    def test_llm_failure_none(self):
        with mock.patch(
            "services.ocr.layer2_gemini._call_gemini_with_retry", side_effect=RuntimeError("boom")
        ):
            with mock.patch("services.ocr.gemini_models.flash", return_value="m"):
                self.assertEqual(
                    category_ai.suggest_category("v", "i", _TREE, api_key="k"), (None, None)
                )


class RuleCategoryTests(unittest.TestCase):
    TREE = [
        {
            "id": "p1",
            "name": "ค่าเดินทางและขนส่ง",
            "children": [
                {"id": "c1", "name": "ค่าน้ำมันเชื้อเพลิง"},
                {"id": "c2", "name": "ค่าแท็กซี่/แกร็บ"},
            ],
        },
        {
            "id": "p_food",
            "name": "ค่าอาหารและรับรอง",
            "children": [{"id": "c_food", "name": "ค่าอาหาร/เครื่องดื่ม"}],
        },
        {
            "id": "p2",
            "name": "ค่าสาธารณูปโภค",
            "children": [{"id": "c3", "name": "ค่าไฟฟ้า"}, {"id": "c4", "name": "ค่าน้ำประปา"}],
        },
    ]

    def _r(self, v, d):
        return category_ai.rule_category(v, d, self.TREE)

    def test_fuel_station_to_fuel(self):
        self.assertEqual(self._r("BANGCHAK BGN", "ไฮดีเซล S"), ("p1", "c1"))

    def test_grab_to_taxi(self):
        self.assertEqual(self._r("Grab", "ค่าโดยสาร"), ("p1", "c2"))

    def test_electric_to_utility(self):
        self.assertEqual(self._r("การไฟฟ้าส่วนภูมิภาค", "ค่าไฟฟ้า"), ("p2", "c3"))

    def test_food_items_override_fuel_station_vendor(self):
        self.assertEqual(
            self._r("บมจ. ปตท. น้ำมันและการค้าปลีก", "TW แบล็คคอฟฟี่ เย็น"),
            ("p_food", "c_food"),
        )

    def test_restaurant_vendor_to_food(self):
        self.assertEqual(self._r("Little Betong", "ไก่ทอดเบตง"), ("p_food", "c_food"))

    def test_unknown_tree_name_falls_through(self):
        self.assertEqual(
            category_ai.rule_category("BANGCHAK", "diesel", [{"name": "X"}]), (None, None)
        )


if __name__ == "__main__":
    unittest.main()
