# -*- coding: utf-8 -*-
"""MR.ERP xlsx · sales_cash(ใบขายเงินสด)· 克隆官方 example.xlsx 生成。

现金销售 = 赊销表头(前 14 列)+ 现金收款列(第 16 列 จำนวนเงินสดรับ = 收讫总额)。
商品明细(sheet2)/尾(sheet3)与赊销同 → 复用 build_sales_credit_* 装配。

克隆策略同 sales_credit(known-facts §6.3):以官方 test_data_mrerp_sample_cash.xlsx 为字节模板,
仅重写 4 个 sheet 的 <sheetData> + sharedStrings,保留 styles/workbook/Content_Types 全部不动。
styles.xml 为 workbook 级共享:数据文本 s=8 / 日期 s=9 / 数值 s=10,表头 s=4(实测该模板 cellXfs)。
"""

import io
import os
import re
import zipfile
from collections import OrderedDict
from typing import Any, Dict, List

from services.erp import mrerp_xlsx_generator as _gen
from services.erp.mrerp_xlsx_fmt import history_number
from services.erp.mrerp_xlsx_sales_credit import (
    build_sales_credit_detail_rows,
    build_sales_credit_row,
    _format_num,
)

_TEMPLATE_NAME = "test_data_mrerp_sample_cash.xlsx"

# 官方模板共享样式索引(该模板 cellXfs · 见 known-facts §6.4)
_S_HEADER = 4  # numFmt 49 文本
_S_TEXT = 8  # 文本数据
_S_DATE = 9  # numFmt 187 日期(存为文本)
_S_NUM = 10  # numFmt 4 数值

_HEADERS_1 = [
    "เลขที่",
    "วันที่",
    "อัตราภาษี",
    "สาขา",
    "แผนก",
    "งาน",
    "พนักงานขาย",
    "กำหนดส่งสินค้า",
    "รหัสลูกค้า",
    "รหัสลูกค้า (บิล)",
    "เลขที่บิล",
    "วันที่",
    "พื้นทีการขาย",
    "ประเภทขนส่ง",
    "หักส่วนลด",
    "จำนวนเงินสดรับ",
    "รับอื่นๆ 1",
    "จำนวนเงินอื่นๆ 1",
    "รับอื่นๆ 2",
    "จำนวนเงินอื่นๆ 2",
    "รับอื่นๆ 3",
    "จำนวนเงินอื่นๆ 3",
    "หมายเหตุ 1",
    "หมายเหตุ 2",
    "หมายเหตุ 3",
]
_HEADERS_2 = ["เลขที่", "รหัสสินค้า", "แผนก", "งาน", "คลัง", "จำนวน", "ราคา/หน่วย", "จำนวนเงิน"]
_HEADERS_3 = ["เลขที่", "เลขที่เงินมัดจำ", "ออกใบขาย"]
_HEADERS_4 = ["เลขที่", "เลขที่เช็ค", "เช็คลงวันที่", "ธนาคาร", "จำนวนเงิน"]

# sheet1 数值列(1-indexed):折扣/现金收讫/其他收款额
_NUM_COLS_1 = {15, 16, 18, 20, 22}
_DATE_COLS_1 = {2, 8, 12}

# 收款科目(รับอื่นๆ)· 收款落哪个 GL 科目 —— 实测 MR.ERP 现金票要求 3 个收款槽全非空,
# 且每槽是**科目表里的科目码**(1111-01=现金 / 1112-01=银行,非付款方式代号)。转账票落银行,
# 现金票落现金。⚠️ 科目码按套账不同 —— 生产须由 mappings["_mrerp_receipt_account_*"] 注入
# (对接 S4 科目解析);未配时用 TEST2019 默认,推别的套账会因科目不存在被 report 回读挡下(fail-safe)。
_DEFAULT_RECEIPT_ACCOUNT_BANK = "1112-01"
_DEFAULT_RECEIPT_ACCOUNT_CASH = "1111-01"


def _receipt_account(history: Dict[str, Any], mappings: Dict[str, Any]) -> str:
    """收款落账科目:现金付→现金科目,其余(转账/刷卡)→银行科目。可经 mappings 覆盖。"""
    from services.erp.express_push.common import payment_is_paid

    fields = history.get("fields") if isinstance(history.get("fields"), dict) else history
    is_cash = payment_is_paid(fields) and str(fields.get("payment_method", "")).lower() in (
        "",
        "cash",
        "เงินสด",
    )
    if isinstance(mappings, dict):
        key = "_mrerp_receipt_account_cash" if is_cash else "_mrerp_receipt_account_bank"
        override = (mappings.get(key) or "").strip()
        if override:
            return override
    return _DEFAULT_RECEIPT_ACCOUNT_CASH if is_cash else _DEFAULT_RECEIPT_ACCOUNT_BANK


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
    raise FileNotFoundError(f"sales_cash template missing: {_TEMPLATE_NAME}")


