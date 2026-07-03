# -*- coding: utf-8 -*-
"""灰度用户前门路由收口(批一·止血)。

灰度用户(全量)由前门大脑裁决。核心止血:把「大脑故障(crash)」与「模型主动裁决(defer)」分开——
  reply        → 发大脑人话(接管)
  card_sent    → 写动作已由确定性执行落地出卡(接管)
  crash        → 先试 L1 确定性直录救援(大脑挂掉时清晰记账句不丢账),否则温和安全兜底(接管)
                 ★绝不掉旧 LLM 地雷(问价格/静默错入账/第二个大脑)
  defer_record → 交旧路(确定性直录·记账救命索)
  defer_edit   → 交旧路(改错/撤销/删除等·保留全部旧能力·铁律 能力只增不减)
无余额     → 交旧路(与旧 L2 同口径,省算力)

即:只有「大脑真故障」才被拦在安全兜底;模型主动判为记账/改错的,照旧交确定性路,能力一个不丢。
"""

from __future__ import annotations

import logging

from services.line_binding import line_agent_bridge

logger = logging.getLogger(__name__)

# 大脑故障时的安全兜底(四语·温和中性·不追问价格·不逼记账)。
_SAFE_FALLBACK = {
    "th": "อยู่ตรงนี้นะคะ 😊 มีอะไรให้เพิร์นลี่ช่วยไหมคะ",
    "zh": "我在呢~😊 有什么可以帮你的吗?",
    "en": "I'm here 😊 Is there anything I can help you with?",
    "ja": "ここにいますよ😊 何かお手伝いできることはありますか?",
}


def _safe_line(lang: str) -> str:
    return _SAFE_FALLBACK.get(lang, _SAFE_FALLBACK["en"])


def _say_with_chips(bound_user, reply_token, body, user_text, lang, tid, line_user_id, quote_token):
    """带 quick-reply chips 的文本回复(P2·教用户能问什么)。
    闸关/发送失败/任何异常 → False,调用方走纯文本 say——chips 是锦上添花,绝不许丢回复。"""
    try:
        from services.agent import quick_chips

        if not quick_chips.enabled_for(str((bound_user or {}).get("id") or "")):
            return False
        from services.line_binding import line_reply

        msg = {
            "type": "text",
            "text": str(body),
            "quickReply": quick_chips.quick_reply(user_text, lang),
        }
        return bool(
            line_reply.reply_messages_context(
                reply_token,
                [msg],
                line_user_id=line_user_id,
                tenant_id=tid,
                quote_token=quote_token or "",
            )
        )
    except Exception:
        logger.warning("[line agent] chips reply failed; plain text", exc_info=True)
        return False


def _l1_rescue_draft(text: str):
    """大脑故障时的分级兜底判定:只对「无 LLM 也能确定性解析」的清晰单笔记账句放行 L1 直录。

    地雷是旧 LLM 误路和反问池,不是 L1 直录本身——供应商抖 5 分钟,"กาแฟ 50" 丢账比
    归类略糙伤害大得多(设计 §3.4·Zihao 授权拍板)。四重否定守门:问句/非断言/改错形/
    收入句/多笔一律不救(宁可安全兜底,绝不误记);救援路只直录、永不反问。
    """
    from services.expense import line_quick_entry as lqe

    try:
        if lqe.parse_multi(text):
            return None
        if lqe.is_question(text) or lqe.is_nonassertive(text) or lqe.is_edit_request(text):
            return None
        if lqe.detect_income(text):
            return None
        parsed = lqe.parse_expense(text)
        if not parsed.has_amount() or not lqe.has_item_context(text):
            return None
        return parsed
    except Exception:  # 救援判定自身出错 → 不救,走安全兜底(救援绝不能把故障变事故)
        return None


def route_gated(
    bound_user,
    reply_token,
    line_user_id,
    text,
    lang,
    tid,
    ws,
    quote_token,
    history,
    *,
    balance_ok,
    quoted_message_id=None,
    say,
    charge,
    book,
) -> str:
    """前门裁决 → 处理 reply/card_sent/crash 并返回 "consumed";其余把模型裁决交还调用方:
    "defer_record"/"defer_edit"(旧路按裁决走对应确定性能力,绝不再第二次解读成别的意图)/
    "skip"(无余额,大脑没上场)。★裁决不许丢:defer_edit 的消息若掉进 L1 记账分支,
    "แก้รายการล่าสุดเป็น 80" 会被误记成一笔 80 新支出(harness 语料抓出的真地雷)。"""
    if not balance_ok:
        return "skip"  # 无余额不跑大脑 → 旧路(与旧 L2 同口径)

    res = line_agent_bridge.try_agent_turn(
        bound_user,
        text,
        lang,
        tid,
        ws,
        line_user_id,
        history,
        reply_token=reply_token,
        quote_token=quote_token,
        quoted_message_id=quoted_message_id,
        book=book,
    )
    if res.kind == "reply":
        charge()
        if not _say_with_chips(
            bound_user, reply_token, res.text, text, lang, tid, line_user_id, quote_token
        ):
            say(res.text)
        return "consumed"
    if res.kind == "card_sent":
        charge()
        return "consumed"
    if res.kind == "crash":
        # ★大脑故障 → 分级兜底:清晰单笔记账句走 L1 确定性直录(零 LLM·不丢账·不计费),
        # 其余安全兜底一句。绝不掉旧 LLM 地雷(问价格/错入账/第二脑)。
        draft = _l1_rescue_draft(text)
        if draft is not None and book:
            try:
                book(
                    bound_user,
                    reply_token,
                    text,
                    tid,
                    ws,
                    draft,
                    False,
                    quote_token,
                    lang,
                    line_user_id,
                )
                logger.info("[line agent] crash rescued via L1 direct record")
                return "consumed"
            except Exception:
                logger.warning("[line agent] L1 rescue failed; safe fallback", exc_info=True)
        # 安全兜底带 chips 最有用:用户正不知道能干嘛,给 2-3 个可点的下一步
        if not _say_with_chips(
            bound_user, reply_token, _safe_line(lang), text, lang, tid, line_user_id, quote_token
        ):
            say(_safe_line(lang))
        return "consumed"
    # defer_record / defer_edit → 交旧路对应确定性能力,并把裁决一起交回(防二次误判)。
    return res.kind
