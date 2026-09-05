"""Metered, quota-aware Document AI reads, preserving raw page geometry."""

from __future__ import annotations

import time
from dataclasses import dataclass

from services.ai_gateway import attribution, logging as ai_log
from services.ai_gateway.providers import enterprise
from services.ai_gateway.tasks import AiResult
from services.ocr.cost import THB_PER_USD
from services.ocr.enterprise_quota import wait_for_slot
from services.ocr.layer1_base import Layer1AuthError, Layer1Error, Layer1QuotaError

# Paid basic OCR rate, deliberately no free-tier/credit deduction.
USD_PER_PAGE = 0.0015


@dataclass
class ReadResult:
    payload: dict
    pages: int
    queue_ms: int
    request_ms: int
    cost_thb: float


def read(content: bytes, mime: str, *, expected_pages: int) -> ReadResult:
    if expected_pages < 1 or expected_pages > 15:
        raise ValueError("Enterprise online reads require chunks of 1–15 pages")
    name = enterprise.processor_name()
    queue_ms = int(wait_for_slot(name) * 1000)
    started = time.monotonic()
    ok, error_kind, billed_pages = False, None, 0
    try:
        payload = enterprise.process_raw(content, mime)
        billed_pages = len(enterprise.page_texts(payload))
        if billed_pages != expected_pages:
            raise Layer1Error("Enterprise OCR response page count differs from input")
        ok = True
        return ReadResult(
            payload,
            billed_pages,
            queue_ms,
            int((time.monotonic() - started) * 1000),
            billed_pages * USD_PER_PAGE * THB_PER_USD,
        )
    except Layer1AuthError:
        error_kind = "auth"
        raise
    except Layer1QuotaError:
        error_kind = "quota"
        raise
    except Exception:
        error_kind = "provider"
        raise
    finally:
        attr = attribution.current() or {}
        ai_log.log_call(
            AiResult(
                ok=ok,
                task=attr.get("task") or "ocr.enterprise",
                schema_version="1",
                provider="document_ai",
                model=enterprise.PROCESSOR_VERSION,
                error_kind=error_kind,
                latency_ms=int((time.monotonic() - started) * 1000),
                cost_thb=billed_pages * USD_PER_PAGE * THB_PER_USD,
            ),
            tenant_id=attr.get("tenant_id"),
            user_id=attr.get("user_id"),
            trace_id=attr.get("trace_id"),
        )
