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
from fastapi.responses import JSONResponse


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


def register_pos_error_handler(app) -> None:
    """app 启动时注册 · 让 PosError 渲染成信封。只挂新异常类型,不碰现有处理器。"""
    app.add_exception_handler(PosError, _pos_error_handler)


def pos_auth(request: Request) -> dict:
    """取当前用户;鉴权失败转成 PosError(信封),保留原 auth.* code 给前端映射。"""
    from core.auth import get_current_user_from_request

    try:
        return get_current_user_from_request(request)
    except HTTPException as exc:
        raise PosError(str(exc.detail), exc.status_code) from exc


def require_tenant(request: Request) -> tuple[str, Optional[str]]:
    """取 (tenant_id, user_id);无 tenant → PosError pos.forbidden(403)。"""
    user = pos_auth(request)
    tid = user.get("tenant_id") if user else None
    if not tid:
        raise PosError("pos.forbidden", 403)
    uid = str(user["id"]) if user and user.get("id") else None
    return str(tid), uid


def assert_module_enabled(tenant_id: str, module_key: str) -> None:
    """模块未开 → PosError pos.module_disabled(403)。POS/库存写接口入口调。"""
    from core import db
    from services.modules import store

    with db.get_cursor_rls(tenant_id) as cur:
        if not store.is_enabled(cur, tenant_id=tenant_id, module_key=module_key):
            raise PosError("pos.module_disabled", 403)
