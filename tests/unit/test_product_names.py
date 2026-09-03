import unittest
from pathlib import Path

from services.products.names import display_product_name, product_name_object, product_names


class ProductNameTests(unittest.TestCase):
    def test_primary_and_additional_names_keep_entry_order(self):
        row = {"name_th": "水", "name_en": "Water", "name_zh": "矿泉水"}
        self.assertEqual(product_names(row), ["水", "Water", "矿泉水"])
        self.assertEqual(display_product_name(row), "水 / Water / 矿泉水")

    def test_duplicate_names_only_display_once(self):
        row = {"name_th": "Coke", "name_en": "coke", "name_zh": "可乐"}
        self.assertEqual(display_product_name(row), "Coke / 可乐")

    def test_api_name_object_carries_stable_display_name(self):
        out = product_name_object({"name_th": "น้ำ", "name_en": "Water", "name_zh": None})
        self.assertEqual(out["display"], "น้ำ / Water")

    def test_home_helper_joins_names_in_primary_first_order(self):
        source = Path("src/home/product-names.ts").read_text(encoding="utf-8")
        self.assertIn("value.name_th ?? value.th", source)
        self.assertIn("names.join(' / ')", source)

    def test_pos_helper_is_a_separate_module_loaded_after_state(self):
        build = Path("scripts/build-home-js.mjs").read_text(encoding="utf-8")
        source = Path("static/pos/pos-product-names.js").read_text(encoding="utf-8")
        self.assertLess(build.index("'pos/pos-data.js'"), build.index("'pos/pos-product-names.js'"))
        self.assertIn("POS.pnm", source)


if __name__ == "__main__":
    unittest.main()
