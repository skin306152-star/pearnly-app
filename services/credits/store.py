# -*- coding: utf-8 -*-
"""Credits 收入流分析(credit_transactions · tenant_credits 表)· 只读聚合 · 数据访问层

从 db.py 抽出(REFACTOR-B2 · 纯搬家 · 0 逻辑改)。
Earn 超管面板用:收入端 KPI(今日/本月/总计)· 各租户额度汇总 · 单租户额度 · 日趋势。
全部只读 SELECT 聚合(不动钱 · 不扣费 · 充值/扣费写入仍在 db.py charge_ocr 等)。
游标走 db.get_cursor(...)·db.py 文件尾 re-export 回本命名空间(admin_cost_routes/admin_users_routes 走 db.* 零改动)。
"""

import logging
from typing import Dict, Any

from core import db

logger = logging.getLogger(__name__)


def get_credits_revenue_overview() -> dict:
    """v0.22 · 收入端 KPI(今日/本月/总计) · 从 credit_transactions 拉
    type='usage'  = 扣费收入(amount_thb 是负数 · 取绝对值)
    type='topup'  = 充值入账(amount_thb 是正数)
    type='adjustment' = 退款(amount_thb 是正数 · 算冲销)
    """
    try:
        with db.get_cursor() as cur:
            cur.execute("""
                SELECT
                    COALESCE(SUM(CASE WHEN type='usage'  AND created_at::date = CURRENT_DATE THEN -amount_thb END), 0) AS today_usage,
                    COALESCE(SUM(CASE WHEN type='topup'  AND created_at::date = CURRENT_DATE THEN  amount_thb END), 0) AS today_topup,
                    COALESCE(SUM(CASE WHEN type='usage'  AND date_trunc('month', created_at) = date_trunc('month', NOW()) THEN -amount_thb END), 0) AS month_usage,
                    COALESCE(SUM(CASE WHEN type='topup'  AND date_trunc('month', created_at) = date_trunc('month', NOW()) THEN  amount_thb END), 0) AS month_topup,
                    COALESCE(SUM(CASE WHEN type='usage'  THEN -amount_thb END), 0) AS total_usage,
                    COALESCE(SUM(CASE WHEN type='topup'  THEN  amount_thb END), 0) AS total_topup,
                    COALESCE(SUM(CASE WHEN type='usage'  AND created_at::date = CURRENT_DATE THEN pages END), 0) AS today_pages,
                    COALESCE(SUM(CASE WHEN type='usage'  AND date_trunc('month', created_at) = date_trunc('month', NOW()) THEN pages END), 0) AS month_pages,
                    COUNT(CASE WHEN type='usage' AND created_at::date = CURRENT_DATE THEN 1 END) AS today_ocr_count,
                    COUNT(CASE WHEN type='usage' AND date_trunc('month', created_at) = date_trunc('month', NOW()) THEN 1 END) AS month_ocr_count
                FROM credit_transactions
            """)
            row = cur.fetchone() or {}

            # 所有 tenant 余额总和
            cur.execute("SELECT COALESCE(SUM(balance_thb), 0) AS total FROM tenant_credits")
            bal_row = cur.fetchone() or {}
            total_balance = float(bal_row.get("total") or 0)

            # 透支公司数(余额 ≤ 0)
            cur.execute("SELECT COUNT(*) AS n FROM tenant_credits WHERE balance_thb <= 0")
            neg_row = cur.fetchone() or {}
            overdraft_count = int(neg_row.get("n") or 0)

            return {
                "today": {
                    "usage_thb": float(row.get("today_usage") or 0),
                    "topup_thb": float(row.get("today_topup") or 0),
                    "pages": int(row.get("today_pages") or 0),
                    "ocr_count": int(row.get("today_ocr_count") or 0),
                },
                "month": {
                    "usage_thb": float(row.get("month_usage") or 0),
                    "topup_thb": float(row.get("month_topup") or 0),
                    "pages": int(row.get("month_pages") or 0),
                    "ocr_count": int(row.get("month_ocr_count") or 0),
                },
                "total": {
                    "usage_thb": float(row.get("total_usage") or 0),
                    "topup_thb": float(row.get("total_topup") or 0),
                },
                "pool_balance_thb": total_balance,
                "overdraft_tenants": overdraft_count,
            }
    except Exception as e:
        logger.error(f"get_credits_revenue_overview failed: {e}")
        return {
            "today": {},
            "month": {},
            "total": {},
            "pool_balance_thb": 0,
            "overdraft_tenants": 0,
        }


