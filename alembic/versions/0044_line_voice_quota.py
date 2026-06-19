"""Pearnly Voice 每日上限 line_voice_quota(自然语气闲聊回复条数计数 · P3A-2)。

Revision ID: 0044_line_voice_quota
Revises: 0043_purchase_image_sha256
Create Date: 2026-06-19

按 LINE 用户 + 泰国时区日期计数,DAILY_CAP=30 控成本(闲聊不二次计费)。键=line_user_id
(LINE 平台身份,跨租户唯一),只是计数器无业务数据 → 不入 tenant 隔离/RLS。
Dual-run:services/expense/line_voice_quota.ensure_table()(prod 无 alembic 钩子,走 ensure;本文件留档)。
"""

from alembic import op

revision = "0044_line_voice_quota"
down_revision = "0043_purchase_image_sha256"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE IF NOT EXISTS line_voice_quota (
            line_user_id text NOT NULL,
            day date NOT NULL,
            n int NOT NULL DEFAULT 0,
            PRIMARY KEY (line_user_id, day)
        )
        """)


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS line_voice_quota")
