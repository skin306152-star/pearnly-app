from __future__ import annotations

import os

from services.line_platform.summary_review_card import build_summary_card, postback_action


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
