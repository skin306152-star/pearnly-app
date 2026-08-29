# -*- coding: utf-8 -*-
"""邀请链接生命周期(docs/permissions/01 invitations 表 · 批3)。

token 只存 sha256 哈希(同改密链路做法),7 天过期,单次使用。
状态派生不另存:pending / accepted / expired / revoked。
接受 = 单事务建号 + membership(角色照邀请)+ member_scopes + 标记 accepted。
现 1 人 1 租户约束(memberships UNIQUE(user_id))不动:接受只走新注册,
已有账号一律人话拒绝(invite.use_new_account)。
"""

from __future__ import annotations

import hashlib
import json
import logging
import secrets
from datetime import datetime, timezone
from html import escape
from typing import Any, Dict, List, Optional

import bcrypt

from core import db
from services.authz import roles_store
from services.authz.registry import ASSIGNABLE_ROLE_KEYS, ROLE_PERMISSIONS, SCOPABLE_ROLE_KEYS
from services.authz.resolver import Authz, create_membership, perms_from_jsonb, resolve
from services.erp.shared_express_flag import erp_shared_express_endpoint_enabled_for

logger = logging.getLogger("mr-pilot")

INVITE_TTL_DAYS = 7

_SYSTEM_ROLE_NAMES = {
    "admin": "Admin",
    "accountant": "Accountant",
    "clerk": "Clerk",
    "viewer": "Viewer",
}


class _RoleNotAssignable(RuntimeError):
    pass


class _InvitationNotConsumable(RuntimeError):
    pass


class _WorkspaceScopeNotAssignable(RuntimeError):
    pass


def role_key_allowed_for_invitation(tenant_id: str, role_key: str) -> bool:
    """Keep the legacy system-role allowlist unless F1 is enabled for this tenant."""
    if role_key in ASSIGNABLE_ROLE_KEYS:
        return True
    if not role_key.startswith("custom:"):
        return False
    return erp_shared_express_endpoint_enabled_for(str(tenant_id))


def _role_name(role_key: str, stored_name: Optional[str] = None) -> str:
    if role_key.startswith("custom:"):
        return stored_name or role_key
    return _SYSTEM_ROLE_NAMES.get(role_key, stored_name or role_key)


def _invitable_role(cur, tenant_id: str, role_key: str) -> Optional[Dict[str, Any]]:
    if role_key in ASSIGNABLE_ROLE_KEYS:
        return {
            "key": role_key,
            "role_name": _role_name(role_key),
            "permissions": ROLE_PERMISSIONS[role_key],
        }
    if not role_key_allowed_for_invitation(tenant_id, role_key):
        return None
    role = roles_store.get_active_custom_role_by_key(cur, tenant_id, role_key)
    if not role:
        return None
    return {
        "key": role["key"],
        "role_name": _role_name(role["key"], role["role_name"]),
        "permissions": perms_from_jsonb(role.get("permissions")),
    }


def _invitation_authority_error(
    actor_authz: Authz,
    *,
    target_permissions: frozenset,
    scope_mode: str,
    workspace_ids: List[int],
) -> Optional[str]:
    if not actor_authz.has("team.member.invite"):
        return "invite.role_not_allowed"
    if not actor_authz.has("team.member.edit_role") and not target_permissions.issubset(
        actor_authz.permissions
    ):
        return "invite.role_not_allowed"
    if actor_authz.scope_mode != "assigned":
        return None
    if scope_mode != "assigned":
        return "team.scope_invalid"
    actor_workspaces = actor_authz.workspace_ids or frozenset()
    if not set(workspace_ids).issubset(actor_workspaces):
        return "team.scope_invalid"
    return None


def _normalized_workspace_ids(workspace_ids: Any) -> Optional[List[int]]:
    try:
        raw_ids = json.loads(workspace_ids) if isinstance(workspace_ids, str) else workspace_ids
        return list(dict.fromkeys(int(workspace_id) for workspace_id in (raw_ids or [])))
    except (TypeError, ValueError):
        return None


