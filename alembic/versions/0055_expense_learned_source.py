"""expense_learned.source:区分用户可编辑关键词规则(user_rule)与纠错自学(空/correction)。

Phase 2「识别关键词/规则中心」:用户在费用数据页给小类挂的关键词写进 expense_learned
(source='user_rule'),归类管线本就学习优先 → 立即生效,写死规则退成出厂默认。UI 只列/删
user_rule 行;纠错自学行照旧隐式参与、不受影响。

prod 无 alembic 钩子,真实加列走 schema.ensure_expense_schema() 首用自愈;本文件为文档留档。
"""

from alembic import op

revision = "0055_expense_learned_source"
down_revision = "0054_line_bindings_monthly_optout"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        "ALTER TABLE expense_learned ADD COLUMN IF NOT EXISTS source text NOT NULL DEFAULT ''"
    )


def downgrade() -> None:
    op.execute("ALTER TABLE expense_learned DROP COLUMN IF EXISTS source")
