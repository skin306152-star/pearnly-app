"""Locked Cowork OCR history reads used by ERP push reservation."""

from fastapi import HTTPException

from services.ocr_history.queries import _DETAIL_COLUMNS, _detail_row


def staged_history(cur, history_id: str, tenant_id: str, actor_id: str, workspace_id: int):
    cur.execute(
        f"SELECT {_DETAIL_COLUMNS} FROM ocr_history "
        "WHERE id = %s AND tenant_id = %s AND user_id = %s "
        "AND workspace_client_id = %s AND staged = TRUE FOR UPDATE",
        (history_id, tenant_id, actor_id, workspace_id),
    )
    row = cur.fetchone()
    if not row:
        raise HTTPException(409, detail="cowork_line_intake.draft_changed")
    return _detail_row(row)