def _workspace_ids_are_assignable(cur, tenant_id: str, workspace_ids: List[int]) -> bool:
    if not workspace_ids:
        return False
    cur.execute(
        "SELECT id FROM workspace_clients WHERE tenant_id = %s "
        "AND id = ANY(%s) AND is_active = TRUE FOR SHARE",
        (str(tenant_id), workspace_ids),
    )
    found = {int(row["id"]) for row in cur.fetchall()}
    return found == set(workspace_ids)


def _current_inviter_authz(cur, invitation: Dict[str, Any]) -> Optional[Authz]:
    tenant_id = str(invitation["tenant_id"])
    invited_by = str(invitation["invited_by"])
    user_sql = (
        "SELECT id::text AS id, tenant_id::text AS tenant_id, role, invited_by, is_active "
        "FROM users WHERE id = %s::uuid AND tenant_id = %s::uuid AND is_active = TRUE"
    )
    cur.execute(user_sql, (invited_by, tenant_id))
    inviter = cur.fetchone()
    if inviter is None:
        return None
    authz = resolve(dict(inviter), cur=cur, lock=True)
    if not authz.membership_id:
        return None
    cur.execute(user_sql + " FOR SHARE", (invited_by, tenant_id))
    locked_inviter = cur.fetchone()
    if locked_inviter is None:
        return None
    return authz


def hash_token(token: str) -> str:
    """一次性链接 token 的存库形态(邀请/所有权转移共用 · 同改密链路只存哈希)。"""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _status(row: Dict[str, Any]) -> str:
    if row.get("revoked_at"):
        return "revoked"
    if row.get("accepted_at"):
        return "accepted"
    expires = row.get("expires_at")
    if expires is not None and expires < datetime.now(timezone.utc):
        return "expired"
    return "pending"


def create_invitation(
    *,
    tenant_id: str,
    invited_by: str,
    channel: str,
    target: str,
    role_key: str,
    scope_mode: str = "all",
    workspace_ids: Optional[List[int]] = None,
    inviter: dict,
) -> Optional[Dict[str, Any]]:
    """建邀请并返回 {id, token, status...}。token 仅此一次返回(只存哈希)。

    校验由路由层做完(角色可邀/作用域合法);此处兜底再拦 owner。
    """
    if not role_key_allowed_for_invitation(tenant_id, role_key):
        return None
    if str(inviter.get("id")) != str(invited_by) or str(inviter.get("tenant_id")) != str(tenant_id):
        return {"error": "invite.role_not_allowed"}
    is_custom = role_key.startswith("custom:")
    if scope_mode == "assigned" and role_key not in SCOPABLE_ROLE_KEYS and not is_custom:
        return None
    token = secrets.token_urlsafe(32)
    ws_ids = _normalized_workspace_ids(workspace_ids)
    if ws_ids is None:
        return {"error": "team.scope_invalid"}
    if scope_mode != "assigned":
        ws_ids = []
    with db.get_cursor(commit=True) as cur:
        actor_authz = resolve(inviter, cur=cur, lock=True)
        role = _invitable_role(cur, str(tenant_id), role_key)
        if role is None:
            return None
        authority_error = _invitation_authority_error(
            actor_authz,
            target_permissions=frozenset(role["permissions"]),
            scope_mode=scope_mode,
            workspace_ids=ws_ids,
        )
        if authority_error:
            return {"error": authority_error}
        if scope_mode == "assigned" and not _workspace_ids_are_assignable(
            cur, str(tenant_id), ws_ids
        ):
            return {"error": "team.scope_invalid"}
        cur.execute(
            """
            INSERT INTO invitations (tenant_id, email, line_target, role_key, scope_mode,
                                     workspace_ids, token_hash, invited_by, expires_at)
            VALUES (%s, %s, %s, %s, %s, %s::jsonb, %s, %s, NOW() + %s * INTERVAL '1 day')
            RETURNING id, created_at, expires_at
            """,
            (
                str(tenant_id),
                target if channel == "email" else None,
                target if channel == "line" else None,
                role_key,
                scope_mode,
                json.dumps(ws_ids),
                hash_token(token),
                str(invited_by),
                INVITE_TTL_DAYS,
            ),
        )
        row = cur.fetchone()
    return {
        "id": str(row["id"]),
        "token": token,
        "channel": channel,
        "target": target,
        "role_key": role_key,
        "role_name": role["role_name"],
        "scope_mode": scope_mode,
        "workspace_ids": ws_ids,
        "expires_at": row["expires_at"].isoformat(),
        "created_at": row["created_at"].isoformat(),
    }


