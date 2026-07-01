# -*- coding: utf-8 -*-
"""识别记录 · 本月聚合(Agent 汇总/用量工具的数据层 · 只读)。

「本月」= Asia/Bangkok 当前自然月(与计费 monthly_page_usage 同锚)。可见性复用
list_status.owner_visibility_where(与列表同一事实源),经 get_cursor_rls 走 RLS。
供 agent history_summary / usage_this_month 工具回填真实合计฿ / 单据数 / 分类分布。
"""

from __future__ import annotations

import logging
from typing import List, Optional

from core import db

from . import list_status as ls

logger = logging.getLogger(__name__)

# created_at 存 UTC;按 Asia/Bangkok 本地时间落在当前自然月内才算「本月」。
_BKK_LOCAL = "(created_at AT TIME ZONE 'Asia/Bangkok')"
_MONTH_START = "date_trunc('month', (now() AT TIME ZONE 'Asia/Bangkok'))"

_EMPTY = {"doc_count": 0, "amount_total": 0.0, "by_category": []}


def month_overview(
    user_id: str,
    tenant_id: Optional[str] = None,
    *,
    workspace_client_id: Optional[int] = None,
    restrict_client_ids: Optional[List[int]] = None,
    retention_days: Optional[int] = None,
    include_categories: bool = True,
) -> dict:
    """本月单据数 + 合计金额(+ 可选分类分布 top5)。

    retention_days==0(不可查历史)→ 返空。分类分布仅在有单据且 include_categories 时查
    (用量工具只需张数,跳过省一次分组查询)。
    """
    if retention_days == 0:
        return dict(_EMPTY)
    where, params = ls.owner_visibility_where(
        user_id, tenant_id, workspace_client_id, restrict_client_ids
    )
    where.append(f"{_BKK_LOCAL} >= {_MONTH_START}")
    where_sql = " AND ".join(where)
    try:
        with db.get_cursor_rls(tenant_id=tenant_id, user_id=user_id) as cur:
            cur.execute(
                f"SELECT COUNT(*) AS doc_count, COALESCE(SUM(total_amount), 0) AS amount_total "
                f"FROM ocr_history WHERE {where_sql}",
                params,
            )
            row = cur.fetchone()
            out = {
                "doc_count": int(row["doc_count"]),
                "amount_total": float(row["amount_total"]),
                "by_category": [],
            }
            if include_categories and out["doc_count"]:
                cur.execute(
                    f"SELECT category_tag, COUNT(*) AS c FROM ocr_history "
                    f"WHERE {where_sql} AND COALESCE(category_tag, '') <> '' "
                    f"GROUP BY category_tag ORDER BY c DESC LIMIT 5",
                    params,
                )
                out["by_category"] = [(r["category_tag"], int(r["c"])) for r in cur.fetchall()]
            return out
    except Exception as e:
        logger.error(f"month_overview 失败 (user_id={user_id}): {e}")
        return dict(_EMPTY)
