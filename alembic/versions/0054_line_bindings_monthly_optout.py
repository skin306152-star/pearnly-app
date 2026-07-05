"""line_bindings.monthly_report_opt_out:月报一键退订标记(W4-1)。

月报默认开(Zihao 2026-07-05 拍板),退订按人记在绑定行上;发送侧扫描时跳过。

prod 无 alembic 钩子,真实加列走 monthly_report._ensure_opt_out_column() 首用自愈;
本文件为文档留档。
"""

from alembic import op

revision = "0054_line_bindings_monthly_optout"
down_revision = "0053_line_agent_profiles"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        "ALTER TABLE line_bindings "
        "ADD COLUMN IF NOT EXISTS monthly_report_opt_out boolean NOT NULL DEFAULT false"
    )


def downgrade() -> None:
    op.execute("ALTER TABLE line_bindings DROP COLUMN IF EXISTS monthly_report_opt_out")
