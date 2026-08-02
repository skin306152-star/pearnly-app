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

from core.rls import apply_tenant_rls

logger = logging.getLogger("mr-pilot")

_UCOLS = (
    "id, tenant_id, product_id, unit_name, factor_to_base, barcode, price, "
    "is_default_sell, created_at, updated_at"
)
_UWRITABLE = ("unit_name", "factor_to_base", "barcode", "price", "is_default_sell")
# 可空列:PATCH 收到显式 None = 清空,得真写 NULL(箱码印错了要能删掉,不能只能改成别的码)。
# 其余是 NOT NULL 列,None 只可能是"这次没传"。路由层用 exclude_unset 保证键=客户端真发过。
NULLABLE_UNIT_FIELDS = {"barcode", "price"}
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
            # 全新库:建表即带 workspace_client_id(套账隔离硬列 · DAL 全列读写)。
            cur.execute("""
                CREATE TABLE IF NOT EXISTS product_units (
                    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
                    tenant_id uuid NOT NULL,
                    workspace_client_id bigint NOT NULL,
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
            # 既有库(本列之前建的表):幂等补列 + 从 products 回填,再补索引。NOT NULL 收口走 alembic 0030
            # (回填后),此处保持可空以免老库有孤儿行时启动失败。
            cur.execute(
                "ALTER TABLE product_units ADD COLUMN IF NOT EXISTS workspace_client_id bigint"
            )
            cur.execute(
                "UPDATE product_units pu SET workspace_client_id = p.workspace_client_id "
                "FROM products p WHERE p.id = pu.product_id AND pu.workspace_client_id IS NULL"
            )
            cur.execute(
                "CREATE INDEX IF NOT EXISTS ix_product_units_ws "
                "ON product_units (tenant_id, workspace_client_id, product_id)"
            )
            apply_tenant_rls(cur, "product_units")
        logger.info("✅ products 多单位列 + product_units 表已就绪 (POS PO-A2)")
    except Exception as e:
        logger.warning(f"ensure_schema product_units 失败(跳过 · 等 alembic 0022/0030): {e}")
    _apply_price_nullability()
    _apply_barcode_uniqueness()


def _apply_price_nullability() -> None:
    """products.unit_price 去 NOT NULL/DEFAULT 0(alembic 0093 双跑 · prod 不跑 alembic)。

    单开事务:这一条失败不该连累建索引那条,反过来也一样。失败按 error 记——列还带着
    DEFAULT 0 时"没设价"照旧静默变成 ฿0,收银台的零元闸对它毫无办法,不能只当个 warning。
    """
    from core import db
    from services.sales import products as products_dal

    try:
        with db.get_cursor(commit=True) as cur:
            products_dal.relax_price_not_null(cur)
    except Exception as e:
        logger.error(f"unit_price 仍是 NOT NULL:没设价会落成 ฿0(等 alembic 0093): {e}")


def _apply_barcode_uniqueness() -> None:
    """条码部分唯一索引(alembic 0092/0093 双跑 · prod 不跑 alembic)。

    单开一个事务:存量真有重码时 CREATE UNIQUE INDEX 会报错,混在上面那段里会把
    product_units 建表一起回滚掉。有冲突时不建索引但按 error 记清冲突组——静默跳过等于
    让人以为已经拦住了,而撞码要到收银台才暴露。

    补列必须在体检之前:体检按 product_active 归组(只看在售商品的单位行),列不在直接报错。
    """
    from core import db
    from services.sales import products as products_dal

    try:
        with db.get_cursor(commit=True) as cur:
            products_dal.ensure_unit_visibility_column(cur)
            conflicts = products_dal.barcode_conflicts(cur)
            dirty = {t: g for t, g in conflicts.items() if g}
            if dirty:
                logger.error(f"条码唯一索引未建:存量有重复条码待清理 {dirty}")
                return
            products_dal.create_barcode_unique_indexes(cur)
    except Exception as e:
        logger.warning(f"条码唯一索引未建(等 alembic 0092/0093): {e}")


def _num(v: Any) -> Any:
    return Decimal(str(v)) if v is not None else None


def list_units(cur, *, tenant_id: str, workspace_client_id: int, product_id: str) -> list:
    cur.execute(
        f"SELECT {_UCOLS} FROM product_units "
        f"WHERE tenant_id = %s AND workspace_client_id = %s AND product_id = %s "
        f"ORDER BY factor_to_base",
        (tenant_id, workspace_client_id, product_id),
    )
    return cur.fetchall()


def get_unit(
    cur, *, tenant_id: str, workspace_client_id: int, product_id: str, unit_id: str
) -> Optional[dict]:
    cur.execute(
        f"SELECT {_UCOLS} FROM product_units "
        f"WHERE tenant_id = %s AND workspace_client_id = %s AND product_id = %s AND id = %s",
        (tenant_id, workspace_client_id, product_id, unit_id),
    )
    return cur.fetchone()


def _clear_default(cur, *, tenant_id: str, workspace_client_id: int, product_id: str) -> None:
    """置某商品所有单位 is_default_sell=FALSE(设新默认前调 · 保证单一默认)。"""
    cur.execute(
        "UPDATE product_units SET is_default_sell = FALSE, updated_at = now() "
        "WHERE tenant_id = %s AND workspace_client_id = %s AND product_id = %s "
        "AND is_default_sell = TRUE",
        (tenant_id, workspace_client_id, product_id),
    )


def create_unit(
    cur, *, tenant_id: str, workspace_client_id: int, product_id: str, fields: dict
) -> dict:
    if fields.get("is_default_sell"):
        _clear_default(
            cur, tenant_id=tenant_id, workspace_client_id=workspace_client_id, product_id=product_id
        )
    cols = ["tenant_id", "workspace_client_id", "product_id"]
    vals: list = [tenant_id, workspace_client_id, product_id]
    for k in _UWRITABLE:
        if fields.get(k) is not None:
            cols.append(k)
            vals.append(_num(fields[k]) if k in _NUMERIC else fields[k])
    placeholders = ", ".join(["%s"] * len(vals))
    cur.execute(
        f"INSERT INTO product_units ({', '.join(cols)}) VALUES ({placeholders}) RETURNING {_UCOLS}",
        vals,
    )
    row = cur.fetchone()
    _sync_product_active(cur, tenant_id=tenant_id, unit_id=row["id"])
    return row


def _sync_product_active(cur, *, tenant_id: str, unit_id) -> None:
    """新单位行的"所属商品在售"标记按商品当前状态落(默认值 TRUE 只对在售商品才对)。

    单位可以挂到已停用的商品上("含停用"列表里点进去,给下次上架先把箱码配好)。默认 TRUE
    的话这行立刻占着码,而查重那边(services/sales/products.find_by)筛掉了不在售的商品,
    一律回"没人用" —— 僵尸码就是这么长出来的:绿字放行,真存撞唯一索引,占码的看不见。
    """
    cur.execute(
        "UPDATE product_units pu SET product_active = p.is_active FROM products p "
        "WHERE p.id = pu.product_id AND pu.tenant_id = %s AND pu.id = %s "
        "AND pu.product_active IS DISTINCT FROM p.is_active",
        (tenant_id, unit_id),
    )


def update_unit(
    cur, *, tenant_id: str, workspace_client_id: int, product_id: str, unit_id: str, fields: dict
) -> Optional[dict]:
    updates = {
        k: fields[k]
        for k in _UWRITABLE
        if k in fields and (fields[k] is not None or k in NULLABLE_UNIT_FIELDS)
    }
    if not updates:
        return get_unit(
            cur,
            tenant_id=tenant_id,
            workspace_client_id=workspace_client_id,
            product_id=product_id,
            unit_id=unit_id,
        )
    if updates.get("is_default_sell"):
        _clear_default(
            cur, tenant_id=tenant_id, workspace_client_id=workspace_client_id, product_id=product_id
        )
    sets = ", ".join(f"{k} = %s" for k in updates) + ", updated_at = now()"
    params = [_num(v) if k in _NUMERIC else v for k, v in updates.items()]
    params += [tenant_id, workspace_client_id, product_id, unit_id]
    cur.execute(
        f"UPDATE product_units SET {sets} "
        f"WHERE tenant_id = %s AND workspace_client_id = %s AND product_id = %s AND id = %s "
        f"RETURNING {_UCOLS}",
        params,
    )
    return cur.fetchone()


def delete_unit(
    cur, *, tenant_id: str, workspace_client_id: int, product_id: str, unit_id: str
) -> bool:
    """硬删单位(product_units 无引用历史 · 直接删行)。"""
    cur.execute(
        "DELETE FROM product_units "
        "WHERE tenant_id = %s AND workspace_client_id = %s AND product_id = %s AND id = %s",
        (tenant_id, workspace_client_id, product_id, unit_id),
    )
    return cur.rowcount > 0
