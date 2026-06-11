# -*- coding: utf-8 -*-
"""自定义角色 DAL(G3 · docs/permissions/07 §四)。

真相 = roles 表 tenant 级行(key='custom:<slug>' · permissions JSONB 勾选码集);resolver 零改动
读它即生效。本模块只管自定义行的增删改查与分配,系统预设行(tenant_id IS NULL)一概不碰。

权限码集合法性在写入口收口:registry 外的码丢弃(deny-by-default),两个提权码
(ownership.transfer / billing.manage · 连 admin 都没有)禁入自定义角色,杜绝越权造角色。
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any, Dict, List, Optional

from core import db
from services.authz.registry import ALL_CODES
from services.authz.resolver import set_membership_role
from services.team import console_store

logger = logging.getLogger("mr-pilot")

# 连 admin 都没有的提权码,不许塞进自定义角色(防越权造角色)
FORBIDDEN_CUSTOM_CODES = frozenset({"ownership.transfer", "billing.manage"})

_MAX_NAME = 40


def _slugify(name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", (name or "").strip().lower()).strip("-")
    return slug or "role"


def _sanitize_codes(codes: Any) -> List[str]:
    """入参码集 → 合法、去重、排序、剔除提权码。"""
    if not isinstance(codes, (list, tuple, set)):
        return []
    valid = {c for c in codes if c in ALL_CODES} - FORBIDDEN_CUSTOM_CODES
    return sorted(valid)


def _unique_slug(cur, tenant_id: str, base: str) -> str:
    """(tenant, key) 唯一:取本租户已用 custom slug,base 撞了就 -2/-3 顺延。"""
    cur.execute(
        "SELECT key FROM roles WHERE tenant_id = %s AND key LIKE 'custom:%%'",
        (str(tenant_id),),
    )
    used = {r["key"] for r in cur.fetchall()}
    candidate = f"custom:{base}"
    if candidate not in used:
        return base
    i = 2
    while f"custom:{base}-{i}" in used:
        i += 1
    return f"{base}-{i}"


def _row_to_dict(r: dict) -> Dict[str, Any]:
    perms = r.get("permissions")
    if isinstance(perms, str):
        try:
            perms = json.loads(perms)
        except (TypeError, ValueError):
            perms = []
    return {
        "id": str(r["id"]),
        "key": r["key"],
        "name": r.get("display_name") or r.get("name"),
        "permissions": list(perms or []),
        "permission_count": len(perms or []),
        "is_active": bool(r.get("is_active", True)),
        "version": int(r.get("version") or 0),
        "member_count": int(r.get("member_count") or 0),
        "created_at": r["created_at"].isoformat() if r.get("created_at") else None,
    }


def list_custom_roles(tenant_id: str) -> List[Dict[str, Any]]:
    """本租户自定义角色 + 在用人数(说明卡/向导基底列表)。"""
    with db.get_cursor() as cur:
        cur.execute(
            """
            SELECT r.id, r.key, r.display_name, r.name, r.permissions, r.is_active,
                   r.version, r.created_at,
                   COUNT(m.id) FILTER (WHERE m.status = 'active') AS member_count
            FROM roles r
            LEFT JOIN memberships m ON m.role_id = r.id AND m.tenant_id = r.tenant_id
            WHERE r.tenant_id = %s AND r.key LIKE 'custom:%%'
            GROUP BY r.id
            ORDER BY r.created_at ASC
            """,
            (str(tenant_id),),
        )
        return [_row_to_dict(dict(r)) for r in cur.fetchall()]


def get_custom_role(tenant_id: str, role_id: str) -> Optional[Dict[str, Any]]:
    with db.get_cursor() as cur:
        cur.execute(
            """
            SELECT r.id, r.key, r.display_name, r.name, r.permissions, r.is_active,
                   r.version, r.created_at,
                   (SELECT COUNT(*) FROM memberships m
                    WHERE m.role_id = r.id AND m.tenant_id = r.tenant_id
                      AND m.status = 'active') AS member_count
            FROM roles r
            WHERE r.tenant_id = %s AND r.id = %s AND r.key LIKE 'custom:%%'
            """,
            (str(tenant_id), str(role_id)),
        )
        row = cur.fetchone()
    return _row_to_dict(dict(row)) if row else None


def create_custom_role(
    *, tenant_id: str, actor_id: str, display_name: str, permission_codes: Any
) -> Dict[str, Any]:
    """建自定义角色。返回 {ok, role} 或 {error}(路由翻 422)。"""
    name = (display_name or "").strip()
    if not (1 <= len(name) <= _MAX_NAME):
        return {"error": "team.role_name_invalid"}
    codes = _sanitize_codes(permission_codes)
    if not codes:
        return {"error": "team.role_permissions_empty"}
    with db.get_cursor(commit=True) as cur:
        slug = _unique_slug(cur, tenant_id, _slugify(name))
        key = f"custom:{slug}"
        cur.execute(
            """
            INSERT INTO roles (name, key, display_name, permissions, is_system,
                               is_active, version, tenant_id, created_by)
            VALUES (%s, %s, %s, %s::jsonb, FALSE, TRUE, 0, %s, %s)
            RETURNING id, key, display_name, name, permissions, is_active, version, created_at
            """,
            (
                f"custom:{tenant_id}:{slug}",
                key,
                name,
                json.dumps(codes),
                str(tenant_id),
                str(actor_id),
            ),
        )
        row = dict(cur.fetchone())
    row["member_count"] = 0
    return {"ok": True, "role": _row_to_dict(row)}


def update_custom_role(
    *,
    tenant_id: str,
    role_id: str,
    display_name: Optional[str] = None,
    permission_codes: Any = None,
    is_active: Optional[bool] = None,
    expected_version: Optional[int] = None,
) -> Dict[str, Any]:
    """改自定义角色(名/码集/停用)。乐观锁:传 expected_version 且与库内不符 → conflict。"""
    current = get_custom_role(tenant_id, role_id)
    if current is None:
        return {"error": "team.role_not_found"}
    if expected_version is not None and int(expected_version) != current["version"]:
        return {"error": "team.role_version_conflict"}

    sets: List[str] = []
    params: List[Any] = []
    if display_name is not None:
        name = display_name.strip()
        if not (1 <= len(name) <= _MAX_NAME):
            return {"error": "team.role_name_invalid"}
        sets.append("display_name = %s")
        params.append(name)
    if permission_codes is not None:
        codes = _sanitize_codes(permission_codes)
        if not codes:
            return {"error": "team.role_permissions_empty"}
        sets.append("permissions = %s::jsonb")
        params.append(json.dumps(codes))
    if is_active is not None:
        sets.append("is_active = %s")
        params.append(bool(is_active))
    if not sets:
        return {"ok": True, "role": current}

    sets.append("version = version + 1")
    params += [str(tenant_id), str(role_id)]
    with db.get_cursor(commit=True) as cur:
        cur.execute(
            f"UPDATE roles SET {', '.join(sets)} "
            "WHERE tenant_id = %s AND id = %s AND key LIKE 'custom:%%'",
            tuple(params),
        )
        if cur.rowcount == 0:
            return {"error": "team.role_not_found"}
    return {"ok": True, "role": get_custom_role(tenant_id, role_id)}


def delete_custom_role(*, tenant_id: str, role_id: str) -> Dict[str, Any]:
    """删自定义角色。仍有 active 成员在用 → 拦(先转移),返回在用人数。"""
    current = get_custom_role(tenant_id, role_id)
    if current is None:
        return {"error": "team.role_not_found"}
    if current["member_count"] > 0:
        return {"error": "team.role_in_use", "member_count": current["member_count"]}
    with db.get_cursor(commit=True) as cur:
        cur.execute(
            "DELETE FROM roles WHERE tenant_id = %s AND id = %s AND key LIKE 'custom:%%'",
            (str(tenant_id), str(role_id)),
        )
        if cur.rowcount == 0:
            return {"error": "team.role_not_found"}
    return {"ok": True, "name": current["name"]}


def assign_role(
    *, tenant_id: str, actor_id: str, target_user_id: str, role_key: str
) -> Dict[str, Any]:
    """把角色(系统或自定义)分给成员。下一次请求即生效(resolver 实时读)。

    系统预设键直接委托 console_store.change_role(复用其 owner/作用域清理边界,不重复实现);
    custom:<slug> 走本地路径(须本租户且 active)。边界:不可改自己 / 不可动 owner。
    """
    if not role_key.startswith("custom:"):
        return console_store.change_role(
            tenant_id=str(tenant_id),
            actor_id=str(actor_id),
            target_user_id=str(target_user_id),
            role_key=role_key,
        )
    if str(actor_id) == str(target_user_id):
        return {"error": "team.cannot_modify_self"}
    member = console_store.get_member(tenant_id, target_user_id)
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
        return {"error": "team.role_not_assignable"}
    return {
        "ok": True,
        "role_from": member["role_key"],
        "username": member.get("username"),
    }
