# -*- coding: utf-8 -*-
"""成本追踪(ocr_cost_log)· 数据访问层

从 db.py 抽出(REFACTOR-B2 · 纯搬家 · 0 逻辑改)。
每次识别完成写一条成本记录 + 管理员成本面板的只读聚合
(KPI / 按用户分组 / 每日趋势 / 每日×引擎堆叠)。纯成本记账 · 不涉任何扣费逻辑。
db.py 文件尾 re-export 回本命名空间 · 所有 `db.xxx()` 调用点不变。
"""

import logging
from typing import Optional, Dict, Any, List

from core import db

logger = logging.getLogger(__name__)


def ensure_ocr_cost_log_table():
    """启动时建表 · 幂等 · v108.2 修 history_id 类型 BIGINT → TEXT(ocr_history.id 是 UUID)"""
    try:
        with db.get_cursor(commit=True) as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS ocr_cost_log (
                    id BIGSERIAL PRIMARY KEY,
                    user_id UUID NOT NULL,
                    tenant_id UUID,
                    history_id TEXT,
                    engine TEXT NOT NULL DEFAULT 'gemini',
                    pages INTEGER NOT NULL DEFAULT 1,
                    input_tokens INTEGER DEFAULT 0,
                    output_tokens INTEGER DEFAULT 0,
                    cost_thb NUMERIC(10, 4) NOT NULL DEFAULT 0,
                    elapsed_ms INTEGER DEFAULT 0,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                );
                CREATE INDEX IF NOT EXISTS idx_cost_log_user ON ocr_cost_log(user_id, created_at DESC);
                CREATE INDEX IF NOT EXISTS idx_cost_log_created ON ocr_cost_log(created_at DESC);
                CREATE INDEX IF NOT EXISTS idx_cost_log_tenant ON ocr_cost_log(tenant_id, created_at DESC);
            """)
            # v108.2 · 已建表的迁移:把 history_id 从 BIGINT 改 TEXT
            try:
                cur.execute("""
                    DO $$
                    BEGIN
                        IF EXISTS (
                            SELECT 1 FROM information_schema.columns
                            WHERE table_name = 'ocr_cost_log'
                              AND column_name = 'history_id'
                              AND data_type = 'bigint'
                        ) THEN
                            ALTER TABLE ocr_cost_log ALTER COLUMN history_id TYPE TEXT USING history_id::TEXT;
                        END IF;
                    END $$;
                """)
            except Exception as _me:
                logger.warning(f"ocr_cost_log.history_id 类型迁移失败(不致命): {_me}")
            logger.info("✅ ocr_cost_log 表已就绪")
    except Exception as e:
        logger.error(f"ensure_ocr_cost_log_table failed: {e}")


def log_ocr_cost(
    user_id: str,
    tenant_id: Optional[str],
    history_id: Optional[Any],  # v108.2 · 接受 str/UUID/int 都可
    engine: str,
    pages: int,
    input_tokens: int,
    output_tokens: int,
    cost_thb: float,
    elapsed_ms: int,
) -> bool:
    """每次识别完写一条成本记录"""
    try:
        with db.get_cursor(commit=True) as cur:
            cur.execute(
                """
                INSERT INTO ocr_cost_log
                (user_id, tenant_id, history_id, engine, pages,
                 input_tokens, output_tokens, cost_thb, elapsed_ms)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """,
                (
                    str(user_id),
                    str(tenant_id) if tenant_id else None,
                    str(history_id) if history_id is not None else None,  # v108.2 · 强制转 str
                    engine,
                    pages,
                    input_tokens,
                    output_tokens,
                    round(float(cost_thb), 4),
                    elapsed_ms,
                ),
            )
            new_id = cur.fetchone()["id"]
            logger.info(
                f"  ✅ ocr_cost_log 写入 id={new_id} user={user_id[:8]} engine={engine} cost=฿{cost_thb:.4f}"
            )
        return True
    except Exception as e:
        import traceback

        logger.error(f"  ❌ log_ocr_cost FAILED: {e}\n{traceback.format_exc()}")
        return False


def get_cost_overview() -> Dict[str, Any]:
    """成本面板 · 顶部 KPI · 今日 / 本月 / 总计"""
    try:
        with db.get_cursor() as cur:
            cur.execute("""
                SELECT
                    COALESCE(SUM(CASE WHEN created_at::date = CURRENT_DATE THEN cost_thb END), 0) AS today_cost,
                    COALESCE(SUM(CASE WHEN created_at::date = CURRENT_DATE THEN pages END), 0) AS today_pages,
                    COALESCE(COUNT(CASE WHEN created_at::date = CURRENT_DATE THEN 1 END), 0) AS today_invoices,
                    COALESCE(SUM(CASE WHEN date_trunc('month', created_at) = date_trunc('month', NOW()) THEN cost_thb END), 0) AS month_cost,
                    COALESCE(SUM(CASE WHEN date_trunc('month', created_at) = date_trunc('month', NOW()) THEN pages END), 0) AS month_pages,
                    COALESCE(COUNT(CASE WHEN date_trunc('month', created_at) = date_trunc('month', NOW()) THEN 1 END), 0) AS month_invoices,
                    COALESCE(SUM(cost_thb), 0) AS total_cost,
                    COALESCE(SUM(pages), 0) AS total_pages,
                    COALESCE(COUNT(*), 0) AS total_invoices
                FROM ocr_cost_log
            """)
            row = cur.fetchone() or {}
            # 引擎占比
            cur.execute("""
                SELECT engine, COUNT(*) AS cnt, COALESCE(SUM(cost_thb), 0) AS cost
                FROM ocr_cost_log
                WHERE date_trunc('month', created_at) = date_trunc('month', NOW())
                GROUP BY engine
            """)
            engines = [dict(r) for r in cur.fetchall()]
            return {
                "today": {
                    "cost_thb": float(row.get("today_cost") or 0),
                    "pages": int(row.get("today_pages") or 0),
                    "invoices": int(row.get("today_invoices") or 0),
                },
                "month": {
                    "cost_thb": float(row.get("month_cost") or 0),
                    "pages": int(row.get("month_pages") or 0),
                    "invoices": int(row.get("month_invoices") or 0),
                },
                "total": {
                    "cost_thb": float(row.get("total_cost") or 0),
                    "pages": int(row.get("total_pages") or 0),
                    "invoices": int(row.get("total_invoices") or 0),
                },
                "engines": [
                    {"engine": e["engine"], "count": int(e["cnt"]), "cost_thb": float(e["cost"])}
                    for e in engines
                ],
            }
    except Exception as e:
        logger.error(f"get_cost_overview failed: {e}")
        return {"today": {}, "month": {}, "total": {}, "engines": []}


def get_cost_by_user(limit: int = 50) -> List[Dict[str, Any]]:
    """按用户分组 · 找烧钱多的"""
    try:
        with db.get_cursor() as cur:
            cur.execute(
                """
                SELECT
                    c.user_id,
                    u.username,
                    u.plan,
                    COALESCE(SUM(CASE WHEN c.created_at::date = CURRENT_DATE THEN c.cost_thb END), 0) AS today_cost,
                    COALESCE(SUM(CASE WHEN date_trunc('month', c.created_at) = date_trunc('month', NOW()) THEN c.cost_thb END), 0) AS month_cost,
                    COALESCE(SUM(c.cost_thb), 0) AS total_cost,
                    COALESCE(SUM(c.pages), 0) AS total_pages,
                    COUNT(*) AS total_invoices,
                    MAX(c.created_at) AS last_used_at
                FROM ocr_cost_log c
                LEFT JOIN users u ON u.id = c.user_id
                GROUP BY c.user_id, u.username, u.plan
                ORDER BY month_cost DESC, total_cost DESC
                LIMIT %s
            """,
                (limit,),
            )
            return [dict(r) for r in cur.fetchall()]
    except Exception as e:
        logger.error(f"get_cost_by_user failed: {e}")
        return []


def get_cost_daily_trend(days: int = 30) -> List[Dict[str, Any]]:
    """每天趋势 · 最近 N 天"""
    try:
        with db.get_cursor() as cur:
            cur.execute("""
                SELECT
                    created_at::date AS day,
                    COALESCE(SUM(cost_thb), 0) AS cost,
                    COALESCE(SUM(pages), 0) AS pages,
                    COUNT(*) AS invoices
                FROM ocr_cost_log
                WHERE created_at >= NOW() - INTERVAL '%s days'
                GROUP BY day
                ORDER BY day ASC
            """ % int(days))
            return [
                {
                    "day": str(r["day"]),
                    "cost_thb": float(r["cost"] or 0),
                    "pages": int(r["pages"] or 0),
                    "invoices": int(r["invoices"] or 0),
                }
                for r in cur.fetchall()
            ]
    except Exception as e:
        logger.error(f"get_cost_daily_trend failed: {e}")
        return []


def get_cost_daily_by_engine(days: int = 30) -> List[Dict[str, Any]]:
    """每天 × 引擎 成本明细(成本趋势堆叠图用)· 纯只读聚合 · 不涉任何扣费逻辑。
    返回 [{day, engine, cost_thb, pages, invoices}] · 前端按引擎归一/堆叠。"""
    try:
        with db.get_cursor() as cur:
            cur.execute("""
                SELECT
                    created_at::date AS day,
                    COALESCE(engine, 'other') AS engine,
                    COALESCE(SUM(cost_thb), 0) AS cost,
                    COALESCE(SUM(pages), 0) AS pages,
                    COUNT(*) AS invoices
                FROM ocr_cost_log
                WHERE created_at >= NOW() - INTERVAL '%s days'
                GROUP BY day, engine
                ORDER BY day ASC
            """ % int(days))
            return [
                {
                    "day": str(r["day"]),
                    "engine": r["engine"],
                    "cost_thb": float(r["cost"] or 0),
                    "pages": int(r["pages"] or 0),
                    "invoices": int(r["invoices"] or 0),
                }
                for r in cur.fetchall()
            ]
    except Exception as e:
        logger.error(f"get_cost_daily_by_engine failed: {e}")
        return []
