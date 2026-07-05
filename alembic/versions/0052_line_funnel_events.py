"""line_funnel_events:LINE 获客漏斗 follow 级打点(Agent 观测 W0)。

加好友→绑定→用起来的转化此前量不出第一级(follow 无落库)。(line_user_id, event)
主键=每人每级只记首次。无 tenant 列:follow 发生在绑定前,天然无租户。

prod 无 alembic 钩子,真实建表走 line_funnel.ensure_table() 首用自愈;本文件为文档留档。
"""

from alembic import op

revision = "0052_line_funnel_events"
down_revision = "0051_agent_turn_log_degraded_intent"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE IF NOT EXISTS line_funnel_events (
            line_user_id text NOT NULL,
            event text NOT NULL,
            created_at timestamptz NOT NULL DEFAULT now(),
            PRIMARY KEY (line_user_id, event)
        )
        """)


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS line_funnel_events")