def list_pending(tenant_id: str) -> List[Dict[str, Any]]:
    with db.get_cursor() as cur:
        cur.execute(
            """
            SELECT i.*, u.username AS inviter_username,
                   r.display_name AS role_display_name, r.name AS role_db_name
            FROM invitations i
            LEFT JOIN users u ON u.id = i.invited_by
            LEFT JOIN roles r ON r.key = i.role_key
              AND ((i.role_key LIKE 'custom:%%' AND r.tenant_id = i.tenant_id)
                   OR (i.role_key NOT LIKE 'custom:%%' AND r.tenant_id IS NULL))
            WHERE i.tenant_id = %s AND i.accepted_at IS NULL AND i.revoked_at IS NULL
              AND i.expires_at > NOW()
            ORDER BY i.created_at DESC
            """,
            (str(tenant_id),),
        )
        rows = [dict(r) for r in cur.fetchall()]
    return [
        {
            "id": str(r["id"]),
            "channel": "email" if r.get("email") else "line",
            "target": r.get("email") or r.get("line_target"),
            "role_key": r["role_key"],
            "role_name": _role_name(
                r["role_key"], r.get("role_display_name") or r.get("role_db_name")
            ),
            "scope_mode": r["scope_mode"],
            "invited_by": r.get("inviter_username"),
            "expires_at": r["expires_at"].isoformat(),
            "created_at": r["created_at"].isoformat(),
        }
        for r in rows
    ]


def revoke(tenant_id: str, invitation_id: str) -> bool:
    with db.get_cursor(commit=True) as cur:
        cur.execute(
            """
            UPDATE invitations SET revoked_at = NOW()
            WHERE id = %s AND tenant_id = %s AND accepted_at IS NULL AND revoked_at IS NULL
            """,
            (str(invitation_id), str(tenant_id)),
        )
        return cur.rowcount > 0


def _find_by_token_with_cursor(cur, token: str, *, lock: bool = False) -> Optional[Dict[str, Any]]:
    sql = """
        SELECT i.*, t.name AS tenant_name,
               r.display_name AS role_display_name, r.name AS role_db_name
        FROM invitations i
        LEFT JOIN tenants t ON t.id = i.tenant_id
        LEFT JOIN roles r ON r.key = i.role_key
          AND ((i.role_key LIKE 'custom:%%' AND r.tenant_id = i.tenant_id)
               OR (i.role_key NOT LIKE 'custom:%%' AND r.tenant_id IS NULL))
        WHERE i.token_hash = %s
    """
    if lock:
        sql += " FOR UPDATE OF i"
    cur.execute(sql, (hash_token(token),))
    row = cur.fetchone()
    if row is None:
        return None
    out = dict(row)
    out["status"] = _status(out)
    out["role_name"] = _role_name(
        out["role_key"], out.get("role_display_name") or out.get("role_db_name")
    )
    return out


def find_by_token(token: str) -> Optional[Dict[str, Any]]:
    """token → 邀请行 + 派生 status + 租户名(接受页渲染)。无效 token → None。"""
    with db.get_cursor() as cur:
        return _find_by_token_with_cursor(cur, token)


