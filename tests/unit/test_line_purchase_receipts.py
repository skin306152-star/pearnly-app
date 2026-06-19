# -*- coding: utf-8 -*-
"""LINE 采购 OCR 回归 fixture — 真票冻结(防 3 类误判复发)。

fixture = 各真票的 OCR 抽取字段(按 C:\\Users\\skin3\\Desktop\\单据 实物建模,含其误判模式),
喂确定性处理层断言卡片/草稿输出。离线运行(不依赖 Vision/DB),把以下行为钉死:

  1. CP ALL / 7-Eleven:total 不得取 Cash 200,应取净应付 110(cash−change 校正 + 折扣)。
  2. Seafood 2722:subtotal/VAT/rounding 等于票面 2544/178.08/-0.08(不反推、不按 7% 覆盖、
     舍入不误用整额 VAT 178)。
  3. Little Betong 431:明细乱读对不上总额 → warn_total=True → 卡片主按钮「เปิดเพื่อตรวจสอบ」。
  4. Amazon 70 / 140:保持 65.42/4.58 与 130.84/9.16,不回归。
"""

import unittest
from decimal import Decimal

from services.line_binding import line_card
from services.line_binding.line_card_i18n import chrome
from services.purchase import intake as ik
from services.purchase import line_ingest as li
from services.purchase import totals as totals_svc


def _grand(fields: dict, kind: str) -> Decimal:
    """跑确定性建单(含 doc 级 rounding/折扣吸收)→ 入账含税合计,等同卡片显示的金额。"""
    draft = ik.build_draft_from_invoice(fields, kind=kind)
    calc = totals_svc.compute_purchase_totals(
        draft["lines"], rounding=Decimal(str(draft.get("rounding", 0) or 0))
    )
    return calc["grand_total"]


def _primary_label(card: dict) -> str:
    """卡片底部主按钮(style=primary)的 label。"""
    found = []

    def walk(n):
        if isinstance(n, dict):
            if n.get("type") == "button" and n.get("style") == "primary":
                found.append(n["action"]["label"])
            for v in n.values():
                walk(v)
        elif isinstance(n, list):
            for x in n:
                walk(x)

    walk(card)
    return found[0] if found else ""


# OCR 抽取建模(fields_from_invoice 口径)——按真票 + 已知误判模式。
CP_ALL = {
    "document_type": "simplified_tax_invoice",
    "seller_name": "CP ALL,7-Eleven",
    "subtotal": "115",
    "vat": "",
    "discount": "5",
    "total_amount": "200",  # 误读:抓成 เงินสด/Cash 200(应为净应付 110)
    "cash_amount": "200",
    "change_amount": "90",
    "payment_method": "qr",
    "items": [
        {"name": "อเมริกาโนเย็น22ลล", "qty": "2", "price": "45", "subtotal": "90"},
        {"name": "Hข้าวโพดมะพร้าวอ่อล", "qty": "1", "price": "25", "subtotal": "25"},
    ],
}

SEAFOOD = {
    "document_type": "receipt",
    "seller_name": "Kodtalay Seafood Buffet",
    "subtotal": "2544",
    "vat": "178.08",
    "total_amount": "2722",
    "cash_amount": "3000",
    "change_amount": "278",
    "items": [
        {"name": "Buffet Premium 799", "qty": "3", "price": "799", "subtotal": "2397"},
        {"name": "เครื่องดื่มรีฟิล", "qty": "3", "price": "49", "subtotal": "147"},
    ],
}

# 实物 6 行:95+125+165+20+20+6 = 431(含小额 6 铢那行)。OCR 读全 → 对账通过。
LITTLE_BETONG_FULL = {
    "document_type": "receipt",
    "seller_name": "Little Betong",
    "total_amount": "431",
    "items": [
        {"name": "ผัดเปรี้ยว", "qty": "1", "price": "95", "subtotal": "95"},
        {"name": "ผัดวุ้นเส้น", "qty": "1", "price": "125", "subtotal": "125"},
        {"name": "ไก่ทอด", "qty": "1", "price": "165", "subtotal": "165"},
        {"name": "ข้าว", "qty": "1", "price": "20", "subtotal": "20"},
        {"name": "น้ำดื่ม", "qty": "1", "price": "20", "subtotal": "20"},
        {"name": "พริกน้ำปลา", "qty": "3", "price": "2", "subtotal": "6"},
    ],
}

# 漏读小额 6 铢那行 → 行额 425 ≠ 票面 431。差 6 铢落在旧 2% 容差(8.62)内会被静默放过 → 必须告警。
LITTLE_BETONG_MISSING = {
    "document_type": "receipt",
    "seller_name": "Little Betong",
    "total_amount": "431",
    "items": LITTLE_BETONG_FULL["items"][:5],
}

