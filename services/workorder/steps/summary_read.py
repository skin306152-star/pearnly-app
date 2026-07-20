# -*- coding: utf-8 -*-
"""销项汇总表直读:落盘路径 → parse_table 契约(classify 的 _read_sales_summary 真实现)。

按扩展名分流再解析,别一律丢给 parse_table:PDF 字节喂进去不会抛,会被 CSV 引擎的 latin-1
兜底解成逐行垃圾(实测 121 行、status=ok),错数一路静默进 R2 销项。PDF 走文字层 + 三级切表
链(services/summary_import/pdf_table),扫描件诚实降级带 reason,交调用方判 flagged。
"""

from __future__ import annotations

from pathlib import Path

from services.summary_import.parse import parse_table
from services.summary_import.pdf_table import parse_pdf_table
from services.workorder import storage


def read(path: str) -> dict:
    """取盘 + 直读(纯函数,零 OCR 成本)。落盘密文由 storage 解回明文(双轨读)。"""
    data = storage.read_bytes(path)
    name = Path(path).name
    if name.lower().endswith(".pdf"):
        return parse_pdf_table(data, filename=name)
    return parse_table(data, filename=name)
