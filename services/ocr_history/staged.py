"""Mutations for user-owned staged OCR drafts."""

from __future__ import annotations

import logging
from typing import Optional

from core import db

logger = logging.getLogger("mr-pilot")


def discard_staged_ocr_history_with_pdf_paths(
    user_id: str, record_ids: list, tenant_id: Optional[str] = None
) -> tuple:
    """Delete only this user's unconverted staged drafts and return their PDF paths."""
    if not record_ids:
        return 0, []
    try:
        with db.get_cursor_rls(tenant_id=tenant_id, user_id=user_id, commit=True) as cur:
            params = (record_ids, user_id)
            guard = (
                "NOT EXISTS (SELECT 1 FROM purchase_docs p WHERE p.ocr_history_id = ocr_history.id) "
                "AND NOT EXISTS (SELECT 1 FROM sales_documents s WHERE s.ocr_history_id = ocr_history.id)"
            )
            cur.execute(
                "SELECT pdf_storage_path FROM ocr_history WHERE id = ANY(%s::uuid[]) "
                f"AND staged = TRUE AND user_id = %s::uuid AND {guard} "
                "AND pdf_storage_path IS NOT NULL",
                params,
            )
            paths = [
                row["pdf_storage_path"] for row in cur.fetchall() if row.get("pdf_storage_path")
            ]
            cur.execute(
                "DELETE FROM ocr_history WHERE id = ANY(%s::uuid[]) AND staged = TRUE "
                f"AND user_id = %s::uuid AND {guard}",
                params,
            )
            return cur.rowcount, paths
    except Exception as exc:
        logger.error("丢弃暂存历史失败: %s", exc)
        return 0, []
