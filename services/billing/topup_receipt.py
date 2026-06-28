# -*- coding: utf-8 -*-
"""Pearnly · 充值凭证 PDF · 泰式标准「ใบเสร็จรับเงิน / ใบกำกับภาษี」(收据/税务发票)。

版式对齐 pearnly_thai_standard_tax_invoice.html:卖方抬头 + ต้นฉบับ/ORIGINAL +
客户栏/文档栏 + 明细表(VAT 7% 拆分)+ 泰文金额大写 + 合计(深色总计条)+
收款详情/备注 + 签名栏 + 页脚。泰文用内嵌 Sarabun(prod 无系统字体也可渲染)。

充值金额按含税处理:总额 = 税前 + VAT7%(税前 = 总额 / 1.07)。
_SELLER 为占位卖方信息 · 正式开票前替换为真实公司/税号/地址。
"""

from __future__ import annotations

import io
import logging
import os
from decimal import Decimal, ROUND_HALF_UP

logger = logging.getLogger("mr-pilot")

_FONT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "export", "fonts")
_INK = "#111827"
_MUTED = "#6b7280"
_GREY2 = "#374151"
_LINE = "#d1d5db"
_LINE2 = "#9ca3af"
_HEAD_BG = "#f3f4f6"
_ZEBRA = "#f9fafb"
_FONT_OK = None

# 占位卖方信息(正式开票前替换为真实公司/税号/地址)。
_SELLER = {
    "name": "บริษัท เพิร์นลี่ จำกัด",
    "branch": "(สำนักงานใหญ่)",
    "tax_id": "0100000000000",
    "address": "ที่อยู่: 000/00 ถนนตัวอย่าง แขวง/ตำบล ตัวอย่าง เขต/อำเภอ ตัวอย่าง กรุงเทพฯ 00000",
    "contact": "โทร: 02-000-0000   อีเมล: billing@pearnly.com",
}

_THAI_NUM = ["ศูนย์", "หนึ่ง", "สอง", "สาม", "สี่", "ห้า", "หก", "เจ็ด", "แปด", "เก้า"]
_THAI_POS = ["", "สิบ", "ร้อย", "พัน", "หมื่น", "แสน"]


def _register_thai_font():
    global _FONT_OK
    if _FONT_OK is None:
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont

        try:
            pdfmetrics.registerFont(
                TTFont("Sarabun", os.path.join(_FONT_DIR, "Sarabun-Regular.ttf"))
            )
            pdfmetrics.registerFont(
                TTFont("Sarabun-Bold", os.path.join(_FONT_DIR, "Sarabun-Bold.ttf"))
            )
            _FONT_OK = True
        except Exception as e:  # noqa: BLE001
            logger.warning("[topup_receipt] Sarabun register failed: %s", str(e)[:120])
            _FONT_OK = False
    return ("Sarabun", "Sarabun-Bold") if _FONT_OK else ("Helvetica", "Helvetica-Bold")


def _read_group(s: str) -> str:
    """读一段 ≤6 位数字(无 ล้าน)。"""
    s = s.lstrip("0")
    if not s:
        return ""
    text = ""
    length = len(s)
    for i, ch in enumerate(s):
        d = int(ch)
        pos = length - 1 - i
        if d == 0:
            continue
        if pos == 0 and d == 1 and length > 1:
            text += "เอ็ด"
        elif pos == 1 and d == 2:
            text += "ยี่สิบ"
        elif pos == 1 and d == 1:
            text += "สิบ"
        else:
            text += _THAI_NUM[d] + _THAI_POS[pos]
    return text


def _read_int(n: int) -> str:
    if n == 0:
        return "ศูนย์"
    s = str(n)
    if len(s) > 6:  # ล้าน 递归(支持 ล้านล้าน)
        return _read_int(int(s[:-6])) + "ล้าน" + _read_group(s[-6:])
    return _read_group(s)


