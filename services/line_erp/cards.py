from __future__ import annotations

import os
from urllib.parse import urlencode

from services.line_dms.menu_cards import (
    THEME_GREEN,
    THEME_PURPLE,
    menu_icon_disc,
)
from services.line_platform.summary_review_card import build_summary_card, postback_action

_TARGET_REASON = {
    "endpoint_disabled": "การเชื่อมต่อนี้ถูกปิดใช้งาน",
    "credentials_missing": "ยังไม่ได้ตั้งค่าบัญชี MR.ERP",
    "erp_connection_failed": "เชื่อมต่อ MR.ERP ไม่สำเร็จ",
    "companion_offline": "โปรแกรมผู้ช่วย Express ออฟไลน์",
    "companion_not_ready": "โปรแกรมผู้ช่วย Express ยังไม่พร้อม",
    "profile_unconfirmed": "ยังไม่ได้ยืนยันชุดบัญชี Express",
    "profile_mismatch": "ชุดบัญชี Express ไม่ตรงกับที่ตั้งค่า",
    "account_set_unavailable": "ไม่พบชุดบัญชี MR.ERP ที่ตั้งค่าไว้",
    "workspace_unbound": "ยังไม่ได้ผูกบัญชี Pearnly",
    "workspace_binding_conflict": "ERP นี้ผูกกับหลายบัญชี",
    "account_set_locked": "ชุดบัญชี Express กำลังถูกใช้งาน",
    "endpoint_revoked": "การเชื่อมต่อนี้ถูกยกเลิก",
}


def _menu_tile(
    num: str,
    icon: str,
    title: str,
    description: str,
    action: str,
    theme: dict[str, str],
) -> dict:
    return {
        "type": "box",
        "layout": "vertical",
        "flex": 1,
        "height": "124px",
        "paddingAll": "12px",
        "cornerRadius": "14px",
        "borderWidth": "1px",
        "borderColor": theme["border"],
        "backgroundColor": "#FFFFFF",
        "action": {
            "type": "postback",
            "data": urlencode({"a": action}),
            "displayText": title,
        },
        "contents": [
            {
                "type": "box",
                "layout": "horizontal",
                "alignItems": "center",
                "contents": [
                    menu_icon_disc(icon, theme["soft"], "38px", "22px"),
                    {"type": "filler"},
                    {
                        "type": "text",
                        "text": num,
                        "size": "lg",
                        "weight": "bold",
                        "color": theme["accent"],
                        "flex": 0,
                    },
                ],
            },
            {"type": "text", "text": title, "size": "sm", "weight": "bold", "margin": "sm"},
            {
                "type": "text",
                "text": description,
                "size": "xxs",
                "color": "#8A8A8A",
                "wrap": True,
                "margin": "xs",
            },
        ],
    }


def _menu_placeholder() -> dict:
    return {
        "type": "box",
        "layout": "vertical",
        "flex": 1,
        "height": "124px",
        "paddingAll": "12px",
        "cornerRadius": "14px",
        "borderWidth": "1px",
        "borderColor": "#EEEEF4",
        "backgroundColor": "#F8F8FA",
        "contents": [{"type": "filler"}],
    }


def _menu_grid(modes: tuple[str, ...]) -> dict:
    allowed = set(modes or ())
    cells = [
        (
            _menu_tile(
                "1",
                "erp-purchase",
                "ซื้อ",
                "บันทึกเอกสารซื้อและเพิ่มสินค้าเข้าสต๊อก",
                "mode:purchase",
                THEME_GREEN,
            )
            if "purchase" in allowed
            else _menu_placeholder()
        ),
        (
            _menu_tile(
                "2",
                "erp-sales",
                "ขาย",
                "บันทึกเอกสารขายและตัดสินค้าออกจากสต๊อก",
                "mode:sales",
                THEME_PURPLE,
            )
            if "sales" in allowed
            else _menu_placeholder()
        ),
        *(_menu_placeholder() for _ in range(4)),
    ]
    return {
        "type": "box",
        "layout": "vertical",
        "spacing": "sm",
        "margin": "lg",
        "contents": [
            {"type": "box", "layout": "horizontal", "spacing": "sm", "contents": cells[0:2]},
            {"type": "box", "layout": "horizontal", "spacing": "sm", "contents": cells[2:4]},
            {"type": "box", "layout": "horizontal", "spacing": "sm", "contents": cells[4:6]},
        ],
    }


