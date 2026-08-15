# -*- coding: utf-8 -*-
"""Daily 周记账域 · 建表 + RLS enroll。

daily_entries 是 Daily 应用(pearnly.com/daily)的唯一数据表:每行属于一个租户
(每受邀用户经 create_owner_user 建号即得独立租户)——「各是各的」的租户隔离在
数据层的第一道防线是应用层 WHERE(store.py 全带 tenant_id),第二道是 RLS policy
(apply_tenant_rls · 业务连接 SET LOCAL ROLE 到 NOBYPASSRLS 角色后强制)。

Dual-run:alembic/versions/0101_daily_entries.py 留档同源 DDL;prod 不跑 alembic,
靠启动 ensure_daily_tables 幂等建表(services/startup.boot_ensures 清单)。
"""

from __future__ import annotations

import logging

from core import db

logger = logging.getLogger(__name__)

_DDL = (
    """
    CREATE TABLE IF NOT EXISTS daily_entries (
        id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
        tenant_id uuid NOT NULL,
        entry_date date NOT NULL,
        kind text NOT NULL CHECK (kind IN ('income', 'expense')),
        title text NOT NULL,
        amount numeric(12, 2) NOT NULL CHECK (amount > 0),
        created_at timestamptz NOT NULL DEFAULT now(),
        updated_at timestamptz NOT NULL DEFAULT now()
    )
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_daily_entries_tenant_date
    ON daily_entries (tenant_id, entry_date)
    """,
)


def ensure_daily_tables() -> None:
    """幂等建表 + 索引(启动期自愈 · 失败仅记日志不阻断主流程,照 membership 范式)。"""
    try:
        with db.get_cursor(commit=True) as cur:
            for stmt in _DDL:
                cur.execute(stmt)
    except Exception as e:
        logger.error(f"ensure_daily_tables failed: {e}")


def ensure_daily_rls() -> None:
    """给 daily_entries 上 tenant policy(幂等 · 独立事务防牵连别的 ensure)。

    force=False:owner 连接仍绕过 → 数据迁移/后台维护通道不破;业务连接
    (get_cursor_rls · NOBYPASSRLS)强制。表未建时 existing_tables 过滤,不炸。
    """
    from core.rls import apply_tenant_rls, existing_tables

    try:
        with db.get_cursor(commit=True) as cur:
            apply_tenant_rls(cur, *existing_tables(cur, ("daily_entries",)))
    except Exception as e:
        logger.warning(f"ensure_daily_rls skipped: {e}")
