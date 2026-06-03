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
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

# app.db 命名空间(大量测试 monkeypatch app.db.xxx · 路由经 app.db 调 · 必须保留)
from core import db  # noqa: F401

try:
    from services.line_binding import line_client  # T1 · LINE Bot(v0.19.0)
except ImportError:
    line_client = None  # line_client.py 不在 pearnly 仓库 · 文件需单独部署到服务器
from routes.report_routes import router as reports_router  # v109.0
from routes.ocr_recognize_routes import (
    router as ocr_recognize_router,
)  # REFACTOR-WB-app · 2026-06-01
from services.auth.auth_signup import router as signup_router  # v109.3
from routes.auth_email_code_routes import (
    router as auth_email_code_router,
)  # REFACTOR-B1 · 2026-05-28
from routes.line_account_merge_routes import (
    router as line_account_merge_router,
)  # REFACTOR-B1 · 2026-05-28
from routes.oauth_routes import (
    router as oauth_router,
)  # REFACTOR-B1 · Google+LINE OAuth · 2026-05-28
from routes.line_webhook_routes import (
    router as line_webhook_router,
)  # REFACTOR-B1 · LINE Bot webhook · 2026-05-28
from routes.login_routes import router as login_router  # REFACTOR-B1 · 主登录 · 2026-05-28
from routes.meta_aliases_routes import (
    router as meta_aliases_router,
)  # REFACTOR-B1 · /api/version + v1 OCR 别名 · 2026-05-28
from routes.ocr_export_routes import (
    router as ocr_export_router,
)  # REFACTOR-B1 · OCR 配额+导出 4 路由 · 2026-05-28
from routes.recon_routes import router as recon_router  # v118.32.0
from routes.recon_jobs_routes import (
    router as recon_jobs_router,
)  # ADR-005 #15 · 对账异步 submit/状态
from routes.import_routes import router as import_router  # ADR-006 · 通用模板学习层 列映射接口
from routes.vat_excel_routes import router as vat_excel_router  # v118.32.4.9.5 · Excel 公式对账内测
from routes.notification_routes import router as notification_router  # REFACTOR-B1 · 2026-05-24
from routes.clients_routes import (
    router as clients_router,
)  # REFACTOR-B1 · 客户管理 5 路由 · 2026-05-24
from routes.team_routes import router as team_router  # REFACTOR-B1 · 员工管理 7 路由 · 2026-05-25
from routes.email_ingest_routes import (
    router as email_ingest_router,
)  # REFACTOR-B1 · 邮箱抓取 6 路由 · 2026-05-25
from routes.rd_routes import router as rd_router  # REFACTOR-B1 · 泰国 RD 税务 4 路由 · 2026-05-25
from routes.workspace_routes import (
    router as workspace_router,
)  # B4 · workspace 账套主体(非破坏) · 2026-05-25
from routes.categories_routes import (
    router as categories_router,
)  # REFACTOR-B1 · 分类 1 路由 · 2026-05-25
from routes.pages_routes import (
    router as pages_router,
)  # REFACTOR-B1 · 静态页面 + 公开 meta 12 路由 · 2026-05-25
from routes.me_routes import (
    router as me_router,
)  # REFACTOR-B1 · /api/me 家族 3 路由 + UserInfo · 2026-05-25
from routes.line_binding_routes import (
    router as line_binding_router,
)  # REFACTOR-B1 · LINE 绑定 + 偏好语言 4 路由 · 2026-05-25
from routes.erp_routes import (  # REFACTOR-B1 · ERP 推送 15 路由 · 2026-05-25
    router as erp_router,
)
from routes.dms_routes import (  # MR.ERP DMS 汽车销售 · 身份证→订车单 1 路由 · 2026-05-31
    router as dms_router,
)
from routes.admin_users_routes import (
    router as admin_users_router,
)  # REFACTOR-B1 · 超管用户/员工 15 路由 · 2026-05-25

# REFACTOR-B1 · OCR 异常检测链单一来源 re-export(契约 test_exception_checks_contract;
# 实际消费者已搬到 services/ocr/recognize/* 与 line_image_ocr · app 自身不再直接调)。
from services.exceptions.exception_checks import _async_run_exception_checks  # noqa: F401
from routes.history_routes import (
    router as history_router,
)  # REFACTOR-B1 · OCR 历史 11 路由(含 assign_client) · 2026-05-25
from routes.settings_routes import (
    router as settings_router,
)  # REFACTOR-B1 · 归档/查重设置 5 路由 · 2026-05-25
from routes.erp_mappings_routes import (
    router as erp_mappings_router,
)  # REFACTOR-B1 · ERP 映射 12 路由 · 2026-05-25
from routes.bank_recon_routes import (
    router as bank_recon_router,
)  # REFACTOR-B1 · 银行对账 11 路由 · 2026-05-25
from routes.admin_migration_routes import (
    router as admin_migration_router,
)  # REFACTOR-B1 · 超管迁移/RLS 7 路由 · 2026-05-25
from routes.admin_cost_routes import (
    router as admin_cost_router,
)  # REFACTOR-B1 · 超管成本/收入/监控 10 路由 · 2026-05-25
from routes.tenant_routes import (
    router as tenant_router,
)  # REFACTOR-B1 · 租户管理 6 路由 · 2026-05-25
from routes.admin_logs_routes import (
    router as admin_logs_router,
)  # REFACTOR-B1 · 操作/审计日志 4 路由 · 2026-05-25
from routes.erp_xero_routes import (
    router as erp_xero_router,
)  # REFACTOR-B1 · ERP 连接器聚合 + Xero 8 路由 · 2026-05-25
from routes.exceptions_routes import (
    router as exceptions_router,
)  # REFACTOR-B1 · 异常处理 8 路由 · 2026-05-24
from routes.billing_routes import (
    router as billing_router,
)  # 阶段 5 Task 5.1 · 抽 11 个 billing 路由(2026-05-22)
from routes.admin_diagnostics_routes import (
    router as admin_diagnostics_router,
)  # 阶段 5 Task 5.2 · 抽 5 个 admin diagnostics + internal/deploy* 路由(2026-05-22)
from core.route_helpers import (  # 公共鉴权 helper;app 再导出锁单一来源(契约 test_route_helpers_contract/test_tid_helper_single_source)
    _plan_permissions,  # noqa: F401
    _tid,  # noqa: F401
)
from services.static_assets import read_frontend_version, purge_stale_static_gz  # REFACTOR-WA-B1
from services.erp.auto_push import (  # ERP 自动推送编排;app 再导出锁单一来源(契约 test_auto_push_module_contract)
    _auto_push_history,  # noqa: F401
    _auto_push_smart_routed,  # noqa: F401
    _trigger_auto_push_all,  # noqa: F401
    _erp_seller_routing_enabled,  # noqa: F401
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
app.include_router(ocr_recognize_router)  # REFACTOR-WB-app · OCR 识别主路由(2026-06-01)
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


# /api/ocr/recognize 主路由(+ _choose_engine)→ ocr_recognize_routes.py
# (REFACTOR-WB-app · 2026-06-01)· 缓存命中/多发票入库/auto-push 三段已拆到
# services/ocr/recognize/{cache,persist,autopush}.py · view 仅见薄 router。


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


# v118.20.1 · 异常栏规则检查 + 智能提醒整条链 → exception_checks.py(REFACTOR-B1 · 单一来源 re-export 见顶部 import)。


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


# v118.35.0.16 · /api/settings/gemini-key(GET/PUT/POST)永久下线 · credits 系统不需用户自带 key


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
