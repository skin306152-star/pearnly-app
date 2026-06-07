"""POS 核心:pos_terminals + pos_cashiers + pos_shifts(POS 项目 · PO-B1 · docs/pos/03 §4)。

Revision ID: 0024_pos_core
Revises: 0023_inventory_core
Create Date: 2026-06-07

收银员体系:role=cashier 经 PIN 登录(pos_cashiers.pin_hash · bcrypt · 绝不存明文)。班次
pos_shifts 记开/交班与日结现金差异。一个终端同时只允许一个 open 班次,靠 partial unique index
(status='open')在 DB 级兜底("已有未结束班次"=pos.shift_already_open)。

外键类型对齐现有混合(03 §0/§7):tenant_id/cashier_id/user_id=uuid;workspace_client_id/
terminal_id=bigint。隔离硬保证 = 应用层 WHERE tenant_id(每条 DAL 语句);ENABLE RLS + policy
为未来最小权限角色兜底(prod 角色 postgres BYPASSRLS · RLS 当前不强制)。
Dual-run:services/pos/cashier.ensure_core_schema() 跑同一幂等 DDL(prod 无自动迁移)。
"""

from alembic import op

revision = "0024_pos_core"
down_revision = "0023_inventory_core"
branch_labels = None
depends_on = None

_RLS_TABLES = ("pos_terminals", "pos_cashiers", "pos_shifts")


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
        CREATE TABLE IF NOT EXISTS pos_terminals (
            id bigserial PRIMARY KEY,
            tenant_id uuid NOT NULL,
            workspace_client_id bigint NOT NULL,
            name text NOT NULL DEFAULT 'แคชเชียร์ 1',
            is_active boolean NOT NULL DEFAULT TRUE,
            created_at timestamptz NOT NULL DEFAULT now(),
            updated_at timestamptz NOT NULL DEFAULT now()
        )
        """)
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_pos_terminals_ws "
        "ON pos_terminals (tenant_id, workspace_client_id)"
    )
    op.execute("""
        CREATE TABLE IF NOT EXISTS pos_cashiers (
            id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id uuid NOT NULL,
            workspace_client_id bigint NOT NULL,
            user_id uuid REFERENCES users(id) ON DELETE SET NULL,
            display_name text NOT NULL,
            pin_hash text NOT NULL,
            color text,
            is_active boolean NOT NULL DEFAULT TRUE,
            created_at timestamptz NOT NULL DEFAULT now(),
            updated_at timestamptz NOT NULL DEFAULT now()
        )
        """)
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_pos_cashiers_ws "
        "ON pos_cashiers (tenant_id, workspace_client_id)"
    )
    op.execute("""
        CREATE TABLE IF NOT EXISTS pos_shifts (
            id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id uuid NOT NULL,
            workspace_client_id bigint NOT NULL,
            terminal_id bigint NOT NULL REFERENCES pos_terminals(id) ON DELETE CASCADE,
            cashier_id uuid NOT NULL REFERENCES pos_cashiers(id) ON DELETE CASCADE,
            opened_at timestamptz NOT NULL DEFAULT now(),
            closed_at timestamptz,
            opening_float numeric(14,2) NOT NULL DEFAULT 0,
            expected_cash numeric(14,2),
            counted_cash numeric(14,2),
            cash_diff numeric(14,2),
            status text NOT NULL DEFAULT 'open',
            created_at timestamptz NOT NULL DEFAULT now()
        )
        """)
    # 一个终端同时只能有一个 open 班次(DB 级兜底 pos.shift_already_open)。
    op.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS uq_pos_shift_open "
        "ON pos_shifts (tenant_id, terminal_id) WHERE status = 'open'"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_pos_shifts_cashier "
        "ON pos_shifts (tenant_id, cashier_id, status)"
    )
    for table in _RLS_TABLES:
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
        op.execute(f"DROP POLICY IF EXISTS tenant_isolation ON {table}")
        op.execute(_policy(table))


def downgrade() -> None:
    for table in reversed(_RLS_TABLES):
        op.execute(f"DROP POLICY IF EXISTS tenant_isolation ON {table}")
    op.execute("DROP TABLE IF EXISTS pos_shifts")
    op.execute("DROP TABLE IF EXISTS pos_cashiers")
    op.execute("DROP TABLE IF EXISTS pos_terminals")
