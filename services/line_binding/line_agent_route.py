# -*- coding: utf-8 -*-
"""灰度用户前门路由收口(批一·止血)。

灰度用户(全量)由前门大脑裁决。核心止血:把「大脑故障(crash)」与「模型主动裁决(defer)」分开——
  reply        → 发大脑人话(接管)
  card_sent    → 记账已直录出卡(接管)
  crash        → 温和安全兜底(接管)· ★绝不掉旧路地雷(问价格/静默错入账/第二个大脑)
  defer_record → 交旧路(确定性直录·记账救命索)
  defer_edit   → 交旧路(改错/撤销/删除等·保留全部旧能力·铁律 能力只增不减)
无余额     → 交旧路(与旧 L2 同口径,省算力)

即:只有「大脑真故障」才被拦在安全兜底;模型主动判为记账/改错的,照旧交确定性路,能力一个不丢。
"""

from __future__ import annotations

from services.line_binding import line_agent_bridge

# 大脑故障时的安全兜底(四语·温和中性·不追问价格·不逼记账)。
_SAFE_FALLBACK = {
    "th": "อยู่ตรงนี้นะคะ 😊 มีอะไรให้เพิร์นลี่ช่วยไหมคะ",
    "zh": "我在呢~😊 有什么可以帮你的吗?",
    "en": "I'm here 😊 Is there anything I can help you with?",
    "ja": "ここにいますよ😊 何かお手伝いできることはありますか?",
}


def _safe_line(lang: str) -> str:
    return _SAFE_FALLBACK.get(lang, _SAFE_FALLBACK["en"])


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
    say,
    charge,
    book,
) -> bool:
    """前门裁决 → 处理 reply/card_sent/crash 并返回 True(已消费);
    defer_record/defer_edit/无余额 → 返回 False(交调用方旧路,保留全部旧能力)。"""
    if not balance_ok:
        return False  # 无余额不跑大脑 → 旧路(与旧 L2 同口径)

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
        book=book,
    )
    if res.kind == "reply":
        charge()
        say(res.text)
        return True
    if res.kind == "card_sent":
        charge()
        return True
    if res.kind == "crash":
        # ★大脑故障(parse 失败/空回复/工具错)→ 安全兜底,绝不掉旧路地雷(问价格/错入账/第二脑)。
        say(_safe_line(lang))
        return True
    return False  # defer_record / defer_edit → 交旧路(记账/改错/撤销等确定性能力)
