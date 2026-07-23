# -*- coding: utf-8 -*-
"""待选车会话的保护与选车链接重发(P1-12)。

面板 token 只活 15 分钟,而面板端点还要求会话停在 picking——用户在 LINE 里随手打一句带
数字的话,会话就被冲成 collecting,一条还没过期的链接当场 401;打 เมนู 冲成 menu 同理。
旧路径下唯一的补救是重拍身份证,而那是真扣一次 OCR 费。

本文件把 picking / booking_review 两个态圈起来:客户档已落定,文本一律不覆写会话,改出
一张重发卡;重发只拿会话里现成的 endpoint_id/customer_id/draft/name 重签 token,零 OCR、
零写档、零扣费。
"""

from __future__ import annotations

from typing import List, Optional

from services.line_binding import line_client
from services.line_dms import booking_flow, cards, menu_cards
from services.line_dms._out import _CHANNEL, _reply

# 客户档已落定、只差选车/确认订车的两个态。证件与手机号都在手上,不必再向用户要材料。
PICK_STATES = frozenset({"picking", "booking_review"})


def is_pending(sess: Optional[dict]) -> bool:
    """会话停在待选车态(客户档已落定,手上可能还有一条有效的选车链接)。"""
    return bool(sess and sess.get("state") in PICK_STATES)


def pending_customer_id(sess: Optional[dict]) -> str:
    """待选车会话里的客户号(纯取值,状态判定归 is_pending)。"""
    return str(((sess or {}).get("payload") or {}).get("customer_id") or "")


def reply_if_pending(reply_token: str, sess: Optional[dict], *, with_menu: bool = False) -> bool:
    """待选车态收到文本:出重发卡、一个字节不动会话。返回是否已接管。

    不覆写会话是要害:会话态是面板端点的准入条件,冲掉它等于把用户手上那条还没过期的
    链接一起掐死。with_menu = 用户打的是 เมนู/问候语 —— 菜单是合法诉求照发,但仍不落
    menu 态(open_menu 会覆写会话),重发卡挂在菜单卡后面,离输入框最近一指可点。
    """
    if not is_pending(sess):
        return False
    cid = pending_customer_id(sess)
    msgs: List[dict] = [menu_cards.menu_card()] if with_menu else []
    if cid:
        msgs.append(cards.pick_resume_card(cid))
    if msgs:
        line_client.reply_messages(reply_token, msgs, channel=_CHANNEL)
    else:  # 无客户号 = 这条待选车会话已经没救(生产不可达,守着异常态别静默)
        _reply(reply_token, cards.TXT_EXPIRED)
    return True


async def handle_postback(
    binding: dict, line_user_id: str, reply_token: str, pb: dict, sess: Optional[dict]
) -> None:
    """[ขอลิงก์เลือกรถใหม่]:cid 对齐会话客户号 → 重签面板 token 重推入口。

    cid 对齐照 continue 卡范式防串档(翻聊天记录点别人那张卡不算数)。重发是纯读:
    不碰 OCR、不写客户档,offer_pick 换新 nonce 顺带让旧链接失效。
    """
    payload = (sess or {}).get("payload") or {}
    cid = pb.get("cid") or ""
    if not is_pending(sess) or not cid or cid != pending_customer_id(sess):
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
