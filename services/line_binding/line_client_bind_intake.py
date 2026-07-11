# -*- coding: utf-8 -*-
"""客户绑定码 webhook 消费编排(D2-S2)。

从 routes/line_webhook_routes.py 抽出(该文件已顶格 500 行 · 不再塞新分支进去)。
排在既有用户 6 位码判定之后:只读 peek 码归属拿 tenant_id 才问闸(闸关时绝不
touch/消费一次性码,码留给人工重发);闸开且码有效才真消费 + 落联系人 + 回执。
任何异常一律 fail-open 交回调用方既有 bind_invalid 回落(照 take_intent「意图层
故障绝不挡主路」纪律),True 才代表本次消息已处理完、调用方应 return。
"""

from __future__ import annotations

import logging
from typing import Optional

logger = logging.getLogger(__name__)


def try_consume(
    code: str, line_user_id: str, reply_token: str, lang: str, quote_token: Optional[str]
) -> bool:
    try:
        from core import feature_flags
        from services.line_binding import line_client, line_client_contact, line_reply

        peek = line_client_contact.peek_client_bind_code(code)
        if not peek:
            return False
        if not feature_flags.pearnly_ai_client_pool_enabled_for(peek.get("tenant_id")):
            return False
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
