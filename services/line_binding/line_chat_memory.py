# -*- coding: utf-8 -*-
"""LINE 短期对话记忆(滚动窗口 · 喂大脑上下文 · PO-15)。

存每个 LINE 用户最近若干条消息(user/bot),每次调大脑(line_agent.understand)时取最近 N 条
(24h 内)作上下文喂 Gemini → 多轮连贯(「改这笔/那个分类」)+ 接得住「上条为啥失败」。
轻量:一张小表,写时顺手清 24h 前;读 LIMIT N。note/recent 各自带事务、best-effort,
绝不阻断主路径。prod 无 alembic 钩子 → startup 经 ensure_table() 幂等建表(alembic 0038 留档)。
"""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

WINDOW = 8
TTL_HOURS = 24
_MAX_LEN = 500

_TABLE = """
CREATE TABLE IF NOT EXISTS line_chat_history (
    id bigserial PRIMARY KEY,
    line_user_id text NOT NULL,
    tenant_id uuid NOT NULL,
    role text NOT NULL,
    content text NOT NULL DEFAULT '',
    created_at timestamptz NOT NULL DEFAULT now()
)
"""

_INDEX = (
    "CREATE INDEX IF NOT EXISTS ix_line_chat_history_user "
    "ON line_chat_history (line_user_id, created_at DESC)"
)


def ensure_table() -> None:
    """幂等建 line_chat_history + RLS(startup 调)。"""
    from core import db
    from core.rls import apply_tenant_rls

    with db.get_cursor(commit=True) as cur:
        cur.execute(_TABLE)
        cur.execute(_INDEX)
        apply_tenant_rls(cur, "line_chat_history")


def note(*, line_user_id, tenant_id, role, content) -> None:
    """记一条对话(role ∈ user|bot)。自带事务 + 写后清 24h 前;best-effort,失败不抛。"""
    text = (content or "").strip()
    if not text or role not in ("user", "bot") or not line_user_id or not tenant_id:
        return
    try:
        from core import db

        with db.get_cursor_rls(str(tenant_id), commit=True) as cur:
            cur.execute(
                "INSERT INTO line_chat_history (line_user_id, tenant_id, role, content) "
                "VALUES (%s, %s, %s, %s)",
                (line_user_id, str(tenant_id), role, text[:_MAX_LEN]),
            )
            cur.execute(
                "DELETE FROM line_chat_history WHERE line_user_id = %s AND tenant_id = %s "
                "AND created_at < now() - make_interval(hours => %s)",
                (line_user_id, str(tenant_id), TTL_HOURS),
            )
    except Exception as e:  # noqa: BLE001
        logger.warning("[chat memory] note failed: %s", str(e)[:120])


def recent(*, line_user_id, tenant_id, limit=WINDOW, hours=TTL_HOURS) -> list:
    """取最近 limit 条(hours 内)· 时间正序 [{role, content}]。先取再记当前条 → 不含当前。失败 → []。"""
    if not line_user_id or not tenant_id:
        return []
    try:
        from core import db

        with db.get_cursor_rls(str(tenant_id)) as cur:
            cur.execute(
                "SELECT role, content FROM line_chat_history "
                "WHERE line_user_id = %s AND tenant_id = %s "
                "AND created_at > now() - make_interval(hours => %s) "
                "ORDER BY created_at DESC LIMIT %s",
                (line_user_id, str(tenant_id), hours, limit),
            )
            rows = cur.fetchall()
        return [{"role": r["role"], "content": r["content"]} for r in reversed(rows)]
    except Exception as e:  # noqa: BLE001
        logger.warning("[chat memory] recent failed: %s", str(e)[:120])
        return []
