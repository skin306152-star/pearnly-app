# -*- coding: utf-8 -*-
"""
services/recon/bank_table_io.py · Pearnly

Low-level table/PDF I/O shared by the bank-statement and GL parsers: workbook
and CSV loaders, header-keyword matching, summary-row detection, and crash-safe
PDF text extraction. Leaf module — no recon-domain dependencies.
"""

import io
import re
from typing import List

# v118.35.0.60 · 汇总/合计行关键词 · 这类行不是交易 · 解析时跳过(防被当成交易行误标)
# 真实案例:AM 1-69 的 "จำนวนเงินฝาก/Total Credit"、"Total Deposit" 被当成交易 · 余额对不上
_SUMMARY_ROW_KW = (
    "total credit",
    "total debit",
    "total deposit",
    "total withdrawal",
    "total transaction",
    "grand total",
    "subtotal",
    "sub total",
    "รวมรายการ",
    "ยอดรวม",
    "รวมยอด",
    "รวมเงิน",
    "总计",
    "合计",
    "小计",
    "本期合计",
    "累计",
)


def _is_summary_row(desc: str) -> bool:
    """识别底部汇总/合计行(Total/รวมรายการ/合计 等)· 这类不是交易 · 应跳过。"""
    d = (desc or "").strip().lower()
    if not d:
        return False
    return any(kw in d for kw in _SUMMARY_ROW_KW)


def _hit(header: str, hints: set) -> bool:
    # v118.35.0.55 · 短 ASCII 词(in/out/cr/dr)必须整词匹配 · 防 'in' 误命中 'Init Br.'
    # (KTB 真实 bug:分行号列 'Init Br.' 被当成存款列)· 长词 / 泰文仍用子串
    h = str(header or "").strip().lower()
    if not h:
        return False
    tokens = None
    for hint in hints:
        hl = hint.lower()
        if hl.isascii() and len(hl) <= 3:
            if tokens is None:
                tokens = set(re.split(r"[\s/().,_\-]+", h))
            if hl in tokens:
                return True
        elif hl in h:
            return True
    return False


def _load_excel_all_sheets(file_bytes: bytes):
    """v118.35.0.55 · 读出所有 sheet · 返回 [(sheet_name, [row_list,...]),...]
    先 openpyxl(.xlsx)· 退 xlrd(旧 .xls)· 都失败返 []"""
    try:
        import openpyxl

        wb = openpyxl.load_workbook(io.BytesIO(file_bytes), data_only=True, read_only=True)
        out = [
            (ws.title, [list(r) for r in ws.iter_rows(values_only=True)]) for ws in wb.worksheets
        ]
        try:
            wb.close()
        except Exception:
            pass
        return out
    except Exception:
        pass
    try:
        import xlrd

        wb = xlrd.open_workbook(file_contents=file_bytes)
        out = []
        for i in range(wb.nsheets):
            ws = wb.sheet_by_index(i)
            out.append((ws.name, [ws.row_values(r) for r in range(ws.nrows)]))
        return out
    except Exception:
        return []


def _load_csv_sheets(file_bytes: bytes):
    """ADR-006 S6a · CSV/TSV → [("csv", rows)]。处理编码(UTF-8 BOM/泰 cp874/中 gbk)+ 分隔符嗅探。

    返回 [] 表示读不了。数字里的千分位逗号靠 csv 引号字段处理(正规 CSV 会给 "10,620.53" 加引号)。
    """
    import csv as _csv
    import io as _io

    text = None
    for enc in ("utf-8-sig", "utf-8", "cp874", "gbk", "latin-1"):
        try:
            text = file_bytes.decode(enc)
            break
        except Exception:
            continue
    if text is None:
        return []
    # 分隔符嗅探(逗号/分号/制表/竖线)· 失败退回逗号
    sample = text[:4096]
    delim = ","
    try:
        delim = _csv.Sniffer().sniff(sample, delimiters=",;\t|").delimiter
    except Exception:
        for d in (";", "\t", "|"):
            if sample.count(d) > sample.count(","):
                delim = d
                break
    try:
        rows = [row for row in _csv.reader(_io.StringIO(text), delimiter=delim)]
        return [("csv", rows)] if rows else []
    except Exception:
        return []


def _pdf_extract_text_safe(file_bytes: bytes) -> List[str]:
    """
    Extract text from PDF without crashing on malformed metadata.
    Tries pdfminer first (no KeyError('date') bug), then pdfplumber, then pypdf.
    Returns list of page text strings.
    """
    # pdfminer is a dependency of pdfplumber and doesn't have the KeyError('date') bug
    try:
        from pdfminer.high_level import extract_text as _pm_extract

        text = _pm_extract(io.BytesIO(file_bytes)) or ""
        if text.strip():
            return [text]
    except Exception:
        pass  # pdfminer 失败 · 走 pypdf 兜底
    # pypdf fallback
    try:
        import pypdf

        reader = pypdf.PdfReader(io.BytesIO(file_bytes))
        return [pg.extract_text() or "" for pg in reader.pages]
    except Exception:
        pass  # pypdf 也失败 · 返回空列表 · 调用方走 Gemini 视觉兜底
    return []