AMAZON_70 = {
    "document_type": "tax_invoice",
    "seller_name": "Cafe Amazon",
    "seller_tax": "0107561000013",
    "buyer_name": "",
    "subtotal": "",
    "vat": "4.58",
    "total_amount": "70",
    "payment_method": "qr",
    "items": [
        {"name": "TW แต่งกลิ่น เย็น", "qty": "1", "price": "60", "subtotal": "60"},
        {"name": "TW ไม่หวาน 0%", "qty": "1", "price": "0", "subtotal": "0"},
        {"name": "TW เพิ่มช็อตเอสเปรสโซ", "qty": "1", "price": "10", "subtotal": "10"},
    ],
}

AMAZON_140 = {
    "document_type": "tax_invoice",
    "seller_name": "Cafe Amazon",
    "seller_tax": "0107561000013",
    "buyer_name": "",
    "subtotal": "",
    "vat": "9.16",
    "total_amount": "140",
    "payment_method": "qr",
    "items": [
        {"name": "TW แต่งกลิ่น เย็น", "qty": "2", "price": "60", "subtotal": "120"},
        {"name": "TW ไม่หวาน 0%", "qty": "1", "price": "0", "subtotal": "0"},
        {"name": "TW เพิ่มช็อตเอสเปรสโซ", "qty": "1", "price": "10", "subtotal": "10"},
        {"name": "TW ไม่หวาน 0%", "qty": "1", "price": "0", "subtotal": "0"},
        {"name": "TW เพิ่มช็อตเอสเปรสโซ", "qty": "1", "price": "10", "subtotal": "10"},
        {"name": "TW แก้ว Mickey (แถมฟรี)", "qty": "1", "price": "0", "subtotal": "0"},
    ],
}


# Bangchak 加油票(真票·真机 bug):净额 1,780·升 44.67·单价 39.85·积分 22/785。
# 误读模式:LLM 把净额 1,780 读成圆整 1000(grand 误记 1000)。确定性兜底:升×单价(印刷行小计
# 一致时取印刷值更准)覆盖飞掉的 total;积分行(整数 qty)绝不当金额。
BANGCHAK_MISREAD = {
    "document_type": "tax_invoice",
    "seller_name": "BANGCHAK BGN-CHAARANSAN",
    "subtotal": "",
    "vat": "",
    "total_amount": "1000",  # ★误读:净额 1,780 被读成 1000
    "items": [
        {"name": "ไฮดีเซล S", "qty": "44.67", "price": "39.85", "subtotal": "1780"},
        {"name": "คะแนนสะสม", "qty": "22", "price": "39.85", "subtotal": "785"},  # 积分·绝不当金额
    ],
}

# total 已被正确读为净额 1,780 的干净票:确定性层不得反过来覆盖(升×单价 1780.10 在容差内)。
BANGCHAK_CLEAN = {
    "document_type": "tax_invoice",
    "seller_name": "BANGCHAK BGN-CHAARANSAN",
    "subtotal": "",
    "vat": "",
    "total_amount": "1780.00",
    "items": [
        {"name": "ไฮดีเซล S", "qty": "44.67", "price": "39.85", "subtotal": "1780"},
        {"name": "คะแนนสะสม", "qty": "22", "price": "39.85", "subtotal": "785"},
    ],
}


class BangchakFuelTotalTests(unittest.TestCase):
    """加油票总额读飞:升×单价兜底,grand=1,780(永不 1000·永不把积分 22 当金额)。"""

    def test_misread_total_corrected_to_net(self):
        n = ik.normalize_ocr_fields(BANGCHAK_MISREAD)
        self.assertEqual(n["total_amount"], "1780.00")
        self.assertIn("fuel_total_from_qty_price", n.get("_corrections") or [])

    def test_booked_grand_is_fuel_net_not_1000(self):
        n = ik.normalize_ocr_fields(BANGCHAK_MISREAD)
        grand = _grand(n, "expense")
        self.assertEqual(grand, Decimal("1780.00"))
        self.assertNotEqual(grand, Decimal("1000.00"))  # ★永不 1000
        self.assertNotEqual(grand, Decimal("876.70"))  # ★永不把积分 22×39.85 当额

    def test_clean_total_not_overwritten(self):
        # total 已正确读 1,780 → 升×单价 1780.10 在容差内,不反向覆盖(保印刷净额)。
        n = ik.normalize_ocr_fields(BANGCHAK_CLEAN)
        self.assertEqual(n["total_amount"], "1780.00")
        self.assertNotIn("fuel_total_from_qty_price", n.get("_corrections") or [])
        self.assertEqual(_grand(n, "expense"), Decimal("1780.00"))

    def test_non_fuel_receipts_unaffected(self):
        # 红线:加油兜底不碰其它票据(无加油品名 → 不触发)。
        for fx, kind, want in (
            (CP_ALL, "expense", "110.00"),
            (SEAFOOD, "expense", "2722.00"),
            (AMAZON_70, "expense", "70.00"),
        ):
            n = ik.normalize_ocr_fields(fx)
            self.assertNotIn("fuel_total_from_qty_price", n.get("_corrections") or [])
            self.assertEqual(_grand(n, kind), Decimal(want))


