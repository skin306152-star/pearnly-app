# -*- coding: utf-8 -*-
"""bank_statement:银行对账单(含零用金)→ 免费结构化解析优先
(Excel 直读 / PDF 文字层坐标重建),扫描件才走 Gemini 兜底。"""

from __future__ import annotations

from services.ocr.contracts import OcrRequest


def handle(req: OcrRequest):
    if req.options.get("shape") == "legacy_parsed_statement":
        return _legacy_parsed_statement(req)

    from services.recon import bank_recon_v2

    return bank_recon_v2._parse_bank_statement_impl(
        req.file_bytes,
        req.filename,
        api_key=req.api_key or "",
        tenant_id=req.tenant_id,
    )


def _legacy_parsed_statement(req: OcrRequest):
    from services.ocr.legacy_adapter import pipeline_result_to_legacy_dict
    from services.ocr.pipeline import (
        IMAGE_EXTENSIONS,
        PDF_EXTENSIONS,
        TABLE_EXTENSIONS,
        run_on_image_bytes,
        run_on_table_bytes,
    )
    from services.recon import bank_recon_v2

    name = (req.filename or "").lower()
    ext = "." + name.rsplit(".", 1)[-1] if "." in name else ""
    if ext in PDF_EXTENSIONS:
        return bank_recon_v2.parse_statement_pdf(req.file_bytes, req.filename)
    if ext in IMAGE_EXTENSIONS:
        pr = run_on_image_bytes(req.file_bytes, api_key=req.api_key, document_type="bank_statement")
    elif ext in TABLE_EXTENSIONS:
        pr = run_on_table_bytes(
            req.file_bytes,
            filename=req.filename or "statement",
            api_key=req.api_key,
            document_type="bank_statement",
        )
    else:
        raise ValueError(f"unsupported bank statement file extension: {ext}")
    return bank_recon_v2.parsed_from_pipeline_legacy(
        pipeline_result_to_legacy_dict(pr), req.filename
    )
