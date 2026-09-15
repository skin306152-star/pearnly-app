from __future__ import annotations

import os

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
    return {
        "type": "text",
        "text": f"{target.get('label', '')} · {'ซื้อ' if direction == 'purchase' else 'ขาย'}\n{record_count} เอกสาร · กรุณาตรวจสอบก่อนบันทึกใน Pearnly ครับ",
        "quickReply": {
            "items": [
                {
                    "type": "action",
                    "action": {
                        "type": "uri",
                        "label": "ตรวจสอบ / แก้ไข",
                        "uri": edit_uri(draft_id),
                    },
                },
                {"type": "action", "action": postback_action("ทิ้งรายการ", "discard", draft_id)},
            ]
        },
    }


def edit_uri(draft_id: str) -> str:
    liff_id = os.getenv("LINE_ERP_LIFF_ID", "").strip()
    return (
        f"https://liff.line.me/{liff_id}/?flow=erp-intake&draft={draft_id}"
        if liff_id
        else f"https://pearnly.com/liff/erp?flow=erp-intake&draft={draft_id}"
    )


__all__ = ["edit_uri", "preview_card"]
