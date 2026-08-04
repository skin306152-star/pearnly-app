# -*- coding: utf-8 -*-
"""POS 小票版式守门(G1/G4 · ABB 简式税票 / 普通收据)。

断言走真渲染 + pymupdf 抽文本(CSS/坐标类假绿在这里不存在:字样在票面就是在,不在就是不在)。
矩阵:VAT 注册/未注册 × 有无 Register No. × 折扣 × 找零 × 二维码 × 纸宽。
"""

import unittest
from datetime import datetime, timezone
from decimal import Decimal

from services.pos import receipt_render


def _doc(**over):
    doc = {
        "doc_kind": "abbrev_tax_invoice",
        "doc_number": "ABB-T1-2026-00187",
        "issue_at": datetime(2026, 8, 5, 7, 32, tzinfo=timezone.utc),
        "cashier_name": "มินท์ (Mint)",
        "lines": [
            {
                "description": "มาสคาร่ากันน้ำ",
                "qty": 1,
                "unit_price": "250.00",
                "line_total": "250.00",
            },
            {"description": "ลิปแมท #04", "qty": 2, "unit_price": "179.00", "line_total": "358.00"},
        ],
        "subtotal": "608.00",
        "discount_total": "0",
        "vat_rate": "7",
        "vat_amount": "39.77",
        "grand_total": "608.00",
        "price_includes_vat": True,
        "payments": [{"method": "cash", "amount": "700.00", "ref": None}],
        "change_amount": "92.00",
        "qr_payload": None,
    }
    doc.update(over)
    return doc


def _seller(**over):
    seller = {
        "name": "บิวตี้เพิร์ล · Beauty Pearl",
        "address": "99/1 ถ.ราษฎร์พัฒนา กรุงเทพฯ 10240",
        "phone": "02-123-4567",
        "tax_id": "0105566012345",
        "register_no": None,
        "logo_url": None,
        "footer_text": None,
    }
    seller.update(over)
    return seller


def _text(doc, seller, **kw):
    import fitz

    data = receipt_render.render_receipt_pdf(doc, seller, deterministic=True, **kw)
    assert data.startswith(b"%PDF")
    with fitz.open(stream=data, filetype="pdf") as pdf:
        return "".join(page.get_text() for page in pdf)


class AbbLayoutTests(unittest.TestCase):
    def test_abb_carries_all_legal_elements(self):
        t = _text(_doc(), _seller())
        for needle in (
            "ใบกำกับภาษีอย่างย่อ",  # 法定抬头(泰文主位)
            "Receipt / Tax Invoice (ABB)",  # 英文并列
            "ราคารวมภาษีมูลค่าเพิ่มแล้ว",  # 含税声明(价内)
            "เลขประจำตัวผู้เสียภาษี 0105566012345",  # 卖方税号
            "ABB-T1-2026-00187",  # 连续票号
            "05/08/2569 14:32",  # 出票时刻(曼谷本地 · 佛历)
            "มินท์ (Mint)",  # 收银员上票
            "ภาษีมูลค่าเพิ่ม 7% (รวมใน)",  # VAT 单独拆示一行(原型细节①)
            "เงินทอน",  # 找零
            "เงินสด",  # 支付方式
        ):
            self.assertIn(needle, t)

    def test_vat_line_amount_and_grand_total_on_face(self):
        t = _text(_doc(), _seller())
        self.assertIn("39.77", t)
        self.assertIn("608.00", t)

    def test_price_excl_vat_drops_included_statement(self):
        t = _text(_doc(price_includes_vat=False, grand_total="650.56"), _seller())
        self.assertNotIn("ราคารวมภาษีมูลค่าเพิ่มแล้ว", t)
        self.assertIn("ภาษีมูลค่าเพิ่ม 7% (VAT)", t)

    def test_register_no_line_only_when_number_exists(self):
        # 原型细节③:没号整行不印(不印空标签),拿到号自动出现。
        without = _text(_doc(), _seller())
        self.assertNotIn("เครื่องบันทึกเงินสดเลขที่", without)
        with_no = _text(_doc(), _seller(register_no="RD-BKK-001234"))
        self.assertIn("เครื่องบันทึกเงินสดเลขที่ (Register No.): RD-BKK-001234", with_no)

    def test_discount_line_only_when_discounted(self):
        self.assertNotIn("ส่วนลด", _text(_doc(), _seller()))
        t = _text(_doc(discount_total="57.00", grand_total="551.00"), _seller())
        self.assertIn("ส่วนลด (Discount)", t)
        self.assertIn("57.00", t)

    def test_change_line_only_when_change_due(self):
        t = _text(
            _doc(
                change_amount="0",
                payments=[{"method": "promptpay", "amount": "608.00", "ref": "K+016842395"}],
            ),
            _seller(),
        )
        self.assertNotIn("เงินทอน", t)
        self.assertIn("พร้อมเพย์", t)
        self.assertIn("K+016842395", t)


