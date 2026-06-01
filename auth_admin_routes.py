"""
auth_admin_routes.py · 超管风控 / 用户管理工具路由

从 auth_signup.py 抽出(模块化深化 · 2026-06-01 · 纯搬家 0 逻辑改)。
funnel / cleanup_demo / risk-suspicious / ban / unban / risk-batch-ban /
password_resets / signup_sources 共 8 个超管路由。auth_signup include 本 router。
auth_signup 的 helper(_require_super_admin / _row_count)经本模块同名 shim
lazy 委托回 auth_signup 破循环 import。
"""

import json
import logging
import traceback
from typing import List

from fastapi import APIRouter, HTTPException, Query, Request
from pydantic import BaseModel, Field

logger = logging.getLogger("mrpilot.signup")
router = APIRouter()


def _require_super_admin(request: Request):
    """lazy 委托 auth_signup._require_super_admin(破循环 import)。"""
    from auth_signup import _require_super_admin as _f

    return _f(request)


def _row_count(row, default=0):
    """lazy 委托 auth_signup._row_count(破循环 import)。"""
    from auth_signup import _row_count as _f

    return _f(row, default)


@router.get("/api/admin/users/funnel")
def admin_user_funnel(request: Request):
    """admin 用户增长 + 国家分布(credits 模式 · 不再有套餐分布)"""
    try:
        _require_super_admin(request)
        import db as _db

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
        admin = _require_super_admin(request)
        import db as _db

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
# 后台 · 风控 · 可疑用户
# ============================================================
@router.get("/api/admin/risk/suspicious")
def admin_suspicious_users(request: Request):
    """后台看可疑用户(同 IP / 同指纹 / 临时邮箱 / 异常 OCR)
    v116 · 加返回 accounts 详细数组(含 user_id) · 给前端批量操作用"""
    try:
        _require_super_admin(request)
        import db as _db

        with _db.get_cursor(commit=True) as cur:
            # 1. 同 IP 注册多个账号
            cur.execute("""
                    SELECT signup_ip, COUNT(*) AS n,
                           jsonb_agg(jsonb_build_object(
                               'user_id', id::text,
                               'email', COALESCE(email, username),
                               'plan', plan,
                               'is_banned', is_banned,
                               'created_at', created_at::text
                           ) ORDER BY created_at DESC) AS accounts,
                           MAX(created_at) AS last_signup
                    FROM users
                    WHERE signup_ip IS NOT NULL
                      AND created_at > NOW() - INTERVAL '7 days'
                    GROUP BY signup_ip
                    HAVING COUNT(*) > 1
                    ORDER BY n DESC
                    LIMIT 50
                """)
            same_ip = []
            for r in cur.fetchall():
                if isinstance(r, dict):
                    accounts = r.get("accounts") or []
                    same_ip.append(
                        {
                            "ip": r.get("signup_ip"),
                            "count": r.get("n", 0),
                            "accounts": accounts if isinstance(accounts, list) else [],
                            "last_signup": (
                                r.get("last_signup").isoformat() if r.get("last_signup") else None
                            ),
                        }
                    )
                else:
                    same_ip.append(
                        {
                            "ip": r[0],
                            "count": r[1],
                            "accounts": (r[2] or []),
                            "last_signup": r[3].isoformat() if r[3] else None,
                        }
                    )

            # 2. 同指纹注册多个账号
            cur.execute("""
                    SELECT signup_fingerprint, COUNT(*) AS n,
                           jsonb_agg(jsonb_build_object(
                               'user_id', id::text,
                               'email', COALESCE(email, username),
                               'plan', plan,
                               'is_banned', is_banned,
                               'created_at', created_at::text
                           ) ORDER BY created_at DESC) AS accounts
                    FROM users
                    WHERE signup_fingerprint IS NOT NULL
                      AND created_at > NOW() - INTERVAL '14 days'
                    GROUP BY signup_fingerprint
                    HAVING COUNT(*) > 1
                    ORDER BY n DESC
                    LIMIT 50
                """)
            same_fp = []
            for r in cur.fetchall():
                if isinstance(r, dict):
                    fp = r.get("signup_fingerprint") or ""
                    accounts = r.get("accounts") or []
                    same_fp.append(
                        {
                            "fingerprint": fp,
                            "fingerprint_short": fp[:20] + "..." if len(fp) > 20 else fp,
                            "count": r.get("n", 0),
                            "accounts": accounts if isinstance(accounts, list) else [],
                        }
                    )
                else:
                    fp = r[0] or ""
                    same_fp.append(
                        {
                            "fingerprint": fp,
                            "fingerprint_short": fp[:20] + "..." if len(fp) > 20 else fp,
                            "count": r[1],
                            "accounts": (r[2] or []),
                        }
                    )

            # 3. OCR 用量异常(单日 > 30 张)
            cur.execute("""
                    SELECT u.id, COALESCE(u.email, u.username) AS user_email, u.plan,
                           u.is_banned,
                           COUNT(o.id) AS today_count
                    FROM users u
                    JOIN ocr_history o ON o.user_id = u.id
                    WHERE o.created_at > NOW() - INTERVAL '24 hours'
                    GROUP BY u.id, u.email, u.username, u.plan, u.is_banned
                    HAVING COUNT(o.id) > 30
                    ORDER BY today_count DESC
                    LIMIT 30
                """)
            heavy = []
            for r in cur.fetchall():
                if isinstance(r, dict):
                    heavy.append(
                        {
                            "user_id": str(r.get("id")),
                            "email": r.get("user_email"),
                            "plan": r.get("plan"),
                            "is_banned": r.get("is_banned", False),
                            "ocr_today": r.get("today_count"),
                        }
                    )
                else:
                    heavy.append(
                        {
                            "user_id": str(r[0]),
                            "email": r[1],
                            "plan": r[2],
                            "is_banned": r[3],
                            "ocr_today": r[4],
                        }
                    )

            # 4. 风控事件最近 24h
            cur.execute("""
                    SELECT event_type, COUNT(*) AS n
                    FROM risk_log
                    WHERE created_at > NOW() - INTERVAL '24 hours'
                    GROUP BY event_type
                    ORDER BY n DESC
                """)
            events_24h = []
            for r in cur.fetchall():
                if isinstance(r, dict):
                    events_24h.append({"event": r.get("event_type"), "count": r.get("n", 0)})
                else:
                    events_24h.append({"event": r[0], "count": r[1]})

        return {
            "ok": True,
            "same_ip_signups": same_ip,
            "same_fingerprint_signups": same_fp,
            "heavy_ocr_users": heavy,
            "risk_events_24h": events_24h,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"admin_suspicious_users: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/admin/users/{user_id}/ban")
