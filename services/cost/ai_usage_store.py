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
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

_ensured = False

# 成本归因列 + 面板索引。ADD COLUMN IF NOT EXISTS / CREATE INDEX IF NOT EXISTS 天然幂等,
# 库里已有(别的进程先建过)照跑不报错。
_ATTRIBUTION_MIGRATIONS = (
    "ALTER TABLE ai_usage ADD COLUMN IF NOT EXISTS entry_point TEXT",
    "ALTER TABLE ai_usage ADD COLUMN IF NOT EXISTS doc_type TEXT",
    "ALTER TABLE ai_usage ADD COLUMN IF NOT EXISTS pages INTEGER",
    # 逐入口成本面板先按时间窗过滤、再按 (entry_point, doc_type) 分组,现有索引都以
    # tenant/task 打头吃不上。前导列必须是 created_at:入口打头时范围条件落不到索引上,
    # 整表还是全扫(2026-08-12 建反了一次,前导列反了等于没建)。
    "CREATE INDEX IF NOT EXISTS idx_ai_usage_created_entry "
    "ON ai_usage(created_at DESC, entry_point)",
    # 建反的旧索引直接拆掉:留着只白占写入开销,面板一条查询也用不上它。
    "DROP INDEX IF EXISTS idx_ai_usage_entry",
)


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
        # 归因三列(2026-08-11 后加 · 建表后 ALTER,同 services/auth/schema.py 范式)。
        # 全可空:旧行没有归因,报表按 NULL 归「未归因」,不回填假值。
        for stmt in _ATTRIBUTION_MIGRATIONS:
            cur.execute(stmt)
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
    entry_point: Optional[str] = None,
    doc_type: Optional[str] = None,
    pages: Optional[int] = None,
) -> bool:
    """写一行 AI 网关调用成本(同步 · 全量吞异常)。返回是否真的落了账。

    调用方 = ai_gateway.logging.log_call,是每次网关调用的收尾;这里任何失败(建表/连接/
    约束)都只 log warning,绝不抛出打断已经跑完的 AI 调用 —— 记账不能连坐主路径。
    返回 False 时调用方要把一次性消费槽的页数还回去(usage_context.restore_pages),
    否则 DB 抖一下这份票的页数分母就永久丢失。
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
                 latency_ms, input_tokens, output_tokens, cost_thb, trace_id,
                 entry_point, doc_type, pages)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
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
                    entry_point or None,
                    doc_type or None,
                    int(pages) if pages else None,
                ),
            )
        return True
    except Exception as e:
        logger.warning("log_ai_usage failed (dropped, not fatal): %s", e)
        return False


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


# 逐入口成本聚合:一条查询出全部分组,NULL 入口的行在 Python 侧归「未归因」——
# 分两条查会让两半的时间窗错开一个执行间隔,合计对不上。
_COST_BY_ENTRY_SQL = """
    SELECT entry_point,
           doc_type,
           COUNT(*) AS calls,
           COALESCE(SUM(pages), 0) AS pages,
           COALESCE(SUM(cost_thb), 0) AS cost_thb,
           COALESCE(SUM(cost_thb), 0) / NULLIF(SUM(pages), 0) AS cost_per_page,
           PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY latency_ms)
               FILTER (WHERE status = 'ok' AND latency_ms IS NOT NULL) AS p50_latency_ms,
           COALESCE(
               ARRAY_AGG(DISTINCT model) FILTER (WHERE COALESCE(model, '') <> ''),
               ARRAY[]::text[]
           ) AS models
    FROM ai_usage
    WHERE created_at >= NOW() - make_interval(days => %s)
    GROUP BY entry_point, doc_type
    ORDER BY SUM(cost_thb) DESC
"""


def get_cost_by_entry_point(days: int = 7) -> Dict[str, Any]:
    """逐入口 × 单据类型的成本聚合(近 N 天)。超管 OCR 引擎面板用。

    每页成本是这张表的重点:定价按 1.5 铢/页走,银行对账单实际更贵,混合均值会把差价藏住。
    页数未知的分组 cost_per_page 返回 None(不是 0)—— 「不知道几页」和「每页 0 铢」是两回事。
    """
    out: Dict[str, Any] = {
        "days": int(days),
        "rows": [],
        "unattributed": {"calls": 0, "cost_thb": 0.0},
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
    try:
        from core import db

        with db.get_cursor() as cur:
            cur.execute(_COST_BY_ENTRY_SQL, (int(days),))
            rows = cur.fetchall()
    except Exception as e:
        logger.error("get_cost_by_entry_point failed: %s", e)
        return out

    for r in rows:
        if not r["entry_point"]:  # 归因列上线前的历史行 + 漏打点的调用点
            out["unattributed"]["calls"] += int(r["calls"])
            out["unattributed"]["cost_thb"] += float(r["cost_thb"])
            continue
        p50 = r["p50_latency_ms"]
        cpp = r["cost_per_page"]
        out["rows"].append(
            {
                "entry_point": r["entry_point"],
                "doc_type": r["doc_type"] or None,
                "calls": int(r["calls"]),
                "pages": int(r["pages"]),
                "cost_thb": round(float(r["cost_thb"]), 6),
                "cost_per_page": round(float(cpp), 6) if cpp is not None else None,
                "p50_latency_ms": int(p50) if p50 is not None else None,
                "models": list(r["models"] or []),
            }
        )
    out["unattributed"]["cost_thb"] = round(out["unattributed"]["cost_thb"], 6)
    return out


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
