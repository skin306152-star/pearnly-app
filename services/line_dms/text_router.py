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
from services.line_dms import cards, commands, edit_flow, menu_cards, menu_flow, pick_resume, store
from services.line_dms._out import _CHANNEL, _reply, _thr


async def route(binding: dict, line_user_id: str, reply_token: str, text: str) -> None:
    tenant = binding["tenant_id"]
    sess = await _thr(store.get_session, tenant, line_user_id)
    cmd = commands.classify(text)

    if cmd == commands.CMD_RESET:
        await _thr(store.clear_session, tenant, line_user_id)
        _reply(reply_token, cards.TXT_RESET)
        return

    if cmd in (commands.CMD_MENU, commands.CMD_GREETING):
        if pick_resume.reply_menu_if_pending(reply_token, sess):
            return
        if (sess or {}).get("state") == "editing":
            # 编辑被菜单打断:就地结束编辑(半截新值作废、已收料留着),不把 editing 带进菜单。
            sess = edit_flow.exit_editing(sess)
        await menu_flow.open_menu(
            binding, line_user_id, reply_token, sess, greet=cmd == commands.CMD_GREETING
        )
        return

    if (sess or {}).get("state") == "editing":  # 逐字段修正:下一条文本 = 新值
        await edit_flow.handle_text(binding, line_user_id, reply_token, sess, text)
        return

    # 待选车态(picking/booking_review):档已落定,文本一律不进下面任何会覆写会话的路
    # ——一次覆写就废掉手上那条选车链接,而重来要重拍身份证、真扣一次 OCR 费。
    if pick_resume.reply_if_pending(reply_token, sess):
        return

    # menu 态的单字 1/2 = 点对应菜单项;其余数字文本(手机号)不被吃成菜单。
    if await menu_flow.handle_choice(binding, line_user_id, reply_token, sess, text):
        return

    if any(ch.isdigit() for ch in text):
        await _capture_phone(binding, line_user_id, reply_token, sess, text)
        return

    nudge = _nudge(sess)
    if nudge is None:  # 无会话 → 菜单卡引路(取代旧 TXT_INTRO 文本)
        line_client.reply_messages(reply_token, [menu_cards.menu_card()], channel=_CHANNEL)
    else:
        _reply(reply_token, nudge)


async def _capture_phone(
    binding: dict, line_user_id: str, reply_token: str, sess: Optional[dict], text: str
) -> None:
    """号码透传:ERP 是权威,它吃什么送什么,不在 Pearnly 写死格式(Zihao 拍板)。
    含数字即视为号码(纯路由判据,区分号码与闲聊);格式对错由 DMS 保存时裁决。"""
    from services.line_dms import flow  # 延迟导入避免 flow ↔ text_router 环依赖

    payload = await flow._merge_session(
        binding, line_user_id, {"phone": text}, keep=("id_card", "endpoint_id", "mode"), sess=sess
    )
    if not payload.get("id_card"):
        _reply(reply_token, cards.TXT_ASK_CARD)
        return
    flow._spawn(
        flow._run_dedup(
            binding, line_user_id, None, payload["id_card"], text, payload.get("endpoint_id")
        )
    )


def _nudge(sess: Optional[dict]) -> Optional[str]:
    """按当前收料进度给下一步提示;None = 无会话,调用方弹菜单卡引路。

    只管「还缺材料」的态:picking/booking_review 已由上面的 pick_resume 分支接管,
    落不到这里——已建档的用户再听见「请发身份证和手机号」就是要人重付一次 OCR。
    """
    if not sess:
        return None
    if sess.get("state") == "reviewing":
        return cards.TXT_PICK_ABOVE
    payload = sess.get("payload") or {}
    if payload.get("id_card") and not payload.get("phone"):
        return cards.TXT_ASK_PHONE
    if payload.get("phone") and not payload.get("id_card"):
        return cards.TXT_ASK_CARD
    return cards.TXT_NEED_BOTH
