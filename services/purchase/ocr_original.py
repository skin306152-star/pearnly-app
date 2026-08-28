"""Expose the OCR original through purchase records without duplicating stored files."""

from __future__ import annotations

from typing import Optional


def _source(ocr_source: str) -> str:
    if ocr_source == "line_erp":
        return "line"
    if ocr_source == "erp_web":
        return "upload"
    return "manual"


def _load(cur, *, tenant_id, history_ids: list) -> dict:
    ids = [str(value) for value in history_ids if value]
    if not ids:
        return {}
    cur.execute(
        "SELECT id::text AS id, source, pdf_storage_path FROM ocr_history "
        "WHERE tenant_id = %s::uuid AND id = ANY(%s::uuid[])",
        (tenant_id, ids),
    )
    return {str(row["id"]): row for row in (cur.fetchall() or [])}


def apply_meta(doc: dict, meta: Optional[dict]) -> None:
    if not meta:
        return
    if (doc.get("source") or "manual") == "manual":
        doc["source"] = _source(str(meta.get("source") or ""))
    if meta.get("pdf_storage_path"):
        doc["ocr_original_available"] = True


def enrich_detail(cur, *, tenant_id, doc: dict, attachments: list) -> None:
    history_id = doc.get("ocr_history_id")
    meta = _load(cur, tenant_id=tenant_id, history_ids=[history_id]).get(str(history_id))
    apply_meta(doc, meta)
    if (
        meta
        and meta.get("pdf_storage_path")
        and not any(item.get("kind") == "bill" for item in attachments)
    ):
        attachments.insert(
            0,
            {
                "id": f"ocr:{history_id}",
                "kind": "bill",
                "url": None,
                "generated": False,
                "created_at": doc.get("created_at"),
            },
        )
    bill_idx = 0
    for attachment in attachments:
        if attachment.get("kind") != "bill":
            continue
        if str(attachment.get("id") or "").startswith("ocr:"):
            attachment["url"] = f"/api/history/{history_id}/page/1.png"
            continue
        attachment["url"] = f"/api/purchase/docs/{doc['id']}/bill-image?idx={bill_idx}"
        bill_idx += 1


def enrich_list(cur, *, tenant_id, docs: list) -> None:
    meta = _load(
        cur,
        tenant_id=tenant_id,
        history_ids=[doc.get("ocr_history_id") for doc in docs],
    )
    for doc in docs:
        history_meta = meta.get(str(doc.get("ocr_history_id") or ""))
        apply_meta(doc, history_meta)
        if (
            history_meta
            and history_meta.get("pdf_storage_path")
            and not doc.get("attachment_count")
        ):
            doc["attachment_count"] = 1


def fallback_ref(cur, *, tenant_id, workspace_client_id, doc_id, idx=0) -> Optional[str]:
    if idx:
        return None
    cur.execute(
        "SELECT h.pdf_storage_path AS url FROM purchase_docs d "
        "JOIN ocr_history h ON h.id = d.ocr_history_id AND h.tenant_id = d.tenant_id "
        "WHERE d.tenant_id = %s AND d.workspace_client_id = %s AND d.id = %s "
        "AND h.pdf_storage_path IS NOT NULL LIMIT 1",
        (tenant_id, workspace_client_id, doc_id),
    )
    row = cur.fetchone()
    return row["url"] if row else None
