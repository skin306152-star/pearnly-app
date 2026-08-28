"""Bulk-load line items for sales document list responses."""

from __future__ import annotations

from services.sales.document_cols import _LINE_COLS


def attach(cur, rows: list[dict], *, tenant_id: str) -> None:
    ids = [row["id"] for row in rows]
    cur.execute(
        f"SELECT {_LINE_COLS} FROM sales_document_lines "
        "WHERE tenant_id=%s AND document_id = ANY(%s::uuid[]) ORDER BY document_id, line_no",
        (tenant_id, ids),
    )
    by_doc: dict = {str(doc_id): [] for doc_id in ids}
    for line in cur.fetchall():
        by_doc.setdefault(str(line["document_id"]), []).append(line)
    for row in rows:
        row["lines"] = by_doc.get(str(row["id"]), [])
