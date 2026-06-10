# -*- coding: utf-8 -*-
"""出账本/报税材料 PDF 渲染(屏4 下载/预览/打包 · books.py 聚合数据的表格化)。

字体/混排复用 usage_report(PR-CJK + PR-Thai script-aware runs);版式 = 标题 + 期间 +
表格(reportlab platypus)。标题/表头 4 语(文件内容也是用户可见面 · i18n 铁律)。
"""

from __future__ import annotations

import io
import zipfile
from decimal import Decimal

from services.usage.usage_report_pdf_text import _build_paragraph_text, _register_fonts

_L = {
    "title.gl": {
        "zh": "总账",
        "th": "บัญชีแยกประเภททั่วไป",
        "en": "General Ledger",
        "ja": "総勘定元帳",
    },
    "title.subsidiary": {
        "zh": "明细账",
        "th": "บัญชีแยกประเภทรายตัว",
        "en": "Subsidiary Ledger",
        "ja": "補助元帳",
    },
    "title.trial_balance": {"zh": "试算表", "th": "งบทดลอง", "en": "Trial Balance", "ja": "試算表"},
    "title.vat": {
        "zh": "进项税 / 销项税报告",
        "th": "รายงานภาษีซื้อ-ภาษีขาย",
        "en": "Input/Output VAT Report",
        "ja": "仕入/売上VAT報告",
    },
    "title.wht": {
        "zh": "预扣税明细",
        "th": "รายละเอียดภาษีหัก ณ ที่จ่าย",
        "en": "Withholding Tax Detail",
        "ja": "源泉徴収税明細",
    },
    "title.financials": {
        "zh": "损益表 · 资产负债表",
        "th": "งบกำไรขาดทุน · งบแสดงฐานะการเงิน",
        "en": "P&L · Balance Sheet",
        "ja": "損益計算書 · 貸借対照表",
    },
    "h.code": {"zh": "编号", "th": "รหัส", "en": "Code", "ja": "番号"},
    "h.account": {"zh": "科目", "th": "บัญชี", "en": "Account", "ja": "勘定科目"},
    "h.opening": {"zh": "期初", "th": "ยกมา", "en": "Opening", "ja": "期首"},
    "h.debit": {"zh": "借方", "th": "เดบิต", "en": "Debit", "ja": "借方"},
    "h.credit": {"zh": "贷方", "th": "เครดิต", "en": "Credit", "ja": "貸方"},
    "h.closing": {"zh": "期末", "th": "ยกไป", "en": "Closing", "ja": "期末"},
    "h.date": {"zh": "日期", "th": "วันที่", "en": "Date", "ja": "日付"},
    "h.voucher": {"zh": "凭证号", "th": "เลขที่ใบสำคัญ", "en": "Voucher", "ja": "伝票番号"},
    "h.description": {"zh": "摘要", "th": "รายการ", "en": "Description", "ja": "摘要"},
    "h.amount": {"zh": "金额", "th": "จำนวนเงิน", "en": "Amount", "ja": "金額"},
    "h.total": {"zh": "合计", "th": "รวม", "en": "Total", "ja": "合計"},
    "sec.output_vat": {"zh": "销项税", "th": "ภาษีขาย", "en": "Output VAT", "ja": "売上VAT"},
    "sec.input_vat": {"zh": "进项税", "th": "ภาษีซื้อ", "en": "Input VAT", "ja": "仕入VAT"},
    "sec.vat_payable": {
        "zh": "应交 VAT(销项−进项)",
        "th": "ภาษีมูลค่าเพิ่มที่ต้องชำระ",
        "en": "VAT Payable",
        "ja": "未払VAT",
    },
    "sec.revenue": {"zh": "收入", "th": "รายได้", "en": "Revenue", "ja": "収益"},
    "sec.expense": {"zh": "费用", "th": "ค่าใช้จ่าย", "en": "Expense", "ja": "費用"},
    "sec.net_profit": {"zh": "本期净利", "th": "กำไรสุทธิ", "en": "Net Profit", "ja": "当期純利益"},
    "sec.assets": {"zh": "资产", "th": "สินทรัพย์", "en": "Assets", "ja": "資産"},
    "sec.liabilities": {"zh": "负债", "th": "หนี้สิน", "en": "Liabilities", "ja": "負債"},
    "sec.equity": {
        "zh": "权益(含本期累计净利)",
        "th": "ส่วนของเจ้าของ",
        "en": "Equity (incl. earnings)",
        "ja": "純資産",
    },
}


