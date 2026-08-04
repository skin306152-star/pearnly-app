# -*- coding: utf-8 -*-
"""POS 热敏小票版式(SM 缺口批次 G1/G4 · ABB 简式税票 / 普通收据 · 80/58mm)。

版式对照桌面原型「ABB小票交互原型v1」逐要素落地。两个版式共骨架、按 doc_kind 切:

- abbrev_tax_invoice:泰国税法 ABB 要件 —— 法定抬头 ใบกำกับภาษีอย่างย่อ、含税声明
  (price_includes_vat 时)、连续票号、出票日期时间(曼谷 · 佛历)、卖方名/税号、
  收银员名、品名/数量/单价、含税总额 + VAT 单独拆示一行、Register No.(有号才印整行)。
- receipt:未注册 VAT 的普通收据 —— **整票不得出现 ใบกำกับภาษี 字样**(冒用违法),
  含 QR 文案在内所有字样都按此约束。

票面法定文案是法规文本,泰文为主关键处英文,不吃 UI 语言切换(不进 i18n)。
纯渲染叶子,不连库;金额只格式化不重算(票面自洽跟存额走)。58mm 缩字号能打即可,
主攻 80mm(原型细节⑤)。
"""

from __future__ import annotations

import io
from datetime import datetime
from decimal import Decimal

from services.sales import pdf as pdf_mod
from services.sales.dates import BANGKOK, to_thai_date
from services.usage.usage_report_pdf_text import _build_paragraph_text, _register_fonts

# 票面固定文案(泰文法规文本 + 关键处英文)。
_TITLE_ABB = ("ใบกำกับภาษีอย่างย่อ", "Receipt / Tax Invoice (ABB)")
_TITLE_RECEIPT = ("ใบเสร็จรับเงิน", "Receipt")
_VAT_INCLUDED = "ราคารวมภาษีมูลค่าเพิ่มแล้ว (VAT Included)"
_TIN = "เลขประจำตัวผู้เสียภาษี"
_REGISTER_NO = "เครื่องบันทึกเงินสดเลขที่ (Register No.)"
_QR_CAPTION = "สแกนขอใบกำกับภาษีเต็มรูป (Full Tax Invoice)"


def render_receipt_pdf(
    doc: dict, seller: dict, *, width_mm: int = 80, deterministic: bool = False
) -> bytes:
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.platypus import HRFlowable, Paragraph, SimpleDocTemplate, Spacer, Table

    seller = seller or {}
    base, bold = _register_fonts()
    fs = 7 if width_mm >= 80 else 6
    margin = 3 * mm
    page_w = width_mm * mm
    avail = page_w - 2 * margin

    def P(text, b=False, align=TA_LEFT, size=None):
        sz = size or fs
        style = ParagraphStyle(
            "t", fontName=(bold if b else base), fontSize=sz, leading=sz + 2, alignment=align
        )
        return Paragraph(
            _build_paragraph_text(str(text if text not in (None, "") else "-"), b), style
        )

    def rule():
        return HRFlowable(width="100%", thickness=0.4, color=colors.grey, dash=(1, 1))

    def kv(label, value, strong=False, size=None):
        return Table(
            [[P(label, b=strong, size=size), P(value, b=strong, align=TA_RIGHT, size=size)]],
            colWidths=[avail * 0.6, avail * 0.4],
            style=[
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 1),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
            ],
        )

    def build_story():
        s = _brand_header(seller, P, TA_CENTER, fs, mm, Spacer)
        s += _title_block(doc, P, TA_CENTER, fs, rule)
        s += _meta_lines(doc, kv)
        s.append(rule())
        s.append(kv("รายการ (Items)", "บาท"))
        for ln in doc.get("lines", []):
            s.append(P(ln.get("description"), True))
            qty = _qty(ln.get("qty"))
            price = pdf_mod._money(ln.get("unit_price"))
            s.append(kv(f"  {qty} x {price}", pdf_mod._money(ln.get("line_total"))))
        s.append(rule())
        s += _total_lines(doc, kv, fs)
        s += _payment_lines(doc, kv, rule)
        s += _qr_block(doc, P, TA_CENTER, mm, Spacer)
        s += _footer_lines(seller, P, TA_CENTER, mm, rule, Spacer)
        return s

    # 自适应纸高(卷纸连续走纸按内容裁切):先量各 flowable 求和再建页。两处不量足就会
    # 溢出第二页、票尾被裁走:① Frame 四边各 6pt 内边距 → 真实排版宽比 avail 窄 12pt,
    # 长品名会多折行,必须按真实宽度量;② HRFlowable 的 spaceBefore/After 不在 wrap
    # 返回高度里,得单独累加(多算一点对卷纸只是多走纸,少算就是裁票)。
    frame_pad = 12
    measured = 0.0
    for f in build_story():
        measured += f.wrap(avail - frame_pad, 100000)[1]
        measured += f.getSpaceBefore() + f.getSpaceAfter()
    page_h = measured + 2 * margin + frame_pad + 2 * mm

    buf = io.BytesIO()
    pdf = SimpleDocTemplate(
        buf,
        pagesize=(page_w, page_h),
        leftMargin=margin,
        rightMargin=margin,
        topMargin=margin,
        bottomMargin=margin,
        title=doc.get("doc_number") or "receipt",
    )
    cmk = pdf_mod._canvasmaker(deterministic)
    pdf.build(build_story(), **({"canvasmaker": cmk} if cmk else {}))
    return buf.getvalue()


