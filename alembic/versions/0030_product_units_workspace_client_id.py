"""product_units 补 workspace_client_id(套账隔离修复 · POS-RO-001)。

Revision ID: 0030_product_units_workspace_client_id
Revises: 0029_pos_payment_settings
Create Date: 2026-06-08

修复 DDL 与运行时不一致:product_units 的建表(0022 + ensure_schema)从未含 workspace_client_id,
但 DAL(services/products/units.py · catalog.py)查询/插入/更新/删除全部按该列过滤——新库或未跑过
旧手册的库一碰拆零/多单位即 SQL 500。本迁移在已上线 prod 库补列 + 从 products 回填 + 收 NOT NULL +
按套账维度建索引。幂等(可重复跑)。Dual-run:units.ensure_schema() 跑同源幂等 DDL(prod 无自动迁移)。
"""

from alembic import op

revision = "0030_product_units_workspace_client_id"
down_revision = "0029_pos_payment_settings"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TABLE product_units ADD COLUMN IF NOT EXISTS workspace_client_id bigint")
    # 回填:product_units.product_id FK→products(CASCADE),每行必有归属商品,取其套账。
    op.execute(
        "UPDATE product_units pu SET workspace_client_id = p.workspace_client_id "
        "FROM products p WHERE p.id = pu.product_id AND pu.workspace_client_id IS NULL"
    )
    op.execute("ALTER TABLE product_units ALTER COLUMN workspace_client_id SET NOT NULL")
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_product_units_ws "
        "ON product_units (tenant_id, workspace_client_id, product_id)"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_product_units_ws")
    op.execute("ALTER TABLE product_units DROP COLUMN IF EXISTS workspace_client_id")
