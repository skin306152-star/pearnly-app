"""AI 网关调用成本落库(ai_usage):Agent 对话/LINE 语音/知识库问答的钱字段从只进日志文件
变成可查询账本(超管成本面板 GET /api/admin/cost/ai-usage)。

Revision ID: 0060_ai_usage
Revises: 0058_pos_sheets_settings
Create Date: 2026-07-09

留档性质:prod 无自动迁移,实际建表靠 services/cost/ai_usage_store.py::ensure_ai_usage_table()
首次写入时懒加载自愈(同 0058 的 dual-run 注释)。唯一写点 = services/ai_gateway/logging.py
::log_call,run_task + transport 4 形态的调用都汇到这里,故含 OCR(与 ocr_cost_log 口径不同、
有重叠,两表不可直接相加)。tenant_id 允许 NULL(系统级调用),RLS 行为见 store 模块 docstring。
"""

from alembic import op

revision = "0060_ai_usage"
down_revision = "0058_pos_sheets_settings"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE IF NOT EXISTS ai_usage (
            id BIGSERIAL PRIMARY KEY,
            tenant_id UUID,
            user_id TEXT,
            task TEXT NOT NULL,
            provider TEXT,
            model TEXT,
            status TEXT NOT NULL,
            error_kind TEXT,
            latency_ms INTEGER,
            input_tokens INTEGER,
            output_tokens INTEGER,
            cost_thb NUMERIC(12, 6) NOT NULL DEFAULT 0,
            trace_id TEXT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
        """)
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_ai_usage_tenant ON ai_usage(tenant_id, created_at DESC)"
    )
    op.execute("CREATE INDEX IF NOT EXISTS idx_ai_usage_task ON ai_usage(task, created_at DESC)")
    op.execute("ALTER TABLE ai_usage ENABLE ROW LEVEL SECURITY")
    op.execute("DROP POLICY IF EXISTS tenant_isolation ON ai_usage")
    # 与 core.rls._TPL["tenant"] 同源(迁移须 standalone 不 import 应用代码 · 故内联同样谓词)。
    op.execute("""
        CREATE POLICY tenant_isolation ON ai_usage
        FOR ALL
        USING (
            tenant_id::text = current_setting('app.current_tenant_id', true)
            OR current_setting('app.bypass_rls', true) = 'on'
        )
        WITH CHECK (
            tenant_id::text = current_setting('app.current_tenant_id', true)
            OR current_setting('app.bypass_rls', true) = 'on'
        )
        """)


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS ai_usage")
