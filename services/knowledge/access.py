"""Workspace-client visibility, shared by every knowledge data layer.

One definition of "what an account set's caller may see", so the rule lives in a
single place instead of being copy-pasted into each DAL. None = no restriction
(owner/super-admin); a list = firm-wide rows (workspace_client_id IS NULL) plus
the account sets the caller may see; [] = firm-wide only. On migration this
collapses into the main project's RLS policy and the explicit filter falls away.
"""

from __future__ import annotations

from typing import Optional, Sequence

# None = unrestricted; a list = the workspace clients the caller may see.
AccessibleIds = Optional[Sequence[int]]


def workspace_filter(accessible_ids: AccessibleIds, *, alias: str = "") -> tuple[str, list]:
    """Build a WHERE fragment + params for workspace visibility, ANDed onto a
    tenant-scoped query. `alias` qualifies the column for joined queries (e.g.
    "e" -> e.workspace_client_id)."""
    if accessible_ids is None:
        return "", []
    column = f"{alias}.workspace_client_id" if alias else "workspace_client_id"
    return (
        f" AND ({column} IS NULL OR {column} = ANY(%s::bigint[]))",
        [list(accessible_ids)],
    )