def _t(key: str, lang: str) -> str:
    d = _L[key]
    return d.get(lang) or d["th"]


def _fmt(v) -> str:
    return f"{Decimal(str(v or 0)):,.2f}"


def _name(row: dict, lang: str) -> str:
    if lang == "th":
        return row.get("name_th") or row.get("name_zh") or ""
    return row.get("name_zh") or row.get("name_th") or ""


def _render_table(title: str, period: str, headers: list, rows: list, widths: list) -> bytes:
    """rows 元素:(cells, kind) · kind ∈ '' / 'section' / 'total' 控底色加粗。"""
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_LEFT, TA_RIGHT
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

    base, bold = _register_fonts()

    def P(text, b=False, align=TA_LEFT, size=8.5):
        style = ParagraphStyle(
            "c", fontName=(bold if b else base), fontSize=size, leading=size + 3, alignment=align
        )
        return Paragraph(
            _build_paragraph_text(str(text if text not in (None, "") else "—"), b), style
        )

    data = [[P(h, True) for h in headers]]
    style_cmds = [
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#D7D7D2")),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#F1F1EC")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]
    for cells, kind in rows:
        r = len(data)
        row_cells = []
        for c in cells:
            is_num = isinstance(c, Decimal)
            text = _fmt(c) if is_num else c
            row_cells.append(P(text, kind in ("section", "total"), TA_RIGHT if is_num else TA_LEFT))
        data.append(row_cells)
        if kind == "section":
            style_cmds.append(("BACKGROUND", (0, r), (-1, r), colors.HexColor("#EFF4FF")))
        elif kind == "total":
            style_cmds.append(("BACKGROUND", (0, r), (-1, r), colors.HexColor("#F8F8F5")))

    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=14 * mm,
        rightMargin=14 * mm,
        topMargin=14 * mm,
        bottomMargin=14 * mm,
    )
    head = [
        P(title, True, size=14),
        Spacer(1, 2 * mm),
        P(period, False, size=9),
        Spacer(1, 4 * mm),
        Table(data, colWidths=[w * mm for w in widths], style=TableStyle(style_cmds), repeatRows=1),
    ]
    doc.build(head)
    return buf.getvalue()


