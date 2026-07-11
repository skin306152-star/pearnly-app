"""LINE 待问池 batch_seq(D2 · R3 串题根治 · 答题编号单一事实源)。

Revision ID: 0070_line_client_batch_seq
Revises: 0069_pos_shift_seq
Create Date: 2026-07-11

推送时 mark_sent 把该题在消息里的固定编号(enumerate start=1)落进 batch_seq,答题侧按存
序号定位「客户嘴里的第 N 题」,不再靠推送/答题两侧各自 ORDER BY created_at 对齐——根治
R3 串题(编号不随期间某题退出 pending、列表收缩而漂移)。不回填:迁移前存量批次 batch_seq
留 NULL,答题侧 _consume 对无 batch_seq 的批次回落按位序(与旧行为一致)。Dual-run:
services/line_binding/line_client_pool_store.ensure_table() 跑同一幂等 ADD COLUMN(prod
alembic 停 0020 靠首用自愈,该列真正落库在自愈路径,本迁移保迁移链诚实 + 新库经 alembic 建全)。
"""

from alembic import op

revision = "0070_line_client_batch_seq"
down_revision = "0069_pos_shift_seq"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TABLE line_client_questions ADD COLUMN IF NOT EXISTS batch_seq smallint")


def downgrade() -> None:
    op.execute("ALTER TABLE line_client_questions DROP COLUMN IF EXISTS batch_seq")
