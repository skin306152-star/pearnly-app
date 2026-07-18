# -*- coding: utf-8 -*-
"""DMS LINE 菜单层(波2):เมนู/问候语弹菜单 → 选建档或订车 → 走既有采集流。

泰方客户照 ChatGPT mockup 要一层入口:用户不必记「先拍卡」的隐式流程,发问候语即见
「1 จัดทำข้อมูลลูกค้า / 2 จัดทำใบจอง」两选项。选完落到 collecting,只是给会话打一个 mode:
  · customer —— 建档为终点,写档后问「要不要顺便订车」而非自动跳订车(客户可能只想建档)。
  · booking / 缺省 —— 建档后自动串联订车(老用户直接拍卡的行为逐字节不变)。
mode 存在会话 payload,_run_dedup 读它决定写档后的分叉(见 after_customer_saved)。

flow.py 只留分发钩子,采集/查重/写档主干仍在 flow;本文件不碰 OCR/计费(菜单层不产生
二次扣费,id_card 已在会话里)。菜单/继续/重拍三类动作均无 nonce 消费:菜单是无状态入口,
继续订车以 cid 对齐防串档,重拍照 edit 范式只校验 reviewing 态的 nonce 不消费。
"""

from __future__ import annotations

from typing import Optional

from services.line_binding import line_client
from services.line_dms import booking_flow, cards, store
from services.line_dms._out import _CHANNEL, _reply, _thr

MENU_ACTIONS = frozenset(
    {
        cards.ACT_MENU_CUSTOMER,
        cards.ACT_MENU_BOOKING,
        cards.ACT_CONTINUE_BOOKING,
        cards.ACT_RETAKE,
    }
)

_MENU_WORD = "เมนู"
_GREETING_PREFIX = "สวัสดี"
_MENU_CHOICES = {"1": cards.ACT_MENU_CUSTOMER, "2": cards.ACT_MENU_BOOKING}
# 弹菜单/切模式时保留的已收料:重复进菜单不丢已拍的卡/已输的号。
_KEEP_KEYS = ("id_card", "phone", "endpoint_id", "mode")


# ── text:弹菜单 / menu 态下的单字 1|2 ───────────────────────────────────────
async def handle_text(
    binding: dict, line_user_id: str, reply_token: str, sess: Optional[dict], text: str
) -> bool:
    """处理菜单相关文本,返回是否已接管(未接管则 flow 继续走手机号/nudge)。

    เมนู 或问候语 → 弹菜单(先于手机号判定);menu 态下的 '1'/'2' → 等同点对应菜单项。
    其余数字文本(如手机号)不被吃成菜单——只认这两个单字符。
    """
    stripped = text.strip()
    if stripped == _MENU_WORD or stripped.startswith(_GREETING_PREFIX):
        await _enter_menu(binding, line_user_id, sess)
        line_client.reply_messages(reply_token, [cards.menu_card()], channel=_CHANNEL)
        return True
    if (sess or {}).get("state") == "menu" and stripped in _MENU_CHOICES:
        await _choose(binding, line_user_id, reply_token, sess, _MENU_CHOICES[stripped])
        return True
    return False


async def _enter_menu(binding: dict, line_user_id: str, sess: Optional[dict]) -> None:
    """置 menu 态,保留已收料(含 mode):弹菜单不丢用户已拍/已输的东西。"""
    old = (sess or {}).get("payload") or {}
    payload = {k: old.get(k) for k in _KEEP_KEYS if old.get(k)}
    await _thr(store.set_session, binding["tenant_id"], line_user_id, "menu", payload)


# ── postback:菜单项 / 继续订车 / 重拍 ───────────────────────────────────────
async def handle_postback(
    binding: dict,
    line_user_id: str,
    reply_token: str,
    action: str,
    pb: dict,
    sess: Optional[dict],
) -> None:
    if action in (cards.ACT_MENU_CUSTOMER, cards.ACT_MENU_BOOKING):
        await _choose(binding, line_user_id, reply_token, sess, action)
    elif action == cards.ACT_CONTINUE_BOOKING:
        await _continue_booking(binding, line_user_id, reply_token, pb, sess)
    else:  # ACT_RETAKE
        await _retake(binding, line_user_id, reply_token, pb, sess)


