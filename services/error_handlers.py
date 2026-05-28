# -*- coding: utf-8 -*-
"""
Pearnly · 全局异常处理(REFACTOR-WA-B1 · 2026-05-29 从 app.py 抽出)

纯搬家 · 0 逻辑改 · app.py 留瘦 @app.exception_handler(Exception) 壳:
    @app.exception_handler(Exception)
    async def _capture_unhandled_500(request, exc):
        return await handle_unhandled_exception(request, exc)

handle_unhandled_exception:服务端记录完整 traceback(_record_500 + logger.exception)·
客户端只收稳定错误码 server.internal_error(不回传异常类型/text/diag_url · P0-03 安全脱敏)·
内部诊断走超管接口 /api/admin/diagnostics/runtime。
"""

import logging

from route_helpers import _record_500

logger = logging.getLogger("mr-pilot")


async def handle_unhandled_exception(request, exc):
    """v118.35.0.28 安全脱敏 (P0-03 体检 2026-05-21)
    服务端仍记录完整 traceback (_record_500 + logger.exception) ·
    但客户端只收到稳定错误码 · 不再回传异常类型/text/diag_url ·
    内部诊断由超管接口 /api/admin/diagnostics/runtime 提供"""
    from fastapi.responses import JSONResponse

    try:
        _record_500(
            path=str(request.url.path),
            method=request.method,
            detail=f"unhandled {type(exc).__name__}: {str(exc)[:200]}",
        )
    except Exception:
        pass
    logger.exception(
        "[capture-500] %s %s · %s",
        request.method,
        request.url.path,
        type(exc).__name__,
    )
    return JSONResponse(
        status_code=500,
        content={"detail": "server.internal_error"},
    )
