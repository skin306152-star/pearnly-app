# -*- coding: utf-8 -*-
"""
services/recon/bank_recon_serialize.py · Pearnly

JSON (de)serialization for reconciliation rows and summary, used to persist
and rehydrate recon results across the async job boundary.
"""

from datetime import date
from typing import List, Dict, Any, Optional
from dataclasses import asdict

from services.recon.bank_recon_types import BankReconRow, BankReconSummary

# EXCEL EXPORT · moved to services/recon/bank_recon_excel.py
from services.recon.bank_recon_excel import export_bank_recon_excel  # noqa: F401 re-export


# ─────────────────────────────────────────────────────────────────────────────
# JSON SERIALIZATION
# ─────────────────────────────────────────────────────────────────────────────
def _date_str(d: Optional[date]) -> Optional[str]:
    return d.isoformat() if d else None


def _date_from_str(s: Optional[str]) -> Optional[date]:
    if not s:
        return None
    try:
        return date.fromisoformat(s)
    except Exception:
        return None


def rows_to_json(rows: List[BankReconRow]) -> List[Dict[str, Any]]:
    result = []
    for r in rows:
        result.append(
            {
                "match_status": r.match_status,
                "match_layer": r.match_layer,
                "stmt_date": _date_str(r.stmt_date),
                "stmt_desc": r.stmt_desc,
                "stmt_withdrawal": r.stmt_withdrawal,
                "stmt_deposit": r.stmt_deposit,
                "stmt_balance": r.stmt_balance,
                "gl_date": _date_str(r.gl_date),
                "gl_doc_no": r.gl_doc_no,
                "gl_account_code": r.gl_account_code,
                "gl_desc": r.gl_desc,
                "gl_debit": r.gl_debit,
                "gl_credit": r.gl_credit,
                "date_diff_days": r.date_diff_days,
                "source_stmt_file": r.source_stmt_file,
                "source_gl_file": r.source_gl_file,
                # v118.33.13.0 · OCR accuracy verification
                "stmt_confidence": r.stmt_confidence,
                "stmt_balance_ok": r.stmt_balance_ok,
                "stmt_autocorrected": getattr(r, "stmt_autocorrected", False),
            }
        )
    return result


def rows_from_json(data: List[Dict[str, Any]]) -> List[BankReconRow]:
    rows = []
    for d in data or []:
        rows.append(
            BankReconRow(
                match_status=d.get("match_status", ""),
                match_layer=d.get("match_layer"),
                stmt_date=_date_from_str(d.get("stmt_date")),
                stmt_desc=d.get("stmt_desc", ""),
                stmt_withdrawal=float(d.get("stmt_withdrawal", 0) or 0),
                stmt_deposit=float(d.get("stmt_deposit", 0) or 0),
                stmt_balance=float(d.get("stmt_balance", 0) or 0),
                gl_date=_date_from_str(d.get("gl_date")),
                gl_doc_no=d.get("gl_doc_no", ""),
                gl_account_code=d.get("gl_account_code", ""),
                gl_desc=d.get("gl_desc", ""),
                gl_debit=float(d.get("gl_debit", 0) or 0),
                gl_credit=float(d.get("gl_credit", 0) or 0),
                date_diff_days=d.get("date_diff_days"),
                source_stmt_file=d.get("source_stmt_file", ""),
                source_gl_file=d.get("source_gl_file", ""),
                stmt_confidence=d.get("stmt_confidence", "high"),
                stmt_balance_ok=d.get("stmt_balance_ok"),
                stmt_autocorrected=bool(d.get("stmt_autocorrected", False)),
            )
        )
    return rows


def summary_to_json(s: BankReconSummary) -> Dict[str, Any]:
    return asdict(s)


def summary_from_json(d: Dict[str, Any]) -> BankReconSummary:
    if not d:
        return BankReconSummary()
    try:
        return BankReconSummary(
            **{k: v for k, v in d.items() if k in BankReconSummary.__dataclass_fields__}
        )
    except Exception:
        return BankReconSummary()
