# -*- coding: utf-8 -*-
"""MR.ERP xlsx · sales_credit 数据装配(row/detail/tail)+ Korn 真样本克隆生成.

mrerp_xlsx_generator 拆分。逻辑 0 改。invoice_no 派生经 facade 模块属性
`_gen.derive_mrerp_invoice_no` 解析(而非裸名)→ 保留测试/适配器对
`mrerp_xlsx_generator.derive_mrerp_invoice_no` 的 monkeypatch 语义(同 mrerp_adapter_masterdata
的 `_gen.` 范式)。preflight 校验(validate_history_for_sales_credit)留 facade(它读
facade 级的 derive_ + MRERP_*_MAX 常量,二者均为 monkeypatch 目标)。本模块仅由 facade
import,勿在 facade 之前直接 import(否则循环 import 半初始化)。
"""

import io
from typing import Any, Dict, List

from services.erp import mrerp_xlsx_generator as _gen
from services.erp.mrerp_xlsx_fmt import fmt_date, fmt_number
from services.erp.mrerp_xlsx_lookups import (
    lookup_customer_code,
    _build_product_lookup,
    _resolve_product_code,
)


# ============================================================
# 数据装配:从 OCR history 装出 sales_credit 的 row dict
# ============================================================
def build_sales_credit_row(history: Dict[str, Any], mappings: Dict[str, Any]) -> Dict[str, Any]:
    """v27.8.1.4 · 严格对齐 Korn 真实样本 18 列 header
    v27.8.1.5 · invoice_no 转 MR.ERP YYMMDD-NNN 标准格式"""
    cid = history.get("client_id") or 0
    customer_code = lookup_customer_code(cid, mappings)

    # v27.8.1.5 · invoice_no 转 MR.ERP 标准格式(原 OCR 号 'INV-...' 不被认)
    mrerp_invoice_no = _gen.derive_mrerp_invoice_no(history)
    inv_date = fmt_date(history.get("invoice_date"))

    return {
        "invoice_no": mrerp_invoice_no,
        "invoice_date": inv_date,
        # 'tax_rate_str' / 'branch_code' / 'department' / 'job' / 'salesman'
        # / 'sales_area' / 'shipping_type' 都用 schema default(TEST2019 已知存在的值)
        "delivery_date": inv_date,  # 通常 = 开票日(没运单时)
        "customer_code": customer_code,
        "customer_bill": customer_code,
        "bill_no": ("SI" + mrerp_invoice_no)[:30],  # 'SI690415-501'
        "bill_date": inv_date,
        # 'discount' default = 0
        # v27.8.1.6 · 严格对齐 Korn 真样本 · 三个 note 都留空(MR.ERP 可能对备注字段格式有限制)
        "note1": "",
        "note2": "",
        "note3": "",
    }


