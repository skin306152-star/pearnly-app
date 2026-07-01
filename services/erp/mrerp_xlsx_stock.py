# -*- coding: utf-8 -*-
"""MR.ERP xlsx · 库存进出(impstktranrec 入库 / impstktraniss 出库)· 克隆官方模板生成。

Zihao 定:库存只做**建库存型商品 + 进出库数量**,不算成本/COGS。2-sheet:
  表头(单号/日期/分店/备注)+ 明细(商品码/仓/数量 · 入库另带单价/金额)。
入库 kind="receive"(明细 8 列 · 带价额)· 出库 kind="issue"(明细 6 列 · 仅数量)。
克隆策略同 purchase:字节模板只重写 sheetData+sharedStrings · 该模板样式 表头 s4/文本 s8/日期 s9/数值 s6。
"""

import io
import os
import re
import zipfile
from collections import OrderedDict
from typing import Any, Dict, List

from services.erp import mrerp_xlsx_generator as _gen
from services.erp.mrerp_xlsx_fmt import fmt_date, fmt_number
from services.erp.mrerp_xlsx_lookups import _build_product_lookup, _resolve_product_code
from services.erp.mrerp_xlsx_sales_credit import _format_num

_TEMPLATES = {
    "receive": "test_data_mrerp_sample_impstktranrec.xlsx",
    "issue": "test_data_mrerp_sample_impstktraniss.xlsx",
}

_S_HEADER = 4  # numFmt 49 文本
_S_TEXT = 8
_S_DATE = 9  # numFmt 187 日期(存文本)
_S_NUM = 6  # numFmt 4 数值

_HEADERS_1 = ["เลขที่", "วันที่", "สาขาบริษัท", "หมายเหตุ 1", "หมายเหตุ 2", "หมายเหตุ 3"]
_HEADERS_REC = ["เลขที่", "รหัสสินค้า", "แผนก", "งาน", "คลัง", "จำนวน", "ราคา/หน่วย", "จำนวนเงิน"]
_HEADERS_ISS = ["เลขที่", "รหัสสินค้า", "แผนก", "งาน", "คลัง", "จำนวน"]


def _col_letter(n: int) -> str:
    s = ""
    while n > 0:
        n, r = divmod(n - 1, 26)
        s = chr(65 + r) + s
    return s


def _xml_escape(s: str) -> str:
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _template_path(kind: str) -> str:
    name = _TEMPLATES[kind]
    here = os.path.dirname(os.path.abspath(__file__))
    root = os.path.dirname(os.path.dirname(here))
    for cand in (os.path.join(root, name), os.path.join(here, name)):
        if os.path.exists(cand):
            return cand
    raise FileNotFoundError(f"stock template missing: {name}")


def _detail_rows(history: Dict[str, Any], mappings: Dict[str, Any]) -> List[Dict[str, Any]]:
    """明细行:商品码经 lookup 解析,数量/单价/金额来自 items(无 items → 单行数量 1)。"""
    lookup = _build_product_lookup(mappings)
    items = history.get("items")
    if not isinstance(items, list):
        fields = history.get("fields")
        items = fields.get("items") if isinstance(fields, dict) else None
    rows: List[Dict[str, Any]] = []
    for it in items or []:
        if not isinstance(it, dict):
            continue
        name = str(it.get("name") or it.get("description") or "").strip()
        qty = fmt_number(it.get("qty") or it.get("quantity")) or 1
        price = fmt_number(it.get("unit_price") or it.get("price")) or 0
        amount = fmt_number(it.get("amount")) or round((qty or 0) * (price or 0), 2)
        rows.append(
            {
                "code": _resolve_product_code(name, lookup) or "",
                "qty": qty,
                "price": price,
                "amount": amount,
            }
        )
    if not rows:
        rows.append({"code": "", "qty": 1, "price": 0, "amount": 0})
    return rows


def validate_stock_history(history: Dict[str, Any], mappings: Dict[str, Any]):
    """库存 preflight(最小):日期 + 至少一条商品明细。返回 (ok, err_code, warnings)。"""
    if not history:
        return False, "ERR_NO_HISTORY", []
    if not history.get("invoice_date"):
        return False, "ERR_NO_INVOICE_DATE", []
    rows = _detail_rows(history, mappings)
    if not rows or all(not r.get("code") for r in rows):
        return False, "ERR_NO_STOCK_ITEM", []
    return True, None, []


