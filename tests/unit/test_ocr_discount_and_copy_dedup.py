# -*- coding: utf-8 -*-
"""折扣勾稽 + 双联明细去重守门(2026-07-03 真票实案回归)。

两个生产实锤(账号 18685123459@163.com 当日识别·prod 落库原样为夹具):
  · INV2026030003:票面折扣 ฿140 漏抓 → 存下 小计5210+VAT354.90≠总额5424.90,
    自己勾稽不平却 conf=high 静默入账。
  · INV2026030002:同票双联(两页),第一联被 OCR 读出碎空格/数量缺单位词,
    去重双双失手 → 真 5 行存成 10 行。
"""

import unittest
from types import SimpleNamespace

from services.ocr import invoice_grouper as ig
from services.ocr import triggers as t
from services.ocr.sanity import evaluate_sanity, infer_missing_discount


def _inv(**kw):
    base = dict(
        is_not_invoice=False,
        document_type="tax_invoice",
        invoice_number="INV1",
        subtotal="",
        vat="",
        total_amount="",
        discount="",
        seller_tax="",
        buyer_tax="",
        items=[],
        additional_invoices=[],
    )
    base.update(kw)
    return SimpleNamespace(**base)


class DiscountInferenceTests(unittest.TestCase):
    def test_f003_real_case_infers_140(self):
        # 小计5210 + VAT354.90 − 总额5424.90 = 140,且 (5210−140)×7% = 354.90 双重勾稽成立
        inv = _inv(subtotal="5210.00", vat="354.90", total_amount="5424.90")
        note = infer_missing_discount(inv)
        self.assertIsNotNone(note)
        self.assertIn("140.00", note)
        self.assertEqual(inv.discount, "140.00")
        # 回填后整票勾稽平 → 硬闸放行
        self.assertEqual(evaluate_sanity(inv), [])

    def test_no_inference_when_vat_cross_check_fails(self):
        # 差额 124.90 但 (5210−124.90)×7% ≠ 230 → 单一差额不动手(可能是选错列)
        inv = _inv(subtotal="5210.00", vat="230.00", total_amount="5315.10")
        self.assertIsNone(infer_missing_discount(inv))
        self.assertEqual(inv.discount, "")

    def test_no_inference_when_discount_present(self):
        inv = _inv(subtotal="5210.00", vat="354.90", total_amount="5424.90", discount="140")
        self.assertIsNone(infer_missing_discount(inv))
        self.assertEqual(inv.discount, "140")

    def test_no_inference_when_balanced(self):
        inv = _inv(subtotal="100.00", vat="7.00", total_amount="107.00")
        self.assertIsNone(infer_missing_discount(inv))

    def test_not_invoice_shortcircuits(self):
        inv = _inv(is_not_invoice=True, subtotal="5210", vat="354.90", total_amount="5424.90")
        self.assertIsNone(infer_missing_discount(inv))


class SanityVatReconTests(unittest.TestCase):
    def test_f003_unbalanced_flagged(self):
        # 折扣没回填成功的兜底面:VAT 在场且两种口径都不平 → 强制转人工,绝不静默 auto
        inv = _inv(subtotal="5210.00", vat="230.00", total_amount="5315.10")
        self.assertTrue(any("勾稽不平" in r for r in evaluate_sanity(inv)))

    def test_discount_nets_out(self):
        inv = _inv(subtotal="5210.00", vat="354.90", total_amount="5424.90", discount="140")
        self.assertEqual(evaluate_sanity(inv), [])

    def test_net_printed_subtotal_passes(self):
        # 有的票小计印的是折后净额:小计+VAT=总额 已平 → 折扣在场也不误杀
        inv = _inv(subtotal="5070.00", vat="354.90", total_amount="5424.90", discount="140")
        self.assertEqual(evaluate_sanity(inv), [])


class AmountMathDiscountTests(unittest.TestCase):
    def test_discount_nets_out_no_trigger(self):
        inv = _inv(subtotal="115", discount="5", vat="7.70", total_amount="117.70")
        self.assertIsNone(t._check_amount_math(inv))

    def test_still_fires_when_neither_form_balances(self):
        inv = _inv(subtotal="100", discount="5", vat="7", total_amount="200")
        r = t._check_amount_math(inv)
        self.assertIsInstance(r, str)
        self.assertIn("amount math fail", r)

    def test_missing_discount_attr_tolerated(self):
        inv = _inv(subtotal="100", vat="7", total_amount="107")
        del inv.discount
        self.assertIsNone(t._check_amount_math(inv))


