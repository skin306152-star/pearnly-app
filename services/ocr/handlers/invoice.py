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
from services.ocr.roundtrip_intake import try_parse_roundtrip


def handle(req: OcrRequest):
    name = (req.filename or "").lower()
    ext = "." + name.rsplit(".", 1)[-1] if "." in name else ""
    max_pages = int(req.options.get("max_pages", 50))
    document_type = req.options.get("document_type", "auto")
    if ext in PDF_EXTENSIONS:
        return run_on_pdf_bytes(
            req.file_bytes, max_pages=max_pages, api_key=req.api_key, document_type=document_type
        )
    if ext in IMAGE_EXTENSIONS:
        return run_on_image_bytes(req.file_bytes, api_key=req.api_key, document_type=document_type)
    if ext in TABLE_EXTENSIONS:
        # 会计改过的复核工作簿丢回来重录:是我们自己写出去的表,逐格读即可,
        # 没必要再让 L2 去"理解"一遍网格(多花钱且平白引入读错)。不是 → None 回落。
        parsed = try_parse_roundtrip(req.file_bytes, req.filename)
        if parsed is not None:
            return parsed
        return run_on_table_bytes(
            req.file_bytes, filename=req.filename, api_key=req.api_key, document_type=document_type
        )
    raise ValueError(f"unsupported OCR file extension: {ext}")
