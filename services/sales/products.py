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
    "unit, unit_price, vat_applicable, image_url, category_id, "
    "base_unit, track_batch, track_expiry, is_weighed, min_stock, default_cost, "
    "is_active, created_at, updated_at"
)

# create 可写列;update 额外允许 is_active(软删/恢复)。
# 末 6 列为 POS PO-A2 库存地基(base_unit/批次效期/称重/低库存阈值/参考成本)。
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
    "base_unit",
    "track_batch",
    "track_expiry",
    "is_weighed",
    "min_stock",
    "default_cost",
)
_UPDATABLE = _WRITABLE + ("is_active",)

# numeric 列经 str→Decimal 存(避免 float 精度)。
_NUMERIC = {"unit_price", "min_stock", "default_cost"}

# 查找键 → 列名白名单(值参数化 · 键不入 SQL 字符串拼接前先经此映射)。
_LOOKUP_COLS = {"code": "code", "barcode": "barcode", "qr": "qr_payload"}


def _money(v: Any) -> Any:
    """金额经 str 转 Decimal 存(避免 float 精度);非金额原样。"""
    return Decimal(str(v)) if v is not None else None


def _norm_code(fields: dict) -> dict:
    """唯一键 code 空白归一为 NULL:留空商品不进唯一索引(uq_products_tenant_code
    WHERE code IS NOT NULL),否则多个"无编码"商品都存空串会撞唯一约束。非空则去首尾空白。"""
    code = fields.get("code")
    if not isinstance(code, str):
        return fields
    f = dict(fields)
    f["code"] = code.strip() or None
    return f


def _revive_soft_deleted(cur, *, tenant_id: str, fields: dict) -> Optional[dict]:
    """新建商品的编码撞到一条【已软删】(is_active=FALSE)同编码记录时复活它并用新内容覆盖。

    软删保留已开票引用,但 uq_products_tenant_code(WHERE code IS NOT NULL)跨 active+inactive
    去重 → 同编码全表至多 1 条,故撞到软删的必无在售同码,复活安全。否则用户删了某编码后
    永远无法再用该编码(列表又看不到死记录,提示"已存在"令人困惑)。无编码或撞在售时返 None,
    走正常 INSERT(在售冲突由唯一约束 → 路由翻 product_code_exists)。"""
    code = fields.get("code")
    if not code:
        return None
    cur.execute(
        "SELECT id FROM products WHERE tenant_id = %s AND code = %s AND is_active = FALSE",
        (tenant_id, code),
    )
    dead = cur.fetchone()
    if not dead:
        return None
    sets = ["is_active = TRUE"]
    vals: list = []
    for k in _WRITABLE:
        if fields.get(k) is not None:
            sets.append(f"{k} = %s")
            vals.append(_money(fields[k]) if k in _NUMERIC else fields[k])
    sets.append("updated_at = now()")
    cur.execute(
        f"UPDATE products SET {', '.join(sets)} WHERE tenant_id = %s AND id = %s RETURNING {_COLS}",
        vals + [tenant_id, dead["id"]],
    )
    return cur.fetchone()


def create_product(cur, *, tenant_id: str, fields: dict) -> dict:
    fields = _norm_code(fields)
    revived = _revive_soft_deleted(cur, tenant_id=tenant_id, fields=fields)
    if revived is not None:
        return revived
    cols = ["tenant_id"]
    vals: list = [tenant_id]
    for k in _WRITABLE:
        if fields.get(k) is not None:
            cols.append(k)
            vals.append(_money(fields[k]) if k in _NUMERIC else fields[k])
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
    fields = _norm_code(fields)
    updates = {k: fields[k] for k in _UPDATABLE if fields.get(k) is not None}
    if not updates:
        return get_product(cur, tenant_id=tenant_id, product_id=product_id)
    sets = ", ".join(f"{k} = %s" for k in updates) + ", updated_at = now()"
    params = [_money(v) if k in _NUMERIC else v for k, v in updates.items()]
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
