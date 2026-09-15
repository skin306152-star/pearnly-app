"""Optional PDF/image evidence for an internal record; never runs recognition."""

from fastapi import HTTPException
from core import db
from services.erp import internal_records
from services.ocr import pdf_storage


def attach(user, history_id, content):
    if not content or len(content) > 20 * 1024 * 1024:
        raise HTTPException(413, detail="file.too_large")
    if not content.startswith(b"%PDF"):
        from services.line_platform.client import image_to_pdf_bytes

        content = image_to_pdf_bytes(content)
    if not content:
        raise HTTPException(422, detail="file.unsupported_type")
    with db.get_cursor_rls(str(user["tenant_id"]), user_id=str(user["id"]), commit=True) as cur:
        cur.execute(
            "SELECT workspace_client_id,pages,source,staged,pdf_storage_path FROM ocr_history "
            "WHERE id=%s::uuid AND tenant_id=%s::uuid AND user_id=%s::uuid FOR UPDATE",
            (str(history_id), str(user["tenant_id"]), str(user["id"])),
        )
        row = cur.fetchone()
        if not row or row.get("source") not in internal_records.SOURCES:
            raise HTTPException(404, detail="history.not_found")
        internal_records.authorize(
            user, row["workspace_client_id"], (row["pages"][0].get("fields") or {}).get("direction")
        )
        if not row["staged"]:
            raise HTTPException(409, detail="erp.formal_document_locked")
        if row.get("pdf_storage_path"):
            raise HTTPException(409, detail="erp.attachment_exists")
        path, size = pdf_storage.save_pdf(str(user["id"]), content)
        if not path:
            raise HTTPException(503, detail="erp.attachment_failed")
        try:
            cur.execute(
                "UPDATE ocr_history SET pdf_storage_path=%s,pdf_size_bytes=%s WHERE id=%s::uuid",
                (path, size, str(history_id)),
            )
        except Exception:
            pdf_storage.delete_pdf(path)
            raise
    return {"ok": True}
