# -*- coding: utf-8 -*-
"""POS/库存性能索引(C2 · docs/pos/04 §4)。

热查询索引加固。绝大多数路径在 A3/B2 已建索引(pos_sales sold_at/shift/receipt、
inventory_transactions ix_txn_product、inventory_batches fefo、inventory_stock uq_*);
唯一缺口:inventory_stock 的唯一索引以 product 打头、不含 workspace_client_id,而
stock_overview/近效期/库存报表都按 (tenant, workspace) 过滤后聚合 → 大库会全租户扫。
本迁移补 (tenant_id, workspace_client_id, product_id) 前缀索引。

与 services/inventory/store.py ensure_schema 双跑(prod 走 bootstrap_pos_schema · 见
[[pos-pob4-b5-b6-shipped]]);CREATE INDEX IF NOT EXISTS 幂等。

Revision ID: 0026_pos_perf_indexes
Revises: 0025_pos_sales
"""

from alembic import op

revision = "0026_pos_perf_indexes"
down_revision = "0025_pos_sales"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_stock_ws_product "
        "ON inventory_stock (tenant_id, workspace_client_id, product_id)"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_stock_ws_product")
