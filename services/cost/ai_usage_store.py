# -*- coding: utf-8 -*-
"""AI 网关调用成本落库(ai_usage)· 数据访问层。

唯一写点 = services/ai_gateway/logging.py::log_call —— Agent 对话/LINE 语音/知识库问答/
OCR 全部经网关(run_task + transport 4 形态)的调用都汇到 log_call,这里落库即全覆盖。

与 ocr_cost_log(services/cost/store.py)口径不同、有重叠(OCR 走 multimodal_to_json 也经
本表)—— 两表统计口径不一致,不可直接相加,取数见 routes/admin_cost_routes.py 对应端点。

建表 = 懒加载一次性 ensure(照 services/line_binding/line_anchor_store.py 先例 · prod 无
alembic 自动迁移钩子 · alembic/versions/0060_ai_usage.py 只留档)。写入全量 try/except 吞
异常 —— log_call 是每次网关调用的收尾,这里抛出会连坐已经跑完的 AI 调用主路径。

隐私红线:只落工程元信息(task/provider/model/status/tokens/cost/trace),不落
prompt/LINE 原文/api key —— log_call 传进来的 result 本来就不含原文,这里原样透传。
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

_ensured = False


def ensure_ai_usage_table() -> None:
    """幂等建 ai_usage + RLS。

    tenant_id 允许 NULL(系统级调用,如无租户上下文的启动期自检)。RLS 用纯 tenant 策略
    (core.rls.apply_tenant_rls):tenant_id 有值的行按 tenant 隔离;tenant_id IS NULL 的行,
    在业务连接強制切到 pearnly_app 角色(RLS_ROLE 配置生效)时对任何非 bypass 会话都不可见
    —— policy 谓词 `tenant_id::text = current_setting(...)`,两边都是 NULL 时比较结果非真,
    USING/WITH CHECK 都过不了。这些系统级行只能经 bypass 连接读到,即本模块聚合函数与
    admin 端点(db.get_cursor 默认走 owner 连接,未强制切最小权限角色时天然绕过 RLS)。
    绝大多数环境未启用 RLS_ROLE 强制切角色,此时 NULL 行照常可写可读;ai_usage 域若未来
    被提升为强制隔离,系统级写入需改走显式 bypass 游标,届时另评估。
    """
    from core import db
    from core.rls import apply_tenant_rls

    with db.get_cursor(commit=True) as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS ai_usage (
                id BIGSERIAL PRIMARY KEY,
                tenant_id UUID,
                user_id TEXT,
                task TEXT NOT NULL,
                provider TEXT,
                model TEXT,
                status TEXT NOT NULL,
                error_kind TEXT,
                latency_ms INTEGER,
                input_tokens INTEGER,
                output_tokens INTEGER,
                cost_thb NUMERIC(12, 6) NOT NULL DEFAULT 0,
                trace_id TEXT,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
            """)
        cur.execute(
            "CREATE INDEX IF NOT EXISTS idx_ai_usage_tenant "
            "ON ai_usage(tenant_id, created_at DESC)"
        )
        cur.execute(
            "CREATE INDEX IF NOT EXISTS idx_ai_usage_task ON ai_usage(task, created_at DESC)"
        )
        apply_tenant_rls(cur, "ai_usage")
        logger.info("✅ ai_usage 表已就绪")


def _ensure_once() -> None:
    """首次写入时建表,此后跳过(进程内幂等 flag,同 line_anchor_store 范式)。"""
    global _ensured
    if _ensured:
        return
    ensure_ai_usage_table()
    _ensured = True


def log_ai_usage(
    *,
    tenant_id: Optional[str],
    user_id: Optional[str],
    task: str,
    provider: str,
    model: str,
    status: str,
    error_kind: Optional[str],
    latency_ms: int,
    input_tokens: int,
    output_tokens: int,
    cost_thb: float,
    trace_id: Optional[str],
) -> None:
    """写一行 AI 网关调用成本(同步 · 全量吞异常)。

    调用方 = ai_gateway.logging.log_call,是每次网关调用的收尾;这里任何失败(建表/连接/
    约束)都只 log warning,绝不抛出打断已经跑完的 AI 调用 —— 记账不能连坐主路径。
    """
    try:
        _ensure_once()
        from core import db

        with db.get_cursor_rls(
            tenant_id=str(tenant_id) if tenant_id else None,
            user_id=str(user_id) if user_id else None,
            commit=True,
        ) as cur:
            cur.execute(
                """
                INSERT INTO ai_usage
                (tenant_id, user_id, task, provider, model, status, error_kind,
                 latency_ms, input_tokens, output_tokens, cost_thb, trace_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    str(tenant_id) if tenant_id else None,
                    str(user_id) if user_id else None,
                    task,
                    provider or "",
                    model or "",
                    status,
                    error_kind,
                    int(latency_ms or 0),
                    int(input_tokens or 0),
                    int(output_tokens or 0),
                    round(float(cost_thb or 0), 6),
                    trace_id,
                ),
            )
    except Exception as e:
        logger.warning("log_ai_usage failed (dropped, not fatal): %s", e)


def get_usage_by_task(days: int = 30) -> List[Dict[str, Any]]:
    """按 task 聚合(近 N 天):calls/cost_thb/tokens。超管成本面板只读端点用。"""
    try:
        from core import db

        with db.get_cursor() as cur:
            cur.execute(
                """
                SELECT task,
                       COUNT(*) AS calls,
                       COALESCE(SUM(cost_thb), 0) AS cost_thb,
                       COALESCE(SUM(input_tokens), 0) AS input_tokens,
                       COALESCE(SUM(output_tokens), 0) AS output_tokens
                FROM ai_usage
                WHERE created_at >= NOW() - make_interval(days => %s)
                GROUP BY task
                ORDER BY cost_thb DESC
                """,
                (int(days),),
            )
            return [
                {
                    "task": r["task"],
                    "calls": int(r["calls"]),
                    "cost_thb": float(r["cost_thb"]),
                    "input_tokens": int(r["input_tokens"]),
                    "output_tokens": int(r["output_tokens"]),
                }
                for r in cur.fetchall()
            ]
    except Exception as e:
        logger.error(f"get_usage_by_task failed: {e}")
        return []


def get_usage_daily_trend(days: int = 30) -> List[Dict[str, Any]]:
    """按日成本合计(近 N 天)。超管成本面板只读端点用。"""
    try:
        from core import db

        with db.get_cursor() as cur:
            cur.execute(
                """
                SELECT created_at::date AS day,
                       COALESCE(SUM(cost_thb), 0) AS cost_thb,
                       COUNT(*) AS calls
                FROM ai_usage
                WHERE created_at >= NOW() - make_interval(days => %s)
                GROUP BY day
                ORDER BY day ASC
                """,
                (int(days),),
            )
            return [
                {
                    "day": str(r["day"]),
                    "cost_thb": float(r["cost_thb"]),
                    "calls": int(r["calls"]),
                }
                for r in cur.fetchall()
            ]
    except Exception as e:
        logger.error(f"get_usage_daily_trend failed: {e}")
        return []
