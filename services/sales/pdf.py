# -*- coding: utf-8 -*-
"""销项单据合规 PDF 生成(PO-6 · docs/sales-module/docs/13)。

reportlab + 复用 usage_report_pdf_text 的泰/中/英混排字体(฿ 已覆盖)。出泰国合规
ใบกำกับภาษี:卖方(账套主体)与买方双方名称·地址·税号,VAT 7% 分列,连号,总/分公司
(Revenue Code §86/4)。纯渲染叶子:输入已组好的 doc/seller/buyer dict,不连库。
"""

from __future__ import annotations

import io
from decimal import Decimal

from services.sales.dates import to_thai_date
from services.usage.usage_report_pdf_text import _build_paragraph_text, _register_fonts

_DOC_LABEL = {
    "tax_invoice": "ใบกำกับภาษี / Tax Invoice",
    "tax_invoice_simple": "ใบกำกับภาษีอย่างย่อ / Simplified Tax Invoice",
    "tax_invoice_receipt": "ใบกำกับภาษี/ใบเสร็จรับเงิน / Tax Invoice / Receipt",
    "receipt": "ใบเสร็จรับเงิน / Receipt",
    "credit_note": "ใบลดหนี้ / Credit Note",
    "debit_note": "ใบเพิ่มหนี้ / Debit Note",
    "quotation": "ใบเสนอราคา / Quotation",
}

# 买方税号标签随买方类型变(docs/15 §4):公司=税号 / 个人=身份证 / 外国=护照。
_BUYER_TIN_LABEL = {
    "company": "เลขประจำตัวผู้เสียภาษี / Tax ID",
    "individual": "เลขบัตรประชาชน / National ID",
    "foreigner": "เลขหนังสือเดินทาง / Passport No.",
}

_PAYMENT_DOC_TYPES = ("receipt", "tax_invoice_receipt")
_PAYMENT_METHOD_LABEL = {
    "cash": "เงินสด / Cash",
    "transfer": "โอนเงิน / Transfer",
    "cheque": "เช็ค / Cheque",
    "card": "บัตร / Card",
    "promptpay": "พร้อมเพย์ / PromptPay",
}

# 正本给买方 / 副本自留(泰国 VAT 注册方至少出 2 联 · docs/16 §E2)。
_COPY_LABEL = {
    "original": "ต้นฉบับ / Original",
    "copy": "สำเนา / Copy",
}
PAGE_SIZES = ("A4", "A5")


def _money(v) -> str:
    return f"{Decimal(str(v if v is not None else 0)):,.2f}"


def _discount_cell(ln: dict) -> str:
    """明细折扣列:无折扣显 '-';有则显金额,百分比输入再括注 (x%)。"""
    disc = Decimal(str(ln.get("discount") or 0))
    if disc == 0:
        return "-"
    pct = ln.get("discount_pct")
    if pct not in (None, "", 0, "0"):
        return f"{_money(disc)} ({_money(pct)}%)"
    return _money(disc)


def _buyer_branch_text(b: dict) -> str:
    """公司买方的总公司/分店标识(§86/4 第 13 项强制字段)。"""
    if b.get("branch_type") == "branch" and b.get("branch_no"):
        return f"สาขาที่ {b['branch_no']} / Branch {b['branch_no']}"
    return "สำนักงานใหญ่ / Head Office"


