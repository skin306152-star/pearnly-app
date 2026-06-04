"""Shared request helpers for the knowledge routers.

Identity resolution and write authorization are the same preamble for documents
and rules, so they live here rather than being duplicated or cross-imported
between route modules.
"""

from __future__ import annotations

from typing import Optional

from fastapi import HTTPException, Request, status

from services.knowledge import contract
from services.knowledge import dal


def resolve_caller(request: Request) -> tuple[contract.Identity, dal.AccessibleIds]:
    """Identity + workspace visibility for one request."""
    identity = contract.get_current_identity(request)
    if not identity.tenant_id:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "missing tenant context")
    return identity, contract.get_accessible_workspace_client_ids(identity)


def authorize_write(accessible: dal.AccessibleIds, workspace_client_id: Optional[int]) -> None:
    """Reject writes to an account set the caller may not see.

    A firm-scoped write (no workspace client) is allowed for anyone in the
    tenant; a workspace-scoped write requires that client to be in the caller's
    visibility (None visibility = owner/super-admin, unrestricted).
    """
    if workspace_client_id is None:
        return
    if accessible is None or workspace_client_id in accessible:
        return
    raise HTTPException(status.HTTP_403_FORBIDDEN, "workspace client not accessible")
