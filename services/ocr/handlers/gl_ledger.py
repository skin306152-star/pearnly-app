# -*- coding: utf-8 -*-
"""gl_ledger:GL 总账 → Excel/CSV 结构直读优先,PDF 走 pipeline,
读不出再退 bank_gl_pdf 的 pdfplumber/Gemini 链。"""

from __future__ import annotations

from services.ocr.contracts import OcrRequest


def handle(req: OcrRequest):
    from services.recon import bank_recon_v2

    return bank_recon_v2._parse_gl_impl(
        req.file_bytes,
        req.filename,
        account_code=str(req.options.get("account_code", "")),
        api_key=req.api_key or "",
        tenant_id=req.tenant_id,
    )