def render_invoice_pdf(
    doc: dict, seller: dict, buyer: dict, *, page: str = "A4", copy_kind: str = "original"
) -> bytes:
    """渲染合规 PDF。page=A4|A5(共用布局);copy_kind=original|copy(正/副本角标·§E2)。"""
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
    from reportlab.lib.pagesizes import A4, A5
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

    pagesize = A5 if str(page).upper() == "A5" else A4
    copy_kind = copy_kind if copy_kind in _COPY_LABEL else "original"
    base, bold = _register_fonts()

    # 列宽按可用页宽等比缩放(A4 基准 180mm),A4/A5 共用同一套布局不溢出。
    sx = (pagesize[0] - 30 * mm) / (180 * mm)

    def cw(*widths):
        return [w * mm * sx for w in widths]

    seller = seller or {}
    buyer = buyer or {}

    def P(text, b=False, align=TA_LEFT, size=9):
        style = ParagraphStyle(
            "c", fontName=(bold if b else base), fontSize=size, leading=size + 3, alignment=align
        )
        return Paragraph(
            _build_paragraph_text(str(text if text not in (None, "") else "-"), b), style
        )

    def party(title, p, tin_label):
        cell = [P(title, True, size=10), P(p.get("name"), True)]
        if p.get("address"):
            cell.append(P(p.get("address")))
        cell.append(P(f"{tin_label}: {p.get('tax_id') or '-'}"))
        if p.get("branch"):
            cell.append(P(p.get("branch")))
        if p.get("phone"):
            cell.append(P(f"โทร / Tel: {p.get('phone')}"))
        return cell

    def buyer_party(title, b):
        """买方块按类型渲染:税号标签随类型,分店仅公司,匿名显散客(docs/15 §4)。"""
        cell = [P(title, True, size=10), P(b.get("name"), True)]
        if b.get("address"):
            cell.append(P(b.get("address")))
        btype = b.get("type")
        if btype == "anonymous":
            cell.append(P("ลูกค้าทั่วไป / Walk-in customer"))
            return cell
        label = _BUYER_TIN_LABEL.get(btype, "เลขประจำตัวผู้เสียภาษี / TIN")
        cell.append(P(f"{label}: {b.get('tax_id') or '-'}"))
        if btype == "company":
            cell.append(P(_buyer_branch_text(b)))
        return cell

    buf = io.BytesIO()
    pdf = SimpleDocTemplate(
        buf,
        pagesize=pagesize,
        leftMargin=15 * mm,
        rightMargin=15 * mm,
        topMargin=15 * mm,
        bottomMargin=15 * mm,
        title=doc.get("doc_number") or "document",
    )
    story = [
        P(_DOC_LABEL.get(doc.get("doc_type"), doc.get("doc_type") or ""), True, TA_CENTER, 15),
        P(_COPY_LABEL[copy_kind], True, TA_CENTER, 9),
        Spacer(1, 4 * mm),
    ]

    meta = Table(
        [
            [
                P("เลขที่ / No.: " + (doc.get("doc_number") or "-"), True),
                P(
                    "วันที่ / Date: " + to_thai_date(doc.get("issue_date")) + " (พ.ศ.)",
                    align=TA_RIGHT,
                ),
            ]
        ],
        colWidths=cw(90, 90),
    )
    story.append(meta)
    story.append(Spacer(1, 3 * mm))

    if doc.get("due_date") or doc.get("payment_terms"):
        bits = []
        if doc.get("due_date"):
            bits.append("ครบกำหนด / Due: " + to_thai_date(doc.get("due_date")) + " (พ.ศ.)")
        if doc.get("payment_terms"):
            bits.append("เงื่อนไข / Terms: " + str(doc.get("payment_terms")))
        story.append(P("    ".join(bits)))
        story.append(Spacer(1, 2 * mm))

    parties = Table(
        [
            [
                party("ผู้ขาย / Seller", seller, "เลขประจำตัวผู้เสียภาษี / TIN"),
                buyer_party("ผู้ซื้อ / Buyer", buyer),
            ]
        ],
        colWidths=cw(90, 90),
    )
    parties.setStyle(
        TableStyle(
            [
                ("BOX", (0, 0), (-1, -1), 0.5, colors.grey),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    story.append(parties)
    story.append(Spacer(1, 4 * mm))

    head = [
        "#",
        "รายการ / Description",
        "จำนวน / Qty",
        "ราคา / Price",
        "ส่วนลด / Discount",
        "จำนวนเงิน / Amount",
    ]
    rows = [[P(h, True, TA_CENTER) for h in head]]
    for ln in doc.get("lines", []):
        rows.append(
            [
                P(ln.get("line_no"), align=TA_CENTER),
                P(ln.get("description")),
                P(_money(ln.get("qty")), align=TA_RIGHT),
                P(_money(ln.get("unit_price")), align=TA_RIGHT),
                P(_discount_cell(ln), align=TA_RIGHT),
                P(_money(ln.get("line_total")), align=TA_RIGHT),
            ]
        )
    items = Table(rows, colWidths=cw(8, 72, 18, 24, 28, 30), repeatRows=1)
    items.setStyle(
        TableStyle(
            [
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("BACKGROUND", (0, 0), (-1, 0), colors.Color(0.93, 0.93, 0.93)),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ]
        )
    )
    story.append(items)
    story.append(Spacer(1, 3 * mm))

    cur = doc.get("currency") or "THB"
    total_rows = [["มูลค่า / Subtotal", _money(doc.get("subtotal"))]]
    if Decimal(str(doc.get("header_discount_amount") or 0)) != 0:
        total_rows.append(
            ["ส่วนลดท้ายบิล / Discount", "-" + _money(doc.get("header_discount_amount"))]
        )
    total_rows.append(
        [f"ภาษีมูลค่าเพิ่ม / VAT {_money(doc.get('vat_rate'))}%", _money(doc.get("vat_amount"))]
    )
    if Decimal(str(doc.get("wht_amount") or 0)) != 0:
        total_rows.append(["หัก ณ ที่จ่าย / WHT", "-" + _money(doc.get("wht_amount"))])
    total_rows.append([f"รวมทั้งสิ้น / Grand Total ({cur})", _money(doc.get("grand_total"))])
    trows = [
        [P(a, align=TA_RIGHT), P(b, b=(i == len(total_rows) - 1), align=TA_RIGHT)]
        for i, (a, b) in enumerate(total_rows)
    ]
    totals = Table(trows, colWidths=cw(150, 30))
    totals.setStyle(
        TableStyle(
            [
                ("LINEABOVE", (0, -1), (-1, -1), 0.7, colors.black),
                ("TOPPADDING", (0, 0), (-1, -1), 2),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
            ]
        )
    )
    story.append(totals)

    pay = _payment_block(doc, P, cw, Table, TableStyle, colors, mm, Spacer)
    if pay:
        story.extend(pay)

    pdf.build(story)
    return buf.getvalue()


def _payment_block(doc, P, cw, Table, TableStyle, colors, mm, Spacer):
    """合并单/收据的收款区(docs/16 §J4):方式/日期/已收;partial 时显未收余额。"""
    if doc.get("doc_type") not in _PAYMENT_DOC_TYPES:
        return None
    status = doc.get("payment_status")
    if not status or status == "unpaid":
        return None
    pm = doc.get("payment_method")
    method = _PAYMENT_METHOD_LABEL.get(pm, pm or "-")
    rows = [
        [P("วิธีชำระ / Method", True), P(method)],
        [P("วันที่ชำระ / Date", True), P(doc.get("payment_date") or "-")],
        [P("ชำระแล้ว / Paid", True), P(_money(doc.get("paid_amount")))],
    ]
    if status == "partial":
        outstanding = Decimal(str(doc.get("grand_total") or 0)) - Decimal(
            str(doc.get("paid_amount") or 0)
        )
        rows.append([P("คงเหลือ / Outstanding", True), P(_money(outstanding))])
    table = Table(rows, colWidths=cw(60, 60))
    table.setStyle(
        TableStyle(
            [
                ("BOX", (0, 0), (-1, -1), 0.5, colors.grey),
                ("INNERGRID", (0, 0), (-1, -1), 0.3, colors.grey),
                ("TOPPADDING", (0, 0), (-1, -1), 2),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
            ]
        )
    )
    return [Spacer(1, 4 * mm), P("การชำระเงิน / Payment", True, size=10), table]
