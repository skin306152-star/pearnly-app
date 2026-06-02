# -*- coding: utf-8 -*-
"""bank_recon_excel.py · Pearnly · 4-sheet openpyxl reconciliation export.

Split verbatim from bank_recon_v2.py. Pure presentation: i18n labels +
openpyxl workbook build, no matching/judgement logic.

Orchestrator: Sheet 1(สรุป)→ bank_recon_excel_summary · 共享样式 → bank_recon_excel_styles
· i18n → bank_recon_excel_i18n · 使用说明 → bank_recon_excel_usage。Sheet 2/5/6 builder 在本文件。
"""

import io
from datetime import date
from typing import Any, Dict, List, Optional

import openpyxl
from openpyxl.styles import Font, Alignment, PatternFill
from openpyxl.utils import get_column_letter

from services.recon.bank_recon_types import BankReconRow, BankReconSummary
from services.recon.bank_recon_excel_styles import (
    COLOR_MATCHED,
    COLOR_L2,
    COLOR_L3,
    COLOR_GL_ONLY,
    COLOR_ST_ONLY,
    _hdr_style,
    _border_range,
    _fmt_date,
)
from services.recon.bank_recon_excel_summary import _build_summary_sheet

# 4 语标签 + 翻译 helper · sheet builder 用 + facade re-export(契约)
from services.recon.bank_recon_excel_i18n import (
    _t,
    _layer_label,
    _status_label,
)

# 使用说明文案 · summary 模块用 · 此处 re-export 保契约
from services.recon.bank_recon_excel_usage import _USAGE_BLOCKS  # noqa: F401  facade re-export


