# -*- coding: utf-8 -*-
"""DMS 改写审批流的 Flex 卡与泰语文案(波4)· 纯函数,零副作用。

三张卡:销售侧「เลือกผู้อนุมัติ」选审批人(首项固定发给全部)、管理员侧申请 diff 卡
(批/拒)、销售侧等待卡(可改派)。动作名/nonce 语义沿 cards.py 单一来源;申请的
一次性由 approval_store.claim 的原子状态迁移保证,postback 只带 req(+aid)。
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from services.line_dms.cards import (
    ACT_APPROVAL_APPROVE,
    ACT_APPROVAL_REJECT,
    ACT_APPROVAL_RETARGET,
    ACT_APPROVAL_TARGET,
    _btn,
    _bubble,
    _data,
    _kv_row,
)

TXT_PICK_APPROVER = "ส่งคำขอให้ใครอนุมัติ"
TXT_PICK_APPROVER_SUB = "เลือกผู้อนุมัติ หรือส่งหาทุกคนเพื่อให้คนที่ว่างก่อนอนุมัติ"
BTN_ALL_APPROVERS = "ส่งหาทุกคน"
BTN_CHANGE_APPROVER = "เปลี่ยนผู้อนุมัติ"
BTN_APPROVE = "อนุมัติ"
BTN_REJECT = "ปฏิเสธ"

TXT_NO_APPROVERS = (
    "ยังไม่มีผู้อนุมัติที่เชื่อมต่อ LINE ในระบบ กรุณาแจ้งผู้ดูแลเพิ่มผู้อนุมัติที่ pearnly.com/dms"
)
TXT_SENT_WAIT = "ส่งคำขอแก้ไขแล้ว รอผู้อนุมัติดำเนินการ"
TXT_REQ_STALE = "คำขอนี้ถูกดำเนินการไปแล้ว"
TXT_REQ_EXPIRED = "คำขอนี้หมดอายุแล้ว กรุณาเริ่มรายการใหม่"
TXT_REQ_APPROVED_ADMIN = "อนุมัติแล้ว อัปเดตข้อมูลลูกค้าเรียบร้อย"
TXT_REQ_APPROVED_SALES = "คำขอแก้ไขได้รับอนุมัติแล้ว ข้อมูลลูกค้าอัปเดตเรียบร้อย"
TXT_REQ_REJECTED_ADMIN = "ปฏิเสธคำขอแล้ว"
TXT_REQ_REJECTED_SALES = "คำขอแก้ไขถูกปฏิเสธ หากจำเป็นกรุณาติดต่อผู้อนุมัติ"
TXT_EXEC_FAIL_ADMIN = (
    "อัปเดตไม่สำเร็จ (ระบบ DMS ปฏิเสธ) คำขอยังค้างอยู่ กดอนุมัติอีกครั้งเพื่อลองใหม่"
)
TXT_APPROVER_NO_ENDPOINT = (
    "บัญชีของคุณยังไม่ได้ตั้งค่าการเชื่อมต่อ DMS จึงอนุมัติไม่ได้ กรุณาแจ้งผู้ดูแล"
)
TXT_NOT_APPROVER = "บัญชีของคุณไม่มีสิทธิ์อนุมัติคำขอนี้"
TXT_PROCESSING = "กำลังอัปเดตข้อมูล กรุณารอสักครู่"

_MAX_APPROVER_BTNS = 6  # LINE bubble 体积约束:6-7 个管理员场景够用,更多走「发给全部」


def picker_card(request_id: str, approvers: List[Dict[str, str]]) -> Dict[str, Any]:
    """销售提审后的选审批人卡:首项固定「发给全部」,下列逐个管理员。"""
    sub = {
        "type": "text",
        "text": TXT_PICK_APPROVER_SUB,
        "size": "xs",
        "color": "#8a8a8a",
        "wrap": True,
    }
    footer = [_btn(BTN_ALL_APPROVERS, _data(ACT_APPROVAL_TARGET, req=request_id, aid="all"))]
    for ap in approvers[:_MAX_APPROVER_BTNS]:
        footer.append(
            _btn(
                ap.get("display_name") or "ผู้อนุมัติ",
                _data(ACT_APPROVAL_TARGET, req=request_id, aid=str(ap["user_id"])),
                "secondary",
            )
        )
    return _bubble(TXT_PICK_APPROVER, [sub], footer, TXT_PICK_APPROVER)


def request_card(
    request_id: str,
    operator_name: str,
    customer_name: str,
    customer_id: str,
    display_diffs: List[Dict[str, str]],
) -> Dict[str, Any]:
    """推给管理员的审批申请卡:谁提的、哪个客户、逐条 旧→新,批/拒两键。"""
    rows: List[Dict[str, Any]] = [
        _kv_row("ผู้ขอ", operator_name),
        _kv_row("ลูกค้า", f"{customer_name or '—'} ({customer_id})"),
        {"type": "separator", "margin": "sm"},
    ]
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
    footer = [
        _btn(BTN_APPROVE, _data(ACT_APPROVAL_APPROVE, req=request_id), "primary"),
        _btn(BTN_REJECT, _data(ACT_APPROVAL_REJECT, req=request_id), "secondary"),
    ]
    return _bubble("คำขอแก้ไขข้อมูลลูกค้า", rows, footer, "คำขอแก้ไขข้อมูลลูกค้า")


def waiting_card(request_id: str, target_label: Optional[str]) -> Dict[str, Any]:
    """销售侧等待回执:发给谁 + 改派按钮(指定的审批人不在时不卡死)。"""
    rows = [_kv_row("ส่งถึง", target_label or BTN_ALL_APPROVERS)]
    footer = [
        _btn(
            BTN_CHANGE_APPROVER,
            _data(ACT_APPROVAL_RETARGET, req=request_id),
            "secondary",
        )
    ]
    return _bubble(TXT_SENT_WAIT, rows, footer, TXT_SENT_WAIT)
