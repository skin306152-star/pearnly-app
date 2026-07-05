"""line_agent_profiles:用户画像 v1 缓存(Agent W3-1/W3-2)。

高频商家/类目/近30天单量/昨日摘要按 (tenant_id, line_user_id) 单行缓存,TTL 6h
惰性重算,对话轮只读缓存不做聚合。数据源 ocr_history/agent_turn_logs,本表只是算果。

prod 无 alembic 钩子,真实建表走 user_profile.ensure_table() 首用自愈;本文件为文档留档。
"""

from alembic import op

revision = "0053_line_agent_profiles"
down_revision = "0052_line_funnel_events"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE IF NOT EXISTS line_agent_profiles (
            tenant_id uuid NOT NULL,
            line_user_id text NOT NULL,
            profile jsonb NOT NULL,
            refreshed_at timestamptz NOT NULL DEFAULT now(),
            PRIMARY KEY (tenant_id, line_user_id)
        )
        """)


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS line_agent_profiles")
