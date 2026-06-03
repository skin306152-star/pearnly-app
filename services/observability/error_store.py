# -*- coding: utf-8 -*-
"""services/observability/error_store.py · REFACTOR-WA-B7 · 错误事件持久化。

自建简单版错误聚合(不上 Sentry):未捕获 500 异常落 error_events 表 · 超管时间线读。
全程 fail-open:写不进 / 表不存在 / DB 抖动 都不能影响主流程或异常处理本身。
request_id / user_id / tenant_id 自动从 B6 日志上下文取(全链路关联)。

表 DDL:scripts/sql/b7_error_events.sql(带外应用 · 不进启动 ensure)。
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from core import db
from services.observability import log_context

logger = logging.getLogger("mr-pilot")

_INSERT = """
    INSERT INTO error_events
        (level, logger, message, request_id, user_id, tenant_id,
         path, method, status_code, exc_type, traceback)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
"""

_SELECT = """
    SELECT id, created_at, level, logger, message, request_id, user_id, tenant_id,
           path, method, status_code, exc_type, traceback
    FROM error_events
    ORDER BY created_at DESC
    LIMIT %s
"""


def record_error(
    *,
    message: str,
    level: str = "ERROR",
    source_logger: Optional[str] = None,
    path: Optional[str] = None,
    method: Optional[str] = None,
    status_code: Optional[int] = None,
    exc_type: Optional[str] = None,
    traceback: Optional[str] = None,
) -> None:
    """持久化一条错误事件 · fail-open(任何异常都吞 · 绝不冒泡到调用方)。

    request_id / user_id / tenant_id 取自当前 B6 日志上下文。
    """
    try:
        ctx = log_context.current()
        with db.get_cursor(commit=True) as cur:
            cur.execute(
                _INSERT,
                (
                    level,
                    source_logger,
                    (message or "")[:2000],
                    ctx.get("request_id"),
                    ctx.get("user_id"),
                    ctx.get("tenant_id"),
                    path,
                    method,
                    status_code,
                    exc_type,
                    (traceback or "")[:8000] or None,
                ),
            )
    except Exception as e:  # fail-open · 不能因记录错误而再抛错(防递归/拖垮主流程)
        logger.warning("record_error skipped (non-blocking): %s", str(e)[:200])


def list_recent_errors(limit: int = 100) -> List[Dict[str, Any]]:
    """读最近错误事件 · fail-open(表不存在/DB 抖动 → 返回 [])。"""
    try:
        limit = max(1, min(int(limit), 500))
        with db.get_cursor() as cur:
            cur.execute(_SELECT, (limit,))
            return [dict(r) for r in cur.fetchall()]
    except Exception as e:
        logger.warning("list_recent_errors failed (non-blocking): %s", str(e)[:200])
        return []
