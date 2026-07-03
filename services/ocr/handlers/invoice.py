# -*- coding: utf-8 -*-
"""invoice:发票/采购/LINE 图 → services/ocr/pipeline(L0 文字层→L1→L2→触发式 L3)。
按扩展名派发的逻辑从 entrypoints.run_pipeline_for_file 原样搬入,返回 PipelineResult。"""

from __future__ import annotations

from services.ocr.contracts import OcrRequest
from services.ocr.pipeline import (
    IMAGE_EXTENSIONS,
    PDF_EXTENSIONS,
    TABLE_EXTENSIONS,
    run_on_image_bytes,
    run_on_pdf_bytes,
    run_on_table_bytes,
)


def handle(req: OcrRequest):
    name = (req.filename or "").lower()
    ext = "." + name.rsplit(".", 1)[-1] if "." in name else ""
    max_pages = int(req.options.get("max_pages", 50))
    if ext in PDF_EXTENSIONS:
        return run_on_pdf_bytes(req.file_bytes, max_pages=max_pages, api_key=req.api_key)
    if ext in IMAGE_EXTENSIONS:
        return run_on_image_bytes(req.file_bytes, api_key=req.api_key)
    if ext in TABLE_EXTENSIONS:
        return run_on_table_bytes(req.file_bytes, filename=req.filename, api_key=req.api_key)
    raise ValueError(f"unsupported OCR file extension: {ext}")
