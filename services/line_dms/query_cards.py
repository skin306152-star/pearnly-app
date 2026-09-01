# -*- coding: utf-8 -*-
"""LINE messages and compact dashboards for fresh DMS queries."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Iterable, List
from urllib.parse import urlencode
from zoneinfo import ZoneInfo

ACT_QUERY_TYPE = "query_type"
ACT_QUERY_DIMENSION = "query_dimension"
ACT_QUERY_STATUS = "query_status"
ACT_QUERY_TOP_GROUP = "query_top_group"
ACT_QUERY_TOP_METRIC = "query_top_metric"
ACT_QUERY_TOP_PERIOD = "query_top_period"
ACT_QUERY_PAGE = "query_page"

TXT_DENIED = (
    "บัญชีนี้ยังไม่ได้รับสิทธิ์ค้นหาข้อมูลใน LINE กรุณาให้เจ้าของเปิดสิทธิ์ในหน้าผู้ปฏิบัติงาน"
)
TXT_PICK_TYPE = "กรุณาเลือกประเภทข้อมูลที่ต้องการค้นหา"
TXT_COMING_SOON = "เมนูนี้ยังไม่เปิดใช้งานในรุ่นแรก กรุณาเลือก 1 บันทึกการขาย"
TXT_PICK_SALES = "เลือกเงื่อนไขหลักเพียงข้อเดียว ระบบจะค้นหาให้ทันที ไม่ต้องตอบทุกข้อ"
TXT_LOADING = "กำลังอ่านข้อมูลล่าสุดจาก DMS"
TXT_QUERY_FAILED = "อ่านข้อมูลจาก DMS ไม่สำเร็จ กรุณาลองใหม่อีกครั้ง"
TXT_NO_ENDPOINT = "ไม่พบบัญชี DMS ที่เปิดใช้งาน กรุณาให้เจ้าของตรวจสอบข้อมูลผู้ปฏิบัติงาน"


def _data(action: str, **values: str) -> str:
    return urlencode({"action": action, **{key: value for key, value in values.items() if value}})


def _item(label: str, action: str, **values: str) -> Dict[str, Any]:
    return {
        "type": "action",
        "action": {
            "type": "postback",
            "label": label[:20],
            "displayText": label,
            "data": _data(action, **values),
        },
    }


def _quick(text: str, items: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
    return {"type": "text", "text": text, "quickReply": {"items": list(items)}}


def query_type_message() -> Dict[str, Any]:
    return _quick(
        TXT_PICK_TYPE,
        [
            _item("1 บันทึกการขาย", ACT_QUERY_TYPE, kind="sales"),
            _item("2 สินค้าคงคลัง", ACT_QUERY_TYPE, kind="inventory"),
            _item("3 รายการอื่น", ACT_QUERY_TYPE, kind="other"),
        ],
    )


def sales_dimension_message() -> Dict[str, Any]:
    choices = [
        ("ล่าสุด 10 รายการ", "latest"),
        ("ที่ปรึกษาการขาย", "advisor"),
        ("รุ่นรถ", "vehicle"),
        ("ลูกค้า", "customer"),
        ("สี", "color"),
        ("วันที่จอง", "booking_date"),
        ("วันที่ส่งมอบ", "delivery_date"),
        ("เงินสด/ไฟแนนซ์", "finance"),
        ("การจัดสรรรถ", "allocation"),
        ("สถานะสัญญา", "contract"),
        ("เลขที่เอกสารขาย", "sales_doc_no"),
        ("หมายเลขเครื่อง", "engine_no"),
        ("ยอดขายสูงสุด", "top"),
    ]
    return _quick(
        TXT_PICK_SALES,
        [_item(label, ACT_QUERY_DIMENSION, dimension=value) for label, value in choices],
    )


def input_prompt(field: str) -> Dict[str, Any]:
    prompts = {
        "advisor": "พิมพ์ชื่อที่ปรึกษาการขาย",
        "vehicle": "พิมพ์รุ่นรถ",
        "customer": "พิมพ์ชื่อลูกค้า",
        "color": "พิมพ์สีรถ",
        "booking_date": "พิมพ์วันที่จอง เช่น 01/09/2569",
        "delivery_date": "พิมพ์วันที่คาดว่าจะส่งมอบ เช่น 15/09/2569",
        "sales_doc_no": "พิมพ์เลขที่เอกสารการขาย",
        "engine_no": "พิมพ์หมายเลขเครื่อง",
    }
    return {"type": "text", "text": prompts.get(field, "พิมพ์คำที่ต้องการค้นหา")}


def status_message(kind: str) -> Dict[str, Any]:
    choices = {
        "finance": [
            ("ซื้อเงินสด", "cash"),
            ("ไฟแนนซ์รออนุมัติ", "finance_pending"),
            ("ไฟแนนซ์อนุมัติ", "finance_approved"),
            ("รอ ผจก.ขาย", "manager_pending"),
        ],
        "allocation": [
            ("ยังไม่จัดสรรรถ", "unallocated"),
            ("จัดสรรแล้ว", "allocated_no_contract"),
            ("พร้อมรับรถ", "ready"),
        ],
        "contract": [
            ("เปิดสัญญาแล้ว", "contract_opened"),
            ("ยังไม่เปิดสัญญา", "contract_not_opened"),
            ("ใบจอง", "booking"),
            ("แบบร่าง", "draft"),
        ],
    }
    return _quick(
        "เลือกสถานะที่ต้องการ",
        [_item(label, ACT_QUERY_STATUS, status=value) for label, value in choices.get(kind, [])],
    )


def top_group_message() -> Dict[str, Any]:
    return _quick(
        "จัดอันดับยอดขายตามอะไร",
        [
            _item("รุ่นรถ", ACT_QUERY_TOP_GROUP, group="model"),
            _item("ประเภทรถ", ACT_QUERY_TOP_GROUP, group="type"),
            _item("ประเภทย่อย", ACT_QUERY_TOP_GROUP, group="subtype"),
        ],
    )


def top_metric_message() -> Dict[str, Any]:
    return _quick(
        "จัดอันดับด้วยจำนวนคันหรือยอดเงิน",
        [
            _item("จำนวนคัน", ACT_QUERY_TOP_METRIC, metric="quantity"),
            _item("ยอดเงิน", ACT_QUERY_TOP_METRIC, metric="amount"),
        ],
    )


def top_period_message() -> Dict[str, Any]:
    return _quick(
        "เลือกช่วงเวลาและจำนวนรายการ (ทุกสาขา/ทีมที่บัญชีนี้มองเห็น)",
        [
            _item("เดือนนี้ Top 5", ACT_QUERY_TOP_PERIOD, period="month", limit="5"),
            _item("เดือนนี้ Top 10", ACT_QUERY_TOP_PERIOD, period="month", limit="10"),
            _item("เดือนนี้ Top 20", ACT_QUERY_TOP_PERIOD, period="month", limit="20"),
            _item("เดือนนี้ Top 30", ACT_QUERY_TOP_PERIOD, period="month", limit="30"),
            _item("ปีนี้ Top 10", ACT_QUERY_TOP_PERIOD, period="year", limit="10"),
            _item("กำหนดเอง 1–30", ACT_QUERY_TOP_PERIOD, period="custom"),
        ],
    )


def top_custom_prompt() -> Dict[str, Any]:
    return {
        "type": "text",
        "text": "พิมพ์ช่วงวันที่และจำนวนรายการ เช่น 01/08/2569-31/08/2569 15",
    }


def _now_label() -> str:
    now = datetime.now(ZoneInfo("Asia/Bangkok"))
    return now.strftime("%d/%m/%Y %H:%M")


def _text_row(label: str, value: Any) -> Dict[str, Any]:
    return {
        "type": "box",
        "layout": "baseline",
        "spacing": "sm",
        "contents": [
            {"type": "text", "text": label, "size": "xxs", "color": "#8a8a8a", "flex": 2},
            {
                "type": "text",
                "text": str(value or "—"),
                "size": "xs",
                "color": "#222238",
                "wrap": True,
                "flex": 5,
            },
        ],
    }


def _record_bubble(row: dict, position: int) -> Dict[str, Any]:
    status = row.get("record_status") or "ไม่ระบุสถานะ"
    rows = [
        _text_row("ลูกค้า", row.get("customer")),
        _text_row("รถ", " · ".join(filter(None, [row.get("vehicle"), row.get("color")]))),
        _text_row("ที่ปรึกษา", row.get("advisor")),
        _text_row("วันที่", row.get("booking_date")),
        _text_row("ส่งมอบ", row.get("delivery_date")),
        _text_row("ไฟแนนซ์", row.get("finance_status")),
        _text_row("จัดสรร", row.get("allocation_status")),
    ]
    if row.get("sales_doc_no") or row.get("engine_no"):
        rows.append(
            _text_row(
                "เอกสาร/เครื่อง",
                " · ".join(filter(None, [row.get("sales_doc_no"), row.get("engine_no")])),
            )
        )
    return {
        "type": "bubble",
        "size": "micro",
        "body": {
            "type": "box",
            "layout": "vertical",
            "paddingAll": "14px",
            "contents": [
                {
                    "type": "text",
                    "text": f"{position}. {row.get('booking_no') or '—'}",
                    "weight": "bold",
                    "size": "sm",
                    "wrap": True,
                    "color": "#392e66",
                },
                {
                    "type": "text",
                    "text": status,
                    "size": "xxs",
                    "color": "#7656d6",
                    "margin": "xs",
                    "wrap": True,
                },
                {"type": "separator", "margin": "md", "color": "#eeeaf8"},
                {
                    "type": "box",
                    "layout": "vertical",
                    "spacing": "sm",
                    "margin": "md",
                    "contents": rows,
                },
            ],
        },
    }


def _navigation(result: dict, kind: str) -> List[Dict[str, Any]]:
    actions = []
    page = int(result.get("page") or 1)
    if page > 1:
        actions.append(_item("หน้าก่อน", ACT_QUERY_PAGE, kind=kind, direction="prev"))
    actions.append(_item("อ่านใหม่", ACT_QUERY_PAGE, kind=kind, direction="refresh"))
    if result.get("has_more"):
        actions.append(_item("หน้าถัดไป", ACT_QUERY_PAGE, kind=kind, direction="next"))
    return actions


def _button(item: Dict[str, Any]) -> Dict[str, Any]:
    return {"type": "button", "style": "link", "height": "sm", "action": item["action"]}


def sales_board(result: dict) -> Dict[str, Any]:
    rows = result.get("rows") or []
    if not rows:
        return _quick(
            "ไม่พบรายการตามเงื่อนไขนี้ · อ่านจาก DMS ล่าสุดเมื่อ " + _now_label(),
            _navigation(result, "records"),
        )
    page = int(result.get("page") or 1)
    summary = {
        "type": "bubble",
        "size": "micro",
        "body": {
            "type": "box",
            "layout": "vertical",
            "paddingAll": "16px",
            "backgroundColor": "#f5f1ff",
            "contents": [
                {"type": "text", "text": "บันทึกการขายจาก DMS", "weight": "bold", "size": "md"},
                {
                    "type": "text",
                    "text": "สถานะเอกสารแสดงตาม DMS จริง · แบบร่างไม่นับเป็นยอดขาย",
                    "size": "xxs",
                    "wrap": True,
                    "color": "#6d6680",
                    "margin": "sm",
                },
                _text_row("หน้า", page),
                _text_row("จำนวน", len(rows)),
                _text_row("อ่านล่าสุด", _now_label()),
            ],
        },
        "footer": {
            "type": "box",
            "layout": "vertical",
            "spacing": "sm",
            "contents": [_button(item) for item in _navigation(result, "records")],
        },
    }
    bubbles = [summary]
    offset = (page - 1) * int(result.get("limit") or 10)
    bubbles.extend(_record_bubble(row, offset + index) for index, row in enumerate(rows, 1))
    return {
        "type": "flex",
        "altText": f"บันทึกการขายล่าสุดจาก DMS {len(rows)} รายการ",
        "contents": {"type": "carousel", "contents": bubbles[:12]},
    }


def top_sales_board(result: dict) -> Dict[str, Any]:
    metric = result.get("metric")
    unit = "บาท" if metric == "amount" else "คัน"
    lines = []
    for index, row in enumerate(result.get("rows") or [], 1):
        value = row.get("value")
        if metric == "amount":
            try:
                value = f"{float(value):,.2f}"
            except (TypeError, ValueError):
                value = str(value or 0)
        lines.append(f"{index}. {row.get('label') or '—'}  {value} {unit}")
    text = "\n".join(lines) if lines else "ไม่พบยอดขายในช่วงเวลานี้"
    navigation = _navigation(result, "top")
    bubble = {
        "type": "bubble",
        "body": {
            "type": "box",
            "layout": "vertical",
            "paddingAll": "18px",
            "contents": [
                {"type": "text", "text": "ยอดขายสูงสุด", "weight": "bold", "size": "lg"},
                {
                    "type": "text",
                    "text": f"{result.get('date_from')} – {result.get('date_to')}",
                    "size": "xs",
                    "color": "#7656d6",
                    "margin": "xs",
                },
                {
                    "type": "text",
                    "text": text,
                    "size": "sm",
                    "wrap": True,
                    "margin": "lg",
                    "lineSpacing": "6px",
                },
                {
                    "type": "text",
                    "text": "ทุกสาขา/ทีมที่บัญชีนี้มองเห็น · อ่านล่าสุด " + _now_label(),
                    "size": "xxs",
                    "wrap": True,
                    "color": "#8a8a8a",
                    "margin": "lg",
                },
            ],
        },
        "footer": {
            "type": "box",
            "layout": "horizontal",
            "contents": [_button(item) for item in navigation],
        },
    }
    return {"type": "flex", "altText": "ยอดขายสูงสุดจาก DMS", "contents": bubble}


__all__ = [name for name in globals() if name.startswith("ACT_")]
