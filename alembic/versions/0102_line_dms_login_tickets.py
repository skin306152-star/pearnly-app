# -*- coding: utf-8 -*-
"""DMS LINE 自动登录一次性票据表 line_dms_login_tickets(批次B)。

Revision ID: 0102_line_dms_login_tickets
Revises: 0101_daily_entries
Create Date: 2026-08-22

LINE 端发票据、DMS 门户核销完成登录:一次性、TTL 上限 60 秒、库内只存
SHA256 哈希。与 0081 的 DMS 三表同族,独立于老会计站 line_bindings。

Dual-run:prod 无 alembic 钩子,真正建表靠启动幂等自愈
(services/startup LINE ensure 循环 → services/line_dms/login_tickets.ensure_table),
本版仅留档。alembic 须 standalone —— 与本文件对应的幂等 DDL(login_tickets._DDL /
_INDEXES)逐字一致,改一处必同改另一处。
RLS 走 apply_tenant_rls 惯例(与 0081 同款:表含 tenant_id → ensure 侧同步施加,
谓词单一来源在 core/rls._TPL["tenant"])。
"""

from alembic import op

revision = "0102_line_dms_login_tickets"
down_revision = "0101_daily_entries"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE IF NOT EXISTS line_dms_login_tickets (
            ticket_hash text PRIMARY KEY,
            tenant_id uuid NOT NULL,
            user_id uuid NOT NULL,
            expires_at timestamptz NOT NULL,
            created_at timestamptz NOT NULL DEFAULT now()
        )
        """)
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_line_dms_login_tickets_expires_at "
        "ON line_dms_login_tickets (expires_at)"
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS line_dms_login_tickets")
