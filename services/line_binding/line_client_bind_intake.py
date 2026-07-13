# -*- coding: utf-8 -*-
"""客户绑定码 webhook 消费编排(D2-S2)。

从 routes/line_webhook_routes.py 抽出(该文件已顶格 500 行 · 不再塞新分支进去)。
排在既有用户 6 位码判定之后:只读 peek 码归属拿 tenant_id 才问闸(闸关时绝不
touch/消费一次性码,码留给人工重发);闸开且码有效才真消费 + 落联系人 + 回执。
任何异常一律 fail-open 交回调用方既有 bind_invalid 回落(照 take_intent「意图层
故障绝不挡主路」纪律),True 才代表本次消息已处理完、调用方应 return。

LN-1 群形态:码发生在群里(group_id 在场)且 pearnly_ai_line_intake 闸开 → 改绑
groupId(一群一客户);闸关时群里发码仍走单聊 contact 现状,逐字节不变。
"""

from __future__ import annotations

import logging
from typing import Optional

logger = logging.getLogger(__name__)


def try_consume(
    code: str,
    line_user_id: str,
    reply_token: str,
    lang: str,
    quote_token: Optional[str],
    *,
    group_id: Optional[str] = None,
) -> bool:
    try:
        from core import feature_flags
        from services.line_binding import line_client, line_client_contact, line_reply

        peek = line_client_contact.peek_client_bind_code(code)
        if not peek:
            return False
        if not feature_flags.pearnly_ai_client_pool_enabled_for(peek.get("tenant_id")):
            return False
        # LN-1 群绑定形态:码发生在群里且收料闸开 → groupId 绑客户;闸关走下方单聊
        # 现状(把发码成员绑成 contact),逐字节不变。
        if group_id and feature_flags.pearnly_ai_line_intake_enabled_for(peek.get("tenant_id")):
            return _consume_into_group(
                peek, code, group_id, line_user_id, reply_token, lang, quote_token
            )
        consumed = line_client_contact.consume_client_bind_code(code)
        if not consumed:
            return False
        profile = line_client.get_user_profile(line_user_id) or {}
        bound = line_client_contact.bind_contact(
            consumed["tenant_id"],
            consumed["workspace_client_id"],
            line_user_id,
            display_name=profile.get("displayName"),
        )
        if not bound:
            return False
        line_reply.reply_text_context(
            reply_token,
            line_client_contact.client_bound_text(lang),
            quote_token=quote_token or "",
            line_user_id=line_user_id,
            tenant_id=consumed["tenant_id"],
        )
        return True
    except Exception:
        logger.warning("[line_client_bind_intake] 客户绑定码分支异常 · 回落原路", exc_info=True)
        return False


def _consume_into_group(
    peek: dict,
    code: str,
    group_id: str,
    line_user_id: str,
    reply_token: str,
    lang: str,
    quote_token: Optional[str],
) -> bool:
    """群里发码 → groupId 绑客户(LN-1 双形态)。一群一客户:已属别家 → 四语拒绝且不
    消费原码(码留给正确的新群再用);消费竞态输了 → False 交回 bind_invalid 现状。"""
    from services.line_binding import line_client_contact, line_client_group, line_intake_store
    from services.line_binding import line_reply

    tenant_id = str(peek["tenant_id"])
    existing = line_client_group.get_group(group_id)
    conflict = existing and (
        str(existing["tenant_id"]) != tenant_id
        or existing["workspace_client_id"] != peek["workspace_client_id"]
    )
    if not conflict:
        consumed = line_client_contact.consume_client_bind_code(code)
        if not consumed:
            return False
        bound = line_client_group.bind_group(
            consumed["tenant_id"],
            consumed["workspace_client_id"],
            group_id,
            bound_by=line_user_id,
        )
        if bound is None:
            return False
        # 预检后仍 conflict = 两码同刻竞绑同群,输方走拒绝(码已耗,PK 竞态窗口极窄,
        # 诚实拒绝优于双绑)。
        conflict = bound == "conflict"
    if conflict:
        text = line_client_group.group_conflict_text(lang)
    else:
        name = line_intake_store.client_display_name(tenant_id, peek["workspace_client_id"])
        text = line_client_group.group_bound_text(lang, name or f"#{peek['workspace_client_id']}")
    line_reply.reply_text_context(
        reply_token,
        text,
        quote_token=quote_token or "",
        line_user_id=line_user_id,
        tenant_id=tenant_id,
    )
    return True
