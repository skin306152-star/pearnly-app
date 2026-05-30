# -*- coding: utf-8 -*-
"""
Mr.Pearnly · FastAPI 主入口 (v3.5)
第 3.5 批:
  - 返回完整权限字段
  - /api/v1/ 路由前缀预留(与旧路径并存)
  - 套餐元数据端点
"""

import os
import logging
from typing import Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, HTTPException, UploadFile, File, Form
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

import db  # v0.6.4 修复:新增 ERP 路由用到了 db.xxx 命名空间

try:
    import line_client  # T1 · LINE Bot(v0.19.0)
except ImportError:
    line_client = None  # line_client.py 不在 pearnly 仓库 · 文件需单独部署到服务器
from db import (
    increment_user_monthly_usage,
    insert_ocr_history,
)
import pdf_storage  # v114 · PDF 留底存储模块
from auth import (
    get_current_user_from_request,
    get_client_ip,
)
from report_routes import router as reports_router  # v109.0
from auth_signup import router as signup_router  # v109.3
from auth_email_code_routes import (
    router as auth_email_code_router,
)  # REFACTOR-B1 · 2026-05-28
from line_account_merge_routes import (
    router as line_account_merge_router,
)  # REFACTOR-B1 · 2026-05-28
from oauth_routes import router as oauth_router  # REFACTOR-B1 · Google+LINE OAuth · 2026-05-28
from line_webhook_routes import (
    router as line_webhook_router,
)  # REFACTOR-B1 · LINE Bot webhook · 2026-05-28
from login_routes import router as login_router  # REFACTOR-B1 · 主登录 · 2026-05-28
from meta_aliases_routes import (
    router as meta_aliases_router,
)  # REFACTOR-B1 · /api/version + v1 OCR 别名 · 2026-05-28
from ocr_export_routes import (
    router as ocr_export_router,
)  # REFACTOR-B1 · OCR 配额+导出 4 路由 · 2026-05-28
from recon_routes import router as recon_router  # v118.32.0
from recon_jobs_routes import router as recon_jobs_router  # ADR-005 #15 · 对账异步 submit/状态
from import_routes import router as import_router  # ADR-006 · 通用模板学习层 列映射接口
from vat_excel_routes import router as vat_excel_router  # v118.32.4.9.5 · Excel 公式对账内测
from notification_routes import router as notification_router  # REFACTOR-B1 · 2026-05-24
from clients_routes import router as clients_router  # REFACTOR-B1 · 客户管理 5 路由 · 2026-05-24
from team_routes import router as team_router  # REFACTOR-B1 · 员工管理 7 路由 · 2026-05-25
from email_ingest_routes import (
    router as email_ingest_router,
)  # REFACTOR-B1 · 邮箱抓取 6 路由 · 2026-05-25
from rd_routes import router as rd_router  # REFACTOR-B1 · 泰国 RD 税务 4 路由 · 2026-05-25
from workspace_routes import (
    router as workspace_router,
)  # B4 · workspace 账套主体(非破坏) · 2026-05-25
from categories_routes import router as categories_router  # REFACTOR-B1 · 分类 1 路由 · 2026-05-25
from pages_routes import (
    router as pages_router,
)  # REFACTOR-B1 · 静态页面 + 公开 meta 12 路由 · 2026-05-25
from me_routes import (
    router as me_router,
)  # REFACTOR-B1 · /api/me 家族 3 路由 + UserInfo · 2026-05-25
from line_binding_routes import (
    router as line_binding_router,
)  # REFACTOR-B1 · LINE 绑定 + 偏好语言 4 路由 · 2026-05-25
from erp_routes import (  # REFACTOR-B1 · ERP 推送 15 路由 · 2026-05-25
    router as erp_router,
)
from admin_users_routes import (
    router as admin_users_router,
)  # REFACTOR-B1 · 超管用户/员工 15 路由 · 2026-05-25

# REFACTOR-B1(2026-05-25)· OCR 异常检测链 · OCR/LINE 上传路由调用(_parse_money 随 history 搬走)
from exception_checks import _async_run_exception_checks
from history_routes import (
    router as history_router,
)  # REFACTOR-B1 · OCR 历史 11 路由(含 assign_client) · 2026-05-25
from settings_routes import (
    router as settings_router,
)  # REFACTOR-B1 · 归档/查重设置 5 路由 · 2026-05-25
from erp_mappings_routes import (
    router as erp_mappings_router,
)  # REFACTOR-B1 · ERP 映射 12 路由 · 2026-05-25
from bank_recon_routes import (
    router as bank_recon_router,
)  # REFACTOR-B1 · 银行对账 11 路由 · 2026-05-25
from admin_migration_routes import (
    router as admin_migration_router,
)  # REFACTOR-B1 · 超管迁移/RLS 7 路由 · 2026-05-25
from admin_cost_routes import (
    router as admin_cost_router,
)  # REFACTOR-B1 · 超管成本/收入/监控 10 路由 · 2026-05-25
from tenant_routes import router as tenant_router  # REFACTOR-B1 · 租户管理 6 路由 · 2026-05-25
from admin_logs_routes import (
    router as admin_logs_router,
)  # REFACTOR-B1 · 操作/审计日志 4 路由 · 2026-05-25
from erp_xero_routes import (
    router as erp_xero_router,
)  # REFACTOR-B1 · ERP 连接器聚合 + Xero 8 路由 · 2026-05-25
from exceptions_routes import (
    router as exceptions_router,
)  # REFACTOR-B1 · 异常处理 8 路由 · 2026-05-24
from billing_routes import (
    router as billing_router,
)  # 阶段 5 Task 5.1 · 抽 11 个 billing 路由(2026-05-22)
from admin_diagnostics_routes import (
    router as admin_diagnostics_router,
)  # 阶段 5 Task 5.2 · 抽 5 个 admin diagnostics + internal/deploy* 路由(2026-05-22)
from route_helpers import (  # REFACTOR-B1 · 公共鉴权/日志/校验 helper(2026-05-24)
    _plan_permissions,
    _tid,
)
from services.ocr.entrypoints import (
    all_pages_not_invoice as _ocr_all_pages_not_invoice,
    billing_quote as _ocr_billing_quote,
    charge_successful_ocr as _ocr_charge_success,
    content_hash as _ocr_content_hash,
    get_cached_history as _ocr_get_cached,
    is_supported_ocr_file as _ocr_is_supported_file,
    run_pipeline_for_file as _ocr_run_pipeline_file,
)
from services.static_assets import read_frontend_version, purge_stale_static_gz  # REFACTOR-WA-B1
from services.erp.auto_push import (  # REFACTOR-WA-B1 · ERP 自动推送编排
    _auto_push_history,
    _auto_push_smart_routed,
    _trigger_auto_push_all,
    _erp_seller_routing_enabled,
)
from services.startup import run_startup, run_shutdown  # REFACTOR-WA-B1
from services.error_handlers import handle_unhandled_exception  # REFACTOR-WA-B1

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass  # dotenv 可选 · 未装则用系统环境变量

