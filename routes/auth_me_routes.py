"""
auth_me_routes.py · /api/me/link_line(+dev)+ /api/me/plan

从 auth_signup.py 抽出(模块化深化 · 2026-06-01 · 纯搬家 0 逻辑改)。
🔴 link_line 是 LINE 绑定路径(铁律 #26)。auth_signup include 本 router。
共享 helper 从 services/auth/signup_core top-level import(无循环)。
"""

import logging
import os
import secrets
import traceback
from typing import Optional

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from services.auth.signup_core import (
    _get_plan,
    _get_user_safe,
    _now,
    _row_count,
    get_plan_features,
)

logger = logging.getLogger("mrpilot.signup")
router = APIRouter()


class LineLinkRequest(BaseModel):
    line_user_id: str
    line_display_name: Optional[str] = None


@router.post("/api/me/link_line")
def link_line(req: LineLinkRequest, request: Request):
    """
    用户绑定 LINE userId · 解锁完整配额

    流程:
    1. 前端通过 LINE OAuth 拿到 userId(由 LINE Login API 返回)
    2. 调本接口 · 把 userId 跟当前用户绑定
    3. 校验:同一 LINE userId 不能绑两个账号(防薅核心)
    """
    try:
        u = _get_user_safe(request)
        if not u:
            raise HTTPException(status_code=401, detail="unauthorized")

        line_user_id = (req.line_user_id or "").strip()
        if not line_user_id or len(line_user_id) < 8:
            raise HTTPException(status_code=400, detail="line_user_id_invalid")

        from core import db as _db

        with _db.get_cursor(commit=True) as cur:
            # 检查 LINE userId 是否已被其他账号绑定
            cur.execute(
                """
                    SELECT id FROM users WHERE line_user_id = %s AND id <> %s LIMIT 1
                """,
                (line_user_id, u.get("id")),
            )
            if cur.fetchone():
                raise HTTPException(status_code=409, detail="line_already_linked_other_account")

            cur.execute(
                """
                    UPDATE users SET
                        line_user_id = %s,
                        line_verified_at = NOW(),
                        line_id = COALESCE(line_id, %s)
                    WHERE id = %s
                """,
                (line_user_id, req.line_display_name or None, u.get("id")),
            )

        return {"ok": True, "line_user_id": line_user_id, "verified": True}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"link_line: {e}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail="line.link_failed")


# ============================================================
# DEV · 模拟 LINE 绑定(0→1 阶段 · LINE OAuth 还没接前用)
# 真 LINE Login API 接入后这个删掉 · 改用真实 OAuth
# ============================================================
@router.post("/api/me/link_line_dev")
def link_line_dev(request: Request):
    """开发期间用 · 模拟绑定一个随机 LINE userId · 让 trial 配额解锁"""
    if (os.environ.get("PEARNLY_ENV") or "").strip().lower() != "development":
        raise HTTPException(status_code=404, detail="not_found")
    try:
        u = _get_user_safe(request)
        if not u:
            raise HTTPException(status_code=401, detail="unauthorized")

        # 生成一个伪随机 ID(防止同一用户多次绑出多个不同 ID)
        from core import db as _db

        with _db.get_cursor(commit=True) as cur:
            cur.execute("SELECT line_user_id FROM users WHERE id=%s", (u.get("id"),))
            row = cur.fetchone()
            existing = None
            if row:
                existing = row.get("line_user_id") if isinstance(row, dict) else row[0]
            if existing:
                return {"ok": True, "line_user_id": existing, "already_linked": True}

            fake_id = f"DEV_{secrets.token_hex(10)}"
            cur.execute(
                """
                    UPDATE users SET line_user_id=%s, line_verified_at=NOW()
                    WHERE id=%s
                """,
                (fake_id, u.get("id")),
            )
        return {"ok": True, "line_user_id": fake_id, "dev_mode": True}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"link_line_dev: {e}")
        raise HTTPException(status_code=500, detail="line.dev_link_failed")


