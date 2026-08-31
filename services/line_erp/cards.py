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


def menu_card(modes=("purchase", "sales")) -> dict:
    """ERP 专用入口:先锁定采购/销售，再接收票据，不让识别模型猜方向。"""
    allowed = set(modes or ())
    items = []
    if "purchase" in allowed:
        items.append(
            _menu_item(
                "1",
                "ซื้อ",
                "บันทึกเอกสารซื้อและเพิ่มสินค้าเข้าสต๊อก",
                "mode:purchase",
                "#2f6bff",
            )
        )
    if "sales" in allowed:
        items.append(
            _menu_item(
                "2",
                "ขาย",
                "บันทึกเอกสารขายและตัดสินค้าออกจากสต๊อก",
                "mode:sales",
                "#f25c6e",
            )
        )
    if not items:
        items.append(
            {
                "type": "text",
                "text": "บัญชีนี้ยังไม่มีสิทธิ์อัปโหลดเอกสาร กรุณาติดต่อผู้ดูแล",
                "size": "sm",
                "color": "#8a8a8a",
                "wrap": True,
                "margin": "lg",
            }
        )
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
                    *items,
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


def _kv(label: str, value: str) -> dict:
    return {
        "type": "box",
        "layout": "horizontal",
        "margin": "sm",
        "contents": [
            {"type": "text", "text": label, "size": "xs", "color": "#777777", "flex": 2},
            {
                "type": "text",
                "text": value or "-",
                "size": "xs",
                "weight": "bold",
                "align": "end",
                "wrap": True,
                "flex": 4,
            },
        ],
    }


def _item_row(item: dict) -> dict:
    kind = {
        "stock": "สินค้า",
        "service": "บริการ",
    }.get(item.get("kind"), "ยังไม่เลือกประเภท")
    meta = f"{item.get('qty') or '-'} × ฿{item.get('price') or '-'} · {kind}"
    return {
        "type": "box",
        "layout": "horizontal",
        "margin": "md",
        "contents": [
            {
                "type": "box",
                "layout": "vertical",
                "flex": 4,
                "contents": [
                    {"type": "text", "text": item.get("name") or "-", "size": "sm", "wrap": True},
                    {"type": "text", "text": meta, "size": "xxs", "color": "#888888", "wrap": True},
                ],
            },
            {
                "type": "text",
                "text": f"฿{item.get('total') or '-'}",
                "size": "sm",
                "weight": "bold",
                "align": "end",
                "flex": 2,
            },
        ],
    }


def preview_card(draft_id: str, mode: str, data: dict) -> dict:
    is_purchase = mode == "purchase"
    title = "ตรวจสอบเอกสารซื้อ" if is_purchase else "ตรวจสอบเอกสารขาย"
    accent = "#16873E" if is_purchase else "#B11B50"
    shown_items = (data.get("items") or [])[:4]
    more = max(0, int(data.get("item_count") or 0) - len(shown_items))
    party = data.get("party_name") or "-"
    if data.get("party_tax"):
        party += f"\nเลขผู้เสียภาษี {data['party_tax']}"
    if data.get("party_branch"):
        party += f" · สาขา {data['party_branch']}"
    if data.get("party_address"):
        party += f"\n{str(data['party_address'])[:120]}"
    item_contents = [_item_row(item) for item in shown_items]
    if not item_contents:
        item_contents.append(
            {"type": "text", "text": "ไม่พบรายการสินค้า", "size": "xs", "color": "#999999"}
        )
    if more:
        item_contents.append(
            {
                "type": "text",
                "text": f"และอีก {more} รายการ · เปิดแก้ไขเพื่อดูทั้งหมด",
                "size": "xxs",
                "color": accent,
                "margin": "md",
                "wrap": True,
            }
        )
    return {
        "type": "flex",
        "altText": title,
        "contents": {
            "type": "bubble",
            "header": {
                "type": "box",
                "layout": "vertical",
                "backgroundColor": accent,
                "paddingAll": "16px",
                "contents": [
                    {
                        "type": "text",
                        "text": title,
                        "weight": "bold",
                        "size": "lg",
                        "color": "#FFFFFF",
                    },
                    {
                        "type": "text",
                        "text": "ตรวจสอบข้อมูลก่อนบันทึกเข้าระบบ",
                        "size": "xxs",
                        "color": "#EAF7EE",
                        "margin": "xs",
                    },
                ],
            },
            "body": {
                "type": "box",
                "layout": "vertical",
                "paddingAll": "16px",
                "contents": [
                    _kv("เลขที่เอกสาร", data.get("document_no") or "-"),
                    _kv("วันที่", data.get("document_date") or "-"),
                    {"type": "separator", "margin": "lg", "color": "#EEEEEE"},
                    {
                        "type": "text",
                        "text": data.get("party_label") or "คู่ค้า",
                        "size": "xxs",
                        "color": "#777777",
                        "margin": "lg",
                    },
                    {
                        "type": "text",
                        "text": party,
                        "size": "sm",
                        "weight": "bold",
                        "wrap": True,
                        "margin": "xs",
                    },
                    {"type": "separator", "margin": "lg", "color": "#EEEEEE"},
                    {
                        "type": "text",
                        "text": f"รายการ ({data.get('item_count') or 0})",
                        "size": "xs",
                        "weight": "bold",
                        "margin": "lg",
                    },
                    *item_contents,
                    {"type": "separator", "margin": "lg", "color": "#EEEEEE"},
                    _kv("ก่อนภาษี", f"฿{data.get('subtotal') or '-'}"),
                    _kv("VAT", f"฿{data.get('vat') or '-'}"),
                    {
                        "type": "box",
                        "layout": "horizontal",
                        "margin": "md",
                        "contents": [
                            {
                                "type": "text",
                                "text": "ยอดรวม",
                                "weight": "bold",
                                "size": "sm",
                                "flex": 2,
                            },
                            {
                                "type": "text",
                                "text": f"฿{data.get('total') or '-'}",
                                "weight": "bold",
                                "size": "lg",
                                "color": accent,
                                "align": "end",
                                "flex": 4,
                            },
                        ],
                    },
                ],
            },
            "footer": {
                "type": "box",
                "layout": "vertical",
                "spacing": "sm",
                "paddingAll": "14px",
                "contents": [
                    _button("ยืนยันบันทึก", "confirm", draft_id),
                    {
                        "type": "box",
                        "layout": "horizontal",
                        "spacing": "sm",
                        "contents": [
                            {
                                "type": "button",
                                "style": "secondary",
                                "height": "sm",
                                "action": {
                                    "type": "uri",
                                    "label": "แก้ไข",
                                    "uri": edit_uri(draft_id),
                                },
                            },
                            {
                                **_button("ทิ้งเอกสาร", "discard", draft_id, "link"),
                                "color": "#C53A3A",
                            },
                        ],
                    },
                ],
            },
        },
    }


def edit_uri(draft_id: str) -> str:
    liff_id = os.getenv("LINE_ERP_LIFF_ID", "").strip()
    return (
        f"https://liff.line.me/{liff_id}?draft={draft_id}"
        if liff_id
        else f"https://pearnly.com/liff/erp/{draft_id}"
    )
