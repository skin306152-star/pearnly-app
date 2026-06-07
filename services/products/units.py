# -*- coding: utf-8 -*-
"""product_units DAL + products 多单位/批次列的双跑迁移(POS 项目 · PO-A2 · docs/pos/03 §2)。

多单位/拆零:1 product 多个售卖单位(盒/板/粒),各自 factor_to_base(换算成 base_unit)、
独立条码、可选售价。卖出/扣库存一律换算成 base_unit。能力块关时前端只用 base_unit,后端照存。

隔离:每条语句 WHERE tenant_id + 按 product_id 限定 + 全参数化。隔离硬保证 = 应用层 WHERE
(prod 角色 BYPASSRLS · 表上 RLS 仅兜底 · 见 [[pos-rls-bypass-app-layer-isolation]])。
"""

from __future__ import annotations

import logging
from decimal import Decimal
from typing import Any, Optional

logger = logging.getLogger("mr-pilot")

_UCOLS = (
    "id, tenant_id, product_id, unit_name, factor_to_base, barcode, price, "
    "is_default_sell, created_at, updated_at"
)
_UWRITABLE = ("unit_name", "factor_to_base", "barcode", "price", "is_default_sell")
# numeric 列经 str→Decimal 存(避免 float 精度)。
_NUMERIC = {"factor_to_base", "price"}

# products 表本次新增的 6 列(都带默认 · 老数据不破)。
_PRODUCT_COLS = (
    "ADD COLUMN IF NOT EXISTS base_unit text NOT NULL DEFAULT 'ชิ้น'",
    "ADD COLUMN IF NOT EXISTS track_batch boolean NOT NULL DEFAULT FALSE",
    "ADD COLUMN IF NOT EXISTS track_expiry boolean NOT NULL DEFAULT FALSE",
    "ADD COLUMN IF NOT EXISTS is_weighed boolean NOT NULL DEFAULT FALSE",
    "ADD COLUMN IF NOT EXISTS min_stock numeric(14,3)",
    "ADD COLUMN IF NOT EXISTS default_cost numeric(14,2)",
)


def ensure_schema() -> None:
    """幂等加 products 6 列 + 建 product_units + RLS(启动调 · 与 alembic 0022 双跑)。"""
    from core import db

    try:
        with db.get_cursor(commit=True) as cur:
            for clause in _PRODUCT_COLS:
                cur.execute(f"ALTER TABLE products {clause}")
            cur.execute("""
                CREATE TABLE IF NOT EXISTS product_units (
                    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
                    tenant_id uuid NOT NULL,
                    product_id uuid NOT NULL REFERENCES products(id) ON DELETE CASCADE,
                    unit_name text NOT NULL,
                    factor_to_base numeric(14,3) NOT NULL,
                    barcode text,
                    price numeric(14,2),
                    is_default_sell boolean NOT NULL DEFAULT FALSE,
                    created_at timestamptz NOT NULL DEFAULT now(),
                    updated_at timestamptz NOT NULL DEFAULT now(),
                    UNIQUE (tenant_id, product_id, unit_name)
                )
                """)
            cur.execute(
                "CREATE INDEX IF NOT EXISTS ix_product_units_product "
                "ON product_units (tenant_id, product_id)"
            )
            cur.execute("ALTER TABLE product_units ENABLE ROW LEVEL SECURITY")
            cur.execute("DROP POLICY IF EXISTS tenant_isolation ON product_units")
            cur.execute("""
                CREATE POLICY tenant_isolation ON product_units
                FOR ALL
                USING (
                    tenant_id::text = current_setting('app.current_tenant_id', true)
                    OR current_setting('app.bypass_rls', true) = 'on'
                )
                WITH CHECK (
                    tenant_id::text = current_setting('app.current_tenant_id', true)
                    OR current_setting('app.bypass_rls', true) = 'on'
                )
                """)
        logger.info("✅ products 多单位列 + product_units 表已就绪 (POS PO-A2)")
    except Exception as e:
        logger.warning(f"ensure_schema product_units 失败(跳过 · 等 alembic 0022): {e}")


def _num(v: Any) -> Any:
    return Decimal(str(v)) if v is not None else None


def list_units(cur, *, tenant_id: str, product_id: str) -> list:
    cur.execute(
        f"SELECT {_UCOLS} FROM product_units WHERE tenant_id = %s AND product_id = %s "
        f"ORDER BY factor_to_base",
        (tenant_id, product_id),
    )
    return cur.fetchall()


def get_unit(cur, *, tenant_id: str, product_id: str, unit_id: str) -> Optional[dict]:
    cur.execute(
        f"SELECT {_UCOLS} FROM product_units "
        f"WHERE tenant_id = %s AND product_id = %s AND id = %s",
        (tenant_id, product_id, unit_id),
    )
    return cur.fetchone()


def _clear_default(cur, *, tenant_id: str, product_id: str) -> None:
    """置某商品所有单位 is_default_sell=FALSE(设新默认前调 · 保证单一默认)。"""
    cur.execute(
        "UPDATE product_units SET is_default_sell = FALSE, updated_at = now() "
        "WHERE tenant_id = %s AND product_id = %s AND is_default_sell = TRUE",
        (tenant_id, product_id),
    )


def create_unit(cur, *, tenant_id: str, product_id: str, fields: dict) -> dict:
    if fields.get("is_default_sell"):
        _clear_default(cur, tenant_id=tenant_id, product_id=product_id)
    cols = ["tenant_id", "product_id"]
    vals: list = [tenant_id, product_id]
    for k in _UWRITABLE:
        if fields.get(k) is not None:
            cols.append(k)
            vals.append(_num(fields[k]) if k in _NUMERIC else fields[k])
    placeholders = ", ".join(["%s"] * len(vals))
    cur.execute(
        f"INSERT INTO product_units ({', '.join(cols)}) VALUES ({placeholders}) "
        f"RETURNING {_UCOLS}",
        vals,
    )
    return cur.fetchone()


def update_unit(
    cur, *, tenant_id: str, product_id: str, unit_id: str, fields: dict
) -> Optional[dict]:
    updates = {k: fields[k] for k in _UWRITABLE if fields.get(k) is not None}
    if not updates:
        return get_unit(cur, tenant_id=tenant_id, product_id=product_id, unit_id=unit_id)
    if updates.get("is_default_sell"):
        _clear_default(cur, tenant_id=tenant_id, product_id=product_id)
    sets = ", ".join(f"{k} = %s" for k in updates) + ", updated_at = now()"
    params = [_num(v) if k in _NUMERIC else v for k, v in updates.items()]
    params += [tenant_id, product_id, unit_id]
    cur.execute(
        f"UPDATE product_units SET {sets} "
        f"WHERE tenant_id = %s AND product_id = %s AND id = %s RETURNING {_UCOLS}",
        params,
    )
    return cur.fetchone()


def delete_unit(cur, *, tenant_id: str, product_id: str, unit_id: str) -> bool:
    """硬删单位(product_units 无引用历史 · 直接删行)。"""
    cur.execute(
        "DELETE FROM product_units WHERE tenant_id = %s AND product_id = %s AND id = %s",
        (tenant_id, product_id, unit_id),
    )
    return cur.rowcount > 0
