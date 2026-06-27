# -*- coding: utf-8 -*-
"""自动化规则域 RLS enroll(REFACTOR-B8 · 孤儿表 re-enroll)。

automation_rules 在仓库内无 CREATE DDL、无 alembic 钩子(prod 既有的 legacy 孤儿表)→ 事故止血时
被全量 DISABLE,此处补回 policy。对齐 ensure_sales_rls / ensure_email_ingest_rls 的「独立
ensure_*_rls」范式。

模板 = tenant_or_user:prod 实测 automation_rules 有 user_id(NOT NULL)+ tenant_id(可空)
两列 → 设 tenant 时按 tenant、孤立用户(tenant_id IS NULL)按 user 兜底,同 clients/ocr_history。

注:error_events 是纯系统错误日志(唯一消费者超管 · SELECT 无 WHERE · INSERT 来自请求上下文常无
租户)→ 设计裁决【不 enroll】,守卫 ensure_no_orphan_rls 维持其 DISABLE 终态,不在此 enroll。
"""

from __future__ import annotations

import logging

from core import db

logger = logging.getLogger(__name__)

_RLS_TABLES = ("automation_rules",)


def ensure_automation_rls() -> None:
    """给 automation_rules 上 tenant_or_user policy(幂等 · 独立事务防牵连别的 ensure)。

    force=False:owner 仍绕过 → 租户级联删(owner_users 删用户时连带删其规则)等系统路径不破;
    业务连接 SET ROLE 后强制隔离。逐表先验存在再 enroll(部分库未建不连累)。
    """
    from core.rls import apply_tenant_or_user_rls, existing_tables

    try:
        with db.get_cursor(commit=True) as cur:
            apply_tenant_or_user_rls(cur, *existing_tables(cur, _RLS_TABLES))
    except Exception as e:
        logger.warning(f"ensure_automation_rls skipped: {e}")
