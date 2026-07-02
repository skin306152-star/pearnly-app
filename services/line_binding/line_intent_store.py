# -*- coding: utf-8 -*-
"""LINE 待决图片意图(LI-2)—— "话先图后"的跨消息接力。

用户先说目的("ใบต่อไปส่งเข้า ERP เลย ไม่ต้องบันทึก")再发图:目的存这里,图到时
line_image_route 原子取走(take = DELETE RETURNING,单发单用)执行对应终端。
一人(tenant+line_user)只留一条活动意图——新意图覆盖旧的(用户改主意=以最新为准);
TTL 默认 15 分钟,过期即失效回默认路,不粘住之后的正常发图。
建表照 line_action_nonce 范式(prod 无 alembic 钩子 → 首用 ensure 幂等自愈)。
"""

from __future__ import annotations

import json
import logging
from typing import Optional

logger = logging.getLogger(__name__)

DEFAULT_TTL_MINUTES = 15

_TABLE = """
CREATE TABLE IF NOT EXISTS line_pending_intents (
    tenant_id uuid NOT NULL,
    line_user_id text NOT NULL,
    workspace_client_id bigint,
    intent jsonb NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    expires_at timestamptz NOT NULL,
    PRIMARY KEY (tenant_id, line_user_id)
)
"""


def ensure_table() -> None:
    """幂等建 line_pending_intents + RLS(首用自愈调)。"""
    from core import db
    from core.rls import apply_tenant_rls

    with db.get_cursor(commit=True) as cur:
        cur.execute(_TABLE)
        apply_tenant_rls(cur, "line_pending_intents")


def _with_heal(fn):
    """表不存在(新库/回滚后)→ 建表重试一次;其余异常向上抛由调用方 fail-safe。"""
    try:
        return fn()
    except Exception as e:
        if "line_pending_intents" not in str(e):
            raise
        ensure_table()
        return fn()


def set_intent(
    tenant_id, line_user_id, intent: dict, *, workspace_client_id=None, ttl_minutes=None
) -> None:
    """存/覆盖该用户的活动意图(upsert:改主意以最新为准)。"""
    from core import db

    ttl = int(ttl_minutes or DEFAULT_TTL_MINUTES)

    def _run():
        with db.get_cursor_rls(str(tenant_id), commit=True) as cur:
            cur.execute(
                "INSERT INTO line_pending_intents "
                "(tenant_id, line_user_id, workspace_client_id, intent, expires_at) "
                "VALUES (%s, %s, %s, %s::jsonb, now() + make_interval(mins => %s)) "
                "ON CONFLICT (tenant_id, line_user_id) DO UPDATE "
                "SET intent = EXCLUDED.intent, workspace_client_id = EXCLUDED.workspace_client_id, "
                "    created_at = now(), expires_at = EXCLUDED.expires_at",
                (
                    str(tenant_id),
                    str(line_user_id),
                    workspace_client_id,
                    json.dumps(intent or {}, ensure_ascii=False),
                    ttl,
                ),
            )

    _with_heal(_run)


def peek_intent(tenant_id, line_user_id) -> bool:
    """有未过期意图?只看不取(缓存快路让位判断用)。任何故障 → False = 快路照旧。"""
    from core import db

    def _run():
        with db.get_cursor_rls(str(tenant_id)) as cur:
            cur.execute(
                "SELECT 1 FROM line_pending_intents "
                "WHERE tenant_id = %s AND line_user_id = %s AND expires_at > now()",
                (str(tenant_id), str(line_user_id)),
            )
            return cur.fetchone() is not None

    try:
        return bool(_with_heal(_run))
    except Exception:
        logger.warning("[line_intent] peek failed; treat as none", exc_info=True)
        return False


def read_intent(tenant_id, line_user_id) -> Optional[dict]:
    """读而不取(DMS 绕过点看意图内容判断是否接管;take 仍只在真正消费方)。
    故障 → None = 当没有意图,绝不挡图片主路。"""
    from core import db

    def _run():
        with db.get_cursor_rls(str(tenant_id)) as cur:
            cur.execute(
                "SELECT intent FROM line_pending_intents "
                "WHERE tenant_id = %s AND line_user_id = %s AND expires_at > now()",
                (str(tenant_id), str(line_user_id)),
            )
            row = cur.fetchone()
        if not row:
            return None
        intent = row.get("intent")
        return intent if isinstance(intent, dict) else json.loads(intent or "{}")

    try:
        return _with_heal(_run)
    except Exception:
        logger.warning("[line_intent] read failed; treat as none", exc_info=True)
        return None


def take_intent(tenant_id, line_user_id) -> Optional[dict]:
    """原子取走并删除(单发单用):过期行同删不返。无 → None(走默认路)。"""
    from core import db

    def _run():
        with db.get_cursor_rls(str(tenant_id), commit=True) as cur:
            cur.execute(
                "DELETE FROM line_pending_intents "
                "WHERE tenant_id = %s AND line_user_id = %s "
                "RETURNING intent, (expires_at > now()) AS alive",
                (str(tenant_id), str(line_user_id)),
            )
            row = cur.fetchone()
        if not row or not row.get("alive"):
            return None
        intent = row.get("intent")
        return intent if isinstance(intent, dict) else json.loads(intent or "{}")

    try:
        return _with_heal(_run)
    except Exception:
        logger.warning("[line_intent] take failed; fall back to default route", exc_info=True)
        return None  # 意图层任何故障都不许挡记账主路
