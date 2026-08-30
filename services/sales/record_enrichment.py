"""Attach upload provenance and the latest ERP push state to sales records."""

from __future__ import annotations

from services.erp.shared_express_log_access import (
    enable_managed_log_reader,
    log_reader_predicate,
)


def push_summary(statuses: list[str]) -> str:
    if not statuses:
        return "not_pushed"
    if any(status in ("failed", "manual") for status in statuses):
        return "failed"
    if any(status in ("pending", "retrying") for status in statuses):
        return "pending"
    if all(status in ("success", "skipped_dup") for status in statuses):
        return "success"
    return "not_pushed"


def enrich(cur, rows: list[dict], *, tenant_id: str, user_id: str) -> None:
    history_ids = [str(row["ocr_history_id"]) for row in rows if row.get("ocr_history_id")]
    if not history_ids:
        return
    workspaces = {
        int(row["seller_workspace_client_id"])
        for row in rows
        if row.get("seller_workspace_client_id") is not None
    }
    workspace_id = next(iter(workspaces)) if len(workspaces) == 1 else None
    shared = enable_managed_log_reader(
        cur,
        user_id=user_id,
        tenant_id=tenant_id,
        workspace_client_id=workspace_id,
    )
    reader_sql, reader_params = log_reader_predicate(
        "l",
        user_id=user_id,
        tenant_id=tenant_id,
        workspace_client_id=workspace_id,
        shared=shared,
    )
    cur.execute(
        "SELECT id, source, posting_kind FROM ocr_history "
        "WHERE tenant_id=%s::uuid AND id=ANY(%s::uuid[])",
        (tenant_id, history_ids),
    )
    history_meta = {str(row["id"]): row for row in cur.fetchall()}
    cur.execute(
        "SELECT DISTINCT ON (l.history_id, l.endpoint_id) l.history_id, l.status, "
        "COALESCE(e.name, e.adapter, 'ERP') AS endpoint_name "
        "FROM erp_push_logs l LEFT JOIN erp_endpoints e ON e.id=l.endpoint_id "
        f"WHERE {reader_sql} AND l.history_id=ANY(%s::uuid[]) "
        "ORDER BY l.history_id, l.endpoint_id, l.created_at DESC, l.id DESC",
        reader_params + (history_ids,),
    )
    pushes: dict[str, list[dict]] = {}
    for push in cur.fetchall():
        pushes.setdefault(str(push["history_id"]), []).append(push)
    for row in rows:
        history_id = str(row.get("ocr_history_id") or "")
        meta = history_meta.get(history_id) or {}
        row["source"] = meta.get("source") or "manual"
        row["posting_kind"] = meta.get("posting_kind")
        current = pushes.get(history_id, [])
        row["push_status"] = push_summary([str(item.get("status") or "") for item in current])
        row["push_endpoints"] = [
            {"name": item.get("endpoint_name") or "ERP", "status": item.get("status")}
            for item in current
        ]