def generate_xlsx_stock(
    histories: List[Dict[str, Any]], mappings: Dict[str, Any], kind: str = "receive"
) -> bytes:
    """克隆官方模板生成库存进出 xlsx。kind='receive'(入库·带价额)/'issue'(出库·仅数量)。"""
    with open(_template_path(kind), "rb") as f:
        template_bytes = f.read()
    files: Dict[str, bytes] = {}
    with zipfile.ZipFile(io.BytesIO(template_bytes), "r") as zf:
        for name in zf.namelist():
            files[name] = zf.read(name)

    shared: "OrderedDict[str, int]" = OrderedDict()

    def sidx(text: Any) -> int:
        text = "" if text is None else str(text)
        if text not in shared:
            shared[text] = len(shared)
        return shared[text]

    def _str_cell(col: int, row: int, val: Any, style: int) -> str:
        return f'<c r="{_col_letter(col)}{row}" s="{style}" t="s"><v>{sidx(val)}</v></c>'

    def _num_cell(col: int, row: int, val: Any) -> str:
        return f'<c r="{_col_letter(col)}{row}" s="{_S_NUM}"><v>{_format_num(val)}</v></c>'

    is_rec = kind == "receive"
    item_headers = _HEADERS_REC if is_rec else _HEADERS_ISS
    item_span = len(item_headers)

    def _header_row(headers: List[str]) -> str:
        cells = "".join(_str_cell(i, 1, h, _S_HEADER) for i, h in enumerate(headers, 1))
        return f'<row r="1" spans="1:{len(headers)}" x14ac:dyDescent="0.2">{cells}</row>'

    # ── Sheet1 header ──────────────────────────────────────────────
    rows1 = [_header_row(_HEADERS_1)]
    for ridx, history in enumerate(histories, start=2):
        inv = _gen.derive_mrerp_invoice_no(history)
        date = fmt_date(history.get("invoice_date")) or ""
        cells = [
            _str_cell(1, ridx, inv, _S_TEXT),
            _str_cell(2, ridx, date, _S_DATE),
            _str_cell(3, ridx, "00000", _S_TEXT),
        ]
        rows1.append(f'<row r="{ridx}" spans="1:6" x14ac:dyDescent="0.2">{"".join(cells)}</row>')
    _replace_sheet(files, "xl/worksheets/sheet1.xml", rows1, f"A1:F{1 + len(histories)}")

    # ── Sheet2 items ───────────────────────────────────────────────
    rows2 = [_header_row(item_headers)]
    cur = 2
    for history in histories:
        inv = _gen.derive_mrerp_invoice_no(history)
        for d in _detail_rows(history, mappings):
            cells = [
                _str_cell(1, cur, inv, _S_TEXT),
                _str_cell(2, cur, d["code"], _S_TEXT),
                _str_cell(3, cur, "BOI1", _S_TEXT),
                _str_cell(4, cur, "00002", _S_TEXT),
                _str_cell(5, cur, "0000", _S_TEXT),
                _num_cell(6, cur, d["qty"]),
            ]
            if is_rec:
                cells.append(_num_cell(7, cur, d["price"]))
                cells.append(_num_cell(8, cur, d["amount"]))
            rows2.append(
                f'<row r="{cur}" spans="1:{item_span}" x14ac:dyDescent="0.2">{"".join(cells)}</row>'
            )
            cur += 1
    _replace_sheet(
        files, "xl/worksheets/sheet2.xml", rows2, f"A1:{_col_letter(item_span)}{max(cur - 1, 1)}"
    )

    parts = [
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\r\n',
        f'<sst xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
        f'count="{len(shared)}" uniqueCount="{len(shared)}">',
    ]
    for text in shared:
        parts.append(f'<si><t xml:space="preserve">{_xml_escape(text)}</t></si>')
    parts.append("</sst>")
    files["xl/sharedStrings.xml"] = "".join(parts).encode("utf-8")

    out = io.BytesIO()
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zf:
        for name, data in files.items():
            zf.writestr(name, data)
    return out.getvalue()


def _replace_sheet(files: Dict[str, bytes], name: str, rows_xml: List[str], dim: str) -> None:
    xml = files[name].decode("utf-8")
    xml = re.sub(
        r"<sheetData>.*?</sheetData>",
        "<sheetData>" + "".join(rows_xml) + "</sheetData>",
        xml,
        flags=re.DOTALL,
    )
    xml = re.sub(r'<dimension ref="[^"]+"', f'<dimension ref="{dim}"', xml)
    files[name] = xml.encode("utf-8")
