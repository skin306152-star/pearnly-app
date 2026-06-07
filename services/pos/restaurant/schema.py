# -*- coding: utf-8 -*-
"""餐厅 POS schema 双跑(POS 项目 · PO-R1 · 与 alembic 0027 同源幂等 DDL · docs/pos/restaurant/01)。

prod 无自动迁移,startup 经 bootstrap_pos_schema 跑这里;DDL 与 0027_restaurant_core 逐字一致。建表顺序:
区域 → 桌台 → session → KOT → 点单行(行 FK 依赖 session/KOT/products/pos_sales)。RLS policy 经
core.rls 单一来源。pos_sales.service_charge 加列(零售恒 0,不破坏)。
"""

from __future__ import annotations

import logging

from core.rls import apply_tenant_rls

logger = logging.getLogger("mr-pilot")

_RLS_TABLES = (
    "pos_areas",
    "pos_tables",
    "pos_table_sessions",
    "pos_session_lines",
    "pos_kot",
)


def ensure_restaurant_schema() -> None:
    from core import db

    try:
        with db.get_cursor(commit=True) as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS pos_areas (
                    id bigserial PRIMARY KEY,
                    tenant_id uuid NOT NULL,
                    workspace_client_id bigint NOT NULL,
                    name text NOT NULL,
                    sort int NOT NULL DEFAULT 0,
                    is_active boolean NOT NULL DEFAULT TRUE,
                    created_at timestamptz NOT NULL DEFAULT now(),
                    updated_at timestamptz NOT NULL DEFAULT now()
                )
                """)
            cur.execute(
                "CREATE INDEX IF NOT EXISTS ix_pos_areas_ws "
                "ON pos_areas (tenant_id, workspace_client_id)"
            )
            cur.execute("""
                CREATE TABLE IF NOT EXISTS pos_tables (
                    id bigserial PRIMARY KEY,
                    tenant_id uuid NOT NULL,
                    workspace_client_id bigint NOT NULL,
                    area_id bigint REFERENCES pos_areas(id) ON DELETE SET NULL,
                    name text NOT NULL,
                    seats int NOT NULL DEFAULT 4,
                    sort int NOT NULL DEFAULT 0,
                    is_active boolean NOT NULL DEFAULT TRUE,
                    created_at timestamptz NOT NULL DEFAULT now(),
                    updated_at timestamptz NOT NULL DEFAULT now()
                )
                """)
            cur.execute(
                "CREATE UNIQUE INDEX IF NOT EXISTS uq_pos_tables_name "
                "ON pos_tables (tenant_id, workspace_client_id, name)"
            )
            cur.execute("""
                CREATE TABLE IF NOT EXISTS pos_table_sessions (
                    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
                    tenant_id uuid NOT NULL,
                    workspace_client_id bigint NOT NULL,
                    table_id bigint NOT NULL REFERENCES pos_tables(id) ON DELETE RESTRICT,
                    service_type text NOT NULL DEFAULT 'dine_in',
                    party_size int NOT NULL DEFAULT 1,
                    status text NOT NULL DEFAULT 'open',
                    opened_at timestamptz NOT NULL DEFAULT now(),
                    closed_at timestamptz,
                    cashier_id uuid REFERENCES pos_cashiers(id) ON DELETE SET NULL,
                    note text,
                    created_by uuid,
                    created_at timestamptz NOT NULL DEFAULT now()
                )
                """)
            cur.execute(
                "CREATE UNIQUE INDEX IF NOT EXISTS uq_table_open "
                "ON pos_table_sessions (tenant_id, table_id) WHERE status <> 'closed'"
            )
            cur.execute(
                "CREATE INDEX IF NOT EXISTS ix_pos_sessions_ws_status "
                "ON pos_table_sessions (tenant_id, workspace_client_id, status)"
            )
            cur.execute("""
                CREATE TABLE IF NOT EXISTS pos_kot (
                    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
                    tenant_id uuid NOT NULL,
                    workspace_client_id bigint NOT NULL,
                    session_id uuid NOT NULL REFERENCES pos_table_sessions(id) ON DELETE CASCADE,
                    ticket_no int NOT NULL,
                    sent_at timestamptz NOT NULL DEFAULT now(),
                    started_at timestamptz,
                    done_at timestamptz,
                    created_by uuid,
                    created_at timestamptz NOT NULL DEFAULT now()
                )
                """)
            cur.execute(
                "CREATE INDEX IF NOT EXISTS ix_pos_kot_ws_session "
                "ON pos_kot (tenant_id, workspace_client_id, session_id)"
            )
            cur.execute("""
                CREATE TABLE IF NOT EXISTS pos_session_lines (
                    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
                    tenant_id uuid NOT NULL,
                    session_id uuid NOT NULL REFERENCES pos_table_sessions(id) ON DELETE CASCADE,
                    kot_id uuid REFERENCES pos_kot(id) ON DELETE SET NULL,
                    product_id uuid NOT NULL REFERENCES products(id) ON DELETE RESTRICT,
                    sell_unit text,
                    unit_factor numeric(14,3) NOT NULL DEFAULT 1,
                    qty numeric(14,3) NOT NULL,
                    unit_price numeric(14,2) NOT NULL,
                    line_discount numeric(14,2) NOT NULL DEFAULT 0,
                    vat_applicable boolean NOT NULL DEFAULT TRUE,
                    note text,
                    kitchen_status text NOT NULL DEFAULT 'pending',
                    settled_sale_id uuid REFERENCES pos_sales(id) ON DELETE SET NULL,
                    created_by uuid,
                    created_at timestamptz NOT NULL DEFAULT now()
                )
                """)
            cur.execute(
                "CREATE INDEX IF NOT EXISTS ix_pos_session_lines_session "
                "ON pos_session_lines (tenant_id, session_id)"
            )
            cur.execute(
                "CREATE INDEX IF NOT EXISTS ix_pos_session_lines_kot "
                "ON pos_session_lines (tenant_id, kot_id)"
            )
            cur.execute(
                "ALTER TABLE pos_sales ADD COLUMN IF NOT EXISTS "
                "service_charge numeric(14,2) NOT NULL DEFAULT 0"
            )
            apply_tenant_rls(cur, *_RLS_TABLES)
        logger.info("✅ 餐厅 POS 5 表 + service_charge 加列 + RLS 已就绪 (POS PO-R1)")
    except Exception as e:
        logger.warning(f"ensure_restaurant_schema 失败(跳过 · 等 alembic 0027): {e}")
