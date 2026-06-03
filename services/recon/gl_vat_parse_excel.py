# -*- coding: utf-8 -*-
"""GL Excel 解析 + 统一入口 dispatch + pipeline 适配（gl_vat_reconciler 拆分）。"""

import io
import logging
from datetime import date, datetime
from typing import List, Dict, Any

from services.recon.field_comparator import normalize_invoice_no
from services.ocr.error_format import short_error as _short_err
from services.recon.gl_vat_types import GlRow
from services.recon.gl_vat_parse_pdf import parse_gl_pdf
from services.recon.gl_vat_parse_common import (
    _to_float,
    _is_revenue_acct,
    _hit,
    _extract_account_code,
    _is_skip_row,
    normalize_doc_no,
    _map_gl_columns,
    _row_has_amount,
    _GL_DEBIT_H,
    _GL_CRED_H,
)

logger = logging.getLogger(__name__)
PARSER_VERSION = "1.0.0"


# ─────────────────────────────────────────────────────────────────────
# GL Excel 解析
# ─────────────────────────────────────────────────────────────────────
def parse_gl_excel(file_bytes: bytes, revenue_prefix: str = "4") -> Dict[str, Any]:
    """
    解析 GL Excel
    自适应两种格式：
      A) 含 "account" 列：每行直接附带科目代码
      B) 科目作为分节标题行：科目代码独占一行/合并单元格
    """
    try:
        import openpyxl
    except ImportError:
        return {"ok": False, "rows": [], "row_count": 0, "error": "openpyxl 未安装"}

    rows: List[GlRow] = []
    current_account = ""
    col_map: Dict[str, int] = {}
    has_acct_col = False

    try:
        wb = openpyxl.load_workbook(io.BytesIO(file_bytes), data_only=True)
        for ws in wb.worksheets:
            current_account = ""
            col_map = {}
            has_acct_col = False
            for row in ws.iter_rows(values_only=True):
                cells = list(row)
                if not any(c is not None and str(c).strip() for c in cells):
                    continue

                # 1. 表头检测
                has_dr = any(_hit(str(c or ""), _GL_DEBIT_H) for c in cells)
                has_cr = any(_hit(str(c or ""), _GL_CRED_H) for c in cells)
                if has_dr and has_cr:
                    col_map = _map_gl_columns(cells)
                    has_acct_col = "account" in col_map
                    continue

                row_text = " ".join(str(c or "") for c in cells)

                # 2. 分节标题（无 account 列时才看）
                if not has_acct_col:
                    acct = _extract_account_code(row_text)
                    if acct and _is_revenue_acct(acct, revenue_prefix):
                        if not _row_has_amount(cells, col_map or {}):
                            current_account = acct
                            continue

                # 3. 跳过汇总行
                if _is_skip_row(cells):
                    continue

                if not col_map:
                    continue

                def _get(field: str) -> str:
                    idx = col_map.get(field)
                    if idx is None or idx >= len(cells):
                        return ""
                    v = cells[idx]
                    if v is None:
                        return ""
                    # BUG-FIX-T5 v118.35.0.46 · datetime cell 转 ISO date 字符串 + 佛历→公历
                    # 同 M4 BUG-FIX-T1 修法(bank_recon_v2._parse_date)· 让 M3 GlRow.date 字段
                    # 不再显示 "2568-12-31 00:00:00" garbage · 改 "2025-12-31" 公历干净
                    if isinstance(v, (datetime, date)):
                        y = v.year
                        if y >= 2500:
                            y -= 543
                        try:
                            return date(y, v.month, v.day).isoformat()
                        except (ValueError, AttributeError):
                            pass
                    return str(v).strip()

                # 决定 account_code
                if has_acct_col:
                    raw = _get("account")
                    acct = _extract_account_code(raw) or raw
                    if not _is_revenue_acct(acct, revenue_prefix):
                        continue
                    current_account = acct
                else:
                    if not current_account:
                        continue

                doc_no = _get("doc_no")
                if not doc_no:
                    continue
                debit = _to_float(_get("debit"))
                credit = _to_float(_get("credit"))
                if debit == 0.0 and credit == 0.0:
                    continue

                rows.append(
                    GlRow(
                        doc_no=doc_no,
                        norm_doc_no=normalize_doc_no(doc_no),
                        date=_get("date"),
                        account_code=current_account,
                        description=_get("description"),
                        debit=debit,
                        credit=credit,
                    )
                )
    except Exception as e:
        logger.error(f"[gl_excel] 解析失败: {e}", exc_info=True)
        return {"ok": False, "rows": [], "row_count": 0, "error": str(e)}

    logger.info(f"[gl_excel] 解析完成: {len(rows)} 行 · 收入前缀={revenue_prefix}")
    return {"ok": True, "rows": rows, "row_count": len(rows), "error": ""}


