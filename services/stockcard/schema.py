# -*- coding: utf-8 -*-
"""商品收发存报表 schema 双跑入口(启动调一次 · 与 alembic 0097 同源幂等 DDL)。

prod 无自动迁移钩子 → startup 经 ensure_stock_card_schema() 幂等建表(与 services/purchase/
schema.py 同款范式)。DDL 与迁移逐字对齐(改一处必同改两处)。失败仅告警不 raise(不挡主服务)。
纯 tenant RLS(仓库实证:含 workspace_client_id 的表统一走纯 tenant policy,应用层
WHERE tenant_id+workspace_client_id 才是隔离主力,见 0059/0064 同款先例)。
"""

from __future__ import annotations

import logging

from core.rls import apply_tenant_rls

logger = logging.getLogger("mr-pilot")

_TABLE = """
    CREATE TABLE IF NOT EXISTS stock_card_openings (
        id bigserial PRIMARY KEY,
        tenant_id uuid NOT NULL,
        workspace_client_id bigint NOT NULL,
        product_id uuid,
        name_key text,
        qty numeric(14,3) NOT NULL,
        unit_cost numeric(14,2) NOT NULL,
        as_of_date date NOT NULL,
        created_by uuid,
        created_at timestamptz NOT NULL DEFAULT now(),
        updated_at timestamptz NOT NULL DEFAULT now(),
        CONSTRAINT ck_stock_card_openings_identity CHECK (
            (product_id IS NOT NULL AND name_key IS NULL) OR
            (product_id IS NULL AND name_key IS NOT NULL)
        )
    )
    """

_INDEXES = (
    "CREATE UNIQUE INDEX IF NOT EXISTS uq_stock_card_openings_product "
    "ON stock_card_openings (tenant_id, workspace_client_id, product_id) "
    "WHERE product_id IS NOT NULL",
    "CREATE UNIQUE INDEX IF NOT EXISTS uq_stock_card_openings_name "
    "ON stock_card_openings (tenant_id, workspace_client_id, name_key) "
    "WHERE name_key IS NOT NULL",
    "CREATE INDEX IF NOT EXISTS ix_stock_card_openings_ws "
    "ON stock_card_openings (tenant_id, workspace_client_id)",
)

_RLS_TABLES = ("stock_card_openings",)


def ensure_stock_card_schema() -> None:
    """幂等建期初表 + 索引 + RLS(startup 调 · 与 alembic 0097 双跑)。"""
    from core import db

    with db.get_cursor(commit=True) as cur:
        cur.execute(_TABLE)
        for idx in _INDEXES:
            cur.execute(idx)
        apply_tenant_rls(cur, *_RLS_TABLES)
