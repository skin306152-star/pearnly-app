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
    card = review_cards.preview_card(
        draft_id=draft_id,
        fields={
            **fields,
            "invoice_number": fields.get("document_number") or fields.get("invoice_number"),
        },
        target=target,
        direction=direction,
        mode="stock",
        lang=lang,
        record_count=record_count,
        item_count=item_count,
        preflight=preflight,
        edit_uri=edit_uri(draft_id),
        discard_action=postback_action(flow_cards._t(lang, "discard"), "discard", draft_id),
    )
    # Keep the existing purchase/sales card and colors; remove external posting metadata.
    body = card["contents"]["body"]["contents"]
    body[0]["contents"][0]["text"] = {
        "th": "บริษัท",
        "zh": "公司",
        "en": "Company",
        "ja": "会社",
    }.get(lang, "บริษัท")
    body[0]["contents"][1]["text"] = str(target.get("label") or "-")
    del body[2]
    footer = card["contents"]["footer"]["contents"]
    footer[0]["action"]["label"] = {"th": "แก้ไข", "zh": "编辑", "en": "Edit", "ja": "編集"}.get(
        lang, "แก้ไข"
    )
    edit, discard = footer
    edit["style"] = "secondary"
    edit.pop("color", None)
    card["contents"]["footer"]["contents"] = [
        {
            "type": "button",
            "style": "primary",
            "height": "sm",
            "action": postback_action(
                {"th": "ยืนยัน", "zh": "确定", "en": "Confirm", "ja": "確定"}.get(lang, "ยืนยัน"),
                "confirm",
                draft_id,
            ),
        },
        {"type": "box", "layout": "horizontal", "spacing": "sm", "contents": [edit, discard]},
    ]
    return card


def saved_card(card: dict) -> dict:
    card["altText"] = "บันทึกแล้ว"
    card["contents"]["header"]["contents"][0]["text"] = "บันทึกแล้ว"
    del card["contents"]["body"]["contents"][-2:]
    del card["contents"]["header"]["contents"][1:]
    card["contents"].pop("footer", None)
    return card


def edit_uri(draft_id: str) -> str:
    liff_id = os.getenv("LINE_ERP_LIFF_ID", "").strip()
    return (
        f"https://liff.line.me/{liff_id}/?flow=erp-intake&draft={draft_id}"
        if liff_id
        else f"https://pearnly.com/liff/erp?flow=erp-intake&draft={draft_id}"
    )


__all__ = ["edit_uri", "preview_card"]
