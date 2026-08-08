# -*- coding: utf-8 -*-
"""今日推送统计(从 push_log_queries 拆出控行数;facade 由该模块顶部 re-import 保持不变)。"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


def get_push_stats_today(
    user_id: str,
    tenant_id: Optional[str] = None,
    workspace_client_id: Optional[int] = None,
) -> Dict[str, Any]:
    """今日推送统计(总数 · 成功 · 失败)

    PO-4 同源 · workspace_client_id 给了 → 只数本套账的推送(+ 未归属 NULL 行);
    列在 ocr_history h 上(erp_push_logs 无该列)→ 过滤时补 LEFT JOIN ocr_history。
    tenant_id 只喂 RLS 上下文(JOIN 的 ocr_history 是 tenant_or_user 隔离 · 同 list_push_logs)。
    """
    try:
        with db.get_cursor_rls(tenant_id=tenant_id, user_id=user_id) as cur:
            ws_join = ""
            ws_where = ""
            params: list = [user_id]
            if workspace_client_id is not None:
                ws_join = " LEFT JOIN ocr_history h ON h.id = l.history_id"
                ws_where = " AND (h.workspace_client_id = %s OR h.workspace_client_id IS NULL)"
                params.append(int(workspace_client_id))
            cur.execute(
                f"""
                SELECT
                    COUNT(*) AS total,
                    COUNT(*) FILTER (WHERE l.status='success') AS success,
                    COUNT(*) FILTER (WHERE l.status='failed') AS failed,
                    COUNT(*) FILTER (WHERE l.trigger='auto') AS auto_cnt
                FROM erp_push_logs l
                {ws_join}
                WHERE l.user_id = %s
                  AND l.created_at >= CURRENT_DATE
                  {ws_where}
            """,
                tuple(params),
            )
            row = cur.fetchone()
            return dict(row) if row else {"total": 0, "success": 0, "failed": 0, "auto_cnt": 0}
    except Exception as e:
        logger.error(f"get_push_stats_today failed: {e}")
        return {"total": 0, "success": 0, "failed": 0, "auto_cnt": 0}


from core import db  # noqa: E402  # 底部引入防循环(同 push_log_queries 惯用法)
