# -*- coding: utf-8 -*-
"""CSV 公式注入防护:中和以 = + @ 及 tab/回车 开头的单元格,防导出被表格软件当公式执行。

安全评估 2026-07-07:多处 CSV 导出把用户可控文本(用户名/客户名/UA/details)原样入格,
受害者用 Excel/LibreOffice 打开时 `=cmd|...` / `=HYPERLINK(...)` 可执行(OWASP CSV Injection)。
行级包裹 safe_row 给危险前缀补一个单引号,不改导出结构、不误伤负数金额(-数字 放行)。
"""

from __future__ import annotations

import re
from typing import Iterable

# 危险前缀(表格软件公式触发符);纯数字单元格(含正负金额)放行,免误伤——
# 但仅"整格就是一个数"才算数,`-1+cmd|...` 这类伪装成负数的公式不放行。
_DANGEROUS_HEAD = ("=", "+", "-", "@", "\t", "\r")
_PURE_NUMBER = re.compile(r"^[+-]?[\d,]+(\.\d+)?$")


def _cell(value: object) -> object:
    if not isinstance(value, str) or not value:
        return value
    if value[0] in _DANGEROUS_HEAD and not _PURE_NUMBER.match(value):
        return "'" + value
    return value


def safe_row(row: Iterable) -> list:
    """把一行的每个单元格过一遍公式中和,返回可直接交给 csv.writer.writerow 的 list。"""
    return [_cell(c) for c in row]


class SafeCsvWriter:
    """包住 csv.writer:每行落盘前经 safe_row 中和。接口与 csv.writer 一致,改构造处即全表受保护。"""

    def __init__(self, inner):
        self._inner = inner

    def writerow(self, row):
        return self._inner.writerow(safe_row(row))

    def writerows(self, rows):
        return self._inner.writerows(safe_row(r) for r in rows)
