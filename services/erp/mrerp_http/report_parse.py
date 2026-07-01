# -*- coding: utf-8 -*-
"""MR.ERP 主数据导入 report 解析(码 + หมายเหตุ 备注)。

主数据 report 是「码+备注」格式(客户码在 A / 商品码在 C · 备注在末列),与发票口径
(mrerp_report_parser)不通用,故独立小解析。空备注=成功。
"""

import io
import re
import zipfile
from typing import Dict, Optional

_SI_RE = re.compile(r"<si>.*?</si>", re.DOTALL)
_TAG_RE = re.compile(r"<[^>]+>")
_ROW_RE = re.compile(r'<row r="(\d+)"[^>]*>(.*?)</row>', re.DOTALL)
_CELL_RE = re.compile(r'<c r="([A-Z]+)\d+"([^>]*)>(?:<v>(.*?)</v>)?</c>')


def _col_idx(letter: str) -> int:
    n = 0
    for ch in letter:
        n = n * 26 + (ord(ch) - 64)
    return n


def parse_master_report(
    report_bytes: bytes, code_col: str = "A", note_col: Optional[str] = None
) -> Dict[str, str]:
    """report → {码: 备注}(空备注=成功)。code_col=码所在列(客户 A / 商品 C),
    note_col=备注列(None=取该行最右单元格)。"""
    out: Dict[str, str] = {}
    with zipfile.ZipFile(io.BytesIO(report_bytes)) as z:
        names = z.namelist()
        sheet = next((n for n in names if n.endswith("sheet1.xml")), None)
        if sheet is None:
            return out
        xml = z.read(sheet).decode("utf-8")
        sst = (
            z.read("xl/sharedStrings.xml").decode("utf-8")
            if "xl/sharedStrings.xml" in names
            else ""
        )
    strings = [_TAG_RE.sub("", s) for s in _SI_RE.findall(sst)]

    def _val(attrs: str, v: Optional[str]) -> str:
        if v is None:
            return ""
        return strings[int(v)] if 't="s"' in attrs else v

    for rm in _ROW_RE.finditer(xml):
        if rm.group(1) == "1":  # 表头
            continue
        cells = {c.group(1): _val(c.group(2), c.group(3)) for c in _CELL_RE.finditer(rm.group(2))}
        code = cells.get(code_col, "")
        if not code:
            continue
        col = note_col or (max(cells, key=_col_idx) if cells else None)
        out[code] = cells.get(col, "") if col else ""
    return out
