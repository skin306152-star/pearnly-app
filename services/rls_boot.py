# -*- coding: utf-8 -*-
"""B8 RLS 孤儿表 enroll 注册表(REFACTOR-B8)。

集中 startup 期所有「纯 enroll」的 ensure_*_rls(给 legacy 无-CREATE-钩子表补回 policy)。各函数
独立事务幂等、内部 existing_tables 先验存在,目标全是 alembic/历史建的 legacy 表,与 boot_ensures
建表无时序依赖 → 统一在建表 ensure 之后、ensure_no_orphan_rls(会 DISABLE 零-policy 孤儿)之前跑。

注:建表同时 enroll 的(archive_settings)、内联进建表函数的(member_scopes/invitations/
ownership_transfers/client_assignments 在 authz/membership schema 里)不在此列。
"""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


# 新增纯 enroll:把 ensure_*_rls 加进此清单 + 在 services/dal_reexports 注册成 db.*。
# 按名字(非函数引用)登记:漏注册 dal_reexports 时只跳过该项(响亮告警),不连坐其余 enroll
# 与末步 ensure_no_orphan_rls 自愈守卫。
_ENROLLS = (
    "ensure_erp_push_rls",
    "ensure_bank_recon_rls",
    "ensure_email_ingest_rls",
    "ensure_sales_rls",
    "ensure_line_binding_rls",
    "ensure_client_rules_rls",
    "ensure_automation_rls",
    "ensure_etax_rls",
    "ensure_risk_check_rls",
    "ensure_knowledge_rls",
    "ensure_settings_misc_rls",
    "ensure_erp_credentials_rls",
)


def run_rls_enrolls() -> None:
    """跑全部纯 enroll 的 ensure_*_rls(各自独立事务·一个失败不连坐其余)。"""
    from core import db

    for name in _ENROLLS:
        ensure_fn = getattr(db, name, None)
        if ensure_fn is None:
            logger.warning(f"启动 RLS enroll {name} 未在 dal_reexports 注册 · 跳过")
            continue
        try:
            ensure_fn()
        except Exception as e:
            logger.warning(f"启动 RLS enroll {name} 失败: {e}")
