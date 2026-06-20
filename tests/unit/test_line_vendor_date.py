# -*- coding: utf-8 -*-
"""LINE 单笔路 卖家+相对日期 平价(#9)守门测试。

锁定:L1 parse_expense 也抽卖家(品牌字典 + 中文「在X买」)与相对日期(今天/昨天/前天/N天前),
与多笔 LLM 路对齐;无线索时卖家为空(不乱填)。"""

import unittest
from datetime import date, timedelta

from services.expense.line_quick_entry import (
    _extract_item_name,
    _extract_vendor,
    parse_expense,
)


def _d(n):
    return (date.today() - timedelta(days=n)).isoformat()


class VendorTests(unittest.TestCase):
    def test_brand_dict(self):
        self.assertEqual(_extract_vendor("昨天在星巴克买咖啡60"), "Starbucks")
        self.assertEqual(_extract_vendor("ที่เซเว่นซื้อน้ำ 20"), "7-Eleven")
        self.assertEqual(_extract_vendor("เติมน้ำมัน ปตท 1000"), "PTT")
        self.assertEqual(_extract_vendor("grab ไปสนามบิน 250"), "Grab")

    def test_zh_at_pattern(self):
        self.assertEqual(_extract_vendor("在小卖部买水10"), "小卖部")
        self.assertEqual(_extract_vendor("在楼下便利店花了35"), "楼下便利店")

    def test_no_cue_empty(self):
        self.assertEqual(_extract_vendor("ค่าน้ำ 50"), "")
        self.assertEqual(_extract_vendor("电费 800"), "")


class ParseExpenseParityTests(unittest.TestCase):
    def test_vendor_and_date_into_draft(self):
        d = parse_expense("昨天在星巴克买咖啡60")
        self.assertEqual(d.vendor_name, "Starbucks")
        self.assertEqual(d.doc_date, _d(1))
        self.assertEqual(str(d.amount), "60")

    def test_relative_dates(self):
        self.assertEqual(parse_expense("前天买菜50").doc_date, _d(2))
        self.assertEqual(parse_expense("3天前打车100").doc_date, _d(3))
        self.assertEqual(parse_expense("今天ค่าน้ำ50").doc_date, _d(0))

    def test_plain_no_vendor(self):
        d = parse_expense("ค่าไฟ 800")
        self.assertEqual(d.vendor_name, "")


class B2VendorItemDisambiguationTests(unittest.TestCase):
    """Phase B-2 供应商/商品/金额消歧场景矩阵(扩词典 + 从品名剥供应商 + 纯数字店号守卫)。"""

    def test_tops_unmarked(self):
        # 「tops 水 20」无标记 → 供应商 Tops · 品名 水 · 金额 20(治 tops 混进品名)
        d = parse_expense("tops 水 20")
        self.assertEqual(d.vendor_name, "Tops")
        self.assertEqual(d.note, "水")
        self.assertEqual(str(d.amount), "20")

    def test_at_tops_buy_water(self):
        d = parse_expense("在tops买水20")
        self.assertEqual(d.vendor_name, "Tops")
        self.assertEqual(d.note, "水")  # tops 剥掉

    def test_711_bare_number_is_store_not_amount(self):
        # 「711 咖啡30」→ 供应商 7-Eleven·裸「711」当店号(不被当金额)·金额 30
        d = parse_expense("711 咖啡30")
        self.assertEqual(d.vendor_name, "7-Eleven")
        self.assertEqual(str(d.amount), "30")
        self.assertEqual(d.note, "咖啡")

    def test_7_11_dash(self):
        self.assertEqual(_extract_vendor("7-11 咖啡30"), "7-Eleven")

    def test_711_single_send_vendor_shows(self):
        # Phase B 尾巴:纯数字「711」单发记账 → 卖家 7-Eleven 正常显示(is_known_brand 守卫·不回归)
        self.assertEqual(_extract_vendor("711 咖啡"), "7-Eleven")
        d = parse_expense("711 咖啡 35")
        self.assertEqual(d.vendor_name, "7-Eleven")

    def test_chain_brands(self):
        self.assertEqual(_extract_vendor("Villa Market 牛奶80"), "Villa Market")
        self.assertEqual(_extract_vendor("foodland 牛奶80"), "Foodland")
        self.assertEqual(_extract_vendor("ฟู้ดแลนด์ นม 80"), "Foodland")
        self.assertEqual(_extract_vendor("วัตสัน ยา 120"), "Watsons")

    def test_no_store_no_vendor(self):
        # 「咖啡 65」无店 → 不编供应商 · 品名 咖啡
        d = parse_expense("咖啡 65")
        self.assertEqual(d.vendor_name, "")
        self.assertEqual(d.note, "咖啡")

    def test_unknown_store_l1_empty_keeps_item(self):
        # 生面孔「ABCmart 鞋990」→ L1 不认 → 供应商空(交大脑)·品名不丢(回落原文不为空)
        d = parse_expense("ABCmart 鞋990")
        self.assertEqual(d.vendor_name, "")  # L1 不乱编
        self.assertTrue(d.note)  # 品名仍在(鞋 / 原文)
        self.assertEqual(str(d.amount), "990")

    def test_item_name_strips_new_brands(self):
        self.assertEqual(_extract_item_name("tops 水 20"), "水")
        self.assertEqual(_extract_item_name("Villa Market 牛奶80"), "牛奶")


if __name__ == "__main__":
    unittest.main()
