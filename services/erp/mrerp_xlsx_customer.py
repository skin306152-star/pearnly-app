# -*- coding: utf-8 -*-
"""MR.ERP xlsx · master_customer(自建客户/买方 · imparmas)· 克隆官方模板生成。

自建客户走 xlsx 导入(非 Playwright 表单)· 单 sheet · 25 列。必填码字段(照抄现有客户 0006):
类型=1-11 / 应收科目=1130-03 / 业务员=กร / 销售区=สุพรรณ(须恰 6 字符)/ 运输=TRUCK1 / 分支=00000。
邮箱必填且须合法格式(空/'-' 都被拒),无则给合法占位。克隆策略同 sales_cash:字节模板只重写
sheetData+sharedStrings,保留 styles(表头 s6/文本 s8/数值 s9-s11)。结构码按套账不同,可经
mappings["_mrerp_customer_*"] 覆盖(别的套账不覆盖会被 report 挡下 fail-safe)。
"""

import io
import os
import re
import zipfile
from collections import OrderedDict
from typing import Any, Dict, List

from services.erp.mrerp_xlsx_fmt import fmt_number

_TEMPLATE_NAME = "test_data_mrerp_sample_customer.xlsx"

_S_HEADER = 6
_S_TEXT = 8
# 数值列(1-indexed)→ 各自样式(该模板 cellXfs)
_NUM_COL_STYLE = {19: 9, 20: 10, 21: 10, 22: 11, 23: 10}

_HEADERS = [
    "รหัสลูกค้า",
    "ประเภทลูกค้า",
    "คำนำหน้า",
    "ชื่อลูกค้า",
    "ที่อยู่ 1",
    "ที่อยู่ 2",
    "ที่อยู่ 3 ",
    "ที่อยู่ 4",
    "รหัสไปรษณีย์",
    "เบอร์โทรศัพท์",
    "อีเมล์",
    "ประเทศ",
    "รหัสบัญชี",
    "คำนำหน้า",
    "ชื่อผู้ติดต่อ",
    "รหัสพนักงานขาย",
    "รหัสพื้นที่การขาย",
    "รหัสประเภทขนส่ง",
    "เครดิตเทอม",
    "ส่วนลด",
    "วงเงินเครดิต",
    "จัดอันดับลูกค้า",
    "อัตราแลกเปลี่ยน",
    "เลขประจำตัวผู้เสียภาษี",
    "รหัสสาขาลูกค้า",
]

# TEST2019 默认结构码(照抄现有客户 0006 的合法值)· 生产按套账经 mappings 覆盖。
# ⚠️ area/account/salesman 是套账专属主数据码,别的套账必须覆盖,否则被 report 挡下(fail-safe)。
_DEFAULTS = {
    "type": "1-11",  # ประเภทลูกค้า · 应收账款(贸易债务人)
    "account": "1130-03",  # รหัสบัญชี · 应收科目
    "salesman": "กร",  # รหัสพนักงานขาย
    "area": "สุพรรณ",  # รหัสพื้นที่การขาย · 须恰 6 字符
    "shipping": "TRUCK1",  # รหัสประเภทขนส่ง
    "branch": "00000",  # 分支 · 总公司
    "prefix": "บริษัท",  # คำนำหน้า · 公司抬头
    "country": "TH",
    "email": "noemail@pearnly.app",  # 邮箱必填且须合法格式 · 单据无邮箱时的占位默认
}
_PLACEHOLDER = "-"  # 必填但无数据的文本字段(MR.ERP 空则报 เป็นค่าว่าง)


def _cfg(mappings: Dict[str, Any], key: str) -> str:
    if isinstance(mappings, dict):
        v = (mappings.get(f"_mrerp_customer_{key}") or "").strip()
        if v:
            return v
    return _DEFAULTS[key]


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
    raise FileNotFoundError(f"customer template missing: {_TEMPLATE_NAME}")


def _num(v) -> str:
    n = fmt_number(v)
    if n is None:
        return "0"
    return str(int(n)) if float(n) == int(n) else repr(float(n))


