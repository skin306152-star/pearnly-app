# -*- coding: utf-8 -*-
"""电子税务(e-Tax)域 RLS enroll(REFACTOR-B8 · 孤儿表 re-enroll)。

etax_submissions / etax_channel_settings 只在 alembic 0006 建、prod 无 startup CREATE 钩子 →
事故止血时被全量 DISABLE,此处补回 policy。对齐 ensure_sales_rls / ensure_client_rules_rls 的
「独立 ensure_*_rls」范式。

模板 = 纯 tenant:两表 tenant_id NOT NULL、无 user_id、workspace_client_id 可空。**不能 tenant_ws**
(同 client_rules:_WS_MATCH 会隐藏 workspace_client_id IS NULL 的 firm-wide 行)。两表当前为 e-Tax
模块占位、repo 内无业务访问点 → enroll-only,force=False 下回填迁移(workspace_backfill)裸 owner 不破。
"""

from __future__ import annotations

import logging

from core import db

logger = logging.getLogger(__name__)

_RLS_TABLES = ("etax_submissions", "etax_channel_settings")


def ensure_etax_rls() -> None:
    """给 etax 两表上 tenant policy(幂等 · 独立事务防牵连别的 ensure)。逐表先验存在防部分库整块失败。"""
    from core.rls import apply_tenant_rls, existing_tables

    try:
        with db.get_cursor(commit=True) as cur:
            apply_tenant_rls(cur, *existing_tables(cur, _RLS_TABLES))
    except Exception as e:
        logger.warning(f"ensure_etax_rls skipped: {e}")
