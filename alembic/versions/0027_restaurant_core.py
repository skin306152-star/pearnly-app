"""餐厅 POS 核心:区域/桌台/开台 session/点单行/厨房单 KOT(POS 项目 · PO-R1 · docs/pos/restaurant/01)。

Revision ID: 0027_restaurant_core
Revises: 0026_pos_perf_indexes
Create Date: 2026-06-07

餐厅 = POS 第二业态,后端全新独立。pos_areas(区域)→ pos_tables(桌台)→ pos_table_sessions(开台挂账,
一桌一活动 session)→ pos_session_lines(多次点单 append · 兼 KOT 明细 · 逐项 kitchen_status)+
pos_kot(一次送厨房一张单)。埋单复用零售 pos_sales,仅加列 service_charge(服务费,零售恒 0)。

外键混合(对齐 03 §0/§7):tenant_id/session_id/kot_id/product_id/cashier_id/settled_sale_id=uuid;
workspace_client_id/table_id/area_id=bigint。钱 numeric(14,2)、量 numeric(14,3)。隔离=应用层
WHERE tenant_id;ENABLE RLS + policy 兜底。Dual-run:services/pos/restaurant/schema.ensure_restaurant_schema()
跑同一幂等 DDL(prod 无自动迁移)。
"""

from alembic import op

revision = "0027_restaurant_core"
down_revision = "0026_pos_perf_indexes"
branch_labels = None
depends_on = None

_RLS_TABLES = (
    "pos_areas",
    "pos_tables",
    "pos_table_sessions",
    "pos_session_lines",
    "pos_kot",
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
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_pos_areas_ws "
        "ON pos_areas (tenant_id, workspace_client_id)"
    )
    op.execute("""
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
    op.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS uq_pos_tables_name "
        "ON pos_tables (tenant_id, workspace_client_id, name)"
    )
    op.execute("""
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
    op.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS uq_table_open "
        "ON pos_table_sessions (tenant_id, table_id) WHERE status <> 'closed'"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_pos_sessions_ws_status "
        "ON pos_table_sessions (tenant_id, workspace_client_id, status)"
    )
    op.execute("""
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
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_pos_kot_ws_session "
        "ON pos_kot (tenant_id, workspace_client_id, session_id)"
    )
    op.execute("""
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
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_pos_session_lines_session "
        "ON pos_session_lines (tenant_id, session_id)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_pos_session_lines_kot "
        "ON pos_session_lines (tenant_id, kot_id)"
    )
    op.execute(
        "ALTER TABLE pos_sales ADD COLUMN IF NOT EXISTS "
        "service_charge numeric(14,2) NOT NULL DEFAULT 0"
    )
    for table in _RLS_TABLES:
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
        op.execute(f"DROP POLICY IF EXISTS tenant_isolation ON {table}")
        op.execute(_policy(table))


def downgrade() -> None:
    for table in reversed(_RLS_TABLES):
        op.execute(f"DROP POLICY IF EXISTS tenant_isolation ON {table}")
    op.execute("ALTER TABLE pos_sales DROP COLUMN IF EXISTS service_charge")
    op.execute("DROP TABLE IF EXISTS pos_session_lines")
    op.execute("DROP TABLE IF EXISTS pos_kot")
    op.execute("DROP TABLE IF EXISTS pos_table_sessions")
    op.execute("DROP TABLE IF EXISTS pos_tables")
    op.execute("DROP TABLE IF EXISTS pos_areas")
