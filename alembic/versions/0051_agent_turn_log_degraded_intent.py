"""agent_turn_logs 加 degraded/intent 两列(Agent 观测 W0)。

degraded=兜底降级标记(grounded_fb/card_text_dropped/card_fail),intent=轮意图
(工具轨迹派生·观测口径)。没有这两列,"答非所问率"和意图分布都量不出,体验迭代盲飞。

prod 无 alembic 钩子,真实补列走 turn_log.ensure_table() 启动自愈;本文件为文档留档,
standalone 内联同款 DDL。
"""

from alembic import op

revision = "0051_agent_turn_log_degraded_intent"
down_revision = "0050_shadow_money_log"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TABLE agent_turn_logs ADD COLUMN IF NOT EXISTS degraded text")
    op.execute("ALTER TABLE agent_turn_logs ADD COLUMN IF NOT EXISTS intent text")


def downgrade() -> None:
    op.execute("ALTER TABLE agent_turn_logs DROP COLUMN IF EXISTS degraded")
    op.execute("ALTER TABLE agent_turn_logs DROP COLUMN IF EXISTS intent")
