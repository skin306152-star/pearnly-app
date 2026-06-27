# -*- coding: utf-8 -*-
"""ERP 凭据域 RLS enroll(REFACTOR-B8 · 孤儿表 re-enroll · 零暴露孤儿收尾)。

erp_oauth_states / erp_oauth_tokens(已删 Xero 集成残留)、mrerp_credentials 在 repo 内无任何代码
访问点(仅一处文档注释提及)、无 CREATE 钩子 → 纯 prod 孤儿,事故止血时被 DISABLE。此处补回 policy
作防御纵深(对齐 ensure_sales_rls 范式)。

模板 = 纯 tenant:三表均 tenant_id NOT NULL(erp_oauth_states 另有 user_id NOT NULL,tenant 已足够)。
erp_connectors prod 不存在(幻影引用)→ existing_tables 自动跳过。force=False:无访问点,纯防御。

注:excel_templates 按设计裁决【不 enroll】——其隔离列是 owner_id(非标准 user_id)且 tenant_id 恒 NULL,
标准模板不匹配;零应用访问点 → 守卫 ensure_no_orphan_rls 维持其 DISABLE 终态。
"""

from __future__ import annotations

import logging

from core import db

logger = logging.getLogger(__name__)

_RLS_TABLES = ("erp_oauth_states", "erp_oauth_tokens", "mrerp_credentials", "erp_connectors")


def ensure_erp_credentials_rls() -> None:
    """给 ERP 凭据零暴露孤儿上 tenant policy(幂等 · 独立事务)。逐表先验存在(erp_connectors 不存在自动跳过)。"""
    from core.rls import apply_tenant_rls, existing_tables

    try:
        with db.get_cursor(commit=True) as cur:
            apply_tenant_rls(cur, *existing_tables(cur, _RLS_TABLES))
    except Exception as e:
        logger.warning(f"ensure_erp_credentials_rls skipped: {e}")