def baht_text(amount) -> str:
    """泰文金额大写:整数部分 + บาท + (ถ้วน | สตางค์)。"""
    q = Decimal(str(amount)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    baht = int(q)
    satang = int((q - baht) * 100)
    out = _read_int(baht) + "บาท"
    out += "ถ้วน" if satang == 0 else _read_group(str(satang)) + "สตางค์"
    return out


def _money(v) -> str:
    return f"{Decimal(str(v or 0)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP):,.2f}"


def _status_th(status: str) -> tuple[str, bool]:
    """返回 (泰文状态, 是否已收款)。"""
    s = (status or "").strip().lower()
    if s == "approved":
        return "ชำระแล้ว", True
    if s == "rejected":
        return "ถูกปฏิเสธ", False
    return "รอตรวจสอบ", False


def build_topup_receipt_pdf(*, lang: str = "th", tenant_name: str, receipt: dict) -> bytes:
    """单笔充值 → 泰式收据/税务发票 PDF bytes。lang 仅用于文件名层 · 文档本身为 TH/EN 双语固定格式。"""
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import mm
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.platypus import (
        SimpleDocTemplate,
        Paragraph,
        Spacer,
        Table,
        TableStyle,
        HRFlowable,
    )

    base, bold = _register_thai_font()

    def ps(name, size, color=_INK, font=None, align=0, leading=None):
        return ParagraphStyle(
            name,
            fontName=font or base,
            fontSize=size,
            textColor=colors.HexColor(color),
            alignment=align,
            leading=leading or size * 1.3,
        )

    st_brand = ps("brand", 16, _INK, bold)
    st_line = ps("ln", 8.4, _GREY2)
    st_lineb = ps("lnb", 8.4, _INK, bold)
    st_title = ps("title", 13, _INK, bold, 2)
    st_entitle = ps("entitle", 8.4, _GREY2, bold, 2)
    st_tag = ps("tag", 8.2, _INK, bold, 1)
    st_boxh = ps("boxh", 9, _INK, bold)
    st_lbl = ps("lbl", 8.2, _MUTED)
    st_val = ps("val", 8.2, _INK)
    st_valb = ps("valb", 8.2, _INK, bold)
    st_th = ps("th", 7.4, _INK, bold, 1)
    st_cell = ps("cell", 8, _INK)
    st_cellr = ps("cellr", 8, _INK, None, 2)
    st_cellrb = ps("cellrb", 8, _INK, bold, 2)
    st_desc = ps("desc", 8, _INK, bold)
    st_sub = ps("sub", 7.2, _MUTED)
    st_foot = ps("foot", 8, _MUTED)

    amt = Decimal(str(receipt.get("amount_thb") or 0)).quantize(
        Decimal("0.01"), rounding=ROUND_HALF_UP
    )
    pre_vat = (amt / Decimal("1.07")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    vat = amt - pre_vat
    rid = receipt.get("id") or 0
    doc_no = f"RV-{int(rid):06d}" if str(rid).isdigit() else f"RV-{rid}"
    status_th, paid = _status_th(receipt.get("status") or "")
    created = receipt.get("created_at") or "-"
    reviewed = receipt.get("reviewed_at") or created

    # ── 抬头(卖方 | 文档标题)─────────────────────────────────────────
    seller = [
        Paragraph("Pearnly", st_brand),
        Paragraph(f"<b>{_SELLER['name']}</b>  {_SELLER['branch']}", st_line),
        Paragraph(f"เลขประจำตัวผู้เสียภาษี: {_SELLER['tax_id']}", st_line),
        Paragraph(_SELLER["address"], st_line),
        Paragraph(_SELLER["contact"], st_line),
    ]
    tag = Table([[Paragraph("ต้นฉบับ / ORIGINAL", st_tag)]], colWidths=[34 * mm])
    tag.setStyle(
        TableStyle(
            [
                ("BOX", (0, 0), (-1, -1), 0.6, colors.HexColor(_INK)),
                ("TOPPADDING", (0, 0), (-1, -1), 1.4 * mm),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 1.4 * mm),
            ]
        )
    )
    doctitle = [
        tag,
        Spacer(1, 2.2 * mm),
        Paragraph("ใบเสร็จรับเงิน / ใบกำกับภาษี", st_title),
        Paragraph("RECEIPT / TAX INVOICE", st_entitle),
    ]
    header = Table([[seller, doctitle]], colWidths=[96 * mm, 90 * mm])
    header.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("ALIGN", (1, 0), (1, 0), "RIGHT"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ]
        )
    )

    # ── 客户栏 / 文档栏 ───────────────────────────────────────────────
    def info_box(title, rows, label_w=32 * mm):
        body = [[Paragraph(title, st_boxh), ""]]
        for k, v, vb in rows:
            body.append([Paragraph(k, st_lbl), Paragraph(v or "-", st_valb if vb else st_val)])
        t = Table(body, colWidths=[label_w, None])
        t.setStyle(
            TableStyle(
                [
                    ("SPAN", (0, 0), (1, 0)),
                    ("BOX", (0, 0), (-1, -1), 0.6, colors.HexColor(_LINE)),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("TOPPADDING", (0, 0), (-1, -1), 0.7 * mm),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 0.7 * mm),
                    ("LEFTPADDING", (0, 0), (-1, -1), 3 * mm),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 3 * mm),
                    ("TOPPADDING", (0, 0), (-1, 0), 2.6 * mm),
                    ("BOTTOMPADDING", (0, 0), (-1, 0), 2 * mm),
                ]
            )
        )
        return t

    cust = info_box(
        "ข้อมูลลูกค้า / Customer",
        [
            ("ชื่อลูกค้า", tenant_name, True),
            ("เลขประจำตัวผู้เสียภาษี", "-", False),
            ("สาขา", "-", False),
            ("ที่อยู่", "-", False),
            ("ผู้ชำระ", receipt.get("payer_name") or "-", False),
        ],
    )
    docb = info_box(
        "ข้อมูลเอกสาร / Document",
        [
            ("เลขที่เอกสาร", doc_no, True),
            ("อ้างอิง", f"#{rid}", False),
            ("วันที่ออก", created, False),
            ("วันที่รับชำระ", reviewed if paid else "-", False),
            ("วิธีชำระเงิน", "เติมเงินออนไลน์", False),
        ],
        label_w=29 * mm,
    )
    inforow = Table([[cust, docb]], colWidths=[104 * mm, 82 * mm])
    inforow.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (0, 0), 0),
                ("RIGHTPADDING", (0, 0), (0, 0), 4 * mm),
                ("LEFTPADDING", (1, 0), (1, 0), 0),
                ("RIGHTPADDING", (1, 0), (-1, -1), 0),
            ]
        )
    )

    # ── 明细表(VAT 拆分)──────────────────────────────────────────────
    desc_cell = [
        Paragraph("ค่าบริการเติมเงินเครดิต Pearnly", st_desc),
        Paragraph("Pearnly credit top-up", st_sub),
    ]
    th = lambda s: Paragraph(s, st_th)  # noqa: E731
    items = [
        [
            th("ลำดับ"),
            th("รายละเอียดสินค้า / บริการ"),
            th("จำนวน"),
            th("ราคาต่อหน่วย"),
            th("ส่วนลด"),
            th("มูลค่าก่อน VAT"),
            th("VAT 7%"),
            th("จำนวนเงิน"),
        ],
        [
            Paragraph("1", st_cell),
            desc_cell,
            Paragraph("1", ps("c", 8, _INK, None, 1)),
            Paragraph(_money(pre_vat), st_cellr),
            Paragraph("0.00", st_cellr),
            Paragraph(_money(pre_vat), st_cellr),
            Paragraph(_money(vat), st_cellr),
            Paragraph(_money(amt), st_cellrb),
        ],
        ["", "", "", "", "", "", "", ""],
    ]
    col_w = [9 * mm, None, 14 * mm, 20 * mm, 16 * mm, 24 * mm, 18 * mm, 24 * mm]
    tbl = Table(items, colWidths=col_w, rowHeights=[None, None, 14 * mm])
    tbl.setStyle(
        TableStyle(
            [
                # 表头(深线 #9ca3af · 灰底)
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(_HEAD_BG)),
                ("BOX", (0, 0), (-1, 0), 0.6, colors.HexColor(_LINE2)),
                ("INNERGRID", (0, 0), (-1, 0), 0.6, colors.HexColor(_LINE2)),
                # 表体(浅线 #d1d5db)· 明细行与填充行合成一格(草稿 border-top:0 · 无中缝横线)
                ("BOX", (0, 1), (-1, -1), 0.6, colors.HexColor(_LINE)),
                ("LINEAFTER", (0, 1), (-2, -1), 0.6, colors.HexColor(_LINE)),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("VALIGN", (0, 0), (-1, 0), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, 1), 1.8 * mm),
                ("BOTTOMPADDING", (0, 0), (-1, 1), 1.8 * mm),
                ("LEFTPADDING", (0, 0), (-1, -1), 1.4 * mm),
                ("RIGHTPADDING", (0, 0), (-1, -1), 1.4 * mm),
            ]
        )
    )

    # ── 金额大写 | 合计表 ─────────────────────────────────────────────
    words_lines = [
        Paragraph("จำนวนเงินเป็นตัวอักษร", st_valb),
        Spacer(1, 1.5 * mm),
        Paragraph(baht_text(amt), st_val),
    ]
    if paid:
        words_lines += [Spacer(1, 1.5 * mm), Paragraph("ได้รับชำระเงินเรียบร้อยแล้ว", st_lbl)]
    words = Table([[words_lines]], colWidths=[None])
    words.setStyle(
        TableStyle(
            [
                ("BOX", (0, 0), (-1, -1), 0.6, colors.HexColor(_LINE)),
                ("LEFTPADDING", (0, 0), (-1, -1), 4 * mm),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4 * mm),
                ("TOPPADDING", (0, 0), (-1, -1), 3 * mm),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3 * mm),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]
        )
    )
    lc = ps("lc", 8.2, _GREY2, bold)
    gl = ps("gl", 9.4, "#ffffff", bold)
    gr = ps("gr", 9.4, "#ffffff", bold, 2)
    tot = Table(
        [
            [Paragraph("รวมมูลค่าสินค้า / บริการ", lc), Paragraph(_money(pre_vat), st_cellr)],
            [Paragraph("ส่วนลด", lc), Paragraph("0.00", st_cellr)],
            [Paragraph("มูลค่าก่อนภาษี", lc), Paragraph(_money(pre_vat), st_cellr)],
            [Paragraph("ภาษีมูลค่าเพิ่ม 7%", lc), Paragraph(_money(vat), st_cellr)],
            [Paragraph("รวมทั้งสิ้น", gl), Paragraph(f"฿ {_money(amt)}", gr)],
        ],
        colWidths=[None, 30 * mm],
    )
    tot.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (0, 3), colors.HexColor(_ZEBRA)),
                ("BACKGROUND", (0, 4), (-1, 4), colors.HexColor(_INK)),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor(_LINE)),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 1.7 * mm),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 1.7 * mm),
                ("LEFTPADDING", (0, 0), (-1, -1), 2.2 * mm),
                ("RIGHTPADDING", (0, 0), (-1, -1), 2.2 * mm),
            ]
        )
    )
    totals = Table([[words, tot]], colWidths=[None, 72 * mm])
    totals.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (0, 0), 0),
                ("RIGHTPADDING", (0, 0), (0, 0), 6 * mm),
                ("LEFTPADDING", (1, 0), (1, 0), 0),
                ("RIGHTPADDING", (1, 0), (-1, -1), 0),
            ]
        )
    )

    # ── 收款详情 / 备注 ───────────────────────────────────────────────
    pay = info_box(
        "รายละเอียดการรับชำระ",
        [("สถานะ", status_th, True), ("ช่องทาง", "Online top-up", False)],
        label_w=29 * mm,
    )
    note_note = receipt.get("note")
    note_body = [
        Paragraph("หมายเหตุ", st_boxh),
        Paragraph(
            f"เอกสารนี้จัดทำจากระบบ Pearnly สำหรับรายการเติมเงินเครดิต เลขที่ {doc_no}"
            + (f" · {note_note}" if note_note else ""),
            st_lbl,
        ),
    ]
    noteb = Table([[note_body]], colWidths=[None])
    noteb.setStyle(
        TableStyle(
            [
                ("BOX", (0, 0), (-1, -1), 0.6, colors.HexColor(_LINE)),
                ("LEFTPADDING", (0, 0), (-1, -1), 3 * mm),
                ("RIGHTPADDING", (0, 0), (-1, -1), 3 * mm),
                ("TOPPADDING", (0, 0), (-1, -1), 2.4 * mm),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2.4 * mm),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]
        )
    )
    payrow = Table([[pay, noteb]], colWidths=[90 * mm, 96 * mm])
    payrow.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (0, 0), 0),
                ("RIGHTPADDING", (0, 0), (0, 0), 5 * mm),
                ("LEFTPADDING", (1, 0), (1, 0), 0),
                ("RIGHTPADDING", (1, 0), (-1, -1), 0),
            ]
        )
    )

    # ── 签名栏 ────────────────────────────────────────────────────────
    def sig(role):
        return [
            HRFlowable(
                width=46 * mm, thickness=0.6, color=colors.HexColor(_INK), spaceBefore=12 * mm
            ),
            Spacer(1, 1.2 * mm),
            Paragraph(role, ps("role", 8.2, _INK, bold, 1)),
            Paragraph("วันที่ ______ / ______ / ______", ps("sd", 7.6, _MUTED, None, 1)),
        ]

    sigs = Table([[sig("ผู้รับเงิน"), sig("ผู้มีอำนาจลงนาม")]], colWidths=[93 * mm, 93 * mm])
    sigs.setStyle(
        TableStyle([("ALIGN", (0, 0), (-1, -1), "CENTER"), ("VALIGN", (0, 0), (-1, -1), "TOP")])
    )

    story = [
        header,
        Spacer(1, 1.5 * mm),
        HRFlowable(width="100%", thickness=1.0, color=colors.HexColor(_INK)),
        Spacer(1, 4 * mm),
        inforow,
        Spacer(1, 4 * mm),
        tbl,
        Spacer(1, 3.5 * mm),
        totals,
        Spacer(1, 3.5 * mm),
        payrow,
        Spacer(1, 5 * mm),
        sigs,
        Spacer(1, 5 * mm),
        HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#e5e7eb")),
        Spacer(1, 1.5 * mm),
        Table(
            [
                [
                    Paragraph("Generated by Pearnly", st_foot),
                    Paragraph("Page 1 / 1", ps("pg", 8, _MUTED, None, 2)),
                ]
            ],
            colWidths=[None, 40 * mm],
        ),
    ]

    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=12 * mm,
        rightMargin=12 * mm,
        topMargin=10 * mm,
        bottomMargin=10 * mm,
        title=f"ใบเสร็จรับเงิน {doc_no}",
    )
    doc.build(story)
    return buf.getvalue()
