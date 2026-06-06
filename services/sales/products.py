# -*- coding: utf-8 -*-
"""销项商品主数据 DAL(PO-2 · docs/sales-module/docs/13)。

纯参数化 SQL 叶子:每个函数收路由层传入的 cursor + tenant_id。租户隔离双保险——
db.get_cursor_rls 设 app.current_tenant_id,这里每条语句再 WHERE tenant_id(镜像
services/knowledge/dal.py)。列名只来自内部白名单,值一律占位符,杜绝注入。
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any, Optional

_COLS = (
    "id, tenant_id, code, barcode, qr_payload, name_th, name_en, name_zh, "
    "unit, unit_price, vat_applicable, image_url, category_id, is_active, "
    "created_at, updated_at"
)

# create 可写列;update 额外允许 is_active(软删/恢复)。
_WRITABLE = (
    "code",
    "barcode",
    "qr_payload",
    "name_th",
    "name_en",
    "name_zh",
    "unit",
    "unit_price",
    "vat_applicable",
    "image_url",
    "category_id",
)
_UPDATABLE = _WRITABLE + ("is_active",)

# 查找键 → 列名白名单(值参数化 · 键不入 SQL 字符串拼接前先经此映射)。
_LOOKUP_COLS = {"code": "code", "barcode": "barcode", "qr": "qr_payload"}


def _money(v: Any) -> Any:
    """金额经 str 转 Decimal 存(避免 float 精度);非金额原样。"""
    return Decimal(str(v)) if v is not None else None


def create_product(cur, *, tenant_id: str, fields: dict) -> dict:
    cols = ["tenant_id"]
    vals: list = [tenant_id]
    for k in _WRITABLE:
        if fields.get(k) is not None:
            cols.append(k)
            vals.append(_money(fields[k]) if k == "unit_price" else fields[k])
    placeholders = ", ".join(["%s"] * len(vals))
    cur.execute(
        f"INSERT INTO products ({', '.join(cols)}) VALUES ({placeholders}) RETURNING {_COLS}",
        vals,
    )
    return cur.fetchone()


def get_product(cur, *, tenant_id: str, product_id: str) -> Optional[dict]:
    cur.execute(
        f"SELECT {_COLS} FROM products WHERE tenant_id = %s AND id = %s",
        (tenant_id, product_id),
    )
    return cur.fetchone()


def list_products(
    cur,
    *,
    tenant_id: str,
    include_inactive: bool = False,
    query: Optional[str] = None,
    limit: int = 200,
) -> list:
    sql = f"SELECT {_COLS} FROM products WHERE tenant_id = %s"
    params: list = [tenant_id]
    if not include_inactive:
        sql += " AND is_active = TRUE"
    if query:
        sql += " AND (name_th ILIKE %s OR name_en ILIKE %s OR name_zh ILIKE %s OR code ILIKE %s)"
        like = f"%{query}%"
        params += [like, like, like, like]
    sql += " ORDER BY name_th LIMIT %s"
    params.append(limit)
    cur.execute(sql, params)
    return cur.fetchall()


def update_product(cur, *, tenant_id: str, product_id: str, fields: dict) -> Optional[dict]:
    updates = {k: fields[k] for k in _UPDATABLE if fields.get(k) is not None}
    if not updates:
        return get_product(cur, tenant_id=tenant_id, product_id=product_id)
    sets = ", ".join(f"{k} = %s" for k in updates) + ", updated_at = now()"
    params = [_money(v) if k == "unit_price" else v for k, v in updates.items()]
    params += [tenant_id, product_id]
    cur.execute(
        f"UPDATE products SET {sets} WHERE tenant_id = %s AND id = %s RETURNING {_COLS}",
        params,
    )
    return cur.fetchone()


def deactivate_product(cur, *, tenant_id: str, product_id: str) -> bool:
    """软删:置 is_active=FALSE(不物删 · 保留已开票引用)。"""
    cur.execute(
        "UPDATE products SET is_active = FALSE, updated_at = now() "
        "WHERE tenant_id = %s AND id = %s",
        (tenant_id, product_id),
    )
    return cur.rowcount > 0


def find_by(cur, *, tenant_id: str, key: str, value: str) -> Optional[dict]:
    """按 code/barcode/qr 精确查在售商品(POS 点单/扫码快速带出)。"""
    col = _LOOKUP_COLS.get(key)
    if not col or not value:
        return None
    cur.execute(
        f"SELECT {_COLS} FROM products "
        f"WHERE tenant_id = %s AND {col} = %s AND is_active = TRUE LIMIT 1",
        (tenant_id, value),
    )
    return cur.fetchone()
