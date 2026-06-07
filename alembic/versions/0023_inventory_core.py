"""库存核心:warehouses + inventory_batches + inventory_stock + inventory_transactions
(POS 项目 · PO-A3 · docs/pos/03 §3)。

Revision ID: 0023_inventory_core
Revises: 0022_product_units_and_flags
Create Date: 2026-06-07

库存唯一真理 = inventory_transactions(immutable 流水);inventory_stock 是它的物化结果,
与流水同事务更新(改库存=记一笔冲销,不改历史)。批次品按 inventory_batches(FEFO 排序键
expiry_date)。离线幂等:transactions.client_uuid UNIQUE(端上生成 · 重复补传不重复扣)。

外键类型对齐现有混合(03 §0):tenant_id/product_id/batch_id=uuid;workspace_client_id/
warehouse_id=bigint。stock 的 (product,warehouse,batch) 唯一靠两条 partial unique index
(NULL batch 与非 NULL 分别约束 · 因 SQL NULL 在普通 UNIQUE 里互不相等)。

隔离硬保证 = 应用层 WHERE tenant_id(每条 DAL 语句);ENABLE RLS + policy 为未来最小权限角色
兜底(prod 角色 postgres BYPASSRLS · RLS 当前不强制 · 见 PO-A1 验证)。
Dual-run:services/inventory/store.ensure_schema() 跑同一幂等 DDL(prod 无自动迁移)。
"""

from alembic import op

revision = "0023_inventory_core"
down_revision = "0022_product_units_and_flags"
branch_labels = None
depends_on = None

_RLS_TABLES = (
    "warehouses",
    "inventory_batches",
    "inventory_stock",
    "inventory_transactions",
)


def _policy(table: str) -> str:
    return f"""
        CREATE POLICY tenant_isolation ON {table}
        FOR ALL
        USING (
            tenant_id::text = current_setting('app.current_tenant_id', true)
            OR current_setting('app.bypass_rls', true) = 'on'
        )
        WITH CHECK (
            tenant_id::text = current_setting('app.current_tenant_id', true)
            OR current_setting('app.bypass_rls', true) = 'on'
        )
    """


def upgrade() -> None:
    op.execute("""
        CREATE TABLE IF NOT EXISTS warehouses (
            id bigserial PRIMARY KEY,
            tenant_id uuid NOT NULL,
            workspace_client_id bigint NOT NULL,
            name text NOT NULL DEFAULT 'ร้าน',
            is_default boolean NOT NULL DEFAULT FALSE,
            is_active boolean NOT NULL DEFAULT TRUE,
            created_at timestamptz NOT NULL DEFAULT now(),
            updated_at timestamptz NOT NULL DEFAULT now()
        )
        """)
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_warehouses_ws "
        "ON warehouses (tenant_id, workspace_client_id)"
    )
    op.execute("""
        CREATE TABLE IF NOT EXISTS inventory_batches (
            id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id uuid NOT NULL,
            product_id uuid NOT NULL REFERENCES products(id) ON DELETE CASCADE,
            batch_no text NOT NULL,
            expiry_date date,
            received_at date NOT NULL DEFAULT CURRENT_DATE,
            unit_cost numeric(14,2),
            created_at timestamptz NOT NULL DEFAULT now(),
            UNIQUE (tenant_id, product_id, batch_no)
        )
        """)
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_batches_fefo "
        "ON inventory_batches (tenant_id, product_id, expiry_date)"
    )
    op.execute("""
        CREATE TABLE IF NOT EXISTS inventory_stock (
            id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id uuid NOT NULL,
            workspace_client_id bigint NOT NULL,
            product_id uuid NOT NULL REFERENCES products(id) ON DELETE CASCADE,
            warehouse_id bigint NOT NULL REFERENCES warehouses(id) ON DELETE CASCADE,
            batch_id uuid REFERENCES inventory_batches(id) ON DELETE CASCADE,
            qty_on_hand numeric(14,3) NOT NULL DEFAULT 0,
            qty_reserved numeric(14,3) NOT NULL DEFAULT 0,
            updated_at timestamptz NOT NULL DEFAULT now()
        )
        """)
    # NULL batch 与非 NULL 分别唯一(SQL NULL 在普通 UNIQUE 里互不相等 → 用两条 partial index)。
    op.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS uq_stock_batched "
        "ON inventory_stock (tenant_id, product_id, warehouse_id, batch_id) "
        "WHERE batch_id IS NOT NULL"
    )
    op.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS uq_stock_nobatch "
        "ON inventory_stock (tenant_id, product_id, warehouse_id) "
        "WHERE batch_id IS NULL"
    )
    op.execute("""
        CREATE TABLE IF NOT EXISTS inventory_transactions (
            id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id uuid NOT NULL,
            workspace_client_id bigint NOT NULL,
            product_id uuid NOT NULL REFERENCES products(id) ON DELETE CASCADE,
            warehouse_id bigint NOT NULL REFERENCES warehouses(id) ON DELETE CASCADE,
            batch_id uuid REFERENCES inventory_batches(id) ON DELETE SET NULL,
            txn_type text NOT NULL,
            qty_delta numeric(14,3) NOT NULL,
            unit_cost numeric(14,2),
            ref_type text,
            ref_id uuid,
            client_uuid uuid UNIQUE,
            reason text,
            created_by uuid,
            created_at timestamptz NOT NULL DEFAULT now()
        )
        """)
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_txn_product "
        "ON inventory_transactions (tenant_id, workspace_client_id, product_id, created_at)"
    )
    for table in _RLS_TABLES:
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
        op.execute(f"DROP POLICY IF EXISTS tenant_isolation ON {table}")
        op.execute(_policy(table))


def downgrade() -> None:
    for table in reversed(_RLS_TABLES):
        op.execute(f"DROP POLICY IF EXISTS tenant_isolation ON {table}")
    op.execute("DROP TABLE IF EXISTS inventory_transactions")
    op.execute("DROP TABLE IF EXISTS inventory_stock")
    op.execute("DROP TABLE IF EXISTS inventory_batches")
    op.execute("DROP TABLE IF EXISTS warehouses")
