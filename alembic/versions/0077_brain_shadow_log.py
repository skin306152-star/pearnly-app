# -*- coding: utf-8 -*-
"""大脑影子建议日志 brain_shadow_log(裁决预判/审核建议 · 只建议不落账)。

Revision ID: 0077_brain_shadow_log
Revises: 0076_erp_push_logs_work_order_id
Create Date: 2026-07-14

services/workorder/brain_shadow.py 的唯一落点:每条 GPT 建议(含被判 invalid 的)逐条
落此表,分歧清单 = 影子转正验收单(照 shadow_money_log 范式)。不是业务表——工单
四表/裁决事件流一行不碰,删掉本表只丢观测数据不丢账。

Dual-run:prod alembic 指针停 0020,真正建表靠 brain_shadow.ensure_table() 首用自愈
(与本文件逐字对齐,照 line_anchor_store 先例);本文件留档。
"""

from alembic import op

revision = "0077_brain_shadow_log"
down_revision = "0076_erp_push_logs_work_order_id"
branch_labels = None
depends_on = None

_RLS = """
    ALTER TABLE brain_shadow_log ENABLE ROW LEVEL SECURITY;
    DROP POLICY IF EXISTS tenant_isolation ON brain_shadow_log;
    CREATE POLICY tenant_isolation ON brain_shadow_log
    FOR ALL
    USING (
        tenant_id::text = current_setting('app.current_tenant_id', true)
        OR current_setting('app.bypass_rls', true) = 'on'
    )
    WITH CHECK (
        tenant_id::text = current_setting('app.current_tenant_id', true)
        OR current_setting('app.bypass_rls', true) = 'on'
    );
"""


def upgrade() -> None:
    op.execute("""
        CREATE TABLE IF NOT EXISTS brain_shadow_log (
            id BIGSERIAL PRIMARY KEY,
            tenant_id UUID NOT NULL,
            work_order_id UUID NOT NULL,
            item_id UUID NOT NULL,
            suggestion TEXT,
            confidence NUMERIC(4, 3),
            reason_zh TEXT,
            cited_event_ids JSONB NOT NULL DEFAULT '[]'::jsonb,
            valid BOOLEAN NOT NULL DEFAULT FALSE,
            invalid_reason TEXT,
            model TEXT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
        """)
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_brain_shadow_log_wo "
        "ON brain_shadow_log (tenant_id, work_order_id, created_at DESC)"
    )
    op.execute(_RLS)


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS brain_shadow_log")