# ============================================================
# 路由 · 当前套餐 + 配额
# ============================================================
@router.get("/api/me/plan")
def get_my_plan(request: Request):
    """前端取当前套餐 + 配额 + 使用情况"""
    try:
        u = _get_user_safe(request)
        if not u:
            raise HTTPException(status_code=401, detail="unauthorized")

        user_id = u.get("id")
        plan = _get_plan(user_id)
        features = get_plan_features(plan)

        from core import db as _db

        used = 0
        clients_count = 0
        line_verified = False
        # ocr_history/clients 计数走 RLS 上下文(穿 tenant+user·users 子查询 owner 兜底)。
        with _db.get_cursor_rls(tenant_id=u.get("tenant_id"), user_id=user_id, commit=True) as cur:
            # 取用户详情(包括 LINE 绑定状态)
            cur.execute(
                """
                    SELECT trial_expires_at, plan_expires_at, company_name, email,
                           line_id, line_user_id, line_verified_at, signup_country,
                           is_banned, ban_reason
                    FROM users WHERE id=%s
                """,
                (user_id,),
            )
            row = cur.fetchone()
            if isinstance(row, dict):
                trial_exp = row.get("trial_expires_at")
                plan_exp = row.get("plan_expires_at")
                company = row.get("company_name")
                email = row.get("email")
                line_id = row.get("line_id")
                line_user_id = row.get("line_user_id")
                line_verified_at = row.get("line_verified_at")
                country = row.get("signup_country")
                is_banned = row.get("is_banned")
                ban_reason = row.get("ban_reason")
            elif row:
                (
                    trial_exp,
                    plan_exp,
                    company,
                    email,
                    line_id,
                    line_user_id,
                    line_verified_at,
                    country,
                    is_banned,
                    ban_reason,
                ) = row
            else:
                trial_exp = plan_exp = company = email = None
                line_id = line_user_id = line_verified_at = country = None
                is_banned = False
                ban_reason = None

            line_verified = bool(line_user_id and line_verified_at)

            # 被封停 · 直接报错
            if is_banned:
                raise HTTPException(status_code=403, detail=f"account_banned: {ban_reason or ''}")

            # v111.1 · 去掉 LINE 双轨制 · features 直接用 PLAN_CONFIG · 不再覆盖

            # OCR 用量 · v111.1 trial 也按月统计(以前是累计)
            cur.execute(
                """
                    SELECT COUNT(*) FROM ocr_history
                    WHERE user_id=%s
                      AND date_trunc('month', created_at) = date_trunc('month', NOW())
                """,
                (user_id,),
            )
            used = _row_count(cur.fetchone(), 0)

            # 客户数
            try:
                cur.execute(
                    "SELECT COUNT(*) FROM clients WHERE user_id=%s AND COALESCE(is_active,true)=true",
                    (user_id,),
                )
                clients_count = _row_count(cur.fetchone(), 0)
            except Exception as e:
                logger.warning(f"[admin_user_detail] clients 计数失败: {e}")

        # v111.1 · trial 7 天倒计时
        days_left = None
        if plan == "trial":
            from datetime import datetime, timedelta

            base_exp = trial_exp
            if not base_exp:
                # 没设 trial_expires_at · 用 created_at + 7 天兜底
                created_at_for_calc = u.get("created_at") if isinstance(u, dict) else None
                if created_at_for_calc and isinstance(created_at_for_calc, str):
                    try:
                        created_at_for_calc = datetime.fromisoformat(
                            created_at_for_calc.replace("Z", "+00:00")
                        )
                    except Exception:
                        created_at_for_calc = None
                if created_at_for_calc:
                    base_exp = created_at_for_calc + timedelta(days=7)
            if base_exp:
                delta = base_exp - _now()
                days_left = max(0, int(delta.total_seconds() // 86400))
                if delta.total_seconds() < 86400 and delta.total_seconds() > 0:
                    days_left = round(delta.total_seconds() / 86400, 2)

        # v111.1 · monthly / yearly 剩余天数 · lifetime 永久(返回 -1 标识)
        plan_days_left = None
        if plan == "lifetime":
            plan_days_left = -1  # 前端显示"永久"
        elif plan in ("monthly", "yearly") and plan_exp:
            delta = plan_exp - _now()
            plan_days_left = max(0, int(delta.total_seconds() // 86400))

        return {
            "ok": True,
            "plan": plan,
            "features": features,
            "line_verified": line_verified,
            "needs_line_verify": False,  # v111.1 · 新模型不再依赖 LINE 解锁
            "usage": {
                "ocr_used": used,
                "ocr_limit": features.get("ocr_per_period", 0),
                "clients_used": clients_count,
                "clients_limit": features.get("clients_max", 0),
            },
            # v111.1 · 暴露上传限制(前端 getMaxFiles 用)
            "limits": {
                "max_upload_files": features.get("max_upload_files", 5),
                "max_pages_per_file": features.get("max_pages_per_file", 50),
                "max_mb_per_file": features.get("max_mb_per_file", 100),
            },
            "trial_days_left": days_left,
            "plan_days_left": plan_days_left,
            "trial_expires_at": trial_exp.isoformat() if trial_exp else None,
            "plan_expires_at": plan_exp.isoformat() if plan_exp else None,
            "profile": {
                "company_name": company,
                "email": email,
                "line_id": line_id,
                "country": country,
            },
            "payment_info": {
                "bank": "Kasikorn Bank",
                "bank_th": "ธนาคารกสิกรไทย",
                "account_no": "011-1-83212-9",
                "promptpay": "+66 85-064-2609",
                "line_id": "@Pearnly",
            },
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"get_my_plan failed: {e}")
        raise HTTPException(status_code=500, detail="plan.load_failed")
