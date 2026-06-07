# -*- coding: utf-8 -*-
"""
Pearnly · 认证模块
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
JWT_REMEMBER_DAYS = 30  # v0.17 · 勾选"记住我"时的长有效期
POS_TOKEN_TTL_HOURS = 12  # POS 收银员 token 有效期(离线缓存窗口 · docs/pos/04 §1)
POS_STORE_TOKEN_TTL_DAYS = 365  # 设备店铺令牌(绑定一次长期用 · docs/pos/04 §1b)


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
        from core import db as _db

        with _db.get_cursor(commit=True) as cur:
            cur.execute("UPDATE users SET active_jti=%s WHERE id=%s", (jti, user_id))
        logger.info(f"[session] new login · user={user_id} jti={jti[:8]}...")
    except Exception as e:
        logger.warning(f"[session] set active_jti failed (non-blocking): {e}")
    return token


def create_pos_token(
    *,
    tenant_id: str,
    workspace_client_id: int,
    cashier_id: str,
    display_name: str,
    ttl_hours: int = POS_TOKEN_TTL_HOURS,
) -> tuple[str, int]:
    """POS 收银员 token(PIN 登录签发 · docs/pos/04 §1)。

    自含 tenant/workspace/cashier 声明,typ='pos',role='cashier'。**不查 users 表、不写
    active_jti**——收银员未必有正式账号,且 token 须支撑离线(get_current_user 的 DB 校验不可用)。
    校验侧走 core.pos_api.pos_auth(按 typ 分流);因无 users 行,POS token 进 /home 接口必 401。
    返回 (token, ttl_hours)。
    """
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(cashier_id),
        "typ": "pos",
        "role": "cashier",
        "tenant_id": str(tenant_id),
        "workspace_client_id": int(workspace_client_id),
        "cashier_id": str(cashier_id),
        "display_name": display_name,
        "iat": now,
        "exp": now + timedelta(hours=ttl_hours),
    }
    return jwt.encode(payload, _jwt_secret(), algorithm=JWT_ALGORITHM), ttl_hours


def create_pos_store_token(
    *,
    tenant_id: str,
    workspace_client_id: int,
    version: int,
    ttl_days: int = POS_STORE_TOKEN_TTL_DAYS,
) -> str:
    """设备店铺令牌(扫店铺码绑定时签发 · docs/pos/04 §1b)。

    typ='pos_store',自含 tenant/workspace + token 版本 ver。能力仅"列本店收银员 / 验 PIN / 卖货",
    **不是收银员 token、更不是老板 token**——设备丢了碰不到会计/财务。老板「重置店铺码」= 库里 bump
    token_version,旧令牌 ver 对不上即失效(校验侧 store_binding.current_version 比对)。长期有效。
    """
    now = datetime.now(timezone.utc)
    payload = {
        "sub": f"store:{int(workspace_client_id)}",
        "typ": "pos_store",
        "tenant_id": str(tenant_id),
        "workspace_client_id": int(workspace_client_id),
        "ver": int(version),
        "iat": now,
        "exp": now + timedelta(days=ttl_days),
    }
    return jwt.encode(payload, _jwt_secret(), algorithm=JWT_ALGORITHM)


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
    from core.db import find_user_by_id

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
                pwd_ts = int(datetime.fromisoformat(str(pwd_at).replace("Z", "+00:00")).timestamp())
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
    # v118.35.0.6 · multi-company · active_tenant_id 优先于 JWT.tenant_id
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

    # REFACTOR-WA-B6 part2 · 鉴权成功后绑定日志上下文(本请求后续日志带 user/tenant)·
    # 纯加观测 0 逻辑改 · try 兜底确保绝不影响鉴权结果(日志失败不能踢用户)
    try:
        from services.observability import log_context

        log_context.bind(user_id=user.get("id"), tenant_id=user.get("tenant_id"))
    except Exception:  # noqa: BLE001 · 观测绝不阻断鉴权
        pass

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
