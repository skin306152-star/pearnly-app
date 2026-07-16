# -*- coding: utf-8 -*-
"""目标驱动前门(FD-0)合同 + 附件两表 ai_goal_contracts / ai_contract_files。

Revision ID: 0079_front_desk_contracts
Revises: 0078_tenant_entrances
Create Date: 2026-07-16

草稿合同是「投料 + 说目标」到「开工单执行」之间的中转站:附件先挂草稿(未确认不进工单),
人点确认后经 services/workorder/steps/intake.register_file 落成 work_order_items。两表不是
第二账本——删掉只丢草稿中转态,已确认的账走工单四表。tenant RLS 照 workorder 四表先例(纯
tenant 隔离,应用层 WHERE 为主 + RLS 第二道防线);子表 ai_contract_files 自带 tenant_id。

Dual-run:prod alembic 指针停 0020,真正建表靠 services/front_desk/contract_store.ensure_table()
首用自愈(与本文件逐字对齐,照 brain_shadow.ensure_table 先例);本文件留档。
"""

from alembic import op

revision = "0079_front_desk_contracts"
down_revision = "0078_tenant_entrances"
branch_labels = None
depends_on = None

_RLS_TEMPLATE = """
    ALTER TABLE {table} ENABLE ROW LEVEL SECURITY;
    DROP POLICY IF EXISTS tenant_isolation ON {table};
    CREATE POLICY tenant_isolation ON {table}
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
        CREATE TABLE IF NOT EXISTS ai_goal_contracts (
            id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id uuid NOT NULL,
            workspace_client_id bigint,
            period text,
            intent text,
            deliverables jsonb NOT NULL DEFAULT '[]'::jsonb,
            status text NOT NULL DEFAULT 'draft',
            utterance_raw text,
            brain_suggestion jsonb NOT NULL DEFAULT '{}'::jsonb,
            work_order_id uuid,
            created_by text,
            confirmed_by text,
            created_at timestamptz NOT NULL DEFAULT now(),
            updated_at timestamptz NOT NULL DEFAULT now()
        )
        """)
    op.execute("""
        CREATE TABLE IF NOT EXISTS ai_contract_files (
            id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            contract_id uuid NOT NULL REFERENCES ai_goal_contracts (id) ON DELETE CASCADE,
            tenant_id uuid NOT NULL,
            file_ref text NOT NULL,
            original_name text,
            sha256 text,
            status text NOT NULL DEFAULT 'staged',
            created_at timestamptz NOT NULL DEFAULT now()
        )
        """)
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_ai_goal_contracts_tenant "
        "ON ai_goal_contracts (tenant_id, created_at DESC)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_ai_goal_contracts_client "
        "ON ai_goal_contracts (tenant_id, workspace_client_id, created_at DESC)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_ai_contract_files_contract "
        "ON ai_contract_files (tenant_id, contract_id)"
    )
    op.execute(_RLS_TEMPLATE.format(table="ai_goal_contracts"))
    op.execute(_RLS_TEMPLATE.format(table="ai_contract_files"))


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS ai_contract_files")
    op.execute("DROP TABLE IF EXISTS ai_goal_contracts")
