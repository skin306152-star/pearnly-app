"""ERP LINE OCR留底；留底失败不影响识别草稿或计费结果。"""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


def generate_and_save_pdf(
    content: bytes,
    pages: list,
    history_ids: list[str],
    user_id: str,
    tenant_id: str | None = None,
) -> dict:
    """生成一份留底 PDF 并回填本批所有 history；不重复执行 OCR 或计费。"""
    ids = [str(value) for value in history_ids if value]
    if not content or not ids:
        return {"saved": False, "updated": 0}
    try:
        if not content.startswith(b"%PDF"):
            from services.line_platform.client import image_to_pdf_bytes

            content = image_to_pdf_bytes(content) or b""
        if not content:
            return {"saved": False, "updated": 0}
        from services.ocr.pdf_backfill import generate_and_save_pdf as save_pdf
        from services.ocr_history.mutations import update_ocr_history_pdf_storage

        rel_path, size = save_pdf(content, pages or [], str(user_id))
        if not rel_path:
            return {"saved": False, "updated": 0}
        updated = update_ocr_history_pdf_storage(
            ids, rel_path, size, str(user_id), tenant_id=tenant_id
        )
        if updated != len(ids):
            logger.warning(
                "ERP LINE PDF history 回填不完整: updated=%s expected=%s", updated, len(ids)
            )
        return {"saved": True, "updated": updated, "path": rel_path}
    except Exception as exc:
        logger.warning("ERP LINE PDF 留底/回填失败(保留草稿): %s", exc)
        return {"saved": False, "updated": 0}
