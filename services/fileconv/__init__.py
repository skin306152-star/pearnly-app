# -*- coding: utf-8 -*-
"""财务文件转换引擎(纯后端)。

带文字层的财务 PDF → 结构化表 → xlsx,自带守恒校验(余额链/借贷/合计闭合)。
无文字层 = 诚实拒绝 no_text_layer,不做 OCR(OCR 归 K1c)。K1b HTTP/UI 在此之上接。
"""

from services.fileconv.convert import convert_pages, convert_pdf
from services.fileconv.model import (
    ConvertResult,
    Issue,
    Table,
    GL_LEDGER,
    BANK_STATEMENT,
    VAT_REPORT,
    GENERIC_TABLE,
    STATUS_OK,
    STATUS_NO_TEXT_LAYER,
)
from services.fileconv.xlsx_out import build_xlsx

__all__ = [
    "convert_pdf",
    "convert_pages",
    "build_xlsx",
    "ConvertResult",
    "Issue",
    "Table",
    "GL_LEDGER",
    "BANK_STATEMENT",
    "VAT_REPORT",
    "GENERIC_TABLE",
    "STATUS_OK",
    "STATUS_NO_TEXT_LAYER",
]