def build_sales_credit_detail_rows(
    history: Dict[str, Any], mappings: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """v27.8.1.4 · OCR items → detail rows · v27.8.1.5 · invoice_no 同步用 MR.ERP 标准格式
    v27.8.1.17 · 加 product_code · 从 mappings['products'] 查 item_name → erp_code · 找不到 fallback '123'(下游 korn_clone 已 fallback)
    """
    mrerp_invoice_no = _gen.derive_mrerp_invoice_no(history)

    # v27.8.1.17 · 建商品 lookup 一次（O(N)）· 内循环 O(1) 查
    product_lookup = _build_product_lookup(mappings)
    # P1「开箱即用」· 通用商品码兜底(由 adapter 注入 mappings)· 配了才有。
    # 商品行对不上 ERP 已有真实商品时,挂这个通用销售商品码,OCR 行描述(item_name)
    # 原样保留为行名/备注。未配(None)= 精确模式 = 老行为(None → 下游 '123')。
    generic_product_code = None
    if isinstance(mappings, dict):
        generic_product_code = (mappings.get("_generic_product_code") or "").strip() or None

    items = []
    for src_field in (
        history.get("items"),
        (
            (history.get("fields") or {}).get("items")
            if isinstance(history.get("fields"), dict)
            else None
        ),
    ):
        if isinstance(src_field, list) and src_field:
            items = src_field
            break
    if not items:
        pages = history.get("pages")
        if isinstance(pages, list):
            for p in pages:
                if not isinstance(p, dict):
                    continue
                pf = p.get("fields") or {}
                if isinstance(pf, dict):
                    pi = pf.get("items")
                    if isinstance(pi, list) and pi:
                        items = pi
                        break

    rows = []
    if items:
        for it in items:
            if not isinstance(it, dict):
                continue
            qty = fmt_number(it.get("qty") or it.get("quantity"))
            price = fmt_number(it.get("unit_price") or it.get("price"))
            amt = fmt_number(it.get("amount") or it.get("total"))
            if qty is None and price is not None and amt is not None and price != 0:
                qty = round(amt / price, 4)
            if price is None and qty is not None and amt is not None and qty != 0:
                price = round(amt / qty, 4)
            if amt is None and qty is not None and price is not None:
                amt = round(qty * price, 2)
            # v27.8.1.17 · 查商品映射 · 找不到返 None · 下游 korn_clone 兜底 '123'
            # P1 · 通用模式下找不到 → 用通用销售商品码(精准其所当精准,通用其所该通用)。
            item_name = it.get("name") or it.get("description") or ""
            erp_code = _resolve_product_code(item_name, product_lookup)
            if erp_code is None and generic_product_code:
                erp_code = generic_product_code
            rows.append(
                {
                    "invoice_no": mrerp_invoice_no,
                    "qty": qty if qty is not None else 1,
                    "unit_price": price if price is not None else 0,
                    "amount": amt if amt is not None else 0,
                    "product_code": erp_code,
                    "item_name": str(item_name or ""),
                }
            )
    if not rows:
        sub = fmt_number(history.get("subtotal") or history.get("amount_before_tax"))
        tot = fmt_number(history.get("total_amount"))
        if sub is None and tot is not None:
            sub = round(tot / 1.07, 2)
        unit = sub or tot or 0
        rows.append(
            {
                "invoice_no": mrerp_invoice_no,
                "qty": 1,
                "unit_price": unit,
                "amount": unit,
                # P1 · 无明细行也用通用码兜底(精确模式仍 None → 下游 '123')。
                "product_code": generic_product_code,
                "item_name": "",
            }
        )
    return rows


def build_sales_credit_tail_row(history: Dict[str, Any]) -> Dict[str, Any]:
    """v27.8.1.4 · tail · v27.8.1.5 同步 invoice_no 格式"""
    mrerp_invoice_no = _gen.derive_mrerp_invoice_no(history)
    return {
        "invoice_no": mrerp_invoice_no,
        "deposit_no": "",
        "is_sales_issued": "",
    }


def _generate_xlsx_sales_credit_korn_clone(
    histories: List[Dict[str, Any]], mappings: Dict[str, Any]
) -> bytes:
    """v27.8.1.12 · 用 Korn 真样本作模板 · 克隆方式生成 sales_credit xlsx

    根因:openpyxl 输出 workbook.xml / [Content_Types].xml 跟 PhpSpreadsheet 期望差异大
    解法:克隆 Korn 真样本(已验证可 import) · 只重写 sharedStrings + sheetData
    保留 metadata:workbook.xml / styles.xml / theme.xml / [Content_Types].xml 等全部不动
    """
    import zipfile
    import os
    import re as _re
    from collections import OrderedDict

    # 模板 git-tracked 在【仓库根】· 目录重组(d05cf6d)把本模块移入 services/erp/ 后,
    # 原 os.path.dirname(__file__) 路径就找不到模板 → 静默回退 openpyxl 版 →
    # MR.ERP 拒收(列数不足 18)→ 推送全失败。逐候选目录找,根目录优先(实测可 import)。
    _here = os.path.dirname(os.path.abspath(__file__))
    _root = os.path.dirname(os.path.dirname(_here))
    template_path = None
    for _cand in (
        os.path.join(_root, "test_data_mrerp_sample_SC.xlsx"),
        os.path.join(_here, "test_data_mrerp_sample_SC.xlsx"),
    ):
        if os.path.exists(_cand):
            template_path = _cand
            break
    if not template_path:
        raise FileNotFoundError("Korn template missing: test_data_mrerp_sample_SC.xlsx")

    with open(template_path, "rb") as f:
        template_bytes = f.read()

    files: Dict[str, bytes] = {}
    with zipfile.ZipFile(io.BytesIO(template_bytes), "r") as zf:
        for name in zf.namelist():
            files[name] = zf.read(name)

    shared: "OrderedDict[str, int]" = OrderedDict()

    def _get_idx(text: str) -> int:
        text = str(text) if text is not None else ""
        if text not in shared:
            shared[text] = len(shared)
        return shared[text]

    def _col_letter(n: int) -> str:
        s = ""
        while n > 0:
            n, r = divmod(n - 1, 26)
            s = chr(65 + r) + s
        return s

    def _xml_escape(s: str) -> str:
        return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    # ─── Sheet 1 (header) ──────────────────────────────────────────
    HEADERS_1 = [
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
        "พื้นที่การขาย",
        "ประเภทขนส่ง",
        "หักส่วนลด",
        "หมายเหตุ 1",
        "หมายเหตุ 2",
        "หมายเหตุ 3",
    ]
    row1_cells = []
    for i, lbl in enumerate(HEADERS_1, 1):
        row1_cells.append(f'<c r="{_col_letter(i)}1" s="2" t="s"><v>{_get_idx(lbl)}</v></c>')
    rows_xml = [
        f'<row r="1" spans="1:19" ht="23.1" customHeight="1" '
        f'x14ac:dyDescent="0.2">{"".join(row1_cells)}</row>'
    ]

    for ridx, history in enumerate(histories, start=2):
        row_data = build_sales_credit_row(history, mappings)
        invoice_no = row_data.get("invoice_no", "")
        invoice_date = row_data.get("invoice_date", "")
        bill_no = row_data.get("bill_no", "")
        cust_code = row_data.get("customer_code", "")
        STR_VALUES = [
            invoice_no,
            invoice_date,
            "7 (แยก)",
            "00000",
            "BOI1",
            "00002",
            "กร ทดสอบ",
            invoice_date,
            cust_code,
            cust_code,
            bill_no,
            invoice_date,
            "สุพรรณบุรี",
            "ขนส่งโดยบริษัท",
        ]
        cells = []
        for i, val in enumerate(STR_VALUES, 1):
            cells.append(
                f'<c r="{_col_letter(i)}{ridx}" s="3" t="s">' f"<v>{_get_idx(val)}</v></c>"
            )
        # 第 15 列(O)= 折扣 0(数值 · 不带 t)
        cells.append(f'<c r="O{ridx}" s="5"><v>0</v></c>')
        # 第 16-18 列(P/Q/R)= 备注完全空 cell
        for i in (16, 17, 18):
            cells.append(f'<c r="{_col_letter(i)}{ridx}" s="3"/>')
        # 第 19 列(S)= 末尾 spacer 完全空 cell(对齐 Korn dim=A1:S2)
        cells.append(f'<c r="S{ridx}" s="6"/>')
        rows_xml.append(
            f'<row r="{ridx}" spans="1:19" ht="23.1" customHeight="1" '
            f'x14ac:dyDescent="0.2">{"".join(cells)}</row>'
        )

    new_sheet_data = "<sheetData>" + "".join(rows_xml) + "</sheetData>"
    s1 = files["xl/worksheets/sheet1.xml"].decode("utf-8")
    s1 = _re.sub(r"<sheetData>.+?</sheetData>", new_sheet_data, s1, flags=_re.DOTALL)
    s1 = _re.sub(r'<dimension ref="[^"]+"', f'<dimension ref="A1:S{1 + len(histories)}"', s1)
    files["xl/worksheets/sheet1.xml"] = s1.encode("utf-8")

    # ─── Sheet 2 (detail) ──────────────────────────────────────────
    HEADERS_2 = ["เลขที่", "รหัสสินค้า", "แผนก", "งาน", "คลัง", "จำนวน", "ราคา/หน่วย", "จำนวนเงิน"]
    rows2 = []
    h_cells = []
    for i, lbl in enumerate(HEADERS_2, 1):
        h_cells.append(f'<c r="{_col_letter(i)}1" s="2" t="s"><v>{_get_idx(lbl)}</v></c>')
    rows2.append(
        f'<row r="1" spans="1:8" ht="23.1" customHeight="1" '
        f'x14ac:dyDescent="0.2">{"".join(h_cells)}</row>'
    )

    cur_row = 2
    total_detail_rows = 0
    for history in histories:
        invoice_no = _gen.derive_mrerp_invoice_no(history)
        detail_rows = build_sales_credit_detail_rows(history, mappings)
        for row_data in detail_rows:
            qty = row_data.get("qty", 0) or 0
            unit_price = row_data.get("unit_price", 0) or 0
            amount = row_data.get("amount", 0) or 0
            product_code = row_data.get("product_code") or "123"
            cells = [
                f'<c r="A{cur_row}" s="3" t="s"><v>{_get_idx(invoice_no)}</v></c>',
                f'<c r="B{cur_row}" s="3" t="s"><v>{_get_idx(product_code)}</v></c>',
                f'<c r="C{cur_row}" s="3" t="s"><v>{_get_idx("BOI1")}</v></c>',
                f'<c r="D{cur_row}" s="3" t="s"><v>{_get_idx("00002")}</v></c>',
                f'<c r="E{cur_row}" s="3" t="s"><v>{_get_idx("0000")}</v></c>',
                f'<c r="F{cur_row}" s="5"><v>{_format_num(qty)}</v></c>',
                f'<c r="G{cur_row}" s="5"><v>{_format_num(unit_price)}</v></c>',
                f'<c r="H{cur_row}" s="5"><v>{_format_num(amount)}</v></c>',
            ]
            rows2.append(
                f'<row r="{cur_row}" spans="1:8" ht="23.1" customHeight="1" '
                f'x14ac:dyDescent="0.2">{"".join(cells)}</row>'
            )
            cur_row += 1
            total_detail_rows += 1

    if total_detail_rows == 0:
        # 至少留 header · 否则 MR.ERP 可能拒
        total_detail_rows = 0  # row 1 only

    new_sheet2_data = "<sheetData>" + "".join(rows2) + "</sheetData>"
    s2 = files["xl/worksheets/sheet2.xml"].decode("utf-8")
    s2 = _re.sub(r"<sheetData>.+?</sheetData>", new_sheet2_data, s2, flags=_re.DOTALL)
    s2_max_row = 1 + total_detail_rows
    s2 = _re.sub(r'<dimension ref="[^"]+"', f'<dimension ref="A1:H{max(s2_max_row, 1)}"', s2)
    files["xl/worksheets/sheet2.xml"] = s2.encode("utf-8")

    # ─── Sheet 3 (tail) · 只 header(跟 Korn 真样本完全一致) ──────
    HEADERS_3 = ["เลขที่", "เลขที่เงินมัดจำ", "ออกใบขาย"]
    h3_cells = []
    for i, lbl in enumerate(HEADERS_3, 1):
        h3_cells.append(f'<c r="{_col_letter(i)}1" s="2" t="s"><v>{_get_idx(lbl)}</v></c>')
    new_sheet3_data = (
        f'<sheetData><row r="1" spans="1:3" ht="23.1" customHeight="1" '
        f'x14ac:dyDescent="0.2">{"".join(h3_cells)}</row></sheetData>'
    )
    s3 = files["xl/worksheets/sheet3.xml"].decode("utf-8")
    s3 = _re.sub(r"<sheetData>.+?</sheetData>", new_sheet3_data, s3, flags=_re.DOTALL)
    s3 = _re.sub(r'<dimension ref="[^"]+"', '<dimension ref="A1:C1"', s3)
    files["xl/worksheets/sheet3.xml"] = s3.encode("utf-8")

    # ─── 重写 sharedStrings.xml ────────────────────────────────────
    parts = [
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\r\n',
        f'<sst xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
        f'count="{len(shared)}" uniqueCount="{len(shared)}">',
    ]
    for text in shared:
        parts.append(f'<si><t xml:space="preserve">{_xml_escape(text)}</t></si>')
    parts.append("</sst>")
    files["xl/sharedStrings.xml"] = "".join(parts).encode("utf-8")

    # ─── 重新打包(保留 Korn 所有其他文件不动)──────────────────
    out_buf = io.BytesIO()
    with zipfile.ZipFile(out_buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for name, data in files.items():
            zf.writestr(name, data)
    return out_buf.getvalue()


def _format_num(n):
    """数值格式化 · 整数不要小数点(跟 Korn 风格一致)"""
    try:
        f = float(n)
        if f == int(f):
            return str(int(f))
        return repr(f)
    except (ValueError, TypeError):
        return "0"
