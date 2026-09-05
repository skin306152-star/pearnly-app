# -*- coding: utf-8 -*-
"""DMS LINE 菜单层(波2):เมนู/问候语弹菜单 → 选建档或订车 → 走既有采集流。

泰方客户照 ChatGPT mockup 要一层入口:用户不必记「先拍卡」的隐式流程,发问候语即见
「1 จัดทำข้อมูลลูกค้า / 2 จัดทำใบจอง」两选项。选完落到 collecting,只是给会话打一个 mode:
  · customer —— 建档为终点,写档后收尾不提订车(泰方拍板:菜单1不弹订车信息)。
  · booking / 缺省 —— 建档后自动串联订车(老用户直接拍卡的行为逐字节不变)。
mode 存在会话 payload,_run_dedup 读它决定写档后的分叉(见 after_customer_saved)。

flow.py 只留分发钩子,采集/查重/写档主干仍在 flow;本文件不碰 OCR/计费(菜单层不产生
二次扣费,id_card 已在会话里)。菜单/继续/重拍三类动作均无 nonce 消费:菜单是无状态入口,
继续订车以 cid 对齐防串档,重拍照 edit 范式只校验 reviewing 态的 nonce 不消费。
"""

from __future__ import annotations

from typing import Optional

from services.cloud_tasks import dispatch as cloud_dispatch
from services.line_platform import client as line_client
from services.line_dms import booking_qa, cards, menu_cards, query_access, store
from services.line_dms._out import _CHANNEL, _push, _reply, _thr

MENU_ACTIONS = frozenset(
    {
        cards.ACT_MENU_CUSTOMER,
        cards.ACT_MENU_BOOKING,
        cards.ACT_CONTINUE_BOOKING,
        cards.ACT_RETAKE,
    }
)

# mode 语义单一落点:customer=只建档收尾;其余(booking/缺省直拍)串联订车。
# flow 出卡分流与本文件落档分流都引用它,别再散写裸字符串比较。
MODE_CUSTOMER = "customer"
_MENU_CHOICES = {
    "1": cards.ACT_MENU_CUSTOMER,
    "2": cards.ACT_MENU_BOOKING,
    "5": cards.ACT_MENU_QUERY,
}
# 弹菜单/切模式时保留的已收料:重复进菜单不丢已拍的卡/已输的号;id_card_mid 是
# 订车逐问的身份证附件源,同样保留(客户档落定后 booking_qa.start 要挂附件)。
_KEEP_KEYS = ("id_card", "id_card_mid", "phone", "endpoint_id", "mode")


# ── text:弹菜单 / menu 态下的单字 1|2 ───────────────────────────────────────
async def open_menu(
    binding: dict,
    line_user_id: str,
    reply_token: str,
    sess: Optional[dict],
    *,
    greet: bool = False,
) -> None:
    """置 menu 态(保留已收料含 mode:弹菜单不丢用户已拍/已输的东西)→ 发菜单卡。

    greet = 问候语进场,照 mockup 先来一句欢迎;เมนู 是回访召唤,只发卡不寒暄。
    词形判定在 commands.classify,本函数只管落态出卡。
    """
    old = (sess or {}).get("payload") or {}
    payload = {k: old.get(k) for k in _KEEP_KEYS if old.get(k)}
    await _thr(store.set_session, binding["tenant_id"], line_user_id, "menu", payload)
    allowed = await _thr(query_access.can_query, binding)
    msgs: list = [menu_cards.menu_card(can_query=bool(allowed))]
    if greet:
        msgs.insert(0, {"type": "text", "text": cards.TXT_MENU_GREETING})
    line_client.reply_messages(reply_token, msgs, channel=_CHANNEL)


