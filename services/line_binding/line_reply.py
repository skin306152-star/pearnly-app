# -*- coding: utf-8 -*-
"""LINE 统一回复出口(P1C):loading + quoteToken + 截断 + 失败日志 + bot 对话记忆。

每次 Pearnly 回复都让用户知道三件事:① 我正在处理(begin_loading·处理开始前转圈)
② 我在回应哪句话(quoteToken 引用用户触发的那条消息)③ 我执行/拒绝哪个动作(文案)。

约束:quoteToken 仅作展示引用,LINE 只允许 text 消息携带 → 注入首条 text;业务对象定位
仍走 quotedMessageId / line_message_refs,绝不拿 quoteToken 当定位源。无 quoteToken 照常
回复不报错。loading / 记忆均 best-effort,失败不阻断主回复。Flex 卡的带引用回执走 line_booker
(它需 sentMessages 元数据绑定记录),本模块管其余全部文本/确认/失败/闲聊/引导/查账回复。
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from services.line_binding import line_client

logger = logging.getLogger("mr-pilot")

_MAX_TEXT = 5000


def begin_loading(line_user_id: Optional[str]) -> None:
    """处理开始前显示转圈(best-effort·失败不阻断)。webhook 入口每事件调一次。"""
    if not line_user_id:
        return
    try:
        line_client.start_loading(line_user_id)
    except Exception as e:
        logger.warning(f"[line_reply] start_loading 跳过(不阻断): {e}")


def _truncate(messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    out = []
    for m in messages:
        if isinstance(m, dict) and m.get("type") == "text" and isinstance(m.get("text"), str):
            m = {**m, "text": m["text"][:_MAX_TEXT]}
        out.append(m)
    return out


def _inject_quote(
    messages: List[Dict[str, Any]], quote_token: Optional[str]
) -> List[Dict[str, Any]]:
    """给首条 text 消息注入 quoteToken(LINE 仅 text 支持引用)。无 token / 无 text → 原样。"""
    if not quote_token:
        return messages
    out = []
    quoted = False
    for m in messages:
        if not quoted and isinstance(m, dict) and m.get("type") == "text" and "quoteToken" not in m:
            m = {**m, "quoteToken": quote_token}
            quoted = True
        out.append(m)
    return out


def _record_bot(
    line_user_id: Optional[str], tenant_id: Optional[str], messages: List[Dict[str, Any]]
) -> None:
    """记 bot 回复进对话记忆(取首条 text·供大脑多轮上下文)。best-effort。"""
    if not (line_user_id and tenant_id):
        return
    text = next(
        (
            m["text"]
            for m in messages
            if isinstance(m, dict) and m.get("type") == "text" and m.get("text")
        ),
        "",
    )
    if not text:
        return
    try:
        from services.line_binding import line_chat_memory

        line_chat_memory.note(
            line_user_id=line_user_id, tenant_id=str(tenant_id), role="bot", content=text
        )
    except Exception as e:
        logger.warning(f"[line_reply] 对话记忆写入跳过(不阻断): {e}")


def _send(
    messages: List[Dict[str, Any]],
    *,
    reply_token: str = "",
    line_user_id: str = "",
    quote_token: str = "",
    tenant_id: Optional[str] = None,
    record: bool = True,
    via_push: bool = False,
) -> bool:
    msgs = _inject_quote(_truncate(messages), quote_token)
    if via_push:
        ok = line_client.push_messages(line_user_id, msgs)
    else:
        ok = line_client.reply_messages(reply_token, msgs)
    if not ok:
        logger.warning(f"[line_reply] {'push' if via_push else 'reply'} 失败")
    if ok and record:
        _record_bot(line_user_id, tenant_id, msgs)
    return ok


def reply_text_context(
    reply_token: str,
    text: str,
    *,
    quote_token: str = "",
    line_user_id: str = "",
    tenant_id: Optional[str] = None,
    record: bool = True,
) -> bool:
    """replyToken 回纯文字 · 默认带 quoteToken + 记 bot 记忆。"""
    return _send(
        [{"type": "text", "text": str(text)}],
        reply_token=reply_token,
        line_user_id=line_user_id,
        quote_token=quote_token,
        tenant_id=tenant_id,
        record=record,
    )


def reply_messages_context(
    reply_token: str,
    messages: List[Dict[str, Any]],
    *,
    quote_token: str = "",
    line_user_id: str = "",
    tenant_id: Optional[str] = None,
    record: bool = True,
) -> bool:
    """replyToken 回多条消息 · 首条 text 带 quoteToken。"""
    return _send(
        messages,
        reply_token=reply_token,
        line_user_id=line_user_id,
        quote_token=quote_token,
        tenant_id=tenant_id,
        record=record,
    )


def push_text_context(
    line_user_id: str,
    text: str,
    *,
    quote_token: str = "",
    tenant_id: Optional[str] = None,
    record: bool = True,
) -> bool:
    """userId 主动推纯文字(异步结果/通知)· 默认带 quoteToken。"""
    return _send(
        [{"type": "text", "text": str(text)}],
        line_user_id=line_user_id,
        quote_token=quote_token,
        tenant_id=tenant_id,
        record=record,
        via_push=True,
    )


def push_messages_context(
    line_user_id: str,
    messages: List[Dict[str, Any]],
    *,
    quote_token: str = "",
    tenant_id: Optional[str] = None,
    record: bool = True,
) -> bool:
    """userId 主动推多条消息 · 首条 text 带 quoteToken。"""
    return _send(
        messages,
        line_user_id=line_user_id,
        quote_token=quote_token,
        tenant_id=tenant_id,
        record=record,
        via_push=True,
    )
