"""Explicit local simulator fixture; replaces only the external OCR model result."""

from contextvars import ContextVar
from uuid import uuid4

fixture_direction = ContextVar("erp_sim_fixture", default=None)


def install():
    from services.ocr import entrypoints
    from services.ocr.schemas import PipelinePageResult, PipelineResult, ThaiInvoice

    original = entrypoints.run_pipeline_for_file

    def recognize(*args, **kwargs):
        direction = fixture_direction.get()
        if not direction:
            return original(*args, **kwargs)
        own = "buyer" if direction == "purchase" else "seller"
        invoice = ThaiInvoice(
            invoice_number=f"SIM-{uuid4().hex[:12]}",
            date="2026-09-15",
            seller_name="Simulator supplier",
            buyer_name="Simulator customer",
            **{f"{own}_tax": "0105559999999"},
            items=[{"name": "SIMULATED OCR item", "qty": "2", "price": "100", "subtotal": "200"}],
            subtotal="200",
            vat="14",
            total_amount="214",
        )
        return PipelineResult(
            pages=[PipelinePageResult(page_number=1, invoice=invoice)],
            page_count=1,
            elapsed_ms=0,
            engine="local_fixture_no_model",
        )

    entrypoints.run_pipeline_for_file = recognize
