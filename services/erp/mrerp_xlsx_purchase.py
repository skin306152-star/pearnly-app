# -*- coding: utf-8 -*-
"""MR.ERP xlsx · purchase(ซื้อสินค้า · impaptran/selmenu=67)· 克隆官方 example.xlsx 生成。

采购 = 3-sheet:表头(供应商/供应商票号/税率)+ 明细(商品/量/单价/金额)+ 尾(押金/收货 · 留空)。
账套主体=买方;供应商(ผู้จำหน่าย)=采购票卖方 → 码经 mappings['suppliers'] 解析,无则回退卖方税号
(与自建供应商码同口径 · 幂等)。克隆策略同 sales_cash(known-facts §6.3):字节模板只重写
<sheetData>+sharedStrings,保留 styles。该模板 cellXfs:表头 s13/文本 s7/日期 s14/数值 s9。
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
from services.purchase.field_clean import clean_tax_id

_TEMPLATE_NAME = "test_data_mrerp_sample_purchase.xlsx"

_S_HEADER = 13  # numFmt 49 文本(表头)
_S_TEXT = 7  # numFmt 49 文本数据
_S_DATE = 14  # numFmt 187 日期(存文本)
_S_NUM = 9  # numFmt 4 数值

_HEADERS_1 = [
    "เลขที่",
    "วันที่",
    "อัตราภาษี",
    "สาขา",
    "แผนก",
    "งาน",
    "พนักงาน",
    "กำหนดส่งสินค้า",
    "รหัสผู้จำหน่าย",
    "รหัสผู้จำหน่าย (บิล)",
    "เลขที่บิล",
    "วันที่",
    "หักส่วนลด",
    "หมายเหตุ 1",
    "หมายเหตุ 2",
    "หมายเหตุ 3",
]
_HEADERS_2 = ["เลขที่", "รหัสสินค้า", "แผนก", "งาน", "คลัง", "จำนวน", "ราคา/หน่วย", "จำนวนเงิน"]
_HEADERS_3 = ["เลขที่", "เลขที่เงินมัดจำ", "ออกใบรับสินค้า"]

_NUM_COLS_1 = {13}  # 折扣
_DATE_COLS_1 = {2, 8, 12}


def _col_letter(n: int) -> str:
    s = ""
    while n > 0:
        n, r = divmod(n - 1, 26)
        s = chr(65 + r) + s
    return s


def _xml_escape(s: str) -> str:
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _template_path() -> str:
    here = os.path.dirname(os.path.abspath(__file__))
    root = os.path.dirname(os.path.dirname(here))
    for cand in (os.path.join(root, _TEMPLATE_NAME), os.path.join(here, _TEMPLATE_NAME)):
        if os.path.exists(cand):
            return cand
    raise FileNotFoundError(f"purchase template missing: {_TEMPLATE_NAME}")


def _supplier_code(history: Dict[str, Any], mappings: Dict[str, Any]) -> str:
    """供应商码:mappings['suppliers'] 命中(按 client_id / 卖方税号)优先,无则回退卖方税号。"""
    fields = history.get("fields") if isinstance(history.get("fields"), dict) else {}
    seller_tax = clean_tax_id(fields.get("seller_tax") or fields.get("seller_tax_id"))
    cid = str(history.get("client_id") or "")
    for row in (mappings or {}).get("suppliers") or []:
        if not isinstance(row, dict):
            continue
        code = str(row.get("erp_code") or "").strip()
        if not code:
            continue
        if seller_tax and clean_tax_id(row.get("seller_tax") or row.get("tax_id")) == seller_tax:
            return code
        if cid and str(row.get("client_id") or "") == cid:
            return code
    return seller_tax or (("V" + cid) if cid else "")


def _detail_rows(history: Dict[str, Any], mappings: Dict[str, Any]) -> List[Dict[str, Any]]:
    """明细行:商品码经 lookup 解析,量/单价/金额来自 items(无 items → 单行按总额兜底)。"""
    lookup = _build_product_lookup(mappings)
    items = history.get("items")
    if not isinstance(items, list):
        items = (
            (history.get("fields") or {}).get("items")
            if isinstance(history.get("fields"), dict)
            else None
        )
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
        sub = fmt_number(history.get("subtotal") or history.get("amount_before_tax"))
        sub = sub if sub is not None else (fmt_number(history.get("total_amount")) or 0)
        rows.append({"code": "", "qty": 1, "price": sub, "amount": sub})
    return rows


def validate_purchase_history(history: Dict[str, Any], mappings: Dict[str, Any]):
    """采购 preflight(最小 · 非 sales_credit 口径):日期 + 正金额 + 供应商码可解析。
    返回 (ok, err_code, warnings)。供应商缺失由 provision_suppliers 前置补,故这里只兜底。"""
    if not history:
        return False, "ERR_NO_HISTORY", []
    if not history.get("invoice_date"):
        return False, "ERR_NO_INVOICE_DATE", []
    total = fmt_number(history.get("total_amount"))
    if total is None:
        sub = fmt_number(history.get("subtotal")) or 0
        total = sub + (fmt_number(history.get("vat")) or 0)
    if not total or total <= 0:
        return False, "ERR_NO_TOTAL_AMOUNT", []
    if not _supplier_code(history, mappings):
        return False, "ERR_NO_SUPPLIER", []
    return True, None, []


def generate_xlsx_purchase(histories: List[Dict[str, Any]], mappings: Dict[str, Any]) -> bytes:
    """克隆官方模板生成 purchase xlsx(AP + 采购明细 · 押金/收货页留空)。"""
    with open(_template_path(), "rb") as f:
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

    def _header_row(headers: List[str], span: int) -> str:
        cells = "".join(_str_cell(i, 1, h, _S_HEADER) for i, h in enumerate(headers, 1))
        return f'<row r="1" spans="1:{span}" x14ac:dyDescent="0.2">{cells}</row>'

    # ── Sheet1 header ──────────────────────────────────────────────
    rows1 = [_header_row(_HEADERS_1, 16)]
    for ridx, history in enumerate(histories, start=2):
        inv = _gen.derive_mrerp_invoice_no(history)
        date = fmt_date(history.get("invoice_date")) or ""
        supplier = _supplier_code(history, mappings)
        bill_no = str(history.get("invoice_number") or history.get("invoice_no") or inv)[:20]
        col_vals = {
            1: inv,
            2: date,
            3: "7 (แยก)",
            4: "00000",
            5: "BOI1",
            6: "00002",
            7: "กร ทดสอบ",
            8: date,
            9: supplier,
            10: supplier,
            11: bill_no,
            12: date,
            13: 0,
        }
        cells = []
        for col in range(1, 14):
            if col in _NUM_COLS_1:
                cells.append(_num_cell(col, ridx, col_vals[col]))
            else:
                style = _S_DATE if col in _DATE_COLS_1 else _S_TEXT
                cells.append(_str_cell(col, ridx, col_vals[col], style))
        rows1.append(f'<row r="{ridx}" spans="1:16" x14ac:dyDescent="0.2">{"".join(cells)}</row>')
    _replace_sheet(files, "xl/worksheets/sheet1.xml", rows1, f"A1:P{1 + len(histories)}")

    # ── Sheet2 items ───────────────────────────────────────────────
    rows2 = [_header_row(_HEADERS_2, 8)]
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
                _num_cell(7, cur, d["price"]),
                _num_cell(8, cur, d["amount"]),
            ]
            rows2.append(f'<row r="{cur}" spans="1:8" x14ac:dyDescent="0.2">{"".join(cells)}</row>')
            cur += 1
    _replace_sheet(files, "xl/worksheets/sheet2.xml", rows2, f"A1:H{max(cur - 1, 1)}")

    # ── Sheet3 tail · 仅表头(无押金/不开收货单 · 库存 S4 另做)──
    _replace_sheet(files, "xl/worksheets/sheet3.xml", [_header_row(_HEADERS_3, 3)], "A1:C1")

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
