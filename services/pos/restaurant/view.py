# -*- coding: utf-8 -*-
"""餐厅 POS 视图格式化小工具(POS 项目 · 共用 · docs/pos/restaurant/02)。

钱字符串化 numeric(14,2)、量字符串化 numeric(14,3)、菜名 4 语对象、UTC ISO、用餐分钟。前端按信封 data 读。
"""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal


def money(v) -> str:
    return f"{Decimal(str(v if v is not None else 0)):.2f}"


def qty(v) -> str:
    return f"{Decimal(str(v if v is not None else 0)):.3f}"


def name_obj(row) -> dict:
    return {"th": row.get("name_th"), "en": row.get("name_en"), "zh": row.get("name_zh")}


def iso(dt) -> str | None:
    return dt.isoformat() if dt else None


def minutes_since(dt) -> int:
    if not dt:
        return 0
    now = datetime.now(timezone.utc)
    delta = now - dt
    return max(0, int(delta.total_seconds() // 60))


def line_view(row) -> dict:
    """点单行(草稿/已下单)统一视图。"""
    return {
        "id": str(row["id"]),
        "product_id": str(row["product_id"]),
        "name": name_obj(row),
        "kot_id": str(row["kot_id"]) if row.get("kot_id") else None,
        "sell_unit": row.get("sell_unit"),
        "qty": qty(row["qty"]),
        "unit_price": money(row["unit_price"]),
        "line_discount": money(row["line_discount"]),
        "vat_applicable": row["vat_applicable"],
        "note": row.get("note"),
        "kitchen_status": row["kitchen_status"],
        "settled_sale_id": str(row["settled_sale_id"]) if row.get("settled_sale_id") else None,
        "line_total": money(row["line_total"]),
    }
