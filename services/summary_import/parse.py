# -*- coding: utf-8 -*-
"""汇总表解析:xlsx/csv 二进制 → {sheet_name, headers, rows}。

不重造表格 I/O:openpyxl/xlrd 双引擎 + CSV 多编码兜底复用 recon 的通用 leaf 工具
(services/recon/bank_table_io · 文件头自述"无 recon 域依赖")。本模块只负责把第一张有内容的
sheet 规整成「表头行 + 数据行」,并标注底部合计行(รวม/total),让前端预先取消勾选。
"""

from __future__ import annotations

from typing import Any, Dict, List

from services.recon.bank_table_io import (
    _is_summary_row,
    _load_csv_sheets,
    _load_excel_all_sheets,
)
from services.summary_import.dates import detect_period

_MAX_ROWS = 2000  # 单批上限:再多是异常输入(月度汇总远小于此),防前端/内存被撑爆
_HEADER_SCAN = 15  # 表头最多藏在前 N 行之下(标题/公司抬头/说明等前言行)

# 汇总表底部合计行:除 recon 关键词外,补「整格恰为总计词」的常见短写(recon 列表按子串匹配,
# 漏了裸「รวม」「合计」这类单格总计行)。不改 recon 共享列表(它服务银行对账,语义不同)。
_TOTAL_CELL = frozenset({"รวม", "รวมทั้งสิ้น", "total", "sum", "合计", "总计", "小计"})


def _looks_summary(cells: List[str]) -> bool:
    """任一格命中 recon 汇总关键词,或整格恰为总计短词 → 合计行。"""
    for c in cells:
        if _is_summary_row(c) or c.strip().lower() in _TOTAL_CELL:
            return True
    return False


def _is_num(s: str) -> bool:
    try:
        float(s.replace(",", "").strip())
        return True
    except (ValueError, AttributeError):
        return False


def _looks_header(cells: List[str]) -> bool:
    """像表头行:≥3 个非空格、且多数为文字(非数字)。用于跳过标题/前言行,定位真表头。"""
    nonempty = [c for c in cells if c.strip()]
    if len(nonempty) < 3:
        return False
    numeric = sum(1 for c in nonempty if _is_num(c))
    return numeric * 2 <= len(nonempty)  # 多数非数字 → 表头;多数数字 → 数据行


def _cell(v: Any) -> str:
    """单元格 → 展示字符串。None/空 → ''; 去首尾空白。数值原样(openpyxl 已给 python 数字)。"""
    if v is None:
        return ""
    return str(v).strip()


def _row_is_empty(row: List[Any]) -> bool:
    return all(_cell(c) == "" for c in row)


def _sheets(file_bytes: bytes, filename: str) -> List[tuple]:
    """按扩展名先试对应引擎,失败交叉兜底(.xlsx 内容进 csv 引擎会得乱码 → 先 excel)。"""
    name = (filename or "").lower()
    if name.endswith(".csv") or name.endswith(".tsv") or name.endswith(".txt"):
        return _load_csv_sheets(file_bytes) or _load_excel_all_sheets(file_bytes)
    return _load_excel_all_sheets(file_bytes) or _load_csv_sheets(file_bytes)


def _pick_sheet(sheets: List[tuple]) -> tuple:
    """选第一张有数据行的 sheet(空 sheet 常见于导出文件尾)。都空 → 第一张。"""
    for name, rows in sheets:
        if any(not _row_is_empty(r) for r in rows):
            return name, rows
    return sheets[0]


def _locate_header(nonempty: List[List[str]]) -> int:
    """真表头行下标(在前 _HEADER_SCAN 行里找"像表头"的);找不到 → 0(退回第一行,兼容干净表)。"""
    for i, cells in enumerate(nonempty[:_HEADER_SCAN]):
        if _looks_header(cells):
            return i
    return 0


def parse_table(file_bytes: bytes, filename: str = "") -> Dict[str, Any]:
    """解析汇总表。返回 {sheet_name, headers, rows, row_count, truncated, preamble, suggested_period}。

    先跳过标题/前言行定位真表头(真实泰国汇总表常有「สรุปยอดขาย...เดือน...」标题行),表头之上
    的前言文字用于自动认年月(日期列只写日号时按此拼完整日期)。rows = 表头之后每条数据行的
    {index, cells, is_summary};is_summary 标注底部合计行。解析不出 → headers/rows 空。
    """
    empty = {
        "sheet_name": "",
        "headers": [],
        "rows": [],
        "row_count": 0,
        "truncated": False,
        "preamble": "",
        "suggested_period": None,
    }
    sheets = _sheets(file_bytes or b"", filename)
    if not sheets:
        return empty

    sheet_name, raw_rows = _pick_sheet(sheets)
    nonempty = [[_cell(c) for c in r] for r in raw_rows if not _row_is_empty(r)]
    if not nonempty:
        return {**empty, "sheet_name": sheet_name}

    hidx = _locate_header(nonempty)
    preamble = " ".join(c for row in nonempty[:hidx] for c in row if c.strip())
    header = nonempty[hidx]

    data: List[Dict[str, Any]] = []
    truncated = False
    for cells in nonempty[hidx + 1 :]:
        if len(data) >= _MAX_ROWS:
            truncated = True
            break
        data.append({"index": len(data), "cells": cells, "is_summary": _looks_summary(cells)})

    period = detect_period(preamble)
    return {
        "sheet_name": sheet_name,
        "headers": header,
        "rows": data,
        "row_count": len(data),
        "truncated": truncated,
        "preamble": preamble,
        "suggested_period": list(period) if period else None,
    }
