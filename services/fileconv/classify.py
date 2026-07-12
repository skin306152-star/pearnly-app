# -*- coding: utf-8 -*-
"""doc_type 识别。基于文字层里的模板标记词判定,识别不了一律 generic_table。

顺序有讲究:GL 台账标记词最专属,先判;其次银行流水(含跑余额);再次税报表;
都不命中落 generic。宁可 generic 也不误判成带守恒校验的强类型。
"""

from services.fileconv.model import (
    GL_LEDGER,
    BANK_STATEMENT,
    VAT_REPORT,
    GENERIC_TABLE,
)

# 泰文 GL 台账(รายงานสมุดแยกประเภท)专属标记。
_GL_MARKERS = ("สมุดแยกประเภท", "แยกประเภท", "รหัสบัญชี")
_GL_COLUMN_MARKERS = ("เดบิต", "เครดิต", "ยอดคงเหลือ")

# 银行/跑余额流水标记(泰/英)。
_BANK_MARKERS = (
    "balance forward",
    "ยอดยกมา",
    "รายการเดินบัญชี",
    "statement of account",
    "bank statement",
)

# 增值税报表(ภ.พ.30 / 进销项)标记。
_VAT_MARKERS = (
    "ภ.พ.30",
    "ภพ.30",
    "ภาษีซื้อ",
    "ภาษีขาย",
    "รายงานภาษีมูลค่าเพิ่ม",
)


def _contains_any(haystack: str, needles) -> bool:
    return any(n in haystack for n in needles)


def classify(full_text: str) -> str:
    lower = full_text.lower()

    if _contains_any(full_text, _GL_MARKERS):
        return GL_LEDGER
    # 三栏借贷余额齐全 = 台账特征(即便标题词缺失)。
    if sum(1 for m in _GL_COLUMN_MARKERS if m in full_text) >= 2:
        return GL_LEDGER

    if _contains_any(lower, _BANK_MARKERS) or _contains_any(full_text, _BANK_MARKERS):
        return BANK_STATEMENT
    # 英文流水三件套 + 跑余额。
    if all(k in lower for k in ("date", "description")) and "balance" in lower:
        return BANK_STATEMENT

    if _contains_any(full_text, _VAT_MARKERS):
        return VAT_REPORT

    return GENERIC_TABLE
