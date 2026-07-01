# -*- coding: utf-8 -*-
"""LINE 会话态「当前套账」—— 等价网页顶栏套账切换器的 LINE 版。

一个租户下可有多个套账(workspace_client)。网页靠 X-Workspace-Client-Id 头切;LINE 没有头,
就把用户选定的套账记在 line_bindings.current_workspace_client_id 上。写入(记账/上传)落「当前
套账」(未选则回落最早建的默认套账);查询在 Agent 侧跨套账聚合(见 executor)。
"""

from __future__ import annotations

from typing import Optional


def _norm(s: str) -> str:
    return "".join((s or "").lower().split())


def current_workspace_id(cur, *, line_user_id) -> Optional[int]:
    """该 LINE 用户选定的当前套账 id;未选 → None。

    按 line_user_id 单键(全局唯一;line_bindings.tenant_id 历史行普遍为 NULL,不能进 WHERE)。
    """
    cur.execute(
        "SELECT current_workspace_client_id FROM line_bindings WHERE line_user_id = %s",
        (line_user_id,),
    )
    row = cur.fetchone()
    val = row.get("current_workspace_client_id") if row else None
    try:
        return int(val) if val is not None else None
    except (TypeError, ValueError):
        return None


def resolve_write_workspace(cur, *, tenant_id, line_user_id) -> Optional[int]:
    """写入路径套账 = 当前套账,未选则回落租户默认套账(最早建的那个)。

    当前套账读取出任何岔子都不许挡记账 → 回落默认套账(fail-safe)。
    """
    from core.workspace_context import default_workspace_id

    try:
        chosen = current_workspace_id(cur, line_user_id=line_user_id)
    except Exception:
        chosen = None
    return chosen or default_workspace_id(cur, tenant_id)


def list_active(cur, *, tenant_id) -> list:
    """本租户的活跃套账(id + name),按建档序。"""
    cur.execute(
        "SELECT id, name FROM workspace_clients "
        "WHERE tenant_id = %s AND is_active ORDER BY created_at, id",
        (tenant_id,),
    )
    return [{"id": int(r["id"]), "name": r["name"]} for r in cur.fetchall()]


def set_current(cur, *, line_user_id, workspace_client_id) -> bool:
    """把该 LINE 用户的当前套账钉到 workspace_client_id。返回是否命中绑定行。

    按 line_user_id 单键(全局唯一;tenant_id 历史行为 NULL,进 WHERE 会写不中)。
    """
    cur.execute(
        "UPDATE line_bindings SET current_workspace_client_id = %s WHERE line_user_id = %s",
        (workspace_client_id, line_user_id),
    )
    return cur.rowcount > 0


def match_by_name(cur, *, tenant_id, name) -> Optional[dict]:
    """按名字模糊(归一子串)匹配活跃套账;唯一命中才返回,零/多命中 → None(交由调用方追问)。"""
    q = _norm(name)
    if not q:
        return None
    hits = [w for w in list_active(cur, tenant_id=tenant_id) if q in _norm(w["name"])]
    return hits[0] if len(hits) == 1 else None
