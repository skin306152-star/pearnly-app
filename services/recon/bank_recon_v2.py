# -*- coding: utf-8 -*-
"""
bank_recon_v2.py · Pearnly · v1.0.0
銀行対照 / Bank Statement vs GL Reconciliation Engine

Supported banks  : KBank · BBL · KKP · KTB · SCB · generic fallback
GL input formats : Excel (.xlsx / .xls) · PDF (pdfplumber → Gemini fallback)
Matching layers  : L1 exact date+amount  · L2 ±DATE_TOL_DAYS tolerance · L3 amount only
Export           : 4-sheet openpyxl · i18n th/en/zh/ja
"""

import io
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


# DATA CLASSES · moved to services/recon/bank_recon_types.py
from services.recon.bank_recon_types import (  # noqa: F401  re-export (recon_routes/tests) + facade-internal
    StatementRow,
    GlRow,
    BankReconRow,
    BankReconSummary,
)

# CONSTANTS / OCR CACHE / UTILITIES · moved to services/recon/bank_recon_utils.py
from services.recon.bank_recon_utils import (  # noqa: F401  re-export + facade-internal
    AMOUNT_TOL,
    MIN_PLUMBER_ROWS,
    DATE_TOL_DAYS,
    _GEMINI_STMT_CACHE,
    _GEMINI_GL_CACHE,
    _cache_get,
    _cache_put,
    _disk_cache_get,
    _disk_cache_put,
    _to_float,
    _parse_date,
    _amount_matches,
    _day_diff,
    _is_gl_skip_row,
    _detect_bank,
    _bank_from_filename,
    _BANK_SIGNATURES,
)

# TABLE / PDF I/O · workbook+csv loaders, header match, summary-row, pdf text · moved to bank_table_io.py
from services.recon.bank_table_io import (  # noqa: F401  re-export + facade-internal (_hit/_is_summary_row tested)
    _is_summary_row,
    _hit,
    _load_excel_all_sheets,
    _load_csv_sheets,
    _pdf_extract_text_safe,
)

# DIRECT XLSX/CSV STATEMENT PARSER · moved to services/recon/bank_stmt_xlsx.py
from services.recon.bank_stmt_xlsx import (  # noqa: F401  re-export (recon_jobs_routes/tests/probes) + facade-internal
    parse_bank_stmt_xlsx_direct,
    _map_bank_stmt_cols,
    _STMT_DEPOSIT_H,
)

# GL PARSERS · Excel/CSV (bank_gl_excel) + PDF (bank_gl_pdf) · column recognition in bank_gl_common
from services.recon.bank_gl_excel import (  # noqa: F401  re-export (recon_routes/recon_jobs/probes/tests) + facade parse_gl
    parse_gl_excel,
)
from services.recon.bank_gl_pdf import parse_gl_pdf  # facade parse_gl dispatch

# ─────────────────────────────────────────────────────────────────────────────
# BANK STATEMENT PARSERS · extractors/text/gemini split to services/recon/bank_stmt_{extract,text,gemini}.py
from services.recon.bank_stmt_extract import (
    _parse_kbank_pages,
    _parse_bbl_pages,
    _parse_generic_pages,
    _parse_stmt_text_coords,
)
from services.recon.bank_stmt_text import (
    _parse_stmt_text_lines,
    _parse_kbank_text_columns,
)
from services.recon.bank_stmt_gemini import _gemini_parse_statement

# STATEMENT BALANCE VERIFY/REPAIR · moved to services/recon/bank_stmt_balance.py
from services.recon.bank_stmt_balance import (
    _stmt_bad_ratio,
    _correct_direction_from_balance,
    _verify_row_balances,
    _repair_amount_from_balance,
    _audit_completeness,
)

# LEGACY ParsedStatement pipeline · moved to services/recon/bank_stmt_legacy.py
from services.recon.bank_stmt_legacy import (  # noqa: F401  re-export (bank_recon_routes.br.*)
    BankTransaction,
    ParsedStatement,
    parsed_from_pipeline_legacy,
    gl_rows_from_pipeline_legacy,
    detect_bank,
    parse_statement_pdf,
)