def admin_ban_user(user_id: str, request: Request, reason: str = Query("")):
    try:
        admin = _require_super_admin(request)
        import db as _db

        with _db.get_cursor(commit=True) as cur:
            cur.execute(
                """
                    UPDATE users SET is_banned=true, ban_reason=%s WHERE id=%s
                """,
                (reason or "manual_ban", user_id),
            )
            cur.execute(
                """
                    INSERT INTO risk_log(user_id, event_type, detail)
                    VALUES (%s, 'admin_ban', %s)
                """,
                (user_id, json.dumps({"reason": reason, "by": str(admin.get("id"))})),
            )
        return {"ok": True}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"admin_ban_user: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/admin/users/{user_id}/unban")
def admin_unban_user(user_id: str, request: Request):
    try:
        _require_super_admin(request)
        import db as _db

        with _db.get_cursor(commit=True) as cur:
            cur.execute(
                """
                    UPDATE users SET is_banned=false, ban_reason=NULL WHERE id=%s
                """,
                (user_id,),
            )
        return {"ok": True}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"admin_unban_user: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# v116 · 风控批量封禁 · 一次封多个账号(同 IP / 同指纹下的群组)
class RiskBatchBanRequest(BaseModel):
    user_ids: List[str] = Field(..., min_length=1, max_length=100)
    reason: str = Field(default="risk_batch_ban", max_length=200)


@router.post("/api/admin/risk/batch-ban")
def admin_risk_batch_ban(req: RiskBatchBanRequest, request: Request):
    """v116 · 批量封禁(风控页用 · 同 IP/指纹群组一键封)"""
    try:
        admin = _require_super_admin(request)
        import db as _db

        banned = 0
        skipped = []
        with _db.get_cursor(commit=True) as cur:
            for uid in req.user_ids:
                try:
                    # 跳过超管自己 + 已经封禁的
                    cur.execute("SELECT is_super_admin, is_banned FROM users WHERE id=%s", (uid,))
                    row = cur.fetchone()
                    if not row:
                        skipped.append({"user_id": uid, "reason": "not_found"})
                        continue
                    is_super = row.get("is_super_admin") if isinstance(row, dict) else row[0]
                    if is_super:
                        skipped.append({"user_id": uid, "reason": "is_super_admin"})
                        continue
                    cur.execute(
                        """
                            UPDATE users SET is_banned=true, ban_reason=%s WHERE id=%s
                        """,
                        (req.reason, uid),
                    )
                    cur.execute(
                        """
                            INSERT INTO risk_log(user_id, event_type, detail)
                            VALUES (%s, 'admin_batch_ban', %s)
                        """,
                        (uid, json.dumps({"reason": req.reason, "by": str(admin.get("id"))})),
                    )
                    banned += 1
                except Exception as inner_e:
                    logger.warning(f"batch_ban {uid} failed: {inner_e}")
                    skipped.append({"user_id": uid, "reason": "error"})
        return {"ok": True, "banned": banned, "skipped": skipped}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"admin_risk_batch_ban: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================
# v109.3.2 · 密码重置体系
# ============================================================


# 密码找回/重置/改密 + 发送器 → auth_password_routes.py(模块化深化 · 2026-06-01)。
# 下方 import 回 router 并 include · 并 re-export send_reset_link_for_employee(team_routes 用)。
@router.get("/api/admin/password_resets")
def admin_password_resets(request: Request):
    """后台 · 查看密码重置请求历史(应急客服)"""
    try:
        _require_super_admin(request)
        import db as _db

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
        import db as _db

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


# ============================================================
# 启动时执行 schema 迁移
# ============================================================
