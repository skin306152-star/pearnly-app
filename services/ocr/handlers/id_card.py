# -*- coding: utf-8 -*-
"""id_card:泰国身份证图 → Gemini 多模态直读(无免费路径,首读 flash_lite 档,
读不出合规 13 位号升级兜底档;两档皆败抛 IdCardExtractError)。"""

from __future__ import annotations

from services.ocr.contracts import OcrRequest


def handle(req: OcrRequest):
    from services.ocr import id_card_extract

    return id_card_extract._extract_id_card_impl(req.file_bytes, req.api_key)
