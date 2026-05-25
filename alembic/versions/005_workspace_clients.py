"""workspace_clients · 账套主体 / 工作台归属(B0 地基)

拆分两个概念(Zihao 2026-05-25 拍板):
  - workspace_client  = "在为哪家公司做账"(账套主体 / 权限 / 用哪个 ERP 账套)。登录选。
  - history.client_id = 发票买方(OCR → MR.ERP 应收客户)。不动。
不复用 clients 表(语义已被买方/对方占用)。Pearnly 只绑定已有 ERP endpoint,
不自动创建账套主体。

⚠️ 双跑:生产不跑 `alembic upgrade`(git-deploy 无钩子)· 真建由
services/workspace/store.ensure_workspace_tables() 在启动时执行(幂等)。
本迁移留档 + 本地/未来钩子用 · 与 002_field_overrides 同范式。

Revision ID: 005_workspace_clients
Revises: 004_import_template_mappings
Create Date: 2026-05-25
"""

from typing import Sequence, Union

from alembic import op

revision: str = "005_workspace_clients"
down_revision: Union[str, Sequence[str], None] = "004_import_template_mappings"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE IF NOT EXISTS workspace_clients (
            id              BIGSERIAL PRIMARY KEY,
            tenant_id       UUID,
            user_id         UUID NOT NULL,
            name            TEXT NOT NULL,
            tax_id          TEXT,
            erp_endpoint_id TEXT,
            is_active       BOOLEAN NOT NULL DEFAULT TRUE,
            created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
        """)
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_workspace_clients_tenant "
        "ON workspace_clients(tenant_id, is_active)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_workspace_clients_user "
        "ON workspace_clients(user_id, is_active)"
    )
    op.execute("ALTER TABLE ocr_history ADD COLUMN IF NOT EXISTS workspace_client_id BIGINT")
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_ocr_history_workspace "
        "ON ocr_history(workspace_client_id) WHERE workspace_client_id IS NOT NULL"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_ocr_history_workspace")
    op.execute("ALTER TABLE ocr_history DROP COLUMN IF EXISTS workspace_client_id")
    op.execute("DROP TABLE IF EXISTS workspace_clients")