def accept(
    token: str, *, username: str, password: str, email: Optional[str] = None
) -> Dict[str, Any]:
    """接受邀请:单事务 新号 + membership(角色照邀请)+ scopes + 标 accepted。

    返回 {ok} 或 {error}:invite.invalid / invite.expired / invite.revoked /
    invite.used / invite.role_not_allowed / team.username_exists / team.email_exists。
    """
    try:
        with db.get_cursor(commit=True) as cur:
            candidate = _find_by_token_with_cursor(cur, token)
            if candidate is None:
                return {"error": "invite.invalid"}
            candidate_tenant_id = str(candidate["tenant_id"])
            candidate_role_key = str(candidate["role_key"])
            target_role = _invitable_role(cur, candidate_tenant_id, candidate_role_key)
            if target_role is None:
                raise _RoleNotAssignable
            inv = _find_by_token_with_cursor(cur, token, lock=True)
            if inv is None:
                return {"error": "invite.invalid"}
            if (
                str(inv["tenant_id"]) != candidate_tenant_id
                or str(inv["role_key"]) != candidate_role_key
            ):
                raise _RoleNotAssignable
            if inv["status"] == "expired":
                return {"error": "invite.expired"}
            if inv["status"] == "revoked":
                return {"error": "invite.revoked"}
            if inv["status"] == "accepted":
                return {"error": "invite.used"}

            tenant_id = str(inv["tenant_id"])
            role_key = str(inv["role_key"])
            if not role_key_allowed_for_invitation(tenant_id, role_key):
                raise _RoleNotAssignable
            allow_custom = role_key.startswith("custom:")
            ws_ids = _normalized_workspace_ids(inv.get("workspace_ids"))
            if ws_ids is None:
                raise _WorkspaceScopeNotAssignable
            if inv["scope_mode"] == "assigned":
                if not _workspace_ids_are_assignable(cur, tenant_id, ws_ids):
                    raise _WorkspaceScopeNotAssignable
            else:
                ws_ids = []
            inviter_authz = _current_inviter_authz(cur, inv)
            if inviter_authz is None:
                raise _RoleNotAssignable
            authority_error = _invitation_authority_error(
                inviter_authz,
                target_permissions=frozenset(target_role["permissions"]),
                scope_mode=str(inv["scope_mode"]),
                workspace_ids=ws_ids,
            )
            if authority_error:
                raise _RoleNotAssignable
            use_email = (email or inv.get("email") or "").strip().lower() or None
            pw_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
            cur.execute("SELECT 1 FROM users WHERE username = %s LIMIT 1", (username,))
            if cur.fetchone():
                return {"error": "team.username_exists"}
            if use_email:
                cur.execute(
                    "SELECT tenant_id FROM users WHERE LOWER(email) = LOWER(%s) LIMIT 1",
                    (use_email,),
                )
                row = cur.fetchone()
                if row:
                    # 1 人 1 租户:邮箱已有账号且已归属公司 → 明确码(接受页人话文案)
                    if row.get("tenant_id"):
                        return {"error": "invite.account_exists_other_tenant"}
                    return {"error": "team.email_exists"}
            cur.execute("SELECT name FROM tenants WHERE id = %s", (tenant_id,))
            trow = cur.fetchone()
            company_name = trow["name"] if trow else None
            cur.execute(
                """
                INSERT INTO users (username, password_hash, email, plan, is_active,
                                   is_super_admin, tenant_id, role, invited_by, company_name)
                VALUES (%s, %s, %s, 'credits', TRUE, FALSE, %s, 'member', %s, %s)
                RETURNING id
                """,
                (username, pw_hash, use_email, tenant_id, str(inv["invited_by"]), company_name),
            )
            new_id = str(cur.fetchone()["id"])
            if not create_membership(
                cur,
                user_id=new_id,
                tenant_id=tenant_id,
                role_key=role_key,
                granted_by=str(inv["invited_by"]),
                scope_mode=inv["scope_mode"],
                allow_custom=allow_custom,
                allow_owner=False,
            ):
                raise _RoleNotAssignable
            if inv["scope_mode"] == "assigned":
                cur.execute(
                    "SELECT id FROM memberships WHERE user_id = %s AND tenant_id = %s",
                    (new_id, tenant_id),
                )
                mrow = cur.fetchone()
                if mrow is None:
                    raise _RoleNotAssignable
                for ws in ws_ids:
                    cur.execute(
                        """
                        INSERT INTO member_scopes (tenant_id, membership_id, workspace_client_id,
                                                   assigned_by)
                        VALUES (%s, %s, %s, %s)
                        ON CONFLICT (membership_id, workspace_client_id) DO NOTHING
                        """,
                        (tenant_id, str(mrow["id"]), int(ws), str(inv["invited_by"])),
                    )
            cur.execute(
                "UPDATE invitations SET accepted_at = NOW(), accepted_user_id = %s "
                "WHERE id = %s AND accepted_at IS NULL AND revoked_at IS NULL "
                "AND expires_at > NOW()",
                (new_id, str(inv["id"])),
            )
            if cur.rowcount != 1:
                raise _InvitationNotConsumable
    except _RoleNotAssignable:
        return {"error": "invite.role_not_allowed"}
    except _InvitationNotConsumable:
        return {"error": "invite.expired"}
    except _WorkspaceScopeNotAssignable:
        return {"error": "team.scope_invalid"}
    return {
        "ok": True,
        "user_id": new_id,
        "tenant_id": tenant_id,
        "role_key": role_key,
        "role_name": inv.get("role_name") or _role_name(role_key),
    }


