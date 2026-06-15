# -*- coding: utf-8 -*-
"""OCR document_type 原始码 → 4 语人话(数据卡/详情避免显 simplified_tax_invoice 等英文代号)。

术语对齐网页 pur-dt-*。空 → 空;未知码 → 原值兜底(不编造)。从 line_card 抽出保 <500。
"""

from __future__ import annotations

_DOC_TYPE_LABELS = {
    "tax_invoice": {"zh": "税务发票", "th": "ใบกำกับภาษี", "en": "Tax invoice", "ja": "税額票"},
    "simplified_tax_invoice": {
        "zh": "简式税票",
        "th": "ใบกำกับภาษีอย่างย่อ",
        "en": "Simplified tax invoice",
        "ja": "簡易税額票",
    },
    "receipt": {"zh": "收据", "th": "ใบเสร็จรับเงิน", "en": "Receipt", "ja": "領収書"},
    "credit_note": {
        "zh": "贷项通知单",
        "th": "ใบลดหนี้",
        "en": "Credit note",
        "ja": "クレジットノート",
    },
    "other": {"zh": "其他", "th": "อื่น ๆ", "en": "Other", "ja": "その他"},
}


def doc_type_label(code: str, lang: str) -> str:
    """document_type 原始码 → 当前语言人话。"""
    code = (code or "").strip()
    if not code:
        return ""
    m = _DOC_TYPE_LABELS.get(code)
    if not m:
        return code
    return m.get((lang or "zh").lower()) or m["en"]
