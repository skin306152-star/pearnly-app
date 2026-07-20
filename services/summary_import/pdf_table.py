# -*- coding: utf-8 -*-
"""PDF 汇总表适配器:带文字层的 PDF → parse_table 的同一份契约。

纯函数、无 DB/无网络。切表交给通用叶子 fileconv.pdf_grid 的三级降级链
(extract_tables → 坐标聚类 → 空白切分),本件只负责:定表头、标合计行、按 parse_table 的
字段名产出,让下游(工单 R2 聚合、录入工作台列映射)不分来源、不再各写一套解析。

两条诚实线,宁可返空也不返半真:
  · 无文字层(扫描件)→ 空表 + reason=no_text_layer,交 OCR 路或人工。绝不把 latin-1 兜底
    解出来的逐行垃圾当表格喂给聚合器——那正是 classify 把 PDF 字节直丢 parse_table 时踩到的
    坑(实测 121 行 status=ok,一路静默进销项)。
  · 三级链都切不出表,或切出来只有表头没有数据行 → 空表 + reason=unstructured_text_layer。
    列位对不齐的表比读不出更危险:错列是静默进 ภ.พ.30,读不出至少会停下来叫人。

level/degraded 原样透出:非 extract_tables 级说明列位是推断来的,上层要留痕、别当同等可靠。
"""

from __future__ import annotations

from typing import Any, Dict, List

from services.fileconv.pdf_grid import LEVEL_TABLE, extract_grid
from services.fileconv.tables import _is_total_line
from services.fileconv.text_layer import extract_pages, has_text_layer
from services.summary_import.dates import detect_period
from services.summary_import.parse import _MAX_ROWS, _locate_header, _looks_summary

REASON_NO_TEXT_LAYER = "no_text_layer"
REASON_UNSTRUCTURED = "unstructured_text_layer"
SOURCE = "pdf_text_layer"


def _empty(reason: str) -> Dict[str, Any]:
    return {
        "sheet_name": "",
        "headers": [],
        "rows": [],
        "row_count": 0,
        "truncated": False,
        "preamble": "",
        "suggested_period": None,
        "source": SOURCE,
        "level": None,
        "degraded": True,
        "reason": reason,
    }


def _text_pages(pdf_bytes: bytes) -> List[str] | None:
    """抽文字层(layout 保留横向位置,给三级链的空白切分兜底用)。判「有没有文字层」时
    先剥掉 layout 补的空格——不剥的话一页空白也能撑过字数密度闸。"""
    pages = extract_pages(pdf_bytes, layout=True)
    if pages is None:
        return None
    stripped = ["\n".join(ln.strip() for ln in p.split("\n") if ln.strip()) for p in pages]
    return pages if has_text_layer(stripped) else None


_HEAD_LINES = 3  # 抬头(报表名 + 期间)最多占的行数;再往下就是表体了


def _head_text(pages: List[str]) -> str:
    lines = [ln.strip() for ln in (pages[0] if pages else "").split("\n") if ln.strip()]
    return " ".join(lines[:_HEAD_LINES])


def parse_pdf_table(pdf_bytes: bytes, filename: str = "") -> Dict[str, Any]:
    """PDF 字节 → {sheet_name, headers, rows, row_count, truncated, preamble,
    suggested_period, source, level, degraded, reason}。

    rows 非空即代表这张表可信到能取数;否则 reason 说明为什么不可信。
    """
    pages = _text_pages(pdf_bytes or b"")
    if pages is None:
        return _empty(REASON_NO_TEXT_LAYER)

    grid = extract_grid(pdf_bytes, pages_text=pages)
    if grid is None:
        return _empty(REASON_UNSTRUCTURED)

    hidx = _locate_header(grid.rows)
    body = grid.rows[hidx + 1 :]
    if not body:
        return _empty(REASON_UNSTRUCTURED)

    rows: List[Dict[str, Any]] = []
    truncated = False
    for cells in body:
        if len(rows) >= _MAX_ROWS:
            truncated = True
            break
        is_summary = _looks_summary(cells) or _is_total_line(" ".join(cells))
        rows.append({"index": len(rows), "cells": list(cells), "is_summary": is_summary})

    # 表头之上的行是前言(标题/抬头),用于自动认年月。extract_tables 只返回表格内部,标题
    # 落在表外 → 网格里没有前言时回落取文字层首页的抬头几行,别把年月白丢了。
    preamble = " ".join(c for row in grid.rows[:hidx] for c in row if c.strip()) or _head_text(
        pages
    )
    period = detect_period(preamble)
    return {
        "sheet_name": filename or "",
        "headers": list(grid.rows[hidx]),
        "rows": rows,
        "row_count": len(rows),
        "truncated": truncated,
        "preamble": preamble,
        "suggested_period": list(period) if period else None,
        "source": SOURCE,
        "level": grid.level,
        "degraded": grid.level != LEVEL_TABLE,
        "reason": None,
    }
