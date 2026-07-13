# -*- coding: utf-8 -*-
"""LINE 收料暂存(LN-1):line_client_groups(群↔客户绑定)+ client_intake_staging(暂存池)。

Revision ID: 0074_line_intake_staging
Revises: 0073_coa_erp_bridge
Create Date: 2026-07-14

一群一客户(line_group_id PK);暂存池幂等锚 line_message_id 全局唯一(LINE redelivery
重投不双记)。Dual-run:services/line_binding/line_client_group.ensure_table() 与
line_intake_store.ensure_table() 跑同一幂等 DDL(prod alembic 停 0020 靠首用自愈,
本迁移保迁移链诚实 + 新库经 alembic 建全)。
"""

from alembic import op

revision = "0074_line_intake_staging"
down_revision = "0073_coa_erp_bridge"
branch_labels = None
depends_on = None

# 与 core.rls._TPL["tenant"] 同源(迁移须 standalone 不 import 应用代码 · 故内联同样谓词)。
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
        CREATE TABLE IF NOT EXISTS line_client_groups (
            line_group_id       text   PRIMARY KEY,
            tenant_id           uuid   NOT NULL,
            workspace_client_id bigint NOT NULL,
            bound_by_line_user  text,
            bound_at            timestamptz NOT NULL DEFAULT now()
        )
        """)
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_line_client_groups_client "
        "ON line_client_groups (tenant_id, workspace_client_id)"
    )
    op.execute(_RLS.format(t="line_client_groups"))

    op.execute("""
        CREATE TABLE IF NOT EXISTS client_intake_staging (
            id                  uuid   PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id           uuid   NOT NULL,
            workspace_client_id bigint NOT NULL,
            line_message_id     text   NOT NULL,
            file_path           text   NOT NULL,
            sha256              text   NOT NULL,
            source              text   NOT NULL,
            sender_line_user_id text,
            suggested_period    text,
            status              text   NOT NULL DEFAULT 'pending',
            created_at          timestamptz NOT NULL DEFAULT now()
        )
        """)
    op.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS uq_client_intake_staging_msg "
        "ON client_intake_staging (line_message_id)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_client_intake_staging_client "
        "ON client_intake_staging (tenant_id, workspace_client_id, status)"
    )
    op.execute(_RLS.format(t="client_intake_staging"))


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS client_intake_staging")
    op.execute("DROP TABLE IF EXISTS line_client_groups")
