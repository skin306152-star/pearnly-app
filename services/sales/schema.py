# -*- coding: utf-8 -*-
"""销项开票域 RLS enroll(REFACTOR-B8 · 孤儿表 re-enroll)。

sales 核心表(documents/lines/sends/settings)+ 连号计数器只在 alembic 0006/0017/0018 建,
prod 无 startup CREATE 钩子、也无 alembic 钩子 → 事故止血时被全量 DISABLE,此处补回 policy。
对齐 ensure_bank_recon_rls / ensure_erp_push_rls / ensure_email_ingest_rls 的「独立 ensure_*_rls」范式。
"""

from __future__ import annotations

import logging

from core import db

logger = logging.getLogger(__name__)

# 全 5 张表 tenant_id NOT NULL、无 user_id → 纯 tenant 模板。
# sales_documents 的账套列叫 seller_workspace_client_id(非 workspace_client_id),
# document_number_sequences 的 workspace_client_id 运行时加且可空 → 都不用 tenant_ws(账套强隔离
# 已由应用层 5 列唯一索引 uq_dns_ws 保证),统一 apply_tenant_rls。
_RLS_TABLES = (
    "sales_documents",
    "sales_document_lines",
    "sales_document_sends",
    "sales_settings",
    "document_number_sequences",
)


def ensure_sales_rls() -> None:
    """给 sales 域孤儿表上 tenant policy(幂等 · 独立事务防牵连别的 ensure)。

    5 张表来自不同 alembic 版本(0006/0017/0018 + 运行时迁移),逐表先验存在再 enroll —— 某张未建
    (部分库)不连累其余。force=False:owner 仍绕过 → 回填迁移(workspace_backfill)、公开 share-token
    取件(sales_send_routes 走 bypass=True)等系统/无租户上下文路径不破;业务连接 SET ROLE 后强制。
    """
    from core.rls import apply_tenant_rls

    try:
        with db.get_cursor(commit=True) as cur:
            for table in _RLS_TABLES:
                cur.execute(
                    "SELECT 1 FROM information_schema.tables "
                    "WHERE table_schema='public' AND table_name=%s",
                    (table,),
                )
                if cur.fetchone() is None:
                    continue
                apply_tenant_rls(cur, table)
    except Exception as e:
        logger.warning(f"ensure_sales_rls skipped: {e}")
