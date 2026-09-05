"""Cross-instance request spacing using the existing internal lease table.

The lease is intentionally NOT released after an HTTP response: it reserves
one request interval, rather than protecting concurrent execution.
"""

from __future__ import annotations

import os
import time
import uuid

from services.ocr.layer1_base import Layer1QuotaError


def try_reserve(key: str, interval_s: float) -> bool:
    from core.db import get_cursor

    with get_cursor(commit=True) as cur:
        cur.execute(
            "INSERT INTO cloud_task_locks(name, owner, lease_until) "
            "VALUES (%s, %s::uuid, clock_timestamp() + %s * interval '1 second') "
            "ON CONFLICT(name) DO UPDATE SET owner=EXCLUDED.owner, "
            "lease_until=EXCLUDED.lease_until "
            "WHERE cloud_task_locks.lease_until <= clock_timestamp() RETURNING owner",
            (key, str(uuid.uuid4()), interval_s),
        )
        return cur.fetchone() is not None


def wait_for_slot(processor: str, *, timeout_s: float = 120) -> float:
    # Quota is project + region + processor TYPE, not processor ID.
    parts = processor.split("/")
    key = f"ocr:documentai:{parts[1]}:{parts[3]}:OCR_PROCESSOR"
    rpm = float(os.environ.get("ENTERPRISE_OCR_REQUESTS_PER_MINUTE", "9"))
    if not 0 < rpm <= 10000:
        raise ValueError("ENTERPRISE_OCR_REQUESTS_PER_MINUTE must be positive and bounded")
    interval = 60 / rpm
    started = time.monotonic()
    while True:
        # Database failure deliberately propagates. A per-process fallback
        # would silently multiply quota when Cloud Run scales out.
        if try_reserve(key, interval):
            return time.monotonic() - started
        remaining = timeout_s - (time.monotonic() - started)
        if remaining <= 0:
            raise Layer1QuotaError("Enterprise OCR shared queue wait exceeded deadline")
        time.sleep(min(interval, 0.5, remaining))
