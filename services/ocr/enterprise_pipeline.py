"""Candidate A pipeline: pinned OCR -> local schema or pinned image + schema.

No legacy prompt or 3.1 call is used in this module. Provider failures propagate;
callers must not silently substitute a different extraction method.
"""

from __future__ import annotations

import io
import time
from copy import deepcopy

from services.ai_gateway import costing
from services.ai_gateway.providers import enterprise, enterprise_schema
from services.ocr import enterprise_reader
from services.ocr.enterprise_adapter import make_page
from services.ocr.enterprise_local.result import check_document, reconstruct
from services.ocr.layer1_base import Layer1Error
from services.ocr.schemas import PipelineResult


def category_for(document_type: str) -> str | None:
    from services.ocr.engine_policy import active_mode

    if active_mode() != "enterprise":
        return None
    return {"bank_statement": "bank", "general_ledger": "gl", "vat_report": "vat"}.get(
        document_type
    )


def read_pdf(pdf: bytes, page_count: int) -> list[enterprise_reader.ReadResult]:
    import fitz

    results = []
    with fitz.open(stream=pdf, filetype="pdf") as document:
        if document.page_count != page_count:
            raise ValueError("PDF render and Enterprise input page counts differ")
        for start in range(0, page_count, 15):
            end = min(start + 15, page_count)
            with fitz.open() as chunk:
                chunk.insert_pdf(document, from_page=start, to_page=end - 1)
                results.append(
                    enterprise_reader.read(
                        chunk.tobytes(),
                        "application/pdf",
                        expected_pages=end - start,
                    )
                )
    return results


def _local_pages(result, category):
    pages = []
    previous = result.document.get("opening_balance", "")
    for number in range(1, result.pages + 1):
        document = deepcopy(result.document)
        document["entries"] = [row for row in document["entries"] if int(row["page"]) == number]
        document["opening_balance"] = previous
        document["closing_balance"] = document["entries"][-1].get("balance", "")
        previous = document["closing_balance"]
        # Document-wide totals must not be repeated as each page's printed totals.
        for field in ("total_debit", "total_credit"):
            document[field] = ""
        pages.append(
            make_page(
                document,
                category,
                number,
                audit=result.audit if number == 1 else [],
                provenance=result.provenance if number == 1 else [],
                issues=result.issues,
                local=True,
            )
        )
    return pages


def run(images: list[bytes], category: str, *, pdf: bytes | None = None) -> PipelineResult:
    if category not in ("bank", "gl", "vat") or not images:
        raise ValueError("Enterprise pipeline requires bank/gl/vat images")
    started = time.monotonic()
    from PIL import Image

    mimes = []
    for content in images:
        with Image.open(io.BytesIO(content)) as image:
            mimes.append(Image.MIME[image.format])
    reads = (
        read_pdf(pdf, len(images))
        if pdf is not None
        else [
            enterprise_reader.read(content, mime, expected_pages=1)
            for content, mime in zip(images, mimes)
        ]
    )
    payloads = [result.payload for result in reads]
    cost = sum(result.cost_thb for result in reads)
    pages = None
    if category in ("bank", "gl"):
        local = reconstruct(payloads, category, expected_pages=len(images))
        if local.arithmetic_passed:
            pages = _local_pages(local, category)
    if pages is None:
        transcripts = [
            page.text for result in reads for page in enterprise.page_texts(result.payload)
        ]
        if len(transcripts) != len(images):
            raise Layer1Error("Enterprise page transcript count differs from images")
        pages = []
        for number, (content, mime, transcript) in enumerate(zip(images, mimes, transcripts), 1):
            outcome, elapsed = enterprise_schema.extract(content, mime, category, transcript)
            if not outcome.ok:
                raise Layer1Error(f"Enterprise schema extraction failed: {outcome.error_kind}")
            document = outcome.data
            for row in document.get("entries") or []:
                row["page"] = str(number)
            # Per-page arithmetic alone is not evidence of full-file correctness.
            issues = ["schema_transcription_requires_document_validation"]
            if not document.get("entries"):
                issues.append("no_transaction_rows")
            page = make_page(document, category, number, issues=issues)
            page.layer2_model = outcome.model
            page.layer2_ms = elapsed
            page.layer2_input_tokens = outcome.input_tokens
            page.layer2_output_tokens = outcome.output_tokens
            pages.append(page)
            cost += costing.estimate_thb(outcome.model, outcome.input_tokens, outcome.output_tokens)
        if category in ("bank", "gl"):
            aggregate = {
                "opening_balance": pages[0].document.opening_balance,
                "closing_balance": pages[-1].document.closing_balance,
                "entries": [
                    {**row.model_dump(), "page": str(page.page_number)}
                    for page in pages
                    for row in page.document.entries
                ],
            }
            for page in pages:
                page.validation_warnings.extend(check_document(aggregate, category, len(images)))
    pages[0].layer1_ms = sum(result.request_ms for result in reads)
    pages[0].extraction_audit["queue_ms"] = sum(result.queue_ms for result in reads)
    elapsed = int((time.monotonic() - started) * 1000)
    return PipelineResult(
        pages=pages,
        page_count=len(images),
        elapsed_ms=elapsed,
        engine="enterprise-2026-09-03-v1",
        estimated_cost_thb=cost,
    )
