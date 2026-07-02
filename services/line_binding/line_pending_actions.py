# -*- coding: utf-8 -*-
"""LINE 泛用确认检查点(M3 状态机设计 §3 · 首个消费者=DMS 建客户)。

"复述完等用户答复"的持久化检查点:复述后存这里,用户回"确认/取消"时 confirm_machine
原子取走(take = DELETE RETURNING,单发单用)分发执行。与 line_pending_intents 同范式:
一人(tenant+line_user)只留一条活动检查点——新复述覆盖旧的;TTL 默认 15 分钟,过期
即失效(回别的话不消费,静置到期)。action 形如 {"tool": "dms_push", ...payload}。
"""

from __future__ import annotations

import json
import logging
from typing import Optional

logger = logging.getLogger(__name__)

DEFAULT_TTL_MINUTES = 15

_TABLE = """
CREATE TABLE IF NOT EXISTS line_pending_actions (
    tenant_id uuid NOT NULL,
    line_user_id text NOT NULL,
    action jsonb NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    expires_at timestamptz NOT NULL,
    PRIMARY KEY (tenant_id, line_user_id)
)
"""


def ensure_table() -> None:
    """幂等建 line_pending_actions + RLS(首用自愈调)。"""
    from core import db
    from core.rls import apply_tenant_rls

    with db.get_cursor(commit=True) as cur:
        cur.execute(_TABLE)
        apply_tenant_rls(cur, "line_pending_actions")


def _with_heal(fn):
    """表不存在(新库/回滚后)→ 建表重试一次;其余异常向上抛由调用方 fail-safe。"""
    try:
        return fn()
    except Exception as e:
        if "line_pending_actions" not in str(e):
            raise
        ensure_table()
        return fn()


def set_action(tenant_id, line_user_id, action: dict, *, ttl_minutes=None) -> None:
    """存/覆盖该用户的活动检查点(upsert:新复述以最新为准)。"""
    from core import db

    ttl = int(ttl_minutes or DEFAULT_TTL_MINUTES)

    def _run():
        with db.get_cursor_rls(str(tenant_id), commit=True) as cur:
            cur.execute(
                "INSERT INTO line_pending_actions "
                "(tenant_id, line_user_id, action, expires_at) "
                "VALUES (%s, %s, %s::jsonb, now() + make_interval(mins => %s)) "
                "ON CONFLICT (tenant_id, line_user_id) DO UPDATE "
                "SET action = EXCLUDED.action, created_at = now(), "
                "    expires_at = EXCLUDED.expires_at",
                (
                    str(tenant_id),
                    str(line_user_id),
                    json.dumps(action or {}, ensure_ascii=False),
                    ttl,
                ),
            )

    _with_heal(_run)


def take_action(tenant_id, line_user_id) -> Optional[dict]:
    """原子取走并删除(单发单用):过期行同删不返。无 → None(交下一级 resume 通道)。"""
    from core import db

    def _run():
        with db.get_cursor_rls(str(tenant_id), commit=True) as cur:
            cur.execute(
                "DELETE FROM line_pending_actions "
                "WHERE tenant_id = %s AND line_user_id = %s "
                "RETURNING action, (expires_at > now()) AS alive",
                (str(tenant_id), str(line_user_id)),
            )
            row = cur.fetchone()
        if not row or not row.get("alive"):
            return None
        action = row.get("action")
        return action if isinstance(action, dict) else json.loads(action or "{}")

    try:
        return _with_heal(_run)
    except Exception:
        logger.warning("[line_actions] take failed; resume falls through", exc_info=True)
        return None  # 检查点层故障不许挡正常消息
