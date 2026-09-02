# -*- coding: utf-8 -*-
"""Authorization and response shaping for the F1 shared endpoint read."""

from __future__ import annotations

from typing import Any, Dict, List

from fastapi import Request

from services.auth.entrance import COWORK, ERP, MAIN
from services.authz.deps import require_perm
from services.erp.endpoint_config import strip_endpoint_for_response
from services.erp import shared_express_store
from services.erp.shared_express_flag import erp_shared_express_endpoint_enabled_for

_SHARED_READ_ENTRIES = frozenset({MAIN, COWORK, ERP})


def is_shared_endpoint_read(user: dict) -> bool:
    """Select B3A only for an exact supported entry and enabled tenant flag."""
    if user.get("entry") not in _SHARED_READ_ENTRIES:
        return False
    return erp_shared_express_endpoint_enabled_for(user.get("tenant_id"))


def list_shared_endpoint_items(request: Request, user: dict) -> List[Dict[str, Any]]:
    """Enforce view permission, deduplicate rows and choose manager or safe projection."""
    require_perm(request, "erp.endpoint.view")
    rows, server_now, may_manage = shared_express_store.list_visible_endpoints(request, user)
    actor_id = str(user.get("id") or "")
    items: List[Dict[str, Any]] = []
    seen = set()
    for row in rows:
        endpoint_id = str(row.get("id") or "")
        if not endpoint_id or endpoint_id in seen:
            continue
        seen.add(endpoint_id)
        shared_express = (
            str(row.get("adapter") or "").strip().lower() == "express"
            and row.get("enabled") is True
            and row.get("shared_scope") is True
        )
        if may_manage and (str(row.get("user_id") or "") == actor_id or shared_express):
            manager_item = dict(row)
            manager_item.pop("tenant_id", None)
            manager_item.pop("workspace_client_id", None)
            items.append(strip_endpoint_for_response(manager_item))
        else:
            items.append(shared_express_store.safe_endpoint_dto(row, server_now))
    return items


def visible_endpoint_for_request(
    request: Request, user: dict, endpoint_id: str
) -> Dict[str, Any] | None:
    """Resolve one exact endpoint without expanding the full workspace endpoint list."""
    require_perm(request, "erp.endpoint.view")
    rows, server_now, _ = shared_express_store.list_visible_endpoints(
        request,
        user,
        endpoint_id=endpoint_id,
    )
    if not rows:
        return None
    return shared_express_store.safe_endpoint_dto(rows[0], server_now)


__all__ = [
    "is_shared_endpoint_read",
    "list_shared_endpoint_items",
    "visible_endpoint_for_request",
]
