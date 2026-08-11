# -*- coding: utf-8 -*-
"""ai_usage 加成本归因三列:每笔 AI 调用能答「哪个入口、哪种单据、几页」。

Revision ID: 0100_ai_usage_attribution
Revises: 0099_line_webhook_event_status
Create Date: 2026-08-11

原来 ai_usage 只记 task/provider/model,成本只能按 task 分组,而 task 是管线内部标签
(ocr.image_json / ocr.layer2),看不出这笔钱是网页上传烧的还是 LINE 烧的、读的是发票
还是银行对账单。定价按 1.5 铢/页走,银行长表实际约 2.2 铢/页 —— 差价被混合均值藏住,
逐入口成本要可见,先得让每一行落账带上归因。

三列全可空:上线前的存量行没有归因,报表按 NULL 归「未归因」单独一档,不回填假值
(回填 = 拿猜的入口冒充事实,正是这次要根治的毛病)。

Dual-run:prod 无自动迁移钩子,真正建列靠首次写入时的幂等自愈
(services/cost/ai_usage_store.ensure_ai_usage_table 跑同一批 DDL),本版仅留档。
"""

from alembic import op

revision = "0100_ai_usage_attribution"
down_revision = "0099_line_webhook_event_status"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TABLE ai_usage ADD COLUMN IF NOT EXISTS entry_point TEXT")
    op.execute("ALTER TABLE ai_usage ADD COLUMN IF NOT EXISTS doc_type TEXT")
    op.execute("ALTER TABLE ai_usage ADD COLUMN IF NOT EXISTS pages INTEGER")
    # 面板查询 = 入口分组 + 时间窗过滤;现有索引都以 tenant/task 打头,吃不上。
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_ai_usage_entry ON ai_usage(entry_point, created_at DESC)"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_ai_usage_entry")
    op.execute("ALTER TABLE ai_usage DROP COLUMN IF EXISTS pages")
    op.execute("ALTER TABLE ai_usage DROP COLUMN IF EXISTS doc_type")
    op.execute("ALTER TABLE ai_usage DROP COLUMN IF EXISTS entry_point")
