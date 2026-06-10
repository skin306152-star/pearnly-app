"""
auth_admin_routes.py · 超管用户管理工具路由(facade)

funnel / cleanup_demo / password_resets / signup_sources 留本模块;
风控组(suspicious / ban / unban / batch-ban)→ auth_admin_risk_routes(include)。
helper(_require_super_admin / _row_count)→ auth_admin_common。auth_signup include 本 router。
"""

import logging
import traceback

from fastapi import APIRouter, HTTPException, Request

from services.auth.auth_admin_common import _require_super_admin, _row_count
from routes.auth_admin_risk_routes import router as _risk_router

logger = logging.getLogger("mrpilot.signup")
router = APIRouter()
router.include_router(_risk_router)


@router.get("/api/admin/users/funnel")
def admin_user_funnel(request: Request):
    """admin 用户增长 + 国家分布(credits 模式 · 不再有套餐分布)"""
    try:
        _require_super_admin(request)
        from core import db as _db

        with _db.get_cursor(commit=True) as cur:
            # 今日/本周/本月新增
            cur.execute("SELECT COUNT(*) FROM users WHERE created_at >= CURRENT_DATE")
            today = _row_count(cur.fetchone())
            cur.execute(
                "SELECT COUNT(*) FROM users WHERE created_at >= CURRENT_DATE - INTERVAL '7 days'"
            )
            week = _row_count(cur.fetchone())
            cur.execute(
                "SELECT COUNT(*) FROM users WHERE date_trunc('month', created_at) = date_trunc('month', NOW())"
            )
            month = _row_count(cur.fetchone())

            # 国家分布
            cur.execute("""
                    SELECT COALESCE(signup_country,'?') AS country, COUNT(*) AS n FROM users
                    GROUP BY 1 ORDER BY 2 DESC
                """)
            by_country = []
            for r in cur.fetchall():
                if isinstance(r, dict):
                    by_country.append({"country": r.get("country") or "?", "count": r.get("n", 0)})
                else:
                    by_country.append({"country": r[0], "count": r[1]})

        return {
            "ok": True,
            "new_today": today,
            "new_week": week,
            "new_month": month,
            "by_country": by_country,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"admin_user_funnel: {e}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================
# CLEANUP-PLAN-01 (2026-05-22) · 4 个老订阅 admin 路由整段删:
#   - GET  /api/admin/payments/pending       (payment_pending 表 · 老订阅付款审核 list)
#   - POST /api/admin/users/upgrade          (admin 升级用户套餐 · 写 users.plan)
#   - GET  /api/admin/payments/{id}/screenshot  (看付款截图)
#   - POST /api/admin/payments/{id}/review   (审批 = 升级 plan · 写 subscription_log)
# credits 模式不再有套餐升级 · 充值审核走 billing_routes.py admin_topup_list
# payment_pending / subscription_log 表保留(DB schema 改动留 REFACTOR-B3 Alembic 时再做)
# ============================================================


# ============================================================
# 后台 · 删除测试 demo 数据(一次性 · 保留 earn)
# ============================================================
@router.post("/api/admin/cleanup_demo")
def admin_cleanup_demo(request: Request):
    """删除 demo / demo_plus 等测试账号 + 数据 · 保留 earn / super_admin"""
    try:
        _require_super_admin(request)
        from core import db as _db

        deleted = {"users": 0, "ocr_history": 0, "clients": 0}
        with _db.get_cursor(commit=True) as cur:
            # 找出要删的用户(demo / demo_plus / 任何 username 以 demo_ 开头)
            cur.execute("""
                    SELECT id, username FROM users
                    WHERE (username='demo' OR username LIKE 'demo_%')
                      AND COALESCE(is_super_admin, false) = false
                """)
            ids = []
            for r in cur.fetchall():
                if isinstance(r, dict):
                    ids.append(str(r.get("id")))
                else:
                    ids.append(str(r[0]))
            if not ids:
                return {"ok": True, "deleted": deleted, "message": "no demo accounts found"}

            placeholders = ",".join(["%s"] * len(ids))
            # 级联删
            try:
                cur.execute(f"DELETE FROM ocr_history WHERE user_id IN ({placeholders})", ids)
                deleted["ocr_history"] = cur.rowcount
            except Exception as e:
                logger.warning(f"cleanup ocr_history skip: {e}")
            try:
                cur.execute(f"DELETE FROM clients WHERE user_id IN ({placeholders})", ids)
                deleted["clients"] = cur.rowcount
            except Exception as e:
                logger.warning(f"cleanup clients skip: {e}")
            # 其他可能的关联表(安全 try)
            for tbl in [
                "ocr_cost_log",
                "subscription_log",
                "payment_pending",
                "push_log",
                "billing_balance_log",
            ]:
                try:
                    cur.execute(f"DELETE FROM {tbl} WHERE user_id IN ({placeholders})", ids)
                except Exception:
                    pass  # 表可能不存在 · 安全跳过
            # 最后删用户
            cur.execute(f"DELETE FROM users WHERE id IN ({placeholders})", ids)
            deleted["users"] = cur.rowcount
        return {"ok": True, "deleted": deleted}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"admin_cleanup_demo: {e}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================
# v109.3.2 · 密码重置体系
# ============================================================


# 密码找回/重置/改密 + 发送器 → auth_password_routes.py(模块化深化 · 2026-06-01)。
@router.get("/api/admin/password_resets")
def admin_password_resets(request: Request):
    """后台 · 查看密码重置请求历史(应急客服)"""
    try:
        _require_super_admin(request)
        from core import db as _db

        with _db.get_cursor(commit=True) as cur:
            cur.execute("""
                SELECT
                    p.id, p.token, p.email, p.expires_at, p.used, p.used_at,
                    p.delivery_method, p.requester_ip, p.created_at,
                    u.username, u.full_name
                FROM password_reset_log p
                LEFT JOIN users u ON u.id = p.user_id
                ORDER BY p.created_at DESC
                LIMIT 100
            """)
            rows = cur.fetchall() or []
        out = []
        for r in rows:
            d = dict(r) if hasattr(r, "keys") else {}
            for k in ("expires_at", "used_at", "created_at"):
                if d.get(k):
                    try:
                        d[k] = d[k].isoformat()
                    except Exception:
                        d[k] = str(d[k])
            out.append(d)
        return {"items": out}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"admin_password_resets: {e}")
        raise HTTPException(500, detail=str(e))


@router.get("/api/admin/signup_sources")
def admin_signup_sources(request: Request):
    """后台 · 注册来源渠道分析"""
    try:
        _require_super_admin(request)
        from core import db as _db

        with _db.get_cursor(commit=True) as cur:
            cur.execute("""
                SELECT
                    COALESCE(signup_source, 'unknown') AS source,
                    COUNT(*) AS user_count,
                    COUNT(*) FILTER (WHERE plan IN ('plus', 'pro', 'lifetime')) AS paid_count,
                    COUNT(*) FILTER (WHERE created_at > NOW() - INTERVAL '7 days') AS week_count
                FROM users
                WHERE signup_source IS NOT NULL OR created_at > NOW() - INTERVAL '90 days'
                GROUP BY COALESCE(signup_source, 'unknown')
                ORDER BY user_count DESC
            """)
            rows = cur.fetchall() or []
        out = []
        for r in rows:
            d = dict(r) if hasattr(r, "keys") else {}
            for k in ("user_count", "paid_count", "week_count"):
                if k in d:
                    d[k] = int(d[k] or 0)
            out.append(d)
        return {"items": out}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"admin_signup_sources: {e}")
        raise HTTPException(500, detail=str(e))