class CpAllCashTotalTests(unittest.TestCase):
    """Issue 1:total 不得取 Cash 200。"""

    def test_total_corrected_from_cash_change(self):
        n = ik.normalize_ocr_fields(CP_ALL)
        self.assertEqual(n["total_amount"], "110.00")
        self.assertIn("total_fixed_from_cash_change", n.get("_corrections") or [])

    def test_booked_grand_is_net_after_discount(self):
        n = ik.normalize_ocr_fields(CP_ALL)
        self.assertEqual(_grand(n, "expense"), Decimal("110.00"))

    def test_items_shown_and_no_false_warn(self):
        n = ik.normalize_ocr_fields(CP_ALL)
        raw, show, warn = li._items_display_decision(n)
        self.assertTrue(show)
        self.assertFalse(warn)  # 折扣解释了 115 行额 vs 110 净额,不误报
        self.assertEqual(len(raw), 2)

    def test_seafood_cash_not_mistaken_for_total(self):
        # 反向保险:Seafood 的 Cash 3000 ≠ total → 校正不得误触发(total 仍 2722)。
        n = ik.normalize_ocr_fields(SEAFOOD)
        self.assertEqual(n["total_amount"], "2722")


class SeafoodBreakdownTests(unittest.TestCase):
    """Issue 2:subtotal/VAT/rounding 等于票面,舍入不误显整额 VAT。"""

    def test_card_amounts_match_receipt(self):
        n = ik.normalize_ocr_fields(SEAFOOD)
        sub, vat, rnd = li._card_amounts(n)
        self.assertEqual(sub, "2,544.00")
        self.assertEqual(vat, "178.08")
        self.assertEqual(rnd, "-0.08")

    def test_rounding_not_full_vat(self):
        n = ik.normalize_ocr_fields(SEAFOOD)
        _, _, rnd = li._card_amounts(n)
        self.assertNotIn("178", rnd)  # 旧 bug:舍入误显 178.00

    def test_booked_grand_is_receipt_total(self):
        n = ik.normalize_ocr_fields(SEAFOOD)
        self.assertEqual(_grand(n, "expense"), Decimal("2722.00"))


class LittleBetongWarnTests(unittest.TestCase):
    """Issue 3:明细对不上 → warn_total → 主按钮「เปิดเพื่อตรวจสอบ」。"""

    def test_full_items_reconcile_no_warn(self):
        # 6 行读全(含 6 铢)→ 合计 431 = 票面 → 正常确认,不告警。
        n = ik.normalize_ocr_fields(LITTLE_BETONG_FULL)
        _, show, warn = li._items_display_decision(n)
        self.assertTrue(show)
        self.assertFalse(warn)

    def test_warn_when_small_line_missing(self):
        # 漏读 6 铢那行(425 ≠ 431,差 6 铢)→ 必须告警(固定 2 铢容差·不被旧 2% 容差吃掉)。
        n = ik.normalize_ocr_fields(LITTLE_BETONG_MISSING)
        _, _, warn = li._items_display_decision(n)
        self.assertTrue(warn)

    def test_primary_button_is_review_when_warn(self):
        card = line_card.result_card(
            state="confirm",
            amount="431.00",
            fields={"vendor": "Little Betong", "detail": "—"},
            doc_id="D1",
            lang="th",
            warn_total=True,
        )
        self.assertEqual(_primary_label(card), chrome("th")["btn_review"])

    def test_primary_button_is_confirm_when_clean(self):
        card = line_card.result_card(
            state="confirm",
            amount="431.00",
            fields={"vendor": "Little Betong", "detail": "—"},
            doc_id="D1",
            lang="th",
            warn_total=False,
        )
        self.assertEqual(_primary_label(card), chrome("th")["btn_confirm"])


class AmazonNoRegressionTests(unittest.TestCase):
    """Amazon 70/140 保持正确(含税倒推税前/VAT + 入账合计)。"""

    def test_amazon_70(self):
        n = ik.normalize_ocr_fields(AMAZON_70)
        self.assertEqual(li._card_amounts(n), ("65.42", "4.58", ""))
        _, _, warn = li._items_display_decision(n)
        self.assertFalse(warn)
        self.assertEqual(_grand(n, "expense"), Decimal("70.00"))

    def test_amazon_140(self):
        n = ik.normalize_ocr_fields(AMAZON_140)
        self.assertEqual(li._card_amounts(n), ("130.84", "9.16", ""))
        _, _, warn = li._items_display_decision(n)
        self.assertFalse(warn)
        self.assertEqual(_grand(n, "expense"), Decimal("140.00"))


if __name__ == "__main__":
    unittest.main()