def menu_card(modes=("purchase", "sales")) -> dict:
    """Render navigation independently; target readiness is checked after mode selection."""
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
                        "type": "box",
                        "layout": "horizontal",
                        "spacing": "md",
                        "alignItems": "center",
                        "contents": [
                            menu_icon_disc("menu-head", "#EAF0FF", "40px", "22px"),
                            {
                                "type": "box",
                                "layout": "vertical",
                                "flex": 1,
                                "contents": [
                                    {
                                        "type": "text",
                                        "text": "เลือกประเภทเอกสาร ERP",
                                        "weight": "bold",
                                        "size": "lg",
                                        "wrap": True,
                                    },
                                    {
                                        "type": "text",
                                        "text": "เลือกรายการก่อนส่งรูปภาพหรือ PDF",
                                        "size": "xxs",
                                        "color": "#8A8A8A",
                                        "wrap": True,
                                        "margin": "xs",
                                    },
                                ],
                            },
                        ],
                    },
                    {"type": "separator", "margin": "lg", "color": "#eeeef4"},
                    _menu_grid(tuple(modes or ())),
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


def _target_item(target: dict, mode: str) -> dict:
    ready = bool(target.get("selectable"))
    workspace = str(target.get("workspace_name") or "บัญชี Pearnly")[:80]
    label = str(target.get("label") or target.get("adapter") or "ERP")[:80]
    reason = _TARGET_REASON.get(
        str(target.get("block_reason") or ""), "ปลายทางนี้ยังไม่พร้อมใช้งาน"
    )
    data = urlencode(
        {
            "a": "target",
            "mode": mode,
            "endpoint": str(target.get("endpoint_id") or ""),
            "workspace": str(target.get("workspace_client_id") or ""),
        }
    )
    item = {
        "type": "box",
        "layout": "vertical",
        "margin": "md",
        "paddingAll": "12px",
        "cornerRadius": "12px",
        "borderWidth": "1px",
        "borderColor": "#7C4DFF" if ready else "#E0E0E8",
        "backgroundColor": "#FFFFFF" if ready else "#F7F7FA",
        "contents": [
            {"type": "text", "text": workspace, "size": "sm", "weight": "bold", "wrap": True},
            {
                "type": "text",
                "text": label,
                "size": "xs",
                "color": "#555566",
                "wrap": True,
                "margin": "xs",
            },
            {
                "type": "text",
                "text": "พร้อมใช้งาน" if ready else reason,
                "size": "xxs",
                "color": "#16873E" if ready else "#B42318",
                "margin": "sm",
            },
        ],
    }
    if ready:
        item["action"] = {"type": "postback", "data": data, "displayText": workspace}
    return item


def target_picker_card(mode: str, targets: list[dict], page: int = 0) -> dict:
    page_size = 6
    page = max(0, int(page or 0))
    start = page * page_size
    visible = targets[start : start + page_size]
    nav = []
    if page > 0:
        nav.append(
            {
                "type": "button",
                "style": "secondary",
                "height": "sm",
                "action": {
                    "type": "postback",
                    "label": "ก่อนหน้า",
                    "data": urlencode({"a": "target-page", "mode": mode, "page": page - 1}),
                },
            }
        )
    if start + page_size < len(targets):
        nav.append(
            {
                "type": "button",
                "style": "secondary",
                "height": "sm",
                "action": {
                    "type": "postback",
                    "label": "ถัดไป",
                    "data": urlencode({"a": "target-page", "mode": mode, "page": page + 1}),
                },
            }
        )
    contents = [
        {"type": "text", "text": "เลือกบัญชีและ ERP", "weight": "bold", "size": "lg"},
        {
            "type": "text",
            "text": "ปลายทางนี้จะใช้กับเอกสารชุดปัจจุบันเท่านั้น",
            "size": "xs",
            "color": "#777788",
            "wrap": True,
            "margin": "xs",
        },
        *[_target_item(target, mode) for target in visible],
    ]
    if not visible:
        contents.append(
            {
                "type": "text",
                "text": "ยังไม่มี ERP ที่ผูกกับบัญชี Pearnly",
                "size": "sm",
                "color": "#B42318",
                "wrap": True,
                "margin": "lg",
            }
        )
    if nav:
        contents.append(
            {
                "type": "box",
                "layout": "horizontal",
                "spacing": "sm",
                "margin": "lg",
                "contents": nav,
            }
        )
    return {
        "type": "flex",
        "altText": "เลือกบัญชีและ ERP",
        "contents": {
            "type": "bubble",
            "body": {
                "type": "box",
                "layout": "vertical",
                "paddingAll": "16px",
                "contents": contents,
            },
        },
    }


