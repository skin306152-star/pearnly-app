from __future__ import annotations

import os
from urllib.parse import urlencode


def _button(label: str, action: str, draft_id: str, style: str = "primary") -> dict:
    return {
        "type": "button",
        "style": style,
        "height": "sm",
        "action": {
            "type": "postback",
            "label": label[:20],
            "data": urlencode({"a": action, "draft": draft_id}),
            "displayText": label,
        },
    }


def _menu_item(num: str, title: str, description: str, action: str, accent: str) -> dict:
    return {
        "type": "box",
        "layout": "horizontal",
        "margin": "md",
        "paddingAll": "14px",
        "cornerRadius": "14px",
        "borderWidth": "1px",
        "borderColor": accent,
        "alignItems": "center",
        "action": {
            "type": "postback",
            "data": urlencode({"a": action}),
            "displayText": title,
        },
        "contents": [
            {
                "type": "text",
                "text": num,
                "size": "xxl",
                "weight": "bold",
                "color": accent,
                "flex": 0,
            },
            {
                "type": "box",
                "layout": "vertical",
                "flex": 1,
                "margin": "md",
                "contents": [
                    {"type": "text", "text": title, "size": "sm", "weight": "bold", "wrap": True},
                    {
                        "type": "text",
                        "text": description,
                        "size": "xxs",
                        "color": "#8a8a8a",
                        "wrap": True,
                        "margin": "xs",
                    },
                ],
            },
            {"type": "text", "text": "›", "size": "xl", "color": accent, "flex": 0},
        ],
    }


def menu_card() -> dict:
    """ERP 专用入口:先锁定采购/销售，再接收票据，不让识别模型猜方向。"""
    return {
        "type": "flex",
        "altText": "เลือกประเภทเอกสาร ERP",
        "contents": {
            "type": "bubble",
            "body": {
                "type": "box",
                "layout": "vertical",
                "paddingAll": "16px",
                "contents": [
                    {
                        "type": "text",
                        "text": "เลือกประเภทเอกสาร ERP",
                        "weight": "bold",
                        "size": "lg",
                    },
                    {
                        "type": "text",
                        "text": "เลือกรายการก่อนส่งรูปภาพหรือ PDF",
                        "size": "xxs",
                        "color": "#8a8a8a",
                        "wrap": True,
                        "margin": "xs",
                    },
                    {"type": "separator", "margin": "lg", "color": "#eeeef4"},
                    _menu_item(
                        "1",
                        "ซื้อ",
                        "บันทึกเอกสารซื้อและเพิ่มสินค้าเข้าสต๊อก",
                        "mode:purchase",
                        "#2f6bff",
                    ),
                    _menu_item(
                        "2",
                        "ขาย",
                        "บันทึกเอกสารขายและตัดสินค้าออกจากสต๊อก",
                        "mode:sales",
                        "#f25c6e",
                    ),
                    {
                        "type": "text",
                        "text": "พิมพ์ เมนู เพื่อเลือกใหม่ได้ตลอดเวลา",
                        "size": "xxs",
                        "color": "#aaaaaa",
                        "align": "center",
                        "wrap": True,
                        "margin": "lg",
                    },
                ],
            },
        },
    }


def preview_card(
    draft_id: str,
    mode: str,
    amount: str = "",
    vendor: str = "",
    detail: str = "",
    document_no: str = "",
    document_date: str = "",
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
        {"type": "text", "text": f"เลขที่: {document_no or '-'}", "wrap": True},
        {"type": "text", "text": f"วันที่: {document_date or '-'}", "wrap": True},
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
        _button("ทิ้ง", "discard", draft_id, "secondary"),
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
