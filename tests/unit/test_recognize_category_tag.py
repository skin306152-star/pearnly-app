# -*- coding: utf-8 -*-
"""识别科目标签归到本套账分类树(泰语)· 纯单测(无 DB/无 LLM)。

守约:命中用套账泰语科目名、模型分类词跨语言映射、都不中留空(绝不落模型原始中文)。
"""

import unittest

from services.ocr.recognize import category_tag


# 预设风格的两级科目树(泰语名·同生产 seed_presets 口径)
TREE = [
    {
        "id": "p_food",
        "name": "ค่าอาหารและรับรอง",
        "children": [{"id": "c_food", "name": "ค่าอาหาร/เครื่องดื่ม"}],
    },
    {
        "id": "p_goods",
        "name": "ซื้อสินค้า/วัตถุดิบ",
        "children": [{"id": "c_goods", "name": "สินค้าสำเร็จรูป"}],
    },
]


class ResolveTagTests(unittest.TestCase):
    def test_vendor_keyword_hits_tenant_thai_category(self):
        # 卖方 Cafe Amazon → 餐饮规则 → 落套账泰语子类名(不是中文)
        tag = category_tag.resolve_tag({"seller_name": "Cafe Amazon", "items": []}, TREE)
        self.assertEqual(tag, "ค่าอาหาร/เครื่องดื่ม")

    def test_item_keyword_hits(self):
        tag = category_tag.resolve_tag(
            {"seller_name": "", "items": [{"name": "กาแฟลาเต้"}]}, TREE
        )
        self.assertEqual(tag, "ค่าอาหาร/เครื่องดื่ม")

    def test_model_chinese_word_maps_to_tenant_thai(self):
        # 关键词不中,但模型吐的中文"餐饮" → 跨语言映射到套账泰语科目(不原样落中文)
        tag = category_tag.resolve_tag(
            {"seller_name": "ร้านไม่รู้จัก", "items": [], "category": "餐饮"}, TREE
        )
        self.assertEqual(tag, "ค่าอาหาร/เครื่องดื่ม")

    def test_no_match_returns_none_not_model_chinese(self):
        # 都不中 → None(留空);绝不把模型的"化妆品"原样落下
        tag = category_tag.resolve_tag(
            {"seller_name": "XYZ Unknown", "items": [], "category": "化妆品"}, TREE
        )
        self.assertIsNone(tag)

    def test_empty_tree_returns_none(self):
        self.assertIsNone(category_tag.resolve_tag({"seller_name": "Cafe Amazon"}, []))
        self.assertIsNone(category_tag.resolve_tag({"seller_name": "Cafe Amazon"}, None))

    def test_item_descriptions_joins_names(self):
        d = category_tag.item_descriptions({"items": [{"name": "A"}, {"description": "B"}]})
        self.assertEqual(d, "A B")
        self.assertEqual(category_tag.item_descriptions({}), "")


if __name__ == "__main__":
    unittest.main()