# RECON JSON (DE)SERIALIZATION · moved to services/recon/bank_recon_serialize.py
from services.recon.bank_recon_serialize import (  # noqa: F401  re-export (recon_routes/recon_jobs)
    rows_to_json,
    rows_from_json,
    summary_to_json,
    summary_from_json,
)

# MULTI-FILE MERGE · moved to services/recon/bank_recon_merge.py
from services.recon.bank_recon_merge import (  # noqa: F401  re-export (recon_routes)
    merge_statements,
    merge_gl_files,
)

# UNIFIED-PIPELINE ADAPTERS · moved to services/recon/bank_recon_pipeline.py
from services.recon.bank_recon_pipeline import (  # facade orchestrator (parse_bank_statement_pdf) + parse_gl dispatch
    _parse_bank_stmt_via_pipeline,
    _parse_gl_via_pipeline,
)

# EXCEL EXPORT · moved to services/recon/bank_recon_excel.py
from services.recon.bank_recon_excel import (  # noqa: F401  re-export (recon_routes/tests)
    export_bank_recon_excel,
)

# STATEMENT-VS-GL RECONCILE CORE · moved to services/recon/bank_recon_reconcile.py
from services.recon.bank_recon_reconcile import (  # noqa: F401  re-export (recon_routes/tests)
    reconcile,
)

# TX↔INVOICE SCORING + SESSION MATCHING · moved to services/recon/bank_recon_scoring.py
from services.recon.bank_recon_scoring import (  # noqa: F401  re-export (bank_recon_routes.br.run_matching_for_session)
    run_matching_for_session,
)