def _brand_header(seller, P, TA_CENTER, fs, mm, Spacer):
    """抬头:logo(有则印)+ 店名 + 地址/电话 + 税号 + Register No.(有号才印整行)。"""
    from services.sales.pdf_brand import logo_flowables

    s = logo_flowables(seller, mm, Spacer)
    s.append(P(seller.get("name"), True, TA_CENTER, fs + 2))
    for field, label in (("address", ""), ("phone", "โทร ")):
        if seller.get(field):
            s.append(P(label + str(seller[field]), align=TA_CENTER))
    if seller.get("tax_id"):
        s.append(P(f"{_TIN} {seller['tax_id']}", align=TA_CENTER))
    if seller.get("register_no"):
        s.append(P(f"{_REGISTER_NO}: {seller['register_no']}", align=TA_CENTER))
    return s


def _title_block(doc, P, TA_CENTER, fs, rule):
    """法定抬头:ABB 大标 + 含税声明(价内时);普通收据只有收据抬头。"""
    is_abb = doc.get("doc_kind") == "abbrev_tax_invoice"
    th, en = _TITLE_ABB if is_abb else _TITLE_RECEIPT
    s = [rule(), P(th, True, TA_CENTER, fs + 3), P(en, align=TA_CENTER)]
    if is_abb and doc.get("price_includes_vat"):
        s.append(P(_VAT_INCLUDED, align=TA_CENTER))
    s.append(rule())
    return s


def _meta_lines(doc, kv):
    """票号 / 出票日期时间(曼谷 · 佛历)/ 收银员(库里有名才印)。"""
    s = [kv("เลขที่ (No.)", doc.get("doc_number") or "-", strong=True)]
    s.append(kv("วันที่ (Date)", _thai_datetime(doc.get("issue_at"))))
    if doc.get("cashier_name"):
        s.append(kv("พนักงาน (Cashier)", doc["cashier_name"]))
    return s


