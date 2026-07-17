# -*- coding: utf-8 -*-
"""DMS LINE 对话流的 Flex 卡与泰语文案(DL-3)· 纯函数,零副作用、零网络。

flow.py 组装状态后调这里出卡;所有对外可见字符串集中在此,便于单测对照断言
(照 webhook 的 _MSG_* 范式)。文案面向经销商销售员:简洁、不堆 emoji。
按钮一律 postback,data 用 querystring 编码 action(+nonce/+cid),flow 侧解析核对。
"""

from __future__ import annotations

from typing import Any, Dict, List
from urllib.parse import urlencode

# ── 文案(单一来源 · 测试按此断言) ─────────────────────────────────────────
TXT_BLURRY = "อ่านบัตรไม่ชัด กรุณาถ่ายใหม่"
TXT_ASK_PHONE = "รับรูปบัตรแล้ว กรุณาพิมพ์เบอร์โทรศัพท์ของลูกค้า"
TXT_ASK_CARD = "รับเบอร์โทรแล้ว กรุณาถ่ายรูปบัตรประชาชนของลูกค้า"
TXT_RESET = "เริ่มรายการใหม่แล้ว ถ่ายรูปบัตรประชาชนเพื่อเริ่มบันทึกลูกค้า"
TXT_INTRO = "ถ่ายรูปบัตรประชาชนของลูกค้าเพื่อเริ่มบันทึกลูกค้าใหม่"
TXT_NEED_BOTH = "กรุณาส่งรูปบัตรประชาชนและเบอร์โทรศัพท์ของลูกค้า"
TXT_PICK_ABOVE = "กรุณาเลือกรายการจากการ์ดด้านบน หรือพิมพ์ เริ่มใหม่ เพื่อเริ่มรายการใหม่"
TXT_EXPIRED = "รายการหมดอายุ เริ่มใหม่อีกครั้ง"
TXT_SAME = "ลูกค้าท่านนี้มีข้อมูลอยู่แล้ว ข้อมูลตรงกัน"
TXT_KEEP = "ใช้ข้อมูลเดิมต่อ"
TXT_ADMIN_NEEDED = "ต้องตั้งค่าบัญชีแอดมินใน Pearnly ก่อนจึงจะอัปเดตได้"
TXT_ADMIN_AUTH_FAIL = "อัปเดตไม่สำเร็จ กรุณาแจ้งผู้ดูแลตรวจสอบรหัสแอดมินใน Pearnly"
TXT_NO_ENDPOINT = "ยังไม่ได้ตั้งค่าการเชื่อมต่อ DMS กรุณาติดต่อผู้ดูแล"
TXT_LOOKUP_FAIL = "ตรวจสอบข้อมูลลูกค้าไม่สำเร็จ กรุณาลองใหม่"
TXT_SAVE_FAIL = "บันทึกไม่สำเร็จ กรุณาลองใหม่"

BTN_SAVE_NEW = "บันทึกลูกค้าใหม่"
BTN_RESTART = "เริ่มใหม่"
BTN_UPDATE = "อัปเดตข้อมูล"
BTN_KEEP = "ใช้ข้อมูลเดิม"
BTN_NEW_CUSTOMER = "ลูกค้าใหม่"

# 动作名(flow 侧 dispatch 用同一常量,避免拼写漂移)
ACT_CREATE = "create_new"
ACT_UPDATE = "update"
ACT_KEEP = "keep"
ACT_RESET = "reset"
ACT_PICK = "pick"

FIELD_LABELS_TH: Dict[str, str] = {
    "prefix_id": "คำนำหน้า",
    "name": "ชื่อ",
    "birthday_be": "วันเกิด",
    "phone": "เบอร์โทร",
    "house_no": "บ้านเลขที่",
    "moo": "หมู่",
    "soi": "ซอย",
    "road": "ถนน",
    "province_id": "จังหวัด",
    "district_id": "อำเภอ",
    "subdistrict_id": "ตำบล",
    "zipcode_id": "รหัสไปรษณีย์",
}

_MAX_CANDIDATES = 4  # 候选卡按钮上限(LINE bubble 体积约束)


def _data(action: str, **kw: str) -> str:
    """postback data 编码:action + 可选 nonce/cid。querystring 稳定可核对。"""
    return urlencode({"action": action, **{k: v for k, v in kw.items() if v}})


def _btn(label: str, data: str, style: str = "primary") -> Dict[str, Any]:
    return {
        "type": "button",
        "style": style,
        "height": "sm",
        "action": {"type": "postback", "label": label, "data": data, "displayText": label},
    }


def _kv_row(label: str, value: str) -> Dict[str, Any]:
    return {
        "type": "box",
        "layout": "baseline",
        "spacing": "sm",
        "contents": [
            {"type": "text", "text": label, "size": "sm", "color": "#8a8a8a", "flex": 2},
            {
                "type": "text",
                "text": value or "—",
                "size": "sm",
                "color": "#111111",
                "flex": 5,
                "wrap": True,
            },
        ],
    }


