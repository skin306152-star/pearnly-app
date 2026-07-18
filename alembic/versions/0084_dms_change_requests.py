"""DMS 改写审批申请表 dms_change_requests(波4)。

Revision ID: 0084_dms_change_requests
Revises: 0083_dms_operator_profiles
Create Date: 2026-07-19

销售(花名册 dms_role='sales')的老客户改写不直写:落申请快照(diffs+draft),管理员在
LINE 批准后以批准人自己的凭据执行。状态机 pending→processing(执行租约)→approved/
rejected;过期惰性落 expired。

Dual-run:services/line_dms/approval_store.ensure_tables()(prod 无 alembic 钩子,走首用
ensure 自愈;本文件留档)。
"""

from alembic import op

revision = "0084_dms_change_requests"
down_revision = "0083_dms_operator_profiles"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE IF NOT EXISTS dms_change_requests (
            id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id uuid NOT NULL,
            operator_user_id uuid NOT NULL,
            endpoint_id text,
            customer_id text NOT NULL,
            customer_name text,
            field_diffs jsonb NOT NULL,
            draft jsonb NOT NULL,
            status text NOT NULL DEFAULT 'pending',
            target_user_id uuid,
            decided_by uuid,
            decided_at timestamptz,
            processing_at timestamptz,
            created_at timestamptz DEFAULT now(),
            expires_at timestamptz NOT NULL
        )
        """)
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_dms_change_requests_tenant_status "
        "ON dms_change_requests (tenant_id, status)"
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS dms_change_requests")