# ─────────────────────────────────────────────────────────────────────
# 统一入口
# ─────────────────────────────────────────────────────────────────────
def parse_gl(file_bytes: bytes, filename: str, revenue_prefix: str = "4") -> Dict[str, Any]:
    """按后缀分发解析 GL 文件。

    2026-05-21 multi-format refactor:
    - .xlsx / .xls      → parse_gl_excel (structural, reliable)
    - .pdf              → parse_gl_pdf   (existing Gemini Vision path)
    - .csv / .tsv / .docx / .doc / .txt / 图片 → 新统一 pipeline,
      显式 document_type='general_ledger' 让 prompt + validators 防止
      description 列的数字(例如 6091)被识别成 debit/credit/amount。
    """
    import os as _os

    ext = (filename or "").lower().rsplit(".", 1)[-1]
    if ext in ("xlsx", "xls"):
        return parse_gl_excel(file_bytes, revenue_prefix)
    if ext == "pdf":
        # 2026-05-21: PDF GL defaults to the new pipeline so description-column
        # numbers (e.g. 6091) can't leak into debit/credit. Set
        # OCR_PDF_GL_LEGACY=true to opt back into the older Gemini-Vision
        # parse_gl_pdf path (kept for emergency rollback).
        if _os.environ.get("OCR_PDF_GL_LEGACY", "").strip().lower() == "true":
            return parse_gl_pdf(file_bytes, revenue_prefix)
        result = _parse_gl_via_pipeline(file_bytes, filename, revenue_prefix)
        if result.get("ok") and result.get("rows"):
            return result
        # Pipeline returned 0 rows or errored — fall back to legacy so we
        # don't worsen the worst case (legacy at least extracted SOMETHING
        # for the production customers we already serve).
        logger.warning(
            f"[parse_gl] pipeline yielded {result.get('row_count')} rows / "
            f"err={result.get('error')!r} · falling back to parse_gl_pdf"
        )
        return parse_gl_pdf(file_bytes, revenue_prefix)
    return _parse_gl_via_pipeline(file_bytes, filename, revenue_prefix)


def _parse_gl_via_pipeline(file_bytes: bytes, filename: str, revenue_prefix: str) -> Dict[str, Any]:
    """Route non-PDF/non-Excel GL files through services/ocr/pipeline with
    document_type=general_ledger, then convert the normalized JSON into the
    List[GlRow] shape gl_vat_reconciler.reconcile_gl_vat expects.

    Supported here: CSV / TSV / Word / image / TXT.
    Excludes Excel and PDF on purpose — those paths already work well and
    have been tested with real customer data; not worth the regression risk
    in this refactor.
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
        return {"ok": False, "rows": [], "row_count": 0, "error": f"pipeline import failed: {e}"}

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
                "error": f"暂不支持 {ext_dot} · 请上传 Excel / PDF / CSV / Word / 图片",
            }
    except Exception as e:
        return {"ok": False, "rows": [], "row_count": 0, "error": _short_err(e)}

    legacy = pipeline_result_to_legacy_dict(pr)
    rows = _gl_rows_from_pipeline_legacy(legacy, revenue_prefix)
    warnings = []
    for p in legacy.get("pages") or []:
        warnings.extend(p.get("_validation_warnings") or [])
    return {
        "ok": True,
        "rows": rows,
        "row_count": len(rows),
        "parser_version": f"{PARSER_VERSION}+pipeline_v1",
        "needs_review": legacy.get("_needs_review", False),
        "validation_warnings": warnings,
    }


def _gl_rows_from_pipeline_legacy(legacy_dict: Dict[str, Any], revenue_prefix: str) -> List[GlRow]:
    """Convert pipeline normalized JSON (general_ledger) → List[GlRow] for
    reconcile_gl_vat. Filters to revenue rows (account_code starts with
    revenue_prefix, e.g. "4") and ensures amounts came from Debit/Credit
    (not from description) — validators already cleared mis-sourced fields,
    so any debit/credit value left here is provenance-clean.
    """
    out: List[GlRow] = []
    for page in legacy_dict.get("pages") or []:
        doc = (page or {}).get("document") or {}
        for e in doc.get("entries") or []:
            account_code = (e.get("account_code") or "").strip()
            if revenue_prefix and not account_code.startswith(revenue_prefix):
                continue
            try:
                debit = float(e.get("debit") or 0)
            except (ValueError, TypeError):
                debit = 0.0
            try:
                credit = float(e.get("credit") or 0)
            except (ValueError, TypeError):
                credit = 0.0
            if debit == 0.0 and credit == 0.0:
                continue
            doc_no_raw = (e.get("voucher_no") or "").strip()
            try:
                norm = normalize_invoice_no(doc_no_raw) if doc_no_raw else ""
            except Exception:
                norm = doc_no_raw
            out.append(
                GlRow(
                    doc_no=doc_no_raw,
                    norm_doc_no=norm,
                    date=e.get("transaction_date") or "",
                    account_code=account_code,
                    description=e.get("description") or "",
                    debit=debit,
                    credit=credit,
                )
            )
    return out
