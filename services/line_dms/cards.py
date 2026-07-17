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
TXT_NO_CREDIT = "เครดิตไม่พอ กรุณาติดต่อผู้ดูแลเพื่อเติมเครดิต"
TXT_BAD_PHONE_FORMAT = "เบอร์โทรไม่ถูกต้อง ต้องขึ้นต้นด้วย 0 และมี 9-10 หลัก เช่น 0812345678"
TXT_SYSTEM_ERROR = "ระบบขัดข้อง กรุณาลองใหม่อีกครั้ง"
TXT_LOOKUP_FAIL = "ตรวจสอบข้อมูลลูกค้าไม่สำเร็จ กรุณาลองใหม่"
TXT_SAVE_FAIL = "บันทึกไม่สำเร็จ กรุณาลองใหม่"

BTN_SAVE_NEW = "บันทึกลูกค้าใหม่"
BTN_RESTART = "เริ่มใหม่"
BTN_UPDATE = "อัปเดตข้อมูล"
BTN_KEEP = "ใช้ข้อมูลเดิม"
BTN_NEW_CUSTOMER = "ลูกค้าใหม่"
BTN_EDIT = "แก้ไข"
BTN_EDIT_CANCEL = "ยกเลิก"

# 逐字段修正(DL-6):可改字段与地道泰文标签(顺序 = quick reply 呈现顺序)。
# 地理四级 id(จังหวัด/อำเภอ/ตำบล/รหัสไปรษณีย์)不进此表——改地址文本后由既有级联匹配重解。
EDIT_FIELDS = (
    ("name", "ชื่อ-นามสกุล"),
    ("people_id", "เลขบัตรประชาชน"),
    ("birthday_be", "วันเกิด"),
    ("phone", "เบอร์โทร"),
    ("house_no", "บ้านเลขที่"),
    ("moo", "หมู่"),
    ("soi", "ซอย"),
    ("road", "ถนน"),
)
_EDIT_LABELS = dict(EDIT_FIELDS)

TXT_EDIT_PICK = "ต้องการแก้ไขข้อมูลใด"
TXT_EDIT_CANCELLED = "ยกเลิกการแก้ไขแล้ว"
TXT_EDIT_BAD_ID = "เลขบัตรประชาชนไม่ถูกต้อง กรุณาพิมพ์เลข 13 หลักให้ถูกต้อง"
TXT_EDIT_BAD_BIRTHDAY = "วันเกิดไม่ถูกต้อง กรุณาพิมพ์เป็น วว/ดด/ปปปป (พ.ศ.)"
TXT_EDIT_BAD_PHONE = "เบอร์โทรไม่ถูกต้อง กรุณาพิมพ์เบอร์ 9-10 หลักขึ้นต้นด้วย 0"
TXT_EDIT_EMPTY = "กรุณาพิมพ์ข้อมูลให้ครบถ้วน"

# 动作名(flow 侧 dispatch 用同一常量,避免拼写漂移)
ACT_CREATE = "create_new"
ACT_UPDATE = "update"
ACT_KEEP = "keep"
ACT_RESET = "reset"
ACT_PICK = "pick"
# 逐字段修正(DL-6):卡上 [แก้ไข] 开菜单 → 选字段 → 收新值 → 重跑查重。
ACT_EDIT = "edit"
ACT_EDIT_FIELD = "edit_field"
ACT_EDIT_CANCEL = "edit_cancel"
# 订车阶段(DL-4a):选车面板落定后的预览确认(booking_flow 侧 dispatch)。
ACT_CONFIRM_BOOKING = "confirm_booking"
ACT_CANCEL_BOOKING = "cancel_booking"

# 订车阶段文案与按钮(DL-4a)
BTN_PICK_CAR = "เลือกรถ (จองรถ)"
BTN_CONFIRM_BOOKING = "ยืนยันจอง"
BTN_CANCEL_BOOKING = "ยกเลิก"
TXT_PICK_INTRO = "บันทึกข้อมูลลูกค้าเรียบร้อย ต้องการเปิดใบจองรถให้ลูกค้าท่านนี้หรือไม่ กดปุ่มด้านล่างเพื่อเลือกรถ"
TXT_BOOKING_CANCELLED = "ยกเลิกการจองแล้ว"
TXT_BOOKING_FAIL = "สร้างใบจองไม่สำเร็จ กรุณาลองใหม่"

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