def _total_lines(doc, kv, fs):
    """合计区:件数小计 → 折扣(有才印)→ 总额(大字)→ VAT 拆示行(仅 ABB)。"""
    qty_total = _qty(sum(Decimal(str(ln.get("qty") or 0)) for ln in doc.get("lines", [])))
    s = [kv(f"รวม {qty_total} ชิ้น (Subtotal)", pdf_mod._money(doc.get("subtotal")))]
    discount = Decimal(str(doc.get("discount_total") or 0))
    if discount > 0:
        s.append(kv("ส่วนลด (Discount)", "-" + pdf_mod._money(discount)))
    s.append(kv("ยอดสุทธิ (Total)", "฿" + pdf_mod._money(doc.get("grand_total")), True, fs + 2))
    if doc.get("doc_kind") == "abbrev_tax_invoice":
        # VAT 金额单独拆示一行是行业惯例(原型细节①拍板:印)。价内标 รวมใน(含在总额内)。
        suffix = " (รวมใน)" if doc.get("price_includes_vat") else " (VAT)"
        rate = _rate(doc.get("vat_rate"))
        s.append(kv(f"ภาษีมูลค่าเพิ่ม {rate}%{suffix}", pdf_mod._money(doc.get("vat_amount"))))
    return s


def _payment_lines(doc, kv, rule):
    """收款区:逐笔支付方式 + 金额(带 ref 括注)+ 找零(有才印)。"""
    payments = doc.get("payments") or []
    if not payments:
        return []
    s = [rule()]
    for p in payments:
        label = pdf_mod._label_fn("th_en", sep=" / ")(
            *pdf_mod._PAYMENT_METHOD_LABEL.get(p.get("method"), (p.get("method") or "-", "", ""))
        )
        if p.get("ref"):
            label += f" · {p['ref']}"
        s.append(kv(label, pdf_mod._money(p.get("amount"))))
    change = Decimal(str(doc.get("change_amount") or 0))
    if change > 0:
        s.append(kv("เงินทอน (Change)", pdf_mod._money(change)))
    return s


def _qr_block(doc, P, TA_CENTER, mm, Spacer):
    """G4 二维码架子:载荷非空才印。开关闸在组装层(账套开 + 仅 ABB);这里再守一道
    版式约束 —— 码文案含 ใบกำกับภาษี 字样,普通收据版给了载荷也不印(整票硬约束)。"""
    payload = doc.get("qr_payload")
    if not payload or doc.get("doc_kind") != "abbrev_tax_invoice":
        return []
    return [
        Spacer(1, 2 * mm),
        _qr_image(payload, 24 * mm),
        P(_QR_CAPTION, align=TA_CENTER),
        P(f"อ้างอิง {doc.get('doc_number') or '-'}", align=TA_CENTER),
    ]


def _footer_lines(seller, P, TA_CENTER, mm, rule, Spacer):
    s = [Spacer(1, 2 * mm), rule(), P("ขอบคุณค่ะ / Thank You", align=TA_CENTER)]
    if seller.get("footer_text"):
        s.append(P(seller["footer_text"], align=TA_CENTER))
    s.append(P("Powered by Pearnly POS", align=TA_CENTER))
    return s


def _qr_image(payload: str, side):
    """QR 载荷 → 定尺寸 reportlab Image(居中)。qrcode 用法同 store_binding.qr_png_base64。"""
    import qrcode
    from reportlab.platypus import Image as RLImage

    img = qrcode.make(payload)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    flowable = RLImage(buf, width=side, height=side)
    flowable.hAlign = "CENTER"
    return flowable


def _thai_datetime(value) -> str:
    """出票时刻 → 曼谷本地「DD/MM/佛历年 HH:MM」。naive 视为已是曼谷值(同 iso_bangkok 约定)。"""
    if not isinstance(value, datetime):
        return to_thai_date(value)
    local = value.astimezone(BANGKOK) if value.tzinfo else value
    return f"{to_thai_date(local.date())} {local:%H:%M}"


def _qty(v) -> str:
    """数量显示:整数去小数尾(2.000 → 2),非整保留原值。"""
    d = Decimal(str(v if v not in (None, "") else 0))
    return str(d.to_integral() if d == d.to_integral() else d.normalize())


def _rate(v) -> str:
    """税率显示:7.00 → 7(同 payment_settings._rate_str 的语义,票面短写)。"""
    d = Decimal(str(v if v not in (None, "") else 0)).normalize()
    return str(d.to_integral() if d == d.to_integral() else d)
