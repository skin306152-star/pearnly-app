# -*- coding: utf-8 -*-
"""
services/ocr/error_format.py · v118.35.0.3 (2026-05-21)

Single-line user-facing error formatter for OCR / reconciliation pipelines.

Why this module exists
----------------------
The OCR pipeline (layer2_structure / layer3_fallback) validates extracted
data against pydantic schemas. When a document's columns don't line up with
the chosen schema (e.g. an unrelated workbook uploaded as a "bank statement"),
pydantic raises a ValidationError whose str() is multi-line, lists every
field, and ends with a pydantic.dev documentation URL — totally unfit to
show a会计师 in a red toast.

Routes like /api/recon/bank-v2/run and /api/recon/gl-vat/run used to embed
the raw exception text into their JSON response via
    f"pipeline parse failed: {type(e).__name__}: {e}"
which surfaced as a giant scary block. Run every such raw exception through
`short_error(e)` and the user sees a single human sentence instead.
"""

from __future__ import annotations

import re
from typing import Any


_PYDANTIC_DOC_RE = re.compile(r"https?://errors\.pydantic\.dev/\S+", re.IGNORECASE)
_MAX_LEN = 160


def short_error(e: BaseException) -> str:
    """Reduce any exception (especially pydantic.ValidationError) into ONE
    short, user-facing line. Safe to embed inside an i18n template like
    'GL 解析失败：{e}'.
    """
    try:
        from pydantic import ValidationError  # local import, avoids hard dep cycle
        if isinstance(e, ValidationError):
            return _fmt_validation(e)
    except Exception:
        pass

    msg = str(e) if e else e.__class__.__name__
    # Strip pydantic doc URLs even when ValidationError is wrapped in another
    # exception (we've seen ValueError("layer2: ... ValidationError(...)")).
    msg = _PYDANTIC_DOC_RE.sub("", msg)
    # Keep only the first line — anything after \n is internals.
    msg = msg.split("\n", 1)[0].strip()
    if len(msg) > _MAX_LEN:
        msg = msg[: _MAX_LEN - 1].rstrip() + "…"
    return msg or e.__class__.__name__


def _fmt_validation(e: Any) -> str:
    try:
        errs = list(e.errors())
    except Exception:
        errs = []
    if not errs:
        return "字段校验失败 · 请确认文件格式与表头是否完整"

    fields = []
    for er in errs:
        loc = er.get("loc") or []
        parts = [str(p) for p in loc if not (isinstance(p, int) and p == 0)]
        if parts:
            fields.append(".".join(parts))
    fields = list(dict.fromkeys(fields))  # de-dup, keep order

    n = len(errs)
    if fields:
        head = ", ".join(fields[:3])
        if len(fields) > 3:
            head += f"…(+{len(fields) - 3})"
        return f"字段识别失败 · 共 {n} 项 · 例如 {head} · 请确认文件表头是否完整"
    return f"字段识别失败 · 共 {n} 项 · 请确认文件表头是否完整"