async def handle_choice(
    binding: dict, line_user_id: str, reply_token: str, sess: Optional[dict], text: str
) -> bool:
    """menu 态下的单字 '1'/'2' = 点对应菜单项,返回是否已接管。

    只认这两个单字符:其余数字文本(如手机号)交回调用方走号码路。
    """
    stripped = text.strip()
    if (sess or {}).get("state") != "menu" or stripped not in _MENU_CHOICES:
        return False
    action = _MENU_CHOICES[stripped]
    if action == cards.ACT_MENU_QUERY:
        from services.line_dms import query_flow

        await query_flow.open_query(binding, line_user_id, reply_token)
    else:
        await _choose(binding, line_user_id, reply_token, sess, action)
    return True


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
    """选中菜单项:给会话打 mode 回 collecting;齐料直接查重,缺料按缺项提示补料。

    有进行中逐问/待确认订车也照常进菜单(会话被覆写 = 放弃,与 เริ่มใหม่ 同语义,不拦)。
    """
    mode = MODE_CUSTOMER if action == cards.ACT_MENU_CUSTOMER else "booking"
    old = (sess or {}).get("payload") or {}
    # 保留清单派生自 _KEEP_KEYS(mode 由本函数按所选菜单重写,不从旧会话带)。
    payload = {k: old.get(k) for k in _KEEP_KEYS if k != "mode" and old.get(k)}
    payload["mode"] = mode
    await _thr(store.set_session, binding["tenant_id"], line_user_id, "collecting", payload)

    id_card, phone = payload.get("id_card"), payload.get("phone")
    if id_card and phone:
        from services.line_dms import flow  # 延迟导入避免 flow ↔ menu_flow 环依赖

        cloud_dispatch.spawn(
            "dms.dedup",
            flow._run_dedup,
            binding,
            line_user_id,
            None,
            id_card,
            phone,
            payload.get("endpoint_id"),
            _legacy_spawn=flow._spawn,
        )
        return
    if id_card:
        tail = cards.TXT_ASK_PHONE
    elif phone:
        tail = cards.TXT_ASK_CARD
    else:
        tail = cards.TXT_MENU_SEND_CARD
    _reply(reply_token, tail)


async def _continue_booking(
    binding: dict, line_user_id: str, reply_token: str, pb: dict, sess: Optional[dict]
) -> None:
    """continue 卡的 [ทำใบจองต่อ]:postback cid 须对齐会话客户号(防串到别的档)→ 开逐问。"""
    payload = (sess or {}).get("payload") or {}
    cid = pb.get("cid") or ""
    if not cid or cid != str(payload.get("customer_id") or ""):
        _reply(reply_token, cards.TXT_EXPIRED)
        return
    await booking_qa.start(
        binding["tenant_id"],
        line_user_id,
        endpoint_id=str(payload.get("endpoint_id") or ""),
        customer_id=cid,
        customer_name=str(payload.get("name") or ""),
        draft=payload.get("draft") or {},
        summary=payload.get("summary"),
        user_id=str(binding.get("user_id") or ""),
        id_card_mid=payload.get("id_card_mid") or None,
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
    if not store.verify_nonce(sess, nonce):
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
    summary: Optional[dict] = None,
) -> None:
    """客户档落定后:booking/缺省 → 开订车逐问;customer → 收尾不提订车。

    菜单1=只建档(泰方拍板 2026-07-19):不再推「ทำใบจองต่อ?」续订卡;其 postback
    处理保留,聊天历史里已发出的旧卡仍能点。same_data=True 表示本次零写入
    (数据已存/选择保留),文案不谎称「已保存」。summary 透传给逐问开局,预览卡
    与客户确认卡共用同一份五要素。"""
    if mode != MODE_CUSTOMER:
        sess = await _thr(store.get_session, binding["tenant_id"], line_user_id)
        payload = (sess or {}).get("payload") or {}
        await booking_qa.start(
            binding["tenant_id"],
            line_user_id,
            endpoint_id=endpoint_id,
            customer_id=customer_id,
            # 零写入路径(同资料点保持)不传 name → 回退建档 draft 里的姓名(照旧选车入口语义)。
            customer_name=name or (draft or {}).get("name", ""),
            draft=draft,
            summary=summary,
            user_id=str(binding.get("user_id") or ""),
            id_card_mid=payload.get("id_card_mid") or None,
        )
        return

    await _thr(store.clear_session, binding["tenant_id"], line_user_id)
    _push(line_user_id, cards.TXT_DONE_SAME if same_data else cards.TXT_DONE_SAVED)
