# -*- coding: utf-8 -*-
"""安全事件日志查询(G2 · docs/permissions/07 §四)。

operation_logs 的团队/权限事件视图。SQL 层按 action 域前缀过滤(防业务日志把
事件挤出窗口,旧实现取近 1000 条再 Python 过滤会丢早期事件)+ 类型/操作者/
时间筛选 + 游标分页 + CSV 导出(UTF-8 BOM,Excel 直开不乱码)。
事件 = action 一等类型(Stripe Security history 形态),不另建表。
"""

from __future__ import annotations

import base64
import binascii
import csv
import io
import json
import logging
from typing import Any, Dict, List, Optional, Tuple

from core import db

logger = logging.getLogger("mr-pilot")

# 安全事件 = 这些域的 action(member./employee. 含 legacy 读侧兼容,role. 留给 ② 的自定义角色)
SECURITY_CATEGORIES = ("team", "role", "scope", "ownership", "member", "employee")
EXPORT_MAX_ROWS = 5000
DEFAULT_PAGE_SIZE = 50
MAX_PAGE_SIZE = 200

CSV_COLUMNS = ("created_at", "action", "actor", "target", "ip", "details")

_SELECT = (
    "SELECT id, action, actor_username, target_name, details, ip, created_at "
    "FROM operation_logs WHERE {where} ORDER BY created_at DESC, id::text DESC LIMIT %s"
)


def encode_cursor(created_at_iso: str, event_id: Any) -> str:
    """游标 = (created_at, id) 的不透明 base64 串。"""
    raw = f"{created_at_iso}|{event_id}".encode("utf-8")
    return base64.urlsafe_b64encode(raw).decode("ascii")


def decode_cursor(cursor: Optional[str]) -> Optional[Tuple[str, str]]:
    """解游标 → (created_at_iso, id);非法/缺失返回 None(视作首页)。"""
    if not cursor:
        return None
    try:
        raw = base64.urlsafe_b64decode(cursor.encode("ascii")).decode("utf-8")
    except (binascii.Error, UnicodeDecodeError, ValueError):
        return None
    created_at, sep, event_id = raw.partition("|")
    if not sep:
        return None
    return created_at, event_id


def _filters(
    tenant_id: str,
    category: Optional[str],
    actor: Optional[str],
    date_from: Optional[str],
    date_to: Optional[str],
) -> Tuple[List[str], List[Any]]:
    """共用 WHERE 片段:租户隔离 + 安全域 + 类型/操作者/时间。全部参数化。"""
    where = ["tenant_id = %s"]
    params: List[Any] = [str(tenant_id)]
    if category in SECURITY_CATEGORIES:
        where.append("split_part(action, '.', 1) = %s")
        params.append(category)
    else:
        where.append("split_part(action, '.', 1) = ANY(%s)")
        params.append(list(SECURITY_CATEGORIES))
    if actor:
        where.append("LOWER(COALESCE(actor_username, '')) LIKE %s")
        params.append(f"%{actor.lower()}%")
    if date_from:
        where.append("created_at >= %s")
        params.append(date_from)
    if date_to:
        where.append("created_at <= %s")
        params.append(date_to)
    return where, params


def _serialize(row: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "id": row.get("id"),
        "action": row.get("action"),
        "actor": row.get("actor_username"),
        "target": row.get("target_name"),
        "details": row.get("details"),
        "ip": row.get("ip"),
        "created_at": row["created_at"].isoformat() if row.get("created_at") else None,
    }


def list_events(
    *,
    tenant_id: str,
    category: Optional[str] = None,
    actor: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    cursor: Optional[str] = None,
    limit: int = DEFAULT_PAGE_SIZE,
) -> Dict[str, Any]:
    """游标分页拉一页安全事件。返回 {events, next_cursor}(无下一页则 next_cursor=None)。"""
    limit = max(1, min(int(limit or DEFAULT_PAGE_SIZE), MAX_PAGE_SIZE))
    where, params = _filters(tenant_id, category, actor, date_from, date_to)
    decoded = decode_cursor(cursor)
    if decoded:
        c_created, c_id = decoded
        # (created_at, id) 复合游标 · id 统一按 text 比较以兼容底层列类型(uuid/bigint)
        where.append("(created_at < %s OR (created_at = %s AND id::text < %s))")
        params += [c_created, c_created, c_id]
    sql = _SELECT.format(where=" AND ".join(where))
    try:
        with db.get_cursor() as cur:
            cur.execute(sql, params + [limit + 1])
            rows = [dict(r) for r in cur.fetchall()]
    except Exception as e:
        logger.error(f"list_security_events failed: {e}")
        return {"events": [], "next_cursor": None}
    next_cursor = None
    if len(rows) > limit:
        last = rows[limit - 1]
        next_cursor = encode_cursor(
            last["created_at"].isoformat() if last.get("created_at") else "",
            last.get("id"),
        )
        rows = rows[:limit]
    return {"events": [_serialize(r) for r in rows], "next_cursor": next_cursor}


def export_events(
    *,
    tenant_id: str,
    category: Optional[str] = None,
    actor: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    max_rows: int = EXPORT_MAX_ROWS,
) -> str:
    """同筛选参数导出 CSV(上限 max_rows 行)。返回带 BOM 的 CSV 文本。"""
    where, params = _filters(tenant_id, category, actor, date_from, date_to)
    sql = _SELECT.format(where=" AND ".join(where))
    try:
        with db.get_cursor() as cur:
            cur.execute(sql, params + [int(max_rows)])
            rows = [dict(r) for r in cur.fetchall()]
    except Exception as e:
        logger.error(f"export_security_events failed: {e}")
        rows = []
    return build_csv(rows)


def build_csv(rows: List[Dict[str, Any]]) -> str:
    """operation_logs 原始行 → CSV(BOM + 表头)。纯函数(无 DB · 便于单测)。"""
    buf = io.StringIO()
    buf.write("﻿")  # BOM · Excel 中/泰文不乱码
    writer = csv.writer(buf)
    writer.writerow(list(CSV_COLUMNS))
    for r in rows:
        created = r.get("created_at")
        writer.writerow(
            [
                created.isoformat() if hasattr(created, "isoformat") else (created or ""),
                r.get("action") or "",
                r.get("actor_username") or "",
                r.get("target_name") or "",
                r.get("ip") or "",
                json.dumps(r.get("details"), ensure_ascii=False) if r.get("details") else "",
            ]
        )
    return buf.getvalue()
