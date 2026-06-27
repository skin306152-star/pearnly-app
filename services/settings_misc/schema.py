# -*- coding: utf-8 -*-
"""杂项设置域 RLS enroll(REFACTOR-B8 · 孤儿表 re-enroll)。

user_settings / api_keys / payment_pending 在 repo 内无 CREATE DDL、无 alembic、无 startup ensure
钩子(prod 既有的 legacy 孤儿表)→ 事故止血时被全量 DISABLE,此处补回 policy。对齐 ensure_sales_rls
/ ensure_automation_rls 的「独立 ensure_*_rls」范式。

模板(按 prod \\d 真实列):
- user_settings / api_keys:user_id NOT NULL + tenant_id 可空 → tenant_or_user(同 clients/ocr_history)。
- payment_pending:user_id NOT NULL、无 tenant_id → 纯 user(用户私有的充值待审记录)。

三表访问点全是 owner 路径(级联删 / 超管 cleanup)→ enroll-only,force=False 下不破。
注:operation_logs(操作/审计日志·超管全局 tenant=NULL·INSERT fail-open)、rd_daily_usage(限流计数器
·DAL 纯 user_id·tenant_id 恒 NULL)按设计裁决【不 enroll】,守卫 ensure_no_orphan_rls 维持其 DISABLE 终态。
"""

from __future__ import annotations

import logging

from core import db

logger = logging.getLogger(__name__)

_TENANT_OR_USER = ("user_settings", "api_keys")
_USER = ("payment_pending",)


def ensure_settings_misc_rls() -> None:
    """给杂项设置 legacy 表上 policy(幂等 · 独立事务防牵连别的 ensure)。逐表先验存在防部分库整块失败。"""
    from core.rls import apply_tenant_or_user_rls, apply_user_rls, existing_tables

    try:
        with db.get_cursor(commit=True) as cur:
            apply_tenant_or_user_rls(cur, *existing_tables(cur, _TENANT_OR_USER))
            apply_user_rls(cur, *existing_tables(cur, _USER))
    except Exception as e:
        logger.warning(f"ensure_settings_misc_rls skipped: {e}")
