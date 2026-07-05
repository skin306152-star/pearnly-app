# -*- coding: utf-8 -*-
"""Agent 轮级审计留痕(agent_turn_logs)——线上排障的回放底座。

对话记忆(line_chat_history)只存文本且 24h 过期,用户投诉"它记错/没记"时无法回放
那一轮模型选了什么工具、拿到什么结果。这里每轮落一行:结局 kind + 工具轨迹 + 耗时 +
trace_id(与 ai_usage 网关日志同号可对上成本)。user_text 截断留存,90 天写时顺清。

degraded/intent(W0 观测):兜底回答混在 reply 里量不出"答非所问率",工具轨迹反推不出
稳定意图分布 → 落库时直接落两列。degraded 由 loop 标在 ctx 上(grounded_fb=拿工具结果
拼的兜底句 / card_text_dropped=卡后跟进被护栏吞 / card_fail=卡后大脑失控),intent 从
工具轨迹派生(零 LLM 成本)。

crash 落行时打 [agent-alarm] error 标记——prod 日志侧按此聚合/告警(crash 率一目了然)。
record 全程 best-effort:审计绝不许挡对话主路径。
"""

from __future__ import annotations

import json
import logging
import random

logger = logging.getLogger(__name__)

RETENTION_DAYS = 90  # 审计回放窗口;采样清老行,表不长毛
_CLEAN_PROB = 0.02  # 清理采样率:90d 保留意味着绝大多数轮删 0 行,别每轮都跑
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
    degraded text,
    intent text,
    created_at timestamptz NOT NULL DEFAULT now()
)
"""

# 存量表补列(prod 无 alembic 钩子,靠启动 ensure;alembic 0051 留档)
_ALTERS = (
    "ALTER TABLE agent_turn_logs ADD COLUMN IF NOT EXISTS degraded text",
    "ALTER TABLE agent_turn_logs ADD COLUMN IF NOT EXISTS intent text",
)

_INDEXES = (
    "CREATE INDEX IF NOT EXISTS ix_agent_turn_logs_tenant "
    "ON agent_turn_logs (tenant_id, created_at DESC)",
    "CREATE INDEX IF NOT EXISTS ix_agent_turn_logs_created ON agent_turn_logs (created_at)",
)

# 工具名 → 意图组。轨迹里第一个命中的工具定调;confirm_resume/recon_intake_text 是
# bridge 短路轮的伪工具名。新工具不进表也不炸——落到 result_kind 派生的粗档。
_INTENT_BY_TOOL = {
    "record_expense": "record",
    "record_multi": "record",
    "undo_entry": "edit",
    "edit_entry": "edit",
    "push_to_erp": "push",
    "push_status": "push",
    "recon_overview": "recon",
    "recon_detail": "recon",
    "recon_intake_start": "recon",
    "recon_intake_text": "recon",
    "confirm_resume": "confirm",
    "plan_incoming_doc": "plan",
    "list_workspaces": "workspace",
    "switch_workspace": "workspace",
    "list_history": "query",
    "history_summary": "query",
    "balance": "query",
    "usage_this_month": "query",
    "list_notifications": "query",
    "my_plan": "query",
    "rd_lookup": "query",
}

_INTENT_BY_KIND = {"defer_record": "record", "defer_edit": "edit", "reply": "chat"}


def derive_intent(result_kind, tool_trace) -> str:
    """轮意图(观测口径,非路由依据):有工具看第一个命中工具,纯文本轮按结局粗分。"""
    for t in tool_trace or []:
        name = (t or {}).get("tool")
        if name in _INTENT_BY_TOOL:
            return _INTENT_BY_TOOL[name]
    return _INTENT_BY_KIND.get(str(result_kind), str(result_kind))


def ensure_table() -> None:
    """幂等建 agent_turn_logs + 补列 + RLS(startup 调,alembic 0047/0051 留档)。"""
    from core import db
    from core.rls import apply_tenant_rls

    with db.get_cursor(commit=True) as cur:
        cur.execute(_TABLE)
        for ddl in _ALTERS + _INDEXES:
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
    degraded="",
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
                " result_kind, tool_trace, elapsed_ms, degraded, intent) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s, %s::jsonb, %s, %s, %s)",
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
                    str(degraded or "") or None,
                    derive_intent(result_kind, tool_trace),
                ),
            )
            if random.random() < _CLEAN_PROB:
                cur.execute(
                    "DELETE FROM agent_turn_logs "
                    "WHERE created_at < now() - make_interval(days => %s)",
                    (RETENTION_DAYS,),
                )
    except Exception:
        logger.warning("[agent turn_log] record failed", exc_info=True)


def stats(hours: int = 24) -> dict:
    """全租户健康聚合(超管排障口:crash/兜底率/意图分布)。owner 游标跨租户,只读。"""
    from core import db

    with db.get_cursor() as cur:
        cur.execute(
            "SELECT result_kind, intent, degraded, count(*) AS n, avg(elapsed_ms)::int AS avg_ms "
            "FROM agent_turn_logs WHERE created_at > now() - make_interval(hours => %s) "
            "GROUP BY result_kind, intent, degraded",
            (hours,),
        )
        rows = cur.fetchall()
    by_kind: dict = {}
    by_intent: dict = {}
    by_degraded: dict = {}
    total = 0
    for r in rows:
        n = int(r["n"])
        total += n
        k = by_kind.setdefault(r["result_kind"], {"count": 0, "ms_sum": 0})
        k["count"] += n
        k["ms_sum"] += n * int(r["avg_ms"] or 0)
        intent = r.get("intent") or "unknown"
        by_intent[intent] = by_intent.get(intent, 0) + n
        deg = r.get("degraded")
        if deg:
            by_degraded[deg] = by_degraded.get(deg, 0) + n
    for v in by_kind.values():
        v["avg_ms"] = round(v.pop("ms_sum") / v["count"]) if v["count"] else None
    crash = by_kind.get("crash", {}).get("count", 0)
    degraded_n = sum(by_degraded.values())
    return {
        "hours": hours,
        "total": total,
        "by_kind": by_kind,
        "by_intent": by_intent,
        "by_degraded": by_degraded,
        "crash_rate": round(crash / total, 4) if total else 0.0,
        "degraded_rate": round(degraded_n / total, 4) if total else 0.0,
    }
