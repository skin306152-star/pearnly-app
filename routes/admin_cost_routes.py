# -*- coding: utf-8 -*-
"""
Pearnly · 超管成本/收入/监控面板路由模块(REFACTOR-B1 · 2026-05-25 抽出)

从 app.py 整片搬过来 · 纯搬家 · 不改业务逻辑 / URL / response shape / error code。
全部路由仅超管可调(_require_super_admin)· 全是只读聚合 + CSV 导出 · 不涉扣费。

覆盖 11 个 API:
  GET /api/admin/cost/overview        · 成本面板 KPI
  GET /api/admin/cost/debug           · 成本追踪诊断(直查 ocr_cost_log)
  GET /api/admin/cost/by_user         · 按用户分组成本
  GET /api/admin/cost/daily_trend     · 成本每日趋势 + 引擎堆叠
  GET /api/admin/cost/ai-usage        · AI 网关全量调用成本(ai_usage · 独立口径 2026-07-09)
  GET /api/admin/credits/overview     · 收入端 KPI
  GET /api/admin/credits/tenants      · 全公司余额清单
  GET /api/admin/credits/daily_trend  · 每日收支趋势
  GET /api/admin/monitoring/overview  · Gemini 限流 + DB 连接池监控
  GET /api/admin/credits/export       · credit_transactions CSV 导出
  GET /api/admin/cost/export          · ocr_cost_log CSV 导出

依赖:
  - db.*(成本/收入只读聚合 + get_cursor)
  - route_helpers._require_super_admin(超管守门 · 公共)
  - services.monitoring.get_monitoring_overview(函数内懒 import)
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException, Request

from core import db
from core.route_helpers import _require_super_admin
from services.export.csv_safe import SafeCsvWriter

logger = logging.getLogger("mr-pilot")

router = APIRouter()


# ============================================================
# v106 · 管理员成本追踪面板 · 4 个路由 · 仅 super_admin 可访问
# ============================================================


@router.get("/api/admin/cost/overview")
async def admin_cost_overview(request: Request):
    """成本面板 · 顶部 KPI(今日/本月/总计 + 引擎占比)"""
    _require_super_admin(request)
    return db.get_cost_overview()


# v107.3 · 诊断接口 · 直接 SELECT 5 条最新记录看是否有数据
@router.get("/api/admin/cost/debug")
async def admin_cost_debug(request: Request):
    """成本追踪诊断 · 仅 super admin · 用于排查为什么前端看不到数据"""
    _require_super_admin(request)
    try:
        with db.get_cursor() as cur:
            # 1. 表是否存在 + 总条数
            cur.execute("""
                SELECT COUNT(*) AS total,
                       MIN(created_at) AS earliest,
                       MAX(created_at) AS latest,
                       SUM(cost_thb) AS sum_cost,
                       SUM(pages) AS sum_pages
                FROM ocr_cost_log
            """)
            stats = dict(cur.fetchone() or {})
            # 2. 最近 5 条
            cur.execute("""
                SELECT id, user_id::text, engine, pages, input_tokens, output_tokens,
                       cost_thb, created_at, created_at::date AS day_only,
                       CURRENT_DATE AS db_today, NOW() AS db_now
                FROM ocr_cost_log
                ORDER BY created_at DESC
                LIMIT 5
            """)
            recent = [dict(r) for r in cur.fetchall()]
            # 3. PostgreSQL 时区设置
            cur.execute("SHOW timezone")
            tz = cur.fetchone()
        # 序列化(datetime → str)
        from datetime import datetime as _dt

        def _ser(v):
            if isinstance(v, _dt):
                return v.isoformat()
            try:
                # date 类型
                return str(v)
            except:
                return v

        return {
            "table_stats": {k: _ser(v) for k, v in stats.items()},
            "postgres_timezone": dict(tz) if tz else {},
            "recent_5": [{k: _ser(v) for k, v in r.items()} for r in recent],
        }
    except Exception as e:
        import traceback

        return {"error": str(e), "traceback": traceback.format_exc()}


@router.get("/api/admin/cost/by_user")
async def admin_cost_by_user(request: Request, limit: int = 50):
    """按用户分组 · 找烧钱多的"""
    _require_super_admin(request)
    rows = db.get_cost_by_user(limit=limit)
    return {
        "users": [
            {
                "user_id": str(r.get("user_id")),
                "username": r.get("username") or "(已删)",
                "plan": r.get("plan") or "",
                "today_cost_thb": float(r.get("today_cost") or 0),
                "month_cost_thb": float(r.get("month_cost") or 0),
                "total_cost_thb": float(r.get("total_cost") or 0),
                "total_pages": int(r.get("total_pages") or 0),
                "total_invoices": int(r.get("total_invoices") or 0),
                "last_used_at": r["last_used_at"].isoformat() if r.get("last_used_at") else None,
            }
            for r in rows
        ],
    }


@router.get("/api/admin/cost/daily_trend")
async def admin_cost_daily_trend(request: Request, days: int = 30):
    """每天趋势 · 默认最近 30 天"""
    _require_super_admin(request)
    days = max(1, min(int(days), 365))
    # by_engine:按天×引擎只读聚合(成本趋势堆叠图用)· 不涉扣费 · 前端归一/堆叠
    return {
        "days": db.get_cost_daily_trend(days=days),
        "by_engine": db.get_cost_daily_by_engine(days=days),
    }


@router.get("/api/admin/cost/ai-usage")
async def admin_cost_ai_usage(request: Request):
    """AI 网关全量调用成本(ai_usage · Agent 对话/LINE 语音/知识库问答 + OCR)· 近 30 天。

    ⚠️ 独立口径,别跟上面 ocr_cost_log 系列数字相加:ai_usage 是网关唯一写点
    (services/ai_gateway/logging.py::log_call)落的账,OCR 走 multimodal_to_json 也经
    这里 —— 与 ocr_cost_log 的 OCR 记账有重叠但统计维度不同(无 engine/pages/history_id),
    两表对不上是预期行为,不是 bug。
    """
    _require_super_admin(request)
    from services.cost.ai_usage_store import get_usage_by_task, get_usage_daily_trend

    return {
        "note": "独立口径 · 与 ocr_cost_log 系列数字有重叠不可相加 · 见本端点注释",
        "by_task": get_usage_by_task(days=30),
        "daily_trend": get_usage_daily_trend(days=30),
    }


# ============================================================
# v118.35.0.22 · Earn 超管 · Credits 数据互通(收入端 · 跟 cost 互补)
# ============================================================
@router.get("/api/admin/credits/overview")
async def admin_credits_overview(request: Request):
    """收入端 KPI · 今日/本月扣费 + 充值 + 余额池总和 + 透支公司数"""
    _require_super_admin(request)
    return db.get_credits_revenue_overview()


@router.get("/api/admin/credits/tenants")
async def admin_credits_tenants(request: Request, limit: int = 100):
    """全公司余额清单 + 当月用量 + 透支警报"""
    _require_super_admin(request)
    limit = max(1, min(int(limit), 500))
    return {"tenants": db.get_tenants_credits_summary(limit=limit)}


@router.get("/api/admin/credits/daily_trend")
async def admin_credits_daily_trend(request: Request, days: int = 30):
    """每天收支趋势 · 从 credit_transactions 拉(替代 ocr_cost_log)"""
    _require_super_admin(request)
    days = max(1, min(int(days), 365))
    return {"days": db.get_credits_daily_trend(days=days)}


# ============================================================
# v118.35.0.25 · Earn 监控面板 · Gemini 限流统计 + DB 连接池(只看数据 · 无 LINE 告警)
# ============================================================
@router.get("/api/admin/monitoring/overview")
async def admin_monitoring_overview(request: Request):
    """监控数据 · Gemini 调用统计 + DB 连接池(超管登录后看)"""
    _require_super_admin(request)
    from services.monitoring import get_monitoring_overview

    return get_monitoring_overview()


@router.get("/api/admin/credits/export")
async def admin_credits_export(request: Request, days: int = 30):
    """导出 CSV · 最近 N 天每条 credit_transactions 记录(供会计对账)"""
    _require_super_admin(request)
    days = max(1, min(int(days), 365))
    try:
        with db.get_cursor() as cur:
            cur.execute(
                """
                SELECT
                    ct.id, ct.tenant_id::text, t.name AS tenant_name,
                    ct.user_id::text, u.username,
                    ct.type, ct.amount_thb, ct.pages, ct.balance_after,
                    ct.description, ct.created_at
                FROM credit_transactions ct
                LEFT JOIN tenants t ON t.id = ct.tenant_id
                LEFT JOIN users u ON u.id = ct.user_id
                WHERE ct.created_at >= NOW() - INTERVAL %s
                ORDER BY ct.created_at DESC
            """,
                (f"{days} days",),
            )
            rows = cur.fetchall() or []
    except Exception as e:
        raise HTTPException(500, detail=f"export_failed: {e}")

    import io
    import csv

    buf = io.StringIO()
    w = SafeCsvWriter(csv.writer(buf))
    w.writerow(
        [
            "id",
            "tenant_id",
            "tenant_name",
            "user_id",
            "username",
            "type",
            "amount_thb",
            "pages",
            "balance_after",
            "description",
            "created_at",
        ]
    )
    for r in rows:
        w.writerow(
            [
                r["id"],
                r["tenant_id"] or "",
                r["tenant_name"] or "",
                r["user_id"] or "",
                r["username"] or "",
                r["type"],
                float(r["amount_thb"] or 0),
                int(r["pages"] or 0),
                float(r["balance_after"] or 0),
                r["description"] or "",
                r["created_at"].isoformat() if r["created_at"] else "",
            ]
        )
    from fastapi.responses import Response

    return Response(
        content="﻿" + buf.getvalue(),  # BOM 让 Excel 识别 UTF-8
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f"attachment; filename=credits_{days}days.csv"},
    )


@router.get("/api/admin/cost/export")
async def admin_cost_export(request: Request, days: int = 30):
    """导出 CSV · 最近 N 天每条成本记录"""
    _require_super_admin(request)
    days = max(1, min(int(days), 365))
    try:
        with db.get_cursor() as cur:
            cur.execute("""
                SELECT c.created_at, u.username, c.engine, c.pages,
                       c.input_tokens, c.output_tokens, c.cost_thb, c.elapsed_ms
                FROM ocr_cost_log c
                LEFT JOIN users u ON u.id = c.user_id
                WHERE c.created_at >= NOW() - INTERVAL '%s days'
                ORDER BY c.created_at DESC
            """ % days)
            rows = cur.fetchall()
        # 拼 CSV
        import io
        import csv

        buf = io.StringIO()
        w = SafeCsvWriter(csv.writer(buf))
        w.writerow(["时间", "用户", "引擎", "页数", "输入Token", "输出Token", "成本THB", "耗时ms"])
        for r in rows:
            w.writerow(
                [
                    r["created_at"].strftime("%Y-%m-%d %H:%M:%S") if r["created_at"] else "",
                    r.get("username") or "(已删)",
                    r.get("engine") or "",
                    int(r.get("pages") or 0),
                    int(r.get("input_tokens") or 0),
                    int(r.get("output_tokens") or 0),
                    f"{float(r.get('cost_thb') or 0):.4f}",
                    int(r.get("elapsed_ms") or 0),
                ]
            )
        from fastapi.responses import Response

        return Response(
            content="﻿" + buf.getvalue(),  # BOM 让 Excel 正确识别中文
            media_type="text/csv; charset=utf-8",
            headers={"Content-Disposition": f'attachment; filename="cost_log_{days}d.csv"'},
        )
    except Exception as e:
        logger.error(f"admin_cost_export failed: {e}")
        raise HTTPException(500, detail="admin.export_failed")
