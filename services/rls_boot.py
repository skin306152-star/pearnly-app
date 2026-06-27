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


def run_rls_enrolls() -> None:
    """跑全部纯 enroll 的 ensure_*_rls(各自独立事务·一个失败不连坐其余)。"""
    from core import db

    enrolls = (
        db.ensure_erp_push_rls,
        db.ensure_bank_recon_rls,
        db.ensure_email_ingest_rls,
        db.ensure_sales_rls,
        db.ensure_line_binding_rls,
        db.ensure_client_rules_rls,
        db.ensure_automation_rls,
        db.ensure_etax_rls,
        db.ensure_risk_check_rls,
        db.ensure_knowledge_rls,
        db.ensure_settings_misc_rls,
        db.ensure_erp_credentials_rls,
    )
    for ensure_fn in enrolls:
        try:
            ensure_fn()
        except Exception as e:
            logger.warning(f"启动 RLS enroll {ensure_fn.__name__} 失败: {e}")