async def _choose(
    binding: dict, line_user_id: str, reply_token: str, sess: Optional[dict], action: str
) -> None:
    """选中菜单项:给会话打 mode 回 collecting;齐料直接查重,缺料按缺项提示补料。"""
    mode = "customer" if action == cards.ACT_MENU_CUSTOMER else "booking"
    old = (sess or {}).get("payload") or {}
    payload = {k: old.get(k) for k in ("id_card", "phone", "endpoint_id") if old.get(k)}
    payload["mode"] = mode
    await _thr(store.set_session, binding["tenant_id"], line_user_id, "collecting", payload)

    id_card, phone = payload.get("id_card"), payload.get("phone")
    if id_card and phone:
        from services.line_dms import flow  # 延迟导入避免 flow ↔ menu_flow 环依赖

        flow._spawn(
            flow._run_dedup(binding, line_user_id, None, id_card, phone, payload.get("endpoint_id"))
        )
        return
    if id_card:
        _reply(reply_token, cards.TXT_ASK_PHONE)
        return
    if phone:
        _reply(reply_token, cards.TXT_ASK_CARD)
        return
    _reply(reply_token, cards.TXT_MENU_SEND_CARD)


async def _continue_booking(
    binding: dict, line_user_id: str, reply_token: str, pb: dict, sess: Optional[dict]
) -> None:
    """continue 卡的 [ทำใบจองต่อ]:postback cid 须对齐会话客户号(防串到别的档)→ 走选车。"""
    payload = (sess or {}).get("payload") or {}
    cid = pb.get("cid") or ""
    if not cid or cid != str(payload.get("customer_id") or ""):
        _reply(reply_token, cards.TXT_EXPIRED)
        return
    await booking_flow.offer_pick(
        binding,
        line_user_id,
        endpoint_id=str(payload.get("endpoint_id") or ""),
        customer_id=cid,
        draft=payload.get("draft") or {},
        name=str(payload.get("name") or ""),
    )


async def _retake(
    binding: dict, line_user_id: str, reply_token: str, pb: dict, sess: Optional[dict]
) -> None:
    """reviewing 卡的 [ถ่ายบัตรใหม่]:清 id_card 留 phone/mode/endpoint 回 collecting 等重拍。

    nonce 只校验不消费(照 edit 范式):重拍是读操作,写档仍由 flow 的 consume_nonce 守卫;
    旧卡的确认因态已回 collecting 而必被拒。nonce 不符 → 过期话术、会话不动。
    """
    payload = (sess or {}).get("payload") or {}
    nonce = pb.get("nonce")
    if not (sess and sess.get("state") == "reviewing" and nonce and payload.get("nonce") == nonce):
        _reply(reply_token, cards.TXT_EXPIRED)
        return
    kept = {k: payload.get(k) for k in ("phone", "mode", "endpoint_id") if payload.get(k)}
    await _thr(store.set_session, binding["tenant_id"], line_user_id, "collecting", kept)
    _reply(reply_token, cards.TXT_RETAKE)


# ── 客户档落定后的分叉(mode 门控订车串联) ─────────────────────────────────
async def after_customer_saved(
    binding: dict,
    line_user_id: str,
    *,
    endpoint_id: str,
    customer_id: str,
    draft: dict,
    name: str = "",
    mode: str = "",
    same_data: bool = False,
) -> None:
    """客户档落定后:booking/缺省 → 照旧 offer_pick;customer → 推 continue 卡等用户决定。

    same_data=True 表示本次零写入(数据已存/选择保留),文案不谎称「已保存」。"""
    if mode != "customer":
        await booking_flow.offer_pick(
            binding,
            line_user_id,
            endpoint_id=endpoint_id,
            customer_id=customer_id,
            draft=draft,
            name=name,
        )
        return

    tenant = binding["tenant_id"]
    if not customer_id:  # 无客户号 → 订车无从谈起,收干净(建档非订车必经)
        await _thr(store.clear_session, tenant, line_user_id)
        return
    payload = {
        "endpoint_id": str(endpoint_id or ""),
        "customer_id": str(customer_id),
        "draft": draft or {},
        "name": name or (draft or {}).get("name", ""),
        "mode": mode,
    }
    await _thr(store.set_session, tenant, line_user_id, "menu_after_save", payload)
    line_client.push_messages(
        line_user_id, [cards.continue_booking_card(customer_id, same_data)], channel=_CHANNEL
    )
