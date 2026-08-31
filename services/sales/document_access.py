"""Scoped reads and row locks for sales documents."""

from __future__ import annotations

from typing import Optional

from services.sales.document_cols import _DOC_COLS, _LINE_COLS
from services.sales.document_list_lines import attach as _attach_list_lines


def workspace_and(workspace_client_id: Optional[int]) -> tuple:
    if workspace_client_id is None:
        return "", ()
    return " AND (seller_workspace_client_id = %s OR seller_workspace_client_id IS NULL)", (
        int(workspace_client_id),
    )


def _creator_and(created_by: Optional[str]) -> tuple:
    if created_by is None:
        return "", ()
    return " AND created_by = %s", (str(created_by),)


def get_document(
    cur,
    *,
    tenant_id: str,
    doc_id,
    workspace_client_id: Optional[int] = None,
    created_by: Optional[str] = None,
) -> Optional[dict]:
    ws_sql, ws_params = workspace_and(workspace_client_id)
    creator_sql, creator_params = _creator_and(created_by)
    cur.execute(
        f"SELECT {_DOC_COLS} FROM sales_documents "
        f"WHERE tenant_id=%s AND id=%s{ws_sql}{creator_sql}",
        (tenant_id, doc_id, *ws_params, *creator_params),
    )
    doc = cur.fetchone()
    if not doc:
        return None
    doc = dict(doc)
    cur.execute(
        f"SELECT {_LINE_COLS} FROM sales_document_lines "
        "WHERE tenant_id=%s AND document_id=%s ORDER BY line_no",
        (tenant_id, doc_id),
    )
    doc["lines"] = cur.fetchall()
    return doc


def list_documents(
    cur,
    *,
    tenant_id: str,
    status: Optional[str] = None,
    client_id: Optional[int] = None,
    q: Optional[str] = None,
    limit: int = 100,
    workspace_client_id: Optional[int] = None,
    created_by: Optional[str] = None,
) -> list:
    ws_sql, ws_params = workspace_and(workspace_client_id)
    creator_sql, creator_params = _creator_and(created_by)
    sql = f"SELECT {_DOC_COLS} FROM sales_documents WHERE tenant_id=%s{ws_sql}{creator_sql}"
    params: list = [tenant_id, *ws_params, *creator_params]
    if status:
        sql += " AND status=%s"
        params.append(status)
    if client_id:
        sql += " AND client_id=%s"
        params.append(client_id)
    if q and q.strip():
        like = f"%{q.strip()}%"
        sql += " AND (doc_number ILIKE %s OR buyer_name ILIKE %s OR buyer_tax_id ILIKE %s)"
        params.extend([like, like, like])
    sql += " ORDER BY created_at DESC LIMIT %s"
    params.append(limit)
    cur.execute(sql, params)
    rows = [dict(row) for row in cur.fetchall()]
    if rows:
        _attach_list_lines(cur, rows, tenant_id=tenant_id)
    return rows


def status_of(
    cur,
    tenant_id: str,
    doc_id,
    lock: bool = False,
    workspace_client_id: Optional[int] = None,
    created_by: Optional[str] = None,
) -> Optional[str]:
    ws_sql, ws_params = workspace_and(workspace_client_id)
    creator_sql, creator_params = _creator_and(created_by)
    cur.execute(
        f"SELECT status FROM sales_documents WHERE tenant_id=%s AND id=%s{ws_sql}{creator_sql}"
        + (" FOR UPDATE" if lock else ""),
        (tenant_id, doc_id, *ws_params, *creator_params),
    )
    row = cur.fetchone()
    return row["status"] if row else None


def lock_for_issue(
    cur,
    tenant_id: str,
    doc_id,
    workspace_client_id: Optional[int] = None,
    created_by: Optional[str] = None,
) -> Optional[dict]:
    ws_sql, ws_params = workspace_and(workspace_client_id)
    creator_sql, creator_params = _creator_and(created_by)
    cur.execute(
        "SELECT status, doc_type, seller_workspace_client_id, grand_total, "
        "buyer_type, buyer_name, buyer_address, buyer_tax_id, buyer_branch_type, buyer_branch_no, "
        "payment_status, payment_method, payment_date "
        f"FROM sales_documents WHERE tenant_id=%s AND id=%s{ws_sql}{creator_sql} FOR UPDATE",
        (tenant_id, doc_id, *ws_params, *creator_params),
    )
    return cur.fetchone()
