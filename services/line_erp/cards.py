from __future__ import annotations

import os

from services.cowork_line import flow_cards, review_cards
from services.line_platform.summary_review_card import postback_action


def preview_card(
    draft_id: str,
    direction: str,
    fields: dict,
    *,
    target: dict,
    posting_mode: str,
    record_count: int = 1,
    item_count: int | None = None,
    preflight: dict | None = None,
    lang: str = "th",
) -> dict:
    return review_cards.preview_card(
        draft_id=draft_id,
        fields=fields,
        target=target,
        direction=direction,
        mode=posting_mode,
        lang=lang,
        record_count=record_count,
        item_count=item_count,
        preflight=preflight,
        edit_uri=edit_uri(draft_id),
        discard_action=postback_action(flow_cards._t(lang, "discard"), "discard", draft_id),
    )


def edit_uri(draft_id: str) -> str:
    liff_id = os.getenv("LINE_ERP_LIFF_ID", "").strip()
    return (
        f"https://liff.line.me/{liff_id}/?flow=erp-intake&draft={draft_id}"
        if liff_id
        else f"https://pearnly.com/liff/erp?flow=erp-intake&draft={draft_id}"
    )


__all__ = ["edit_uri", "preview_card"]