def _bubble(
    header: str, body_rows: List[Dict[str, Any]], footer_btns: List[Dict[str, Any]], alt: str
) -> Dict[str, Any]:
    return {
        "type": "flex",
        "altText": alt,
        "contents": {
            "type": "bubble",
            "body": {
                "type": "box",
                "layout": "vertical",
                "spacing": "sm",
                "contents": [
                    {"type": "text", "text": header, "weight": "bold", "size": "md", "wrap": True},
                    {"type": "separator", "margin": "sm"},
                    *body_rows,
                ],
            },
            "footer": {
                "type": "box",
                "layout": "vertical",
                "spacing": "sm",
                "contents": footer_btns,
            },
        },
    }


def new_customer_card(summary: Dict[str, str], nonce: str) -> Dict[str, Any]:
    """场景①新建:五要素复述 + [บันทึกลูกค้าใหม่][เริ่มใหม่]。"""
    rows = [
        _kv_row("เลขบัตร", summary.get("people_id", "")),
        _kv_row("ชื่อ", summary.get("name", "")),
        _kv_row("วันเกิด", summary.get("birthday_be", "")),
        _kv_row("ที่อยู่", summary.get("address", "")),
        _kv_row("เบอร์โทร", summary.get("phone", "")),
    ]
    footer = [
        _btn(BTN_SAVE_NEW, _data(ACT_CREATE, nonce=nonce), "primary"),
        _btn(BTN_RESTART, _data(ACT_RESET), "secondary"),
    ]
    return _bubble("ลูกค้าใหม่ ยืนยันข้อมูลเพื่อบันทึก", rows, footer, "ยืนยันบันทึกลูกค้าใหม่")


def diff_card(display_diffs: List[Dict[str, str]], has_admin: bool, nonce: str) -> Dict[str, Any]:
    """场景③已有客户 + 有差异:逐条「字段: 旧 → 新」+ 按钮。

    配了 admin → [อัปเดตข้อมูล][ใช้ข้อมูลเดิม];没配 → 设置提示 + [ใช้ข้อมูลเดิม](不给更新键)。
    """
    rows: List[Dict[str, Any]] = []
    for d in display_diffs:
        rows.append(
            {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "text",
                        "text": d.get("label", ""),
                        "size": "sm",
                        "weight": "bold",
                        "color": "#111111",
                    },
                    {
                        "type": "text",
                        "text": f"{d.get('old') or '—'}  →  {d.get('new') or '—'}",
                        "size": "sm",
                        "color": "#c0392b",
                        "wrap": True,
                    },
                ],
            }
        )
    footer: List[Dict[str, Any]] = []
    if has_admin:
        footer.append(_btn(BTN_UPDATE, _data(ACT_UPDATE, nonce=nonce), "primary"))
    else:
        rows.append({"type": "separator", "margin": "sm"})
        rows.append(
            {
                "type": "text",
                "text": TXT_ADMIN_NEEDED,
                "size": "xs",
                "color": "#8a8a8a",
                "wrap": True,
            }
        )
    footer.append(_btn(BTN_KEEP, _data(ACT_KEEP), "secondary"))
    return _bubble("พบข้อมูลเดิม มีบางส่วนไม่ตรงกัน", rows, footer, "พบข้อมูลลูกค้าที่ต่างกัน")


def candidates_card(candidates: List[Dict[str, str]], nonce: str) -> Dict[str, Any]:
    """场景④相似:候选按钮(码 · 姓名 · 证号尾4)+ [ลูกค้าใหม่] 兜底。人工认领。"""
    rows: List[Dict[str, Any]] = []
    for c in candidates[:_MAX_CANDIDATES]:
        cid = str(c.get("customer_id") or "")
        tail = (str(c.get("people_id") or ""))[-4:]
        label = f"{c.get('cuscode') or '—'} · {c.get('name') or ''}"
        if tail:
            label += f" · x{tail}"
        rows.append(_btn(label[:40], _data(ACT_PICK, nonce=nonce, cid=cid), "link"))
    footer = [_btn(BTN_NEW_CUSTOMER, _data(ACT_CREATE, nonce=nonce), "primary")]
    return _bubble(
        "พบลูกค้าที่ใกล้เคียง เลือกรายการที่ตรงกัน", rows, footer, "เลือกลูกค้าที่ตรงกัน"
    )


def receipt_text(customer_id: str, name: str, mode: str) -> str:
    """写档成功回执:客户码 + 姓名 + 做了什么(诚实告知实际动作)。"""
    action = "สร้างลูกค้าใหม่" if mode == "create" else "อัปเดตข้อมูลลูกค้า"
    return f"บันทึกสำเร็จ · {action}\nรหัสลูกค้า: {customer_id or '—'}\nชื่อ: {name or '—'}"
