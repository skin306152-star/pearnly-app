# -*- coding: utf-8 -*-
"""bank_statement:银行对账单(含零用金)→ 免费结构化解析优先
(Excel 直读 / PDF 文字层坐标重建),扫描件才走 Gemini 兜底。"""

from __future__ import annotations

from services.ocr.contracts import OcrRequest


def handle(req: OcrRequest):
    from services.recon import bank_recon_v2

    return bank_recon_v2._parse_bank_statement_impl(
        req.file_bytes,
        req.filename,
        api_key=req.api_key or "",
        tenant_id=req.tenant_id,
    )
