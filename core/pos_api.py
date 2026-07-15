# -*- coding: utf-8 -*-
"""POS/库存接口公共层 — 统一响应信封 + 错误 + 守卫(POS 项目 · docs/pos/04 §0)。

为什么独立一层(治销项血泪「字段读错 body.data / 裸错误码」):
  POS 全部接口只用一种信封——成功 {"ok": true, "data": {...}},失败
  {"ok": false, "error": {"code": "...", "message_key": "..."}}。前端先看 ok 再读
  data/error.code,不靠 HTTP 码判业务成败,也不裸读顶层字段。

用法(POS/库存路由):
  - 成功:`return ok({...})`
  - 业务失败:`raise PosError("pos.out_of_stock", 409, detail="...")`
  - 取用户:`user = pos_auth(request)`(鉴权失败也转成信封,不漏 FastAPI 默认 {detail}）
  - 模块守门:`assert_module_enabled(tenant_id, "pos")`(关→pos.module_disabled）

PosError 经 register_pos_error_handler() 注册的处理器渲染成信封;不动任何现有
HTTPException 行为(只认新异常类型),避免影响共用登录/其它路由。
"""

from __future__ import annotations

from typing import Any, Optional

from fastapi import HTTPException, Request
from fastapi.exception_handlers import request_validation_exception_handler
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from core import db

# POS/库存/模块接口前缀:这些路径的请求体校验错误也要走信封(其余路由保持 FastAPI 默认)。
# /api/me/modules 既匹配 GET(精确)也匹配 toggle 子路径(/api/me/modules/{key} 走前缀)。
_POS_PREFIXES = (
    "/api/inventory",
    "/api/pos",
    "/api/me/modules",
    "/api/purchase",
    "/api/accounting",
    "/api/summary-import",
)
_POS_EXACT = ("/api/me/onboarding",)

# 请求体校验错误的模块错误码(按前缀取首个命中;未列 → pos.line_invalid)。新模块加一行即可。
_VALIDATION_CODES = {
    "/api/purchase": "purchase.line_invalid",
    "/api/accounting": "acct.unexpected",
    "/api/summary-import": "purchase.line_invalid",
}


def ok(data: Optional[dict] = None) -> dict:
    """成功信封。data 缺省为空对象(前端永远能安全读 body.data）。"""
    return {"ok": True, "data": data if data is not None else {}}


class PosError(Exception):
    """POS 业务错误 · 渲染成 {"ok": false, "error": {...}} + 对应 HTTP 码。

    code:06 错误码字典里的 key(前端映射 4 语,绝不裸露)。
    http_status:对应 HTTP(默认 400)。
    detail:可选调试串(如 out_of_stock 缺哪个品),前端可拼进文案,不作主文案。
    """

    def __init__(self, code: str, http_status: int = 400, detail: Optional[str] = None):
        super().__init__(code)
        self.code = code
        self.http_status = http_status
        self.detail = detail


def _error_body(code: str, detail: Optional[str] = None) -> dict:
    body: dict[str, Any] = {"ok": False, "error": {"code": code, "message_key": code}}
    if detail:
        body["error"]["detail"] = detail
    return body


async def _pos_error_handler(request: Request, exc: PosError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.http_status,
        content=_error_body(exc.code, exc.detail),
    )


def _is_pos_path(request: Request) -> bool:
    path = str(request.url.path or "")
    return path.startswith(_POS_PREFIXES) or path in _POS_EXACT


async def _pos_validation_handler(request: Request, exc: RequestValidationError):
    """POS/库存路径的请求体校验错误 → 信封(pos.line_invalid);其余路由走 FastAPI 默认。

    FastAPI 的请求体校验在路由函数执行前触发,不经 PosError;不接管的话 POS 前端会收到
    默认 {detail:[...]} 而非信封(读 body.error.code 失败)。这里按路径前缀只接管 POS。
    """
    if _is_pos_path(request):
        path = str(request.url.path or "")
        code = next(
            (c for p, c in _VALIDATION_CODES.items() if path.startswith(p)), "pos.line_invalid"
        )
        return JSONResponse(status_code=422, content=_error_body(code, "invalid_request_body"))
    return await request_validation_exception_handler(request, exc)


def register_pos_error_handler(app) -> None:
    """app 启动时注册:PosError → 信封;POS 路径的请求体校验错误 → 信封。

    PosError 是新异常类型(不碰现有处理器)。RequestValidationError 处理器对非 POS 路径委托
    回 FastAPI 默认实现,行为不变。
    """
    app.add_exception_handler(PosError, _pos_error_handler)
    app.add_exception_handler(RequestValidationError, _pos_validation_handler)


def pos_auth(request: Request) -> dict:
    """取当前主体;鉴权失败转成 PosError(信封),保留原 auth.* code 给前端映射。

    两种 token 分流:
      - POS 收银员 token(typ='pos'):自含 tenant/workspace/cashier 声明,合成主体直接返回
        (不查 users · 支撑离线)。形如普通 user dict + workspace_client_id/cashier_id。
      - 其余(老板/会计/超管):走 get_current_user_from_request(查 users + session 校验)。
    """
    cashier = _pos_token_subject(request)
    if cashier is not None:
        return cashier

    from core.auth import get_current_user_from_request

    try:
        return get_current_user_from_request(request)
    except HTTPException as exc:
        raise PosError(str(exc.detail), exc.status_code) from exc


