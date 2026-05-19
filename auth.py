# -*- coding: utf-8 -*-
"""
Mr.Pearnly · 认证模块
- bcrypt 密码验证
- JWT 令牌生成和验证
- v118.28.9 · 改密后旧 JWT 失效(token.iat < user.password_changed_at → 401)
"""

import os
import uuid
import logging
import bcrypt
import jwt
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from fastapi import HTTPException, Request, status

logger = logging.getLogger(__name__)

JWT_ALGORITHM = "HS256"
JWT_EXPIRE_DAYS = 7
JWT_REMEMBER_DAYS = 30   # v0.17 · 勾选"记住我"时的长有效期


def _jwt_secret() -> str:
    s = os.environ.get("JWT_SECRET", "").strip()
    if not s or len(s) < 16:
        raise RuntimeError("JWT_SECRET 未设置或长度过短(至少 16 字符)")
    return s


def verify_password(plain_password: str, password_hash: str) -> bool:
    """验证密码"""
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"),
            password_hash.encode("utf-8"),
        )
    except Exception as e:
        logger.error(f"密码验证异常: {e}")
        return False


def create_access_token(
    user_id: str,
    username: str,
    plan: str,
    tenant_id: Optional[str] = None,
    role: str = "owner",
    is_super_admin: bool = False,
    remember_me: bool = False,
) -> str:
    """生成 JWT 令牌
    remember_me=True → 有效期 30 天(v0.17 · "记住我" 勾选时)
    remember_me=False → 默认 7 天

    v22 多租户 · 新增字段:
    - tenant_id:租户 id(数据隔离)
    - role:owner / member
    - is_super_admin:超级管理员标志
    """
    days = JWT_REMEMBER_DAYS if remember_me else JWT_EXPIRE_DAYS
    # v118.32.5.5.10 · 1 账号 1 设备:每次签发新 jti · 注册为 active_jti · 旧 jti 自动失效
    jti = str(uuid.uuid4())
    payload = {
        "sub": user_id,
        "jti": jti,
        "username": username,
        "plan": plan,
        "tenant_id": tenant_id,
        "role": role,
        "is_super_admin": is_super_admin,
        "iat": datetime.now(timezone.utc),
        "exp": datetime.now(timezone.utc) + timedelta(days=days),
    }
    token = jwt.encode(payload, _jwt_secret(), algorithm=JWT_ALGORITHM)
    # 写入 users.active_jti(失败不阻塞登录 · 老用户兼容)
    try:
        import db as _db
        with _db.get_cursor(commit=True) as cur:
            cur.execute("UPDATE users SET active_jti=%s WHERE id=%s", (jti, user_id))
        logger.info(f"[session] new login · user={user_id} jti={jti[:8]}...")
    except Exception as e:
        logger.warning(f"[session] set active_jti failed (non-blocking): {e}")
    return token


def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    """解码 JWT 令牌"""
    try:
        return jwt.decode(token, _jwt_secret(), algorithms=[JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        logger.info("JWT 已过期")
        return None
    except jwt.InvalidTokenError as e:
        logger.info(f"JWT 无效: {e}")
        return None


def get_current_user_from_request(request: Request) -> Dict[str, Any]:
    """
    FastAPI 依赖:从请求头的 Authorization Bearer Token 中获取用户
    失败返回 401
    错误码用字符串,前端自己翻译成 4 语言
    """
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="auth.missing_token",
        )

    token = auth[7:].strip()
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="auth.invalid_token",
        )

    # 从 DB 查最新的用户信息(防止 JWT 过期后权限还有效)
    from db import find_user_by_id
    user = find_user_by_id(payload["sub"])
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="auth.user_not_found",
        )
    if not user.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="auth.account_disabled",
        )

    # ============================================================
    # v118.28.9 · 改密后旧 JWT 失效
    # 规则:JWT 签发时间 (iat) 早于 用户最后改密时间 (password_changed_at) → 401
    # 用户改密后,所有旧设备 / 旧标签页的 token 立即作废
    # 异常时放行(避免列缺失导致全员被踢的灾难)
    # ============================================================
    try:
        iat = payload.get("iat")
        pwd_at = user.get("password_changed_at")
        if iat is not None and pwd_at is not None:
            # PyJWT 解码后 iat 是 int (unix timestamp);pwd_at 是 datetime
            if hasattr(pwd_at, "timestamp"):
                pwd_ts = int(pwd_at.timestamp())
            else:
                # 兜底:字符串 ISO 格式
                pwd_ts = int(
                    datetime.fromisoformat(
                        str(pwd_at).replace("Z", "+00:00")
                    ).timestamp()
                )
            if int(iat) < pwd_ts:
                logger.info(
                    f"[v118.28.9] token 被改密事件作废 · user={user.get('id')} "
                    f"iat={iat} pwd_at={pwd_ts}"
                )
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="auth.password_changed_relogin",
                )
    except HTTPException:
        raise
    except Exception as _e:
        logger.warning(f"[v118.28.9] password_changed_at 比对异常 · 放行: {_e}")

    # ============================================================
    # v118.32.5.5.10 · 1 账号 1 设备 session 控制
    # 规则:JWT.jti 必须 == users.active_jti · 不等 = 旧设备 → 401
    # 老 token(无 jti)或老用户(无 active_jti)= 兼容放行 · 下次登录自动迁移
    # ============================================================
    try:
        token_jti = payload.get("jti")
        user_active_jti = user.get("active_jti")
        if token_jti and user_active_jti and token_jti != user_active_jti:
            logger.info(
                f"[session] revoked · user={user.get('id')} "
                f"token_jti={token_jti[:8]}... active={user_active_jti[:8]}..."
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="auth.session_revoked",
            )
    except HTTPException:
        raise
    except Exception as _e:
        logger.warning(f"[session] jti 比对异常 · 放行: {_e}")

    # ============================================================
    # Task 3 · active_tenant_id 优先于 JWT.tenant_id
    #   多公司用户切换公司时只更新 users.active_tenant_id
    #   不动 JWT · 业务逻辑统一从 user["tenant_id"] 读
    # ============================================================
    try:
        active_tid = user.get("active_tenant_id")
        if active_tid:
            user["_jwt_tenant_id"] = user.get("tenant_id")
            user["tenant_id"] = active_tid
    except Exception as _e:
        logger.warning(f"[active_tenant] override skip: {_e}")

    return user


def get_client_ip(request: Request) -> str:
    """
    获取客户端真实 IP
    Hugging Face Space 会通过 X-Forwarded-For 传递
    """
    xff = request.headers.get("X-Forwarded-For", "")
    if xff:
        return xff.split(",")[0].strip()
    real_ip = request.headers.get("X-Real-IP", "")
    if real_ip:
        return real_ip.strip()
    if request.client:
        return request.client.host
    return "unknown"
