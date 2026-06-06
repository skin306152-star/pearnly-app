# -*- coding: utf-8 -*-
"""商品 Excel 批量导入解析(PO-3 · docs/sales-module/docs/13)。

读上传的 .xlsx → 表头按别名映射到字段 → 逐行校验 → 返回 (可入库行, 行级错误)。
入库由路由层用 services/sales/products.create_product 完成(同一参数化路径)。
纯解析叶子:不连库、不鉴权。
"""

from __future__ import annotations

import io
from decimal import Decimal, InvalidOperation
from typing import Any

import openpyxl

# 表头别名(小写去空格)→ 字段。中/英/泰常见写法都收。
_HEADER_ALIASES = {
    "name_th": "name_th",
    "ชื่อสินค้า": "name_th",
    "ชื่อ": "name_th",
    "商品名称": "name_th",
    "名称": "name_th",
    "name": "name_th",
    "name_en": "name_en",
    "english": "name_en",
    "英文名": "name_en",
    "name_zh": "name_zh",
    "中文名": "name_zh",
    "code": "code",
    "รหัส": "code",
    "รหัสสินค้า": "code",
    "编码": "code",
    "货号": "code",
    "barcode": "barcode",
    "บาร์โค้ด": "barcode",
    "条码": "barcode",
    "qr": "qr_payload",
    "qr_payload": "qr_payload",
    "二维码": "qr_payload",
    "unit": "unit",
    "หน่วย": "unit",
    "单位": "unit",
    "unit_price": "unit_price",
    "price": "unit_price",
    "ราคา": "unit_price",
    "单价": "unit_price",
    "价格": "unit_price",
    "vat": "vat_applicable",
    "vat_applicable": "vat_applicable",
    "含税": "vat_applicable",
    "category_id": "category_id",
}

_TRUTHY = {"1", "true", "yes", "y", "ใช่", "是"}


def _norm_header(h: Any) -> str:
    return str(h).strip().lower() if h is not None else ""


def _to_bool(v: Any) -> bool:
    if isinstance(v, bool):
        return v
    return str(v).strip().lower() in _TRUTHY


def _to_price(v: Any) -> Decimal:
    try:
        p = Decimal(str(v).replace(",", "").strip())
    except (InvalidOperation, ValueError):
        raise ValueError("unit_price_not_number")
    if p < 0:
        raise ValueError("unit_price_negative")
    return p


def _is_blank(row) -> bool:
    return row is None or all(c is None or str(c).strip() == "" for c in row)


def parse_workbook(file_bytes: bytes) -> tuple[list[dict], list[dict]]:
    """解析 xlsx 字节 → (valid_rows, errors)。errors 每条 {row, error}。

    抛 ValueError(非 xlsx / 缺商品名列 / 空表)由路由层转 400。
    """
    try:
        wb = openpyxl.load_workbook(io.BytesIO(file_bytes), data_only=True, read_only=True)
    except Exception:
        raise ValueError("file_not_xlsx")
    try:
        ws = wb.active
        rows = ws.iter_rows(values_only=True)
        try:
            header = next(rows)
        except StopIteration:
            raise ValueError("empty_file")

        col_field = {}
        for idx, h in enumerate(header):
            field = _HEADER_ALIASES.get(_norm_header(h))
            if field:
                col_field[idx] = field
        if "name_th" not in col_field.values():
            raise ValueError("missing_name_column")

        valid: list[dict] = []
        errors: list[dict] = []
        for row_no, row in enumerate(rows, start=2):
            if _is_blank(row):
                continue
            try:
                valid.append(_build_record(row, col_field))
            except (ValueError, TypeError) as e:
                errors.append({"row": row_no, "error": str(e)})
        return valid, errors
    finally:
        wb.close()


def _build_record(row, col_field: dict) -> dict:
    rec: dict = {}
    for idx, field in col_field.items():
        if idx >= len(row):
            continue
        val = row[idx]
        if val is None or (isinstance(val, str) and not val.strip()):
            continue
        if field == "unit_price":
            rec[field] = _to_price(val)
        elif field == "vat_applicable":
            rec[field] = _to_bool(val)
        elif field == "category_id":
            rec[field] = int(val)
        else:
            rec[field] = str(val).strip()
    if not rec.get("name_th"):
        raise ValueError("name_th_required")
    return rec
