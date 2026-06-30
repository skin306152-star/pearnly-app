# -*- coding: utf-8 -*-
"""对话 Agent 插座 ↔ LINE 入口的桥(WP5)。

line_expense.handle_expense_text 在大脑步前调 try_agent_turn:钥匙闸命中则试新 Agent loop,
返回渲染好的回复 = Agent 接管本轮;返回 None = defer(钥匙闸关/未命中/异常/无工具意图),
调用方逐字节落回旧 understand()+_dispatch_agent()。能力只增不减,旧路一行不改。
"""

from __future__ import annotations

import logging
from typing import Optional

logger = logging.getLogger(__name__)


def try_agent_turn(bound_user, text, lang, tid, ws, line_user_id, history) -> Optional[str]:
    """钥匙闸 + 单轮 Agent。命中并被 Agent 接管 → 4 语回复文案;否则 None(交旧路)。"""
    from core import feature_flags

    uid = str(bound_user["id"]) if bound_user.get("id") else None
    if not feature_flags.agent_enabled_for(uid):
        return None
    try:
        from services.agent import agent_i18n, loop
        from services.agent.contracts import AgentContext

        ctx = AgentContext(
            user=bound_user,
            tenant_id=tid,
            workspace_client_id=ws,
            line_user_id=line_user_id,
        )
        key = loop.handle_turn(text, ctx, history=history)
        return agent_i18n.render(key, lang) if key is not None else None
    except Exception:
        # 任何异常一律 defer(铁律:Agent 不许把错误抛给用户);带 uid + 栈便于排障。
        logger.warning("[line agent] turn failed; defer to legacy (uid=%s)", uid, exc_info=True)
        return None
