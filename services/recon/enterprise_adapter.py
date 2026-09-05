"""Recon entrance adapter; consumes every page and never repairs output twice."""

from __future__ import annotations

from datetime import date

from services.ocr.engine_policy import engine_context
from services.ocr.enterprise_pipeline import category_for
from services.ocr.error_format import short_error
from services.ocr.pipeline import IMAGE_EXTENSIONS, run_on_image_bytes, run_on_pdf_bytes
from services.recon.bank_recon_types import GlRow, StatementRow
from services.recon.bank_recon_utils import _to_float


def _date(value):
    try:
        return date.fromisoformat(value)
    except (TypeError, ValueError):
        return None


def try_parse(content: bytes, filename: str, category: str, *, account_code="") -> dict | None:
    ext = "." + filename.lower().rsplit(".", 1)[-1]
    if ext != ".pdf" and ext not in IMAGE_EXTENSIONS:
        return None  # structured formats retain their native parsers
    document_type = "bank_statement" if category == "bank" else "general_ledger"
    task = "bank_statement" if category == "bank" else "gl_ledger"
    with engine_context(task):
        if category_for(document_type) is None:
            return None
        try:
            pipeline = (run_on_pdf_bytes if ext == ".pdf" else run_on_image_bytes)(
                content,
                document_type=document_type,
            )
        except Exception as exc:
            return {
                "ok": False,
                "rows": [],
                "row_count": 0,
                "error_code": "ocr_failed",
                "error": short_error(exc),
                "parser_version": "enterprise-v1",
                "needs_review": True,
            }
    rows = []
    for page in pipeline.pages:
        for entry in page.document.entries:
            if category == "bank":
                rows.append(
                    StatementRow(
                        date=_date(entry.transaction_date),
                        description=entry.description,
                        deposit=_to_float(entry.deposit),
                        withdrawal=_to_float(entry.withdrawal),
                        balance=_to_float(entry.balance),
                        source_file=filename,
                        confidence="low" if page.needs_manual_review else "medium",
                        amount_autocorrected=entry.chain_amount_imputed,
                        direction_autocorrected=entry.chain_repaired,
                    )
                )
            elif not account_code or entry.account_code == account_code:
                rows.append(
                    GlRow(
                        date=_date(entry.transaction_date),
                        doc_no=entry.voucher_no,
                        account_code=entry.account_code,
                        description=entry.description,
                        debit=_to_float(entry.debit),
                        credit=_to_float(entry.credit),
                        balance=_to_float(entry.balance),
                        source_file=filename,
                    )
                )
    return {
        "ok": bool(rows),
        "rows": rows,
        "row_count": len(rows),
        "opening": _to_float(pipeline.pages[0].document.opening_balance),
        "closing": _to_float(pipeline.pages[-1].document.closing_balance),
        "bank_code": "generic",
        "accounts": sorted({r.account_code for r in rows}) if category == "gl" else [],
        "parser_version": pipeline.engine,
        "needs_review": any(p.needs_manual_review for p in pipeline.pages),
        "extraction_audit": [p.extraction_audit for p in pipeline.pages],
        "validation_warnings": [w for p in pipeline.pages for w in p.validation_warnings],
        "estimated_cost_thb": pipeline.estimated_cost_thb,
        "elapsed_ms": pipeline.elapsed_ms,
        "page_count": pipeline.page_count,
    }