def posting_mode_card(mode: str, target: dict) -> dict:
    adapter = str(target.get("adapter") or "").lower()
    if adapter == "express":
        options = [("stock", "สินค้าในสต๊อก"), ("service", "บริการ / ไม่กระทบสต๊อก")]
        title = "เลือกรูปแบบการบันทึก"
    else:
        options = [("credit", "เครดิต")]
        if mode == "sales":
            options.insert(0, ("cash", "เงินสด"))
        title = "เลือกวิธีชำระเงิน"
    buttons = [
        {
            "type": "button",
            "style": "primary" if index == 0 else "secondary",
            "color": "#7C4DFF" if index == 0 else None,
            "margin": "md" if index else "lg",
            "action": {
                "type": "postback",
                "label": label,
                "displayText": label,
                "data": urlencode({"a": f"posting:{value}"}),
            },
        }
        for index, (value, label) in enumerate(options)
    ]
    for button in buttons:
        if button.get("color") is None:
            button.pop("color", None)
    return {
        "type": "flex",
        "altText": title,
        "contents": {
            "type": "bubble",
            "body": {
                "type": "box",
                "layout": "vertical",
                "paddingAll": "16px",
                "contents": [
                    {"type": "text", "text": title, "weight": "bold", "size": "lg"},
                    {
                        "type": "text",
                        "text": f"{target.get('workspace_name') or ''} · {target.get('label') or ''}",
                        "size": "xs",
                        "color": "#777788",
                        "wrap": True,
                        "margin": "xs",
                    },
                    *buttons,
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


def preview_card(draft_id: str, mode: str, data: dict) -> dict:
    is_purchase = mode == "purchase"
    title = "ตรวจสอบเอกสารซื้อ" if is_purchase else "ตรวจสอบเอกสารขาย"
    accent = "#16873E" if is_purchase else "#B11B50"
    party = data.get("party_name") or "-"
    if data.get("party_tax"):
        party += f"\nเลขผู้เสียภาษี {data['party_tax']}"
    if data.get("party_branch"):
        party += f" · สาขา {data['party_branch']}"
    if data.get("party_address"):
        party += f"\n{str(data['party_address'])[:120]}"
    summary = [
        _kv("จำนวนเอกสาร", str(max(1, int(data.get("document_count") or 1)))),
        _kv("เลขที่เอกสาร", data.get("document_no") or "-"),
        _kv("วันที่", data.get("document_date") or "-"),
        {"type": "separator", "margin": "lg", "color": "#EEEEEE"},
        _kv(data.get("party_label") or "คู่ค้า", party),
        _kv("ก่อนภาษี", f"฿{data.get('subtotal') or '-'}"),
        _kv("VAT", f"฿{data.get('vat') or '-'}"),
        _kv("ยอดรวม", f"฿{data.get('total') or '-'}"),
    ]
    return build_summary_card(
        title=title,
        subtitle="สรุปเอกสาร · เปิดรายละเอียดเพื่อตรวจสอบและลงบัญชี",
        alt_text=title,
        accent=accent,
        summary=summary,
        detail_label="รายการสินค้า/บริการ",
        detail_count=int(data.get("item_count") or 0),
        detail_hint="แตะเพื่อดูเอกสารต้นฉบับ ฟิลด์ OCR และรายการทั้งหมด",
        edit_label="ดู / แก้ไขรายละเอียด",
        edit_uri=edit_uri(draft_id),
        discard_action=postback_action("ทิ้งเอกสาร", "discard", draft_id),
    )


def edit_uri(draft_id: str) -> str:
    liff_id = os.getenv("LINE_ERP_LIFF_ID", "").strip()
    return (
        f"https://liff.line.me/{liff_id}/?flow=erp-intake&draft={draft_id}"
        if liff_id
        else f"https://pearnly.com/liff/erp?flow=erp-intake&draft={draft_id}"
    )
