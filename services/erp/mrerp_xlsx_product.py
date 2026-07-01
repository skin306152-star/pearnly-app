# -*- coding: utf-8 -*-
"""MR.ERP xlsx · master_product(自建商品 · impstkmas)· 克隆官方模板生成。

自建商品走 xlsx 导入 · 单 sheet · 29 列 · 库存型(STKTYP=1)。必填极多(照抄现有商品 P26050030):
成本法/4 单位/8 个 GL 科目(收入·退·折 / 采购·退·折 / 存货 / 成本)/供应商。8 科目 + 类目 + 单位
按套账不同,可经 mappings["_mrerp_product_*"] 覆盖(别的套账不覆盖会被 report 挡下 fail-safe)。
克隆策略同 customer:字节模板只重写 sheetData+sharedStrings,保留 styles(表头 s4/文本 s7/数值 s9)。
"""

import io
import os
import re
import zipfile
from collections import OrderedDict
from typing import Any, Dict, List

from services.erp.mrerp_xlsx_fmt import fmt_number

_TEMPLATE_NAME = "test_data_mrerp_sample_product.xlsx"

_S_HEADER = 4
_S_TEXT = 7
_S_NUM = 9
_NUM_COLS = {9, 14, 16, 17, 18, 19, 20}  # 售价/买卖单位数/标准成本/寿命/最小/最大

_HEADERS = [
    "ประเภทสินค้า",
    "รหัสหมวดสินค้า",
    "รหัสสินค้า",
    "ชื่อสินค้า",
    "รหัสสินค้าเพื่อซื้อ",
    "ชื่อสินค้าเพื่อซื้อ",
    "รหัสสินค้าเพื่อขาย",
    "ชื่อสินค้าเพื่อขาย",
    "ราคาขาย",
    "วิธีคำนวณต้นทุนสินค้า",
    "รหัสจำนวนนับ",
    "รหัสหน่วยนับมาตรฐาน",
    "หน่วยนับซื้อ",
    "จำนวนต่อหน่วยนับซื้อ",
    "หน่วยนับขาย",
    "จำนวนต่อหน่วยนับขาย",
    "ต้นทุนมาตรฐาน",
    "อายุ-วัน",
    "จำนวนสินค้าต่ำสุด",
    "จำนวนสินค้าสูงสุด",
    "รหัสบัญชีรายได้-ขายเชื่อ",
    "รหัสบัญชีรายได้-รับคืน",
    "รหัสบัญชีรายได้-ส่วนลดจ่าย",
    "รหัสบัญชีซื้อสินค้า",
    "รหัสบัญชีซื้อ-ส่งคืน",
    "รหัสบัญชีซื้อ-ส่วนลดรับ",
    "รหัสบัญชีสินค้า",
    "รหัสบัญชีต้นทุนขาย",
    "รหัสผู้จำหน่าย",
]

# TEST2019 默认结构码(照抄现有商品 P26050030)· 生产按套账经 mappings 覆盖
_DEFAULTS = {
    # ★import 认的是短标签非 select 值/全名(实测:类型只认 "จัดทำสต๊อค",带 "สินค้า : " 前缀被拒)
    "type": "จัดทำสต๊อค",  # 库存型(Zihao 定:商品建库存型)
    "category": "03-FIG",
    "cost_method": "Average",
    "unit_count": "ผน",
    "unit_std": "ผน",
    "unit_buy": "ผน",
    "unit_sell": "ผน",
    "acc_rev": "4110-01",  # 收入-赊销
    "acc_ret": "4110-10",  # 收入-退货
    "acc_dis": "4110-20",  # 收入-折让
    "acc_pur": "5110-01",  # 采购
    "acc_purret": "5110-11",  # 采购退回
    "acc_purdis": "5110-21",  # 采购折让
    "acc_inv": "1150-30",  # 存货科目
    "acc_cost": "5100-01",  # 销货成本
    "supplier": "CODE_NOAP",  # 无供应商占位
}


def _cfg(mappings: Dict[str, Any], key: str) -> str:
    if isinstance(mappings, dict):
        v = (mappings.get(f"_mrerp_product_{key}") or "").strip()
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
    raise FileNotFoundError(f"product template missing: {_TEMPLATE_NAME}")


def _num(v) -> str:
    n = fmt_number(v)
    if n is None:
        return "0"
    return str(int(n)) if float(n) == int(n) else repr(float(n))


def build_product_row(prod: Dict[str, Any], mappings: Dict[str, Any]) -> Dict[int, Any]:
    """OCR 商品行 → 商品主数据 29 列(1-indexed)· 码/名/售价来自单据,结构码走默认/覆盖。"""
    code = str(prod.get("code") or "")[:15]
    name = str(prod.get("name") or "")[:50] or "-"
    price = fmt_number(prod.get("price") or prod.get("unit_price")) or 0
    return {
        1: _cfg(mappings, "type"),
        2: _cfg(mappings, "category"),
        3: code,
        4: name,
        5: code,  # 采购码 = 商品码
        6: name,
        7: code,  # 销售码 = 商品码
        8: name,
        9: price,  # 售价
        10: _cfg(mappings, "cost_method"),
        11: _cfg(mappings, "unit_count"),
        12: _cfg(mappings, "unit_std"),
        13: _cfg(mappings, "unit_buy"),
        14: 1,  # 每采购单位数量
        15: _cfg(mappings, "unit_sell"),
        16: 1,  # 每销售单位数量
        17: 0,  # 标准成本
        18: 365,  # 寿命-天
        19: 0,  # 最小库存
        20: 0,  # 最大库存
        21: _cfg(mappings, "acc_rev"),
        22: _cfg(mappings, "acc_ret"),
        23: _cfg(mappings, "acc_dis"),
        24: _cfg(mappings, "acc_pur"),
        25: _cfg(mappings, "acc_purret"),
        26: _cfg(mappings, "acc_purdis"),
        27: _cfg(mappings, "acc_inv"),
        28: _cfg(mappings, "acc_cost"),
        29: _cfg(mappings, "supplier"),
    }


def generate_xlsx_product(products: List[Dict[str, Any]], mappings: Dict[str, Any]) -> bytes:
    """克隆官方模板生成 master_product xlsx(库存型)。"""
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
    rows = [f'<row r="1" spans="1:29" x14ac:dyDescent="0.2">{h_cells}</row>']
    for ridx, prod in enumerate(products, start=2):
        row_data = build_product_row(prod, mappings)
        cells = "".join(_cell(col, ridx, val) for col, val in sorted(row_data.items()))
        rows.append(f'<row r="{ridx}" spans="1:29" x14ac:dyDescent="0.2">{cells}</row>')

    xml = files["xl/worksheets/sheet1.xml"].decode("utf-8")
    xml = re.sub(
        r"<sheetData>.*?</sheetData>",
        "<sheetData>" + "".join(rows) + "</sheetData>",
        xml,
        flags=re.DOTALL,
    )
    xml = re.sub(r'<dimension ref="[^"]+"', f'<dimension ref="A1:AC{1 + len(products)}"', xml)
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
