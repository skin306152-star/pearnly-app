"""Loss-aware adapter from the frozen extraction contract to business schemas."""

from __future__ import annotations

from copy import deepcopy

from services.ocr.schemas import PipelinePageResult, ThaiInvoice
from services.ocr.schemas_documents import (
    BankStatementDocument,
    GeneralLedgerDocument,
    VatReportDocument,
)

TYPES = {"bank": BankStatementDocument, "gl": GeneralLedgerDocument, "vat": VatReportDocument}
DOCUMENT_TYPES = {"bank": "bank_statement", "gl": "general_ledger", "vat": "vat_report"}


def make_page(
    document: dict,
    category: str,
    page_number: int,
    *,
    audit=None,
    provenance=None,
    issues=None,
    local=False,
) -> PipelinePageResult:
    data = deepcopy(document)
    audit, provenance, issues = audit or [], provenance or [], issues or []
    data["document_type"] = DOCUMENT_TYPES[category]
    for row in data.get("entries") or []:
        if category == "gl":
            # Benchmark uses debit/credit; production recon uses deposit/withdrawal.
            row["direction"] = {"debit": "deposit", "credit": "withdrawal"}.get(
                row.get("direction"), row.get("direction", "")
            )
            row["raw_row_data"] = {
                **row.get("raw_row_data", {}),
                "enterprise_source": deepcopy(row),
            }
    review = bool(local or issues or audit)
    return PipelinePageResult(
        page_number=page_number,
        invoice=ThaiInvoice(is_not_invoice=True),
        document_type=DOCUMENT_TYPES[category],
        document=TYPES[category].model_validate(data),
        layer_chain=["enterprise", "local_schema" if local else "schema38"],
        needs_manual_review=review,
        confidence_band="needs_review" if review else "yellow_confirm",
        # Do not fabricate a calibrated confidence score from arithmetic gates.
        final_confidence=0,
        validation_warnings=list(issues),
        extraction_audit={
            "contract": "enterprise-2026-09-03-v1",
            "local": local,
            "repairs": deepcopy(audit),
            "provenance": deepcopy(provenance),
        },
    )