def render(kind: str, payload: dict, *, lang: str = "th") -> bytes:
    period = payload.get("period") or ""
    if kind == "gl":
        rows = [
            (
                [a["code"], _name(a, lang), a["opening"], a["debit"], a["credit"], a["closing"]],
                "",
            )
            for a in payload["accounts"]
        ]
        rows.append(
            (
                [
                    _t("h.total", lang),
                    "",
                    "",
                    payload["totals"]["debit"],
                    payload["totals"]["credit"],
                    "",
                ],
                "total",
            )
        )
        headers = [
            _t("h.code", lang),
            _t("h.account", lang),
            _t("h.opening", lang),
            _t("h.debit", lang),
            _t("h.credit", lang),
            _t("h.closing", lang),
        ]
        return _render_table(_t("title.gl", lang), period, headers, rows, [18, 56, 27, 27, 27, 27])
    if kind == "trial_balance":
        rows = [([r["code"], _name(r, lang), r["debit"], r["credit"]], "") for r in payload["rows"]]
        rows.append(
            (
                [_t("h.total", lang), "", payload["totals"]["debit"], payload["totals"]["credit"]],
                "total",
            )
        )
        headers = [
            _t("h.code", lang),
            _t("h.account", lang),
            _t("h.debit", lang),
            _t("h.credit", lang),
        ]
        return _render_table(
            _t("title.trial_balance", lang), period, headers, rows, [22, 84, 38, 38]
        )
    if kind == "subsidiary":
        rows = []
        for a in payload["accounts"]:
            rows.append(([f"{a['code']} {_name(a, lang)}", "", "", "", ""], "section"))
            for ln in a["lines"]:
                rows.append(
                    (
                        [
                            str(ln["date"]),
                            ln["voucher_no"],
                            ln["description"],
                            ln["debit"],
                            ln["credit"],
                        ],
                        "",
                    )
                )
            rows.append(
                ([_t("h.total", lang), "", "", a["debit_total"], a["credit_total"]], "total")
            )
        headers = [
            _t("h.date", lang),
            _t("h.voucher", lang),
            _t("h.description", lang),
            _t("h.debit", lang),
            _t("h.credit", lang),
        ]
        return _render_table(
            _t("title.subsidiary", lang), period, headers, rows, [22, 26, 80, 27, 27]
        )
    if kind == "vat":
        rows = [([_t("sec.output_vat", lang), "", "", ""], "section")]
        rows += [
            ([str(r["date"]), r["voucher_no"], r["ref"] or r["description"], r["amount"]], "")
            for r in payload["sales"]["rows"]
        ]
        rows.append(([_t("h.total", lang), "", "", payload["sales"]["total"]], "total"))
        rows.append(([_t("sec.input_vat", lang), "", "", ""], "section"))
        rows += [
            ([str(r["date"]), r["voucher_no"], r["ref"] or r["description"], r["amount"]], "")
            for r in payload["purchase"]["rows"]
        ]
        rows.append(([_t("h.total", lang), "", "", payload["purchase"]["total"]], "total"))
        rows.append(([_t("sec.vat_payable", lang), "", "", payload["vat_payable"]], "total"))
        headers = [
            _t("h.date", lang),
            _t("h.voucher", lang),
            _t("h.description", lang),
            _t("h.amount", lang),
        ]
        return _render_table(_t("title.vat", lang), period, headers, rows, [24, 30, 90, 38])
    if kind == "wht":
        rows = [
            ([str(r["date"]), r["voucher_no"], r["ref"] or r["description"], r["amount"]], "")
            for r in payload["rows"]
        ]
        rows.append(([_t("h.total", lang), "", "", payload["total"]], "total"))
        headers = [
            _t("h.date", lang),
            _t("h.voucher", lang),
            _t("h.description", lang),
            _t("h.amount", lang),
        ]
        return _render_table(_t("title.wht", lang), period, headers, rows, [24, 30, 90, 38])
    if kind == "financials":
        pnl, bs = payload["pnl"], payload["balance_sheet"]
        rows = [([_t("sec.revenue", lang), ""], "section")]
        rows += [([f"{r['code']} {_name(r, lang)}", r["amount"]], "") for r in pnl["revenue"]]
        rows.append(([_t("h.total", lang), pnl["revenue_total"]], "total"))
        rows.append(([_t("sec.expense", lang), ""], "section"))
        rows += [([f"{r['code']} {_name(r, lang)}", r["amount"]], "") for r in pnl["expense"]]
        rows.append(([_t("h.total", lang), pnl["expense_total"]], "total"))
        rows.append(([_t("sec.net_profit", lang), pnl["net_profit"]], "total"))
        rows.append(([_t("sec.assets", lang), ""], "section"))
        rows += [([f"{r['code']} {_name(r, lang)}", r["amount"]], "") for r in bs["assets"]]
        rows.append(([_t("h.total", lang), bs["asset_total"]], "total"))
        rows.append(([_t("sec.liabilities", lang), ""], "section"))
        rows += [([f"{r['code']} {_name(r, lang)}", r["amount"]], "") for r in bs["liabilities"]]
        rows.append(([_t("h.total", lang), bs["liability_total"]], "total"))
        rows.append(([_t("sec.equity", lang), bs["equity_total"]], "total"))
        headers = [_t("h.account", lang), _t("h.amount", lang)]
        return _render_table(_t("title.financials", lang), period, headers, rows, [130, 52])
    raise ValueError(f"unknown report kind: {kind}")


def export_package(payloads: dict, *, period: str, lang: str = "th") -> bytes:
    """payloads: kind → books.py 聚合数据。打包全部 PDF 成 zip(屏4「打包本月」)。"""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for kind, payload in payloads.items():
            zf.writestr(f"{kind}_{period}.pdf", render(kind, payload, lang=lang))
    return buf.getvalue()
