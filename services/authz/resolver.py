# -*- coding: utf-8 -*-
"""user → 生效权限集(docs/permissions/03)。

真相链:memberships(user↔tenant↔role)→ roles.permissions JSONB。
存量兜底:无 membership 行时按 users.role 映射(owner→owner · member→accountant ·
docs/permissions/01 存量映射),保证批1零行为变化、回填遗漏不致拒人。
写侧(create_membership / set_membership_role)同时双写 users.role 兼容缓存
(owner→'owner' 其余→'member',老前端/JWT claim 读它)。
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from typing import Any, Optional

from services.authz.registry import ALL_CODES, ROLE_PERMISSIONS

logger = logging.getLogger("mr-pilot")


@dataclass(frozen=True)
class Authz:
    """单请求内的生效权限快照。permissions 已展开(all 短路成全集)。"""

    role_key: str
    permissions: frozenset = field(default_factory=frozenset)
    scope_mode: str = "all"
    membership_id: Optional[str] = None
    workspace_ids: Optional[frozenset] = None  # 仅 scope_mode='assigned' 时非 None

    def has(self, code: str) -> bool:
        """deny-by-default:registry 外的码永远 False。"""
        return code in ALL_CODES and code in self.permissions

    def allows_workspace(self, workspace_client_id) -> bool:
        if self.scope_mode != "assigned":
            return True
        if workspace_client_id is None or self.workspace_ids is None:
            return False
        return int(workspace_client_id) in self.workspace_ids


def perms_from_jsonb(permissions: Any) -> frozenset:
    """roles.permissions JSONB → 码集。{"all": true} 展开全集;未知码丢弃(deny)。"""
    if permissions is None:
        return frozenset()
    if isinstance(permissions, str):
        try:
            permissions = json.loads(permissions)
        except (TypeError, ValueError):
            return frozenset()
    if isinstance(permissions, dict):
        if permissions.get("all") is True:
            return ALL_CODES
        return frozenset()
    if isinstance(permissions, (list, tuple, set)):
        return frozenset(c for c in permissions if c in ALL_CODES)
    return frozenset()


def legacy_role_key(user: dict) -> str:
    """无 membership 时的存量映射(docs/permissions/01):
    users.role='owner' 或 invited_by 为空 → owner;受邀员工(member)→ accountant。
    """
    role = (user.get("role") or "").strip()
    if role == "cashier":
        return "cashier"
    if role == "owner" or user.get("invited_by") is None:
        return "owner"
    return "accountant"


def resolve(user: dict, cur=None) -> Authz:
    """取该用户在其生效租户下的权限快照。cur 可复用调用方游标(省连接)。"""
    tenant_id = user.get("tenant_id")
    if not tenant_id:
        return Authz(role_key="none")
    if cur is not None:
        return _resolve_with_cursor(cur, user, str(tenant_id))
    from core import db

    with db.get_cursor() as own_cur:
        return _resolve_with_cursor(own_cur, user, str(tenant_id))


def _resolve_with_cursor(cur, user: dict, tenant_id: str) -> Authz:
    cur.execute(
        """
        SELECT m.id, m.scope_mode, r.key AS role_key, r.permissions
        FROM memberships m JOIN roles r ON r.id = m.role_id
        WHERE m.user_id = %s AND m.tenant_id = %s AND m.status = 'active'
        LIMIT 1
        """,
        (str(user["id"]), tenant_id),
    )
    row = cur.fetchone()
    if row is None or not row.get("role_key"):
        key = legacy_role_key(user)
        return Authz(role_key=key, permissions=ROLE_PERMISSIONS.get(key, frozenset()))

    role_key = row["role_key"]
    perms = perms_from_jsonb(row["permissions"])
    scope_mode = row.get("scope_mode") or "all"
    workspace_ids: Optional[frozenset] = None
    if scope_mode == "assigned":
        cur.execute(
            "SELECT workspace_client_id FROM member_scopes "
            "WHERE tenant_id = %s AND membership_id = %s",
            (tenant_id, str(row["id"])),
        )
        workspace_ids = frozenset(int(r["workspace_client_id"]) for r in cur.fetchall())
    return Authz(
        role_key=role_key,
        permissions=perms,
        scope_mode=scope_mode,
        membership_id=str(row["id"]),
        workspace_ids=workspace_ids,
    )


# ── 写侧(双写 users.role 兼容缓存)


def _legacy_role_value(role_key: str) -> str:
    return "owner" if role_key == "owner" else "member"


def _system_role_id(cur, role_key: str) -> Optional[str]:
    cur.execute("SELECT id FROM roles WHERE key = %s AND tenant_id IS NULL", (role_key,))
    row = cur.fetchone()
    return str(row["id"]) if row else None


def create_membership(
    cur,
    *,
    user_id: str,
    tenant_id: str,
    role_key: str,
    granted_by: Optional[str] = None,
    scope_mode: str = "all",
) -> bool:
    """建号点调(注册建 owner / 邀请入组)。幂等(已有行不动)。用调用方事务。"""
    role_id = _system_role_id(cur, role_key)
    if not role_id:
        logger.warning(f"create_membership: system role {role_key!r} missing (ensure 未跑?)")
        return False
    cur.execute(
        """
        INSERT INTO memberships (user_id, tenant_id, role_id, status, scope_mode,
                                 granted_by, granted_at)
        VALUES (%s, %s, %s, 'active', %s, %s, NOW())
        ON CONFLICT (user_id) DO NOTHING
        """,
        (str(user_id), str(tenant_id), role_id, scope_mode, granted_by),
    )
    cur.execute(
        "UPDATE users SET role = %s WHERE id = %s",
        (_legacy_role_value(role_key), str(user_id)),
    )
    return True


def set_membership_role(
    cur,
    *,
    user_id: str,
    tenant_id: str,
    role_key: str,
    granted_by: Optional[str] = None,
) -> bool:
    """改角色(批3 接口/转移流用)。membership 必须已存在且属本租户。"""
    role_id = _system_role_id(cur, role_key)
    if not role_id:
        return False
    cur.execute(
        """
        UPDATE memberships SET role_id = %s, granted_by = %s, granted_at = NOW()
        WHERE user_id = %s AND tenant_id = %s
        """,
        (role_id, granted_by, str(user_id), str(tenant_id)),
    )
    if cur.rowcount == 0:
        return False
    cur.execute(
        "UPDATE users SET role = %s WHERE id = %s",
        (_legacy_role_value(role_key), str(user_id)),
    )
    return True


def count_active_owners(cur, tenant_id: str) -> int:
    """本租户 active owner 数(最后一个 owner 拦截用)。"""
    cur.execute(
        """
        SELECT COUNT(*) AS c FROM memberships m
        JOIN roles r ON r.id = m.role_id
        WHERE m.tenant_id = %s AND m.status = 'active' AND r.key = 'owner'
        """,
        (str(tenant_id),),
    )
    row = cur.fetchone()
    return int(row["c"] if isinstance(row, dict) else row[0])
