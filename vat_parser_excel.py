# -*- coding: utf-8 -*-
"""VAT 报告解析 · Excel(.xlsx/.xls)路径(零成本 openpyxl 表头识别)。"""

import io
import logging
from typing import List, Dict, Any

from vat_parser_common import (
    _to_float,
    PARSER_VERSION,
    _SKIP_H,
    _map_columns,
    _build_row,
)

logger = logging.getLogger(__name__)


# ======================================================================
# 1. Excel 解析(零成本)
# ======================================================================


def parse_excel(file_bytes: bytes) -> Dict[str, Any]:
    try:
        import openpyxl
    except ImportError:
        return {"ok": False, "error": "openpyxl 未安装", "rows": []}

    rows: List[Dict] = []
    meta: Dict[str, Any] = {}
    try:
        wb = openpyxl.load_workbook(io.BytesIO(file_bytes), data_only=True)
        ws = wb.active

        header_idx = None
        for i, row in enumerate(ws.iter_rows(min_row=1, max_row=30, values_only=True), 1):
            text = " ".join(str(c or "").lower() for c in row)
            if "เลขที่" in text or "invoice no" in text or "วันที่" in text:
                header_idx = i
                break
        if header_idx is None:
            return {"ok": False, "error": "找不到表头行", "rows": []}

        headers = tuple(str(c.value or "") for c in ws[header_idx])
        col_map = _map_columns(headers)

        row_no = 0
        for raw in ws.iter_rows(min_row=header_idx + 1, values_only=True):
            cells = list(raw)
            if not any(c for c in cells if c not in (None, "")):
                continue
            first = str(cells[0] or "").strip().lower()
            if any(k in first for k in _SKIP_H):
                if "amount_pre_vat" in col_map:
                    meta["total_amount_pre_vat"] = _to_float(cells[col_map["amount_pre_vat"]])
                if "vat_amount" in col_map:
                    meta["total_vat"] = _to_float(cells[col_map["vat_amount"]])
                continue
            row_no += 1
            rows.append(_build_row(row_no, cells, col_map))

        return {
            "ok": True,
            "rows": rows,
            "meta": meta,
            "warnings": [],
            "parser_version": PARSER_VERSION,
            "row_count": len(rows),
            "method": "excel",
        }
    except Exception as e:
        logger.error(f"parse_excel failed: {e}")
        return {"ok": False, "error": str(e), "rows": []}
