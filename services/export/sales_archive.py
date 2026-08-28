# -*- coding: utf-8 -*-
"""已确认销售记录的 Google Drive 原票归档。"""

from __future__ import annotations

import logging

from core import db
from services.export import drive as drive_svc
from services.export import google_oauth, google_store
from services.ocr import pdf_storage
from services.ocr.pdf_utils import render_page_png_bytes

logger = logging.getLogger("mr-pilot")


def _subject_name(cur, *, tenant_id, workspace_client_id) -> str:
    cur.execute(
        "SELECT name FROM workspace_clients WHERE id = %s AND tenant_id = %s",
        (workspace_client_id, tenant_id),
    )
    row = cur.fetchone()
    return (row and row.get("name")) or f"workspace-{workspace_client_id}"


def _sales_docs(cur, *, tenant_id, workspace_client_id, history_ids) -> list[dict]:
    if not history_ids:
        return []
    cur.execute(
        """
        SELECT id, issue_date, buyer_name, ocr_history_id
        FROM sales_documents
        WHERE tenant_id = %s
          AND seller_workspace_client_id = %s
          AND status = 'issued'
          AND ocr_history_id = ANY(%s::uuid[])
        ORDER BY issue_date, id
        """,
        (tenant_id, workspace_client_id, [str(value) for value in history_ids]),
    )
    return [dict(row) for row in cur.fetchall()]


def _original_pdf(cur, *, tenant_id, history_id) -> bytes | None:
    cur.execute(
        """
        SELECT pdf_storage_path
        FROM ocr_history
        WHERE id = %s::uuid
          AND user_id IN (SELECT id FROM users WHERE tenant_id = %s::uuid)
        LIMIT 1
        """,
        (history_id, tenant_id),
    )
    row = cur.fetchone()
    if not row or not row.get("pdf_storage_path"):
        return None
    return pdf_storage.read_bytes(row["pdf_storage_path"])


def run_sales_export(params: dict, progress_cb=None) -> tuple:
    progress_cb = progress_cb or (lambda _progress: None)
    tenant_id = params.get("tenant_id")
    workspace_client_id = params.get("workspace_client_id")
    history_ids = list(dict.fromkeys(params.get("history_ids") or []))
    lang = params.get("lang") or "th"

    with db.get_cursor(commit=False) as cur:
        token = google_oauth.valid_access_token(
            cur, tenant_id=tenant_id, workspace_client_id=workspace_client_id
        )
        if not token:
            return "__failed__", {"error_code": "google_not_connected"}
        docs = _sales_docs(
            cur,
            tenant_id=tenant_id,
            workspace_client_id=workspace_client_id,
            history_ids=history_ids,
        )
        doc_ids = [str(doc["id"]) for doc in docs]
        archived = google_store.already_archived_ids(
            cur,
            tenant_id=tenant_id,
            workspace_client_id=workspace_client_id,
            doc_ids=doc_ids,
        )
        subject = _subject_name(cur, tenant_id=tenant_id, workspace_client_id=workspace_client_id)

    client = drive_svc.DriveClient(token)
    done_n = 0
    skip_n = len(archived)
    drive_url = ""
    for doc in docs:
        doc_id = str(doc["id"])
        if doc_id in archived:
            continue
        try:
            with db.get_cursor(commit=True) as cur:
                original = _original_pdf(cur, tenant_id=tenant_id, history_id=doc["ocr_history_id"])
                if not original:
                    skip_n += 1
                    progress_cb({"done_n": done_n, "skip_n": skip_n, "total": len(docs)})
                    continue
                rendered = render_page_png_bytes(original)
                png = rendered[0] if rendered else None
                result = drive_svc.archive_doc(
                    client,
                    subject=subject,
                    doc_date=doc["issue_date"],
                    supplier=doc.get("buyer_name") or "",
                    doc_id=doc_id,
                    lang=lang,
                    image_bytes=png,
                    image_name="original.png",
                    image_mime="image/png",
                    pdf_bytes=original,
                )
                google_store.mark_archived(
                    cur,
                    tenant_id=tenant_id,
                    workspace_client_id=workspace_client_id,
                    doc_id=doc_id,
                    drive_folder_id=result.get("evidence_folder_id"),
                    drive_url=result.get("evidence_url"),
                    sheet_synced=False,
                )
            done_n += 1
            drive_url = result.get("evidence_url") or drive_url
            progress_cb({"done_n": done_n, "skip_n": skip_n, "total": len(docs)})
        except Exception as exc:  # noqa: BLE001
            logger.warning("sales archive doc %s failed: %s", doc_id, exc)

    progress_cb(
        {
            "done_n": done_n,
            "skip_n": skip_n,
            "total": len(docs),
            "drive_url": drive_url,
            "sheet_url": "",
        }
    )
    return "export_archived_docs", workspace_client_id
