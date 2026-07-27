# -*- coding: utf-8 -*-
"""管家会话附件表(万能口 F1):对话里扔进来的料落这张表。

Revision ID: 0091_steward_attachments
Revises: 0090_steward_authz_budget
Create Date: 2026-07-27

不复用 ocr_history(识别结果表,一行一张票)也不复用 work_order_items(会计业务对象)的
理由写在 services/steward/attachments.py 顶注。expires_at 默认 30 天:对话附件是临时件,
到期由 attachments.sweep_expired 收(挂 background_loops.run_recovery_tick)。

留档性质:prod 不跑 alembic upgrade,真正建表靠 services/steward/schema.ensure_tables()
首用幂等自愈(与本迁移逐字对齐)。
"""

from alembic import op

revision = "0091_steward_attachments"
down_revision = "0090_steward_authz_budget"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE IF NOT EXISTS steward_attachments (
            id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id uuid NOT NULL,
            session_id uuid NOT NULL REFERENCES steward_sessions (id) ON DELETE CASCADE,
            message_id uuid,
            user_id text NOT NULL,
            original_name text NOT NULL DEFAULT '',
            file_ref text NOT NULL DEFAULT '',
            size_bytes bigint NOT NULL DEFAULT 0,
            sha256 text NOT NULL DEFAULT '',
            mime text NOT NULL DEFAULT '',
            kind text NOT NULL DEFAULT 'unknown',
            kind_source text NOT NULL DEFAULT 'unknown',
            kind_reason text NOT NULL DEFAULT '',
            detect jsonb NOT NULL DEFAULT '{}'::jsonb,
            status text NOT NULL DEFAULT 'ready',
            promoted_to text,
            created_at timestamptz NOT NULL DEFAULT now(),
            expires_at timestamptz NOT NULL DEFAULT now() + interval '30 days'
        )
        """)
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_steward_attachments_session "
        "ON steward_attachments (tenant_id, session_id, created_at)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_steward_attachments_expiry "
        "ON steward_attachments (expires_at)"
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS steward_attachments")
