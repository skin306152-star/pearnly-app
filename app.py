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
)
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
from dms_routes import (  # MR.ERP DMS 汽车销售 · 身份证→订车单 1 路由 · 2026-05-31
    router as dms_router,
)
from admin_users_routes import (
    router as admin_users_router,
)  # REFACTOR-B1 · 超管用户/员工 15 路由 · 2026-05-25

# REFACTOR-B1 · OCR 异常检测链单一来源 re-export(契约 test_exception_checks_contract;
# 实际消费者已搬到 services/ocr/recognize/* 与 line_image_ocr · app 自身不再直接调)。
from exception_checks import _async_run_exception_checks  # noqa: F401
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
    content_hash as _ocr_content_hash,
    get_cached_history as _ocr_get_cached,
)
from services.ocr.recognize.cache import serve_cache_hit  # REFACTOR-WB-app · 2026-06-01
from services.ocr.recognize.persist import persist_invoices  # REFACTOR-WB-app · 2026-06-01
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
app.include_router(dms_router)  # MR.ERP DMS · 身份证→订车单 1 路由(2026-05-31)
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
        return serve_cache_hit(
            cached=cached,
            user=user,
            plan=plan,
            _erp_mode=_erp_mode,
            file=file,
            monthly_quota=monthly_quota,
            file_hash=file_hash,
        )

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

    _persist = persist_invoices(
        result=result,
        user=user,
        confidence=confidence,
        _billing=_billing,
        _chg_kind=_chg_kind,
        _chg_units=_chg_units,
        file=file,
        content=content,
        file_hash=file_hash,
        client_id=client_id,
        _ws_client_id=_ws_client_id,
    )
    invoice_groups = _persist["invoice_groups"]
    invoice_count = _persist["invoice_count"]
    history_ids = _persist["history_ids"]
    duplicate_warnings = _persist["duplicate_warnings"]
    primary_history_id = _persist["primary_history_id"]
    primary_archive_name = _persist["primary_archive_name"]
    primary_category_tag = _persist["primary_category_tag"]

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

    # REFACTOR-WA-OCRPERF Step1 · PDF 留底后台化:响应返回后才生成 searchable PDF + save_pdf
    #   + 回填 pdf_storage_path(前端 has_pdf 届时显示下载)。字段/响应字段一字不变;
    #   留底失败只是没下载(同原 try/except 降级)。sync CPU/disk 走 to_thread 不堵 event loop。
    if history_ids:
        try:
            # asyncio 在本函数是局部名(上方 384/1075 条件分支里有 import asyncio · 编译期即
            # 把 asyncio 标记为函数局部)· 那些分支没走时 asyncio 未绑定 → 这里显式 import 绑定,
            # 防 UnboundLocalError(实测:无 auto-push 端点的账号触发过 · prod E2E 抓到)。
            import asyncio

            _pdf_pages = result.get("pages") or []
            _pdf_uid = str(user["id"])
            _pdf_tid = _tid(user)
            _pdf_hids = list(history_ids)
            _pdf_content = content

            async def _bg_pdf_backfill():
                try:
                    from services.ocr.pdf_backfill import generate_and_save_pdf

                    rel, size = await asyncio.to_thread(
                        generate_and_save_pdf, _pdf_content, _pdf_pages, _pdf_uid
                    )
                    if rel:
                        await asyncio.to_thread(
                            db.update_ocr_history_pdf_storage,
                            _pdf_hids,
                            rel,
                            size,
                            _pdf_uid,
                            _pdf_tid,
                        )
                except Exception as _bge:
                    logger.warning(f"[ocrperf] PDF 后台留底/回填失败(已忽略): {_bge}")

            asyncio.create_task(_bg_pdf_backfill())
        except Exception as _sched_err:
            logger.warning(f"[ocrperf] PDF 后台任务调度失败(已忽略): {_sched_err}")

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
# _handle_line_text → line_webhook_routes.py(REFACTOR-B1)。
# _handle_line_image_ocr(LINE 图片 OCR 后台 · ~255 行)→ services/ocr/line_image_ocr.py
# (REFACTOR-WB-app · 2026-06-01 · 纯搬家 0 逻辑改)· webhook 里 lazy import 调到。


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