# INV2026030002 双联两页的 prod 落库原样(节选真实行·第一联碎空格·第二联干净带单位词)
_COPY1_ITEMS = [
    {
        "qty": "1",
        "name": "CAKE : Matcha cream cheese cake ราคา ส่ง ขนาด 3 ปอนด์ ค้าง รับ จาก บิล ที่ แล้ว / ตัด 12",
        "price": "0.00",
        "subtotal": "0.00",
    },
    {
        "qty": "1",
        "name": "CHEESE : Strawberry rare cheese cake ราคา ส่ง 3 ปอนด์ ค้าง รับ จาก บิล ที่ แล้ว / ตัด 12",
        "price": "0.00",
        "subtotal": "0.00",
    },
    {
        "qty": "1",
        "name": "CHEESE : Blueberry rare cheese cake ราคา ส่ง ขนาด 3 ปอนด์ ค้าง รับ จาก บิล ที่ แล้ว / ตัด 12",
        "price": "0.00",
        "subtotal": "0.00",
    },
    {
        "qty": "1",
        "name": "CAKE : Banana chocolate mousse cake ราคา ส่ง ขนาด 3 ปอนด์ ตัด 12",
        "price": "720.00",
        "subtotal": "720.00",
    },
    {
        "qty": "1",
        "name": "ค่า จัด ส่ง 385 / 90 ม 10 ต นคร สวร รศ์ ตก อ เมือง จ นคร สวร รรศ์ 60000 Tel. 0857282922",
        "price": "380.00",
        "subtotal": "380.00",
    },
]
_COPY2_ITEMS = [
    {
        "qty": "1 ก้อน",
        "name": "CAKE : Matcha cream cheese cake ราคาส่ง ขนาด 3 ปอนด์ ค้างรับจากบิลที่แล้ว / ตัด 12",
        "price": "0.00",
        "subtotal": "0.00",
    },
    {
        "qty": "1 ก้อน",
        "name": "CHEESE : Strawberry rare cheese cake ราคาส่ง 3 ปอนด์ ค้างรับจากบิลที่แล้ว / ตัด 12",
        "price": "0.00",
        "subtotal": "0.00",
    },
    {
        "qty": "1 ก้อน",
        "name": "CHEESE : Blueberry rare cheese cake ราคาส่ง ขนาด 3 ปอนด์ ค้างรับจากบิลที่แล้ว / ตัด 12",
        "price": "0.00",
        "subtotal": "0.00",
    },
    {
        "qty": "1 ก้อน",
        "name": "CAKE : Banana chocolate mousse cake ราคาส่ง ขนาด 3 ปอนด์ ตัด 12",
        "price": "720.00",
        "subtotal": "720.00",
    },
    {
        "qty": "1 ครั้ง",
        "name": "ค่าจัดส่ง 385 / 90 ม 10 ต นครสวรรค์ตก อ เมือง จ นครสวรรค์ 60000 Tel. 0857282922",
        "price": "380.00",
        "subtotal": "380.00",
    },
]


def _page(idx, items, inv_no="INV2026030002"):
    return {"page_index": idx, "fields": {"invoice_number": inv_no, "items": items}}


class CopyPageDedupTests(unittest.TestCase):
    def test_f002_real_case_5_not_10(self):
        groups = ig.group_pages_to_invoices([_page(1, _COPY1_ITEMS), _page(2, _COPY2_ITEMS)])
        self.assertEqual(len(groups), 1)
        merged = groups[0]["invoice_fields"]["items"]
        self.assertEqual(len(merged), 5, [i["name"] for i in merged])
        # 口味变体(同价同量的 Strawberry/Blueberry)必须都活着
        names = " | ".join(i["name"] for i in merged)
        self.assertIn("Strawberry", names)
        self.assertIn("Blueberry", names)

    def test_same_page_flavor_variants_not_merged(self):
        # 同页两行同价同量、名字高相似(口味变体)→ 不做模糊,都保留
        items = [
            {"qty": "1", "name": "CHEESE : Strawberry rare cheese cake ตัด 12", "price": "0.00"},
            {"qty": "1", "name": "CHEESE : Blueberry rare cheese cake ตัด 12", "price": "0.00"},
        ]
        merged = ig._merge_items([_page(1, items)])
        self.assertEqual(len(merged), 2)

    def test_normal_multipage_invoice_untouched(self):
        # 各页行互不重复的正常跨页发票:判重数不过半 → 模糊永不启用,行数不缩水
        p1 = [
            {"qty": "1", "name": "สินค้า A", "price": "100.00"},
            {"qty": "2", "name": "สินค้า B", "price": "50.00"},
        ]
        p2 = [
            {"qty": "1", "name": "สินค้า C ราคาพิเศษ", "price": "100.00"},
            {"qty": "1", "name": "สินค้า D", "price": "80.00"},
        ]
        merged = ig._merge_items([_page(1, p1), _page(2, p2)])
        self.assertEqual(len(merged), 4)

    def test_discount_field_survives_merge(self):
        pages = [
            _page(1, [], inv_no="X"),
            {"page_index": 2, "fields": {"invoice_number": "X", "discount": "140.00", "items": []}},
        ]
        groups = ig.group_pages_to_invoices(pages)
        self.assertEqual(groups[0]["invoice_fields"].get("discount"), "140.00")


if __name__ == "__main__":
    unittest.main(verbosity=2)
