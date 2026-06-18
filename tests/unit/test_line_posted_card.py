# -*- coding: utf-8 -*-
"""入账成功 / 当前状态数据卡(P1G):详情 → 卡片字段映射 + posted 卡构建。"""

import unittest

from services.line_binding import line_posted_card as pc


def _detail():
    return {
        "doc": {
            "id": "abc123def456",
            "grand_total": "190.00",
            "doc_date": "2026-06-18",
            "doc_no": "INV-1",
            "payment_method": "cash",
            "subtotal": "177.57",
            "vat_amount": "12.43",
        },
        "supplier": {"name": "7-11", "tax_id": "1234567890123", "address": "Bangkok"},
        "lines": [
            {"description": "กาแฟ", "line_total": "70"},
            {"description": "ข้าว", "line_total": "120"},
            {"description": "", "line_total": "0"},  # 空描述行不上卡
        ],
    }


class FieldsFromDetailTests(unittest.TestCase):
    def test_maps_core_fields(self):
        f = pc.fields_from_detail(_detail())
        self.assertEqual(f["date"], "2026-06-18")
        self.assertEqual(f["vendor"], "7-11")
        self.assertEqual(f["seller_tax"], "1234567890123")
        self.assertEqual(f["invoice_number"], "INV-1")
        self.assertEqual(f["payment_method"], "cash")
        self.assertEqual(f["vat"], "12.43")

    def test_items_skip_empty_description(self):
        f = pc.fields_from_detail(_detail())
        self.assertEqual([it["name"] for it in f["items"]], ["กาแฟ", "ข้าว"])

    def test_empty_detail_no_crash(self):
        f = pc.fields_from_detail({})
        self.assertEqual(f["vendor"], "")
        self.assertEqual(f["items"], [])


class BuildTests(unittest.TestCase):
    def test_posted_card_has_status_amount_and_actions(self):
        card = pc.build(_detail(), doc_id="abc123def456", lang="zh")
        self.assertEqual(card["type"], "flex")
        blob = str(card)
        self.assertIn("已保存", blob)  # 状态徽章
        self.assertIn("190.00", blob)  # 金额
        self.assertIn("查看详情", blob)  # ดูรายการ
        self.assertIn("撤销", blob)  # ยกเลิก
        self.assertIn("DEF456", blob)  # 记录号(末 6 位大写)

    def test_thai_lang(self):
        card = pc.build(_detail(), doc_id="abc123def456", lang="th")
        self.assertIn("บันทึกแล้ว", str(card))


if __name__ == "__main__":
    unittest.main()
