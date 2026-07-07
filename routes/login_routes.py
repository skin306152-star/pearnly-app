"""
login_routes.py · 主登录路由 + 失败锁定 + 模型(REFACTOR-B1)

从 app.py L1274-1500 抽出 · 0 业务逻辑改:
    POST /api/login   主登录 · 失败 5/30min 锁 · 5 道校验(密码/激活/过期)+ JWT 签发

包含:
    - LoginRequest / LoginResponse Pydantic 模型(v0.17 remember_me + v109.3.2 remember 别名)
    - _record_login_failure 内部 helper(写 login_failure_log · 锁定逻辑用)
    - login 路由本体:
        - v109.3.2 同邮箱 5 次/30min → 429 account_locked
        - 用户名查找 / 密码校验 / is_active / expires_at
        - 成功登录:db.update_last_login + create_access_token + 清失败日志
        - 返回 {token, access_token, user, is_super_admin}

E2E 闸:spec 01(登录地基)+ spec 13(改密)+ spec 15(session 互踢)兜底。
"""

from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from core import db
from core.auth import create_access_token, revoke_current_token, verify_password

logger = logging.getLogger(__name__)

router = APIRouter()


class LoginRequest(BaseModel):
    username: str = Field(..., min_length=1, max_length=100)
    password: str = Field(..., min_length=1, max_length=200)
    # v0.17 · "记住我" · True 则 token 30 天有效 · 默认 7 天
    remember_me: bool = False
    # v109.3.2 · 兼容前端简写
    remember: Optional[bool] = None

    def is_remember(self) -> bool:
        if self.remember is not None:
            return bool(self.remember)
        return bool(self.remember_me)


class LoginResponse(BaseModel):
    token: str
    user: dict


def _record_login_failure(username: str, request: Request):
    """记录登录失败 · 用于锁定逻辑(commit=True 必需:不落库则 30min 计数恒 0 · 账号锁失效)"""
    try:
        ip = request.client.host if request.client else None
        ua = request.headers.get("user-agent", "")[:200]
        with db.get_cursor(commit=True) as cur:
            cur.execute(
                """
                INSERT INTO login_failure_log(email_or_username, ip, user_agent)
                VALUES (%s, %s, %s)
            """,
                (username.lower().strip(), ip, ua),
            )
    except Exception as e:
        logger.warning(f"login fail log skip: {e}")


@router.post("/api/login", response_model=LoginResponse)
async def login(req: LoginRequest, request: Request):
    # v109.3.2 · 登录失败次数检查(同邮箱 5 次/30 分钟)
    try:
        with db.get_cursor() as cur:
            cur.execute(
                """
                SELECT COUNT(*) AS n FROM login_failure_log
                WHERE email_or_username = %s
                  AND created_at > NOW() - INTERVAL '30 minutes'
            """,
                (req.username.lower().strip(),),
            )
            row = cur.fetchone()
            n = row.get("n") if isinstance(row, dict) else (row[0] if row else 0)
            if n and int(n) >= 5:
                raise HTTPException(429, detail="account_locked")
    except HTTPException:
        raise
    except Exception:
        # 表不存在等情况 · 不阻塞登录
        pass

    user = db.find_user_by_username(req.username)
    if not user:
        _record_login_failure(req.username, request)
        raise HTTPException(401, detail="auth.invalid_credentials")

    if not verify_password(req.password, user["password_hash"]):
        _record_login_failure(req.username, request)
        raise HTTPException(401, detail="auth.invalid_credentials")

    if not user.get("is_active", True):
        raise HTTPException(403, detail="auth.account_disabled")

    from datetime import datetime, timezone

    if user.get("expires_at"):
        try:
            exp = user["expires_at"]
            exp_dt = (
                exp
                if hasattr(exp, "tzinfo")
                else datetime.fromisoformat(str(exp).replace("Z", "+00:00"))
            )
            if exp_dt < datetime.now(timezone.utc):
                raise HTTPException(403, detail="auth.account_expired")
        except HTTPException:
            raise
        except Exception as e:
            logger.warning(f"[auth] 校验账户过期失败: {e}")

    db.update_last_login(str(user["id"]))
    # v118.11 · plan=NULL 防御兜底 · 防止 token payload 含 None 导致后续验证异常
    _safe_plan = user.get("plan") or "free"
    token = create_access_token(
        user_id=str(user["id"]),
        username=user["username"],
        plan=_safe_plan,
        tenant_id=str(user["tenant_id"]) if user.get("tenant_id") else None,
        role=user.get("role") or "owner",
        is_super_admin=bool(user.get("is_super_admin")),
        remember_me=req.is_remember(),
    )
    # 登录成功 · 清空失败记录(commit=True:清除也要落库,否则下次仍按旧失败数误锁)
    try:
        with db.get_cursor(commit=True) as cur:
            cur.execute(
                "DELETE FROM login_failure_log WHERE email_or_username = %s",
                (req.username.lower().strip(),),
            )
    except Exception as e:
        logger.warning(f"[login] 清理失败日志失败: {e}")

    # 返回 · 同时提供 token 和 access_token 两个键(向前兼容)
    # POS PO-B1 · 带 role 让前端落地分流(role=cashier → /pos)
    user_info = {
        "id": str(user["id"]),
        "username": user["username"],
        "plan": user["plan"],
        "role": user.get("role") or "owner",
    }
    return JSONResponse(
        {
            "token": token,
            "access_token": token,
            "user": user_info,
            "is_super_admin": bool(user.get("is_super_admin")),
        }
    )


@router.post("/api/logout")
async def logout(request: Request):
    revoke_current_token(request)
    return {"ok": True}


@router.post("/api/auth/logout")
async def auth_logout(request: Request):
    return await logout(request)
