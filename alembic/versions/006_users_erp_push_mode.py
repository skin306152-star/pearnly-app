"""users.erp_push_mode · ERP 自动处理方式(P1b)

账户级默认处理方式(Zihao 2026-05-26 拍板 · 上传时可临时覆盖本批):
  - smart    = 智能分拣(按发票卖方→账套→ERP 端点 · 新用户默认推荐)
  - fixed    = 固定当前账套(全推 auto_push 端点 · 现行为)
  - ocr_only = 只识别不推送(完全跳过 auto-push)

⚠️ 双跑:生产不跑 `alembic upgrade`(git-deploy 无钩子)· 真加列由
db.ensure_google_sub_column()(users 多列 ensure)在启动时执行(幂等)。
本迁移留档 + 本地/未来钩子用 · 与 005_workspace_clients 同范式。

Revision ID: 006_users_erp_push_mode
Revises: 005_workspace_clients
Create Date: 2026-05-26
"""

from typing import Sequence, Union

from alembic import op

revision: str = "006_users_erp_push_mode"
down_revision: Union[str, Sequence[str], None] = "005_workspace_clients"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS erp_push_mode TEXT DEFAULT 'smart'")


def downgrade() -> None:
    op.execute("ALTER TABLE users DROP COLUMN IF EXISTS erp_push_mode")