def _qr_item(label: str, data: str) -> Dict[str, Any]:
    """quick reply 动作项(postback · data 编码 action+nonce+field)。"""
    return {
        "type": "action",
        "action": {"type": "postback", "label": label, "data": data, "displayText": label},
    }


def edit_menu_message(nonce: str) -> Dict[str, Any]:
    """[แก้ไข] 展开的字段选择(quick reply)· 每项带 field 键 + 当前 nonce,末项取消。"""
    items = [
        _qr_item(label, _data(ACT_EDIT_FIELD, nonce=nonce, field=key)) for key, label in EDIT_FIELDS
    ]
    items.append(_qr_item(BTN_EDIT_CANCEL, _data(ACT_EDIT_CANCEL, nonce=nonce)))
    return {"type": "text", "text": TXT_EDIT_PICK, "quickReply": {"items": items}}


def edit_prompt(field: str) -> str:
    """选中字段后的输入提示:พิมพ์ค่าใหม่ของ<字段名>。"""
    return f"พิมพ์ค่าใหม่ของ{_EDIT_LABELS.get(field, field)}"


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
        _btn(BTN_EDIT, _data(ACT_EDIT, nonce=nonce), "secondary"),
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
    footer.append(_btn(BTN_EDIT, _data(ACT_EDIT, nonce=nonce), "secondary"))
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


# ── 订车阶段(DL-4a) ────────────────────────────────────────────────────
def pick_button_message(pick_url: str) -> Dict[str, Any]:
    """客户档落定后推的选车入口:URI 按钮跳车辆选择面板(带签名 token)。"""
    return {
        "type": "flex",
        "altText": BTN_PICK_CAR,
        "contents": {
            "type": "bubble",
            "body": {
                "type": "box",
                "layout": "vertical",
                "spacing": "sm",
                "contents": [{"type": "text", "text": TXT_PICK_INTRO, "size": "sm", "wrap": True}],
            },
            "footer": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "button",
                        "style": "primary",
                        "height": "sm",
                        "action": {"type": "uri", "label": BTN_PICK_CAR, "uri": pick_url},
                    }
                ],
            },
        },
    }


def booking_review_card(preview: Dict[str, str], nonce: str) -> Dict[str, Any]:
    """选车提交后的订车预览:客户五要素 + 车型/颜色/价格/顾问/交车日 + [ยืนยันจอง][ยกเลิก]。"""
    rows = [
        _kv_row("ลูกค้า", preview.get("customer_name", "")),
        _kv_row("เลขบัตร", preview.get("people_id", "")),
        _kv_row("รุ่นรถ", preview.get("car", "")),
        _kv_row("สี", preview.get("paint", "")),
        _kv_row("ราคา", preview.get("price", "")),
        _kv_row("ที่ปรึกษา", preview.get("advisor", "")),
        _kv_row("วันที่ส่งมอบ", preview.get("delivery_date_be", "")),
    ]
    footer = [
        _btn(BTN_CONFIRM_BOOKING, _data(ACT_CONFIRM_BOOKING, nonce=nonce), "primary"),
        _btn(BTN_CANCEL_BOOKING, _data(ACT_CANCEL_BOOKING), "secondary"),
    ]
    return _bubble("ยืนยันการจองรถ", rows, footer, "ยืนยันการจองรถ")


def booking_receipt_text(booking_no: str, car: str, delivery_date_be: str) -> str:
    """订车成功回执:BK 单号 + 车型 + 交车日。"""
    return (
        f"เปิดใบจองสำเร็จ\nเลขที่ใบจอง: {booking_no or '—'}\n"
        f"รุ่นรถ: {car or '—'}\nวันที่ส่งมอบ: {delivery_date_be or '—'}"
    )
