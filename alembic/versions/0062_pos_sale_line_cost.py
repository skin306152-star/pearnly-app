# -*- coding: utf-8 -*-
"""POS 销售行成本快照(POS 报表毛利 · docs/pos/04 §7 补)。

Revision ID: 0062_pos_sale_line_cost
Revises: 0061_supplier_posting_profiles
Create Date: 2026-07-10

pos_sale_lines 新增 cost_total(numeric(14,2) · 可空):卖出扣库存那一刻的 COGS 快照,
按实际扣减的批次/散装成本算(services/pos/stock.cost_for_moves),不是报表期现算——避免
批次成本事后被改单据历史失真。NULL = 未知成本(老单据/无进货成本记录),报表须诚实置空,
不得当 0。Dual-run:services/pos/sales_store.ensure_sales_schema() 跑同一幂等 DDL。
"""

from alembic import op

revision = "0062_pos_sale_line_cost"
down_revision = "0061_supplier_posting_profiles"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TABLE pos_sale_lines ADD COLUMN IF NOT EXISTS cost_total numeric(14,2)")


def downgrade() -> None:
    op.execute("ALTER TABLE pos_sale_lines DROP COLUMN IF EXISTS cost_total")
