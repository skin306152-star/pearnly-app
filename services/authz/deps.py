# -*- coding: utf-8 -*-
"""require_perm 统一执行点(docs/permissions/03 · OWASP deny-by-default)。

判定顺序(单点 · 路由不得自己写 if role):
  1. 超管短路放行(平台层)
  2. POS 双令牌(typ=pos/pos_store)只认收银码集,其余一律 403
  3. 模块联动:码所属模块在 tenant_modules 关闭 → 403 module_disabled
  4. 角色码集含码(或 all)→ 过,否则 403 forbidden
  5. 作用域:带 workspace 维度的路由再调 check_workspace_scope(未分配 → 404 防枚举)

两个入口同逻辑不同错误形态:require_perm 抛 HTTPException(主程序路由),
require_perm_pos 抛 PosError(POS 信封路由)。授权失败记结构化日志可聚合。
"""

from __future__ import annotations

import logging
from typing import Optional

from fastapi import HTTPException, Request

from services.authz.registry import ALL_CODES, CASHIER_CODES, module_of
from services.authz.resolver import Authz, resolve

logger = logging.getLogger("mr-pilot")

_STATE_KEY = "_authz_snapshot"


def _deny_log(user: dict, code: str, reason: str, request: Optional[Request]) -> None:
    logger.info(
        "[authz] deny user=%s tenant=%s code=%s reason=%s path=%s",
        user.get("id"),
        user.get("tenant_id"),
        code,
        reason,
        getattr(getattr(request, "url", None), "path", ""),
    )


def _pos_token_payload(request: Request) -> Optional[dict]:
    """Bearer 是 POS 双令牌(typ=pos/pos_store)→ 返 payload;否则 None。"""
    from core.auth import decode_access_token

    auth = request.headers.get("Authorization", "") if request else ""
    if not auth.startswith("Bearer "):
        return None
    payload = decode_access_token(auth[7:].strip())
    if payload and payload.get("typ") in ("pos", "pos_store"):
        return payload
    return None


def _cached_authz(request: Optional[Request], user: dict, cur=None) -> Authz:
    """同请求多次 require_perm 复用一次 resolve(查库一次)。"""
    state = getattr(request, "state", None) if request is not None else None
    cached = getattr(state, _STATE_KEY, None) if state is not None else None
    if cached is not None and cached[0] == str(user.get("id")):
        return cached[1]
    authz = resolve(user, cur=cur)
    if state is not None:
        setattr(state, _STATE_KEY, (str(user.get("id")), authz))
    return authz


def _module_disabled(user: dict, code: str) -> bool:
    mod = module_of(code)
    if mod is None:
        return False
    from core import db
    from services.modules import store as modules_store

    with db.get_cursor() as cur:
        return not modules_store.is_enabled(cur, tenant_id=str(user["tenant_id"]), module_key=mod)


def _check(request: Request, user: dict, code: str) -> tuple[bool, str]:
    """共用判定核。返回 (allowed, deny_reason)。code 必须在 registry(否则恒拒)。"""
    if code not in ALL_CODES:
        return False, "unknown_code"
    if user.get("is_super_admin"):
        return True, ""
    if user.get("role") == "cashier" or (
        request is not None and _pos_token_payload(request) is not None
    ):
        if code in CASHIER_CODES:
            return True, ""
        return False, "pos_token_out_of_scope"
    if not user.get("tenant_id"):
        return False, "no_tenant"
    if _module_disabled(user, code):
        return False, "module_disabled"
    authz = _cached_authz(request, user)
    if authz.has(code):
        return True, ""
    return False, "forbidden"


def require_perm(request: Request, code: str) -> dict:
    """主程序路由守门:过 → 返 user dict;拒 → 403(authz.forbidden/module_disabled)。"""
    from core.auth import get_current_user_from_request

    user = get_current_user_from_request(request)
    allowed, reason = _check(request, user, code)
    if allowed:
        return user
    _deny_log(user, code, reason, request)
    if reason == "module_disabled":
        raise HTTPException(403, detail="authz.module_disabled")
    raise HTTPException(403, detail="authz.forbidden")


def require_perm_pos(request: Request, code: str) -> dict:
    """POS 信封路由守门:同 require_perm,错误走 PosError 信封。"""
    from core.pos_api import PosError, pos_auth

    user = pos_auth(request)
    allowed, reason = _check(request, user, code)
    if allowed:
        return user
    _deny_log(user, code, reason, request)
    if reason == "module_disabled":
        raise PosError("pos.module_disabled", 403)
    raise PosError("pos.forbidden", 403)


def get_authz(request: Optional[Request], user: dict) -> Authz:
    """取当前请求的权限快照(作用域过滤等下游用)。"""
    return _cached_authz(request, user)


def check_workspace_scope(
    request: Optional[Request], user: dict, workspace_client_id, *, pos: bool = False
) -> None:
    """第 5 步作用域:scope_mode='assigned' 且套账未分配 → 404(防 IDOR 枚举)。

    超管/收银员令牌(自含 workspace 声明)不查。带 workspace 维度的路由在解析出
    套账 id 后调用;scope_mode='all' 成员零开销直接过。
    """
    if user.get("is_super_admin") or user.get("role") == "cashier":
        return
    authz = _cached_authz(request, user)
    if authz.allows_workspace(workspace_client_id):
        return
    _deny_log(user, f"workspace:{workspace_client_id}", "scope_not_assigned", request)
    if pos:
        from core.pos_api import PosError

        raise PosError("pos.not_found", 404)
    raise HTTPException(404, detail="authz.not_found")
