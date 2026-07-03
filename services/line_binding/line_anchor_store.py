# -*- coding: utf-8 -*-
"""跨轮对话锚点(anchors)存取 —— 「把刚才那张推进 ERP」的"刚才"记在这里。

每用户单行 upsert(last-write-wins),存最近一轮对话碰过的对象 id
(如 last_history_id);TTL 45 分钟,过期即失效不粘住后续对话。
锚点只是"候选提示":消费方(executor._locate_doc)读时必复核对象仍可见,
绝不盲信。存取任何故障一律吞掉退现状 —— 锚点层不许挡对话主路。
建表照 line_pending_intents 范式(prod 无 alembic 钩子 → 首用 ensure 幂等自愈)。
"""

from __future__ import annotations

import json
import logging

logger = logging.getLogger(__name__)

DEFAULT_TTL_MINUTES = 45

_TABLE = """
CREATE TABLE IF NOT EXISTS line_agent_anchors (
    tenant_id uuid NOT NULL,
    line_user_id text NOT NULL,
    anchors jsonb NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    expires_at timestamptz NOT NULL,
    PRIMARY KEY (tenant_id, line_user_id)
)
"""


def ensure_table() -> None:
    """幂等建 line_agent_anchors + RLS(首用自愈调)。"""
    from core import db
    from core.rls import apply_tenant_rls

    with db.get_cursor(commit=True) as cur:
        cur.execute(_TABLE)
        apply_tenant_rls(cur, "line_agent_anchors")


def _with_heal(fn):
    """表不存在(新库/回滚后)→ 建表重试一次;其余异常向上抛由调用方吞。"""
    try:
        return fn()
    except Exception as e:
        if "line_agent_anchors" not in str(e):
            raise
        ensure_table()
        return fn()


def get_anchors(tenant_id, line_user_id) -> dict:
    """读该用户的活动锚点。无/过期/任何故障 → {}(当没有,现状不变)。"""
    from core import db

    def _run():
        with db.get_cursor_rls(str(tenant_id)) as cur:
            cur.execute(
                "SELECT anchors FROM line_agent_anchors "
                "WHERE tenant_id = %s AND line_user_id = %s AND expires_at > now()",
                (str(tenant_id), str(line_user_id)),
            )
            row = cur.fetchone()
        if not row:
            return {}
        anchors = row.get("anchors")
        return anchors if isinstance(anchors, dict) else json.loads(anchors or "{}")

    try:
        return _with_heal(_run)
    except Exception:
        logger.warning("[line_anchor] read failed; treat as none", exc_info=True)
        return {}


def set_anchors(tenant_id, line_user_id, anchors: dict, *, ttl_minutes=None) -> None:
    """存/覆盖该用户的锚点(upsert 刷新 TTL)。故障吞掉 —— 存不上只是下轮少个锚。"""
    from core import db

    ttl = int(ttl_minutes or DEFAULT_TTL_MINUTES)

    def _run():
        with db.get_cursor_rls(str(tenant_id), commit=True) as cur:
            cur.execute(
                "INSERT INTO line_agent_anchors "
                "(tenant_id, line_user_id, anchors, expires_at) "
                "VALUES (%s, %s, %s::jsonb, now() + make_interval(mins => %s)) "
                "ON CONFLICT (tenant_id, line_user_id) DO UPDATE "
                "SET anchors = EXCLUDED.anchors, created_at = now(), "
                "    expires_at = EXCLUDED.expires_at",
                (
                    str(tenant_id),
                    str(line_user_id),
                    json.dumps(anchors or {}, ensure_ascii=False),
                    ttl,
                ),
            )

    try:
        _with_heal(_run)
    except Exception:
        logger.warning("[line_anchor] write failed; dropped", exc_info=True)
