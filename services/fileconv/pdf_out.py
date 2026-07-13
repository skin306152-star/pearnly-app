# -*- coding: utf-8 -*-
"""K2 · ConvertResult → 打印级 PDF(泰文混排 · 页眉页脚 · 守恒校验戳)。

版式照 services/accounting/books_pdf.py 范式:reportlab platypus,字体/script-aware 混排
复用 usage_report_pdf_text(泰/中/日已解决,零新字体代码)。守恒结果不新算——戳文案只读
ConvertResult.conserved/issues,不重做 validate.py 的判断。

戳三态(诚实,不假背书):
  · 台账类(GL/流水)且守恒全过 → 绿色确认戳
  · 台账类但有不平行 → 戳点名处数,表内对应行标黄(line_no 直接映射行位置)
  · 非台账/认不出结构(generic)→ 明示未做数字校验,不背书
"""

from __future__ import annotations

import io
from datetime import datetime, timezone
from decimal import Decimal
from functools import partial
from typing import List

from services.fileconv.model import (
    BANK_STATEMENT,
    GL_LEDGER,
    ISSUE_ROW_HIGHLIGHT,
    REJECT_STATUSES,
    ConvertResult,
    Table,
)
from services.usage.usage_report_pdf_text import _build_paragraph_text, _register_fonts

_LEDGER_TYPES = (GL_LEDGER, BANK_STATEMENT)
_LANDSCAPE_COL_THRESHOLD = 8
_ISSUE_ROW_BG = "#" + ISSUE_ROW_HIGHLIGHT  # PDF/xlsx 不平行同一视觉语言(单源在 model)

_L = {
    "title.gl": {
        "zh": "总账",
        "th": "บัญชีแยกประเภททั่วไป",
        "en": "General Ledger",
        "ja": "総勘定元帳",
    },
    "title.bank": {
        "zh": "银行流水",
        "th": "รายการเดินบัญชี",
        "en": "Bank Statement",
        "ja": "銀行明細",
    },
    "title.generic": {"zh": "表格", "th": "ตาราง", "en": "Table", "ja": "表"},
    "h.source": {"zh": "来源文件", "th": "ไฟล์ต้นทาง", "en": "Source file", "ja": "元ファイル"},
    "h.generated": {"zh": "生成日期", "th": "วันที่สร้าง", "en": "Generated on", "ja": "生成日"},
    "stamp.conserved": {
        "zh": "✓ 余额链/借贷合计已校验",
        "th": "✓ ตรวจสอบยอดคงเหลือ/ยอดเดบิต-เครดิตแล้ว",
        "en": "✓ Balance chain / debit-credit verified",
        "ja": "✓ 残高チェーン/借方貸方を検証済み",
    },
    "stamp.has_issues": {
        "zh": "⚠ {n} 处不平(见明细)",
        "th": "⚠ พบยอดไม่ตรง {n} จุด (ดูรายละเอียดในตาราง)",
        "en": "⚠ {n} discrepancies found (see highlighted rows)",
        "ja": "⚠ 不一致 {n} 件(該当行を参照)",
    },
    "stamp.generic": {
        "zh": "未识别为财务台账,未做数字校验",
        "th": "ไม่สามารถระบุเป็นบัญชีทางการเงินได้ · ไม่มีการตรวจสอบตัวเลข",
        "en": "Not recognized as a financial ledger — no numeric validation performed",
        "ja": "会計帳簿として認識できず、数値検証は未実施です",
    },
    "reject.title": {
        "zh": "转换被拒绝",
        "th": "การแปลงถูกปฏิเสธ",
        "en": "Conversion rejected",
        "ja": "変換は拒否されました",
    },
    "reject.body": {
        "zh": "此文件未能生成规范 PDF(格式不支持 / 已损坏 / 无可读内容)。",
        "th": "ไม่สามารถแปลงไฟล์นี้เป็น PDF ได้ (รูปแบบไม่รองรับ / ไฟล์เสียหาย / ไม่มีเนื้อหาที่อ่านได้)",
        "en": "This file could not be converted to PDF (unsupported format / corrupt / no readable content).",
        "ja": "このファイルはPDFに変換できませんでした(未対応形式・破損・読み取り可能な内容なし)。",
    },
    "page": {"zh": "第 {p} 页", "th": "หน้า {p}", "en": "Page {p}", "ja": "{p} ページ"},
}

_TITLE_KEYS = {GL_LEDGER: "title.gl", BANK_STATEMENT: "title.bank"}


def _t(key: str, lang: str) -> str:
    d = _L[key]
    return d.get(lang) or d["th"]


def _now_str() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def _stamp_text(result: ConvertResult, lang: str) -> str:
    if result.doc_type in _LEDGER_TYPES:
        if result.conserved:
            return _t("stamp.conserved", lang)
        return _t("stamp.has_issues", lang).replace("{n}", str(len(result.issues)))
    return _t("stamp.generic", lang)


def _is_numeric(v) -> bool:
    return isinstance(v, Decimal) or (isinstance(v, (int, float)) and not isinstance(v, bool))


def _cell_text(v) -> str:
    if v is None or v == "":
        return ""
    if _is_numeric(v):
        return f"{Decimal(str(v)):,.2f}"
    return str(v)


