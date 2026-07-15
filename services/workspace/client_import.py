# -*- coding: utf-8 -*-
"""IN-0d · 客户名录 Excel 批量导入:表头自动识别 + 行提取(纯函数,零 DB 依赖)。

复用 summary_import 的通用表格解析(services.summary_import.parse.parse_table ·
xlsx/csv 双引擎 + 编码兜底 + 前言/表头行定位,同一套"先例"不重造表格 I/O),本模块只加
客户名录专属的表头列同义词匹配(name/tax_id/branch/phone/address)+ 逐行抽取。

行级校验分两层:结构性(缺 name / 税号格式错,本模块 structural_error,零 DB)交给
本模块;需要 DB/租户上下文的判定(税号查重/M1 泰文名闸/pos_only 一号一店)留给路由层
(routes/client_import_routes.py)调用 routes.workspace_routes 的共享校验体
——不在此重复第二套实现。
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from services.purchase.field_clean import clean_tax_id
from services.summary_import.parse import parse_table

MAX_BYTES = 8 * 1024 * 1024  # 与 summary_import 上限口径一致
MAX_ROWS = 500  # 事务所客户名录常见 50-93 家,留足余量;超限判异常输入,不吞内存

# 表头同义词(泰/英/中)。_match_column 用子串匹配,顺序不影响命中(dict 遍历
# 找到第一个"字段尚未匹配过的列"即停)。
_HEADER_SYNONYMS: Dict[str, List[str]] = {
    "name": [
        "client name",
        "company name",
        "customer name",
        "name",
        "ชื่อลูกค้า",
        "ชื่อบริษัท",
        "ชื่อกิจการ",
        "ชื่อ",
        "客户名称",
        "客户名",
        "公司名称",
        "公司名",
        "名称",
    ],
    "tax_id": [
        "tax id",
        "tax_id",
        "taxid",
        "vat id",
        "vat no",
        "เลขประจำตัวผู้เสียภาษี",
        "เลขที่ผู้เสียภาษี",
        "เลขผู้เสียภาษี",
        "税务登记号",
        "纳税人识别号",
        "税号",
    ],
    "branch": ["branch no", "branch", "สาขา", "分公司", "分支机构"],
    "phone": [
        "telephone",
        "phone",
        "tel",
        "mobile",
        "โทรศัพท์",
        "เบอร์โทรศัพท์",
        "เบอร์โทร",
        "联系电话",
        "电话",
        "手机",
    ],
    "address": ["address", "ที่อยู่", "地址"],
}

ERR_MISSING_NAME = "client_import.err_missing_name"
ERR_BAD_TAX_ID = "client_import.err_bad_tax_id"


def _match_column(header_cell: str) -> Optional[str]:
    """单个表头格 → 归一字段名(name/tax_id/branch/phone/address)。都不命中 → None。"""
    h = (header_cell or "").strip().lower()
    if not h:
        return None
    for field, synonyms in _HEADER_SYNONYMS.items():
        for syn in synonyms:
            if syn in h:
                return field
    return None


def _match_headers(headers: List[str]) -> Dict[str, int]:
    """表头行 → {字段名: 列下标}。同一字段多列命中取靠前那列(先出现的更可能是主列)。"""
    matched: Dict[str, int] = {}
    for idx, cell in enumerate(headers):
        field = _match_column(cell)
        if field and field not in matched:
            matched[field] = idx
    return matched


def _cell_at(cells: List[str], idx: Optional[int]) -> str:
    if idx is None or idx >= len(cells):
        return ""
    return str(cells[idx] or "").strip()


def parse_client_rows(file_bytes: bytes, filename: str = "") -> Dict[str, Any]:
    """上传文件 → {headers, matched, rows, row_count, truncated, name_column_found}。

    name 列猜不中 → name_column_found=False(前端诚实报"认不出表头",不瞎猜硬导);
    其余列(tax_id/branch/phone/address)缺失时整批留空,不算失败(可选字段)。
    """
    parsed = parse_table(file_bytes, filename)
    headers = parsed.get("headers") or []
    empty: Dict[str, Any] = {
        "headers": headers,
        "matched": {},
        "rows": [],
        "row_count": 0,
        "truncated": False,
        "name_column_found": False,
    }
    if not headers:
        return empty
    matched = _match_headers(headers)
    if "name" not in matched:
        return {**empty, "matched": matched}

    raw_rows = [r for r in (parsed.get("rows") or []) if not r.get("is_summary")]
    truncated = bool(parsed.get("truncated")) or len(raw_rows) > MAX_ROWS
    rows: List[Dict[str, Any]] = []
    for r in raw_rows[:MAX_ROWS]:
        cells = r.get("cells") or []
        rows.append(
            {
                "row_index": r.get("index", len(rows)),
                "name": _cell_at(cells, matched.get("name")),
                "tax_id": _cell_at(cells, matched.get("tax_id")),
                "branch": _cell_at(cells, matched.get("branch")),
                "phone": _cell_at(cells, matched.get("phone")),
                "address": _cell_at(cells, matched.get("address")),
            }
        )
    return {
        "headers": headers,
        "matched": matched,
        "rows": rows,
        "row_count": len(rows),
        "truncated": truncated,
        "name_column_found": True,
    }


def structural_error(name: str, tax_id: str) -> Optional[str]:
    """行级最基础的结构校验(建档前先过一遍,少打一次共享校验体往返)。

    缺 name → ERR_MISSING_NAME;税号给了但不是合法泰国 13 位税号 → ERR_BAD_TAX_ID
    (税号本可选,空值不算错;格式错的留给用户回表里改,不当空值默默吞掉)。
    """
    if not (name or "").strip():
        return ERR_MISSING_NAME
    if (tax_id or "").strip() and not clean_tax_id(tax_id):
        return ERR_BAD_TAX_ID
    return None