def get_tenants_credits_summary(limit: int = 100) -> list:
    """v0.22 · 全公司列表 · 余额 + 当月用量 + 透支警报
    按余额降序 · 让超管看哪家公司钱多 / 哪家透支了
    """
    try:
        ym = db._bkk_year_month()
        with db.get_cursor() as cur:
            cur.execute(
                f"""
                SELECT
                    t.id::text AS tenant_id,
                    t.name AS tenant_name,
                    COALESCE(tc.balance_thb, 0) AS balance_thb,
                    COALESCE(mpu.pages_used, 0) AS pages_this_month,
                    COALESCE(ts.pages_used_this_cycle, 0) AS sub_pages_used,
                    COALESCE(
                        (SELECT SUM(-ct.amount_thb) FROM credit_transactions ct
                         WHERE ct.tenant_id = t.id AND ct.type='usage'
                         AND date_trunc('month', ct.created_at) = date_trunc('month', NOW())),
                        0
                    ) AS month_usage_thb,
                    COALESCE(
                        (SELECT SUM(ct.amount_thb) FROM credit_transactions ct
                         WHERE ct.tenant_id = t.id AND ct.type='topup'),
                        0
                    ) AS lifetime_topup_thb,
                    (SELECT MAX(ct.created_at) FROM credit_transactions ct
                     WHERE ct.tenant_id = t.id AND ct.type='usage') AS last_usage_at,
                    t.created_at AS tenant_created_at
                FROM tenants t
                LEFT JOIN tenant_credits tc ON tc.tenant_id = t.id
                LEFT JOIN monthly_page_usage mpu
                       ON mpu.tenant_id = t.id AND mpu.year_month = %s
                {db.active_sub_usage_join_sql("ts", "t.id")}
                ORDER BY balance_thb DESC NULLS LAST
                LIMIT %s
            """,
                (ym, limit),
            )
            rows = cur.fetchall() or []

        out = []
        for r in rows:
            bal = float(r["balance_thb"] or 0)
            # 本月用量 = 按量表 + 活跃订阅本周期用量(两计数器互斥不重复计 · 见
            # services/billing/subscription.py active_sub_usage_join_sql)
            pages_this_month = int(r["pages_this_month"] or 0) + int(r.get("sub_pages_used") or 0)
            out.append(
                {
                    "tenant_id": r["tenant_id"],
                    "tenant_name": r["tenant_name"] or "(无名)",
                    "balance_thb": bal,
                    "pages_this_month": pages_this_month,
                    "month_usage_thb": float(r["month_usage_thb"] or 0),
                    "lifetime_topup_thb": float(r["lifetime_topup_thb"] or 0),
                    "last_usage_at": r["last_usage_at"].isoformat() if r["last_usage_at"] else None,
                    "tenant_created_at": (
                        r["tenant_created_at"].isoformat() if r["tenant_created_at"] else None
                    ),
                    "is_overdraft": bal <= 0,
                    "is_low_balance": 0 < bal < 50,
                }
            )
        return out
    except Exception as e:
        logger.error(f"get_tenants_credits_summary failed: {e}")
        return []


