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


def _entrance_scope_deny(user: dict, code: str) -> str:
    """入口作用域闸(Phase3 · 各是各的):token.entry 不在码允许的入口集 → 拒。

    码可跨多门共用(entrance_of_code 返集合:sales/purchase/inv/intake={main,pos}、
    tax={main,ai}…)。中性横切码(返 None)短路放行,否则 /api/me 系列 bootstrap 全崩;
    entrance_api_scope 关(默认)= 不拦,现状零变化。返回 deny_reason("" = 放行)。
    """
    from services.auth.entrance import entrance_of_code

    code_entrances = entrance_of_code(code)
    if code_entrances is None:
        return ""
    from core.feature_flags import entrance_api_scope_enabled_for

    if not entrance_api_scope_enabled_for(user.get("tenant_id")):
        return ""
    if (user.get("entry") or "main") not in code_entrances:
        return "entrance_scope"
    return ""


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
    # 入口作用域(各是各的):main 会话 token 打不进 pos/ai 码,反之亦然(闸开时)。超管上面已短路
    # 天然豁免;收银员 entry='pos' 与 pos.* 天然匹配不回归;中性横切码短路放行(见 _entrance_scope_deny)。
    ent_reason = _entrance_scope_deny(user, code)
    if ent_reason:
        return False, ent_reason
    # POS 双令牌主体到这里必已是 role=cashier(typ=pos 由 pos_auth 合成;typ=pos_store
    # 进不了用户鉴权早 401)——不再额外解一次 JWT。
    if user.get("role") == "cashier":
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


def require_perm_pos(request: Request, code: str, err: str = "pos.forbidden") -> dict:
    """POS 信封路由守门:同 require_perm,错误走 PosError 信封。

    err 给模块自有错误码命名空间(purchase.forbidden / acct.forbidden),保住前端
    错误码契约;module_disabled 全模块统一 pos.module_disabled(既有约定)。
    """
    from core.pos_api import PosError, pos_auth

    user = pos_auth(request)
    allowed, reason = _check(request, user, code)
    if allowed:
        return user
    _deny_log(user, code, reason, request)
    if reason == "module_disabled":
        raise PosError("pos.module_disabled", 403)
    raise PosError(err, 403)


def require_perm_tid(request: Request, code: str) -> tuple:
    """require_perm 的 (tenant_id, user_id) 形态(_require_tenant 调用点的机械替换)。"""
    user = require_perm(request, code)
    tid = user.get("tenant_id")
    uid = str(user["id"]) if user.get("id") else None
    return str(tid), uid


def require_perm_pos_tid(request: Request, code: str, err: str = "pos.forbidden") -> tuple:
    """require_perm_pos 的 (tenant_id, user_id) 形态(require_owner 等调用点的机械替换)。"""
    user = require_perm_pos(request, code, err)
    tid = user.get("tenant_id")
    if not tid:
        from core.pos_api import PosError

        raise PosError(err, 403)
    uid = str(user["id"]) if user.get("id") else None
    return str(tid), uid


def actor_has_perm(request: Optional[Request], user: dict, code: str) -> bool:
    """给定主体 dict 是否持某码(不抛,返 bool)。共用 _check 判定核 —— 收银员令牌天然
    只认 CASHIER_CODES(对 pos.refund.approve 恒 False),超管/成员按角色码集判。授权闸等
    需要「先看操作者本人有没有权、没有再走覆盖流」的场景用它,不必 try/except require_perm。"""
    return _check(request, user, code)[0]


def get_authz(request: Optional[Request], user: dict) -> Authz:
    """取当前请求的权限快照(作用域过滤等下游用)。"""
    return _cached_authz(request, user)


def peek_authz(request: Optional[Request]) -> Optional[Authz]:
    """读本请求已缓存的权限快照(require_perm 走过后必有);无 user 不重解。

    字段遮蔽等读侧只需「已判定的这个人能不能看某字段」,不该再触发一次查库;超管短路
    不落快照(返 None),由调用方按超管全可见兜底。"""
    state = getattr(request, "state", None) if request is not None else None
    cached = getattr(state, _STATE_KEY, None) if state is not None else None
    return cached[1] if cached is not None else None


def is_owner_role(request: Optional[Request], user: dict) -> bool:
    """owner 视角判定(计费等 owner 专属读侧)。批5:invited_by IS NULL 语义退役,
    改读 membership 角色;无 tenant 时走存量映射兜底(与 resolver 同口径)。"""
    if user.get("is_super_admin"):
        return True
    if not user.get("tenant_id"):
        from services.authz.resolver import legacy_role_key

        return legacy_role_key(user) == "owner"
    return _cached_authz(request, user).role_key == "owner"


def check_request_scope(
    request: Optional[Request], workspace_client_id, *, pos: bool = False
) -> None:
    """套账解析点的作用域闸(resolve_ws / workspace_context 等 ws 选定处调)。

    优先用本请求已缓存的权限快照;没有(路由还没走 require_perm)则按 Authorization
    懒解一次普通用户(POS 双令牌/匿名直接跳过——它们各有自含校验)。scope_mode='all'
    与超管零额外开销。未分配 → 404 防枚举。
    """
    if request is None or workspace_client_id is None:
        return
    state = getattr(request, "state", None)
    cached = getattr(state, _STATE_KEY, None) if state is not None else None
    if cached is None:
        if _pos_token_payload(request) is not None:
            return
        from core.auth import get_current_user_from_request

        try:
            user = get_current_user_from_request(request)
        except Exception:
            return
        if user.get("is_super_admin") or user.get("role") == "cashier":
            return
        authz = _cached_authz(request, user)
    else:
        authz = cached[1]
        user = {"id": cached[0]}
    _assert_scope(request, user, authz, workspace_client_id, pos)


def check_workspace_scope(
    request: Optional[Request], user: dict, workspace_client_id, *, pos: bool = False
) -> None:
    """第 5 步作用域:scope_mode='assigned' 且套账未分配 → 404(防 IDOR 枚举)。

    超管/收银员令牌(自含 workspace 声明)不查。带 workspace 维度的路由在解析出
    套账 id 后调用;scope_mode='all' 成员零开销直接过。
    """
    if user.get("is_super_admin") or user.get("role") == "cashier":
        return
    _assert_scope(request, user, _cached_authz(request, user), workspace_client_id, pos)


def _assert_scope(request, user: dict, authz: Authz, workspace_client_id, pos: bool) -> None:
    if authz.allows_workspace(workspace_client_id):
        return
    _deny_log(user, f"workspace:{workspace_client_id}", "scope_not_assigned", request)
    if pos:
        from core.pos_api import PosError

        raise PosError("pos.not_found", 404)
    raise HTTPException(404, detail="authz.not_found")
