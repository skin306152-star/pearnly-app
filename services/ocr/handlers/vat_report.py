# -*- coding: utf-8 -*-
"""vat_report:销项 VAT 报表 → Excel 直读 / PDF 文字层+regex 优先,
扫描件/图片才走 Gemini(分页防超 token)。"""

from __future__ import annotations

from services.ocr.contracts import OcrRequest


def handle(req: OcrRequest):
    from services.vat import vat_report_parser

    return vat_report_parser._parse_vat_report_impl(
        req.file_bytes, req.filename, api_key=req.api_key
    )
