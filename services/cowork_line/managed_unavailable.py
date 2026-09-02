"""Finish Cowork OCR confirmation when its workspace has no managed Express profile."""

from __future__ import annotations

from typing import Any

from services.cowork_line.push_history import staged_history
from services.erp.document_managed_target import insert_workspace_endpoint_required
from services.erp.shared_express_push import _confirmed_direction


def confirm_without_endpoint(
    cur,
    *,
    tenant_id: str,
    actor_id: str,
    workspace_client_id: int,
    history_ids: list[str],
) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for history_id in history_ids:
        history = staged_history(
            cur,
            history_id,
            tenant_id,
            actor_id,
            workspace_client_id,
        )
        _confirmed_direction(
            cur,
            history_id=history_id,
            tenant_id=tenant_id,
            workspace_client_id=workspace_client_id,
            history=history,
            entry="cowork",
        )
        item = insert_workspace_endpoint_required(
            cur,
            actor_id=actor_id,
            tenant_id=tenant_id,
            workspace_client_id=workspace_client_id,
            history_id=history_id,
            history=history,
            source="cowork_line",
        )
        cur.execute(
            "UPDATE ocr_history SET staged = FALSE,last_push_status = 'manual',"
            "last_pushed_at = clock_timestamp(),updated_at = clock_timestamp() "
            "WHERE id = %s AND tenant_id = %s AND user_id = %s "
            "AND workspace_client_id = %s AND staged = TRUE",
            (history_id, tenant_id, actor_id, workspace_client_id),
        )
        if cur.rowcount != 1:
            raise RuntimeError("managed Express unavailable confirmation rowcount mismatch")
        results.append(item)
    return results


__all__ = ["confirm_without_endpoint"]
