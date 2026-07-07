# -*- coding: utf-8 -*-
"""一句话记账 schema 双跑入口(LINE 文本路会话态 + 学习词典 · docs/smart-intake/14)。

prod 无 alembic 钩子 → startup 经 ensure_expense_schema() 幂等建表。统一智能通道下,记账解析
后直接落采购进项草稿单(无独立捕获表),这里只保留多轮澄清会话态与可学习归类词典。
隔离靠应用层 WHERE tenant_id + workspace_client_id,RLS 兜底(prod 现 BYPASSRLS)。
"""

from __future__ import annotations

import logging

from core.rls import apply_tenant_rls

logger = logging.getLogger("mr-pilot")

# 多轮澄清会话态(短 TTL):缺金额时存半成品,用户补一句后合并。每 LINE 用户至多一条(PK)。
_PENDING_TABLE = """
CREATE TABLE IF NOT EXISTS line_pending_entry (
    line_user_id text PRIMARY KEY,
    tenant_id uuid NOT NULL,
    workspace_client_id bigint NOT NULL,
    draft jsonb NOT NULL DEFAULT '{}'::jsonb,
    missing text NOT NULL DEFAULT '',
    created_at timestamptz NOT NULL DEFAULT now()
)
"""

# 可学习归类词典:用户改过的 关键词→科目 记下,下次同词直接对(越用越省)。
_LEARNED_TABLE = """
CREATE TABLE IF NOT EXISTS expense_learned (
    tenant_id uuid NOT NULL,
    workspace_client_id bigint NOT NULL,
    keyword text NOT NULL,
    category_id uuid,
    subcategory_id uuid,
    category_name text NOT NULL DEFAULT '',
    subcategory_name text NOT NULL DEFAULT '',
    updated_at timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (tenant_id, workspace_client_id, keyword)
)
"""


def ensure_expense_schema() -> None:
    """幂等建 line_pending_entry / expense_learned + RLS(startup 调)。"""
    from core import db

    with db.get_cursor(commit=True) as cur:
        cur.execute(_PENDING_TABLE)
        cur.execute(_LEARNED_TABLE)
        # source:'user_rule'=用户在费用数据页可编辑的关键词规则,''/'correction'=纠错自学(见 0055)。
        cur.execute(
            "ALTER TABLE expense_learned ADD COLUMN IF NOT EXISTS source text NOT NULL DEFAULT ''"
        )
        apply_tenant_rls(cur, "line_pending_entry", "expense_learned")
