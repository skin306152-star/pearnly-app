"""LINE webhook 事件去重表 line_webhook_events(redelivery 幂等)。

Revision ID: 0046_line_webhook_events
Revises: 0045_line_pending_intents
Create Date: 2026-07-03

LINE 重投同一事件时按 webhookEventId 原子判重(INSERT ON CONFLICT DO NOTHING),
防文本直录被重投双记账。非租户表(webhook 早于身份解析)→ RLS 显式 DISABLE。
Dual-run:services/line_binding/line_webhook_dedup.ensure_table()(prod 无 alembic 钩子,
走 ensure;本文件留档)。
"""

from alembic import op

revision = "0046_line_webhook_events"
down_revision = "0045_line_pending_intents"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE IF NOT EXISTS line_webhook_events (
            event_id text PRIMARY KEY,
            received_at timestamptz NOT NULL DEFAULT now()
        )
        """)
    op.execute("ALTER TABLE line_webhook_events DISABLE ROW LEVEL SECURITY")


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS line_webhook_events")
