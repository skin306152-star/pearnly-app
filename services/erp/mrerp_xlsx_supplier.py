# -*- coding: utf-8 -*-
"""MR.ERP xlsx · master_supplier(自建供应商/卖方 · impapmas)· 克隆官方模板生成。

自建供应商走 xlsx 导入 · 单 sheet · 22 列。必填码字段(照抄现有供应商 / 靠 report 校正):
类型=B(须恰 4 字符)/ 应付科目=M / 分支=V(须恰 5 字符)。邮箱必填且须合法格式(同客户)。
克隆策略同 customer:字节模板只重写 sheetData+sharedStrings,保留 styles(表头 s6/文本 s7/数值 s10)。
结构码按套账不同,可经 mappings["_mrerp_supplier_*"] 覆盖(别的套账不覆盖会被 report 挡下 fail-safe)。
"""

import io
import os
import re
import zipfile
from collections import OrderedDict
from typing import Any, Dict, List

from services.erp.mrerp_xlsx_fmt import fmt_number

_TEMPLATE_NAME = "test_data_mrerp_sample_supplier.xlsx"

_S_HEADER = 6
_S_TEXT = 7
_S_NUM = 10
_NUM_COLS = {16, 17, 18, 19, 20}  # 信用期/折扣/信用额/评级/汇率

_HEADERS = [
    "รหัสผู้จำหน่าย",
    "ประเภทผู้จำหน่าย",
    "คำนำหน้า",
    "ชื่อผู้จำหน่าย",
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
    "เครดิตเทอม",
    "ส่วนลด",
    "วงเงินเครดิต",
    "จัดอันดับผู้จำหน่าย",
    "อัตราแลกเปลี่ยน",
    "เลขประจำตัวผู้เสียภาษี",
    "รหัสสาขาผู้จำหน่าย",
]

# TEST2019 默认结构码 · 生产按套账经 mappings 覆盖。⚠️ type/account/branch 是套账专属主数据码。
_DEFAULTS = {
    "type": "2-21",  # ประเภทผู้จำหน่าย · 应付账款(贸易债权人)· 恰 4 字符
    "account": "2110-01",  # รหัสบัญชี · 应付科目
    "branch": "00000",  # รหัสสาขา · 总公司 · 恰 5 字符
    "prefix": "บริษัท",  # คำนำหน้า
    "country": "TH",
    "email": "noemail@pearnly.app",
}
_PLACEHOLDER = "-"


def _cfg(mappings: Dict[str, Any], key: str) -> str:
    if isinstance(mappings, dict):
        v = (mappings.get(f"_mrerp_supplier_{key}") or "").strip()
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
    raise FileNotFoundError(f"supplier template missing: {_TEMPLATE_NAME}")


def _num(v) -> str:
    n = fmt_number(v)
    if n is None:
        return "0"
    return str(int(n)) if float(n) == int(n) else repr(float(n))


def _email(v: Any) -> str:
    s = str(v or "").strip()
    return s[:50] if re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", s) else _DEFAULTS["email"]


def build_supplier_row(sup: Dict[str, Any], mappings: Dict[str, Any]) -> Dict[int, Any]:
    """OCR 卖方 → 供应商主数据 22 列(1-indexed)· 名/税号/地址来自单据,结构码走默认/覆盖。"""
    name = str(sup.get("name") or sup.get("supplier_name") or "")[:100] or _PLACEHOLDER
    tax = re.sub(r"\D", "", str(sup.get("tax_id") or sup.get("taxid") or ""))[:13] or _PLACEHOLDER
    addr = str(sup.get("address") or "")

    def _or_ph(v: str) -> str:
        return v.strip() if v and v.strip() else _PLACEHOLDER

    return {
        1: str(sup.get("code") or "")[:20],
        2: _cfg(mappings, "type"),
        3: _cfg(mappings, "prefix"),
        4: name,
        5: _or_ph(addr[:100]),
        6: _or_ph(addr[100:200]),
        7: _PLACEHOLDER,
        8: _PLACEHOLDER,
        9: _or_ph(str(sup.get("postcode") or "")[:20]),
        10: _or_ph(str(sup.get("phone") or "")[:40]),
        11: _email(sup.get("email")),
        12: _cfg(mappings, "country"),
        13: _cfg(mappings, "account"),
        14: _cfg(mappings, "prefix"),
        15: name[:50],
        16: 0,  # เครดิตเทอม
        17: 0,  # ส่วนลด
        18: 0,  # วงเงินเครดิต
        19: 0,  # จัดอันดับ
        20: 1,  # อัตราแลกเปลี่ยน
        21: tax,
        22: _cfg(mappings, "branch"),
    }


def generate_xlsx_supplier(suppliers: List[Dict[str, Any]], mappings: Dict[str, Any]) -> bytes:
    """克隆官方模板生成 master_supplier xlsx。"""
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
        if col in _NUM_COLS:
            return f'<c r="{letter}{row}" s="{_S_NUM}"><v>{_num(val)}</v></c>'
        return f'<c r="{letter}{row}" s="{_S_TEXT}" t="s"><v>{sidx(val)}</v></c>'

    h_cells = "".join(
        f'<c r="{_col_letter(i)}1" s="{_S_HEADER}" t="s"><v>{sidx(h)}</v></c>'
        for i, h in enumerate(_HEADERS, 1)
    )
    rows = [f'<row r="1" spans="1:22" x14ac:dyDescent="0.2">{h_cells}</row>']
    for ridx, sup in enumerate(suppliers, start=2):
        row_data = build_supplier_row(sup, mappings)
        cells = "".join(_cell(col, ridx, val) for col, val in sorted(row_data.items()))
        rows.append(f'<row r="{ridx}" spans="1:22" x14ac:dyDescent="0.2">{cells}</row>')

    xml = files["xl/worksheets/sheet1.xml"].decode("utf-8")
    xml = re.sub(
        r"<sheetData>.*?</sheetData>",
        "<sheetData>" + "".join(rows) + "</sheetData>",
        xml,
        flags=re.DOTALL,
    )
    xml = re.sub(r'<dimension ref="[^"]+"', f'<dimension ref="A1:V{1 + len(suppliers)}"', xml)
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
