"""Pearnly AI 工单制(M0 数据地基):work_orders + events/items/deliverables 4 表。

Revision ID: 0059_workorder_core
Revises: 0058_pos_sheets_settings
Create Date: 2026-07-09

一条命令把客户一期原始资料跑成「待签申报 + 底稿 + 证据链」(桌面 pearnly ai/
M0-施工任务包-v1.md §3)。work_orders 每客户每期一张(唯一约束 tenant+账套+期间+
意图,重复开单幂等返回既有单);其余三表挂在 work_order_id 下面。work_order_events
只追加(证据链底座 + 断点续跑恢复源),DAL 层不给它 UPDATE/DELETE。四表统一纯 tenant
RLS(仓库实证:apply_tenant_workspace_rls 虽存在但零表采用,见 b8-rls-HANDOFF §7.15.2)。
Dual-run:services/workorder/schema.ensure_workorder_schema() 同源幂等 DDL。
"""

from alembic import op

revision = "0059_workorder_core"
down_revision = "0058_pos_sheets_settings"
branch_labels = None
depends_on = None

_RLS = """
    ALTER TABLE {t} ENABLE ROW LEVEL SECURITY;
    DROP POLICY IF EXISTS tenant_isolation ON {t};
    CREATE POLICY tenant_isolation ON {t}
    FOR ALL
    USING (
        tenant_id::text = current_setting('app.current_tenant_id', true)
        OR current_setting('app.bypass_rls', true) = 'on'
    )
    WITH CHECK (
        tenant_id::text = current_setting('app.current_tenant_id', true)
        OR current_setting('app.bypass_rls', true) = 'on'
    );
"""


def upgrade() -> None:
    op.execute("""
        CREATE TABLE IF NOT EXISTS work_orders (
            id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id uuid NOT NULL,
            workspace_client_id bigint NOT NULL,
            period text NOT NULL,
            intent text NOT NULL DEFAULT 'monthly_vat',
            status text NOT NULL DEFAULT 'collecting',
            current_step text,
            created_at timestamptz NOT NULL DEFAULT now(),
            updated_at timestamptz NOT NULL DEFAULT now()
        )
        """)
    # 幂等开单:同租户同账套同期同意图只有一张工单。
    op.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS uq_work_orders_scope "
        "ON work_orders (tenant_id, workspace_client_id, period, intent)"
    )
    op.execute(_RLS.format(t="work_orders"))

    # 只追加:无 UPDATE/DELETE 路径。bigserial 主键在单写入者场景下天然是事件发生顺序。
    op.execute("""
        CREATE TABLE IF NOT EXISTS work_order_events (
            id bigserial PRIMARY KEY,
            tenant_id uuid NOT NULL,
            work_order_id uuid NOT NULL REFERENCES work_orders (id) ON DELETE CASCADE,
            step text NOT NULL,
            event_type text NOT NULL,
            payload jsonb NOT NULL DEFAULT '{}'::jsonb,
            actor text NOT NULL DEFAULT 'system',
            created_at timestamptz NOT NULL DEFAULT now()
        )
        """)
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_wo_events_wo "
        "ON work_order_events (tenant_id, work_order_id, id)"
    )
    op.execute(_RLS.format(t="work_order_events"))

    op.execute("""
        CREATE TABLE IF NOT EXISTS work_order_items (
            id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id uuid NOT NULL,
            work_order_id uuid NOT NULL REFERENCES work_orders (id) ON DELETE CASCADE,
            source text NOT NULL,
            kind text NOT NULL DEFAULT 'unknown',
            file_ref text,
            ocr_history_id uuid,
            status text NOT NULL DEFAULT 'pending',
            flag_reason text,
            dedupe_key text,
            created_at timestamptz NOT NULL DEFAULT now(),
            updated_at timestamptz NOT NULL DEFAULT now()
        )
        """)
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_wo_items_wo ON work_order_items (tenant_id, work_order_id)"
    )
    # 幂等 intake:同一工单内同一 dedupe_key 只落一行(NULL 不参与去重)。
    op.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS uq_wo_items_dedupe "
        "ON work_order_items (tenant_id, work_order_id, dedupe_key) WHERE dedupe_key IS NOT NULL"
    )
    op.execute(_RLS.format(t="work_order_items"))

    op.execute("""
        CREATE TABLE IF NOT EXISTS work_order_deliverables (
            id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id uuid NOT NULL,
            work_order_id uuid NOT NULL REFERENCES work_orders (id) ON DELETE CASCADE,
            kind text NOT NULL,
            artifact_path text,
            numbers jsonb NOT NULL DEFAULT '{}'::jsonb,
            created_at timestamptz NOT NULL DEFAULT now()
        )
        """)
    # 幂等 package:重跑同一 kind 的交付物覆盖而非累加。
    op.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS uq_wo_deliverables_kind "
        "ON work_order_deliverables (tenant_id, work_order_id, kind)"
    )
    op.execute(_RLS.format(t="work_order_deliverables"))


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS work_order_deliverables")
    op.execute("DROP TABLE IF EXISTS work_order_items")
    op.execute("DROP TABLE IF EXISTS work_order_events")
    op.execute("DROP TABLE IF EXISTS work_orders")