def _email(v: Any) -> str:
    """MR.ERP 客户邮箱必填**且**须合法格式(空报 เป็นค่าว่าง · '-' 报格式非法)。
    单据无邮箱时给合法占位默认,满足校验。"""
    s = str(v or "").strip()
    return s[:50] if re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", s) else _DEFAULTS["email"]


def build_customer_row(cust: Dict[str, Any], mappings: Dict[str, Any]) -> Dict[int, Any]:
    """OCR 买方 → 客户主数据 25 列(1-indexed)· 名/税号/地址来自单据,结构码走默认/覆盖。"""
    name = str(cust.get("name") or cust.get("customer_name") or "")[:100] or _PLACEHOLDER
    tax = re.sub(r"\D", "", str(cust.get("tax_id") or cust.get("taxid") or ""))[:13] or _PLACEHOLDER
    addr = str(cust.get("address") or "")

    def _or_ph(v: str) -> str:
        return v.strip() if v and v.strip() else _PLACEHOLDER

    # MR.ERP 客户导入把地址 2-4/邮箱/联系人等都当必填(空→报错)· 无数据填占位 "-"。
    return {
        1: str(cust.get("code") or "")[:20],
        2: _cfg(mappings, "type"),
        3: _cfg(mappings, "prefix"),
        4: name,
        5: _or_ph(addr[:100]),
        6: _or_ph(addr[100:200]),
        7: _PLACEHOLDER,
        8: _PLACEHOLDER,
        9: _or_ph(str(cust.get("postcode") or "")[:20]),
        10: _or_ph(str(cust.get("phone") or "")[:40]),
        11: _email(cust.get("email")),
        12: _cfg(mappings, "country"),
        13: _cfg(mappings, "account"),
        14: _cfg(mappings, "prefix"),
        15: name[:50],
        16: _cfg(mappings, "salesman"),
        17: _cfg(mappings, "area"),
        18: _cfg(mappings, "shipping"),
        19: 0,  # เครดิตเทอม
        20: 0,  # ส่วนลด
        21: 0,  # วงเงินเครดิต
        22: 0,  # จัดอันดับ
        23: 1,  # อัตราแลกเปลี่ยน
        24: tax,
        25: _cfg(mappings, "branch"),
    }


def generate_xlsx_customer(customers: List[Dict[str, Any]], mappings: Dict[str, Any]) -> bytes:
    """克隆官方模板生成 master_customer xlsx。"""
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

    def _cell(col: int, row: int, val: Any) -> str:
        letter = _col_letter(col)
        if col in _NUM_COL_STYLE:
            return f'<c r="{letter}{row}" s="{_NUM_COL_STYLE[col]}"><v>{_num(val)}</v></c>'
        return f'<c r="{letter}{row}" s="{_S_TEXT}" t="s"><v>{sidx(val)}</v></c>'

    # header
    h_cells = "".join(
        f'<c r="{_col_letter(i)}1" s="{_S_HEADER}" t="s"><v>{sidx(h)}</v></c>'
        for i, h in enumerate(_HEADERS, 1)
    )
    rows = [
        f'<row r="1" spans="1:25" ht="23.1" customHeight="1" '
        f'x14ac:dyDescent="0.2">{h_cells}</row>'
    ]
    for ridx, cust in enumerate(customers, start=2):
        row_data = build_customer_row(cust, mappings)
        cells = "".join(_cell(col, ridx, val) for col, val in sorted(row_data.items()))
        rows.append(
            f'<row r="{ridx}" spans="1:25" ht="23.1" customHeight="1" '
            f'x14ac:dyDescent="0.2">{cells}</row>'
        )

    xml = files["xl/worksheets/sheet1.xml"].decode("utf-8")
    xml = re.sub(
        r"<sheetData>.*?</sheetData>",
        "<sheetData>" + "".join(rows) + "</sheetData>",
        xml,
        flags=re.DOTALL,
    )
    xml = re.sub(r'<dimension ref="[^"]+"', f'<dimension ref="A1:Y{1 + len(customers)}"', xml)
    files["xl/worksheets/sheet1.xml"] = xml.encode("utf-8")

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
