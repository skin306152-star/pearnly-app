# -*- coding: utf-8 -*-
"""
bank_recon_v2.py · Pearnly · v1.0.0
銀行対照 / Bank Statement vs GL Reconciliation Engine

Supported banks  : KBank · BBL · KKP · KTB · SCB · generic fallback
GL input formats : Excel (.xlsx / .xls) · PDF (pdfplumber → Gemini fallback)
Matching layers  : L1 exact date+amount  · L2 ±3-day tolerance · L3 amount only
Export           : 4-sheet openpyxl · i18n th/en/zh/ja
"""

import io
import re
import logging
from datetime import date
from typing import List, Dict, Any, Optional, Tuple

# v118.35.0.3 · 包装 pipeline 抛出的 pydantic ValidationError · 不再把
# "Input should be a valid string ... https://errors.pydantic.dev/2.13/v/..."
# 整串塞进对账中心红色 toast 给用户看
from services.ocr.error_format import short_error as _short_err

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# CONSTANTS
# ─────────────────────────────────────────────────────────────────────────────
DATE_TOL_DAYS = 3  # days tolerance for layer-2 matching


# DATA CLASSES · moved to services/recon/bank_recon_types.py
from services.recon.bank_recon_types import (
    StatementRow,
    GlRow,
    BankReconRow,
    BankReconSummary,
)

