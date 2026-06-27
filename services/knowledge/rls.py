# -*- coding: utf-8 -*-
"""knowledge RAG 知识库域 RLS enroll(REFACTOR-B8 · 孤儿表 re-enroll)。

6 张表只在 alembic 0001/0002/0004 建、prod 无 startup CREATE 钩子 → 事故止血时被全量 DISABLE,
此处补回 policy。对齐 ensure_client_rules_rls / ensure_risk_check_rls 的「独立 ensure_*_rls」范式。

模板 = 纯 tenant:6 表全部 tenant_id NOT NULL、无 user_id、workspace_client_id 可空(大多 NULL=
firm-wide)。**不能 tenant_ws**:读路径(access.workspace_filter)故意含 `workspace_client_id IS NULL`
firm-wide 行,_WS_MATCH 会隐藏 NULL 行 → 业务破(同 client_rules)。子表 chunks/embeddings/ingest_jobs
虽有 document_id/chunk_id fk 但自带 tenant_id 列 → 直接 tenant,不需 via-parent。

force=False:11 个访问点已全走 get_cursor_rls(tenant)(knowledge_routes/knowledge_ask_routes),
无后台 worker(ingest 内联请求事务)→ enroll-only,零业务代码改动。
"""

from __future__ import annotations

import logging

from core import db

logger = logging.getLogger(__name__)

_RLS_TABLES = (
    "knowledge_bases",
    "knowledge_documents",
    "knowledge_ingest_jobs",
    "knowledge_chunks",
    "knowledge_embeddings",
    "knowledge_answers",
)


def ensure_knowledge_rls() -> None:
    """给 knowledge RAG 6 表上 tenant policy(幂等 · 独立事务防牵连别的 ensure)。逐表先验存在防部分库整块失败。"""
    from core.rls import apply_tenant_rls, existing_tables

    try:
        with db.get_cursor(commit=True) as cur:
            apply_tenant_rls(cur, *existing_tables(cur, _RLS_TABLES))
    except Exception as e:
        logger.warning(f"ensure_knowledge_rls skipped: {e}")