def _pos_token_subject(request: Request) -> Optional[dict]:
    """Bearer 是 POS 收银员 token(typ='pos')→ 合成主体;否则 None(交给普通用户鉴权)。"""
    from core.auth import decode_access_token

    headers = getattr(request, "headers", None)
    auth = headers.get("Authorization", "") if headers else ""
    if not auth.startswith("Bearer "):
        return None
    payload = decode_access_token(auth[7:].strip())
    if not payload or payload.get("typ") != "pos":
        return None
    return {
        "id": payload.get("cashier_id"),
        "tenant_id": payload.get("tenant_id"),
        "workspace_client_id": payload.get("workspace_client_id"),
        "cashier_id": payload.get("cashier_id"),
        "display_name": payload.get("display_name"),
        "role": "cashier",
        "is_super_admin": False,
        "entry": "pos",  # 收银员会话天然属 pos 入口(Phase3 API 作用域按此归类)
    }


def require_tenant(request: Request) -> tuple[str, Optional[str]]:
    """取 (tenant_id, user_id);无 tenant → PosError pos.forbidden(403)。"""
    user = pos_auth(request)
    tid = user.get("tenant_id") if user else None
    if not tid:
        raise PosError("pos.forbidden", 403)
    uid = str(user["id"]) if user and user.get("id") else None
    return str(tid), uid


def require_workspace(cur, tenant_id: str, workspace_client_id: int) -> None:
    """账套归属校验:workspace_client_id 必属本租户,否则 pos.forbidden(403)。用调用方游标。"""
    cur.execute(
        "SELECT 1 FROM workspace_clients WHERE id = %s AND tenant_id = %s",
        (workspace_client_id, tenant_id),
    )
    if not cur.fetchone():
        raise PosError("pos.forbidden", 403)


def assert_module_enabled(cur, tenant_id: str, module_key: str) -> None:
    """模块未开 → PosError pos.module_disabled(403)。用调用方已开的游标(不另起连接)。"""
    from services.modules import store

    if not store.is_enabled(cur, tenant_id=tenant_id, module_key=module_key):
        raise PosError("pos.module_disabled", 403)


def subject(request: Request, permission: str = "pos.sale.operate") -> tuple[dict, str]:
    """取 (user, tenant_id);无 tenant → PosError pos.forbidden(403)。写事务信封的第一步。"""
    from services.authz.deps import require_perm_pos

    user = require_perm_pos(request, permission)
    tid = user.get("tenant_id")
    if not tid:
        raise PosError("pos.forbidden", 403)
    return user, str(tid)


def require_workspace_access(
    cur, request: Request, tenant_id: str, workspace_client_id: int
) -> None:
    """Verify tenant ownership and the platform member's assigned workspace scope."""
    from services.authz.deps import check_request_scope

    require_workspace(cur, tenant_id, workspace_client_id)
    check_request_scope(request, workspace_client_id, pos=True)


def resolve_ws(user: dict, override: Optional[int]) -> int:
    """定位账套:收银员 token 自带 workspace_client_id,老板调走 override;都无 → pos.forbidden。"""
    token_ws = user.get("workspace_client_id")
    if token_ws is not None and override is not None and int(token_ws) != int(override):
        raise PosError("pos.forbidden", 403)
    ws = token_ws or override
    if ws is None:
        raise PosError("pos.forbidden", 403)
    return int(ws)


def pos_write(
    request: Request,
    *,
    ws_override: Optional[int],
    write_fn,
    module_key: str = "pos",
    permission: str = "pos.sale.operate",
    before_write=None,
    after_commit=None,
) -> dict:
    """POS 写事务信封 · 单一事实源(治「路由与授权层各持一份租户隔离+模块闸副本必漂移」)。

    鉴权 → 账套定位 → 单事务(get_cursor_rls commit=True)内:模块闸 + 账套归属 + 可选写前钩子
    + write_fn 原子写。租户隔离与模块闸是安全边界,只此一处,任何 POS 写都过同一道门。

      - before_write(cur, ctx):可选,在同一事务游标里跑(如退货授权闸),ctx 带 user/tenant/ws。
      - write_fn(cur, tid, ws, user):真正的写,返回业务结果。
      - after_commit(result, ctx):可选,事务提交【后】跑(如审计须独立连接、不随退货回滚)。

    返回 ok(result)。
    """
    user, tid = subject(request, permission)
    ws = resolve_ws(user, ws_override)
    ctx = {"user": user, "tenant_id": tid, "workspace_client_id": ws}
    with db.get_cursor_rls(tid, commit=True) as cur:
        assert_module_enabled(cur, tid, module_key)
        require_workspace_access(cur, request, tid, ws)
        if before_write is not None:
            before_write(cur, ctx)
        result = write_fn(cur, tid, ws, user)
    if after_commit is not None:
        after_commit(result, ctx)
    return ok(result)
