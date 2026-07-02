"""LINE 待决图片意图 line_pending_intents(LI-2 · 话先图后的跨消息接力)。

Revision ID: 0045_line_pending_intents
Revises: 0044_line_voice_quota
Create Date: 2026-07-02

一人一条活动意图(tenant+line_user 主键·upsert 覆盖),TTL 过期即失效回默认路。
租户数据 → apply_tenant_rls 隔离(ensure 侧同步施加)。
Dual-run:services/line_binding/line_intent_store.ensure_table()(prod 无 alembic 钩子,
走首用 ensure 自愈;本文件留档)。
"""

from alembic import op

revision = "0045_line_pending_intents"
down_revision = "0044_line_voice_quota"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE IF NOT EXISTS line_pending_intents (
            tenant_id uuid NOT NULL,
            line_user_id text NOT NULL,
            workspace_client_id bigint,
            intent jsonb NOT NULL,
            created_at timestamptz NOT NULL DEFAULT now(),
            expires_at timestamptz NOT NULL,
            PRIMARY KEY (tenant_id, line_user_id)
        )
        """)


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS line_pending_intents")