def _build_match_results_sheet(wb, recon_rows: List[BankReconRow], lang: str) -> None:
    # ══════════════════════════════════════════════════════════════════
    # SHEET 2: ผลการจับคู่ (Consolidated Match Results · v118.34)
    # Combines what were previously 3 sheets (matched + unmatched_gl + unmatched_stmt).
    # First column "Status" distinguishes:
    #   - "✓ Matched"  (matched rows, color by match layer L1/L2/L3)
    #   - "GL Debit/Credit Only"  (purple tint)
    #   - "Stmt Withdrawal/Deposit Only"  (blue tint)
    # Match Layer column shows L1/L2/L3 for matched rows, "—" for unmatched.
    # ══════════════════════════════════════════════════════════════════
    ws2 = wb.create_sheet(_t("sh_match_results", lang))
    ws2.sheet_view.showGridLines = False

    match_cols = [
        (_t("col_status", lang), 18),
        (_t("col_match_layer", lang), 12),
        (_t("col_date", lang), 12),
        (_t("col_desc", lang), 26),
        (_t("col_withdrawal", lang), 12),
        (_t("col_deposit", lang), 12),
        (_t("col_balance", lang), 12),
        (_t("col_gl_date", lang), 12),
        (_t("col_gl_doc", lang), 14),
        (_t("col_gl_acct", lang), 11),
        (_t("col_gl_desc", lang), 26),
        (_t("col_gl_debit", lang), 12),
        (_t("col_gl_credit", lang), 12),
        (_t("col_date_diff", lang), 10),
        (_t("col_source_stmt", lang), 18),
        (_t("col_source_gl", lang), 18),
    ]
    for ci, (hdr, width) in enumerate(match_cols, 1):
        _hdr_style(ws2, 1, ci, hdr)
        ws2.column_dimensions[get_column_letter(ci)].width = width

    # Group + sort the recon_rows by category
    matched_rows_for_export = sorted(
        [rr for rr in recon_rows if rr.match_status == "matched"],
        key=lambda x: (x.stmt_date or date.min, x.gl_date or date.min),
    )
    gl_only_rows_for_export = sorted(
        [rr for rr in recon_rows if rr.match_status in ("gl_debit_only", "gl_credit_only")],
        key=lambda x: (x.gl_date or date.min, x.gl_doc_no or ""),
    )
    stmt_only_rows_for_export = sorted(
        [
            rr
            for rr in recon_rows
            if rr.match_status in ("stmt_withdrawal_only", "stmt_deposit_only")
        ],
        key=lambda x: (x.stmt_date or date.min, x.stmt_desc or ""),
    )

    _DASH = "—"

    ri = 2
    # Matched block (tinted by match layer)
    for row in matched_rows_for_export:
        layer_fill_color = (
            COLOR_MATCHED
            if row.match_layer == 1
            else COLOR_L2 if row.match_layer == 2 else COLOR_L3
        )
        fill = PatternFill("solid", fgColor=layer_fill_color)
        vals = [
            _t("status_matched", lang),
            _layer_label(row.match_layer, lang),
            _fmt_date(row.stmt_date),
            row.stmt_desc,
            row.stmt_withdrawal or "",
            row.stmt_deposit or "",
            row.stmt_balance or "",
            _fmt_date(row.gl_date),
            row.gl_doc_no,
            row.gl_account_code,
            row.gl_desc,
            row.gl_debit or "",
            row.gl_credit or "",
            row.date_diff_days if row.date_diff_days is not None else "",
            row.source_stmt_file,
            row.source_gl_file,
        ]
        for ci, val in enumerate(vals, 1):
            cell = ws2.cell(ri, ci, val)
            cell.fill = fill
            if isinstance(val, float) and val != "":
                cell.number_format = "#,##0.00"
                cell.alignment = Alignment(horizontal="right")
            else:
                cell.alignment = Alignment(vertical="center")
            cell.font = Font(size=9)
        ri += 1

    # GL-only block (purple tint)
    for row in gl_only_rows_for_export:
        fill = PatternFill("solid", fgColor=COLOR_GL_ONLY if ri % 2 == 0 else "F3E8FF")
        vals = [
            _status_label(row.match_status, lang),
            _DASH,
            "",  # stmt date
            "",  # stmt desc
            "",  # stmt withdrawal
            "",  # stmt deposit
            "",  # stmt balance
            _fmt_date(row.gl_date),
            row.gl_doc_no,
            row.gl_account_code,
            row.gl_desc,
            row.gl_debit or "",
            row.gl_credit or "",
            "",  # date diff
            "",  # source stmt
            row.source_gl_file,
        ]
        for ci, val in enumerate(vals, 1):
            cell = ws2.cell(ri, ci, val)
            cell.fill = fill
            if isinstance(val, float) and val != "":
                cell.number_format = "#,##0.00"
                cell.alignment = Alignment(horizontal="right")
            else:
                cell.alignment = Alignment(vertical="center")
            cell.font = Font(size=9)
        ri += 1

    # Stmt-only block (blue tint)
    for row in stmt_only_rows_for_export:
        fill = PatternFill("solid", fgColor=COLOR_ST_ONLY if ri % 2 == 0 else "EBF5FB")
        vals = [
            _status_label(row.match_status, lang),
            _DASH,
            _fmt_date(row.stmt_date),
            row.stmt_desc,
            row.stmt_withdrawal or "",
            row.stmt_deposit or "",
            row.stmt_balance or "",
            "",  # gl date
            "",  # gl doc
            "",  # gl acct
            "",  # gl desc
            "",  # gl debit
            "",  # gl credit
            "",  # date diff
            row.source_stmt_file,
            "",  # source gl
        ]
        for ci, val in enumerate(vals, 1):
            cell = ws2.cell(ri, ci, val)
            cell.fill = fill
            if isinstance(val, float) and val != "":
                cell.number_format = "#,##0.00"
                cell.alignment = Alignment(horizontal="right")
            else:
                cell.alignment = Alignment(vertical="center")
            cell.font = Font(size=9)
        ri += 1

    _border_range(ws2, 1, max(1, ri - 1), 1, len(match_cols))
    ws2.freeze_panes = "C2"  # freeze status + match layer cols


