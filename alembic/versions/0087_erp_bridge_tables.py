# -*- coding: utf-8 -*-
"""ERP 桥(内网 → 云)两表:erp_bridges 桥身份 + bridge_jobs 任务信箱。

Revision ID: 0087_erp_bridge_tables
Revises: 0086_ocr_history_posting_kind
Create Date: 2026-07-26

桥装在客户内网、主动外拨连云端,云端永不回连(内网不开洞)。erp_bridges 是桥的身份 +
它上报的账套镜像(写桥唯一闸据此判"同一账套是不是已经有写桥在线");bridge_jobs 是
"云端问、桥答"的信箱,一行一次问答,门面等它变 done。

与小助手 companion 零共享:独立表、独立密钥前缀 brg_、独立路由前缀 /api/erp/bridge/。

留档性质:prod 不跑 alembic upgrade,真正落表靠 services/erp/bridge/store.ensure_tables()
首次使用时幂等自愈(与本迁移逐字对齐)。
"""

from alembic import op

revision = "0087_erp_bridge_tables"
down_revision = "0086_ocr_history_posting_kind"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE IF NOT EXISTS erp_bridges (
            id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id uuid NOT NULL,
            name text NOT NULL,
            secret_hash text NOT NULL,
            role text NOT NULL DEFAULT 'read',
            effective_role text NOT NULL DEFAULT 'read',
            books jsonb NOT NULL DEFAULT '[]'::jsonb,
            bridge_version text,
            host text,
            last_seen_at timestamptz,
            created_at timestamptz NOT NULL DEFAULT now()
        )
        """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_erp_bridges_tenant ON erp_bridges (tenant_id)")
    op.execute("""
        CREATE TABLE IF NOT EXISTS bridge_jobs (
            id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id uuid NOT NULL,
            bridge_id uuid NOT NULL,
            book_id text,
            kind text NOT NULL,
            payload jsonb NOT NULL DEFAULT '{}'::jsonb,
            status text NOT NULL DEFAULT 'queued',
            result jsonb,
            error jsonb,
            lease_owner text,
            lease_expires_at timestamptz,
            created_at timestamptz NOT NULL DEFAULT now(),
            finished_at timestamptz
        )
        """)
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_bridge_jobs_bridge_status ON bridge_jobs (bridge_id, status)"
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS bridge_jobs")
    op.execute("DROP TABLE IF EXISTS erp_bridges")
