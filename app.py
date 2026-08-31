# -*- coding: utf-8 -*-
"""
Pearnly · FastAPI 主入口 (v3.5)
第 3.5 批:
  - 返回完整权限字段
  - /api/v1/ 路由前缀预留(与旧路径并存)
  - 套餐元数据端点
"""

import os
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

# app.db 命名空间(大量测试 monkeypatch app.db.xxx · 路由经 app.db 调 · 必须保留)
from core import db  # noqa: F401

# 路由清单在 routes/registry.py(本文件只装配应用:lifespan/中间件/异常处理/静态挂载)。
from routes.registry import include_all as include_all_routers

# REFACTOR-B1 · OCR 异常检测链单一来源 re-export(契约 test_exception_checks_contract;
# 实际消费者已搬到 services/ocr/recognize/*，app 自身不再直接调)。
from services.exceptions.exception_checks import _async_run_exception_checks  # noqa: F401
from core.route_helpers import (  # 公共鉴权 helper;app 再导出锁单一来源(契约 test_route_helpers_contract/test_tid_helper_single_source)
    _plan_permissions,  # noqa: F401
    _tid,  # noqa: F401
)
from services.static_assets import read_frontend_version, purge_stale_static_gz  # REFACTOR-WA-B1
from services.erp.auto_push import (  # ERP 自动推送编排;app 再导出锁单一来源(契约 test_auto_push_module_contract)
    _auto_push_history,  # noqa: F401
    _auto_push_smart_routed,  # noqa: F401
    _erp_seller_routing_enabled,  # noqa: F401
)
from services.startup import run_startup, run_shutdown  # REFACTOR-WA-B1
from services.error_handlers import handle_unhandled_exception  # REFACTOR-WA-B1
from core.pos_api import register_pos_error_handler  # POS 信封异常处理 · PO-A1

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass  # dotenv 可选 · 未装则用系统环境变量

# REFACTOR-WA-B6 · 结构化日志(JSON + request_id 全链路)· 替代裸 basicConfig
from services.observability.logging_config import configure_logging

configure_logging()
logger = logging.getLogger("mr-pilot")


# 最近 500 错误现场摘要(_last_500_event / _record_500 / _read_last_500)已搬到
# route_helpers.py(REFACTOR-B1 · 2026-05-25)· app.py 全局异常处理器 import _record_500 ·
# erp_routes 写 / admin_diagnostics 读 都直接 from route_helpers import · 共享同一状态(单例)。


DEMO_IP_DAILY_LIMIT = int(os.environ.get("DEMO_IP_DAILY_LIMIT", "20"))
OCR_MAX_PAGES_PER_UPLOAD = int(os.environ.get("OCR_MAX_PAGES_PER_UPLOAD", "5"))
OCR_MAX_FILE_SIZE_MB = int(os.environ.get("OCR_MAX_FILE_SIZE_MB", "20"))


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动/关闭序列已抽到 services/startup.py(REFACTOR-WA-B1 · 2026-05-29)·
    # app.py 留瘦壳:run_startup 返回后台 task 句柄 · run_shutdown 收尾 cancel。
    tasks = await run_startup()
    yield
    await run_shutdown(tasks)


app = FastAPI(title="Pearnly API", version="0.3.5-mvp", lifespan=lifespan)
include_all_routers(app)  # 全部路由清单见 routes/registry.py(顺序即匹配优先级)

# v118.35.0.28 P0-04 CORS 收紧 (体检 2026-05-21):
# 旧 allow_origins=["*"] + allow_credentials=True 浏览器会自动拒绝凭据请求,
# 但无凭据跨域 fetch 仍放行 · 收紧到生产白名单 + env 覆盖 + dev 自动放 localhost
# 注: 用户从 pearnly.com 访问时 home.js 调 /api/* 是同源, 根本不触发 CORS;
# 收紧只影响第三方域名想跨域调 API 的场景 · 无嵌入式合作伙伴情况下零风险
_cors_default = "https://pearnly.com,https://www.pearnly.com"
_cors_origins_str = (os.environ.get("CORS_ALLOW_ORIGINS") or _cors_default).strip()
_cors_allow_origins = [o.strip() for o in _cors_origins_str.split(",") if o.strip()]
_cors_kwargs = {
    "allow_origins": _cors_allow_origins,
    "allow_credentials": True,
    "allow_methods": ["*"],
    "allow_headers": ["*"],
}
# PEARNLY_ENV=development 时额外放 localhost 任意端口 · 本地开发不会被 CORS 卡
if (os.environ.get("PEARNLY_ENV") or "").strip().lower() == "development":
    _cors_kwargs["allow_origin_regex"] = r"^http://(localhost|127\.0\.0\.1)(:\d+)?$"
app.add_middleware(CORSMiddleware, **_cors_kwargs)

# REFACTOR-WA-B5 · 全局限流(保守 · 豁免基建 · fail-open)· 先于 RequestContext 添加 →
# RequestContext 处于更外层 → 429 响应也带 request_id
from services.ratelimit.middleware import RateLimitMiddleware

app.add_middleware(RateLimitMiddleware)

# REFACTOR-WA-B6 · request_id 全链路上下文 · 最后添加 → 处于最外层 → 最先绑定
from services.observability.request_context import RequestContextMiddleware

app.add_middleware(RequestContextMiddleware)

from services.security.headers import SecurityHeadersMiddleware

app.add_middleware(SecurityHeadersMiddleware)


# v118.34.13 (Zihao 2026-05-19 拍板) · catch-all exception handler so
# any uncaught exception writes a traceback snapshot into _last_500_event
# before propagating. HTTPException(500, ...) raised explicitly bypasses
# this (FastAPI handles it before this hook fires), so routes that raise
# 500 must also call _record_500 manually — see erp_endpoints_create.
@app.exception_handler(Exception)
async def _capture_unhandled_500(request: Request, exc: Exception):
    # 处理体已抽到 services/error_handlers.py(REFACTOR-WA-B1 · 2026-05-29)
    return await handle_unhandled_exception(request, exc)


# POS/库存 PosError → 统一信封 {"ok": false, "error": {...}}(POS 项目 · PO-A1 · 2026-06-07)
register_pos_error_handler(app)


# v118.27.5.4 · 前端版本号自动读取(给 /api/version 用 · 检测新版弹横幅)
# 启动时解析 home.html 里的 ?v= 数字 · 部署后立刻反映


PEARNLY_FRONTEND_VERSION = read_frontend_version()
logger.info(f"📌 前端版本 PEARNLY_FRONTEND_VERSION = {PEARNLY_FRONTEND_VERSION}")


purge_stale_static_gz()


# 静态资源挂载
app.mount("/static", StaticFiles(directory="static"), name="static")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app:app", host="0.0.0.0", port=int(os.environ.get("PORT", "7860")), reload=True)