def parse_bank_statement_pdf(
    file_bytes: bytes, filename: str, api_key: str = "", tenant_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Parse a bank statement.

    2026-05-21 multi-format refactor: name kept for back-compat but now
    accepts ANY format. .pdf goes through the existing pdfplumber + Gemini
    pipeline. Other formats (Excel / CSV / Word / image / TXT) go through
    services/ocr/pipeline with document_type='bank_statement' so the
    bank-statement prompt + validators block description-column digits
    from being assigned to deposit / withdrawal / balance.

    Strategy for PDF: (1) safe text extraction (2) pdfplumber tables (3) text-line fallback (4) Gemini
    """
    import os as _os

    # Filename is the high-precision bank signal (content detection drowns in
    # interbank-transfer counterparty names); it overrides detected codes below.
    fn_bank = _bank_from_filename(filename)

    ext = (filename or "").lower().rsplit(".", 1)[-1]
    if ext != "pdf":
        result = _parse_bank_stmt_via_pipeline(file_bytes, filename, tenant_id=tenant_id)
        if fn_bank and result.get("ok"):
            result["bank_code"] = fn_bank
        return result

    # 2026-05-21: PDF bank statement defaults to new pipeline (document_type
    # =bank_statement + validators). Set OCR_PDF_STMT_LEGACY=true to opt back
    # into the existing pdfplumber+Gemini path.
    if _os.environ.get("OCR_PDF_STMT_LEGACY", "").strip().lower() != "true":
        pipeline_result = _parse_bank_stmt_via_pipeline(file_bytes, filename, tenant_id=tenant_id)
        if pipeline_result.get("ok") and pipeline_result.get("rows"):
            if fn_bank:
                pipeline_result["bank_code"] = fn_bank
            return pipeline_result
        logger.warning(
            f"[parse_bank_statement] pipeline yielded "
            f"{pipeline_result.get('row_count')} rows / "
            f"err={pipeline_result.get('error')!r} · falling back to legacy"
        )

    # ── Step 1: extract text safely (immune to pdfplumber KeyError crash) ──
    page_texts = _pdf_extract_text_safe(file_bytes)
    all_text = "\n".join(page_texts)
    bank_code = fn_bank or (_detect_bank(all_text) if all_text.strip() else "generic")
    # DEBUG v118.33.11.1
    logger.info(
        f"[stmt_parse][{filename}] pages={len(page_texts)} chars={len(all_text)} bank={bank_code}"
    )
    if all_text.strip():
        logger.info(f"[stmt_parse][{filename}] first600: " + repr(all_text[:600]))
    if all_text.strip():
        try:
            import os

            os.makedirs("/tmp/stmt_debug", exist_ok=True)
            with open(f"/tmp/stmt_debug/{filename}.txt", "w") as _df:
                _df.write(all_text)
        except Exception:
            pass

    # ── Step 2: try pdfplumber table extraction ──
    all_tables: List = []
    try:
        import pdfplumber

        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            if not all_text.strip():
                all_text = "\n".join(p.extract_text() or "" for p in pdf.pages)
                bank_code = fn_bank or _detect_bank(all_text)
            for p in pdf.pages:
                try:
                    tbls = p.extract_tables() or []
                    all_tables.extend(tbls)
                except Exception:
                    pass  # 该页 extract_tables 失败 · 跳过(每页容错)
    except Exception as e:
        logger.warning(f"pdfplumber stmt [{filename}] skipped: {e}")

    # ── Step 3: table-based parsing ──
    rows: List[StatementRow] = []
    opening = 0.0
    closing = 0.0

    if all_tables:
        if bank_code == "kbank":
            rows, opening, closing = _parse_kbank_pages(all_tables)
        elif bank_code == "bbl":
            rows, opening, closing = _parse_bbl_pages(all_tables)
        else:
            rows, opening, closing = _parse_generic_pages(all_tables)

        if len(rows) < MIN_PLUMBER_ROWS and bank_code == "generic":
            rows2, op2, cl2 = _parse_kbank_pages(all_tables)
            if len(rows2) > len(rows):
                rows, opening, closing = rows2, op2, cl2

    # ── Step 4a: KBank column-stacked text (pdfminer-extracted) ──
    if len(rows) < MIN_PLUMBER_ROWS and all_text.strip() and bank_code == "kbank":
        col_rows, col_op, col_cl = _parse_kbank_text_columns(all_text)
        logger.info(f"[stmt_parse][{filename}] step4a kbank-columns: rows={len(col_rows)}")
        if len(col_rows) > len(rows):
            rows, opening, closing = col_rows, col_op, col_cl
    # ── Step 4b: generic text-line fallback ──
    if len(rows) < MIN_PLUMBER_ROWS and all_text.strip():
        text_rows, text_op, text_cl = _parse_stmt_text_lines(all_text, bank_code)
        logger.info(
            f"[stmt_parse][{filename}] step4b text-line: tbl_rows={len(rows)} text_rows={len(text_rows)} bank={bank_code}"
        )
        if len(text_rows) > len(rows):
            rows, opening, closing = text_rows, text_op, text_cl

    # ── Step 4c: 坐标感知文本解析(密集多页文本 PDF · BAY/SCB 等)v118.35.0.66 ──
    # 行级解析对存/取分立列的文本 PDF 易把列对错位(BAY 314 存全判成取 → 触发 Gemini
    # 再漏读)。坐标解析按表头列 x 归位 · 跨全部页 · 取『行数更多且余额链不更差』者。
    if all_text.strip():
        try:
            coord_rows, coord_op, coord_cl = _parse_stmt_text_coords(file_bytes)
        except Exception as e:
            coord_rows, coord_op, coord_cl = [], 0.0, 0.0
            logger.warning(f"[stmt_parse][{filename}] step4c coords skipped: {e}")
        if coord_rows:
            coord_bad = _stmt_bad_ratio(coord_rows, coord_op)
            cur_bad = _stmt_bad_ratio(rows, opening)
            logger.info(
                f"[stmt_parse][{filename}] step4c coords: rows={len(coord_rows)} "
                f"bad={coord_bad:.2f} vs cur rows={len(rows)} bad={cur_bad:.2f}"
            )
            # 坐标解析行数更多 · 且余额链不比现有更坏 → 采用(更全 + 列对位正确)
            if len(coord_rows) > len(rows) and coord_bad <= max(cur_bad, 0.05):
                rows, opening, closing = coord_rows, coord_op, coord_cl

    # ── Step 5: Gemini fallback ──
    # v118.35.0.52 · 触发条件升级:行数不足 OR 免费解析余额链大面积对不上(列错位 · 如
    # BAY/Krungsri 余额读成 0、KBank 把交易ID当金额)· 用余额链可信度做仲裁 · 取更优者。
    _free_rows, _free_op, _free_cl, _free_bank = rows, opening, closing, bank_code
    _free_bad = _stmt_bad_ratio(rows, opening)
    _need_gemini = (len(rows) < MIN_PLUMBER_ROWS) or (_free_bad > 0.30)
    if _need_gemini:
        logger.info(
            f"[stmt_parse][{filename}] step5 gemini: api_key_present={bool(api_key)} "
            f"text_chars={len(all_text)} free_rows={len(rows)} free_bad={_free_bad:.2f}"
        )
    printed_totals = None  # v118.35.0.63 · 账单印刷页脚汇总(仅 Gemini 路径有)· 完整性交叉校验用
    if _need_gemini and api_key:
        gemini_result = _gemini_parse_statement(file_bytes, filename, api_key)
        g_rows = gemini_result.get("rows") or []
        logger.info(
            f"[stmt_parse][{filename}] step5 gemini result: ok={gemini_result.get('ok')} rows={len(g_rows)}"
        )
        if gemini_result.get("ok") and g_rows:
            g_op = gemini_result.get("opening", opening)
            g_bad = _stmt_bad_ratio(g_rows, g_op)
            # 免费行数不足 → 直接用 Gemini;否则谁的余额链更可信用谁
            if len(_free_rows) < MIN_PLUMBER_ROWS or g_bad < _free_bad:
                logger.info(
                    f"[stmt_parse][{filename}] 采用 Gemini(free_bad={_free_bad:.2f} > gemini_bad={g_bad:.2f})"
                )
                rows = g_rows
                opening = g_op
                closing = gemini_result.get("closing", closing)
                bank_code = gemini_result.get("bank_code", bank_code)
                printed_totals = gemini_result.get("printed_totals")
            else:
                logger.info(
                    f"[stmt_parse][{filename}] 保留免费解析(更可信 · gemini_bad={g_bad:.2f})"
                )
                rows, opening, closing, bank_code = _free_rows, _free_op, _free_cl, _free_bank

    for r in rows:
        r.source_file = filename

    # v118.35.0.60 · 跳过底部汇总/合计行(Total/รวมรายการ/合计)· 不是交易 · 防被当交易误标 + 污染余额链
    #   汇合点统一过滤 · 覆盖 table/text/Gemini 全部解析路径
    rows = [r for r in rows if not _is_summary_row(r.description)]

    # v118.35.0.50 · 先用余额涨跌纠正 OCR 把借贷方向读反的行(必须在余额验证之前)
    _correct_direction_from_balance(rows, opening)

    # v118.33.13.0 · row-by-row balance arithmetic verification
    # For each row: prev_balance + deposit - withdrawal should equal current balance.
    # If it doesn't, set balance_ok=False so the UI can flag for human review.
    _verify_row_balances(rows, opening)
    # v118.35.0.62 · 余额链自动修复『数字读错的金额』· 把可证的 ⚠ 变成自动修正
    _repair_amount_from_balance(rows, opening)
    balance_warn_count = sum(1 for r in rows if r.balance_ok is False)
    low_conf_count = sum(1 for r in rows if r.confidence == "low")
    if balance_warn_count or low_conf_count:
        logger.info(
            f"[stmt_parse][{filename}] verification: "
            f"balance_warn={balance_warn_count} low_conf={low_conf_count} total={len(rows)}"
        )

    if not rows:
        hint = " (PDF has no extractable text)" if not all_text.strip() else ""
        return {
            "ok": False,
            "error": f"No statement rows found in PDF{hint}",
            "rows": [],
            "opening": 0.0,
            "closing": 0.0,
        }

    # v118.35.0.66 · 期初/期末兜底回填:Gemini 有时不回传 opening/closing 字段(实测 AM:
    # 4 笔交易全对、B/F 行也读到了,但 opening/closing 仍是 0 → 汇总区显示 0、期末交叉校验跳过)。
    # 行里已有 B/F 余额 + 末行余额时,数学补回(只在拿到 0/未知时补 · 不覆盖已知值)。
    _OPEN_KW = ("b/f", "brought forward", "ยอดยกมา", "ยกมา", "opening", "期初", "上期")
    if not opening:
        first = rows[0]
        fd = (first.description or "").lower()
        if (
            (first.deposit or 0) == 0
            and (first.withdrawal or 0) == 0
            and first.balance
            and any(k in fd for k in _OPEN_KW)
        ):
            opening = first.balance  # 显式 B/F 行余额
        else:
            fm = next((r for r in rows if (r.deposit or 0) or (r.withdrawal or 0)), None)
            if fm and fm.balance:  # 退路:首笔有动行『余额−净额』反推
                opening = round(fm.balance - ((fm.deposit or 0) - (fm.withdrawal or 0)), 2)
    if not closing:
        closing = next((r.balance for r in reversed(rows) if r.balance), closing)

    # v118.35.0.63 · 完整性交叉校验(印刷合计/笔数 + 期末平衡)· 主动发现漏行
    completeness = _audit_completeness(rows, opening, closing, printed_totals)
    if not completeness["ok"]:
        logger.info(f"[stmt_parse][{filename}] completeness issues: {completeness['issues']}")

    return {
        "ok": True,
        "rows": rows,
        "opening": opening,
        "closing": closing,
        "bank_code": bank_code,
        "row_count": len(rows),
        "balance_warn_count": balance_warn_count,
        "low_conf_count": low_conf_count,
        "completeness": completeness,  # v118.35.0.63
    }


def parse_gl(
    file_bytes: bytes,
    filename: str,
    account_code: str = "",
    api_key: str = "",
    tenant_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Route to Excel / PDF / pipeline GL parser based on file extension.

    2026-05-21 multi-format refactor:
    - .xlsx / .xls / .xlsm → parse_gl_excel (structural)
    - .pdf                 → parse_gl_pdf   (existing Gemini path)
    - .csv / .tsv / .docx / .doc / .txt / images → unified services/ocr/pipeline
      with document_type='general_ledger' so prompt + validators block
      description-column numbers (e.g. 6091) from being parsed as amounts.
    """
    import os as _os

    ext = (filename or "").lower().rsplit(".", 1)[-1]
    if ext in ("xlsx", "xls", "xlsm"):
        result = parse_gl_excel(file_bytes, filename, account_code, tenant_id=tenant_id)
    elif ext in ("csv", "tsv"):
        # ADR-006 S6b · GL CSV 先走学习层(免费)· ok 或 needs_mapping 直接返回;
        # 只有真读不出(非 needs_mapping 失败)才降级 Gemini pipeline。
        result = parse_gl_excel(file_bytes, filename, account_code, tenant_id=tenant_id)
        if not result.get("ok") and not result.get("needs_mapping"):
            logger.info(f"[parse_gl] csv direct miss · falling back to pipeline: {filename}")
            result = _parse_gl_via_pipeline(file_bytes, filename, account_code)
    elif ext == "pdf":
        # 2026-05-21: PDF GL defaults to new pipeline (document_type=
        # general_ledger + validators). OCR_PDF_GL_LEGACY=true rolls back
        # to the previous Gemini Vision parse_gl_pdf path.
        if _os.environ.get("OCR_PDF_GL_LEGACY", "").strip().lower() == "true":
            result = parse_gl_pdf(file_bytes, filename, account_code, api_key)
        else:
            result = _parse_gl_via_pipeline(file_bytes, filename, account_code)
            if not (result.get("ok") and result.get("rows")):
                logger.warning(
                    f"[parse_gl] pipeline yielded {result.get('row_count')} rows / "
                    f"err={result.get('error')!r} · falling back to parse_gl_pdf"
                )
                result = parse_gl_pdf(file_bytes, filename, account_code, api_key)
    else:
        result = _parse_gl_via_pipeline(file_bytes, filename, account_code)

    if result.get("ok"):
        for r in result.get("rows", []):
            r.source_file = filename

    return result
