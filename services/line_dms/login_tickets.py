# -*- coding: utf-8 -*-
"""Pearnly DMS · 一次性登录票据 DAL。

LINE 端发票据、DMS 门户核销后完成登录。票据一次性、TTL 上限 60 秒。
库内只存 SHA256 哈希(明文不落库 · 库泄露不泄票据);核销走单句
DELETE ... RETURNING —— 过期判断与一次性由 DB 原子完成,并发双花至多一方赢。
门户核销无租户上下文 → owner 连接(与 line_dms_binding_codes 同款)。
"""

from __future__ import annotations

import hashlib
import logging
import secrets
from typing import Optional

logger = logging.getLogger(__name__)

MAX_TICKET_TTL_SECONDS = 60

_TABLE = "line_dms_login_tickets"

# DDL 与 alembic 0102_line_dms_login_tickets 逐字一致(双跑留档 · 改一处必同改另一处)。
_DDL = """
CREATE TABLE IF NOT EXISTS line_dms_login_tickets (
    ticket_hash text PRIMARY KEY,
    tenant_id uuid NOT NULL,
    user_id uuid NOT NULL,
    expires_at timestamptz NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now()
)
"""

# expires_at 索引:核销按 hash 走 PK,索引只服务过期票清扫(WHERE expires_at < now())。
_INDEXES = (
    "CREATE INDEX IF NOT EXISTS idx_line_dms_login_tickets_expires_at "
    "ON line_dms_login_tickets (expires_at)",
)


def _ticket_hash(ticket: str) -> str:
    return hashlib.sha256(ticket.encode("utf-8")).hexdigest()


def ensure_table() -> None:
    """幂等建表 + 索引 + apply_tenant_rls(启动 ensure + 首用自愈调)。"""
    from core import db
    from core.rls import apply_tenant_rls

    with db.get_cursor(commit=True) as cur:
        cur.execute(_DDL)
        for stmt in _INDEXES:
            cur.execute(stmt)
        apply_tenant_rls(cur, _TABLE)


def _with_heal(fn):
    """表不存在(新库/回滚后)→ 建表重试一次;其余异常向上抛由 _dal 兜底。"""
    try:
        return fn()
    except Exception as e:
        if _TABLE not in str(e):
            raise
        ensure_table()
        return fn()


def _dal(label: str, default):
    """DAL 兜底:_with_heal 跑 fn,异常记 error 返 default(失败软降级不抛 · 核销返 None 即 fail-closed)。"""

    def run(fn):
        try:
            return _with_heal(fn)
        except Exception as e:
            logger.error(f"[line_dms] {label} failed: {e}")
            return default

    return run


def issue_login_ticket(
    tenant_id, user_id, ttl_seconds: int = MAX_TICKET_TTL_SECONDS
) -> Optional[dict]:
    """为 (tenant, user) 发一次性登录票据:明文只返调用方一次,库里只有 SHA256 哈希。

    TTL 夹到 [0, MAX_TICKET_TTL_SECONDS](60s 上限)。返回 {"ticket", "expires_at"(iso)};
    落库失败 → None。
    """
    from core import db

    ttl = max(0, min(int(ttl_seconds), MAX_TICKET_TTL_SECONDS))
    ticket = secrets.token_urlsafe(32)

    def _run():
        with db.get_cursor(commit=True) as cur:
            cur.execute("DELETE FROM line_dms_login_tickets WHERE expires_at <= now()")
            cur.execute(
                "INSERT INTO line_dms_login_tickets "
                "(ticket_hash, tenant_id, user_id, expires_at) "
                "VALUES (%s, %s, %s, now() + (%s * interval '1 second')) "
                "RETURNING ticket_hash, expires_at",
                (_ticket_hash(ticket), str(tenant_id), str(user_id), ttl),
            )
            return cur.fetchone()

    row = _dal("issue_login_ticket", None)(_run)
    if not row:
        return None
    return {"ticket": ticket, "expires_at": row["expires_at"].isoformat()}


def consume_login_ticket(ticket: str) -> Optional[dict]:
    """原子核销登录票据 → {"tenant_id", "user_id"};无效/过期/已核销 → None。

    单句 DELETE ... RETURNING:过期判断与一次性在 DB 层一步完成。
    按哈希查,明文永不入库、永不出现在响应里。
    """
    from core import db

    ticket = (ticket or "").strip()
    if not ticket:
        return None

    def _run():
        with db.get_cursor(commit=True) as cur:
            cur.execute(
                "DELETE FROM line_dms_login_tickets "
                "WHERE ticket_hash = %s AND expires_at > now() "
                "RETURNING tenant_id, user_id",
                (_ticket_hash(ticket),),
            )
            return cur.fetchone()

    row = _dal("consume_login_ticket", None)(_run)
    if not row:
        return None
    return {"tenant_id": str(row["tenant_id"]), "user_id": str(row["user_id"])}
