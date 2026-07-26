# -*- coding: utf-8 -*-
"""LINE 卡片动作一次性令牌(防重放 · PO-12 · 涉钱)。

数据卡 postback 动作(确认入账/撤销/丢弃)带一次性 token:发卡时 mint 入库,点击时 consume
原子消费(UPDATE ... WHERE consumed_at IS NULL ...),重复/并发点击只第一次拿到 RETURNING。
token 即能力凭证 → 服务端据它反查目标记录,不信客户端 postback 里的 doc_id(纵深防御)。
隔离=每句 WHERE tenant_id;TTL 默认 72h,过期与已消费分别给友好提示。
prod 无 alembic 钩子 → startup 经 ensure_table() 幂等建表(alembic 0037 留档)。
"""

from __future__ import annotations

import secrets

DEFAULT_TTL_HOURS = 72

_TABLE = """
CREATE TABLE IF NOT EXISTS line_action_nonces (
    token text PRIMARY KEY,
    tenant_id uuid NOT NULL,
    workspace_client_id bigint NOT NULL,
    user_id text NOT NULL DEFAULT '',
    action_ref text NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    expires_at timestamptz NOT NULL,
    consumed_at timestamptz
)
"""

_INDEX = (
    "CREATE INDEX IF NOT EXISTS ix_line_action_nonces_expires " "ON line_action_nonces (expires_at)"
)


def ensure_table() -> None:
    """幂等建 line_action_nonces + RLS(startup 调)。"""
    from core import db
    from core.rls import apply_tenant_rls

    with db.get_cursor(commit=True) as cur:
        cur.execute(_TABLE)
        cur.execute(_INDEX)
        apply_tenant_rls(cur, "line_action_nonces")


def mint(
    cur,
    *,
    tenant_id,
    workspace_client_id,
    action_ref,
    user_id="",
    ttl_hours=DEFAULT_TTL_HOURS,
    ttl_minutes=None,
) -> str:
    """发卡时建一次性 token,返回 urlsafe 串。无 ref → 空串(卡走无 token 链路,不强发)。

    ttl_minutes 给分钟级时效场景(管家写授权卡 5 分钟口径,make_interval 的 hours 参数是
    整数表达不了),给了它就覆盖 ttl_hours;单位名来自闭集,不进 SQL 拼接面。
    """
    if not action_ref:
        return ""
    unit, ttl = ("mins", ttl_minutes) if ttl_minutes is not None else ("hours", ttl_hours)
    token = secrets.token_urlsafe(18)
    cur.execute(
        "INSERT INTO line_action_nonces "
        "(token, tenant_id, workspace_client_id, user_id, action_ref, expires_at) "
        f"VALUES (%s, %s, %s, %s, %s, now() + make_interval({unit} => %s))",
        (
            token,
            tenant_id,
            workspace_client_id,
            str(user_id or ""),
            str(action_ref),
            int(ttl),
        ),
    )
    return token


def consume(cur, *, tenant_id, token, ref_kind=None) -> dict:
    """原子消费一次性 token。

    返回 {status, action_ref, workspace_client_id, user_id}:
      ok       首次有效消费 → 携目标记录(用它,不信客户端 doc_id)
      expired  过了 TTL
      used     已消费过(重放/双击)→ 仍携目标记录,供按真实状态重发当前卡(P1G 验收 2)
      missing  无此 token(伪造/旧卡无 token/类别不符)
    并发双击靠 `UPDATE ... WHERE consumed_at IS NULL` 行锁串行化,只一次命中 RETURNING。

    ref_kind:收窄可消费的令牌类别(action_ref 的 `{"kind": ...}` 前缀)。这张表由
    LINE 数据卡与管家授权卡共用,不带类别过滤的消费会把别的子系统的一次性凭证隔空烧掉;
    类别不符一律按 missing —— 不消费,也不泄漏别家 token 的存在性。值来自调用方常量闭集,
    不进 SQL 拼接面。
    """
    if not token:
        return {"status": "missing"}
    kind_sql = " AND action_ref LIKE %s" if ref_kind else ""
    kind_params = (f'{{"kind": "{ref_kind}"%',) if ref_kind else ()
    cur.execute(
        "UPDATE line_action_nonces SET consumed_at = now() "
        "WHERE token = %s AND tenant_id = %s AND consumed_at IS NULL AND expires_at > now() "
        f"{kind_sql} RETURNING action_ref, workspace_client_id, user_id",
        (token, tenant_id) + kind_params,
    )
    row = cur.fetchone()
    if row:
        return {
            "status": "ok",
            "action_ref": row["action_ref"],
            "workspace_client_id": row["workspace_client_id"],
            "user_id": row["user_id"],
        }
    cur.execute(
        "SELECT consumed_at, action_ref, workspace_client_id, "
        "(expires_at <= now()) AS expired FROM line_action_nonces "
        f"WHERE token = %s AND tenant_id = %s{kind_sql}",
        (token, tenant_id) + kind_params,
    )
    info = cur.fetchone()
    if info is None:
        return {"status": "missing"}
    if info["consumed_at"] is not None:
        return {
            "status": "used",
            "action_ref": info["action_ref"],
            "workspace_client_id": info["workspace_client_id"],
        }
    return {"status": "expired"}


def latest_pending(cur, *, tenant_id, user_id, kind, within_minutes=15):
    """最近铸造、未消费、未过期的指定类动作 token(M3 文本确认通道定位用)。

    只认 within_minutes 内铸的卡:nonce TTL 72h 是防重放口径,文本"确认"是会话语境口径,
    旧卡不该被一句确认字样隔空引爆。无 → None。
    """
    cur.execute(
        "SELECT token FROM line_action_nonces "
        "WHERE tenant_id = %s AND user_id = %s AND consumed_at IS NULL "
        "  AND expires_at > now() AND created_at > now() - make_interval(mins => %s) "
        "  AND action_ref LIKE %s "
        "ORDER BY created_at DESC LIMIT 1",
        (tenant_id, str(user_id or ""), int(within_minutes), f'%"kind": "{kind}"%'),
    )
    row = cur.fetchone()
    return row["token"] if row else None
