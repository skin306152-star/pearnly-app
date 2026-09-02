"""Identity and authorization guards for Cowork ERP reservations."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from fastapi import HTTPException

from services.authz.resolver import resolve


def require_uuid(value: object, code: str) -> str:
    try:
        return str(UUID(str(value)))
    except (TypeError, ValueError, AttributeError) as exc:
        raise HTTPException(404, detail=code) from exc


def require_identity(identity: dict[str, Any]) -> tuple[str, str]:
    tenant_id = str(identity.get("tenant_id") or "").strip()
    actor_id = str(identity.get("user_id") or "").strip()
    if not tenant_id or not actor_id:
        raise HTTPException(404, detail="authz.not_found")
    return tenant_id, actor_id


def require_active_actor(cur, identity: dict[str, Any], workspace_id: int):
    membership_id = str(identity.get("membership_id") or "").strip()
    tenant_id = str(identity.get("tenant_id") or "").strip()
    actor_id = str(identity.get("user_id") or "").strip()
    line_user_id = str(identity.get("line_user_id") or "").strip()
    if not membership_id or not tenant_id or not actor_id or not line_user_id:
        raise HTTPException(403, detail="authz.forbidden")
    cur.execute(
        "SELECT u.role,u.invited_by FROM cowork_line_identities identity "
        "JOIN memberships membership ON membership.id = identity.membership_id "
        "AND membership.user_id = identity.user_id "
        "AND membership.tenant_id = identity.tenant_id "
        "JOIN users u ON u.id = identity.user_id AND u.tenant_id = identity.tenant_id "
        "WHERE identity.membership_id = %s AND identity.tenant_id = %s "
        "AND identity.user_id = %s AND identity.line_user_id = %s "
        "AND identity.revoked_at IS NULL AND membership.status = 'active' "
        "AND u.is_active = TRUE FOR SHARE OF identity,membership,u",
        (membership_id, tenant_id, actor_id, line_user_id),
    )
    actor = cur.fetchone()
    if not actor:
        raise HTTPException(403, detail="authz.forbidden")
    authz = resolve(
        {
            "id": actor_id,
            "tenant_id": tenant_id,
            "role": actor.get("role"),
            "invited_by": actor.get("invited_by"),
            "entry": "cowork",
        },
        cur=cur,
        lock=True,
    )
    if (
        str(authz.membership_id or "") != membership_id
        or not authz.has("erp.endpoint.view")
        or not authz.has("erp.push.operate")
        or not authz.allows_workspace(workspace_id)
    ):
        raise HTTPException(403, detail="authz.forbidden")
    return authz


__all__ = ["require_active_actor", "require_identity", "require_uuid"]
