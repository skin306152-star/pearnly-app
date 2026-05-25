# -*- coding: utf-8 -*-
"""操作/审计日志(operation_logs)· 数据访问层

从 db.py 抽出(REFACTOR-B2 · 纯搬家 · 0 逻辑改)。
记录谁(actor)对什么(target)做了什么(action)· 含超管标记 · tenant 过滤 ·
分页+搜索+时间过滤(管理员操作日志/审计日志面板)。
db.py 文件尾 re-export 回本命名空间 · 所有 `db.xxx()` 调用点不变。
"""

import json as _json
import logging
from typing import Optional, Dict, Any, List

import db

logger = logging.getLogger(__name__)


def insert_operation_log(
    tenant_id: Optional[str],
    actor_user_id: Optional[str],
    actor_username: Optional[str],
    actor_is_super: bool,
    action: str,
    target_type: Optional[str] = None,
    target_id: Optional[str] = None,
    target_name: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
    ip: Optional[str] = None,
    ua: Optional[str] = None,
) -> bool:
    """记一条操作日志 · 失败不阻塞主流程"""
    try:
        with db.get_cursor(commit=True) as cur:
            cur.execute(
                """
                INSERT INTO operation_logs (
                    tenant_id, actor_user_id, actor_username, actor_is_super,
                    action, target_type, target_id, target_name, details, ip, ua
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s::jsonb, %s, %s)
            """,
                (
                    str(tenant_id) if tenant_id else None,
                    str(actor_user_id) if actor_user_id else None,
                    actor_username,
                    bool(actor_is_super),
                    action,
                    target_type,
                    str(target_id) if target_id else None,
                    target_name,
                    _json.dumps(details or {}, ensure_ascii=False),
                    ip,
                    (ua or "")[:300],
                ),
            )
            return True
    except Exception as e:
        logger.warning(f"insert_operation_log failed (action={action}): {e}")
        return False


def list_operation_logs(
    tenant_id: Optional[str] = None,
    limit: int = 200,
) -> List[Dict[str, Any]]:
    """
    查操作日志
    - tenant_id 传则过滤该租户 · 不传则全局(仅超管用全局)
    """
    try:
        with db.get_cursor() as cur:
            if tenant_id:
                cur.execute(
                    """
                    SELECT * FROM operation_logs
                    WHERE tenant_id = %s
                    ORDER BY created_at DESC
                    LIMIT %s
                """,
                    (str(tenant_id), int(limit)),
                )
            else:
                cur.execute(
                    """
                    SELECT * FROM operation_logs
                    ORDER BY created_at DESC
                    LIMIT %s
                """,
                    (int(limit),),
                )
            return [dict(r) for r in cur.fetchall()]
    except Exception as e:
        logger.error(f"list_operation_logs failed: {e}")
        return []


# v118.29.0 · 操作日志分页 + 搜索 + 时间过滤
def list_operation_logs_paged(
    tenant_id: Optional[str] = None,
    page: int = 1,
    per_page: int = 50,
    q: Optional[str] = None,
    action: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    limit_all: int = 0,  # >0 时返回全部(给 CSV 导出用 · 不分页)
    actor_is_super: Optional[bool] = None,  # v118.28.8 · 给客户老板看 Pearnly 访问日志用
) -> Dict[str, Any]:
    page = max(1, int(page or 1))
    per_page = max(1, min(500, int(per_page or 50)))
    offset = (page - 1) * per_page

    where = []
    params: List[Any] = []
    if tenant_id:
        where.append("tenant_id = %s")
        params.append(str(tenant_id))
    if q:
        where.append(
            "(LOWER(COALESCE(actor_username, '')) LIKE %s OR LOWER(COALESCE(action, '')) LIKE %s OR LOWER(COALESCE(target_name, '')) LIKE %s)"
        )
        like = f"%{q.lower()}%"
        params += [like, like, like]
    if action:
        where.append("action = %s")
        params.append(action)
    if date_from:
        where.append("created_at >= %s")
        params.append(date_from)
    if date_to:
        where.append("created_at <= %s")
        params.append(date_to)
    if actor_is_super is True:
        where.append("COALESCE(actor_is_super, false) = true")
    elif actor_is_super is False:
        where.append("COALESCE(actor_is_super, false) = false")
    where_sql = (" WHERE " + " AND ".join(where)) if where else ""

    try:
        with db.get_cursor() as cur:
            cur.execute(f"SELECT COUNT(*) AS c FROM operation_logs{where_sql}", params)
            total_row = cur.fetchone()
            total = int((total_row.get("c") if isinstance(total_row, dict) else total_row[0]) or 0)

            if limit_all and limit_all > 0:
                cur.execute(
                    f"SELECT * FROM operation_logs{where_sql} ORDER BY created_at DESC LIMIT %s",
                    params + [int(limit_all)],
                )
            else:
                cur.execute(
                    f"SELECT * FROM operation_logs{where_sql} ORDER BY created_at DESC LIMIT %s OFFSET %s",
                    params + [per_page, offset],
                )
            rows = [dict(r) for r in cur.fetchall()]
        return {"rows": rows, "total": total, "page": page, "per_page": per_page}
    except Exception as e:
        logger.error(f"list_operation_logs_paged failed: {e}")
        return {"rows": [], "total": 0, "page": page, "per_page": per_page}