def _draw_furniture(canvas, doc, *, header_text: str, stamp_text: str, base: str) -> None:
    """每页页眉/页脚。文本走 Paragraph(script-aware 混排),不用 canvas.drawString 裸绘——
    单一字体覆盖不了混排泰/中/日,同 books_pdf 解法。"""
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.platypus import Paragraph

    canvas.saveState()
    w, h = doc.pagesize
    style = ParagraphStyle(
        "furniture", fontName=base, fontSize=7.5, leading=10, textColor="#666666"
    )

    header = Paragraph(_build_paragraph_text(header_text), style)
    header.wrapOn(canvas, w - doc.leftMargin - doc.rightMargin, 12)
    header.drawOn(canvas, doc.leftMargin, h - doc.topMargin + 4)

    footer = Paragraph(_build_paragraph_text(stamp_text), style)
    footer.wrapOn(canvas, w - doc.leftMargin - doc.rightMargin - 50, 12)
    footer.drawOn(canvas, doc.leftMargin, doc.bottomMargin - 14)

    canvas.setFont("Helvetica", 7.5)
    canvas.drawRightString(w - doc.rightMargin, doc.bottomMargin - 14, str(doc.page))
    canvas.restoreState()


def _table_flowable(table: Table, bad_lines: set, avail_width: float):
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_LEFT, TA_RIGHT
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.platypus import LongTable, Paragraph, Spacer, TableStyle

    base, bold = _register_fonts()
    # 样式只有三种组合,提到循环外一次建好——千行 GL 表逐格现造 ParagraphStyle
    # 是 O(rows×cols) 次全量属性继承,纯浪费(下载 PDF 是同步热路径)。
    header_style = ParagraphStyle("h", fontName=bold, fontSize=8.2, leading=11, alignment=TA_LEFT)
    num_style = ParagraphStyle("n", fontName=base, fontSize=8, leading=11, alignment=TA_RIGHT)
    text_style = ParagraphStyle("t", fontName=base, fontSize=8, leading=11, alignment=TA_LEFT)

    def cell(text, is_num, header=False):
        style = header_style if header else (num_style if is_num else text_style)
        return Paragraph(_build_paragraph_text(str(text), header), style)

    data = [[cell(h, False, header=True) for h in table.columns]]
    for row in table.rows:
        data.append([cell(_cell_text(v), _is_numeric(v)) for v in row])

    col_w = avail_width / max(len(table.columns), 1)
    style_cmds = [
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#D7D7D2")),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2C5282")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]
    for line_no in bad_lines:
        if 0 < line_no < len(data):
            style_cmds.append(
                ("BACKGROUND", (0, line_no), (-1, line_no), colors.HexColor(_ISSUE_ROW_BG))
            )

    title_style = ParagraphStyle("title", fontName=bold, fontSize=11, leading=14)
    return [
        Paragraph(_build_paragraph_text(table.name, True), title_style),
        Spacer(1, 4),
        LongTable(
            data, colWidths=[col_w] * len(table.columns), style=TableStyle(style_cmds), repeatRows=1
        ),
        Spacer(1, 10),
    ]


def _render_reject(result: ConvertResult, lang: str) -> bytes:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

    base, bold = _register_fonts()
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=20 * mm,
        rightMargin=20 * mm,
        topMargin=30 * mm,
        bottomMargin=20 * mm,
    )
    title_style = ParagraphStyle("t", fontName=bold, fontSize=15, leading=20)
    body_style = ParagraphStyle("b", fontName=base, fontSize=10, leading=15)
    story = [
        Paragraph(_build_paragraph_text(_t("reject.title", lang), True), title_style),
        Spacer(1, 10),
        Paragraph(_build_paragraph_text(_t("reject.body", lang)), body_style),
        Spacer(1, 6),
        Paragraph(_build_paragraph_text(f"{result.source_name} · {result.status}"), body_style),
    ]
    doc.build(story)
    return buf.getvalue()


def render(result: ConvertResult, *, lang: str = "th") -> bytes:
    """ConvertResult → PDF bytes。拒绝态/空表 → 诚实一页说明;否则逐张表渲染,列多
    (>8)自动横版(单文档一个纸张方向 · 混合宽表场景不在本期范围内)。"""
    if result.status in REJECT_STATUSES or not result.tables:
        return _render_reject(result, lang)

    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib.units import mm
    from reportlab.platypus import PageBreak, SimpleDocTemplate

    wide = any(len(t.columns) > _LANDSCAPE_COL_THRESHOLD for t in result.tables)
    pagesize = landscape(A4) if wide else A4
    base, _ = _register_fonts()

    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=pagesize,
        leftMargin=12 * mm,
        rightMargin=12 * mm,
        topMargin=18 * mm,
        bottomMargin=18 * mm,
    )
    avail_width = pagesize[0] - doc.leftMargin - doc.rightMargin

    bad_lines = {issue.line_no for issue in result.issues}
    story: List = []
    for i, table in enumerate(result.tables):
        if i:
            story.append(PageBreak())
        story.extend(_table_flowable(table, bad_lines, avail_width))

    doc_title = _t(_TITLE_KEYS.get(result.doc_type, "title.generic"), lang)
    header_text = f"{doc_title} · {result.source_name} · {_t('h.generated', lang)} {_now_str()}"
    stamp_text = _stamp_text(result, lang)
    furniture = partial(_draw_furniture, header_text=header_text, stamp_text=stamp_text, base=base)
    doc.build(story, onFirstPage=furniture, onLaterPages=furniture)
    return buf.getvalue()
