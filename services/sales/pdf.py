# -*- coding: utf-8 -*-
"""销项单据合规 PDF 生成(PO-6 · docs/sales-module/docs/13)。

reportlab + 复用 usage_report_pdf_text 的泰/中/英混排字体(฿ 已覆盖)。出泰国合规
ใบกำกับภาษี:卖方(账套主体)与买方双方名称·地址·税号,VAT 7% 分列,连号,总/分公司
(Revenue Code §86/4)。纯渲染叶子:输入已组好的 doc/seller/buyer dict,不连库。
"""

from __future__ import annotations

import io
from decimal import Decimal

from services.usage.usage_report_pdf_text import _build_paragraph_text, _register_fonts

_DOC_LABEL = {
    "tax_invoice": "ใบกำกับภาษี / Tax Invoice",
    "tax_invoice_simple": "ใบกำกับภาษีอย่างย่อ / Simplified Tax Invoice",
    "receipt": "ใบเสร็จรับเงิน / Receipt",
    "credit_note": "ใบลดหนี้ / Credit Note",
    "debit_note": "ใบเพิ่มหนี้ / Debit Note",
    "quotation": "ใบเสนอราคา / Quotation",
}


def _money(v) -> str:
    return f"{Decimal(str(v if v is not None else 0)):,.2f}"


def render_invoice_pdf(doc: dict, seller: dict, buyer: dict) -> bytes:
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

    base, bold = _register_fonts()
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

    buf = io.BytesIO()
    pdf = SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=15 * mm,
        rightMargin=15 * mm,
        topMargin=15 * mm,
        bottomMargin=15 * mm,
        title=doc.get("doc_number") or "document",
    )
    story = [
        P(_DOC_LABEL.get(doc.get("doc_type"), doc.get("doc_type") or ""), True, TA_CENTER, 15),
        Spacer(1, 4 * mm),
    ]

    meta = Table(
        [
            [
                P("เลขที่ / No.: " + (doc.get("doc_number") or "-"), True),
                P("วันที่ / Date: " + (doc.get("issue_date") or "-"), align=TA_RIGHT),
            ]
        ],
        colWidths=[90 * mm, 90 * mm],
    )
    story.append(meta)
    story.append(Spacer(1, 3 * mm))

    parties = Table(
        [
            [
                party("ผู้ขาย / Seller", seller, "เลขประจำตัวผู้เสียภาษี / TIN"),
                party("ผู้ซื้อ / Buyer", buyer, "เลขประจำตัวผู้เสียภาษี / TIN"),
            ]
        ],
        colWidths=[90 * mm, 90 * mm],
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

    head = ["#", "รายการ / Description", "จำนวน / Qty", "ราคา / Price", "จำนวนเงิน / Amount"]
    rows = [[P(h, True, TA_CENTER) for h in head]]
    for ln in doc.get("lines", []):
        rows.append(
            [
                P(ln.get("line_no"), align=TA_CENTER),
                P(ln.get("description")),
                P(_money(ln.get("qty")), align=TA_RIGHT),
                P(_money(ln.get("unit_price")), align=TA_RIGHT),
                P(_money(ln.get("line_total")), align=TA_RIGHT),
            ]
        )
    items = Table(rows, colWidths=[10 * mm, 95 * mm, 20 * mm, 25 * mm, 30 * mm], repeatRows=1)
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
    total_rows = [
        ["มูลค่า / Subtotal", _money(doc.get("subtotal"))],
        [f"ภาษีมูลค่าเพิ่ม / VAT {_money(doc.get('vat_rate'))}%", _money(doc.get("vat_amount"))],
    ]
    if Decimal(str(doc.get("wht_amount") or 0)) != 0:
        total_rows.append(["หัก ณ ที่จ่าย / WHT", "-" + _money(doc.get("wht_amount"))])
    total_rows.append([f"รวมทั้งสิ้น / Grand Total ({cur})", _money(doc.get("grand_total"))])
    trows = [
        [P(a, align=TA_RIGHT), P(b, b=(i == len(total_rows) - 1), align=TA_RIGHT)]
        for i, (a, b) in enumerate(total_rows)
    ]
    totals = Table(trows, colWidths=[150 * mm, 30 * mm])
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

    pdf.build(story)
    return buf.getvalue()