def get_tenant_credit_summary(tenant_id: str) -> Dict[str, Any]:
    """单租户 credits 汇总(Earn 用户详情抽屉用)· 余额 + 本月扣费/页数 + 累计充值 + 充值次数。
    取不到/出错返回 {} · 调用方按缺省隐藏(抽屉不做空壳)。"""
    if not tenant_id:
        return {}
    try:
        ym = db._bkk_year_month()
        with db.get_cursor() as cur:
            cur.execute(
                f"""
                SELECT
                    COALESCE(tc.balance_thb, 0) AS balance_thb,
                    COALESCE(mpu.pages_used, 0) AS pages_this_month,
                    COALESCE(ts.pages_used_this_cycle, 0) AS sub_pages_used,
                    COALESCE(
                        (SELECT SUM(-ct.amount_thb) FROM credit_transactions ct
                         WHERE ct.tenant_id = t.id AND ct.type='usage'
                         AND date_trunc('month', ct.created_at) = date_trunc('month', NOW())),
                        0) AS month_usage_thb,
                    COALESCE(
                        (SELECT SUM(ct.amount_thb) FROM credit_transactions ct
                         WHERE ct.tenant_id = t.id AND ct.type='topup'), 0) AS lifetime_topup_thb,
                    (SELECT COUNT(*) FROM credit_transactions ct
                     WHERE ct.tenant_id = t.id AND ct.type='topup') AS topup_count,
                    (SELECT MAX(ct.created_at) FROM credit_transactions ct
                     WHERE ct.tenant_id = t.id AND ct.type='topup') AS last_topup_at
                FROM tenants t
                LEFT JOIN tenant_credits tc ON tc.tenant_id = t.id
                LEFT JOIN monthly_page_usage mpu
                       ON mpu.tenant_id = t.id AND mpu.year_month = %s
                {db.active_sub_usage_join_sql("ts", "t.id")}
                WHERE t.id = %s
                """,
                (ym, tenant_id),
            )
            r = cur.fetchone()
        if not r:
            return {}
        bal = float(r["balance_thb"] or 0)
        # 本月用量 = 按量表 + 活跃订阅本周期用量(两计数器互斥不重复计 · 见
        # services/billing/subscription.py active_sub_usage_join_sql)
        pages_this_month = int(r["pages_this_month"] or 0) + int(r.get("sub_pages_used") or 0)
        return {
            "balance_thb": bal,
            "pages_this_month": pages_this_month,
            "month_usage_thb": float(r["month_usage_thb"] or 0),
            "lifetime_topup_thb": float(r["lifetime_topup_thb"] or 0),
            "topup_count": int(r["topup_count"] or 0),
            "last_topup_at": r["last_topup_at"].isoformat() if r["last_topup_at"] else None,
            "is_overdraft": bal <= 0,
            "is_low_balance": 0 < bal < 50,
        }
    except Exception as e:
        logger.error(f"get_tenant_credit_summary failed: {e}")
        return {}


def get_credits_daily_trend(days: int = 30) -> list:
    """v0.22 · 每日收支趋势 · 用 credit_transactions(替代 ocr_cost_log)"""
    try:
        with db.get_cursor() as cur:
            cur.execute("""
                SELECT
                    created_at::date AS day,
                    COALESCE(SUM(CASE WHEN type='usage' THEN -amount_thb END), 0) AS usage_thb,
                    COALESCE(SUM(CASE WHEN type='topup' THEN amount_thb END), 0) AS topup_thb,
                    COALESCE(SUM(CASE WHEN type='usage' THEN pages END), 0) AS pages,
                    COUNT(CASE WHEN type='usage' THEN 1 END) AS ocr_count
                FROM credit_transactions
                WHERE created_at >= NOW() - INTERVAL '%s days'
                GROUP BY day
                ORDER BY day ASC
            """ % int(max(1, min(days, 365))))
            return [
                {
                    "day": str(r["day"]),
                    "usage_thb": float(r["usage_thb"] or 0),
                    "topup_thb": float(r["topup_thb"] or 0),
                    "pages": int(r["pages"] or 0),
                    "ocr_count": int(r["ocr_count"] or 0),
                }
                for r in cur.fetchall()
            ]
    except Exception as e:
        logger.error(f"get_credits_daily_trend failed: {e}")
        return []