def _cash_received(history: Dict[str, Any]) -> str:
    tot = history_number(history, "total_amount")
    if tot is None:
        sub = history_number(history, "subtotal", "amount_before_tax") or 0
        vat = history_number(history, "vat") or 0
        tot = round(sub + vat, 2)
    return _format_num(tot)


def generate_xlsx_sales_cash(histories: List[Dict[str, Any]], mappings: Dict[str, Any]) -> bytes:
    """克隆官方模板生成 sales_cash xlsx(现金全额收讫 · cheque 页留空)。"""
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

    def _str_cell(col: int, row: int, val: str, style: int) -> str:
        return f'<c r="{_col_letter(col)}{row}" s="{style}" t="s"><v>{sidx(val)}</v></c>'

    def _num_cell(col: int, row: int, val) -> str:
        return f'<c r="{_col_letter(col)}{row}" s="{_S_NUM}"><v>{_format_num(val)}</v></c>'

    def _header_row(headers: List[str], span: int) -> str:
        cells = "".join(_str_cell(i, 1, h, _S_HEADER) for i, h in enumerate(headers, 1))
        return (
            f'<row r="1" spans="1:{span}" ht="23.1" customHeight="1" '
            f'x14ac:dyDescent="0.2">{cells}</row>'
        )

    # ── Sheet1 header ──────────────────────────────────────────────
    rows1 = [_header_row(_HEADERS_1, 25)]
    for ridx, history in enumerate(histories, start=2):
        base = build_sales_credit_row(history, mappings)
        inv, date = base["invoice_no"], base["invoice_date"]
        cust, bill = base["customer_code"], base["bill_no"]
        col_vals = {
            1: inv,
            2: date,
            3: "7 (แยก)",
            4: "00000",
            5: "BOI1",
            6: "00002",
            7: "กร ทดสอบ",
            8: date,
            9: cust,
            10: cust,
            11: bill,
            12: date,
            13: "สุพรรณบุรี",
            14: "ขนส่งโดยบริษัท",
            15: 0,
            16: 0,  # 折扣 0 · 现金收讫 0(全额走收款科目槽,见下)
        }
        # 收款槽 1-3(รับอื่นๆ):MR.ERP 现金票要求 3 槽全非空 → 槽1 记全额到收款科目,
        # 槽2/3 用同科目占位、金额 0(满足非空校验,不产生额外分录)。见 _receipt_account。
        acct = _receipt_account(history, mappings)
        col_vals.update({17: acct, 18: _cash_received(history), 19: acct, 20: 0, 21: acct, 22: 0})
        cells = []
        for col in range(1, 23):
            if col in _NUM_COLS_1:
                cells.append(_num_cell(col, ridx, col_vals[col]))
            else:
                style = _S_DATE if col in _DATE_COLS_1 else _S_TEXT
                cells.append(_str_cell(col, ridx, col_vals[col], style))
        rows1.append(
            f'<row r="{ridx}" spans="1:25" ht="23.1" customHeight="1" '
            f'x14ac:dyDescent="0.2">{"".join(cells)}</row>'
        )
    _replace_sheet(files, "xl/worksheets/sheet1.xml", rows1, f"A1:Y{1 + len(histories)}")

    # ── Sheet2 items ───────────────────────────────────────────────
    rows2 = [_header_row(_HEADERS_2, 8)]
    cur = 2
    for history in histories:
        inv = _gen.derive_mrerp_invoice_no(history)
        for d in build_sales_credit_detail_rows(history, mappings):
            code = d.get("product_code") or "123"
            cells = [
                _str_cell(1, cur, inv, _S_TEXT),
                _str_cell(2, cur, code, _S_TEXT),
                _str_cell(3, cur, "BOI1", _S_TEXT),
                _str_cell(4, cur, "00002", _S_TEXT),
                _str_cell(5, cur, "0000", _S_TEXT),
                _num_cell(6, cur, d.get("qty", 0) or 0),
                _num_cell(7, cur, d.get("unit_price", 0) or 0),
                _num_cell(8, cur, d.get("amount", 0) or 0),
            ]
            rows2.append(
                f'<row r="{cur}" spans="1:8" ht="23.1" customHeight="1" '
                f'x14ac:dyDescent="0.2">{"".join(cells)}</row>'
            )
            cur += 1
    _replace_sheet(files, "xl/worksheets/sheet2.xml", rows2, f"A1:H{max(cur - 1, 1)}")

    # ── Sheet3 tail / Sheet4 cheque · 仅表头(现金全额 · 无押金/支票)──
    _replace_sheet(files, "xl/worksheets/sheet3.xml", [_header_row(_HEADERS_3, 3)], "A1:C1")
    _replace_sheet(files, "xl/worksheets/sheet4.xml", [_header_row(_HEADERS_4, 5)], "A1:E1")

    # ── sharedStrings ──────────────────────────────────────────────
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
