# -*- coding: utf-8 -*-
"""gl_ledger:GL 总账 → Excel/CSV 结构直读优先,PDF 走 pipeline,
读不出再退 bank_gl_pdf 的 pdfplumber/Gemini 链。"""

from __future__ import annotations

from services.ocr.contracts import OcrRequest


def handle(req: OcrRequest):
    if req.options.get("flavor") == "gl_vat":
        from services.recon import gl_vat_parse_excel

        return gl_vat_parse_excel._parse_gl_impl(
            req.file_bytes,
            req.filename,
            revenue_prefix=str(req.options.get("revenue_prefix") or "4"),
        )

    from services.recon import bank_recon_v2

    return bank_recon_v2._parse_gl_impl(
        req.file_bytes,
        req.filename,
        account_code=str(req.options.get("account_code", "")),
        api_key=req.api_key or "",
        tenant_id=req.tenant_id,
    )
