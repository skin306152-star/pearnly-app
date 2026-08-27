from __future__ import annotations

import os
from urllib.parse import urlencode


def _button(label: str, action: str, draft_id: str) -> dict:
    return {
        "type": "button",
        "style": "primary",
        "action": {
            "type": "postback",
            "label": label[:20],
            "data": urlencode({"a": action, "draft": draft_id}),
        },
    }


def menu_card() -> dict:
    return {
        "type": "flex",
        "altText": "เลือกประเภทเอกสาร",
        "contents": {
            "type": "bubble",
            "body": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {"type": "text", "text": "เลือกประเภทเอกสาร", "weight": "bold", "size": "lg"},
                    _button("1 ซื้อ", "mode:purchase", ""),
                    _button("2 ขาย", "mode:sales", ""),
                ],
            },
        },
    }


def preview_card(
    draft_id: str, mode: str, amount: str = "", vendor: str = "", detail: str = ""
) -> dict:
    title = "ตัวอย่างเอกสารซื้อ" if mode == "purchase" else "ตัวอย่างเอกสารขาย"
    liff_id = os.getenv("LINE_ERP_LIFF_ID", "").strip()
    edit_uri = (
        f"https://liff.line.me/{liff_id}?draft={draft_id}"
        if liff_id
        else f"https://pearnly.com/liff/erp/{draft_id}"
    )
    body = [
        {"type": "text", "text": title, "weight": "bold", "size": "lg"},
        {"type": "text", "text": f"ยอดรวม ฿{amount or '-'}", "wrap": True},
        {"type": "text", "text": f"ผู้ขาย/ลูกค้า: {vendor or '-'}", "wrap": True},
        {"type": "text", "text": f"รายการ: {detail or '-'}", "wrap": True},
        {
            "type": "text",
            "text": "กรุณาตรวจสอบข้อมูลทั้งหมดก่อนยืนยันหรือทิ้ง",
            "wrap": True,
            "size": "sm",
        },
        _button("ยืนยัน", "confirm", draft_id),
        {
            "type": "button",
            "style": "secondary",
            "action": {"type": "uri", "label": "แก้ไข", "uri": edit_uri},
        },
        _button("ทิ้ง", "discard", draft_id),
    ]
    return {
        "type": "flex",
        "altText": title,
        "contents": {
            "type": "bubble",
            "body": {"type": "box", "layout": "vertical", "contents": body},
        },
    }


def edit_uri(draft_id: str) -> str:
    liff_id = os.getenv("LINE_ERP_LIFF_ID", "").strip()
    return (
        f"https://liff.line.me/{liff_id}?draft={draft_id}"
        if liff_id
        else f"https://pearnly.com/liff/erp/{draft_id}"
    )
