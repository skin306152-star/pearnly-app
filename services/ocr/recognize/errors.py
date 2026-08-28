"""Classify OCR pipeline failures without depending on HTTP route state."""

from __future__ import annotations

from typing import Optional

_USER_FAULT_EXC_NAMES = {
    "Layer1PDFError": "ocr.invalid_file",
    "Layer1InvalidImageError": "ocr.unreadable_file",
}


def classify_pipeline_error(exc: Exception) -> Optional[str]:
    if isinstance(exc, ValueError):
        return f"ocr.invalid_file: {exc}"
    detail = _USER_FAULT_EXC_NAMES.get(type(exc).__name__)
    if detail == "ocr.invalid_file":
        return f"{detail}: {exc}"
    return detail