logging.basicConfig(
    level=os.environ.get("LOG_LEVEL", "INFO"),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
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


app = FastAPI(title="Mr.Pearnly API", version="0.3.5-mvp", lifespan=lifespan)
app.include_router(reports_router)  # v109.0
app.include_router(signup_router)  # v109.3
app.include_router(recon_router)  # v118.32.0 · 销项税对账
app.include_router(vat_excel_router)  # v118.32.4.9.5 · Excel 公式对账内测(skin306152 only)
app.include_router(notification_router)  # REFACTOR-B1 · 通知规则 6 路由(2026-05-24)
app.include_router(clients_router)  # REFACTOR-B1 · 客户管理 5 路由(2026-05-24)
app.include_router(team_router)  # REFACTOR-B1 · 员工管理 7 路由(2026-05-25)
app.include_router(erp_mappings_router)  # REFACTOR-B1 · ERP 映射 12 路由(2026-05-25)
app.include_router(email_ingest_router)  # REFACTOR-B1 · 邮箱抓取 6 路由(2026-05-25)
app.include_router(rd_router)  # REFACTOR-B1 · 泰国 RD 税务 4 路由(2026-05-25)
app.include_router(workspace_router)  # B4 · workspace 账套主体读写(非破坏 · 2026-05-25)
app.include_router(settings_router)  # REFACTOR-B1 · 归档/查重设置 5 路由(2026-05-25)
app.include_router(categories_router)  # REFACTOR-B1 · 分类 1 路由(2026-05-25)
app.include_router(pages_router)  # REFACTOR-B1 · 静态页面 + 公开 meta 12 路由(2026-05-25)
app.include_router(me_router)  # REFACTOR-B1 · /api/me 家族 3 路由(me/v1/me/profile)(2026-05-25)
app.include_router(line_binding_router)  # REFACTOR-B1 · LINE 绑定 + 偏好语言 4 路由(2026-05-25)
app.include_router(erp_router)  # REFACTOR-B1 · ERP 推送 15 路由(2026-05-25)
app.include_router(admin_users_router)  # REFACTOR-B1 · 超管用户/员工 15 路由(2026-05-25)
app.include_router(history_router)  # REFACTOR-B1 · OCR 历史 11 路由(含 assign_client)(2026-05-25)
app.include_router(bank_recon_router)  # REFACTOR-B1 · 银行对账 11 路由(2026-05-25)
app.include_router(admin_migration_router)  # REFACTOR-B1 · 超管迁移/RLS 7 路由(2026-05-25)
app.include_router(admin_cost_router)  # REFACTOR-B1 · 超管成本/收入/监控 10 路由(2026-05-25)
app.include_router(tenant_router)  # REFACTOR-B1 · 租户管理 6 路由(2026-05-25)
app.include_router(admin_logs_router)  # REFACTOR-B1 · 操作/审计日志 4 路由(2026-05-25)
app.include_router(erp_xero_router)  # REFACTOR-B1 · ERP 连接器聚合 + Xero 8 路由(2026-05-25)
app.include_router(exceptions_router)  # REFACTOR-B1 · 异常处理 8 路由(2026-05-24)
app.include_router(billing_router)  # 阶段 5 Task 5.1 · billing 11 路由(2026-05-22)
app.include_router(
    admin_diagnostics_router
)  # 阶段 5 Task 5.2 · admin diagnostics + internal/deploy* 5 路由(2026-05-22)
app.include_router(recon_jobs_router)  # ADR-005 #15 · 对账异步 submit + 统一状态查询
app.include_router(import_router)  # ADR-006 · 通用模板学习层 列映射接口
app.include_router(auth_email_code_router)  # REFACTOR-B1 · 邮箱验证码 2 路由(2026-05-28)
app.include_router(line_account_merge_router)  # REFACTOR-B1 · LINE 补邮箱+合并 2 路由(2026-05-28)
app.include_router(oauth_router)  # REFACTOR-B1 · Google+LINE OAuth 4 路由(2026-05-28)
app.include_router(line_webhook_router)  # REFACTOR-B1 · LINE Bot webhook · 2026-05-28
app.include_router(login_router)  # REFACTOR-B1 · 主登录 · 2026-05-28
app.include_router(meta_aliases_router)  # REFACTOR-B1 · /api/version + v1 OCR 别名 · 2026-05-28
app.include_router(ocr_export_router)  # REFACTOR-B1 · OCR 配额+导出 4 路由 · 2026-05-28
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


# v118.34.13 (Zihao 2026-05-19 拍板) · catch-all exception handler so
# any uncaught exception writes a traceback snapshot into _last_500_event
# before propagating. HTTPException(500, ...) raised explicitly bypasses
# this (FastAPI handles it before this hook fires), so routes that raise
# 500 must also call _record_500 manually — see erp_endpoints_create.
@app.exception_handler(Exception)
async def _capture_unhandled_500(request: Request, exc: Exception):
    # 处理体已抽到 services/error_handlers.py(REFACTOR-WA-B1 · 2026-05-29)
    return await handle_unhandled_exception(request, exc)


# ============================================================
# v118.27.5.4 · 前端版本号自动读取(给 /api/version 用 · 检测新版弹横幅)
# 启动时解析 home.html 里的 ?v= 数字 · 部署后立刻反映
# ============================================================


PEARNLY_FRONTEND_VERSION = read_frontend_version()
logger.info(f"📌 前端版本 PEARNLY_FRONTEND_VERSION = {PEARNLY_FRONTEND_VERSION}")


purge_stale_static_gz()


# (_build_user_info → me_routes.py · REFACTOR-B1)


# _plan_permissions 已抽到 route_helpers.py(REFACTOR-B1 · 2026-05-25)·
# app.py 从 route_helpers import 回来 · 13 处调用点不变。


# (Health & Contact 公开 meta 路由 → pages_routes.py · REFACTOR-B1)


# v118.35.0.6 · /api/plans + /api/v1/plans 已下线 · credits 系统接管(legacy/credits-system-5de6cc5 tag)


# /api/login 主登录路由 + _record_login_failure → login_routes.py(REFACTOR-B1)


# ============================================================
# User
# ============================================================
# (/api/me · /api/v1/me · /api/me/profile + ProfileUpdate → me_routes.py · REFACTOR-B1)


# ============================================================
# OCR
# ============================================================
# /api/ocr/quota → ocr_export_routes.py(REFACTOR-B1)


@app.post("/api/ocr/recognize")
async def ocr_recognize(
    request: Request,
    file: UploadFile = File(...),
    client_id: Optional[str] = Form(None),  # v27.8.1.13a · 右上角客户切换器选中时自动归属
    # B1 相 1 (2026-05-26) · workspace 账套归属(在为哪家公司做账)· 可选 · Form 或 header
    # X-Workspace-Client-Id · 带不上 NULL · 非强制(缺失不拦上传)· 与 client_id(买方)独立。
    workspace_client_id: Optional[str] = Form(None),
    # P1b (2026-05-26) · ERP 自动处理方式 · 临时覆盖本批(可空 · 缺省走账户级默认)。
    # smart=智能分拣 / fixed=固定当前账套 / ocr_only=只识别不推送。
    push_mode: Optional[str] = Form(None),
):
    user = get_current_user_from_request(request)
    client_ip = get_client_ip(request)
    plan = user.get("plan", "free")

    # B1 相 1 · 解析 workspace 账套归属:优先 Form,回退 header;非数字/缺失 → None(写 NULL)。
    _ws_raw = workspace_client_id or request.headers.get("X-Workspace-Client-Id")
    _ws_client_id = int(_ws_raw) if (_ws_raw and str(_ws_raw).strip().isdigit()) else None

    # P1b · ERP 自动处理方式:本批 Form 覆盖优先,否则读账户级默认(容错 smart)。
    # ocr_only → 下方两处 auto-push 直接跳过(零风险纯跳过);smart/fixed 的真正分流在 P1d。
    _pm = (push_mode or "").strip()
    _erp_mode = _pm if _pm in db.ERP_PUSH_MODES else db.get_erp_push_mode(str(user["id"]))

    # 1. 基本校验 (2026-05-21 multi-format refactor: PDF + image + Excel + CSV + Word)
    from services.ocr.pipeline import (
        PDF_EXTENSIONS,
        IMAGE_EXTENSIONS,
        TABLE_EXTENSIONS,
    )

    _all_exts = PDF_EXTENSIONS | IMAGE_EXTENSIONS | TABLE_EXTENSIONS
    _fname = (file.filename or "").lower()
    _ext = "." + _fname.rsplit(".", 1)[-1] if "." in _fname else ""
    if not _fname or _ext not in _all_exts:
        raise HTTPException(400, detail="ocr.unsupported_format")

    content = await file.read()
    if len(content) == 0:
        raise HTTPException(400, detail="ocr.empty_file")

    # 2. 按套餐决定页数/大小上限 · v0.8 单一数据源
    p_perms = _plan_permissions(plan)
    max_pages = p_perms["max_pages_per_upload"]
    max_mb = p_perms["max_file_size_mb"]

    if len(content) > max_mb * 1024 * 1024:
        raise HTTPException(400, detail={"code": "ocr.file_too_large", "mb": max_mb})

    # 3. 页数校验 — only meaningful for PDFs. Excel/CSV/Word/image skip this.
    if _ext in PDF_EXTENSIONS:
        from services.ocr.pdf_utils import count_pdf_pages

        page_count = count_pdf_pages(content)
        if page_count == 0:
            raise HTTPException(400, detail="ocr.invalid_pdf")
        if page_count > max_pages:
            raise HTTPException(
                400,
                detail={
                    "code": "ocr.too_many_pages",
                    "max": max_pages,
                    "actual": page_count,
                },
            )
    else:
        page_count = 1  # images / single-CSV / single-DOCX count as 1 page

    # 4. 配额检查 · v0.15 · 新双轨:自带 key → 不限 · 否则扣 user.monthly_quota
    # === v118.46 · 纯 credits 按量扣费(2026-05-24 Zihao 拍板:全平台只此一个套餐)===
    #   OCR 准入只看「是否豁免 或 余额>0」· 旧 plan / monthly_quota / 自带 key / trial 反薅闸
    #   全部下线(0 起步·必须充值才能用 → 没有免费额度可薅 → 天然防薅)。
    #   旧函数 check_ocr_quota / _check_user_quota 不再用于 OCR 准入(保留供其它老路径兼容)。
    #   下游若干变量(quota_info / monthly_quota / used_month)给 credits-mode 默认值兼容。
    quota_info = {"mode": "credits", "monthly_quota": None, "used_this_month": 0}
    monthly_quota = None  # None = 不限月配额(credits 模式按余额扣)
    used_today = None
    used_month = 0

    # 4.5. 文件指纹缓存 · v0.8 改:所有 plan 都启用(按 user_id 隔离,不跨用户)
    # v92 · 缓存窗口从 24h 扩到 30 天(默认) · 月末复核上月票也能命中 · 省 Gemini 配额
    # v118.47 · 缓存必须先于余额闸:缓存命中不产生新 OCR 成本,余额为 0 也应可复用旧结果。
    file_hash = _ocr_content_hash(content)
    cached = _ocr_get_cached(user, file_hash)
    if cached:
        logger.info(f"  🎯 命中文件缓存 (hash={file_hash[:12]}..., 省额度)")

        # v0.9 · 缓存命中也触发自动推送(用户的期待是"每次上传就推送")
        # P1b · ocr_only 模式 → 完全跳过 auto-push(纯跳过 · 零风险)。
        cache_auto_pushed = False
        if _erp_mode == "ocr_only":
            logger.info("[Cache][P1b] ocr_only 模式 · 跳过自动推送")
        elif _plan_permissions(plan).get("can_auto_push_erp"):
            try:
                auto_eps = db.list_erp_endpoints(str(user["id"]), auto_push_only=True)
                if auto_eps:
                    import asyncio

                    # P1d · 缓存命中也走同一分流(开+smart→分拣 · 否则现行为)。
                    if _erp_seller_routing_enabled(str(user["id"])) and _erp_mode == "smart":
                        asyncio.create_task(
                            _auto_push_smart_routed(
                                str(user["id"]), [cached["id"]], _tid(user), auto_eps
                            )
                        )
                    else:
                        asyncio.create_task(
                            _auto_push_history(
                                str(user["id"]), cached["id"], auto_eps, tenant_id=_tid(user)
                            )
                        )
                    cache_auto_pushed = True
                    logger.info(f"🚀 [Cache] 自动推送已入队 · history={cached['id']}")
            except Exception as e:
                logger.warning(f"[Cache] 自动推送入队失败: {e}")
            # v27.8.1.3 · 同时触发 Xero 自动推(独立通道)
            try:
                _trigger_auto_push_all(str(user["id"]), _tid(user), cached["id"])
            except Exception as e:
                logger.warning(f"[Cache] xero 自动推入队失败: {e}")

        # v118.20.1.7 · 缓存命中也跑异常检测(unique index 保证幂等 · 不会重写)
        # 这是关键 · 否则:历史已识别 + 这次重传 → 缓存命中 → 异常栏永远收不到这张
        try:
            import asyncio as _asyncio_exc_c

            _cached_pages = cached.get("pages") or []
            _primary = next(
                (p for p in _cached_pages if not p.get("is_duplicate") and not p.get("is_copy")),
                None,
            )
            _primary = _primary or (_cached_pages[0] if _cached_pages else None)
            _cf = (_primary or {}).get("fields") or {}
            _exc_total_c = None
            _raw_t_c = _cf.get("total_amount")
            if _raw_t_c:
                try:
                    _exc_total_c = float(str(_raw_t_c).replace(",", "").strip())
                except Exception as e:
                    logger.warning(f"[cache_hit] total_amount 解析失败: {e}")
            _asyncio_exc_c.create_task(
                _async_run_exception_checks(
                    history_id=str(cached["id"]),
                    user_id=str(user["id"]),
                    tenant_id=_tid(user),
                    seller_name=_cf.get("seller_name"),
                    invoice_no=_cf.get("invoice_number"),
                    total_amount=_exc_total_c,
                    confidence=cached.get("confidence"),
                    duplicate=None,  # 缓存命中说明 hash 全等 · 由专门的 duplicate 路径处理(本身已是同张)
                    fields=_cf,
                )
            )
            logger.info(f"  🛡  [Cache] 异常检测已入队 · hid={cached['id']}")
        except Exception as _e_c:
            logger.warning(f"[Cache] 异常检测入队失败(不影响识别): {_e_c}")

        # v106.2 · 缓存命中也记 1 条成本日志(成本 0 · engine=cache)
        # 让面板能看到"省了多少次"+ 总张数也包含缓存命中
        try:
            db.log_ocr_cost(
                user_id=str(user["id"]),
                tenant_id=str(user.get("tenant_id")) if user.get("tenant_id") else None,
                history_id=cached["id"],
                engine="cache",
                pages=int(cached.get("page_count") or 0),
                input_tokens=0,
                output_tokens=0,
                cost_thb=0.0,
                elapsed_ms=0,
            )
        except Exception as _ce:
            logger.warning(f"缓存命中日志写入失败(不影响识别): {_ce}")

        return {
            "filename": file.filename,
            "page_count": cached["page_count"],
            "elapsed_ms": 0,
            "engine": "cache",
            "pages": cached["pages"],
            "confidence": cached["confidence"],
            "history_id": cached["id"],
            "archive_name": cached.get("archive_name"),
            "category_tag": cached.get("category_tag"),
            "from_cache": True,
            "auto_pushed": cache_auto_pushed,
            "quota": {
                "ip_used_today": None,
                "ip_daily_limit": None,
                "used_this_month": int(user.get("used_this_month") or 0),
                "monthly_quota": monthly_quota,
            },
        }

    # v118.35.0.21 · Credits 余额前置检查(v0.20 重做 · 1 次 SELECT · 修连接池超时)
    _billing = {
        "allowed": True,
        "is_exempt": True,
        "balance_thb": 0.0,
        "pages_used_this_month": 0,
        "error_code": None,
    }
    try:
        _billing = db.get_billing_status_combined(str(user.get("id")), _tid(user))
        if not _billing.get("allowed") and not _billing.get("is_exempt"):
            if _ext in PDF_EXTENSIONS or _ext in IMAGE_EXTENSIONS:
                _est_cost = float(
                    db.estimate_pdf_cost_thb(_billing.get("pages_used_this_month", 0), page_count)
                )
            else:
                _chars = db._excel_char_count_estimate(content, file.filename or "")
                _est_cost = float(db.estimate_excel_cost_thb(_chars))
            raise HTTPException(
                402,
                detail={
                    "code": "insufficient_balance",
                    "balance": _billing.get("balance_thb", 0.0),
                    "estimated_cost": _est_cost,
                    "pages_used_this_month": _billing.get("pages_used_this_month", 0),
                },
            )
    except HTTPException:
        raise
    except Exception as _be:
        logger.warning(f"[credits] billing pre-check skip(error tolerated): {_be}")

    # 5. 选引擎(v103 · 永远走降级链 · _choose_engine 保留兼容)
    engine_name = _choose_engine(plan, user)

    # v105 · 简化引擎架构 · Gemini 主 + Google Vision 备
    own_key = (user.get("gemini_api_key") or user.get("custom_gemini_api_key") or "").strip()
    api_key = own_key or None

    # OCR · 新 pipeline 唯一路径(text_path layer 0 + Vision + Flash-Lite + Flash · 100% 埋点)
    # 2026-05-21 multi-format refactor: dispatch by extension to PDF /
    # image / table reader. PDF and image go through OCR; Excel/CSV/Word
    # bypass OCR via table_path.
    chain_info = ["pipeline_v1"]
    fallback_used = False
    _chg_kind = None  # v118.46 · 扣费参数 · 算在此 · 实际扣费在 history 落库后
    _chg_units = 0
    try:
        from services.ocr.pipeline import (
            run_on_pdf_bytes as _pipeline_run_pdf,
            run_on_image_bytes as _pipeline_run_image,
            run_on_table_bytes as _pipeline_run_table,
        )
        from services.ocr.legacy_adapter import pipeline_result_to_legacy_dict

        if _ext in PDF_EXTENSIONS:
            _pipe_res = _pipeline_run_pdf(content, max_pages=max_pages, api_key=api_key)
        elif _ext in IMAGE_EXTENSIONS:
            _pipe_res = _pipeline_run_image(content, api_key=api_key)
        else:  # TABLE_EXTENSIONS — Excel / CSV / Word / TXT
            _pipe_res = _pipeline_run_table(
                content, filename=file.filename or "upload", api_key=api_key
            )
            chain_info = ["pipeline_v1_table"]
        result = pipeline_result_to_legacy_dict(_pipe_res)
        _pipeline_cost_thb = float(_pipe_res.estimated_cost_thb)
        logger.info(
            f"🆕 pipeline_v1 · file={file.filename} · ext={_ext} · pages={_pipe_res.page_count} "
            f"· cost=฿{_pipeline_cost_thb:.4f} · elapsed={_pipe_res.elapsed_ms}ms"
        )
        # Step0 观测(REFACTOR-WA-OCRPERF)· 结构化 per-page layer 计时 · 纯观测不改逻辑
        try:
            from services.ocr.observability import log_pipeline_timing

            log_pipeline_timing(_pipe_res, source="recognize", filename=file.filename or "")
        except Exception:
            pass

        # v118.46 · 算扣费参数(实际扣费挪到 history 落库后:才有 history_id + 已确认非发票通过)
        #   图片(PNG/JPG/扫描)与 PDF 统一按页/张扣;CSV/XLSX/DOCX/TXT 按字符。
        if not _billing.get("is_exempt"):
            try:
                if _ext in PDF_EXTENSIONS or _ext in IMAGE_EXTENSIONS:
                    _chg_kind = "pdf"
                    _chg_units = int(_pipe_res.page_count or page_count or 1)
                else:
                    _chg_kind = "excel"
                    _chg_units = db._excel_char_count_estimate(content, file.filename or "")
            except Exception as _ce:
                logger.warning(f"💳 扣费参数计算跳过: {_ce}")
    except HTTPException:
        raise
    except Exception as _pipe_err:
        err_name = type(_pipe_err).__name__
        if err_name == "Layer1PDFError" or isinstance(_pipe_err, ValueError):
            raise HTTPException(400, detail=f"ocr.invalid_file: {_pipe_err}")
        logger.exception(f"❌ pipeline_v1 失败: {err_name}: {_pipe_err}")
        raise HTTPException(500, detail="ocr.engine_error")

    # ============================================================
    # v93 · 场景 2 · 非发票检测(Gemini Prompt 里新增 is_not_invoice 字段)
    # 如果全部页面都不是发票 · 直接报错 · 不入库 · 不扣配额
    # ============================================================
    if result.get("pages"):
        _pages = result["pages"]
        # 所有页都标记为 is_not_invoice=true 才算非发票(一份 PDF 可能混了封面 + 发票)
        all_not_invoice = True
        for p in _pages:
            f = p.get("fields") or {}
            is_not = f.get("is_not_invoice")
            # 兼容字符串 / 布尔
            if isinstance(is_not, str):
                is_not = is_not.strip().lower() == "true"
            if not is_not:
                all_not_invoice = False
                break
        if all_not_invoice and len(_pages) > 0:
            logger.warning(f"⚠️ Gemini 判定非发票 · 不入库 · file={file.filename}")
            raise HTTPException(400, detail="ocr.not_invoice")

    # v105 · 删除 Typhoon 二次增援 · 简化引擎架构
    typhoon_enhanced = False
    typhoon_pages_enhanced = []

    # 6. 更新配额 · v87 多租户支持:shared=扣租户 · monthly=扣用户(老) · admin/lifetime 不扣
    new_month_used = None
    qm = quota_info.get("mode")
    if qm == "shared" and user.get("tenant_id"):
        try:
            tu = db.increment_tenant_monthly_usage(str(user["tenant_id"]), page_count)
            if tu >= 0:
                new_month_used = tu
        except Exception as e:
            logger.warning(f"increment_tenant_monthly_usage failed: {e}")
    elif qm == "monthly" and monthly_quota is not None:
        new_month_used = increment_user_monthly_usage(str(user["id"]), page_count)

    # 7. 智能置信度
    #    策略:不再跨页"合并取第一个非空值",避免一页成功一页失败被误判为高
    #    改为:对所有【非副本】页取每页独立置信度,然后取最高
    def _page_confidence(p):
        f = p.get("fields", {}) or {}
        s = 0
        if f.get("invoice_number"):
            s += 1
        if f.get("date"):
            s += 1
        if f.get("total_amount"):
            s += 1
        if f.get("seller_name") or f.get("seller_tax"):
            s += 1
        if f.get("buyer_name") or f.get("buyer_tax"):
            s += 1
        items = f.get("items") or []
        if items:
            s += 2
        # v118.20.4.2 · 文本路径补偿:subtotal + vat 双有 → 等价 items(发票结构完整)
        elif f.get("subtotal") and f.get("vat"):
            s += 2
        return s

    # 副本/签字页过滤(去重)
    # v105.1 修复:多联发票(底单/发票/收据)Gemini 可能把全部页标 is_copy · 导致主页 0
    # 改进:至少保留 1 页作为主页(取得分最高的)
    seen_invoice_numbers = set()
    primary_pages = []
    for p in result["pages"]:
        inv = (p.get("fields") or {}).get("invoice_number")
        is_copy = p.get("is_copy", False)
        # 副本 OR 同一发票号已经见过 → 标记为非主页
        if is_copy or (inv and inv in seen_invoice_numbers):
            p["is_duplicate"] = True
            continue
        if inv:
            seen_invoice_numbers.add(inv)
        p["is_duplicate"] = False
        primary_pages.append(p)

    # v105.1 · 兜底 · 如果一张主页都没有(多联发票全标副本) · 取第一张得分最高的当主页
    if not primary_pages and result["pages"]:
        # 同发票号去重 · 然后选得分最高
        unique_pages = []
        seen_inv = set()
        for p in result["pages"]:
            inv = (p.get("fields") or {}).get("invoice_number")
            if inv and inv in seen_inv:
                continue
            if inv:
                seen_inv.add(inv)
            unique_pages.append(p)
        if unique_pages:
            best_page = max(unique_pages, key=_page_confidence)
            best_page["is_duplicate"] = False
            primary_pages.append(best_page)
            logger.info(f"  ⚠️ 所有页都标副本 · 兜底选第 {best_page.get('page', '?')} 页作为主页")

    # 对主页取最高置信度
    if primary_pages:
        max_score = max(_page_confidence(p) for p in primary_pages)
    else:
        max_score = 0

    if max_score >= 6:
        confidence = "high"
    elif max_score >= 3:
        confidence = "medium"
    else:
        confidence = "low"
    logger.info(
        f"  识别置信度: {confidence} (最高得分 {max_score}, "
        f"主页 {len(primary_pages)}/{len(result['pages'])})"
    )

    # 8. 写入历史记录 · v0.8 改:所有 plan 都写(Free 也能看历史,只是保留 7 天)
    history_id = None
    # v0.11 · 多发票智能分组:把 PDF 拆成 N 张独立发票,每张一条历史
    import uuid as _uuid
    import invoice_grouper
    import archive as _archive

    try:
        invoice_groups = invoice_grouper.group_pages_to_invoices(result["pages"])
        logger.info(f"📑 识别结果拆分为 {len(invoice_groups)} 张发票")
    except Exception as e:
        logger.warning(f"发票分组失败,回退为单张: {e}")
        invoice_groups = [
            {
                "invoice_fields": {},
                "source_pages": result["pages"],
                "page_indices": list(range(1, result["page_count"] + 1)),
            }
        ]

    invoice_count = len(invoice_groups)
    source_pdf_id = str(_uuid.uuid4()) if invoice_count > 1 else None

    # 取用户归档模板(一次查询复用)
    try:
        template = db.get_archive_template(str(user["id"])) or _archive.DEFAULT_TEMPLATE
    except Exception:
        template = _archive.DEFAULT_TEMPLATE

    history_ids = []
    duplicate_warnings = []  # v0.13 · 收集所有发票的重复警告
    primary_history_id = None  # 第一张发票的 history_id · 兼容老前端字段
    primary_archive_name = None
    primary_category_tag = None

    # v0.13 · 检查用户是否启用重复检测(默认开)
    dup_check_on = True
    try:
        dup_check_on = db.get_user_dup_check_enabled(str(user["id"]))
    except Exception as e:
        logger.warning(f"[dup_check] 读取用户设置失败 · 用默认值: {e}")

    # v114 · PDF 留底 · 所有发票共享同一份原 PDF · 失败不阻塞主流程
    # v115 · 升级 · 先生成 searchable PDF(把 OCR 文字塞进不可见层)· 失败 fallback 原 PDF
    _pdf_rel_path, _pdf_size_bytes = None, None
    try:
        # v115 · 收集每页搜索文本 · 用 Gemini 已识别的字段拼出
        _pdf_to_save = content
        try:
            import pdf_searchable

            _pages_texts = pdf_searchable.extract_searchable_text_from_pages(
                result.get("pages") or []
            )
            if any(t.strip() for t in _pages_texts):
                _searchable = pdf_searchable.make_searchable_pdf(content, _pages_texts)
                if _searchable:
                    _pdf_to_save = _searchable
        except Exception as _se:
            logger.warning(f"v115 · searchable PDF 生成失败 · 用原始 PDF: {_se}")

        _pdf_rel_path, _pdf_size_bytes = pdf_storage.save_pdf(str(user["id"]), _pdf_to_save)
    except Exception as _pdf_err:
        logger.warning(f"⚠️ PDF 留底失败(已忽略): {_pdf_err}")

    for idx, group in enumerate(invoice_groups, start=1):
        g_pages = group["source_pages"]
        g_fields = group["invoice_fields"]

        # 给每张发票生成归档名(基于该张的合并字段)
        try:
            g_archive_name = _archive.preview_name(g_fields or {}, template)
            g_category_tag = (g_fields.get("category") or "").strip() or None if g_fields else None
        except Exception as e:
            logger.warning(f"归档名生成失败(发票 #{idx}): {e}")
            g_archive_name = None
            g_category_tag = None

        # v118.18 · 推荐分类「学习」· 同 seller 历史用过的 category 优先于 Gemini 的猜测
        try:
            g_seller = (g_fields.get("seller_name") or "").strip() if g_fields else None
            if g_seller:
                _learned = db.get_category_for_seller(
                    seller_name=g_seller,
                    user_id=str(user["id"]),
                    tenant_id=_tid(user),
                )
                if _learned:
                    g_category_tag = _learned
                    # 同步覆盖 g_fields["category"] · 让 pages 写入也带这个 · 抽屉打开就显示学到的科目
                    if g_fields is not None:
                        g_fields["category"] = _learned
        except Exception as _ce:
            logger.warning(f"category 学习查询失败(已忽略): {_ce}")

        # 为该张发票构造一份独立的 pages(只含该发票的页 + 合并后的主 fields)
        # pages 列表里:第一项放"主页"(含合并 fields)· 其他页按原顺序保留
        g_pages_for_save = []
        for pi, p in enumerate(g_pages):
            pc = dict(p)
            if pi == 0 and g_fields:
                # 主页的 fields 用合并后的 · 其他页保持原样
                pc["fields"] = g_fields
            g_pages_for_save.append(pc)

        # ─────────────────────────────────────────
        # v0.13 · 入库前重复检测
        # 检测到 · 仅记录警告 · 不阻断写入(让用户在前端选择如何处理)
        # ─────────────────────────────────────────
        if dup_check_on and g_fields:
            try:
                # 提取 summary 字段
                inv_no = (g_fields.get("invoice_number") or "").strip() or None
                seller = (g_fields.get("seller_name") or "").strip() or None
                # date 转 ISO 格式
                date_iso = None
                raw_date = g_fields.get("date")
                if raw_date:
                    try:
                        from datetime import datetime as _dt

                        s = str(raw_date).replace("/", "-")[:10]
                        _dt.strptime(s, "%Y-%m-%d")
                        date_iso = s
                    except Exception as e:
                        logger.warning(f"[ocr_post] invoice_date 解析失败: {e}")
                # 金额转 float
                total_f = None
                raw_amt = g_fields.get("total_amount")
                if raw_amt:
                    try:
                        total_f = float(str(raw_amt).replace(",", "").strip())
                    except Exception as e:
                        logger.warning(f"[ocr_post] total_amount 解析失败: {e}")

                dup = db.check_duplicate_invoice(
                    user_id=str(user["id"]),
                    invoice_no=inv_no,
                    invoice_date=date_iso,
                    seller_name=seller,
                    total_amount=total_f,
                )
                if dup:
                    duplicate_warnings.append(
                        {
                            "invoice_index": idx,  # 第几张
                            "invoice_total": invoice_count,  # 共几张
                            "level": dup["level"],  # exact / likely
                            "matched_fields": dup["matched_fields"],
                            "match": dup["match"],
                            "current": {
                                "invoice_no": inv_no,
                                "invoice_date": date_iso,
                                "seller_name": seller,
                                "total_amount": total_f,
                            },
                        }
                    )
                    logger.info(
                        f"⚠️ 检测到重复发票 (idx={idx} · {dup['level']} · 匹配于历史 {dup['match']['id']})"
                    )
            except Exception as e:
                logger.warning(f"重复检测失败(已忽略): {e}")

        # v92 · Bug 1 第 1 层防御 · 识别成功才带 file_hash · 防止空结果污染缓存
        _gf = g_fields or {}
        _has_inv = bool(str(_gf.get("invoice_number") or "").strip())
        _has_amt = _gf.get("total_amount") is not None and bool(
            str(_gf.get("total_amount")).strip()
        )
        _has_seller = bool(str(_gf.get("seller_name") or "").strip())
        _recognized_ok = _has_inv or _has_amt or _has_seller
        _cache_hash = file_hash if (idx == 1 and _recognized_ok) else None
        if idx == 1 and not _recognized_ok:
            logger.warning(f"⚠️ 识别失败(关键字段全空) · file_hash 不入缓存 · file={file.filename}")

        hid = insert_ocr_history(
            user_id=str(user["id"]),
            tenant_id=_tid(user),  # 2026-05-24 · 多租户归属(原缺 → tenant_id 恒 NULL)
            filename=file.filename or "untitled",
            page_count=len(g_pages),
            pages=g_pages_for_save,
            confidence=confidence,
            elapsed_ms=result["elapsed_ms"] if idx == 1 else 0,  # 只在第一条记录总耗时
            file_size_kb=len(content) // 1024 if idx == 1 else None,
            file_hash=_cache_hash,  # v92 · 仅识别成功时带 hash
            archive_name=g_archive_name,
            category_tag=g_category_tag,
            source_pdf_id=source_pdf_id,
            source_page_indices=group["page_indices"] if invoice_count > 1 else None,
            source_index=idx if invoice_count > 1 else None,
            source_total=invoice_count if invoice_count > 1 else None,
            # v114 · PDF 留底 · 所有发票共享同一份原 PDF
            pdf_storage_path=_pdf_rel_path,
            pdf_size_bytes=_pdf_size_bytes,
            # v27.8.1.13a · 右上角客户切换器选中时自动归属(多发票同一 PDF 共享同一 client_id)
            client_id=(
                int(client_id) if (client_id and str(client_id).strip().isdigit()) else None
            ),
            # B1 相 1 · workspace 账套归属(可选·校验在 insert_ocr_history 内·带不上 NULL)
            workspace_client_id=_ws_client_id,
        )
        if hid:
            history_ids.append(hid)
            # 把 history_id 关联到对应的 dup warning(便于前端提供"删除"操作)
            _dup_for_idx = None
            if duplicate_warnings and duplicate_warnings[-1].get("invoice_index") == idx:
                duplicate_warnings[-1]["new_history_id"] = hid
                _dup_for_idx = duplicate_warnings[-1]
            if idx == 1:
                primary_history_id = hid
                primary_archive_name = g_archive_name
                primary_category_tag = g_category_tag
                # v118.46 · 扣费(成功识别 + 落库后 · 只扣一次 · 传 history_id 让 usage-history 显示文件名)
                #   描述结尾带 history_id 前 8 位 → usage-history 的 LIKE join 能命中(修 filename 空)
                if not _billing.get("is_exempt") and _chg_units > 0 and hid:
                    try:
                        import asyncio as _asyncio_chg

                        _asyncio_chg.create_task(
                            _asyncio_chg.to_thread(
                                db.charge_ocr_async,
                                str(user.get("id")),
                                _tid(user),
                                _chg_kind,
                                _chg_units,
                                str(hid),
                                f"OCR {_chg_kind} · {file.filename} · {str(hid)[:8]}",
                            )
                        )
                    except Exception as _ce:
                        logger.warning(f"💳 async charge dispatch skip: {_ce}")

            # 买方→Pearnly client 闭环(Zihao 2026-05-26 拍板 · 税号优先·混合)。
            # 右上角客户切换器没选 client_id(常态)时,把发票买方解析/创建成 client:
            #   决策逻辑全在 services/clients/store.resolve_or_create_buyer_client:
            #   assigned/created → 写回 history.client_id · 放行 auto-push(闭环)
            #   suggest          → 写 _suggested_client_* 到 history.pages · 等用户确认
            #   review/none      → 不绑/不建(防同名异主体错并 & qa_4 多页买方冲突)
            # 根因(替代旧「只匹配已存在客户」逻辑):新买方第一次出现匹配不到 →
            #   client_id=null → 推送必 ERR_NO_CLIENT。有合法 13 位税号即按税号建客户闭环。
            _auto_resolved_client = False
            try:
                history_existing_client = (
                    int(client_id) if (client_id and str(client_id).strip().isdigit()) else None
                )
                if not history_existing_client:
                    _buyer_name = (g_fields or {}).get("buyer_name")
                    _buyer_tax = (g_fields or {}).get("buyer_tax")
                    # 同一张发票多页的买方候选(给冲突检测 · qa_4)
                    _buyer_candidates = [
                        (p.get("fields") or {}).get("buyer_name") for p in (g_pages_for_save or [])
                    ]
                    decision = db.resolve_or_create_buyer_client(
                        buyer_name=_buyer_name,
                        buyer_tax=_buyer_tax,
                        user_id=str(user["id"]),
                        tenant_id=_tid(user),
                        buyer_candidates=_buyer_candidates,
                    )
                    _act = decision.get("action")
                    _rcid = decision.get("client_id")
                    if _act in ("assigned", "created") and _rcid:
                        db.update_history_client_id(
                            hid, _rcid, str(user["id"]), tenant_id=_tid(user)
                        )
                        _auto_resolved_client = True
                        logger.info(
                            "[buyer-resolve] %s history=%s client_id=%s name=%r "
                            "conf=%.2f source=%s",
                            _act,
                            hid[:8],
                            _rcid,
                            decision.get("client_name"),
                            decision.get("confidence", 0.0),
                            decision.get("match_source"),
                        )
                    elif _act == "suggest" and _rcid:
                        # 建议归属 · 不 auto-assign · stash 到 history.pages[0].fields
                        logger.info(
                            "[buyer-resolve] SUGGEST history=%s client_id=%s name=%r conf=%.2f",
                            hid[:8],
                            _rcid,
                            decision.get("client_name"),
                            decision.get("confidence", 0.0),
                        )
                        try:
                            _new_pages = [dict(p) for p in (g_pages_for_save or [])]
                            if _new_pages:
                                _f = dict(_new_pages[0].get("fields") or {})
                                _f["_suggested_client_id"] = _rcid
                                _f["_suggested_client_name"] = decision.get("client_name")
                                _f["_suggested_client_confidence"] = decision.get("confidence")
                                _new_pages[0] = {**_new_pages[0], "fields": _f}
                                db.update_ocr_history_pages(
                                    str(user["id"]), hid, _new_pages, tenant_id=_tid(user)
                                )
                        except Exception as _se:
                            logger.warning(f"stash suggestion failed: {_se}")
                    else:
                        logger.info(
                            "[buyer-resolve] %s history=%s buyer=%r reason=%s",
                            _act,
                            hid[:8],
                            (_buyer_name or "")[:40],
                            decision.get("reason"),
                        )
            except Exception as _are:
                logger.warning(f"buyer-resolve client_id failed (history={hid[:8]}): {_are}")

            # 卖方智能分拣 → workspace 归属(Phase 1 · Zihao 2026-05-26)。
            # 销项发票「卖方」= 账套主体 = workspace_client。归属**完全由 seller 决定**,
            # 右上角切换器只是查看过滤器、不再决定上传归属。
            #   匹配到(assigned/unbound)→ 写该 workspace_client_id(覆盖)
            #   未匹配/多候选(none/multi)→ 置 NULL → 日志显「未归属/待确认卖方」
            # 注:当前 workspace_client_id 仅供日志/视图显示消费(推送路由 P1d 再接);
            #     故此处只影响"归属显示",安全。
            try:
                _seller_match = db.match_workspace_for_seller(
                    seller_tax=(g_fields or {}).get("seller_tax"),
                    seller_name=(g_fields or {}).get("seller_name"),
                    user_id=str(user["id"]),
                    tenant_id=_tid(user),
                )
                _ws_assigned = (
                    _seller_match.get("workspace_client_id")
                    if _seller_match.get("action") in ("assigned", "unbound")
                    else None
                )
                db.update_history_workspace_client_id(
                    hid, _ws_assigned, str(user["id"]), tenant_id=_tid(user)
                )
                logger.info(
                    "[seller-route] %s history=%s seller=%r workspace_client_id=%s",
                    _seller_match.get("action"),
                    hid[:8],
                    ((g_fields or {}).get("seller_name") or "")[:40],
                    _ws_assigned,
                )
            except Exception as _sre:
                logger.warning(f"seller-route failed (history={hid[:8]}): {_sre}")

            # v118.20.1 · 异常栏 · 异步跑零成本规则(不阻塞 OCR 主流程)
            try:
                import asyncio as _asyncio_exc

                # 安全解析 total · 不依赖外层 try 块里的 total_f
                _exc_total = None
                _raw_t = (g_fields or {}).get("total_amount")
                if _raw_t:
                    try:
                        _exc_total = float(str(_raw_t).replace(",", "").strip())
                    except Exception as e:
                        logger.warning(f"[exc_check] total_amount 解析失败: {e}")
                _asyncio_exc.create_task(
                    _async_run_exception_checks(
                        history_id=str(hid),
                        user_id=str(user["id"]),
                        tenant_id=_tid(user),
                        seller_name=(g_fields or {}).get("seller_name"),
                        invoice_no=(g_fields or {}).get("invoice_number"),
                        total_amount=_exc_total,
                        confidence=confidence,
                        duplicate=_dup_for_idx,
                        fields=g_fields or {},  # v118.20.1.5 · 全字段 · 给自洽性规则用
                    )
                )
            except Exception as _exc_e:
                logger.warning(f"异常检测入队失败(不影响识别): {_exc_e}")

    # v0.9 · 自动推送 ERP(异步 · 不阻塞返回)· 每张发票都推
    # 批 1 改动 1 (v118.34.33) · 只对有 client_id 的 history 触发 auto-push.
    # 没 client_id 的就交给「待归属」/「建议归属」UI 让用户确认 · 防止
    # auto-push 必炸 ERR_NO_CLIENT 浪费 retry 队列(对应 Zihao 截图里
    # 一直 retry 的混乱).
    # P1b · ocr_only 模式 → 完全跳过 auto-push + Xero 触发(纯跳过 · 零风险)。
    auto_pushed = False
    if _erp_mode == "ocr_only":
        logger.info("[P1b] ocr_only 模式 · 跳过 %d 张发票的自动推送", len(history_ids or []))
    elif history_ids and _plan_permissions(plan).get("can_auto_push_erp"):
        try:
            auto_eps = db.list_erp_endpoints(str(user["id"]), auto_push_only=True)
            if auto_eps:
                # 重新查 history 拿真实 client_id (auto-resolve 已经 update 过)
                pushable_ids = []
                for hid in history_ids:
                    h = db.get_ocr_history_detail(
                        str(user["id"]),
                        hid,
                        tenant_id=_tid(user),
                    )
                    if h and h.get("client_id"):
                        pushable_ids.append(hid)
                    else:
                        logger.info(
                            "[auto-push] skip history=%s · no client_id assigned",
                            hid[:8],
                        )
                if pushable_ids:
                    import asyncio

                    # P1d · ERP_SELLER_ROUTING 开 + smart → 按卖方账套路由分组批量推;
                    # 否则(关 / fixed)走现行为:每张推所有 auto_push 端点。
                    if _erp_seller_routing_enabled(str(user["id"])) and _erp_mode == "smart":
                        asyncio.create_task(
                            _auto_push_smart_routed(
                                str(user["id"]),
                                pushable_ids,
                                _tid(user),
                                auto_eps,
                            ),
                        )
                    else:
                        for hid in pushable_ids:
                            asyncio.create_task(
                                _auto_push_history(
                                    str(user["id"]),
                                    hid,
                                    auto_eps,
                                    tenant_id=_tid(user),
                                ),
                            )
                    auto_pushed = True
                    logger.info(
                        "🚀 自动推送已入队 · %d/%d 张发票 × %d 端点 " "(没归属的发票跳过)",
                        len(pushable_ids),
                        len(history_ids),
                        len(auto_eps),
                    )
        except Exception as e:
            logger.warning(f"自动推送入队失败(不影响识别): {e}")
        # v27.8.1.3 · 同时触发 Xero 自动推(独立通道 · 跟 webhook 并存)
        try:
            for hid in history_ids:
                _trigger_auto_push_all(str(user["id"]), _tid(user), hid)
        except Exception as e:
            logger.warning(f"xero 自动推入队失败: {e}")

    # 写入成本日志 · pipeline-v1 自带完整成本(Vision per-page + Flash-Lite + Flash · 100% 埋点)
    try:
        # 汇总 token 用量
        total_input_tokens = sum(int(p.get("input_tokens") or 0) for p in result.get("pages", []))
        total_output_tokens = sum(int(p.get("output_tokens") or 0) for p in result.get("pages", []))
        total_pages = int(result.get("page_count") or len(result.get("pages", [])) or 0)
        cost_thb = _pipeline_cost_thb
        primary_engine = "pipeline_v1"
        # 写一条记录(以本次识别的主 history 为锚)
        db.log_ocr_cost(
            user_id=str(user["id"]),
            tenant_id=str(user.get("tenant_id")) if user.get("tenant_id") else None,
            history_id=primary_history_id,
            engine=primary_engine,
            pages=total_pages,
            input_tokens=total_input_tokens,
            output_tokens=total_output_tokens,
            cost_thb=cost_thb,
            elapsed_ms=int(result.get("elapsed_ms") or 0),
        )
        logger.info(
            f"💰 成本记录 · {total_pages} 页 · in={total_input_tokens} out={total_output_tokens} · ≈THB {cost_thb:.4f}"
        )
    except Exception as _cost_err:
        logger.warning(f"成本记录写入失败(不影响识别): {_cost_err}")

    # P0 修 (2026-05-26) · 同页多票防静默漏:收集 pipeline 标出的"可能漏识别发票"页
    # (_validation_warnings 里以 possible_missed_invoice 开头),回前端明确提示 +
    # 标记 needs_review · 让用户进人工核对 · 绝不静默成功。
    missed_invoice_warnings = []
    for _pg in result.get("pages") or []:
        for _w in _pg.get("_validation_warnings") or []:
            if isinstance(_w, str) and _w.startswith("possible_missed_invoice"):
                missed_invoice_warnings.append({"page": _pg.get("page_number"), "reason": _w})

    return {
        "filename": file.filename,
        "page_count": result["page_count"],
        "elapsed_ms": result["elapsed_ms"],
        "engine": result["engine"],
        "pages": result["pages"],
        "confidence": confidence,
        # P0 修 · 可能漏识别发票(同页多票兜底)· 非空时前端必须提示用户人工核对
        "missed_invoice_warnings": missed_invoice_warnings,
        "needs_review": bool(missed_invoice_warnings),
        "history_id": primary_history_id,  # 兼容老前端
        "history_ids": history_ids,  # v0.11 · 全部 id 列表
        "invoice_count": invoice_count,  # v0.11 · 识别出几张发票
        # v118.27.5.1 · 多发票拆分修复 · 给前端每张独立 fields(导出/抽屉用)
        # 之前只返回扁平 pages · 前端 mergeFields 把多发票合并成 1 个 → 导出丢字段
        "invoices": [
            {
                "history_id": history_ids[i] if i < len(history_ids) else None,
                "fields": (invoice_groups[i] or {}).get("invoice_fields") or {},
                "page_indices": (invoice_groups[i] or {}).get("page_indices") or [],
                "page_count": len((invoice_groups[i] or {}).get("source_pages") or []),
                "source_index": i + 1,
                "source_total": invoice_count,
            }
            for i in range(min(invoice_count, len(history_ids) or invoice_count))
        ],
        "archive_name": primary_archive_name,
        "category_tag": primary_category_tag,
        "auto_pushed": auto_pushed,
        # v0.12 · Typhoon 增援标记(v105 已废弃 · 留兼容字段不破坏前端)
        "typhoon_enhanced": typhoon_enhanced,
        "typhoon_pages": typhoon_pages_enhanced,
        # v105 · 引擎降级简化:Gemini 主 + Vision 备
        "engine_chain": chain_info,
        "fallback_used": fallback_used,
        # v0.13 · 重复发票警告
        "duplicate_warnings": duplicate_warnings,
        "quota": {
            "ip_used_today": None,
            "ip_daily_limit": None,
            "used_this_month": (
                new_month_used
                if new_month_used is not None
                else int(user.get("used_this_month") or 0)
            ),
            "monthly_quota": monthly_quota,
        },
    }


def _choose_engine(plan: str = None, user: dict = None) -> str:
    """v0.15 · 所有用户统一用 Gemini · plan/user 参数保留做兼容"""
    return "gemini"


# /api/ocr/export + /api/ocr/export-by-history-ids + _merge_pages_to_fields
# → ocr_export_routes.py(REFACTOR-B1 · 2026-05-28)


# ============================================================
# /api/v1/ 别名(未来升级用,当前只是路由别名)
# ============================================================
# (/api/v1/me → me_routes.py · REFACTOR-B1)


# /api/v1/ocr/quota + /api/v1/ocr/recognize → meta_aliases_routes.py(REFACTOR-B1)
# /api/v1/ocr/export 仍留 app.py(ExportRequest model 紧耦合 · 留后续轮)


# /api/v1/ocr/export → ocr_export_routes.py(REFACTOR-B1 · 2026-05-28)


# v118.35.0.6 · /api/v1/plans 已下线 · 配套 /api/plans · credits 系统接管


# (/api/v1/health · /api/v1/contact → pages_routes.py · REFACTOR-B1)


# ============================================================
# 第 5 批 · 历史记录路由(Plus/Pro · Free 禁用)
# ============================================================


# ============================================================
# v118.20.1 · 异常栏(Exceptions)规则检查 + 智能提醒(LINE)整条链已抽到
# exception_checks.py(REFACTOR-B1 · 2026-05-25)· EXC_RULE_* 常量 / _parse_money /
# _is_valid_thai_tax_id / _async_run_exception_checks / _notify_exception_high /
# _notify_large_invoice / _format_thb / _user_lang_safe / _rule_belongs_to 全搬过去。
# 顶部 from exception_checks import _async_run_exception_checks, _parse_money ·
# OCR/LINE 上传路由 + history PUT 共用 → 单一来源(拆 history 组前置 · 解循环 import)。
# ============================================================


# ─── API 端点 ───────────────────────────────────────────


# _tid 已搬到 route_helpers.py(REFACTOR-B1 · 2026-05-25)· 顶部 from route_helpers import _tid


# ============================================================
# OCR 历史记录 10 路由(list/detail/update/delete/pdf/batch-delete + v1 别名)
# + HistoryUpdateRequest/HistoryBatchDeleteRequest model + _check_history_access
# 已抽到 history_routes.py(REFACTOR-B1 · 2026-05-25 · 步骤 B)· 顶部
# from history_routes import router as history_router · app.include_router(history_router)。
# history PUT 编辑后重跑规则用 exception_checks._async_run_exception_checks(步骤 A 已搬)。
# ============================================================


# ============================================================
# 第 6.0 批 · ERP 推送(支柱 3)
# ============================================================

# 上述 ERP 推送 15 路由 + _check_push_access + 6 model + _strip_endpoint_for_response
# + _fetch_listing_with_retry 已抽到 erp_routes.py(REFACTOR-B1 · 2026-05-25)·
# 顶部 from erp_routes import router as erp_router · app.include_router(erp_router)。
# ⚠️ 铁律 #10 async tripwire(局部 import asyncio as _asyncio + to_thread)随路由搬走。


# ERP 推送日志/重试/批量路由(debug-xlsx / push_status / logs / stats / retry /
# batch-retry / batch-delete)已随 erp_routes.py 一并抽出(REFACTOR-B1 · 2026-05-25)。


# ============================================================
# 第 5.1 批 · 泰国 RD 税务 API(校验+同步)· RdQueryRequest + _check_rd_access + 4 路由
# 已抽到 rd_routes.py(REFACTOR-B1 · 2026-05-25)· app.include_router(rd_router)
# ============================================================


# ============================================================
# v0.7 智能归档 + v0.13 重复发票检测设置(3 model + 2 helper + 5 路由)
# 已抽到 settings_routes.py(REFACTOR-B1 · 2026-05-25)· app.include_router(settings_router)
# (注:/api/archive/rename-preview 也一并搬出 · 它原先排在下方 gemini-key 墓碑注释之后)
# ============================================================


# ============================================================
# v0.15 · 用户自带 Gemini API Key
# 设计:
#   GET  · 读遮罩信息(安全)
#   PUT  · 保存 key
#   POST /test · 用 key 做一次最小调用验证有效
# v118.35.0.16 · /api/settings/gemini-key GET/PUT/POST routes 永久下线 · credits 系统不需要用户自带 key


# ============================================================
# 静态 + 根路由
# ============================================================
app.mount("/static", StaticFiles(directory="static"), name="static")


# (静态页面路由 / · /login · /home · /admin · /admin/{rest} → pages_routes.py · REFACTOR-B1)


# /api/version → meta_aliases_routes.py(REFACTOR-B1 · 2026-05-28)
# 注意:每次部署改 release_notes 时改 meta_aliases_routes.py 里的字典(铁律 #6 · 4 语)


# (/reset · /terms · /privacy → pages_routes.py · REFACTOR-B1)


# Google + LINE OAuth(start/callback 各 2 路由 · 共用 _oauth_state_cache + helpers)
# 已抽到 oauth_routes.py(REFACTOR-B1 · 2026-05-28)


# /api/me/needs_email + /api/me/line_complete_email → line_account_merge_routes.py(REFACTOR-B1)


# ============================================================
# v118.27.6 · SMTP 邮件 + 注册邮箱验证码 → auth_email_code_routes.py(REFACTOR-B1)


# _build_verification_email_html / _RE_EMAIL_V276 / SendEmailCodeRequest / VerifyEmailCodeRequest /
# send_email_code / verify_email_code 已抽到 auth_email_code_routes.py(REFACTOR-B1)


# (LINE 绑定 API + /api/me/lang → line_binding_routes.py · REFACTOR-B1)


# ------------------------------------------------------------
# T1 · LINE Webhook(v0.19.0 · 签名校验 + 事件分发)
# 图片 OCR 留到 T1 轮 3
# ------------------------------------------------------------


# LINE webhook 主路由 + _normalize_line_lang/_ev_lang/_follow_lang/_handle_line_event/
# _handle_line_text → line_webhook_routes.py(REFACTOR-B1)· _handle_line_image_ocr 留 app.py
# (依赖 _ocr_* helpers · webhook 里通过 lazy `from app import _handle_line_image_ocr` 调到)


# ============================================================
# T1 轮 3 · LINE 图片 OCR 后台任务(v0.19.0)
# ============================================================


async def _handle_line_image_ocr(
    bound_user: dict,
    line_user_id: str,
    message_id: str,
    lang: str,
    filename: str = None,
):
    """
    异步处理 LINE 图片/文件消息:
      1. 下载内容
      2. 按网页上传同一支持清单喂 OCR pipeline
      3. 插入 ocr_history(source='line_bot')
      4. 非缓存成功识别后按 credits 定价扣费
      5. push 结果给用户
    """
    try:
        # 1. 下载
        file_bytes = line_client.download_message_content(message_id)
        filename = filename or f"line_{message_id}.jpg"
        if not file_bytes:
            line_client.push_text(line_user_id, line_client.t_ocr(lang, "err_download"))
            return
        if not _ocr_is_supported_file(filename):
            line_client.push_text(line_user_id, line_client.t_line(lang, "unsupported"))
            return

        # 2. 用户 / credits 检查(复用网页入口的 credits 逻辑)
        user_fresh = db.find_user_by_id(bound_user["id"])
        if not user_fresh:
            line_client.push_text(line_user_id, line_client.t_ocr(lang, "err_plan"))
            return

        # 3. 文件指纹缓存查找:命中则跳 OCR + 跳扣费
        file_hash = _ocr_content_hash(file_bytes)
        cached = _ocr_get_cached(user_fresh, file_hash)
        if cached:
            logger.info(f"[line_ocr] 命中文件缓存 (hash={file_hash[:12]}...) hid={cached['id']}")
            # 跑异常 hook(同网页缓存命中分支 · 不重复扣配额)
            try:
                import asyncio as _asyncio_exc_lc

                _cached_pages = cached.get("pages") or []
                _primary = next(
                    (
                        p
                        for p in _cached_pages
                        if not p.get("is_duplicate") and not p.get("is_copy")
                    ),
                    None,
                )
                _primary = _primary or (_cached_pages[0] if _cached_pages else None)
                _cf = (_primary or {}).get("fields") or {}
                _exc_total_c = None
                _raw_t_c = _cf.get("total_amount")
                if _raw_t_c:
                    try:
                        _exc_total_c = float(str(_raw_t_c).replace(",", "").strip())
                    except Exception as e:
                        logger.warning(f"[line_cache] total_amount 解析失败: {e}")
                _asyncio_exc_lc.create_task(
                    _async_run_exception_checks(
                        history_id=str(cached["id"]),
                        user_id=str(user_fresh["id"]),
                        tenant_id=(
                            str(user_fresh.get("tenant_id"))
                            if user_fresh.get("tenant_id")
                            else None
                        ),
                        seller_name=_cf.get("seller_name"),
                        invoice_no=_cf.get("invoice_number"),
                        total_amount=_exc_total_c,
                        confidence=cached.get("confidence"),
                        duplicate=None,
                        fields=_cf,
                    )
                )
                logger.info(f"  🛡  [LINE Cache] 异常检测已入队 · hid={cached['id']}")
            except Exception as _e_lc:
                logger.warning(f"[line_ocr] 缓存异常检测入队失败: {_e_lc}")
            # 推 cached 结果给用户(模拟 OCR 完成)
            reply_txt = line_client.format_ocr_result_for_line(
                lang, cached.get("pages") or [], invoice_count=len(cached.get("pages") or [])
            )
            line_client.push_text(line_user_id, reply_txt)
            return

        quote = _ocr_billing_quote(user_fresh, file_bytes, filename, max_pages=50)
        if not quote.get("allowed"):
            code = quote.get("error_code")
            if code == "insufficient_balance":
                line_client.push_text(line_user_id, line_client.t_ocr(lang, "err_quota"))
            else:
                line_client.push_text(line_user_id, line_client.t_ocr(lang, "err_ocr"))
            return

        # 4. OCR · 新 pipeline 唯一路径
        own_key = (
            user_fresh.get("gemini_api_key") or user_fresh.get("custom_gemini_api_key") or ""
        ).strip()
        api_key = own_key or None
        # 检查 API key 可用性(用户自带或系统默认)
        if not api_key and not os.environ.get("GEMINI_API_KEY", "").strip():
            line_client.push_text(line_user_id, line_client.t_ocr(lang, "err_plan"))
            return

        try:
            from services.ocr.legacy_adapter import pipeline_result_to_legacy_dict

            _pipe_res = _ocr_run_pipeline_file(
                file_bytes,
                filename,
                api_key=api_key,
                max_pages=50,
            )
            result = pipeline_result_to_legacy_dict(_pipe_res)
            _pipeline_cost_thb = float(_pipe_res.estimated_cost_thb)
            logger.info(
                f"🆕 [line_ocr] pipeline_v1 · pages={_pipe_res.page_count} "
                f"· cost=฿{_pipeline_cost_thb:.4f}"
            )
        except Exception as _pipe_err:
            logger.error(f"[line_ocr] pipeline 识别失败: {type(_pipe_err).__name__}: {_pipe_err}")
            line_client.push_text(line_user_id, line_client.t_ocr(lang, "err_ocr"))
            return

        pages = result.get("pages") or []
        if not pages:
            line_client.push_text(line_user_id, line_client.t_ocr(lang, "err_ocr"))
            return
        if _ocr_all_pages_not_invoice(pages):
            line_client.push_text(line_user_id, line_client.t_ocr(lang, "err_ocr"))
            return

        # 5. 写 history(source='line_bot')
        # file_hash 已在 3.5 计算(v118.22.0.3)
        try:
            hid = insert_ocr_history(
                user_id=str(user_fresh["id"]),
                tenant_id=str(user_fresh.get("tenant_id")) if user_fresh.get("tenant_id") else None,
                filename=filename,
                page_count=int(quote.get("page_count") or result.get("page_count") or len(pages)),
                pages=pages,
                confidence=result.get("confidence") or "unknown",
                elapsed_ms=result.get("elapsed_ms") or 0,
                file_size_kb=len(file_bytes) // 1024,
                file_hash=file_hash,
                source="line_bot",
                source_ref=line_user_id,
            )
        except Exception as e:
            logger.warning(f"[line_ocr] 写 history 失败(不影响回复): {e}")
            hid = None
        if hid:
            try:
                import asyncio as _asyncio_charge_l

                _asyncio_charge_l.create_task(
                    _asyncio_charge_l.to_thread(
                        _ocr_charge_success,
                        user_fresh,
                        quote,
                        str(hid),
                        f"LINE OCR · {filename} · {str(hid)[:8]}",
                    )
                )
            except Exception as _chg_e:
                logger.warning(f"[line_ocr] credits charge dispatch failed: {_chg_e}")

        # LINE 入口 cost 埋点(pipeline 唯一路径,100% 记录)
        try:
            _line_in = sum(int(p.get("input_tokens") or 0) for p in pages)
            _line_out = sum(int(p.get("output_tokens") or 0) for p in pages)
            db.log_ocr_cost(
                user_id=str(user_fresh["id"]),
                tenant_id=str(user_fresh.get("tenant_id")) if user_fresh.get("tenant_id") else None,
                history_id=hid,
                engine="pipeline_v1",
                pages=len(pages),
                input_tokens=_line_in,
                output_tokens=_line_out,
                cost_thb=_pipeline_cost_thb,
                elapsed_ms=int(result.get("elapsed_ms") or 0),
            )
            logger.info(f"💰 [line_ocr] cost log · ฿{_pipeline_cost_thb:.4f}")
        except Exception as _ce:
            logger.warning(f"[line_ocr] cost log failed (non-blocking): {_ce}")

        # 5.5 · 异常栏 hook(v118.22.0.2 修复 · LINE 入口此前漏挂 · 致 LINE 票据从不进 5 类规则)
        # v118.22.0.3 · 增加 duplicate 预检 · 让 LINE 票据也享有「重复发票拦截」防护
        if hid:
            try:
                import asyncio as _asyncio_exc_l

                _primary = pages[0] if pages else {}
                _f = _primary.get("fields") or {}
                _exc_total = None
                _raw_t = _f.get("total_amount")
                if _raw_t:
                    try:
                        _exc_total = float(str(_raw_t).replace(",", "").strip())
                    except Exception as e:
                        logger.warning(f"[line_ocr_exc] total_amount 解析失败: {e}")
                # duplicate 检测(同网页入口)
                _dup = None
                try:
                    _dup_raw = db.check_duplicate_invoice(
                        user_id=str(user_fresh["id"]),
                        invoice_no=_f.get("invoice_number"),
                        invoice_date=_f.get("invoice_date"),
                        seller_name=_f.get("seller_name"),
                        total_amount=_exc_total,
                        exclude_id=str(hid),
                    )
                    if _dup_raw:
                        _dup = {
                            "level": _dup_raw.get("level"),
                            "matched_fields": _dup_raw.get("matched_fields"),
                            "match": _dup_raw.get("match"),
                        }
                except Exception as _e_dup:
                    logger.warning(f"[line_ocr] duplicate 检测失败(不影响 hook): {_e_dup}")
                _asyncio_exc_l.create_task(
                    _async_run_exception_checks(
                        history_id=str(hid),
                        user_id=str(user_fresh["id"]),
                        tenant_id=(
                            str(user_fresh.get("tenant_id"))
                            if user_fresh.get("tenant_id")
                            else None
                        ),
                        seller_name=_f.get("seller_name"),
                        invoice_no=_f.get("invoice_number"),
                        total_amount=_exc_total,
                        confidence=result.get("confidence"),
                        duplicate=_dup,
                        fields=_f,
                    )
                )
                logger.info(
                    f"  🛡  [LINE] 异常检测已入队 · hid={hid} · dup={'有' if _dup else '无'}"
                )
            except Exception as _e:
                logger.warning(f"[line_ocr] 异常检测入队失败(不影响推送): {_e}")

        # 6. 推送识别结果
        reply_txt = line_client.format_ocr_result_for_line(lang, pages, invoice_count=len(pages))
        line_client.push_text(line_user_id, reply_txt)
        logger.info(f"[line_ocr] 完成 · user={user_fresh['id']} · hid={hid}")

    except Exception as e:
        logger.exception(f"[line_ocr] 未知异常: {e}")
        try:
            line_client.push_text(line_user_id, line_client.t_ocr(lang, "err_ocr"))
        except Exception as _pe:
            logger.warning(f"[line_ocr] err 通知 push_text 失败: {_pe}")


# ============================================================
# v22 超级管理员后台 API
# ============================================================
# 访问条件:JWT 里 is_super_admin = true
# 这是唯一有权限查看 / 修改所有租户的入口
# ============================================================


# 已抽到 admin_migration_routes.py(REFACTOR-B1 · 2026-05-25 · 超管迁移/RLS 7 路由)·
# @router 注册 + app.include_router(admin_migration_router)


# 已抽到 tenant_routes.py(REFACTOR-B1 · 2026-05-25 · 租户管理 6 路由 + 3 model)·
# @router 注册 + app.include_router(tenant_router)


# 已抽到 admin_cost_routes.py(REFACTOR-B1 · 2026-05-25 · 超管成本/收入/监控 10 路由)·
# @router 注册 + app.include_router(admin_cost_router)


# ============================================================
# v108 · Google AI Studio 余额追踪 · 3 个 API 路由
# 半自动 · 管理员每周更新真实余额 · 系统自动校准
# ============================================================


# 2026-05-25 · Earn 后台改造:删 Google "实际余额" 卡(手动录入值会误导成自动余额)·
# 余额改由 admin 直达两个 Google 计费页自查(Cloud Vision + Gemini AI Studio)· 见 admin.html 引擎计费入口卡。
# 已删:GET/POST /api/admin/billing/balance + GET /api/admin/billing/history + BalanceUpdateRequest +
#       db.get_balance_summary / db.add_balance_log。表 billing_balance_log 与 db.get_latest_balance 保留
#       (vat_excel_routes 仍用 calibration_factor 兜底)。


# ============================================================
# v107 · 客户(Client)实体 API
# REFACTOR-B1(2026-05-24)· /api/clients 5 路由已抽到 clients_routes.py ·
# assign_client(/api/history/{id}/assign_client)也已并入 history_routes.py(REFACTOR-B1 · 2026-05-25)·
# AssignClientRequest model 随之搬走 · history 组 11 路由现全在 history_routes。
# ============================================================


# 已抽到 tenant_routes.py(REFACTOR-B1 · 2026-05-25 · admin tenant CRUD + /api/me/tenant-usage)·
# @router 注册 + app.include_router(tenant_router)


# ============================================================
# v23 · 用户管理(超管)/ 员工管理(老板)/ 操作日志 / users.csv / 级联删除
# 4 model + CascadeDeleteRequest + 15 路由 已抽到 admin_users_routes.py
# (REFACTOR-B1 · 2026-05-25)· 顶部 from admin_users_routes import router as
# admin_users_router · app.include_router(admin_users_router)。AdminUpdateTenant* /
# EmployeeToggleRequest 仍在 tenant_routes / team_routes(admin_users 从那 import)。
# ============================================================


# ============================================================
# v118.18 · 推荐分类(supplier_categories)前端 API
# ============================================================


# 已抽到 categories_routes.py(REFACTOR-B1 · 2026-05-25 · /api/categories 单路由)·
# 顶部 from categories_routes import router as categories_router · app.include_router(categories_router)


# ============================================================
# v118.22.1 · 智能提醒(Notifications)· 数据底座 + 测试发送
# 触发 hook 接入留 v118.22.1.1 做(异常 hook + 大额 hook)
# ============================================================
# 模板常量已在 v118.22.1.1 helper 段(本文件 1900 多行处)统一声明


# 通知规则 models/校验/6 路由已抽到 notification_routes.py(REFACTOR-B1 · 2026-05-24)


# ============================================================
# v118.27.0 · ERP 映射底座(客户/科目/税码/商品 12 路由)
# 已抽到 erp_mappings_routes.py(REFACTOR-B1 · 2026-05-25)·
# @router 注册 + app.include_router(erp_mappings_router)
# ============================================================


# 已抽到 erp_xero_routes.py(REFACTOR-B1 · 2026-05-25 · ERP 连接器聚合 + Xero 8 路由)·
# _ensure_fresh_xero_token 也搬过去 · 顶部 from erp_xero_routes import router, _ensure_fresh_xero_token
# @router 注册 + app.include_router(erp_xero_router)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app:app", host="0.0.0.0", port=int(os.environ.get("PORT", "7860")), reload=True)
