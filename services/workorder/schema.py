# -*- coding: utf-8 -*-
"""工单制 schema 双跑入口(启动调一次 · 与 alembic 0059 同源幂等 DDL · 铁律 #5)。

prod 无自动迁移钩子 → startup 经 ensure_workorder_schema() 幂等建 4 表 + RLS policy。
DDL 与迁移逐字对齐(改一处必同改两处)。失败仅告警不 raise(不挡主服务)。

四表关系:work_orders 是每客户每期一张的顶层单据,workspace_client_id 恒非空(每单
只属一个客户账套);其余三表以 work_order_id 挂在它下面,各自也带一份 tenant_id
(同 purchase_lines/journal_lines 的子表惯例)。四表统一纯 tenant RLS(`apply_tenant_rls`)
——docs/refactor/b8-rls-HANDOFF §7.15.2/7.20 反复验过:仓库里 `apply_tenant_workspace_rls`
虽存在(core/rls.py)但实际零表采用,purchase_docs/journal_vouchers 等有 workspace_client_id
的表照样只挂纯 tenant policy,应用层 WHERE tenant_id+workspace_client_id 才是真正的隔离主力、
RLS 是第二道防线,不重复造未经验证的模板。

work_order_events 是唯一追加表:证据链底座 + 断点续跑的恢复源(重放到最后一条
step_done = 当前进度)。DAL 层(store.py)故意不给它 UPDATE/DELETE 函数。
"""

from __future__ import annotations

import logging

from core.rls import apply_tenant_rls

logger = logging.getLogger("mr-pilot")

_TABLES = (
    """
    CREATE TABLE IF NOT EXISTS work_orders (
        id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
        tenant_id uuid NOT NULL,
        workspace_client_id bigint NOT NULL,
        period text NOT NULL,
        intent text NOT NULL DEFAULT 'monthly_vat',
        status text NOT NULL DEFAULT 'collecting',
        current_step text,
        created_at timestamptz NOT NULL DEFAULT now(),
        updated_at timestamptz NOT NULL DEFAULT now()
    )
    """,
    # 只追加:无 UPDATE/DELETE 路径(store.py 只给 append + 查询)。id 是 bigserial ——
    # 单写入者场景下自增序天然就是事件发生顺序,断点续跑靠它重放,不必依赖 created_at 去重时间戳。
    """
    CREATE TABLE IF NOT EXISTS work_order_events (
        id bigserial PRIMARY KEY,
        tenant_id uuid NOT NULL,
        work_order_id uuid NOT NULL REFERENCES work_orders (id) ON DELETE CASCADE,
        step text NOT NULL,
        event_type text NOT NULL,
        payload jsonb NOT NULL DEFAULT '{}'::jsonb,
        actor text NOT NULL DEFAULT 'system',
        created_at timestamptz NOT NULL DEFAULT now()
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS work_order_items (
        id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
        tenant_id uuid NOT NULL,
        work_order_id uuid NOT NULL REFERENCES work_orders (id) ON DELETE CASCADE,
        source text NOT NULL,
        kind text NOT NULL DEFAULT 'unknown',
        file_ref text,
        ocr_history_id uuid,
        status text NOT NULL DEFAULT 'pending',
        flag_reason text,
        dedupe_key text,
        created_at timestamptz NOT NULL DEFAULT now(),
        updated_at timestamptz NOT NULL DEFAULT now()
    )
    """,
    # numbers 快照关键数字(如销项/进项税额)供证据索引直接引用,不必每次重算。
    """
    CREATE TABLE IF NOT EXISTS work_order_deliverables (
        id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
        tenant_id uuid NOT NULL,
        work_order_id uuid NOT NULL REFERENCES work_orders (id) ON DELETE CASCADE,
        kind text NOT NULL,
        artifact_path text,
        numbers jsonb NOT NULL DEFAULT '{}'::jsonb,
        created_at timestamptz NOT NULL DEFAULT now()
    )
    """,
)

_INDEXES = (
    # 幂等开单:同租户同账套同期同意图只有一张工单(§3 唯一约束)。
    "CREATE UNIQUE INDEX IF NOT EXISTS uq_work_orders_scope "
    "ON work_orders (tenant_id, workspace_client_id, period, intent)",
    "CREATE INDEX IF NOT EXISTS ix_wo_events_wo "
    "ON work_order_events (tenant_id, work_order_id, id)",
    "CREATE INDEX IF NOT EXISTS ix_wo_items_wo " "ON work_order_items (tenant_id, work_order_id)",
    # 幂等 intake:同一工单内同一 dedupe_key 只落一行(NULL 不参与去重——非全部 item 都算指纹)。
    "CREATE UNIQUE INDEX IF NOT EXISTS uq_wo_items_dedupe "
    "ON work_order_items (tenant_id, work_order_id, dedupe_key) WHERE dedupe_key IS NOT NULL",
    # 幂等 package:重跑同一 kind 的交付物覆盖而非累加(§6 金标测试 6·幂等)。
    "CREATE UNIQUE INDEX IF NOT EXISTS uq_wo_deliverables_kind "
    "ON work_order_deliverables (tenant_id, work_order_id, kind)",
)

_RLS_TABLES = (
    "work_orders",
    "work_order_events",
    "work_order_items",
    "work_order_deliverables",
)


def ensure_workorder_schema() -> None:
    """幂等建工单制 4 表 + 索引 + RLS(startup 调 · 与 alembic 0059 同源)。"""
    from core import db

    with db.get_cursor(commit=True) as cur:
        for ddl in _TABLES:
            cur.execute(ddl)
        for idx in _INDEXES:
            cur.execute(idx)
        apply_tenant_rls(cur, *_RLS_TABLES)
