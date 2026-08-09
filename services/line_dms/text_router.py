# -*- coding: utf-8 -*-
"""DMS LINE 文本分发:全局命令 → 状态分支 → 号码/缺料提示。

分发顺序是这条对话流的安全属性:全局命令(commands.classify)先于任何状态判定。
editing 态曾对文本有优先占有权,菜单词被当成新姓名写进 id_card 并重跑查重;editing
只是众多状态之一,不该独占文本。

会话在入口只读一次,沿分支透传,同一条消息不重复读库。
"""

from __future__ import annotations

from typing import Optional

from services.line_binding import line_client
from services.line_dms import (
    booking_qa,
    cards,
    commands,
    edit_flow,
    menu_cards,
    menu_flow,
    qa_cards,
    store,
)
from services.line_dms._out import _CHANNEL, _reply, _thr


async def route(binding: dict, line_user_id: str, reply_token: str, text: str) -> None:
    tenant = binding["tenant_id"]
    cmd = commands.classify(text)  # 纯函数、零 IO:重置路径压根不必读会话

    if cmd == commands.CMD_RESET:
        await _thr(store.clear_session, tenant, line_user_id)
        _reply(reply_token, cards.TXT_RESET)
        return

    sess = await _thr(store.get_session, tenant, line_user_id)
    state = (sess or {}).get("state")

    if cmd in (commands.CMD_MENU, commands.CMD_GREETING):
        # 菜单命令覆盖任何进行中会话(含逐问):会话被覆写 = 放弃,与 เริ่มใหม่ 同语义。
        if state == "editing":
            # 编辑被菜单打断:就地结束编辑(半截新值作废、已收料留着),不把 editing 带进菜单。
            sess = {"payload": edit_flow.exit_editing(sess)}
        await menu_flow.open_menu(
            binding, line_user_id, reply_token, sess, greet=cmd == commands.CMD_GREETING
        )
        return

    if state == "editing":  # 逐字段修正:下一条文本 = 新值
        await edit_flow.handle_text(binding, line_user_id, reply_token, sess, text)
        return

    # 逐问/确认态先于一切文本路(尤其「含数字→手机号」):金额/单字被吃成号码就废一次会话。
    # booking_review 态文本只提醒点确认/丢弃,不覆写会话(确认/取消是 postback 专属)。
    if state == "booking_qa":
        if await booking_qa.handle_text(
            binding["tenant_id"], line_user_id, text, reply_token, sess=sess
        ):
            return
    if state == "booking_review":
        _reply(reply_token, qa_cards.TXT_CONFIRM_ABOVE)
        return

    # menu 态的单字 1/2 = 点对应菜单项;其余数字文本(手机号)不被吃成菜单。
    if await menu_flow.handle_choice(binding, line_user_id, reply_token, sess, text):
        return

    if any(ch.isdigit() for ch in text):
        await _capture_phone(binding, line_user_id, reply_token, sess, text)
        return

    if not sess:  # 无会话 → 菜单卡引路(取代旧 TXT_INTRO 文本)
        line_client.reply_messages(reply_token, [menu_cards.menu_card()], channel=_CHANNEL)
    else:
        _reply(reply_token, _nudge(sess))


async def _capture_phone(
    binding: dict, line_user_id: str, reply_token: str, sess: Optional[dict], text: str
) -> None:
    """号码透传:ERP 是权威,它吃什么送什么,不在 Pearnly 写死格式(Zihao 拍板)。
    含数字即视为号码(纯路由判据,区分号码与闲聊);格式对错由 DMS 保存时裁决。"""
    from services.line_dms import flow  # 延迟导入避免 flow ↔ text_router 环依赖

    payload = await flow._merge_session(
        binding,
        line_user_id,
        {"phone": text},
        keep=("id_card", "id_card_mid", "endpoint_id", "mode"),
        sess=sess,
    )
    if not payload.get("id_card"):
        _reply(reply_token, cards.TXT_ASK_CARD)
        return
    flow._spawn(
        flow._run_dedup(
            binding, line_user_id, None, payload["id_card"], text, payload.get("endpoint_id")
        )
    )


def _nudge(sess: dict) -> str:
    """按当前收料进度给下一步提示(无会话由调用方弹菜单卡引路,不进这里)。

    只管「还缺材料」的态:booking_qa/booking_review 已由上面的分支接管,落不到这里——
    已建档的用户再听见「请发身份证和手机号」就是要人重付一次 OCR。
    """
    if sess.get("state") == "reviewing":
        return cards.TXT_PICK_ABOVE
    payload = sess.get("payload") or {}
    if payload.get("id_card") and not payload.get("phone"):
        return cards.TXT_ASK_PHONE
    if payload.get("phone") and not payload.get("id_card"):
        return cards.TXT_ASK_CARD
    return cards.TXT_NEED_BOTH
