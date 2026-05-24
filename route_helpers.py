# -*- coding: utf-8 -*-
"""
Pearnly · 路由公共 helper 模块(REFACTOR-B1 · 2026-05-24 抽出)

把散在 app.py 里、被多个路由组共用的鉴权 / 日志 / 校验 helper 集中到这里 ·
让后续抽 team / history / admin 等 router 时直接 import · 不再各自复制一份。

纯搬家 · 不改业务逻辑 / 返回值 / 异常 code。app.py 与已抽出的
billing_routes / admin_diagnostics_routes 改成从这里 import(去掉各自的拷贝)。

依赖:
  - db.*(insert_operation_log / create_tenant / get_cursor)
  - auth.get_current_user_from_request
  不 import app.py · 防循环 import。

覆盖:
  _require_super_admin       · 超管守门(非超管 403)
  _require_owner_or_super    · 老板或超管(含懒建 tenant 兜底)
  _log_op                    · 写操作日志便捷函数
  _get_client_ip             · 从 X-Forwarded-For / client.host 取真实 IP
  _check_password_strength   · 密码强度校验(返 None 通过 / code 拒绝)
  _WEAK_PASSWORDS            · 常见弱密码黑名单
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from fastapi import HTTPException, Request, status

import db
from auth import get_current_user_from_request

logger = logging.getLogger("mr-pilot")


def _require_super_admin(request: Request) -> Dict[str, Any]:
    """超级管理员守门员 · 非超管 403"""
    user = get_current_user_from_request(request)
    if not user.get("is_super_admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="admin.not_super_admin",
        )
    return user


def _get_client_ip(request):
    xff = request.headers.get("X-Forwarded-For", "")
    if xff:
        return xff.split(",")[0].strip()
    return request.client.host if request.client else None


def _log_op(
    request: Request, user, action, target_type=None, target_id=None, target_name=None, details=None
):
    """记操作日志的便捷函数"""
    try:
        db.insert_operation_log(
            tenant_id=str(user["tenant_id"]) if user.get("tenant_id") else None,
            actor_user_id=str(user["id"]),
            actor_username=user.get("username"),
            actor_is_super=bool(user.get("is_super_admin")),
            action=action,
            target_type=target_type,
            target_id=target_id,
            target_name=target_name,
            details=details,
            ip=_get_client_ip(request),
            ua=request.headers.get("User-Agent", "")[:300],
        )
    except Exception as e:
        logger.warning(f"_log_op failed: {e}")


_WEAK_PASSWORDS = {
    "111111",
    "112233",
    "121212",
    "123123",
    "123321",
    "123456",
    "1234567",
    "12345678",
    "123456789",
    "1234567890",
    "131313",
    "147258",
    "159753",
    "654321",
    "666666",
    "888888",
    "987654",
    "abc123",
    "abcd1234",
    "admin",
    "admin123",
    "iloveyou",
    "letmein",
    "monkey",
    "password",
    "password1",
    "password123",
    "qazwsx",
    "qwerty",
    "qwerty123",
    "qwertyuiop",
    "welcome",
    "zxcvbnm",
}


def _check_password_strength(password: str) -> Optional[str]:
    """
    返回 None 表示通过 · 返回错误 code 表示拒绝
    code: pwd.too_short / pwd.too_weak_numeric / pwd.too_weak_common / pwd.too_weak
    """
    if not password or len(password) < 8:
        return "pwd.too_short"
    if password.lower() in _WEAK_PASSWORDS:
        return "pwd.too_weak_common"
    if password.isdigit():
        return "pwd.too_weak_numeric"
    has_letter = any(c.isalpha() for c in password)
    has_digit = any(c.isdigit() for c in password)
    if not (has_letter and has_digit):
        return "pwd.too_weak"
    return None


def _require_owner_or_super(request: Request) -> Dict[str, Any]:
    """老板或超管
    v118.26.2.4 · BUG 4 修补:新注册老板 tenant_id=NULL · 加员工时被拒
    懒建模式:首次需要 tenant 时自动建一个 + 回填 user.tenant_id · 不影响新签名 API
    """
    user = get_current_user_from_request(request)
    if user.get("is_super_admin"):
        return user
    if user.get("role") != "owner":
        raise HTTPException(403, detail="team.only_owner_or_super")
    if not user.get("tenant_id"):
        # v118.26.2.4 · 懒建 tenant · 只在首次需要时
        try:
            tenant_name = (
                user.get("company_name")
                or user.get("full_name")
                or user.get("username")
                or f"user_{str(user['id'])[:8]}"
            )[:100]
            new_tid = db.create_tenant(
                name=tenant_name,
                owner_user_id=str(user["id"]),
                tenant_type="shared_api",
                monthly_quota=100,
                notes="auto-created on first owner action",
            )
            if new_tid:
                with db.get_cursor(commit=True) as _cur:
                    _cur.execute(
                        "UPDATE users SET tenant_id = %s WHERE id = %s AND tenant_id IS NULL",
                        (new_tid, str(user["id"])),
                    )
                user["tenant_id"] = new_tid
                logger.info(
                    f"[v118.26.2.4 lazy-tenant] +tenant {new_tid[:8]}.. for user {user.get('username')!r}"
                )
        except Exception as _e:
            logger.error(f"_require_owner_or_super lazy-tenant fail: {_e}")
            raise HTTPException(500, detail="team.tenant_create_failed")
        if not user.get("tenant_id"):
            raise HTTPException(400, detail="team.no_tenant")
    return user