class PlainReceiptTests(unittest.TestCase):
    def test_plain_receipt_never_says_tax_invoice(self):
        # 未注册 VAT 冒印 ใบกำกับภาษี 字样违法 —— 整票硬闸,含 QR 文案在内。
        doc = _doc(
            doc_kind="receipt",
            doc_number="RCP-T1-2026-00187",
            qr_payload="https://pearnly.com/pos/full-tax-invoice?ws=1&no=RCP-T1-2026-00187",
        )
        t = _text(doc, _seller(register_no="RD-BKK-001234"))
        self.assertIn("ใบเสร็จรับเงิน", t)
        self.assertNotIn("ใบกำกับภาษี", t)

    def test_plain_receipt_has_no_vat_split_line(self):
        t = _text(_doc(doc_kind="receipt", doc_number="RCP-T1-2026-00187"), _seller())
        self.assertNotIn("ภาษีมูลค่าเพิ่ม", t)


class QrAndWidthTests(unittest.TestCase):
    def test_qr_block_prints_caption_and_reference(self):
        t = _text(_doc(qr_payload="https://pearnly.com/pos/full-tax-invoice?ws=1&no=X"), _seller())
        self.assertIn("สแกนขอใบกำกับภาษีเต็มรูป", t)
        self.assertIn("อ้างอิง ABB-T1-2026-00187", t)

    def test_no_qr_block_without_payload(self):
        self.assertNotIn("สแกน", _text(_doc(), _seller()))

    def test_58mm_still_renders(self):
        data = receipt_render.render_receipt_pdf(_doc(), _seller(), width_mm=58, deterministic=True)
        self.assertTrue(data.startswith(b"%PDF"))

    def test_receipt_is_single_page_and_footer_on_face(self):
        # 自适应纸高必须装下整票:票尾溢出第二页 = 打印机只出第一页,感谢语和页脚被裁走。
        import fitz

        doc = _doc(
            qr_payload="https://pearnly.com/pos/full-tax-invoice?ws=1&no=X",
            lines=_doc()["lines"] * 4,  # 8 行长票
        )
        data = receipt_render.render_receipt_pdf(
            doc, _seller(register_no="RD-1", footer_text="x"), deterministic=True
        )
        with fitz.open(stream=data, filetype="pdf") as pdf:
            self.assertEqual(len(pdf), 1)
            self.assertIn("Powered by Pearnly POS", pdf[0].get_text())

    def test_footer_text_prints_when_configured(self):
        t = _text(_doc(), _seller(footer_text="ติดตามโปรที่ LINE @beautypearl"))
        self.assertIn("ติดตามโปรที่ LINE @beautypearl", t)
        self.assertIn("Powered by Pearnly POS", t)

    def test_missing_cashier_drops_the_line(self):
        t = _text(_doc(cashier_name=None), _seller())
        self.assertNotIn("พนักงาน", t)


class HelperTests(unittest.TestCase):
    def test_qty_drops_integral_tail(self):
        self.assertEqual(receipt_render._qty(Decimal("2.000")), "2")
        self.assertEqual(receipt_render._qty("1.5"), "1.5")

    def test_rate_short_form(self):
        self.assertEqual(receipt_render._rate("7.00"), "7")
        self.assertEqual(receipt_render._rate(Decimal("6.5")), "6.5")

    def test_thai_datetime_converts_to_bangkok_buddhist(self):
        dt = datetime(2026, 12, 31, 18, 30, tzinfo=timezone.utc)  # 曼谷已是次年 1/1 01:30
        self.assertEqual(receipt_render._thai_datetime(dt), "01/01/2570 01:30")


if __name__ == "__main__":
    unittest.main()
