"""products 多单位/批次标志列 + product_units 表(POS 项目 · PO-A2 · docs/pos/03 §2)。

Revision ID: 0022_product_units_and_flags
Revises: 0021_tenant_modules
Create Date: 2026-06-07

库存/POS 的商品地基:products 加 6 列(都带默认 · 老数据不破)——base_unit(库存按它记)、
track_batch/track_expiry(批号/效期能力)、is_weighed(称重品)、min_stock(低库存阈值)、
default_cost(无批次时参考成本);新表 product_units 展开多单位/拆零换算(盒/板/粒 各自条码/售价)。
卖出一律换算成 base_unit 落账(factor_to_base)。能力块关时前端只用 base_unit,后端照存。

隔离:应用层 WHERE tenant_id(每条 DAL 语句)。product_units ENABLE RLS + policy 为未来最小
权限角色兜底(prod 角色 postgres BYPASSRLS · RLS 当前不强制 · 见 PO-A1 验证)。

Dual-run:services/products/units.ensure_schema() 跑同一幂等 DDL(prod 无自动迁移)。
"""

from alembic import op

revision = "0022_product_units_and_flags"
down_revision = "0021_tenant_modules"
branch_labels = None
depends_on = None

_ADD_COLS = (
    "ADD COLUMN IF NOT EXISTS base_unit text NOT NULL DEFAULT 'ชิ้น'",
    "ADD COLUMN IF NOT EXISTS track_batch boolean NOT NULL DEFAULT FALSE",
    "ADD COLUMN IF NOT EXISTS track_expiry boolean NOT NULL DEFAULT FALSE",
    "ADD COLUMN IF NOT EXISTS is_weighed boolean NOT NULL DEFAULT FALSE",
    "ADD COLUMN IF NOT EXISTS min_stock numeric(14,3)",
    "ADD COLUMN IF NOT EXISTS default_cost numeric(14,2)",
)

_DROP_COLS = (
    "default_cost",
    "min_stock",
    "is_weighed",
    "track_expiry",
    "track_batch",
    "base_unit",
)


def upgrade() -> None:
    for clause in _ADD_COLS:
        op.execute(f"ALTER TABLE products {clause}")
    op.execute("""
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
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_product_units_product "
        "ON product_units (tenant_id, product_id)"
    )
    op.execute("ALTER TABLE product_units ENABLE ROW LEVEL SECURITY")
    op.execute("DROP POLICY IF EXISTS tenant_isolation ON product_units")
    op.execute("""
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


def downgrade() -> None:
    op.execute("DROP POLICY IF EXISTS tenant_isolation ON product_units")
    op.execute("DROP TABLE IF EXISTS product_units")
    for col in _DROP_COLS:
        op.execute(f"ALTER TABLE products DROP COLUMN IF EXISTS {col}")
