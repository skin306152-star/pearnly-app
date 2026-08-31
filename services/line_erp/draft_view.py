"""Read member-owned ERP LINE draft records with preview URLs."""

from __future__ import annotations

from fastapi import HTTPException


def records(user_id: str, tenant_id: str, draft_id: str, history_ids: list[str]) -> list[dict]:
    from services.ocr_history.queries import get_ocr_history_detail

    result = []
    for history_id in history_ids:
        detail = get_ocr_history_detail(user_id, history_id, tenant_id=tenant_id)
        if detail is None:
            raise HTTPException(403, detail="line_erp.draft_forbidden")
        page_numbers = []
        for index, page in enumerate(detail.get("pages") or []):
            raw_number = page.get("page_number") if isinstance(page, dict) else None
            try:
                page_number = max(0, int(raw_number or index + 1) - 1)
            except (TypeError, ValueError):
                page_number = index
            if page_number not in page_numbers:
                page_numbers.append(page_number)
        page_numbers = page_numbers or [0]
        detail["preview_urls"] = [
            f"/api/line/erp/draft/{draft_id}/records/{history_id}/page/{page}.png"
            for page in page_numbers
        ]
        detail["preview_url"] = detail["preview_urls"][0]
        result.append(detail)
    return result


__all__ = ["records"]
