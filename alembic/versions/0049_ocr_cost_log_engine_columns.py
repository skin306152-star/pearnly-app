"""ocr_cost_log 引擎策略观测列:model / mode / l3_fired / status。

Revision ID: 0049_ocr_cost_log_engine_columns
Revises: 0048_line_agent_anchors
Create Date: 2026-07-04

Earn 后台「OCR 引擎」指标(模型占比 / L3 触发率 / 失败率)靠这四列;
成本按每次识别实际用的模型单价落账,失败也记一行(status='failed')。
Dual-run:services/cost/store.ensure_ocr_cost_log_table() 启动幂等 ALTER
(prod 无 alembic 钩子,走启动自愈;本文件留档)。
"""

from alembic import op

revision = "0049_ocr_cost_log_engine_columns"
down_revision = "0048_line_agent_anchors"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        ALTER TABLE ocr_cost_log ADD COLUMN IF NOT EXISTS model TEXT NOT NULL DEFAULT '';
        ALTER TABLE ocr_cost_log ADD COLUMN IF NOT EXISTS mode TEXT NOT NULL DEFAULT '';
        ALTER TABLE ocr_cost_log ADD COLUMN IF NOT EXISTS l3_fired BOOLEAN NOT NULL DEFAULT FALSE;
        ALTER TABLE ocr_cost_log ADD COLUMN IF NOT EXISTS status TEXT NOT NULL DEFAULT 'ok';
        """)


def downgrade() -> None:
    op.execute("""
        ALTER TABLE ocr_cost_log DROP COLUMN IF EXISTS model;
        ALTER TABLE ocr_cost_log DROP COLUMN IF EXISTS mode;
        ALTER TABLE ocr_cost_log DROP COLUMN IF EXISTS l3_fired;
        ALTER TABLE ocr_cost_log DROP COLUMN IF EXISTS status;
        """)
