# -*- coding: utf-8 -*-
"""Agent 轮级审计留痕(agent_turn_logs)——线上排障的回放底座。

对话记忆(line_chat_history)只存文本且 24h 过期,用户投诉"它记错/没记"时无法回放
那一轮模型选了什么工具、拿到什么结果。这里每轮落一行:结局 kind + 工具轨迹 + 耗时 +
trace_id(与 ai_usage 网关日志同号可对上成本)。user_text 截断留存,90 天写时顺清。

crash 落行时打 [agent-alarm] error 标记——prod 日志侧按此聚合/告警(crash 率一目了然)。
record 全程 best-effort:审计绝不许挡对话主路径。
"""

from __future__ import annotations

import json
import logging

logger = logging.getLogger(__name__)

RETENTION_DAYS = 90  # 审计回放窗口;写时顺手清,表不长毛
_TEXT_MAX = 300

_TABLE = """
CREATE TABLE IF NOT EXISTS agent_turn_logs (
    id bigserial PRIMARY KEY,
    tenant_id uuid,
    user_id text,
    line_user_id text,
    trace_id text,
    lang text,
    user_text text NOT NULL DEFAULT '',
    result_kind text NOT NULL,
    tool_trace jsonb NOT NULL DEFAULT '[]'::jsonb,
    elapsed_ms integer,
    created_at timestamptz NOT NULL DEFAULT now()
)
"""

_INDEXES = (
    "CREATE INDEX IF NOT EXISTS ix_agent_turn_logs_tenant "
    "ON agent_turn_logs (tenant_id, created_at DESC)",
    "CREATE INDEX IF NOT EXISTS ix_agent_turn_logs_created ON agent_turn_logs (created_at)",
)


def ensure_table() -> None:
    """幂等建 agent_turn_logs + RLS(startup 调,alembic 0047 留档)。"""
    from core import db
    from core.rls import apply_tenant_rls

    with db.get_cursor(commit=True) as cur:
        cur.execute(_TABLE)
        for ddl in _INDEXES:
            cur.execute(ddl)
        apply_tenant_rls(cur, "agent_turn_logs")


def record(
    *,
    tenant_id,
    user_id,
    line_user_id,
    trace_id,
    lang,
    user_text,
    result_kind,
    tool_trace,
    elapsed_ms,
) -> None:
    """落一行轮审计。best-effort:任何故障只记日志,绝不挡对话。"""
    if result_kind == "crash":
        # 告警口:prod 日志按 [agent-alarm] 聚合(大脑集体降级第一时间可见,不等用户投诉)
        logger.error(
            "[agent-alarm] crash tenant=%s trace=%s elapsed_ms=%s",
            tenant_id,
            trace_id,
            elapsed_ms,
        )
    if not tenant_id:
        return
    try:
        from core import db

        with db.get_cursor_rls(str(tenant_id), commit=True) as cur:
            cur.execute(
                "INSERT INTO agent_turn_logs "
                "(tenant_id, user_id, line_user_id, trace_id, lang, user_text, "
                " result_kind, tool_trace, elapsed_ms) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s, %s::jsonb, %s)",
                (
                    str(tenant_id),
                    str(user_id or "") or None,
                    line_user_id,
                    trace_id,
                    lang,
                    (user_text or "")[:_TEXT_MAX],
                    str(result_kind),
                    json.dumps(list(tool_trace or []), ensure_ascii=False, default=str),
                    elapsed_ms,
                ),
            )
            cur.execute(
                "DELETE FROM agent_turn_logs "
                "WHERE created_at < now() - make_interval(days => %s)",
                (RETENTION_DAYS,),
            )
    except Exception:
        logger.warning("[agent turn_log] record failed", exc_info=True)


def stats(hours: int = 24) -> dict:
    """全租户结局分布(超管排障口:crash/defer/兜底率)。owner 游标跨租户聚合,只读。"""
    from core import db

    with db.get_cursor() as cur:
        cur.execute(
            "SELECT result_kind, count(*) AS n, avg(elapsed_ms)::int AS avg_ms "
            "FROM agent_turn_logs WHERE created_at > now() - make_interval(hours => %s) "
            "GROUP BY result_kind",
            (hours,),
        )
        rows = cur.fetchall()
    by_kind = {r["result_kind"]: {"count": int(r["n"]), "avg_ms": r["avg_ms"]} for r in rows}
    total = sum(v["count"] for v in by_kind.values())
    crash = by_kind.get("crash", {}).get("count", 0)
    return {
        "hours": hours,
        "total": total,
        "by_kind": by_kind,
        "crash_rate": round(crash / total, 4) if total else 0.0,
    }