# CONSTANTS / OCR CACHE / UTILITIES · moved to services/recon/bank_recon_utils.py
from services.recon.bank_recon_utils import (  # noqa: F401  re-export + facade-internal
    AMOUNT_TOL,
    MIN_PLUMBER_ROWS,
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

    ext = (filename or "").lower().rsplit(".", 1)[-1]
    if ext != "pdf":
        return _parse_bank_stmt_via_pipeline(file_bytes, filename, tenant_id=tenant_id)

    # 2026-05-21: PDF bank statement defaults to new pipeline (document_type
    # =bank_statement + validators). Set OCR_PDF_STMT_LEGACY=true to opt back
    # into the existing pdfplumber+Gemini path.
    if _os.environ.get("OCR_PDF_STMT_LEGACY", "").strip().lower() != "true":
        pipeline_result = _parse_bank_stmt_via_pipeline(file_bytes, filename, tenant_id=tenant_id)
        if pipeline_result.get("ok") and pipeline_result.get("rows"):
            return pipeline_result
        logger.warning(
            f"[parse_bank_statement] pipeline yielded "
            f"{pipeline_result.get('row_count')} rows / "
            f"err={pipeline_result.get('error')!r} · falling back to legacy"
        )

    # ── Step 1: extract text safely (immune to pdfplumber KeyError crash) ──
    page_texts = _pdf_extract_text_safe(file_bytes)
    all_text = "\n".join(page_texts)
    bank_code = _detect_bank(all_text) if all_text.strip() else "generic"
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
                bank_code = _detect_bank(all_text)
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


def _parse_bank_stmt_via_pipeline(
    file_bytes: bytes, filename: str, tenant_id: Optional[str] = None
) -> Dict[str, Any]:
    """Bank-recon-v2 adapter: route non-PDF bank statements through the
    unified pipeline with document_type='bank_statement', then convert to
    List[StatementRow] so the rest of bank-v2/run consumes it unchanged.

    Validators guarantee deposit/withdrawal/balance came from their
    respective columns — description / reference / account-number digits
    are rejected and cleared before this adapter runs.
    """
    try:
        from services.ocr.pipeline import (
            run_on_image_bytes as _run_image,
            run_on_table_bytes as _run_table,
            IMAGE_EXTENSIONS,
            TABLE_EXTENSIONS,
        )
        from services.ocr.legacy_adapter import pipeline_result_to_legacy_dict
    except ImportError as e:
        return {
            "ok": False,
            "rows": [],
            "row_count": 0,
            "bank_code": "generic",
            "error": f"pipeline import failed: {e}",
        }

    ext_dot = "." + (filename or "").lower().rsplit(".", 1)[-1]

    # v118.35.0.19 · xlsx/xls 优先走直读 fallback(零成本 · 跳 Gemini)
    # 用户上传自家导出 / 银行下载 / 自己整理的 Excel · 表头清晰时直读即可
    # 直读不命中(表头识别不出) → 自动降级到 Gemini pipeline
    if ext_dot in (".xlsx", ".xls", ".xlsm", ".csv", ".tsv"):
        direct = parse_bank_stmt_xlsx_direct(file_bytes, filename, tenant_id=tenant_id)
        if direct.get("ok"):
            logger.info(
                f"[stmt_parse][{filename}] xlsx_direct OK · {direct['row_count']} rows · skip Gemini"
            )
            return direct
        # ADR-006 · 新模板拿不准 → 走"确认列对应"· 不烧 Gemini · 原样上抛
        if direct.get("needs_mapping"):
            logger.info(f"[stmt_parse][{filename}] xlsx_direct needs_mapping · skip Gemini")
            return direct
        logger.info(
            f"[stmt_parse][{filename}] xlsx_direct miss({direct.get('error_code')}) · falling back to Gemini"
        )

    try:
        if ext_dot in IMAGE_EXTENSIONS:
            pr = _run_image(file_bytes, document_type="bank_statement")
        elif ext_dot in TABLE_EXTENSIONS:
            pr = _run_table(file_bytes, filename=filename or "stmt", document_type="bank_statement")
        else:
            return {
                "ok": False,
                "rows": [],
                "row_count": 0,
                "bank_code": "generic",
                "error_code": "file_not_supported",
                "error": f"unsupported format {ext_dot}",
            }
    except Exception as e:
        return {
            "ok": False,
            "rows": [],
            "row_count": 0,
            "bank_code": "generic",
            "error_code": "ocr_failed",
            "error": _short_err(e),
        }

    legacy = pipeline_result_to_legacy_dict(pr)
    pages = legacy.get("pages") or []
    if not pages:
        return {
            "ok": False,
            "rows": [],
            "row_count": 0,
            "bank_code": "generic",
            "error": "no pages parsed",
        }
    doc = (pages[0] or {}).get("document") or {}
    bank_name_l = (doc.get("bank_name") or "").lower()
    bank_code = "generic"
    for code, sigs in _BANK_SIGNATURES.items():
        if any(s in bank_name_l or s in (doc.get("bank_name") or "") for s in sigs):
            bank_code = code
            break

    rows: List[StatementRow] = []
    for e in doc.get("entries") or []:
        deposit = _to_float(e.get("deposit"))
        withdrawal = _to_float(e.get("withdrawal"))
        balance = _to_float(e.get("balance"))
        if deposit == 0.0 and withdrawal == 0.0:
            continue
        tx_date = None
        if e.get("transaction_date"):
            try:
                yy, mm, dd = e["transaction_date"].split("-")
                tx_date = date(int(yy), int(mm), int(dd))
            except (ValueError, AttributeError):
                tx_date = _parse_date(e.get("transaction_date_raw") or "")
        rows.append(
            StatementRow(
                date=tx_date,
                description=e.get("description") or "",
                withdrawal=withdrawal,
                deposit=deposit,
                balance=balance,
                source_file=filename,
            )
        )
    return {
        "ok": True,
        "rows": rows,
        "row_count": len(rows),
        "bank_code": bank_code,
        "parser_version": "bank_recon_v2+pipeline_v1",
        "needs_review": legacy.get("_needs_review", False),
    }


def _parse_gl_via_pipeline(
    file_bytes: bytes, filename: str, account_code: str = ""
) -> Dict[str, Any]:
    """Bank-recon-v2 adapter: route GL through services/ocr/pipeline with
    document_type='general_ledger', then convert to List[GlRow]."""
    try:
        from services.ocr.pipeline import (
            run_on_image_bytes as _run_image,
            run_on_table_bytes as _run_table,
            IMAGE_EXTENSIONS,
            TABLE_EXTENSIONS,
        )
        from services.ocr.legacy_adapter import pipeline_result_to_legacy_dict
    except ImportError as e:
        return {
            "ok": False,
            "rows": [],
            "row_count": 0,
            "accounts": [],
            "error": f"pipeline import failed: {e}",
        }
    ext_dot = "." + (filename or "").lower().rsplit(".", 1)[-1]
    try:
        if ext_dot in IMAGE_EXTENSIONS:
            pr = _run_image(file_bytes, document_type="general_ledger")
        elif ext_dot in TABLE_EXTENSIONS:
            pr = _run_table(file_bytes, filename=filename or "gl", document_type="general_ledger")
        else:
            return {
                "ok": False,
                "rows": [],
                "row_count": 0,
                "accounts": [],
                "error_code": "file_not_supported",
                "error": f"unsupported format {ext_dot}",
            }
    except Exception as e:
        return {
            "ok": False,
            "rows": [],
            "row_count": 0,
            "accounts": [],
            "error_code": "ocr_failed",
            "error": _short_err(e),
        }

    legacy = pipeline_result_to_legacy_dict(pr)
    rows = gl_rows_from_pipeline_legacy(legacy)
    if account_code:
        rows = [r for r in rows if r.account_code == account_code]
    accounts = sorted({r.account_code for r in rows if r.account_code})
    return {
        "ok": True,
        "rows": rows,
        "row_count": len(rows),
        "accounts": accounts,
        "parser_version": "bank_recon_v2+pipeline_v1",
        "needs_review": legacy.get("_needs_review", False),
    }


# ─────────────────────────────────────────────────────────────────────────────
# MULTI-FILE MERGE
# ─────────────────────────────────────────────────────────────────────────────
def merge_statements(
    parsed_list: List[Dict[str, Any]],
) -> Tuple[List[StatementRow], float, float, str]:
    """Merge multiple parsed bank statements, deduplicate, sort by date."""
    seen_hashes = set()
    all_rows: List[StatementRow] = []
    opening = 0.0
    closing = 0.0
    bank_code = "generic"
    earliest_date = None
    latest_date = None

    for p in parsed_list:
        if not p.get("ok"):
            continue
        if p.get("bank_code") and p["bank_code"] != "generic":
            bank_code = p["bank_code"]
        for r in p.get("rows") or []:
            if r.row_hash in seen_hashes:
                continue
            seen_hashes.add(r.row_hash)
            all_rows.append(r)
            if r.date:
                if earliest_date is None or r.date < earliest_date:
                    earliest_date = r.date
                if latest_date is None or r.date > latest_date:
                    latest_date = r.date

    # v118.35.0.48 · 只按日期稳定排序 · 保留对账单原始打印顺序(同日多笔不重排)
    # 旧版按 (date, withdrawal, deposit) 排 · 把同一天的存/取款按金额重排 · 打乱了
    # 对账单的"上一行余额 ± 金额 = 本行余额"链条 · 导致余额验证误报 + 显示顺序错乱。
    # Python sort 稳定 → 同日行保持 append(= 解析 = PDF 顶到底)顺序。
    all_rows.sort(key=lambda r: (r.date or date.min,))

    # Opening: from first parsed file that has an opening balance
    for p in parsed_list:
        if p.get("ok") and p.get("opening", 0.0) != 0.0:
            opening = p["opening"]
            break

    # Closing: from last parsed file or recalculate
    for p in reversed(parsed_list):
        if p.get("ok") and p.get("closing", 0.0) != 0.0:
            closing = p["closing"]
            break

    if opening == 0.0 and all_rows:
        first = all_rows[0]
        if first.deposit > 0:
            opening = round(first.balance - first.deposit, 2)
        elif first.withdrawal > 0:
            opening = round(first.balance + first.withdrawal, 2)

    if closing == 0.0 and all_rows:
        closing = all_rows[-1].balance

    return all_rows, opening, closing, bank_code


def merge_gl_files(
    parsed_list: List[Dict[str, Any]], account_code: str = ""
) -> Tuple[List[GlRow], List[str], float, float]:
    """Merge multiple parsed GL files, deduplicate, sort by date."""
    seen_hashes = set()
    all_rows: List[GlRow] = []
    all_accounts: set = set()
    opening = 0.0

    for p in parsed_list:
        if not p.get("ok"):
            continue
        if p.get("opening", 0.0) != 0.0 and opening == 0.0:
            opening = p["opening"]
        for acct in p.get("accounts") or []:
            all_accounts.add(acct)
        for r in p.get("rows") or []:
            if account_code and r.account_code and not r.account_code.startswith(account_code):
                continue
            if r.row_hash in seen_hashes:
                continue
            seen_hashes.add(r.row_hash)
            all_rows.append(r)

    all_rows.sort(key=lambda r: (r.date or date.min, r.doc_no or ""))

    # v118.33.13.5 · Cash-ledger formula (matches parse_gl_pdf v118.33.13.4):
    # debit = cash IN (balance increase), credit = cash OUT (balance decrease)
    # The OLD formula `opening + credit - debit` was the expense/revenue
    # perspective and produced wrong closing balances for bank GLs.
    total_credit = sum(r.credit for r in all_rows)
    total_debit = sum(r.debit for r in all_rows)
    closing = round(opening + total_debit - total_credit, 2)

    return all_rows, sorted(all_accounts), opening, closing


# ─────────────────────────────────────────────────────────────────────────────
# MATCHING ENGINE
# ─────────────────────────────────────────────────────────────────────────────
def reconcile(
    stmt_rows: List[StatementRow],
    gl_rows: List[GlRow],
    stmt_opening: float = 0.0,
    gl_opening: float = 0.0,
    stmt_closing: float = 0.0,
    gl_closing: float = 0.0,
    bank_code: str = "",
    gl_account_code: str = "",
) -> Tuple[List[BankReconRow], BankReconSummary]:
    """
    3-layer matching: L1 exact date+amount, L2 ±3-day+amount, L3 amount only.
    Returns (recon_rows, summary).
    """
    recon_rows: List[BankReconRow] = []

    # Work with indices to track matched/unmatched
    gl_used = [False] * len(gl_rows)
    stmt_used = [False] * len(stmt_rows)

    def try_match_gl(stmt_row: StatementRow, layer: int) -> Optional[int]:
        """Find best GL match for a statement row. Returns GL index or None."""
        target_amount = stmt_row.withdrawal if stmt_row.withdrawal > 0 else stmt_row.deposit
        # Withdrawal from bank = company paid out = GL Credit; Deposit = GL Debit
        direction = "C" if stmt_row.withdrawal > 0 else "D"

        best_idx = None
        best_day_diff = 999

        for gi, gr in enumerate(gl_rows):
            if gl_used[gi]:
                continue
            gl_amount = gr.debit if direction == "D" else gr.credit
            if not _amount_matches(target_amount, gl_amount):
                continue
            if gl_amount == 0:
                continue

            dd = _day_diff(stmt_row.date, gr.date)
            if layer == 1:
                if dd is None or dd > 0:
                    continue
                best_idx = gi
                break
            elif layer == 2:
                if dd is None or dd > DATE_TOL_DAYS:
                    continue
                if dd < best_day_diff:
                    best_day_diff = dd
                    best_idx = gi
            elif layer == 3:
                if best_idx is None:
                    best_idx = gi

        return best_idx

    # Layer 1: exact date + exact amount
    for si, sr in enumerate(stmt_rows):
        gi = try_match_gl(sr, layer=1)
        if gi is not None:
            gr = gl_rows[gi]
            stmt_used[si] = True
            gl_used[gi] = True
            recon_rows.append(
                BankReconRow(
                    match_status="matched",
                    match_layer=1,
                    stmt_date=sr.date,
                    stmt_desc=sr.description,
                    stmt_withdrawal=sr.withdrawal,
                    stmt_deposit=sr.deposit,
                    stmt_balance=sr.balance,
                    stmt_confidence=sr.confidence,
                    stmt_balance_ok=sr.balance_ok,
                    stmt_autocorrected=(sr.amount_autocorrected or sr.direction_autocorrected),
                    gl_date=gr.date,
                    gl_doc_no=gr.doc_no,
                    gl_account_code=gr.account_code,
                    gl_desc=gr.description,
                    gl_debit=gr.debit,
                    gl_credit=gr.credit,
                    date_diff_days=0,
                    source_stmt_file=sr.source_file,
                    source_gl_file=gr.source_file,
                )
            )

    # Layer 2: ±3-day tolerance
    for si, sr in enumerate(stmt_rows):
        if stmt_used[si]:
            continue
        gi = try_match_gl(sr, layer=2)
        if gi is not None:
            gr = gl_rows[gi]
            stmt_used[si] = True
            gl_used[gi] = True
            dd = _day_diff(sr.date, gr.date) or 0
            recon_rows.append(
                BankReconRow(
                    match_status="matched",
                    match_layer=2,
                    stmt_date=sr.date,
                    stmt_desc=sr.description,
                    stmt_withdrawal=sr.withdrawal,
                    stmt_deposit=sr.deposit,
                    stmt_balance=sr.balance,
                    stmt_confidence=sr.confidence,
                    stmt_balance_ok=sr.balance_ok,
                    stmt_autocorrected=(sr.amount_autocorrected or sr.direction_autocorrected),
                    gl_date=gr.date,
                    gl_doc_no=gr.doc_no,
                    gl_account_code=gr.account_code,
                    gl_desc=gr.description,
                    gl_debit=gr.debit,
                    gl_credit=gr.credit,
                    date_diff_days=dd,
                    source_stmt_file=sr.source_file,
                    source_gl_file=gr.source_file,
                )
            )

    # Layer 3: amount only (no date constraint) — flagged
    for si, sr in enumerate(stmt_rows):
        if stmt_used[si]:
            continue
        gi = try_match_gl(sr, layer=3)
        if gi is not None:
            gr = gl_rows[gi]
            stmt_used[si] = True
            gl_used[gi] = True
            dd = _day_diff(sr.date, gr.date)
            recon_rows.append(
                BankReconRow(
                    match_status="matched",
                    match_layer=3,
                    stmt_date=sr.date,
                    stmt_desc=sr.description,
                    stmt_withdrawal=sr.withdrawal,
                    stmt_deposit=sr.deposit,
                    stmt_balance=sr.balance,
                    stmt_confidence=sr.confidence,
                    stmt_balance_ok=sr.balance_ok,
                    stmt_autocorrected=(sr.amount_autocorrected or sr.direction_autocorrected),
                    gl_date=gr.date,
                    gl_doc_no=gr.doc_no,
                    gl_account_code=gr.account_code,
                    gl_desc=gr.description,
                    gl_debit=gr.debit,
                    gl_credit=gr.credit,
                    date_diff_days=dd,
                    source_stmt_file=sr.source_file,
                    source_gl_file=gr.source_file,
                )
            )

    # Remaining unmatched statement rows
    for si, sr in enumerate(stmt_rows):
        if stmt_used[si]:
            continue
        status = "stmt_withdrawal_only" if sr.withdrawal > 0 else "stmt_deposit_only"
        recon_rows.append(
            BankReconRow(
                match_status=status,
                match_layer=None,
                stmt_date=sr.date,
                stmt_desc=sr.description,
                stmt_withdrawal=sr.withdrawal,
                stmt_deposit=sr.deposit,
                stmt_balance=sr.balance,
                stmt_confidence=sr.confidence,
                stmt_balance_ok=sr.balance_ok,
                stmt_autocorrected=(sr.amount_autocorrected or sr.direction_autocorrected),
                source_stmt_file=sr.source_file,
            )
        )

    # Remaining unmatched GL rows
    for gi, gr in enumerate(gl_rows):
        if gl_used[gi]:
            continue
        status = "gl_debit_only" if gr.debit > 0 else "gl_credit_only"
        recon_rows.append(
            BankReconRow(
                match_status=status,
                match_layer=None,
                gl_date=gr.date,
                gl_doc_no=gr.doc_no,
                gl_account_code=gr.account_code,
                gl_desc=gr.description,
                gl_debit=gr.debit,
                gl_credit=gr.credit,
                source_gl_file=gr.source_file,
            )
        )

    # Sort: matched first (by stmt_date), then unmatched
    def _sort_key(r: BankReconRow):
        order = 0 if r.match_status == "matched" else 1
        d = r.stmt_date or r.gl_date or date.min
        return (order, d)

    recon_rows.sort(key=_sort_key)

    # Build summary
    matched_rows = [r for r in recon_rows if r.match_status == "matched"]
    gl_debit_only = [r for r in recon_rows if r.match_status == "gl_debit_only"]
    gl_credit_only = [r for r in recon_rows if r.match_status == "gl_credit_only"]
    stmt_wd_only = [r for r in recon_rows if r.match_status == "stmt_withdrawal_only"]
    stmt_dep_only = [r for r in recon_rows if r.match_status == "stmt_deposit_only"]

    gl_debit_only_amt = round(sum(r.gl_debit for r in gl_debit_only), 2)
    gl_credit_only_amt = round(sum(r.gl_credit for r in gl_credit_only), 2)
    stmt_wd_only_amt = round(sum(r.stmt_withdrawal for r in stmt_wd_only), 2)
    stmt_dep_only_amt = round(sum(r.stmt_deposit for r in stmt_dep_only), 2)

    # Reconciliation formula:
    # stmt_closing ≈ gl_closing + opening_diff - gl_debit_only + gl_credit_only
    #                           - stmt_wd_only + stmt_dep_only
    opening_diff = round(stmt_opening - gl_opening, 2)
    formula_closing = round(
        gl_closing
        + opening_diff
        - gl_debit_only_amt
        + gl_credit_only_amt
        - stmt_wd_only_amt
        + stmt_dep_only_amt,
        2,
    )
    formula_diff = round(stmt_closing - formula_closing, 2)

    summary = BankReconSummary(
        bank_code=bank_code,
        gl_account_code=gl_account_code,
        stmt_opening=stmt_opening,
        stmt_closing=stmt_closing,
        gl_opening=gl_opening,
        gl_closing=gl_closing,
        stmt_total_deposit=round(sum(r.deposit for r in stmt_rows), 2),
        stmt_total_withdrawal=round(sum(r.withdrawal for r in stmt_rows), 2),
        gl_total_credit=round(sum(r.credit for r in gl_rows), 2),
        gl_total_debit=round(sum(r.debit for r in gl_rows), 2),
        matched_count=len(matched_rows),
        gl_debit_only_count=len(gl_debit_only),
        gl_credit_only_count=len(gl_credit_only),
        stmt_withdrawal_only_count=len(stmt_wd_only),
        stmt_deposit_only_count=len(stmt_dep_only),
        gl_debit_only_amount=gl_debit_only_amt,
        gl_credit_only_amount=gl_credit_only_amt,
        stmt_withdrawal_only_amount=stmt_wd_only_amt,
        stmt_deposit_only_amount=stmt_dep_only_amt,
        opening_diff=opening_diff,
        formula_stmt_closing=formula_closing,
        formula_diff=formula_diff,
    )

    return recon_rows, summary


# ============================================================
# v0.18 · 匹配算法
# ============================================================

# 权重配置(总和 100)
_W_AMOUNT = 50
_W_DATE = 30
_W_DIRECTION = 15
_W_KEYWORD = 5

# 阈值
THRESH_AUTO = 85  # 自动选中
THRESH_SUGGEST = 60  # 可显示为疑似

# 发票金额/日期误差容忍
AMOUNT_TOL_EQUAL = 0.01  # 小于这个差值 = 金额精确一致
AMOUNT_TOL_SMALL = 1.00  # 1 泰铢内
AMOUNT_TOL_MEDIUM = 10.00  # 10 泰铢内(手续费差 / 汇率小差)
DATE_TOL_DAYS = 7  # 超过 7 天不计候选


def score_amount(bank_amount: float, invoice_amount: float) -> float:
    """金额接近度 → 0..50"""
    if not bank_amount or not invoice_amount:
        return 0.0
    diff = abs(float(bank_amount) - float(invoice_amount))
    if diff <= AMOUNT_TOL_EQUAL:
        return float(_W_AMOUNT)  # 完全一致
    if diff <= AMOUNT_TOL_SMALL:
        return float(_W_AMOUNT) - 5  # 1 泰铢内:45
    if diff <= AMOUNT_TOL_MEDIUM:
        return float(_W_AMOUNT) - 15  # 10 泰铢内:35
    # 更大差距:按比例打分(误差 ≤ 1% 给 20 分,≤ 5% 给 10 分)
    pct = diff / max(float(invoice_amount), 0.01)
    if pct <= 0.01:
        return 20.0
    if pct <= 0.05:
        return 10.0
    return 0.0


def score_date(bank_date: Optional[str], invoice_date: Optional[str]) -> float:
    """日期接近度 → 0..30"""
    if not bank_date or not invoice_date:
        return 0.0
    try:
        d1 = date.fromisoformat(bank_date)
        d2 = date.fromisoformat(invoice_date)
    except (ValueError, TypeError):
        return 0.0
    days = abs((d1 - d2).days)
    if days == 0:
        return float(_W_DATE)  # 同日:30
    if days <= 1:
        return 25.0
    if days <= 3:
        return 20.0
    if days <= 7:
        return 10.0
    return 0.0


def score_direction(bank_direction: str, invoice_meta: Dict[str, Any]) -> float:
    """方向一致性 → 0 或 15
    银行 OUT = 付出去钱 = 对应 采购/费用 发票(应付)
    银行 IN  = 收到钱    = 对应 销售/收入 发票(应收)
    判断依据:ocr_history 里的 category_tag / vendor 字段
    """
    if not bank_direction:
        return 0.0
    cat = (invoice_meta.get("category_tag") or "").lower()
    # 简单分类:销售/收入类 vs 采购/费用类
    income_words = ["sale", "sales", "revenue", "income", "销售", "收入"]
    expense_words = ["purchase", "expense", "cost", "fee", "采购", "费用", "开支"]
    is_income = any(w in cat for w in income_words)
    is_expense = any(w in cat for w in expense_words)

    if bank_direction == "IN" and is_income:
        return float(_W_DIRECTION)
    if bank_direction == "OUT" and is_expense:
        return float(_W_DIRECTION)
    if bank_direction == "OUT" and not is_income:
        # 大多数 OCR 历史是采购发票(默认场景)
        return float(_W_DIRECTION) * 0.7  # 约 10 分
    # 其他情况:不扣分但不加分
    return float(_W_DIRECTION) * 0.3  # 约 4.5 分


def score_keyword(bank_desc: str, invoice_meta: Dict[str, Any]) -> float:
    """描述关键词相似 → 0..5 · 软加分"""
    if not bank_desc:
        return 0.0
    desc_lower = bank_desc.lower()
    vendor = (invoice_meta.get("vendor") or "").lower()
    ref = (invoice_meta.get("invoice_no") or "").lower()

    score = 0.0
    # 供应商名在描述里出现(取前 6 字符以上的片段)
    if vendor and len(vendor) >= 3:
        # 拆 vendor 单词 · 任一个在 desc 中出现就给分
        for w in re.findall(r"[A-Za-z\u0E00-\u0E7F\u4e00-\u9fff]{3,}", vendor):
            if w in desc_lower:
                score += 3.0
                break
    # 发票号在描述里
    if ref and ref in desc_lower:
        score += 2.0
    return min(score, float(_W_KEYWORD))


def match_one_tx(bank_tx: Dict[str, Any], candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """对一条银行流水 · 在候选发票集合中打分排序 · 返回 [{history_id, score, reason, breakdown}, ...]"""
    scored: List[Dict[str, Any]] = []
    for inv in candidates:
        s_amt = score_amount(
            bank_tx.get("amount") or 0, inv.get("amount_total") or inv.get("total") or 0
        )
        if s_amt <= 0:
            continue  # 金额差太大 · 直接跳过
        s_date = score_date(bank_tx.get("tx_date"), inv.get("invoice_date"))
        s_dir = score_direction(bank_tx.get("direction") or "", inv)
        s_kw = score_keyword(bank_tx.get("description") or "", inv)
        total = round(s_amt + s_date + s_dir + s_kw, 2)

        # 生成人类可读原因
        parts = []
        if s_amt >= _W_AMOUNT - 0.5:
            parts.append("金额精确")
        elif s_amt >= _W_AMOUNT - 5.5:
            parts.append("金额接近")
        if s_date >= _W_DATE - 0.5:
            parts.append("同日")
        elif s_date >= 25:
            parts.append("日期差 1 天")
        elif s_date >= 20:
            parts.append("日期差 3 天内")
        elif s_date >= 10:
            parts.append("日期差 7 天内")
        if s_kw > 0:
            parts.append("描述匹配")
        reason = " + ".join(parts) if parts else "低置信"

        scored.append(
            {
                "history_id": inv["id"],
                "score": total,
                "reason": reason,
                "breakdown": {
                    "amount": s_amt,
                    "date": s_date,
                    "direction": s_dir,
                    "keyword": s_kw,
                },
            }
        )
    # 按分降序
    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored[:5]  # 最多留 5 个候选


# ============================================================
# Session 级匹配:遍历所有流水 · 查候选 · 写结果
# ============================================================
def run_matching_for_session(session_id: str, user_id: str) -> Dict[str, Any]:
    """
    对一个对账会话下的所有流水跑匹配
    返回统计:{tx_total, matched, suggested, unmatched, elapsed_ms}
    """
    import time
    import db

    t0 = time.time()
    txs = db.list_bank_recon_transactions(session_id, user_id, limit=2000)
    if not txs:
        return {
            "tx_total": 0,
            "matched": 0,
            "suggested": 0,
            "unmatched": 0,
            "elapsed_ms": 0,
            "error": "no_transactions",
        }

    stat = {"matched": 0, "suggested": 0, "unmatched": 0}

    for tx in txs:
        # 只处理 unmatched / suggested(已被用户确认的 matched 跳过)
        if tx.get("match_status") == "matched":
            stat["matched"] += 1
            continue

        amt = tx.get("amount")
        tx_date = tx.get("tx_date")
        if not amt or not tx_date:
            stat["unmatched"] += 1
            continue

        # 预筛选候选
        if hasattr(tx_date, "isoformat"):
            tx_date_str = tx_date.isoformat()
        else:
            tx_date_str = str(tx_date)

        candidates = db.find_invoice_candidates_for_tx(
            user_id=user_id,
            amount=float(amt),
            tx_date=tx_date_str,
            amount_tol=AMOUNT_TOL_MEDIUM,
            date_tol_days=DATE_TOL_DAYS,
        )

        if not candidates:
            db.save_match_result(tx["id"], [], THRESH_AUTO, THRESH_SUGGEST)
            stat["unmatched"] += 1
            continue

        # 打分
        tx_for_score = {
            "amount": float(amt),
            "tx_date": tx_date_str,
            "direction": tx.get("direction") or "",
            "description": tx.get("description") or "",
        }
        scored = match_one_tx(tx_for_score, candidates)

        # 写结果(算法内只保留 ≥ THRESH_SUGGEST 的)
        scored_kept = [s for s in scored if s["score"] >= THRESH_SUGGEST]
        final_status = db.save_match_result(tx["id"], scored_kept, THRESH_AUTO, THRESH_SUGGEST)
        stat[final_status] = stat.get(final_status, 0) + 1

    # 更新 session 头统计
    db.update_session_match_stats(session_id)

    elapsed = int((time.time() - t0) * 1000)
    return {
        "tx_total": len(txs),
        "matched": stat.get("matched", 0),
        "suggested": stat.get("suggested", 0),
        "unmatched": stat.get("unmatched", 0),
        "elapsed_ms": elapsed,
    }
