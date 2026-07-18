# -*- coding: utf-8 -*-
"""
services/recon/bank_recon_pipeline.py · Pearnly

Adapters bridging the unified services/ocr pipeline output to the recon
engine: parse statements / GL via the pipeline (Excel/CSV/Word/image) and
normalise into StatementRow / GlRow. The pdfplumber+Gemini paths stay in the
bank_recon_v2 orchestrators.
"""

import logging
from datetime import date
from typing import List, Dict, Any, Optional

from services.ocr.error_format import short_error as _short_err
from services.recon.bank_recon_types import StatementRow
from services.recon.bank_recon_utils import _to_float, _parse_date, _BANK_SIGNATURES
from services.recon.bank_stmt_balance import (
    _correct_direction_from_balance,
    _repair_amount_from_balance,
    _verify_row_balances,
)
from services.recon.bank_stmt_xlsx import parse_bank_stmt_xlsx_direct
from services.recon.bank_stmt_legacy import gl_rows_from_pipeline_legacy
from services.recon.bank_table_io import _is_summary_row

logger = logging.getLogger(__name__)


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
        tx_date = _parse_date(e.get("transaction_date_raw") or "")
        if tx_date is None and e.get("transaction_date"):
            try:
                yy, mm, dd = e["transaction_date"].split("-")
                tx_date = date(int(yy), int(mm), int(dd))
            except (ValueError, AttributeError):
                tx_date = None
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

    # 台账#11 · 图片/扫描件路此前拿到行就直接返回,余额链三件套(方向纠正/逐行核对/
    # 金额反推修复)只跑 PDF 与 xlsx 路 → 实弹 5/56 行方向翻转静默放行。与其余两路
    # 同序接线;期初取文档级字段(无动行已被上面过滤,行内无从兜底)。
    rows = [r for r in rows if not _is_summary_row(r.description)]
    opening = _to_float(doc.get("opening_balance"))
    closing = _to_float(doc.get("closing_balance"))
    _correct_direction_from_balance(rows, opening)
    _verify_row_balances(rows, opening)
    _repair_amount_from_balance(rows, opening)
    balance_warn_count = sum(1 for r in rows if r.balance_ok is False)
    if not closing:
        closing = next((r.balance for r in reversed(rows) if r.balance), 0.0)

    return {
        "ok": True,
        "rows": rows,
        "row_count": len(rows),
        "opening": opening,
        "closing": closing,
        "bank_code": bank_code,
        "balance_warn_count": balance_warn_count,
        "parser_version": "bank_recon_v2+pipeline_v1",
        "needs_review": bool(legacy.get("_needs_review", False) or balance_warn_count),
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