def _build_stmt_detail_sheet(wb, recon_rows: List[BankReconRow], lang: str) -> None:
    # ══════════════════════════════════════════════════════════════════
    # SHEET 5: Statement Detail (all parsed statement rows + OCR check)
    # v118.33.13.0
    # ══════════════════════════════════════════════════════════════════
    ws5 = wb.create_sheet(_t("sh_stmt_detail", lang))
    ws5.sheet_view.showGridLines = False

    sd_cols = [
        (_t("col_date", lang), 12),
        (_t("col_desc", lang), 38),
        (_t("col_withdrawal", lang), 14),
        (_t("col_deposit", lang), 14),
        (_t("col_balance", lang), 14),
        (_t("col_confidence", lang), 12),
        (_t("col_balance_ok", lang), 12),
        (_t("col_source_file", lang), 22),
    ]
    for ci, (hdr, width) in enumerate(sd_cols, 1):
        _hdr_style(ws5, 1, ci, hdr)
        ws5.column_dimensions[get_column_letter(ci)].width = width

    CONF_LBL = {
        "high": _t("conf_high", lang),
        "medium": _t("conf_medium", lang),
        "low": _t("conf_low", lang),
    }
    CONF_FILL = {"high": "D8F3DC", "medium": "FFF3CD", "low": "FFDAD6"}

    # Source: stmt-side rows (all of them — matched + stmt-only)
    stmt_side_rows = [
        r
        for r in recon_rows
        if r.stmt_date is not None
        or r.stmt_balance != 0
        or r.stmt_withdrawal != 0
        or r.stmt_deposit != 0
    ]
    # Sort by stmt_date
    stmt_side_rows.sort(key=lambda x: (x.stmt_date or date.min, x.stmt_desc))

    for ri, row in enumerate(stmt_side_rows, 2):
        conf = (row.stmt_confidence or "high").lower()
        if getattr(row, "stmt_autocorrected", False):
            # v118.35.0.62 · 系统按余额自动修正过 · 显式标黄『已修正』· 透明 · 提示可复核
            bal_str = _t("bal_fixed", lang)
            bal_fill = "FFE082"
        elif row.stmt_balance_ok is True:
            bal_str = _t("bal_ok", lang)
            bal_fill = "D8F3DC"
        elif row.stmt_balance_ok is False:
            bal_str = _t("bal_warn", lang)
            bal_fill = "FFDAD6"
        else:
            bal_str = _t("bal_na", lang)
            bal_fill = None
        vals = [
            _fmt_date(row.stmt_date),
            row.stmt_desc,
            row.stmt_withdrawal or "",
            row.stmt_deposit or "",
            row.stmt_balance or "",
            CONF_LBL.get(conf, conf),
            bal_str,
            row.source_stmt_file,
        ]
        for ci, val in enumerate(vals, 1):
            cell = ws5.cell(ri, ci, val)
            cell.font = Font(size=9)
            if isinstance(val, float) and val:
                cell.number_format = "#,##0.00"
                cell.alignment = Alignment(horizontal="right")
            # Highlight confidence/balance columns
            if ci == 6:
                cell.fill = PatternFill("solid", fgColor=CONF_FILL.get(conf, "FFFFFF"))
                cell.alignment = Alignment(horizontal="center")
            if ci == 7 and bal_fill:
                cell.fill = PatternFill("solid", fgColor=bal_fill)
                cell.alignment = Alignment(horizontal="center")
        # Tint the whole row red if balance check failed
        if row.stmt_balance_ok is False:
            for ci in range(1, len(vals) + 1):
                if ws5.cell(ri, ci).fill.fgColor.rgb in (None, "00000000", "FFFFFFFF"):
                    ws5.cell(ri, ci).fill = PatternFill("solid", fgColor="FEF2F2")

    _border_range(ws5, 1, max(1, len(stmt_side_rows) + 1), 1, len(sd_cols))
    ws5.freeze_panes = "A2"


