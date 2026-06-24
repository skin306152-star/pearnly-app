# -*- coding: utf-8 -*-
"""一次性语料生成器:按 docs/integrations/express-push/25-test-invoice-corpus-spec.md 造测试发票 PDF。

真实泰国税务发票(ใบกำกับภาษี)版式 · 嵌入 Sarabun(OFL)· 含 §86/4 必备字段。采购票买方税号 /
销项票卖方税号统一用占位 {OWN_TAX}(Owner 替换成真测试工作区税号,方向判定才成立)。组 4 反伤账
按"应被拦/标记"故意造错。每张内嵌一行"场景号 + 预期结果"(可见页脚 + PDF metadata)。

输出:outputs/test_invoices/<组目录>/ + README.md 索引。运行:python scripts/_gen_test_invoices.py
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal
from typing import Callable, Optional

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

_FONT_DIR = os.path.join(os.path.dirname(__file__), "..", "services", "export", "fonts")
OUT_ROOT = os.path.join(os.path.expanduser("~"), "Desktop", "test_invoices")

# 自家公司 = DATAT 账套真身(skin306152 测试工作区主体)· 与 workspace_clients 对齐方向判定才准。
OWN_TAX = "0735527000289"
PAGE_W, PAGE_H = A4

THAI_DIGITS = "๐๑๒๓๔๕๖๗๘๙"
TH_MONTHS = [
    "",
    "มกราคม",
    "กุมภาพันธ์",
    "มีนาคม",
    "เมษายน",
    "พฤษภาคม",
    "มิถุนายน",
    "กรกฎาคม",
    "สิงหาคม",
    "กันยายน",
    "ตุลาคม",
    "พฤศจิกายน",
    "ธันวาคม",
]


def register_fonts() -> tuple[str, str]:
    pdfmetrics.registerFont(TTFont("Sarabun", os.path.join(_FONT_DIR, "Sarabun-Regular.ttf")))
    pdfmetrics.registerFont(TTFont("Sarabun-Bold", os.path.join(_FONT_DIR, "Sarabun-Bold.ttf")))
    return "Sarabun", "Sarabun-Bold"


def register_cjk() -> str:
    """页脚的中文场景注释需 CJK 字体(Sarabun 无中文字形)。Deng.ttf=DengXian 含中+拉丁。"""
    for p in (r"C:\Windows\Fonts\Deng.ttf", r"C:\Windows\Fonts\simhei.ttf"):
        if os.path.exists(p):
            try:
                pdfmetrics.registerFont(TTFont("CJK", p))
                return "CJK"
            except Exception:
                continue
    return "Sarabun"


FONT, FONT_B = register_fonts()
CJK = register_cjk()


def emoji_safe(s: str) -> str:
    """CJK 字体无彩色 emoji 字形 → 转纯文本标记,避免页脚出现缺字方块。"""
    return (
        s.replace("✅", "[OK]")
        .replace("⚠️", "[!]")
        .replace("❌", "[X]")
        .replace("⚠", "[!]")
        .replace("️", "")
    )


def money(v, thai=False) -> str:
    s = f"{Decimal(str(v)):,.2f}"
    return "".join(THAI_DIGITS[int(c)] if c.isdigit() else c for c in s) if thai else s


def to_thai_digits(s: str) -> str:
    return "".join(THAI_DIGITS[int(c)] if c.isdigit() else c for c in str(s))


def be_date(y: int, m: int, d: int, thai_digits=False) -> str:
    s = f"{d} {TH_MONTHS[m]} {y + 543}"  # 泰国发票用佛历
    return to_thai_digits(s) if thai_digits else s


def q2(v) -> Decimal:
    return Decimal(str(v)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


# ---- 真实感泰文公司(税号为虚构 13 位,非真税号)----
OWN = {
    "name": "บริษัท มานะชัยบริการ จำกัด (สำนักงานใหญ่)",
    "addr": "99/9 ถนนพหลโยธิน แขวงจตุจักร เขตจตุจักร กรุงเทพฯ 10900",
    "tax": OWN_TAX,
}
SUP = {
    "office": {
        "name": "บริษัท ไทยสเตชันเนอรี่ ซัพพลาย จำกัด",
        "addr": "88 ถนนพระราม 4 แขวงสีลม เขตบางรัก กรุงเทพฯ 10500",
        "tax": "0105556012345",
    },
    "fuel": {
        "name": "บริษัท บางจาก ปิโตรเลียม จำกัด (มหาชน)",
        "addr": "210 ถนนสุขุมวิท แขวงบางจาก เขตพระโขนง กรุงเทพฯ 10260",
        "tax": "0107536000269",
    },
    "pos": {
        "name": "บริษัท ซีพี ออลล์ จำกัด (มหาชน) สาขา 00123",
        "addr": "283 ถนนสีลม แขวงสีลม เขตบางรัก กรุงเทพฯ 10500",
        "tax": "0107542000011",
    },
    "build": {
        "name": "บริษัท สยามวัสดุก่อสร้าง จำกัด",
        "addr": "55 หมู่ 3 ถนนบางนา-ตราด ตำบลบางพลี อำเภอบางพลี สมุทรปราการ 10540",
        "tax": "0115551023456",
    },
    "newA": {
        "name": "บริษัท นิวเทค โซลูชั่นส์ จำกัด",
        "addr": "9/9 ถนนรัชดาภิเษก แขวงดินแดง เขตดินแดง กรุงเทพฯ 10400",
        "tax": "0105560099887",
    },
    "newB": {
        "name": "ห้างหุ้นส่วนจำกัด รุ่งเรืองพาณิชย์",
        "addr": "12 ถนนเพชรเกษม ตำบลหาดใหญ่ อำเภอหาดใหญ่ สงขลา 90110",
        "tax": "0903555044556",
    },
    # 同一供应商不同写法(测归一)
    "varA": {
        "name": "บริษัท ที.ดับบลิว.จี. ที จำกัด",
        "addr": "1 ถนนวิทยุ แขวงลุมพินี เขตปทุมวัน กรุงเทพฯ 10330",
        "tax": "0105549011223",
    },
    "varB": {
        "name": "บ. ที.ดับบลิว.จี.ที จก.",
        "addr": "1 ถ.วิทยุ ลุมพินี ปทุมวัน กทม. 10330",
        "tax": "0105549011223",
    },
    "cn": {
        "name": "บริษัท เซี่ยงไฮ้ อิมพอร์ต (ประเทศไทย) จำกัด · 上海进出口",
        "addr": "เลขที่ 7 อาคารเอ็มไพร์ ถนนสาทรใต้ กรุงเทพฯ 10120",
        "tax": "0105558077665",
    },
}
CUS = {
    "co": {
        "name": "บริษัท ลูกค้าสัมพันธ์ จำกัด",
        "addr": "456 ถนนเพชรบุรีตัดใหม่ แขวงบางกะปิ เขตห้วยขวาง กรุงเทพฯ 10310",
        "tax": "0105557066778",
    },
    "svc": {
        "name": "บริษัท เอเชีย โลจิสติกส์ จำกัด",
        "addr": "77 ถนนวิภาวดีรังสิต แขวงจตุจักร เขตจตุจักร กรุงเทพฯ 10900",
        "tax": "0105559055443",
    },
    # S4 自建客户:newC 全新(应自动建 ARMAS);dupC 与 newC 核心名近似但税号不同(应转人工不建重复)。
    "newC": {
        "name": "บริษัท เอ็มเพ็กซ์ เทรดดิ้ง จำกัด",
        "addr": "159 ถนนสุขุมวิท 24 แขวงคลองตัน เขตคลองเตย กรุงเทพฯ 10110",
        "tax": "0105561033221",
    },
    "dupC": {
        "name": "บริษัท เอ็มเพกซ์ เทรดดิ้ง จำกัด",
        "addr": "160 ถนนสุขุมวิท 24 แขวงคลองตัน เขตคลองเตย กรุงเทพฯ 10110",
        "tax": "0105562044332",
    },
}


@dataclass
class Item:
    desc: str
    qty: Decimal
    price: Decimal

    @property
    def amount(self) -> Decimal:
        return q2(self.qty * self.price)


@dataclass
class Invoice:
    num: str  # 场景号 "01"
    fname: str  # 文件名(不含扩展)
    group: str  # 子目录
    title: str  # 中文场景简述
    expected: str  # 预期结果
    chain: str  # 测哪条链路
    seller: dict
    buyer: dict
    items: list
    inv_no: str
    date: tuple  # (y,m,d) gregorian
    doc_type: str = "ใบกำกับภาษี / ใบส่งของ"
    payment: str = "เงินสด"  # 现金 / เงินเชื่อ 赊
    vat_included: bool = False  # 含税价
    vat_split: bool = True  # 税前+VAT 分列展示
    thai_digits: bool = False
    currency: str = "บาท"
    discount: Optional[Decimal] = None
    force_total: Optional[Decimal] = None  # 明细对不上时强制总额
    note_extra: str = ""  # 票面额外标注(押金/退货等)
    renderer: Optional[Callable] = None  # 特殊版式

    def totals(self):
        sub = sum((it.amount for it in self.items), Decimal("0"))
        if self.discount:
            sub = q2(sub - self.discount)
        if self.vat_included:
            grand = self.force_total if self.force_total is not None else sub
            base = q2(Decimal(grand) / Decimal("1.07"))
            vat = q2(Decimal(grand) - base)
            return base, vat, q2(Decimal(grand))
        vat = q2(sub * Decimal("0.07"))
        grand = self.force_total if self.force_total is not None else q2(sub + vat)
        return sub, vat, q2(grand)


# ---------- 低层绘制 ----------
def _t(c, x, y, s, size=10, bold=False, right=False, center=False, color=(0, 0, 0)):
    c.setFont(FONT_B if bold else FONT, size)
    c.setFillColorRGB(*color)
    if right:
        c.drawRightString(x, y, s)
    elif center:
        c.drawCentredString(x, y, s)
    else:
        c.drawString(x, y, s)
    c.setFillColorRGB(0, 0, 0)


def _footer(c, inv: Invoice, w=PAGE_W):
    c.setFont(CJK, 7)
    c.setFillColorRGB(0.55, 0.55, 0.55)
    c.drawString(
        15 * mm, 8 * mm, emoji_safe(f"【场景 {inv.num}】{inv.title} — 预期:{inv.expected}")
    )
    c.setFillColorRGB(0, 0, 0)


def _party(c, x, y, label, p: dict, w, td=False):
    _t(c, x, y, label, 9, bold=True, color=(0.3, 0.3, 0.3))
    _t(c, x, y - 14, p["name"], 11, bold=True)
    # 地址自动折行
    addr = p["addr"]
    c.setFont(FONT, 9)
    lines, cur = [], ""
    for word in addr.split(" "):
        if c.stringWidth(cur + " " + word, FONT, 9) > w:
            lines.append(cur)
            cur = word
        else:
            cur = (cur + " " + word).strip()
    if cur:
        lines.append(cur)
    yy = y - 28
    for ln in lines[:3]:
        _t(c, x, yy, ln, 9, color=(0.2, 0.2, 0.2))
        yy -= 12
    _t(c, x, yy, f"เลขประจำตัวผู้เสียภาษี: {p['tax']}", 9, bold=True)  # 税号恒阿拉伯(真票惯例)
    return yy - 14


# ---------- 标准发票 ----------
def render_standard(c, inv: Invoice):
    td = inv.thai_digits
    c.setFont(FONT_B, 18)
    _t(c, PAGE_W / 2, PAGE_H - 30 * mm, inv.doc_type, 17, bold=True, center=True)
    _t(
        c,
        PAGE_W / 2,
        PAGE_H - 36 * mm,
        "(ต้นฉบับ / ORIGINAL)",
        8,
        center=True,
        color=(0.4, 0.4, 0.4),
    )

    top = PAGE_H - 48 * mm
    _party(c, 15 * mm, top, "ผู้ขาย / ผู้ประกอบการ", inv.seller, 95 * mm, td)
    # 票号/日期 右上
    _t(c, PAGE_W - 15 * mm, top, "เลขที่ (No.):", 9, right=True, color=(0.3, 0.3, 0.3))
    _t(
        c,
        PAGE_W - 15 * mm,
        top - 12,
        to_thai_digits(inv.inv_no) if td else inv.inv_no,
        11,
        bold=True,
        right=True,
    )
    _t(c, PAGE_W - 15 * mm, top - 28, "วันที่ (Date):", 9, right=True, color=(0.3, 0.3, 0.3))
    _t(c, PAGE_W - 15 * mm, top - 40, be_date(*inv.date, thai_digits=td), 11, bold=True, right=True)

    by = _party(c, 15 * mm, top - 60, "ผู้ซื้อ / ลูกค้า", inv.buyer, 120 * mm, td)
    if inv.note_extra:
        _t(c, 15 * mm, by, inv.note_extra, 10, bold=True, color=(0.6, 0.2, 0.1))
        by -= 16

    _items_table(c, inv, by - 6)
    _footer(c, inv)


def _items_table(c, inv: Invoice, top_y):
    td = inv.thai_digits
    x0, x1 = 15 * mm, PAGE_W - 15 * mm
    cols = [
        x0 + 8 * mm,
        x0 + 14 * mm,
        x1 - 70 * mm,
        x1 - 35 * mm,
        x1,
    ]  # seq|desc start|qty|price|amount
    y = top_y
    c.setFillColorRGB(0.93, 0.95, 0.96)
    c.rect(x0, y - 16, x1 - x0, 16, fill=1, stroke=0)
    c.setFillColorRGB(0, 0, 0)
    _t(c, x0 + 4, y - 12, "ลำดับ", 8, bold=True)
    _t(c, cols[1], y - 12, "รายการ (Description)", 8, bold=True)
    _t(c, cols[2] + 18 * mm, y - 12, "จำนวน", 8, bold=True, right=True)
    _t(c, cols[3] + 14 * mm, y - 12, "ราคา/หน่วย", 8, bold=True, right=True)
    _t(c, cols[4], y - 12, "จำนวนเงิน", 8, bold=True, right=True)
    y -= 16
    c.setLineWidth(0.5)
    c.line(x0, y, x1, y)
    for i, it in enumerate(inv.items, 1):
        y -= 18
        _t(c, x0 + 4, y + 4, to_thai_digits(str(i)) if td else str(i), 9)
        _t(c, cols[1], y + 4, it.desc, 9)
        _t(
            c,
            cols[2] + 18 * mm,
            y + 4,
            (
                money(it.qty, td)
                if it.qty != it.qty.to_integral()
                else (to_thai_digits(str(int(it.qty))) if td else str(int(it.qty)))
            ),
            9,
            right=True,
        )
        _t(c, cols[3] + 14 * mm, y + 4, money(it.price, td), 9, right=True)
        _t(c, cols[4], y + 4, money(it.amount, td), 9, right=True)
    y -= 8
    c.line(x0, y, x1, y)
    sub, vat, grand = inv.totals()
    lblr = cols[4] - 48 * mm  # 标签右对齐边 · 留 48mm 给金额(含百万级)避免压字
    y -= 18
    if inv.discount:
        _t(c, lblr, y + 4, "ส่วนลด:", 9, right=True)
        _t(c, cols[4], y + 4, "-" + money(inv.discount, td), 9, right=True)
        y -= 16
    label_sub = "มูลค่าสินค้า/บริการ (ก่อน VAT)" if inv.vat_split else "ราคารวมภาษีมูลค่าเพิ่ม"
    _t(c, lblr, y + 4, label_sub + ":", 9, right=True)
    _t(c, cols[4], y + 4, money(sub, td) + f" {inv.currency}", 9, right=True)
    y -= 16
    _t(c, lblr, y + 4, "ภาษีมูลค่าเพิ่ม 7%:", 9, right=True)
    _t(c, cols[4], y + 4, money(vat, td) + f" {inv.currency}", 9, right=True)
    y -= 18
    c.setFillColorRGB(0.93, 0.95, 0.96)
    c.rect(cols[4] - 98 * mm, y - 4, 98 * mm, 20, fill=1, stroke=0)
    c.setFillColorRGB(0, 0, 0)
    _t(c, lblr, y + 4, "จำนวนเงินรวมทั้งสิ้น:", 10, bold=True, right=True)
    _t(c, cols[4], y + 4, money(grand, td) + f" {inv.currency}", 11, bold=True, right=True)
    y -= 28
    _t(c, x0, y, f"การชำระเงิน (Payment): {inv.payment}", 9, color=(0.3, 0.3, 0.3))
    _t(c, x0, y - 28, "ผู้รับเงิน / Authorized: ____________________", 9, color=(0.4, 0.4, 0.4))


# ---------- 特殊版式 ----------
def render_pos(c, inv: Invoice):
    """便利店 POS 小票:窄页 + 噪声前缀 + 等宽感。"""
    _t(c, inv._w / 2, inv._h - 12 * mm, inv.seller["name"], 9, bold=True, center=True)
    _t(c, inv._w / 2, inv._h - 17 * mm, inv.seller["addr"][:34], 6, center=True)
    _t(c, inv._w / 2, inv._h - 21 * mm, f"TAX ID {inv.seller['tax']}", 6, center=True)
    _t(c, inv._w / 2, inv._h - 26 * mm, "ใบกำกับภาษีอย่างย่อ / TAX INV(ABB)", 7, center=True)
    y = inv._h - 32 * mm
    _t(c, 6 * mm, y, f"POS#0007 RC{inv.inv_no} {be_date(*inv.date)}", 6, color=(0.3, 0.3, 0.3))
    y -= 12
    for it in inv.items:
        _t(c, 6 * mm, y, f"{it.desc[:22]}", 7)
        _t(c, inv._w - 6 * mm, y, money(it.amount), 7, right=True)
        y -= 11
    sub, vat, grand = inv.totals()
    y -= 4
    c.line(6 * mm, y, inv._w - 6 * mm, y)
    y -= 12
    _t(c, 6 * mm, y, "ยอดก่อนภาษี", 7)
    _t(c, inv._w - 6 * mm, y, money(sub), 7, right=True)
    y -= 11
    _t(c, 6 * mm, y, "VAT 7%", 7)
    _t(c, inv._w - 6 * mm, y, money(vat), 7, right=True)
    y -= 11
    _t(c, 6 * mm, y, "รวมสุทธิ", 8, bold=True)
    _t(c, inv._w - 6 * mm, y, money(grand), 8, bold=True, right=True)
    y -= 14
    _t(c, 6 * mm, y, "เงินสด / CASH", 7)
    _t(c, inv._w - 6 * mm, y, money(grand), 7, right=True)
    c.setFont(CJK, 5)
    c.setFillColorRGB(0.6, 0.6, 0.6)
    c.drawCentredString(inv._w / 2, 6 * mm, emoji_safe(f"【{inv.num}】{inv.expected}"))
    c.setFillColorRGB(0, 0, 0)


def render_fuel(c, inv: Invoice):
    """加油票:升数 + 积分 + 真总额,故意把 ลิตร/คะแนน 当噪声数字。"""
    render_standard(c, inv)


def render_noninvoice(c, inv: Invoice):
    """非发票:菜单/随手拍,无任何发票要素。"""
    _t(
        c,
        PAGE_W / 2,
        PAGE_H - 40 * mm,
        "เมนูอาหาร · ร้านอาหารตามสั่งป้านิด",
        16,
        bold=True,
        center=True,
    )
    items = [
        ("ข้าวผัดกะเพราหมู", "60"),
        ("ต้มยำกุ้ง", "120"),
        ("ข้าวเปล่า", "10"),
        ("น้ำเปล่า", "10"),
        ("ผัดไทย", "70"),
    ]
    y = PAGE_H - 60 * mm
    for n, p in items:
        _t(c, 30 * mm, y, n, 13)
        _t(c, PAGE_W - 30 * mm, y, p + " บาท", 13, right=True)
        y -= 22
    _t(
        c,
        PAGE_W / 2,
        y - 20,
        "เปิดทุกวัน 08.00 - 20.00 น. · โทร 02-123-4567",
        10,
        center=True,
        color=(0.4, 0.4, 0.4),
    )
    _footer(c, inv)


def render_handwritten(c, inv: Invoice):
    """手写感收据:斜体近似 + 关键金额像手写。"""
    _t(c, PAGE_W / 2, PAGE_H - 35 * mm, "ใบเสร็จรับเงิน / บิลเงินสด", 16, bold=True, center=True)
    y = PAGE_H - 55 * mm
    _t(c, 25 * mm, y, f"วันที่ ......{be_date(*inv.date)}......", 12)
    y -= 24
    _t(c, 25 * mm, y, f"ได้รับเงินจาก {inv.buyer['name']}", 12)
    y -= 24
    for it in inv.items:
        _t(c, 25 * mm, y, f"- {it.desc}", 12)
        _t(c, PAGE_W - 30 * mm, y, money(it.amount), 12, right=True)
        y -= 22
    _, _, grand = inv.totals()
    y -= 10
    c.setLineWidth(1.2)
    c.line(25 * mm, y, PAGE_W - 25 * mm, y)
    y -= 22
    # "手写"总额:用粗体 + 斜放近似
    c.saveState()
    c.translate(PAGE_W - 70 * mm, y)
    c.rotate(-4)
    _t(c, 0, 0, "รวม " + money(grand) + " บาท", 16, bold=True, color=(0.05, 0.05, 0.4))
    c.restoreState()
    _t(
        c,
        25 * mm,
        y - 30,
        "ลงชื่อ ............................ ผู้รับเงิน",
        11,
        color=(0.3, 0.3, 0.3),
    )
    _footer(c, inv)


def render_multipage(c, inv: Invoice):
    """多页长发票:25 行跨 2 页,合计在末页。"""
    per_page = 16
    pages = [inv.items[i : i + per_page] for i in range(0, len(inv.items), per_page)]
    total_pages = len(pages)
    for pi, chunk in enumerate(pages, 1):
        _t(c, PAGE_W / 2, PAGE_H - 28 * mm, inv.doc_type, 16, bold=True, center=True)
        _t(
            c,
            PAGE_W - 15 * mm,
            PAGE_H - 28 * mm,
            f"หน้า {pi}/{total_pages}",
            9,
            right=True,
            color=(0.3, 0.3, 0.3),
        )
        top = PAGE_H - 40 * mm
        _party(c, 15 * mm, top, "ผู้ขาย", inv.seller, 95 * mm)
        _t(
            c,
            PAGE_W - 15 * mm,
            top,
            f"เลขที่ {inv.inv_no}  วันที่ {be_date(*inv.date)}",
            9,
            right=True,
        )
        by = top - 56
        sub_inv = Invoice(**{**inv.__dict__, "items": chunk, "renderer": None})
        if pi < total_pages:
            # 仅画明细,不画合计
            _items_only(c, chunk, by, cont=True)
            _t(
                c,
                PAGE_W / 2,
                20 * mm,
                "(ยอดรวมแสดงในหน้าสุดท้าย)",
                8,
                center=True,
                color=(0.5, 0.5, 0.5),
            )
        else:
            _items_table(c, inv, by)  # 末页带全票合计(收敛到票面)
        _footer(c, inv)
        if pi < total_pages:
            c.showPage()


def _items_only(c, items, top_y, cont=False):
    x0, x1 = 15 * mm, PAGE_W - 15 * mm
    y = top_y
    _t(c, x0 + 4, y - 12, "ลำดับ", 8, bold=True)
    _t(c, x0 + 14 * mm, y - 12, "รายการ", 8, bold=True)
    _t(c, x1, y - 12, "จำนวนเงิน", 8, bold=True, right=True)
    y -= 16
    c.line(x0, y, x1, y)
    base = 1
    for i, it in enumerate(items, base):
        y -= 18
        _t(c, x0 + 4, y + 4, str(i), 9)
        _t(c, x0 + 14 * mm, y + 4, it.desc, 9)
        _t(c, x1, y + 4, money(it.amount), 9, right=True)


# ============ 场景定义 ============
def _items(*triples):
    return [Item(d, Decimal(str(q)), Decimal(str(p))) for d, q, p in triples]


def build_scenarios() -> list:
    S = []
    # ---- 组 1 正确 happy path ----
    S.append(
        Invoice(
            "01",
            "01_purchase_credit_goods",
            "group1_correct",
            "采购·赊购·货品·单行",
            "✅ 采购 RR · 可推",
            "识别+方向+推送",
            SUP["build"],
            OWN,
            _items(("เหล็กเส้น SD40 ขนาด 12 มม.", 100, 185)),
            "RR581215-004",
            (2025, 12, 15),
            payment="เงินเชื่อ (เครดิต 30 วัน)",
        )
    )
    S.append(
        Invoice(
            "02",
            "02_purchase_cash_expense_office",
            "group1_correct",
            "采购·现购·办公费用",
            "✅ 采购 HP · 走 DBF 费用",
            "识别+推送(费用)",
            SUP["office"],
            OWN,
            _items(("กระดาษ A4 80 แกรม (กล่อง)", 5, 480), ("ปากกาลูกลื่น (โหล)", 3, 120)),
            "IV6812-0098",
            (2025, 12, 16),
            payment="เงินสด",
        )
    )
    S.append(
        Invoice(
            "03",
            "03_sales_credit_service",
            "group1_correct",
            "销项·赊销·服务",
            "✅ 销项 IV · 服务项(RPA 路)",
            "识别+方向(销项)+推送",
            OWN,
            CUS["svc"],
            _items(("ค่าบริการที่ปรึกษาระบบบัญชี (เดือน ธ.ค.)", 1, 25000)),
            "INV6812-031",
            (2025, 12, 20),
            payment="เงินเชื่อ",
        )
    )
    S.append(
        Invoice(
            "04",
            "04_sales_cash_goods",
            "group1_correct",
            "销项·现销·货品",
            "✅ 销项 HS",
            "识别+方向(销项)",
            OWN,
            CUS["co"],
            _items(("กล่องบรรจุภัณฑ์ ขนาด L", 200, 18), ("เทปกาว OPP", 50, 22)),
            "INV6812-032",
            (2025, 12, 21),
            payment="เงินสด",
        )
    )
    S.append(
        Invoice(
            "05",
            "05_purchase_multi_line_5",
            "group1_correct",
            "采购·多行货品(5 行)",
            "✅ 多行汇总收敛票面",
            "识别(多行收敛)",
            SUP["office"],
            OWN,
            _items(
                ("หมึกพิมพ์ HP 678 ดำ", 4, 650),
                ("หมึกพิมพ์ HP 678 สี", 4, 720),
                ("กระดาษการ์ดสี (รีม)", 10, 95),
                ("แฟ้มเอกสาร 2 ห่วง", 24, 35),
                ("ลวดเย็บกระดาษ (กล่อง)", 12, 18),
            ),
            "IV6812-0101",
            (2025, 12, 18),
            payment="เงินเชื่อ",
        )
    )
    S.append(
        Invoice(
            "06",
            "06_purchase_satang_decimals",
            "group1_correct",
            "采购·含小数 satang",
            "✅ 金额精度不丢",
            "识别(小数精度)",
            SUP["build"],
            OWN,
            _items(("ปูนซีเมนต์ปอร์ตแลนด์ (ถุง)", 33, 123.45), ("ทรายหยาบ (คิว)", 2.5, 450.50)),
            "RR6812-0210",
            (2025, 12, 12),
            payment="เงินสด",
        )
    )
    S.append(
        Invoice(
            "07",
            "07_purchase_vat_included",
            "group1_correct",
            "采购·含税价(VAT included)",
            "✅ 税前=total−vat 反算",
            "识别(含税反算)",
            SUP["office"],
            OWN,
            _items(("ชุดโต๊ะทำงานพร้อมเก้าอี้", 1, 8025)),
            "IV6812-0110",
            (2025, 12, 10),
            payment="เงินสด",
            vat_included=True,
            vat_split=False,
            force_total=8025,
        )
    )
    S.append(
        Invoice(
            "08",
            "08_purchase_vat_split",
            "group1_correct",
            "采购·税前+VAT 分列",
            "✅ 直接采信不反算",
            "识别(分列采信)",
            SUP["office"],
            OWN,
            _items(("เครื่องพิมพ์เลเซอร์ขาวดำ", 2, 4500)),
            "IV6812-0111",
            (2025, 12, 11),
            payment="เงินเชื่อ",
            vat_split=True,
        )
    )
    S.append(
        Invoice(
            "09",
            "09_purchase_new_supplier",
            "group1_correct",
            "采购·新供应商(Express 无此商)",
            "✅ 自动建档 APMAS",
            "推送(供应商建档)",
            SUP["newA"],
            OWN,
            _items(("บริการพัฒนาเว็บไซต์ (เฟส 1)", 1, 45000)),
            "NT6812-007",
            (2025, 12, 19),
            payment="เงินเชื่อ",
        )
    )

    # ---- 组 2 方向判定 ----
    S.append(
        Invoice(
            "10",
            "10_direction_own_as_seller",
            "group2_direction",
            "自家税号在卖方位",
            "✅ 判销项",
            "方向判定",
            OWN,
            CUS["co"],
            _items(("ค่าออกแบบบรรจุภัณฑ์", 1, 12000)),
            "INV6812-040",
            (2025, 12, 17),
            payment="เงินเชื่อ",
        )
    )
    S.append(
        Invoice(
            "11",
            "11_direction_own_as_buyer",
            "group2_direction",
            "自家税号在买方位",
            "✅ 判采购",
            "方向判定",
            SUP["build"],
            OWN,
            _items(("อิฐมอญ (ก้อน)", 5000, 1.8)),
            "RR6812-0220",
            (2025, 12, 14),
            payment="เงินเชื่อ",
        )
    )
    amb_buyer = {
        "name": "บริษัท ทั่วไป จำกัด",
        "addr": "1 ถนนใดถนนหนึ่ง กรุงเทพฯ",
        "tax": "0100000000000",
    }
    S.append(
        Invoice(
            "12",
            "12_direction_ambiguous",
            "group2_direction",
            "两端都无自家税号/税号脏",
            "⚠️ ambiguous → 留人工(不乱推)",
            "方向判定(模糊)",
            SUP["office"],
            amb_buyer,
            _items(("สินค้าทั่วไป", 1, 1000)),
            "IV6812-0130",
            (2025, 12, 13),
            payment="เงินสด",
        )
    )

    # ---- 组 3 识别难点 ----
    S.append(
        Invoice(
            "13",
            "13_ocr_buddhist_date",
            "group3_ocr_hard",
            "佛历日期 25xx",
            "✅ 转公历 2025",
            "识别(佛历转换)",
            SUP["office"],
            OWN,
            _items(("หมึกพิมพ์ (ชุด)", 2, 1200)),
            "IV6812-0140",
            (2025, 12, 9),
            payment="เงินสด",
        )
    )
    S.append(
        Invoice(
            "14",
            "14_ocr_thai_numerals",
            "group3_ocr_hard",
            "泰文数字 ๑๒๓",
            "✅ 转阿拉伯数字",
            "识别(泰数字)",
            SUP["office"],
            OWN,
            _items(("กระดาษถ่ายเอกสาร (รีม)", 12, 105)),
            "IV6812-0141",
            (2025, 12, 8),
            payment="เงินสด",
            thai_digits=True,
        )
    )
    S.append(
        Invoice(
            "15",
            "15_ocr_fuel_liter_points",
            "group3_ocr_hard",
            "加油票(升数/积分)",
            "✅ 升数/积分不当金额·取真总额",
            "识别(噪声数字)",
            SUP["fuel"],
            OWN,
            _items(("น้ำมันดีเซล B7  22.00 ลิตร @ 31.94", 1, 702.68)),
            "BCP6812-5521",
            (2025, 12, 7),
            payment="เงินสด",
            note_extra="สะสมคะแนน Member 555  ·  เลขไมล์ 120,450 กม.",
            renderer=render_fuel,
        )
    )
    pos = Invoice(
        "16",
        "16_ocr_pos_convenience",
        "group3_ocr_hard",
        "7-11/便利店 POS 小票",
        "✅ 清洗 POS 噪声·总额对",
        "识别(POS 清洗)",
        SUP["pos"],
        OWN,
        _items(
            ("TW#100 น้ำดื่ม 600ml", 2, 7),
            ("T-BONE ขนมปัง", 1, 25),
            ("ORIGINAL กาแฟกระป๋อง", 3, 18),
        ),
        "0012345",
        (2025, 12, 6),
        payment="เงินสด",
        renderer=render_pos,
    )
    pos._w, pos._h = 80 * mm, 200 * mm
    S.append(pos)
    long_items = _items(
        *[
            (f"รายการสินค้า ลำดับที่ {i} · อะไหล่รหัส P{i:03d}", i % 5 + 1, 50 + i * 7)
            for i in range(1, 26)
        ]
    )
    S.append(
        Invoice(
            "17",
            "17_ocr_multipage_long",
            "group3_ocr_hard",
            "多页长发票(>20 行)",
            "✅ 多页合并·收敛票面",
            "识别(跨页合并)",
            SUP["build"],
            OWN,
            long_items,
            "RR6812-0301",
            (2025, 12, 5),
            payment="เงินเชื่อ",
            renderer=render_multipage,
        )
    )
    S.append(
        Invoice(
            "18",
            "18_ocr_discount_line",
            "group3_ocr_hard",
            "含折扣行 ส่วนลด",
            "✅ 折扣正确处理",
            "识别(折扣)",
            SUP["office"],
            OWN,
            _items(("เก้าอี้สำนักงาน", 10, 1500)),
            "IV6812-0150",
            (2025, 12, 4),
            payment="เงินเชื่อ",
            discount=Decimal("1500"),
        )
    )
    bad_buyer = {"name": OWN["name"], "addr": OWN["addr"], "tax": OWN_TAX}
    bad_seller = {
        "name": SUP["office"]["name"],
        "addr": SUP["office"]["addr"],
        "tax": "01055560123",
    }  # 11 位
    S.append(
        Invoice(
            "19",
            "19_ocr_invalid_taxid",
            "group3_ocr_hard",
            "税号非法(位数≠13)",
            "✅ 标税号无效·不显假值",
            "识别(税号校验)",
            bad_seller,
            bad_buyer,
            _items(("วัสดุสิ้นเปลือง", 1, 800)),
            "IV6812-0160",
            (2025, 12, 3),
            payment="เงินสด",
        )
    )

    def render_blurry(c, inv):
        c.saveState()
        c.translate(PAGE_W / 2, PAGE_H / 2)
        c.rotate(3.5)
        c.translate(-PAGE_W / 2, -PAGE_H / 2)
        render_standard(c, inv)
        c.restoreState()
        # 模糊覆盖:半透明灰条纹近似退化
        c.setFillColorRGB(0.5, 0.5, 0.5, 0.12)
        for yy in range(0, int(PAGE_H), 3):
            c.rect(0, yy, PAGE_W, 1.2, fill=1, stroke=0)
        c.setFillColorRGB(0, 0, 0)

    blur = Invoice(
        "20",
        "20_ocr_skew_blurry",
        "group3_ocr_hard",
        "模糊/倾斜扫描",
        "✅ 鲁棒 或 诚实低置信留人工",
        "识别(退化图鲁棒)",
        SUP["office"],
        OWN,
        _items(("อุปกรณ์สำนักงานรวม", 1, 3500)),
        "IV6812-0170",
        (2025, 12, 2),
        payment="เงินสด",
    )
    blur.renderer = render_blurry
    S.append(blur)
    S.append(
        Invoice(
            "21",
            "21_ocr_handwritten",
            "group3_ocr_hard",
            "手写金额收据",
            "✅ 识别或低置信留人工",
            "识别(手写)",
            SUP["newB"],
            OWN,
            _items(("ค่าขนส่งสินค้า", 1, 1500), ("ค่าแรงติดตั้ง", 1, 800)),
            "0456",
            (2025, 12, 1),
            payment="เงินสด",
            renderer=render_handwritten,
        )
    )

    # ---- 组 4 反伤账(故意造错)----
    S.append(
        Invoice(
            "22",
            "22_block_not_invoice_menu",
            "group4_intercept",
            "不是发票(菜单/随手拍)",
            "❌ 不建账·提示非发票",
            "拦截(非发票)",
            SUP["office"],
            OWN,
            [],
            "-",
            (2025, 12, 1),
            renderer=render_noninvoice,
        )
    )
    # 23 重复:与 01 同号同额(故意)
    S.append(
        Invoice(
            "23",
            "23_block_duplicate_of_01",
            "group4_intercept",
            "重复发票(同号同额再传)",
            "❌ 标重复·绝不重复记账",
            "拦截(幂等去重)",
            SUP["build"],
            OWN,
            _items(("เหล็กเส้น SD40 ขนาด 12 มม.", 100, 185)),
            "RR581215-004",
            (2025, 12, 15),
            payment="เงินเชื่อ (เครดิต 30 วัน)",
            note_extra="(สำเนาซ้ำ — เลขที่/ยอดตรงกับ 01)",
        )
    )
    S.append(
        Invoice(
            "24",
            "24_flag_future_date",
            "group4_intercept",
            "未来日期发票(日期>今天)",
            "⚠️ 反造假·标记复核",
            "拦截(未来日期)",
            SUP["office"],
            OWN,
            _items(("บริการล่วงหน้า", 1, 5000)),
            "IV6906-0001",
            (2026, 12, 31),
            payment="เงินเชื่อ",
        )
    )
    S.append(
        Invoice(
            "25",
            "25_flag_backdated_suspicious",
            "group4_intercept",
            "倒签/像伪造(编号日期异常)",
            "⚠️ 标记",
            "拦截(异常造票)",
            SUP["office"],
            OWN,
            _items(("ค่าบริการย้อนหลัง", 1, 30000)),
            "IV6512-9999",
            (2022, 1, 5),
            payment="เงินสด",
            note_extra="ออกใบแทน ณ วันที่ 2568 (เลขที่ไม่เรียงลำดับ)",
        )
    )
    S.append(
        Invoice(
            "26",
            "26_flag_foreign_currency_usd",
            "group4_intercept",
            "外币发票(USD)",
            "⚠️ 标记·不当泰铢记",
            "拦截(外币)",
            SUP["newA"],
            OWN,
            _items(("Cloud hosting service (annual)", 1, 1200)),
            "INV-US-0091",
            (2025, 12, 1),
            payment="Wire transfer",
            currency="USD",
            vat_split=False,
            vat_included=True,
            force_total=1284,
        )
    )
    S.append(
        Invoice(
            "27",
            "27_flag_deposit_receipt",
            "group4_intercept",
            "押金/定金收据 เงินมัดจำ",
            "⚠️ 特殊处理·不当费用直推",
            "拦截(押金)",
            SUP["build"],
            OWN,
            _items(("เงินมัดจำค่าสินค้า (10%) ตามใบสั่งซื้อ PO-6812-1", 1, 20000)),
            "DEP6812-01",
            (2025, 12, 1),
            payment="เงินสด",
            note_extra="เงินมัดจำ / เงินประกัน — ยังไม่ส่งมอบสินค้า",
        )
    )
    mm_inv = Invoice(
        "28",
        "28_flag_sum_mismatch",
        "group4_intercept",
        "明细加总 ≠ 总额",
        "⚠️ 标记复核",
        "拦截(对不上)",
        SUP["office"],
        OWN,
        _items(("สินค้า A", 2, 500), ("สินค้า B", 3, 300)),
        "IV6812-0180",
        (2025, 12, 1),
        payment="เงินสด",
        force_total=Decimal("9999"),
    )
    S.append(mm_inv)
    miss_seller = {"name": SUP["office"]["name"], "addr": SUP["office"]["addr"], "tax": ""}
    S.append(
        Invoice(
            "29",
            "29_flag_missing_fields",
            "group4_intercept",
            "缺关键字段(无税号/金额残缺)",
            "⚠️ 低置信→留人工",
            "拦截(残缺)",
            miss_seller,
            OWN,
            _items(("รายการไม่ระบุราคา", 1, 0)),
            "-",
            (2025, 12, 1),
            payment="",
            note_extra="(ไม่มีเลขประจำตัวผู้เสียภาษี / ยอดเงินไม่ชัด)",
        )
    )
    S.append(
        Invoice(
            "30",
            "30_credit_note_return",
            "group4_intercept",
            "退货/贷项通知单 ใบลดหนี้",
            "✅/⚠️ 冲销负向处理·不当正常采购",
            "拦截(贷项)",
            SUP["build"],
            OWN,
            _items(("รับคืนสินค้า เหล็กเส้น (ชำรุด)", 20, 185)),
            "CN6812-0005",
            (2025, 12, 22),
            payment="หักลดหนี้",
            doc_type="ใบลดหนี้ (Credit Note)",
            note_extra="อ้างอิงใบกำกับภาษีเดิม RR581215-004 — มูลค่าลดลง",
        )
    )
    S.append(
        Invoice(
            "31",
            "31_flag_zero_amount",
            "group4_intercept",
            "零金额 0.00",
            "⚠️ 标记·不建空账",
            "拦截(零额)",
            SUP["office"],
            OWN,
            _items(("ตัวอย่างสินค้า (แจกฟรี)", 1, 0)),
            "IV6812-0190",
            (2025, 12, 1),
            payment="-",
        )
    )

    # ---- 组 5 推送 / ERP ----
    S.append(
        Invoice(
            "32a",
            "32a_push_expense_dbf",
            "group5_push",
            "费用发票→推送(非货品)",
            "✅ 走 DBF 直写 RR/HP",
            "推送(DBF 费用)",
            SUP["office"],
            OWN,
            _items(("ค่าบริการทำความสะอาดสำนักงาน (เดือน)", 1, 6000)),
            "IV6812-0200",
            (2025, 12, 1),
            payment="เงินสด",
        )
    )
    S.append(
        Invoice(
            "32b",
            "32b_push_goods_route",
            "group5_push",
            "货品发票→推送(货品)",
            "✅ 销项 RPA 服务项/采购 DBF",
            "推送(货品路由)",
            SUP["build"],
            OWN,
            _items(("ท่อ PVC ขนาด 4 นิ้ว", 200, 95)),
            "RR6812-0400",
            (2025, 12, 1),
            payment="เงินเชื่อ",
        )
    )
    S.append(
        Invoice(
            "33",
            "33_push_brand_new_supplier",
            "group5_push",
            "全新供应商发票(Express APMAS 无)",
            "✅ 自动建档",
            "推送(供应商建档)",
            SUP["newB"],
            OWN,
            _items(("ค่าที่ปรึกษากฎหมาย", 1, 15000)),
            "RR6812-0500",
            (2025, 12, 1),
            payment="เงินเชื่อ",
        )
    )
    # S4 自建客户(ARMAS):先推 S4a 建客户,再推 S4b 触发疑似重复转人工(顺序关键)。
    S.append(
        Invoice(
            "S4a",
            "S4a_sales_new_customer",
            "group5_push",
            "销项·全新客户(Express ARMAS 无)",
            "✅ 自动建档 ARMAS · 销项过账",
            "推送(客户建档)",
            OWN,
            CUS["newC"],
            _items(("ค่าบริการออกแบบและพิมพ์บรรจุภัณฑ์", 1, 32000)),
            "INV6812-041",
            (2025, 12, 22),
            payment="เงินเชื่อ",
        )
    )
    S.append(
        Invoice(
            "S4b",
            "S4b_sales_dup_customer",
            "group5_push",
            "销项·疑似重复客户(名近·税号不同)",
            "⚠️ 疑似重复·转人工(不建重复 ARMAS 户)",
            "推送(客户去重守卫)",
            OWN,
            CUS["dupC"],
            _items(("ค่าบริการออกแบบสื่อโฆษณา", 1, 18000)),
            "INV6812-042",
            (2025, 12, 23),
            payment="เงินเชื่อ",
            note_extra="(ทดสอบ: ชื่อใกล้กับ เอ็มเพ็กซ์ เทรดดิ้ง แต่เลขภาษีต่างกัน)",
        )
    )

    # 组 5 · 批量混合(34):8 正常 + 1 重复 + 1 非发票,落 batch_34/
    for i in range(1, 9):
        S.append(
            Invoice(
                f"34-{i:02d}",
                f"34_batch_normal_{i:02d}",
                "group5_push/batch_34",
                f"批量·正常票 {i}/8",
                "✅ 应正常识别(批量 8 成)",
                "批量韧性",
                SUP["office"] if i % 2 else SUP["build"],
                OWN,
                _items((f"สินค้าชุดที่ {i}", i + 1, 100 + i * 30)),
                f"BT6812-{i:03d}",
                (2025, 12, i),
                payment="เงินสด",
            )
        )
    S.append(
        Invoice(
            "34-dup",
            "34_batch_duplicate",
            "group5_push/batch_34",
            "批量·重复票(撞 34-01)",
            "❌ 标重复·不重复记账",
            "批量韧性(去重)",
            SUP["office"],
            OWN,
            _items(("สินค้าชุดที่ 1", 2, 130)),
            "BT6812-001",
            (2025, 12, 1),
            payment="เงินสด",
            note_extra="(สำเนาซ้ำกับ BT6812-001)",
        )
    )
    S.append(
        Invoice(
            "34-non",
            "34_batch_not_invoice",
            "group5_push/batch_34",
            "批量·非发票混入",
            "❌ 拦非发票·不卡死整批",
            "批量韧性(非发票)",
            SUP["office"],
            OWN,
            [],
            "-",
            (2025, 12, 1),
            renderer=render_noninvoice,
        )
    )

    # ---- 调研补充(Owner 可挑)----
    S.append(
        Invoice(
            "R1",
            "R1_large_amount_million",
            "group6_research",
            "大额(百万级)",
            "✅ 大额金额范围鲁棒",
            "识别(金额范围)",
            SUP["build"],
            OWN,
            _items(("เครื่องจักรสายการผลิต รุ่น X-900", 1, 1850000)),
            "RR6812-9001",
            (2025, 12, 1),
            payment="เงินเชื่อ",
        )
    )
    S.append(
        Invoice(
            "R2",
            "R2_tiny_amount",
            "group6_research",
            "小额(几十铢)",
            "✅ 小额鲁棒",
            "识别(金额范围)",
            SUP["pos"],
            OWN,
            _items(("ถุงพลาสติก", 1, 12)),
            "IV6812-9002",
            (2025, 12, 1),
            payment="เงินสด",
        )
    )
    S.append(
        Invoice(
            "R3a",
            "R3a_same_supplier_variant_A",
            "group6_research",
            "同供应商写法 A(测归一)",
            "✅ 与 R3b 归一同一供应商",
            "识别(供应商归一)",
            SUP["varA"],
            OWN,
            _items(("บริการที่ปรึกษา รอบที่ 1", 1, 8000)),
            "TWG6812-01",
            (2025, 12, 1),
            payment="เงินเชื่อ",
        )
    )
    S.append(
        Invoice(
            "R3b",
            "R3b_same_supplier_variant_B",
            "group6_research",
            "同供应商写法 B(测归一)",
            "✅ 与 R3a 归一同一供应商",
            "识别(供应商归一)",
            SUP["varB"],
            OWN,
            _items(("บริการที่ปรึกษา รอบที่ 2", 1, 8000)),
            "TWG6812-02",
            (2025, 12, 2),
            payment="เงินเชื่อ",
        )
    )
    S.append(
        Invoice(
            "R4",
            "R4_mixed_th_cn",
            "group6_research",
            "中泰混排发票",
            "✅ OCR 语言鲁棒",
            "识别(语言鲁棒)",
            SUP["cn"],
            OWN,
            _items(("เครื่องนำเข้า 进口设备 Model-220", 2, 35000)),
            "SH6812-0001",
            (2025, 12, 1),
            payment="เงินเชื่อ",
        )
    )
    return S


def main():
    scenarios = build_scenarios()
    for inv in scenarios:
        out_dir = os.path.join(OUT_ROOT, inv.group)
        os.makedirs(out_dir, exist_ok=True)
        path = os.path.join(out_dir, inv.fname + ".pdf")
        is_pos = inv.renderer is render_pos
        pagesize = (inv._w, inv._h) if is_pos else A4
        c = canvas.Canvas(path, pagesize=pagesize)
        c.setTitle(f"[{inv.num}] {inv.title}")
        c.setSubject(f"预期:{inv.expected} | 链路:{inv.chain}")
        c.setKeywords(f"scenario={inv.num};expected={inv.expected};chain={inv.chain}")
        c.setAuthor("Pearnly test corpus (Opus 4.8)")
        (inv.renderer or render_standard)(c, inv)
        c.showPage()
        c.save()
    write_readme(scenarios)
    print(f"Generated {len(scenarios)} PDFs -> {os.path.relpath(OUT_ROOT)}")


# 每张「这是什么 + 上传后你该看到什么」· 全大白话,不用术语。
PLAIN = {
    "01": "你赊账买了一批钢筋。→ 系统应认出『这是你买进的(采购)』,能往 Express 推。",
    "02": "你付现金买了办公用品。→ 应认出是采购(费用类)。",
    "03": "你卖出一项服务(赊账)。→ 应认出『这是你卖出的(销项)』。",
    "04": "你现金卖出一批包装盒。→ 应认出是销项(卖出)。",
    "05": "一张发票上有 5 行商品。→ 应把每行加起来,跟发票总额对得上。",
    "06": "金额带小数(几毛几分)。→ 应一分不差地算准。",
    "07": "标价是『已含税价』。→ 应自己倒推出不含税的价。",
    "08": "不含税价和税额分两行写清楚。→ 应直接照用,不重算。",
    "09": "这个供应商系统里还没有。→ 应自动帮你建一个供应商档案。",
    "10": "你公司的名字/税号在『卖方』那一栏。→ 应判成卖出(销项)。",
    "11": "你公司的名字/税号在『买方』那一栏。→ 应判成买进(采购)。",
    "12": "买卖双方都不是你公司、税号也看不清。→ 应『不乱猜』,标成需要人工确认。",
    "13": "日期写的是泰国佛历(2568 年)。→ 应换算成公历 2025 年。",
    "14": "金额用泰文数字写的(๑๒๓)。→ 应换成我们看的普通数字。",
    "15": "加油小票上有『升数、积分』这些数字。→ 别把升数/积分当成钱,要取真正的总价。",
    "16": "7-11 那种小票,商品名前面有乱码/编号。→ 应清掉杂讯,总额对得上。",
    "17": "发票很长、超过一页。→ 应把几页合起来算,跟总额对得上。",
    "18": "其中一行是『折扣』。→ 应正确把折扣减掉。",
    "19": "税号位数不对(不是 13 位)。→ 应标『税号无效』,不显示一个假的。",
    "20": "扫描得很糊、还歪了。→ 能认就认;认不准就老实说『拿不准,请人工看』。",
    "21": "金额是手写的。→ 能认就认;认不准就老实说拿不准。",
    "22": "这其实是一张菜单,根本不是发票。→ 应不记账,提示『这不是发票』。",
    "23": "跟第 01 张一模一样,再传一次。→ 应认出是重复的,绝不记成两笔账。",
    "24": "发票日期写在『未来』(还没到的日子)。→ 应标『可疑,人工复核』。",
    "25": "日期、编号都很反常,像事后补开/造假。→ 应标成可疑。",
    "26": "金额是美元,不是泰铢。→ 应标记,别当成泰铢记进去。",
    "27": "这是『定金/押金』收据,不是真买到东西。→ 应特殊处理,别当普通费用直接推。",
    "28": "每行加起来跟发票总额对不上。→ 应标『需要复核』。",
    "29": "没税号、金额也看不清(残缺)。→ 应当低置信,留人工。",
    "30": "这是退货/折让单(金额是负的)。→ 应当『冲减』处理,别当又买了一笔。",
    "31": "金额是 0 元。→ 应标记,不建一笔空账。",
    "32a": "一张服务费发票。→ 应能写进 Express。",
    "32b": "一张货品发票。→ 应按货品的路线推。",
    "33": "Express 里还没有这家供应商。→ 应自动帮你建档。",
    "S4a": "你卖东西给一家**全新客户**(Express 里还没有)。→ 应自动帮你在 ARMAS 建这个客户档案、并把这笔销项记进去。",
    "S4b": "你卖东西给一家客户,名字跟刚建的『เอ็มเพ็กซ์ เทรดดิ้ง』几乎一样、但**税号不同**。→ 应『留个心眼』:疑似重复,转人工确认,**绝不**默默又建一个重复客户。(先传 S4a 再传 S4b 才看得出效果)",
    "R1": "金额上百万。→ 大数字也要算得对。",
    "R2": "金额只有十几块。→ 小数字也要算得对。",
    "R3a": "和 R3b 是同一家公司,只是名字写法稍不一样(全称 vs 简写)。→ 应认出是同一家。",
    "R3b": "和 R3a 是同一家公司,只是名字写法稍不一样。→ 应认出是同一家。",
    "R4": "发票里中文、泰文混着写。→ 两种文字都要能认。",
}

_GROUPS_PLAIN = {
    "group1_correct": "① 正常发票(应该顺顺利利认出来)",
    "group2_direction": "② 分清「你买进」还是「你卖出」",
    "group3_ocr_hard": "③ 难认的发票(看认得准不准)",
    "group4_intercept": "④ 故意造错的 —— 看系统拦不拦得住(★最重要)",
    "group5_push": "⑤ 推送到 Express",
    "group6_research": "⑥ 额外加测的(有空再挑着测)",
}


def write_readme(scenarios: list):
    lines = [
        "# 测试发票 · 使用说明(大白话版)",
        "",
        "这是一批**专门做出来的假发票**,用来试 Pearnly 行不行。每张都先告诉你:",
        "**这张是什么、上传后你应该看到什么结果** —— 你照着对,就知道系统做得对不对。",
        "",
        "怎么看结果:",
        "- ✅ 顺利 = 系统应该正常认出来、该买该卖分清楚。",
        "- ⚠️ 标记 = 系统应该『留个心眼』,标出来让人工再看一眼,别自动记。",
        "- ❌ 拦住 = 系统应该挡下来,**绝不能**糊里糊涂记成一笔账。",
        "",
        "## ⚠️ 上传前先做一件事(很关键,不然全白测)",
        "这些发票上「你自己公司」那一栏,统一写成:",
        "- 公司名:**บริษัท มานะชัยบริการ จำกัด**",
        "- 税号:**0735527000289**",
        "",
        "系统就是靠这个税号,来分辨一张发票是『你买东西』还是『你卖东西』。所以请在网站里",
        "把你这家测试公司的**名字和税号设成上面这两行一模一样**,上传时也**选中这家公司**。",
        "否则系统对不上号,会一直说『分不清方向』。(对方公司——供应商/客户——都是随便编的,不用管。)",
        "",
        "每张 PDF 的最下面,都有一行灰字写着这张的场景号和预期,方便你一眼对上。",
        "",
        "---",
        "",
    ]
    for gdir, gtitle in _GROUPS_PLAIN.items():
        rows = [
            s for s in scenarios if s.group.split("/")[0] == gdir and "/batch_34" not in s.group
        ]
        if not rows and gdir != "group5_push":
            continue
        lines += [f"## {gtitle}", "", "| 文件 | 这张是什么 · 上传后该看到什么 |", "|---|---|"]
        for s in rows:
            rel = os.path.join(s.group, s.fname + ".pdf").replace("\\", "/")
            lines.append(f"| `{rel}` | {PLAIN.get(s.num, s.title)} |")
        if gdir == "group5_push":
            lines.append(
                "| `group5_push/batch_34/`(10 张) | "
                "**一次性把这 10 张全传上去**:里面 8 张正常 + 1 张重复 + 1 张不是发票。"
                "看系统能不能:正常的认出来、重复的拦掉、菜单那张拦掉,而且**不会因为坏的两张就整批卡死**。 |"
            )
        lines.append("")
    lines += [
        "---",
        "",
        "## 第 ④ 组要特别说一下",
        "这一组**故意是错的 / 有问题的**,不是让系统认对,而是看它**拦不拦得住**——",
        "重复的、日期填到未来的、外币的、押金收据、明细对不上、缺东西的、退货单、0 元的、",
        "还有根本不是发票的(菜单)。系统要么挡下来、要么标出来让你再看,**就是不能闷头记一笔账**。",
        "这组最能看出来『靠不靠谱、会不会记错账』。",
    ]
    with open(os.path.join(OUT_ROOT, "README.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
