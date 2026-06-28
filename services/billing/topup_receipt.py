# -*- coding: utf-8 -*-
"""Pearnly · 充值凭证 PDF(单笔 topup_request → 一张收据式 PDF)。

Pearnly 给客户开的充值收据:品牌抬头 + 凭证编号 + 公司 + 金额 + 状态 + 付款人 +
申请/到账时间 + 备注。泰文用嵌入的 Sarabun(prod 无系统字体也能渲染),标签四语
(zh/en/th/ja)随系统语言。状态如实(已到账/待审核/已驳回)。

字体方案复用 services/export/proof_pdf.py(嵌入 services/export/fonts/Sarabun-*.ttf)。
"""

from __future__ import annotations

import io
import logging
import os
from decimal import Decimal

logger = logging.getLogger("mr-pilot")

# 复用 export 域已 commit 的 Sarabun 字体(prod 无系统字体也可)。
_FONT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "export", "fonts")
_BRAND = "#7C4DFF"  # Pearnly 主色(紫)
_INK = "#111827"
_MUTED = "#6b7280"
_LINE = "#e5e7eb"

_FONT_OK = None

_I18N = {
    "zh": {
        "title": "充值凭证",
        "receipt_no": "凭证编号",
        "company": "公司",
        "amount": "充值金额",
        "status": "状态",
        "payer": "付款人",
        "created": "申请时间",
        "credited": "到账时间",
        "note": "备注",
        "approved": "已到账",
        "pending": "待审核",
        "rejected": "已驳回",
        "issued_by": "由 Pearnly 出具",
        "generated": "生成时间",
        "disclaimer": "本凭证为账户充值记录,非税务发票。",
    },
    "en": {
        "title": "Top-up Receipt",
        "receipt_no": "Receipt No.",
        "company": "Company",
        "amount": "Amount",
        "status": "Status",
        "payer": "Payer",
        "created": "Requested",
        "credited": "Credited",
        "note": "Note",
        "approved": "Credited",
        "pending": "Pending",
        "rejected": "Rejected",
        "issued_by": "Issued by Pearnly",
        "generated": "Generated",
        "disclaimer": "This is an account top-up record, not a tax invoice.",
    },
    "th": {
        "title": "ใบรับเงินเติมเครดิต",
        "receipt_no": "เลขที่ใบรับ",
        "company": "บริษัท",
        "amount": "จำนวนเงิน",
        "status": "สถานะ",
        "payer": "ผู้ชำระ",
        "created": "วันที่ขอ",
        "credited": "วันที่เข้าบัญชี",
        "note": "หมายเหตุ",
        "approved": "เข้าบัญชีแล้ว",
        "pending": "รอตรวจสอบ",
        "rejected": "ถูกปฏิเสธ",
        "issued_by": "ออกโดย Pearnly",
        "generated": "วันที่ออก",
        "disclaimer": "เอกสารนี้เป็นบันทึกการเติมเครดิต ไม่ใช่ใบกำกับภาษี",
    },
    "ja": {
        "title": "チャージ領収書",
        "receipt_no": "領収番号",
        "company": "会社",
        "amount": "金額",
        "status": "状態",
        "payer": "支払者",
        "created": "申請日時",
        "credited": "入金日時",
        "note": "備考",
        "approved": "入金済み",
        "pending": "審査待ち",
        "rejected": "却下",
        "issued_by": "Pearnly 発行",
        "generated": "発行日時",
        "disclaimer": "本書はチャージ記録であり、税務上の請求書ではありません。",
    },
}


def _t(lang: str, key: str) -> str:
    return _I18N.get(lang, _I18N["en"]).get(key, _I18N["en"].get(key, key))


def _register_thai_font():
    """注册嵌入 Sarabun → (base, bold);失败回落 Helvetica。"""
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


def _status_label(lang: str, status: str) -> str:
    s = (status or "").strip().lower()
    if s == "approved":
        return _t(lang, "approved")
    if s == "rejected":
        return _t(lang, "rejected")
    return _t(lang, "pending")


def build_topup_receipt_pdf(*, lang: str, tenant_name: str, receipt: dict) -> bytes:
    """单笔充值凭证 → PDF bytes。receipt 含 id/amount_thb/payer_name/note/status/
    created_at/reviewed_at(均已格式化为字符串)。"""
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import mm
    from reportlab.platypus import (
        SimpleDocTemplate,
        Paragraph,
        Spacer,
        Table,
        TableStyle,
    )
    from reportlab.lib.styles import ParagraphStyle

    if lang not in _I18N:
        lang = "en"
    base, bold = _register_thai_font()

    brand = ParagraphStyle("brand", fontName=bold, fontSize=20, textColor=colors.HexColor(_BRAND))
    title = ParagraphStyle("title", fontName=bold, fontSize=15, textColor=colors.HexColor(_INK))
    label = ParagraphStyle("label", fontName=base, fontSize=10, textColor=colors.HexColor(_MUTED))
    value = ParagraphStyle("value", fontName=bold, fontSize=11.5, textColor=colors.HexColor(_INK))
    amount = ParagraphStyle("amount", fontName=bold, fontSize=26, textColor=colors.HexColor(_BRAND))
    foot = ParagraphStyle("foot", fontName=base, fontSize=8.5, textColor=colors.HexColor(_MUTED))

    amt = Decimal(str(receipt.get("amount_thb") or 0))

    def kv(k, v):
        return [Paragraph(_t(lang, k), label), Paragraph(str(v or "—"), value)]

    rows = [
        kv("receipt_no", "#" + str(receipt.get("id") or "")),
        kv("company", tenant_name or "—"),
        kv("status", _status_label(lang, receipt.get("status") or "")),
        kv("payer", receipt.get("payer_name") or "—"),
        kv("created", receipt.get("created_at") or "—"),
    ]
    if (receipt.get("status") or "").lower() == "approved" and receipt.get("reviewed_at"):
        rows.append(kv("credited", receipt.get("reviewed_at")))
    if receipt.get("note"):
        rows.append(kv("note", receipt.get("note")))

    info = Table(rows, colWidths=[40 * mm, 120 * mm])
    info.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 7),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
                ("LINEBELOW", (0, 0), (-1, -2), 0.5, colors.HexColor(_LINE)),
            ]
        )
    )

    amount_block = Table(
        [[Paragraph(_t(lang, "amount"), label)], [Paragraph(f"฿ {amt:,.2f}", amount)]],
        colWidths=[160 * mm],
    )
    amount_block.setStyle(
        TableStyle(
            [
                ("TOPPADDING", (0, 0), (-1, -1), 2),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f5f3ff")),
                ("LEFTPADDING", (0, 0), (-1, -1), 14),
                ("TOPPADDING", (0, 0), (0, 0), 12),
                ("BOTTOMPADDING", (1, 0), (1, 0), 12),
            ]
        )
    )

    story = [
        Paragraph("Pearnly", brand),
        Spacer(1, 4 * mm),
        Paragraph(_t(lang, "title"), title),
        Spacer(1, 6 * mm),
        amount_block,
        Spacer(1, 8 * mm),
        info,
        Spacer(1, 10 * mm),
        Paragraph(_t(lang, "issued_by") + " · " + _t(lang, "disclaimer"), foot),
    ]

    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=18 * mm,
        rightMargin=18 * mm,
        topMargin=20 * mm,
        bottomMargin=18 * mm,
        title=f"{_t(lang, 'title')} #{receipt.get('id') or ''}",
    )
    doc.build(story)
    return buf.getvalue()