def _build_gl_detail_sheet(wb, recon_rows: List[BankReconRow], lang: str) -> None:
    # ══════════════════════════════════════════════════════════════════
    # SHEET 6: GL Detail (all GL rows reconstructed from recon_rows)
    # v118.34 · Mirrors Sheet 5 (Statement Detail) — same visual idiom
    # ══════════════════════════════════════════════════════════════════
    ws_gl = wb.create_sheet(_t("sh_gl_detail", lang))
    ws_gl.sheet_view.showGridLines = False

    gld_cols = [
        (_t("col_date", lang), 12),
        (_t("col_doc_no", lang), 16),
        (_t("col_account_code", lang), 14),
        (_t("col_desc", lang), 38),
        (_t("col_debit", lang), 14),
        (_t("col_credit", lang), 14),
        (_t("col_source_file", lang), 22),
    ]
    for ci, (hdr, width) in enumerate(gld_cols, 1):
        _hdr_style(ws_gl, 1, ci, hdr)
        ws_gl.column_dimensions[get_column_letter(ci)].width = width

    # Source: every recon_row that carries GL data
    # (matched rows + gl_debit_only + gl_credit_only).
    # Stmt-only rows have no GL data → excluded.
    gl_data_rows = [
        r
        for r in recon_rows
        if r.match_status == "matched" or r.match_status in ("gl_debit_only", "gl_credit_only")
    ]
    gl_data_rows.sort(
        key=lambda x: (x.gl_date or date.min, x.gl_doc_no or "", x.gl_account_code or "")
    )

    for ri, row in enumerate(gl_data_rows, 2):
        alt_fill = "F8F9FA" if ri % 2 == 0 else None
        vals = [
            _fmt_date(row.gl_date),
            row.gl_doc_no,
            row.gl_account_code,
            row.gl_desc,
            row.gl_debit if row.gl_debit else "",
            row.gl_credit if row.gl_credit else "",
            row.source_gl_file,
        ]
        for ci, val in enumerate(vals, 1):
            cell = ws_gl.cell(ri, ci, val)
            cell.font = Font(size=9)
            if isinstance(val, float) and val:
                cell.number_format = "#,##0.00"
                cell.alignment = Alignment(horizontal="right")
            else:
                cell.alignment = Alignment(vertical="center")
            if alt_fill:
                cell.fill = PatternFill("solid", fgColor=alt_fill)

    _border_range(ws_gl, 1, max(1, len(gl_data_rows) + 1), 1, len(gld_cols))
    ws_gl.freeze_panes = "A2"


def export_bank_recon_excel(
    recon_rows: List[BankReconRow],
    summary: BankReconSummary,
    lang: str = "th",
    task_info: Optional[Dict[str, Any]] = None,
    parse_info: Optional[Dict[str, Any]] = None,
    anchor_overrides: Optional[Dict[str, Dict[str, float]]] = None,
    anchor_ocr: Optional[Dict[str, float]] = None,
    warnings: Optional[List[str]] = None,
) -> bytes:
    """Generate Excel report with File Info + 4 data sheets, all headers i18n.

    P0.2 BUG-B-T2 v118.35.0.38 · anchor_overrides + anchor_ocr 来自 summary_json
    · anchor_overrides 非空时 · sheet 1 顶部加警示行 + 末尾加 "手动录入痕迹" section
    · 标黄(FFE082)被用户覆盖的 cell · 灰字显示 OCR 原值参考
    """
    lang = lang if lang in ("th", "en", "zh", "ja") else "th"

    wb = openpyxl.Workbook()
    _build_summary_sheet(
        wb, recon_rows, summary, lang, task_info, parse_info, anchor_overrides, warnings
    )
    _build_match_results_sheet(wb, recon_rows, lang)
    _build_stmt_detail_sheet(wb, recon_rows, lang)
    _build_gl_detail_sheet(wb, recon_rows, lang)

    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()
