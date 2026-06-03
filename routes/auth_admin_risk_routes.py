"""超管风控路由 · 可疑用户 / 封禁 / 批量封禁(从 auth_admin_routes 抽出 · 0 逻辑改)。"""

import json
import logging
from typing import List

from fastapi import APIRouter, HTTPException, Query, Request
from pydantic import BaseModel, Field

from services.auth.auth_admin_common import _require_super_admin

logger = logging.getLogger("mrpilot.signup")
router = APIRouter()


# ============================================================
# 后台 · 风控 · 可疑用户
# ============================================================
@router.get("/api/admin/risk/suspicious")
def admin_suspicious_users(request: Request):
    """后台看可疑用户(同 IP / 同指纹 / 临时邮箱 / 异常 OCR)
    v116 · 加返回 accounts 详细数组(含 user_id) · 给前端批量操作用"""
    try:
        _require_super_admin(request)
        from core import db as _db

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
        from core import db as _db

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
        from core import db as _db

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
        from core import db as _db

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