def send_invite_email(target_email: str, invite_url: str, tenant_name: str, role_name: str) -> bool:
    """邮件通道:复用系统 SMTP 主通道(同改密邮件)。失败仅记日志(链接仍可复制发送)。"""
    subject = "Pearnly · Team Invitation / 团队邀请"
    safe_tenant_name = escape(str(tenant_name), quote=True)
    safe_role_name = escape(str(role_name), quote=True)
    safe_invite_url = escape(str(invite_url), quote=True)
    html = f"""
        <div style="font-family:Inter,Sarabun,sans-serif;max-width:560px;margin:0 auto;padding:32px;background:#f8fafc;">
            <div style="background:#fff;border-radius:12px;padding:32px;box-shadow:0 4px 24px rgba(0,0,0,0.05);">
                <div style="margin-bottom:24px;"><img src="https://pearnly.com/static/brand/pwa-icon-192.png?v=1" width="32" height="32" alt="Pearnly" style="vertical-align:middle;border-radius:7px;display:inline-block;" /><span style="display:inline-block;vertical-align:middle;margin-left:8px;font-weight:800;font-size:18px;color:#4c1d95;">Pearnly</span></div>
                <h1 style="font-size:22px;color:#0f172a;margin:0 0 12px 0;">{safe_tenant_name} invites you</h1>
                <p style="font-size:14px;color:#64748b;line-height:1.6;">{safe_tenant_name} 邀请你以「{safe_role_name}」身份加入 Pearnly(7 天内有效)。</p>
                <div style="text-align:center;margin:28px 0;">
                    <a href="{safe_invite_url}" style="display:inline-block;padding:12px 32px;background:#7c4dff;color:#fff;border-radius:10px;text-decoration:none;font-weight:600;font-size:14px;">Accept Invitation / 接受邀请</a>
                </div>
                <p style="font-size:12px;color:#94a3b8;line-height:1.6;">If the button doesn't work, copy this link:<br><span style="word-break:break-all;color:#475569;">{safe_invite_url}</span></p>
            </div>
        </div>
        """
    try:
        from routes.auth_email_code_routes import _smtp_send_email

        ok, err = _smtp_send_email(target_email, subject, html)
        if not ok:
            logger.warning(f"invite email send fail: {err}")
        return bool(ok)
    except Exception as e:
        logger.warning(f"invite email send error: {e}")
        return False
