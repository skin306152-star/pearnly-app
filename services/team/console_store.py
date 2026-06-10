# -*- coding: utf-8 -*-
"""控制台成员管理 DAL(批3 · docs/permissions/03 接口契约的数据层)。

成员真相 = memberships JOIN roles(批1);users 行只供资料字段。
所有写操作边界(改自己/动 owner/最后一个 owner)在这里集中拦,路由层翻 422。
"""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Optional

from core import db
from services.authz.registry import ASSIGNABLE_ROLE_KEYS, SCOPABLE_ROLE_KEYS
from services.authz.resolver import set_membership_role

logger = logging.getLogger("mr-pilot")


def list_members(tenant_id: str) -> List[Dict[str, Any]]:
    """全角色成员列表(含 owner)+ 作用域摘要。"""
    with db.get_cursor() as cur:
        cur.execute(
            """
            SELECT u.id, u.username, u.email, u.is_active, u.last_login_at, u.created_at,
                   m.id AS membership_id, m.scope_mode, r.key AS role_key,
                   COALESCE(s.ws_ids, '[]'::json) AS ws_ids
            FROM memberships m
            JOIN users u ON u.id = m.user_id
            JOIN roles r ON r.id = m.role_id
            LEFT JOIN (
                SELECT membership_id, json_agg(workspace_client_id) AS ws_ids
                FROM member_scopes WHERE tenant_id = %s GROUP BY membership_id
            ) s ON s.membership_id = m.id
            WHERE m.tenant_id = %s AND m.status = 'active'
            ORDER BY (r.key = 'owner') DESC, u.created_at ASC
            """,
            (str(tenant_id), str(tenant_id)),
        )
        rows = [dict(r) for r in cur.fetchall()]
    out = []
    for r in rows:
        ws_ids = r.get("ws_ids")
        if isinstance(ws_ids, str):
            ws_ids = json.loads(ws_ids)
        out.append(
            {
                "id": str(r["id"]),
                "username": r.get("username"),
                "email": r.get("email"),
                "role_key": r.get("role_key"),
                "scope_mode": r.get("scope_mode") or "all",
                "workspace_ids": [int(w) for w in (ws_ids or [])],
                "is_active": bool(r.get("is_active", True)),
                "last_login_at": (
                    r["last_login_at"].isoformat() if r.get("last_login_at") else None
                ),
                "created_at": r["created_at"].isoformat() if r.get("created_at") else None,
            }
        )
    return out


def get_member(tenant_id: str, user_id: str) -> Optional[Dict[str, Any]]:
    with db.get_cursor() as cur:
        cur.execute(
            """
            SELECT m.id AS membership_id, m.scope_mode, r.key AS role_key, u.username
            FROM memberships m
            JOIN roles r ON r.id = m.role_id
            JOIN users u ON u.id = m.user_id
            WHERE m.tenant_id = %s AND m.user_id = %s AND m.status = 'active'
            """,
            (str(tenant_id), str(user_id)),
        )
        row = cur.fetchone()
    return dict(row) if row else None


def change_role(
    *, tenant_id: str, actor_id: str, target_user_id: str, role_key: str
) -> Dict[str, Any]:
    """改角色。返回 {ok, role_from} 或 {error}(路由翻 422)。"""
    if str(actor_id) == str(target_user_id):
        return {"error": "team.cannot_modify_self"}
    if role_key not in ASSIGNABLE_ROLE_KEYS:
        return {"error": "team.role_not_assignable"}
    member = get_member(tenant_id, target_user_id)
    if member is None:
        return {"error": "team.member_not_found"}
    if member["role_key"] == "owner":
        return {"error": "team.target_is_owner"}
    with db.get_cursor(commit=True) as cur:
        ok = set_membership_role(
            cur,
            user_id=str(target_user_id),
            tenant_id=str(tenant_id),
            role_key=role_key,
            granted_by=str(actor_id),
        )
        if not ok:
            return {"error": "team.member_not_found"}
        # owner/admin 强制全租户作用域(02 矩阵):升管理员时清 assigned 残留
        if role_key not in SCOPABLE_ROLE_KEYS:
            cur.execute(
                "UPDATE memberships SET scope_mode = 'all' WHERE user_id = %s AND tenant_id = %s",
                (str(target_user_id), str(tenant_id)),
            )
            cur.execute(
                "DELETE FROM member_scopes WHERE tenant_id = %s AND membership_id = %s",
                (str(tenant_id), str(member["membership_id"])),
            )
    return {"ok": True, "role_from": member["role_key"], "username": member.get("username")}


def set_scope(
    *,
    tenant_id: str,
    actor_id: str,
    target_user_id: str,
    scope_mode: str,
    workspace_ids: List[int],
) -> Dict[str, Any]:
    """配作用域(全量替换)。返回 {ok, added, removed} 或 {error}。"""
    if str(actor_id) == str(target_user_id):
        return {"error": "team.cannot_modify_self"}
    if scope_mode not in ("all", "assigned"):
        return {"error": "team.scope_invalid"}
    member = get_member(tenant_id, target_user_id)
    if member is None:
        return {"error": "team.member_not_found"}
    if member["role_key"] == "owner":
        return {"error": "team.target_is_owner"}
    if scope_mode == "assigned" and member["role_key"] not in SCOPABLE_ROLE_KEYS:
        return {"error": "team.scope_not_allowed"}
    mid = str(member["membership_id"])
    with db.get_cursor(commit=True) as cur:
        valid_ids: List[int] = []
        if scope_mode == "assigned":
            wanted = [int(ws) for ws in (workspace_ids or [])]
            if wanted:
                cur.execute(
                    "SELECT id FROM workspace_clients WHERE id = ANY(%s) AND tenant_id = %s",
                    (wanted, str(tenant_id)),
                )
                valid_ids = sorted(int(r["id"]) for r in cur.fetchall())
            if not valid_ids:
                return {"error": "team.scope_empty"}
        cur.execute(
            "SELECT workspace_client_id FROM member_scopes WHERE tenant_id=%s AND membership_id=%s",
            (str(tenant_id), mid),
        )
        before = {int(r["workspace_client_id"]) for r in cur.fetchall()}
        cur.execute(
            "DELETE FROM member_scopes WHERE tenant_id = %s AND membership_id = %s",
            (str(tenant_id), mid),
        )
        for ws in valid_ids:
            cur.execute(
                """
                INSERT INTO member_scopes (tenant_id, membership_id, workspace_client_id,
                                           assigned_by)
                VALUES (%s, %s, %s, %s)
                """,
                (str(tenant_id), mid, ws, str(actor_id)),
            )
        cur.execute(
            "UPDATE memberships SET scope_mode = %s WHERE id = %s",
            (scope_mode, mid),
        )
    after = set(valid_ids)
    return {
        "ok": True,
        "username": member.get("username"),
        "added": sorted(after - before),
        "removed": sorted(before - after),
    }


def guard_member_action(tenant_id: str, actor_id: str, target_user_id: str) -> Optional[str]:
    """启停/移除的共用边界:改自己 / 动 owner = 拒。返回错误码或 None。"""
    if str(actor_id) == str(target_user_id):
        return "team.cannot_modify_self"
    member = get_member(tenant_id, target_user_id)
    if member is None:
        return "team.member_not_found"
    if member["role_key"] == "owner":
        return "team.target_is_owner"
    return None
