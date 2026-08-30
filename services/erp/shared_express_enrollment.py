# -*- coding: utf-8 -*-
"""Transactional promotion of an owner-owned legacy Express endpoint."""

from __future__ import annotations

import logging
from typing import Any, Dict

from fastapi import HTTPException

from core import db
from services.audit.store import insert_operation_log_tx
from services.authz.resolver import resolve
from services.erp.legacy_generation import lock_endpoint_binding
from services.erp.shared_express_managed_schema import enable_managed_express_owner_access
from services.erp.shared_express_enrollment_schema import enrollment_rls_ready

logger = logging.getLogger(__name__)


class EnrollmentConflict(Exception):
    """A valid request cannot promote because the target state is occupied."""


def endpoint_has_legacy_activity(cur, endpoint_id: str) -> bool:
    """Read the production activity routine through its stable public contract."""
    cur.execute(
        "SELECT public.erp_endpoint_has_legacy_activity(%s) AS busy",
        (str(endpoint_id),),
    )
    return bool(cur.fetchone()["busy"])


def _conflict(detail: str) -> HTTPException:
    return HTTPException(status_code=409, detail=detail)


def enroll_legacy_express_endpoint(
    *,
    user: Dict[str, Any],
    endpoint_id: str,
    workspace_client_id: int,
    request_ip: str | None,
    request_ua: str | None,
) -> Dict[str, Any]:
    tenant_id = str(user.get("tenant_id") or "").strip()
    actor_id = str(user.get("id") or "").strip()
    if not tenant_id or not actor_id:
        raise HTTPException(404, detail="authz.not_found")
    if not enrollment_rls_ready():
        raise HTTPException(503, detail="erp.shared_endpoint_unavailable")

    try:
        with db.get_cursor_rls(tenant_id=tenant_id, user_id=actor_id, commit=True) as cur:
            lock_endpoint_binding(cur, endpoint_id)
            cur.execute("SET LOCAL app.current_workspace_id = %s", (str(workspace_client_id),))

            authz = resolve(user, cur=cur, lock=True)
            if (
                authz.membership_id is None
                or authz.role_key != "owner"
                or not authz.has("erp.endpoint.manage")
            ):
                raise HTTPException(403, detail="authz.forbidden")

            cur.execute(
                "SELECT id FROM users WHERE id = %s AND tenant_id = %s "
                "AND is_active = TRUE FOR UPDATE",
                (actor_id, tenant_id),
            )
            if not cur.fetchone():
                raise HTTPException(404, detail="authz.not_found")

            cur.execute(
                "SELECT id, erp_endpoint_id FROM workspace_clients "
                "WHERE id = %s AND tenant_id = %s AND is_active = TRUE FOR UPDATE",
                (workspace_client_id, tenant_id),
            )
            workspace = cur.fetchone()
            if not workspace:
                raise HTTPException(404, detail="workspace.not_found")

            if not enable_managed_express_owner_access(
                cur,
                tenant_id=tenant_id,
                workspace_client_id=workspace_client_id,
                actor_user_id=actor_id,
            ):
                raise HTTPException(503, detail="erp.shared_endpoint_unavailable")

            cur.execute(
                "SELECT id, name, adapter, config, enabled, shared_scope, tenant_id, "
                "workspace_client_id, user_id, binding_generation "
                "FROM erp_endpoints WHERE id = %s FOR UPDATE",
                (endpoint_id,),
            )
            endpoint = cur.fetchone()
            if not endpoint:
                raise HTTPException(404, detail="erp.endpoint_not_found")

            adapter = str(endpoint.get("adapter") or "").strip().lower()
            generation = int(endpoint.get("binding_generation") or 0)
            owner_id = str(endpoint.get("user_id") or "")
            endpoint_tenant = endpoint.get("tenant_id")
            endpoint_workspace = endpoint.get("workspace_client_id")
            if adapter != "express" or owner_id != actor_id:
                raise HTTPException(404, detail="erp.endpoint_not_found")
            if endpoint_tenant is not None and str(endpoint_tenant) != tenant_id:
                raise HTTPException(404, detail="erp.endpoint_not_found")

            cur.execute(
                "SELECT id FROM workspace_clients "
                "WHERE erp_endpoint_id = %s AND is_active = TRUE AND id <> %s "
                "FOR UPDATE",
                (str(endpoint_id), int(workspace_client_id)),
            )
            if cur.fetchone():
                raise _conflict("erp.endpoint_workspace_conflict")

            if generation > 0:
                if (
                    str(endpoint_tenant) == tenant_id
                    and int(endpoint_workspace or 0) == int(workspace_client_id)
                    and endpoint.get("shared_scope") is True
                    and str(workspace.get("erp_endpoint_id") or "") == str(endpoint_id)
                ):
                    return _safe_response(endpoint, changed=False, workspace_id=workspace_client_id)
                raise _conflict("erp.endpoint_already_managed")
            if generation != 0:
                raise HTTPException(409, detail="erp.endpoint_generation_conflict")

            if endpoint_has_legacy_activity(cur, endpoint_id):
                raise _conflict("erp.endpoint_busy")

            existing_id = workspace.get("erp_endpoint_id")
            if existing_id and str(existing_id) != str(endpoint_id):
                raise _conflict("erp.workspace_endpoint_conflict")

            cur.execute(
                "UPDATE erp_endpoints SET binding_generation = 1, shared_scope = TRUE, "
                "tenant_id = %s, workspace_client_id = %s, updated_at = NOW() "
                "WHERE id = %s AND user_id = %s AND adapter = 'express' "
                "AND binding_generation = 0 RETURNING id, name, enabled, shared_scope, "
                "binding_generation, workspace_client_id",
                (tenant_id, workspace_client_id, endpoint_id, actor_id),
            )
            promoted = cur.fetchone()
            if not promoted:
                raise HTTPException(409, detail="erp.endpoint_generation_conflict")

            cur.execute(
                "UPDATE workspace_clients SET erp_endpoint_id = %s, updated_at = NOW() "
                "WHERE id = %s AND tenant_id = %s AND is_active = TRUE "
                "AND (erp_endpoint_id IS NULL OR erp_endpoint_id = %s)",
                (str(endpoint_id), workspace_client_id, tenant_id, str(endpoint_id)),
            )
            if cur.rowcount != 1:
                raise _conflict("erp.workspace_endpoint_conflict")

            insert_operation_log_tx(
                cur,
                tenant_id=tenant_id,
                actor_user_id=actor_id,
                actor_username=user.get("username"),
                actor_is_super=bool(user.get("is_super_admin")),
                action="erp.endpoint.enroll",
                target_type="erp_endpoint",
                target_id=str(endpoint_id),
                target_name=str(endpoint.get("name") or "")[:80],
                details={
                    "workspace_client_id": int(workspace_client_id),
                    "generation_before": 0,
                    "generation_after": 1,
                    "enabled_before": bool(endpoint.get("enabled")),
                    "enabled_after": bool(endpoint.get("enabled")),
                    "shared_scope_before": bool(endpoint.get("shared_scope")),
                    "shared_scope_after": True,
                    "profile_changed": False,
                    "reason": "owner_enroll",
                },
                ip=request_ip,
                ua=request_ua,
            )
            return _safe_response(promoted, changed=True, workspace_id=workspace_client_id)
    except HTTPException:
        raise
    except EnrollmentConflict as exc:
        raise _conflict(str(exc)) from exc
    except Exception as exc:
        if getattr(exc, "pgcode", None) == "23505":
            raise _conflict("erp.workspace_endpoint_conflict") from exc
        logger.exception("legacy Express endpoint enrollment failed")
        raise


def _safe_response(endpoint: Dict[str, Any], *, changed: bool, workspace_id: int) -> Dict[str, Any]:
    return {
        "ok": True,
        "endpoint_id": str(endpoint.get("id") or ""),
        "workspace_client_id": int(workspace_id),
        "binding_generation": int(endpoint.get("binding_generation") or 1),
        "enabled": bool(endpoint.get("enabled")),
        "shared_scope": bool(endpoint.get("shared_scope")),
        "lifecycle": "managed",
        "changed": bool(changed),
    }
