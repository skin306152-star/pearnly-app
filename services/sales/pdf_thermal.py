# -*- coding: utf-8 -*-
"""热敏卷纸窄版收据渲染(§E1 · 80mm/58mm POS 简易票)。

A4 表格列宽在窄卷纸上必溢出,所以热敏走独立的单列布局:逐行堆叠、小字号、自适应纸高
(卷纸连续走纸,按内容长度裁切)。复用 pdf.py 的标签/金额/合计算法,只换排版。纯渲染叶子。
"""

from __future__ import annotations

import io

from services.sales import pdf as pdf_mod
from services.sales.dates import to_thai_date
from services.usage.usage_report_pdf_text import _build_paragraph_text, _register_fonts


def render_thermal_pdf(
    doc: dict,
    seller: dict,
    buyer: dict,
    *,
    copy_kind: str = "original",
    width_mm: int = 80,
    lang: str = "th_en",
    deterministic: bool = False,
) -> bytes:
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.platypus import HRFlowable, Paragraph, SimpleDocTemplate, Spacer, Table

    seller = seller or {}
    buyer = buyer or {}
    copy_kind = copy_kind if copy_kind in pdf_mod._COPY_LABEL else "original"
    L = pdf_mod._label_fn(lang, sep="/")
    base, bold = _register_fonts()
    # 58mm 卷纸印幅更窄,整体再收一档字号。
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

    def kv(label, value, strong=False):
        """标签左 / 值右(合计、收款用)。"""
        return Table(
            [[P(label), P(value, b=strong, align=TA_RIGHT)]],
            colWidths=[avail * 0.6, avail * 0.4],
            style=[
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 1),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
            ],
        )

    def build_story():
        s = [
            P(pdf_mod._doc_label(doc.get("doc_type"), L), True, TA_CENTER, fs + 2),
            P(L(*pdf_mod._COPY_LABEL[copy_kind]), align=TA_CENTER, size=fs - 1),
            Spacer(1, 1.5 * mm),
            P(seller.get("name"), True, TA_CENTER, fs + 1),
        ]
        for field, label in (
            ("address", ""),
            ("tax_id", L("เลขภาษี", "TIN", "税号") + " "),
            ("phone", L("โทร", "Tel", "电话") + " "),
        ):
            if seller.get(field):
                s.append(P(label + str(seller[field]), align=TA_CENTER))
        s += [Spacer(1, 1 * mm), rule()]
        s.append(P(L("เลขที่", "No.", "编号") + " " + (doc.get("doc_number") or "-"), True))
        s.append(
            P(L("วันที่", "Date", "日期") + " " + to_thai_date(doc.get("issue_date")) + " (พ.ศ.)")
        )
        s += _buyer_lines(doc, buyer, P, L)
        s.append(rule())
        for ln in doc.get("lines", []):
            s.append(P(ln.get("description"), True))
            qty = pdf_mod._money(ln.get("qty"))
            price = pdf_mod._money(ln.get("unit_price"))
            s.append(kv(f"{qty} x {price}", pdf_mod._money(ln.get("line_total"))))
        s.append(rule())
        rows = pdf_mod._total_rows(doc, lang)
        for i, (label, value) in enumerate(rows):
            s.append(kv(label, value, strong=(i == len(rows) - 1)))
        s += _payment_lines(doc, P, kv, rule, L)
        s += [Spacer(1, 2 * mm), P(L("ขอบคุณค่ะ", "Thank you", "谢谢惠顾"), align=TA_CENTER)]
        return s

    # 自适应纸高:先按内容宽度量一遍各 flowable 高度求和,再以该高度建页渲染(单页卷纸)。
    measured = 0.0
    for f in build_story():
        measured += f.wrap(avail, 100000)[1]
    page_h = measured + 2 * margin + 4 * mm

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


def _buyer_lines(doc, buyer, P, L):
    """窄版买方块:匿名只标散客;其余显名称 + 类型对应税号标签。"""
    btype = buyer.get("type")
    if not btype:
        return []
    lines = [P(L("ผู้ซื้อ", "Buyer", "买方") + ": " + str(buyer.get("name") or "-"))]
    if btype == "anonymous":
        lines.append(P(L("ลูกค้าทั่วไป", "Walk-in", "散客")))
        return lines
    label = L(*pdf_mod._BUYER_TIN_LABEL.get(btype, ("เลขประจำตัวผู้เสียภาษี", "TIN", "税号")))
    lines.append(P(f"{label}: {buyer.get('tax_id') or '-'}"))
    return lines


def _payment_lines(doc, P, kv, rule, L):
    """收款区(§J4):仅收据/合并单且已收款时出;partial 标未收余额。"""
    from decimal import Decimal

    if doc.get("doc_type") not in pdf_mod._PAYMENT_DOC_TYPES:
        return []
    status = doc.get("payment_status")
    if not status or status == "unpaid":
        return []
    pm = doc.get("payment_method")
    method = L(*pdf_mod._PAYMENT_METHOD_LABEL.get(pm, (pm or "-", "", "")))
    out = [
        rule(),
        kv(L("วิธีชำระ", "Method", "付款方式"), method),
        kv(L("ชำระแล้ว", "Paid", "已付"), pdf_mod._money(doc.get("paid_amount"))),
    ]
    if status == "partial":
        outstanding = Decimal(str(doc.get("grand_total") or 0)) - Decimal(
            str(doc.get("paid_amount") or 0)
        )
        out.append(kv(L("คงเหลือ", "Outstanding", "未付余额"), pdf_mod._money(outstanding)))
    return out
