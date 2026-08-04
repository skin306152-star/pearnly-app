# -*- coding: utf-8 -*-
"""会话列表 / 改名 / 删除与消息游标分页的 DAL(S1 会话流改版新增)。

store.py 已顶在 500 行预算线上,这批新增的读写单独成层;表结构仍在 schema.py,
索引 ix_steward_sessions_tenant (tenant_id, last_active_at DESC) 正是列表要走的那条。

三条口径:
- 列表只列「说过话」的会话:挂载时预建、一句没说的空会话不进历史(那是草稿位不是记录),
  空会话本身保留,回来接着用不受影响。
- 归属三锚同 store.get_session:(租户, 会话, 建会话的人)。会话是私人工作记录,
  改名/删除同样只有本人可以。
- 分页游标用 (created_at, id) 双键:created_at 在同一事务里可能同值,单键会漏行。
"""

from __future__ import annotations

from typing import Any, Optional

from services.steward.store import _MESSAGE_COLUMNS, _SESSION_COLUMNS

_MAX_TITLE = 120
_DEFAULT_SESSIONS_LIMIT = 60
_DEFAULT_PAGE_LIMIT = 60


def list_sessions(
    cur, *, tenant_id: str, user_id: str, limit: int = _DEFAULT_SESSIONS_LIMIT
) -> list[dict]:
    """本人会话列表,最近活跃在前。EXISTS 过滤零消息的空会话(见顶注)。"""
    cur.execute(
        f"SELECT {_SESSION_COLUMNS} FROM steward_sessions s "
        "WHERE s.tenant_id = %s AND s.user_id = %s "
        "AND EXISTS (SELECT 1 FROM steward_messages m "
        "            WHERE m.tenant_id = s.tenant_id AND m.session_id = s.id) "
        "ORDER BY s.last_active_at DESC, s.id DESC LIMIT %s",
        (tenant_id, str(user_id), int(limit)),
    )
    return [dict(r) for r in cur.fetchall()]


def rename_session(cur, *, tenant_id: str, session_id: str, user_id: str, title: str) -> bool:
    cur.execute(
        "UPDATE steward_sessions SET title = %s "
        "WHERE tenant_id = %s AND id = %s AND user_id = %s",
        (title[:_MAX_TITLE], tenant_id, session_id, str(user_id)),
    )
    return cur.rowcount > 0


def delete_session(cur, *, tenant_id: str, session_id: str, user_id: str) -> Optional[list[str]]:
    """删会话。行级由外键 ON DELETE CASCADE 连消息/任务/附件行一起收;盘上的附件原件
    数据库删不到,先把 file_ref 收回来交给调用方在【事务提交后】删文件 —— 反过来
    (先删文件再回滚)会留下一批行还在、件已没的死引用。返回 None = 会话不存在/不是本人。"""
    cur.execute(
        "SELECT file_ref FROM steward_attachments WHERE tenant_id = %s AND session_id = %s",
        (tenant_id, session_id),
    )
    refs = [str(r["file_ref"]) for r in cur.fetchall() if r.get("file_ref")]
    cur.execute(
        "DELETE FROM steward_sessions WHERE tenant_id = %s AND id = %s AND user_id = %s",
        (tenant_id, session_id, str(user_id)),
    )
    return refs if cur.rowcount > 0 else None


def list_messages_page(
    cur,
    *,
    tenant_id: str,
    session_id: str,
    before_id: Optional[str] = None,
    limit: int = _DEFAULT_PAGE_LIMIT,
) -> tuple[list[dict], bool]:
    """按 (created_at, id) 游标取一页消息,升序返回 + 还有没有更早的。
    before_id 指向已拿到的最早那条;它不存在(被删/伪造)按无游标处理,不报错 ——
    游标只是翻页位置,坏了从最新页重来即可。"""
    n = max(1, int(limit))
    anchor = None
    if before_id:
        cur.execute(
            "SELECT created_at, id FROM steward_messages "
            "WHERE tenant_id = %s AND session_id = %s AND id = %s",
            (tenant_id, session_id, before_id),
        )
        row = cur.fetchone()
        anchor = (row["created_at"], row["id"]) if row else None
    where = "tenant_id = %s AND session_id = %s"
    params: list[Any] = [tenant_id, session_id]
    if anchor:
        where += " AND (created_at, id) < (%s, %s)"
        params.extend(anchor)
    cur.execute(
        f"SELECT {_MESSAGE_COLUMNS} FROM steward_messages WHERE {where} "
        "ORDER BY created_at DESC, id DESC LIMIT %s",
        (*params, n + 1),
    )
    rows = [dict(r) for r in cur.fetchall()]
    has_more = len(rows) > n
    return list(reversed(rows[:n])), has_more


def public_session(row: dict) -> dict[str, Any]:
    """会话 → 侧栏列表视图。title 可能还空着(建了会话、第一句话还没落)——原样给空串,
    前端按「新对话」词条显示,不在这里替它编标题。"""
    return {
        "session_id": str(row["id"]),
        "title": row.get("title") or "",
        "last_active_at": (
            row["last_active_at"].isoformat() if row.get("last_active_at") else None
        ),
    }
