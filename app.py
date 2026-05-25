# -*- coding: utf-8 -*-
"""
Mr.Pearnly · FastAPI 主入口 (v3.5)
第 3.5 批:
  - 返回完整权限字段
  - /api/v1/ 路由前缀预留(与旧路径并存)
  - 套餐元数据端点
"""

import os
import json
import logging
from typing import Optional, List, Any, Dict
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, HTTPException, UploadFile, File, Form
from fastapi.responses import HTMLResponse, Response, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

import db  # v0.6.4 修复:新增 ERP 路由用到了 db.xxx 命名空间

try:
    import line_client  # T1 · LINE Bot(v0.19.0)
except ImportError:
    line_client = None  # line_client.py 不在 pearnly 仓库 · 文件需单独部署到服务器
from db import (
    find_user_by_username,
    update_last_login,
    increment_user_monthly_usage,
    insert_ocr_history,
)
import pdf_storage  # v114 · PDF 留底存储模块
from auth import (
    verify_password,
    create_access_token,
    get_current_user_from_request,
    get_client_ip,
)
from report_routes import router as reports_router  # v109.0
from auth_signup import router as signup_router  # v109.3
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
    flush_test_connection_caches as _flush_erp_caches,
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
    # _ensure_fresh_xero_token 单一来源在 erp_xero_routes · app.py Xero 自动推送后台函数复用
    _ensure_fresh_xero_token,
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
    _record_500,
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


def _probe_chromium_launch():
    """v118.34.11 (Zihao 2026-05-19 拍板) · Actually try to launch
    chromium. Returns {"ok": bool, "error": str?}. The Playwright
    sync_api → chromium.launch dance is what production wizard clicks
    do; if libs are missing we want to surface the same TargetClosedError
    HERE at startup, not on the first user click.

    Cheap: launches headless with the same server-side args we use in
    production (--no-sandbox / --disable-dev-shm-usage / --disable-gpu),
    grabs Browser.version(), closes everything. Usually ~1-2 s.

    Never raises. Any failure is captured into the returned dict so
    the diagnostic can be served via /api/version without 500ing.
    """
    try:
        from playwright.sync_api import sync_playwright as _sp
    except ImportError as e:
        return {"ok": False, "error": f"playwright import failed: {e}"}
    pw = None
    browser = None
    try:
        pw = _sp().start()
        browser = pw.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu",
            ],
        )
        # Browser.version is a property in playwright-python sync API,
        # not a method — calling it raises 'str object is not callable'.
        version = browser.version
        return {"ok": True, "version": version, "error": None}
    except Exception as e:
        msg = f"{type(e).__name__}: {str(e)[:300]}"
        logger.warning("[playwright-bootstrap] chromium launch probe failed: %s", msg)
        return {"ok": False, "error": msg}
    finally:
        try:
            if browser is not None:
                browser.close()
        except Exception:
            pass
        try:
            if pw is not None:
                pw.stop()
        except Exception:
            pass


def _ensure_playwright_installed():
    """v118.34.6 (Zihao 2026-05-19 拍板) · Playwright 装上的第四次尝试。

    历史:
      • v118.34.3 admin URL → 要找密钥 · 用户拒绝
      • v118.34.4 lifespan 纯后台 spawn → 5+ 分钟仍没装上 · 无可见性
      • v118.34.5 lifespan 同步装 → pip 阻塞 lifespan,旧 git-deploy.sh
        的 30s 健康检查窗口超时,部署被回滚到 v118.34.4
      • v118.34.6 (本版) · 把动作分两层:
          - 同步快查 + 立刻写状态文件 (<2 s · 不会卡 lifespan)
          - 后台 detached 跑 pip + playwright install + 自 restart
          - 配合 git-deploy.sh 新版 heredoc · 下次部署起 deploy.sh 自己
            会跑 pip install -r requirements.txt + playwright install
            chromium · 不再依赖 lifespan 自己装

    诊断字段写到 /tmp/pearnly-playwright-status.json · /api/version 读后
    暴露给用户 · 浏览器直接看。
    """
    import importlib
    import json
    import os as _os
    import shutil
    import subprocess
    import sys
    import time as _t

    status_path = "/tmp/pearnly-playwright-status.json"

    def _write_status(**kwargs):
        try:
            payload = {"ts": int(_t.time()), **kwargs}
            with open(status_path, "w") as f:
                json.dump(payload, f)
        except Exception:
            pass

    # ── Quick probe: is pip package importable RIGHT NOW? ──
    pip_importable = False
    pip_version = None
    try:
        importlib.import_module("playwright.sync_api")
        pip_importable = True
        try:
            pip_version = getattr(importlib.import_module("playwright"), "__version__", None)
        except Exception:
            pip_version = None
    except ImportError:
        pip_importable = False

    # ── Quick probe: chromium binary on disk? ──
    cache_root = _os.environ.get("PLAYWRIGHT_BROWSERS_PATH") or _os.path.expanduser(
        "~/.cache/ms-playwright"
    )
    chromium_installed = False
    chromium_dir = None
    try:
        if _os.path.isdir(cache_root):
            for name in _os.listdir(cache_root):
                if name.startswith("chromium") and _os.path.isdir(_os.path.join(cache_root, name)):
                    chromium_installed = True
                    chromium_dir = _os.path.join(cache_root, name)
                    break
    except Exception:
        pass

    # Write the status snapshot up-front so /api/version reports
    # something even if we're about to spawn a long-running install.
    _write_status(
        playwright_installed=pip_importable,
        chromium_installed=chromium_installed,
        chromium_dir=chromium_dir,
        pip_version=pip_version,
        python_bin=sys.executable,
        effective_uid=_os.getuid() if hasattr(_os, "getuid") else None,
        attempted_at_startup=True,
    )

    if pip_importable and chromium_installed:
        logger.info(
            "[playwright-bootstrap] both pip package + chromium binary ready · skipping install"
        )
        # v118.34.11 · even when both pieces look OK, actually try to
        # launch chromium briefly. The v118.34.10 production failure
        # was exactly this: pip + binary both present but the launch
        # crashed because system libs (libnss3, libgbm1, etc) were
        # missing. The real-launch probe writes the result into the
        # status file so /api/version can surface it.
        launch_result = _probe_chromium_launch()
        _write_status(
            playwright_installed=pip_importable,
            chromium_installed=chromium_installed,
            chromium_dir=chromium_dir,
            chromium_can_launch=launch_result["ok"],
            chromium_launch_error=launch_result.get("error"),
            pip_version=pip_version,
            python_bin=sys.executable,
            effective_uid=_os.getuid() if hasattr(_os, "getuid") else None,
            attempted_at_startup=True,
        )
        # If launch fails, fall through to spawn install-deps in
        # background. install-deps is idempotent so it's safe to call
        # even when nothing's missing — it'll just no-op the apt steps.
        if not launch_result["ok"]:
            logger.warning(
                "[playwright-bootstrap] chromium launch FAILED at startup: %s · "
                "spawning install-deps in background",
                launch_result.get("error"),
            )
        else:
            return  # All three pieces verified · nothing to spawn.

    # ── Missing pieces · spawn detached install + restart ──
    # We DO NOT block lifespan here. git-deploy.sh's health-check
    # window is 30 s on the legacy heredoc, 90 s on the new one. Pip
    # alone is usually <15 s; chromium is 30-120 s; doing them in
    # lifespan blocks past 30 s on the first cold deploy → rollback,
    # which is exactly the v118.34.5 trap.
    sentinel = "/tmp/pearnly-playwright-installing"
    if _os.path.exists(sentinel):
        logger.info(
            "[playwright-bootstrap] sentinel exists — install already in progress, "
            "not spawning a second one"
        )
        return

    # v118.34.7 (Zihao 2026-05-19 拍板) · 真正的根因找到了:
    # /api/version 显示 chromium_installed=true 但 playwright_installed=false。
    # 这意味着 `python3 -m playwright install chromium` 跑成功了
    # (chromium 二进制在 /root/.cache/ms-playwright/chromium_headless_shell-*),
    # 但 mrpilot 的 Python 进程 import playwright.sync_api 仍失败。
    #
    # 原因:之前的 install 命令用 `pip3` (system pip · /usr/bin/pip3)
    # 装到 system site-packages,但 mrpilot 跑在 venv 里(或不同 Python
    # 解释器),它的 import 路径看不到 system site-packages。
    #
    # 修法:全部命令用 `{sys.executable} -m pip` · 这样 pip 和 mrpilot
    # 是同一个解释器,site-packages 同一份。chromium 同理用
    # `{sys.executable} -m playwright`。
    py_bin = sys.executable or shutil.which("python3") or "python3"
    # v118.34.11 · 三段式后台装:pip → chromium binary → chromium 系统依赖(apt)
    # 第 3 步是 v118.34.10 漏掉的 · 没装 lib* 时 chromium.launch 立刻
    # TargetClosedError(用户在生产看到的报错)。`playwright install-deps`
    # 是 idempotent · 已装的 apt 包跳过 · 失败也不阻断 restart。
    cmd = (
        f"set -e; "
        f"touch {sentinel}; "
        f"echo '[playwright-bootstrap] $(date) starting · py={py_bin}' "
        f"  >> /var/log/mrpilot-deploy.log; "
        # 用 mrpilot 自己的 python 跑 pip · 保证装到 mrpilot 的 site-packages
        f"if ! {py_bin} -m pip install playwright >> /var/log/mrpilot-deploy.log 2>&1; then "
        f"  {py_bin} -m pip install playwright --break-system-packages "
        f"    >> /var/log/mrpilot-deploy.log 2>&1 || true; "
        f"fi; "
        f"echo '[playwright-bootstrap] $(date) pip done, downloading chromium...' "
        f"  >> /var/log/mrpilot-deploy.log; "
        f"{py_bin} -m playwright install chromium "
        f"  >> /var/log/mrpilot-deploy.log 2>&1 || true; "
        f"echo '[playwright-bootstrap] $(date) chromium binary done, installing system deps...' "
        f"  >> /var/log/mrpilot-deploy.log; "
        f"{py_bin} -m playwright install-deps chromium "
        f"  >> /var/log/mrpilot-deploy.log 2>&1 || true; "
        f"echo '[playwright-bootstrap] $(date) system deps done, restarting mrpilot...' "
        f"  >> /var/log/mrpilot-deploy.log; "
        f"systemctl restart mrpilot >> /var/log/mrpilot-deploy.log 2>&1 || true; "
        f"rm -f {sentinel}"
    )
    # v118.34.9 · revert to simple Popen. systemd-run might block lifespan
    # or fail if the unit can't be created in mrpilot's cgroup context.
    # The simple detached Popen with start_new_session=True survives if
    # the install completes before mrpilot's next restart (~10-60 s for
    # pip alone since chromium is already on disk).
    try:
        subprocess.Popen(
            ["bash", "-c", cmd],
            close_fds=True,
            start_new_session=True,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        logger.warning(
            "[playwright-bootstrap] spawned plain detached install + restart. "
            "Watch /api/version playwright.playwright_installed."
        )
    except Exception as e:
        logger.warning("[playwright-bootstrap] spawn failed: %s", e)
        _write_status(
            playwright_installed=pip_importable,
            chromium_installed=chromium_installed,
            pip_install_error=f"spawn failed: {type(e).__name__}: {e}",
        )


def _read_playwright_status():
    """Read the status snapshot written by _ensure_playwright_installed.
    Returns a dict with at minimum playwright_installed / chromium_installed
    (both falsy if file missing). Used by /api/version to surface state.
    Also re-probes chromium on every call so the user can see install
    progress in real time without waiting for the next restart."""
    import json
    import os as _os

    status_path = "/tmp/pearnly-playwright-status.json"
    payload = {}
    try:
        with open(status_path) as f:
            payload = json.load(f) or {}
    except Exception:
        payload = {}

    # Re-probe chromium live (cheap dir check); pip import status is
    # what was true at startup and shouldn't change without a restart.
    try:
        cache_root = _os.environ.get("PLAYWRIGHT_BROWSERS_PATH") or _os.path.expanduser(
            "~/.cache/ms-playwright"
        )
        live_chromium = False
        if _os.path.isdir(cache_root):
            for name in _os.listdir(cache_root):
                if name.startswith("chromium") and _os.path.isdir(_os.path.join(cache_root, name)):
                    live_chromium = True
                    break
        payload["chromium_installed"] = live_chromium
    except Exception:
        pass

    # v118.34.9 · add deploy log tail so the user can see WHY repeated
    # deploys roll back without SSH. Limited to last 40 lines and grep
    # filtered to interesting markers to keep payload reasonable.
    deploy_log_tail = ""
    try:
        with open("/var/log/mrpilot-deploy.log") as f:
            lines = f.readlines()[-40:]
            deploy_log_tail = "".join(lines)[-3000:]
    except Exception as e:
        deploy_log_tail = f"(log unreadable: {e})"

    # Also expose any sentinels still on /tmp so we can spot stuck installs.
    sentinels = []
    try:
        for name in _os.listdir("/tmp"):
            if name.startswith("pearnly-"):
                sentinels.append(name)
    except Exception:
        pass

    return {
        "playwright_installed": bool(payload.get("playwright_installed")),
        "chromium_installed": bool(payload.get("chromium_installed")),
        # v118.34.11 · most authoritative signal · true only if a real
        # chromium.launch + version() round-trip succeeded at last
        # startup. False here with True for the two above means system
        # libs (libnss3, libgbm1, ...) are missing — see chromium_launch_error.
        "chromium_can_launch": bool(payload.get("chromium_can_launch")),
        "chromium_launch_error": payload.get("chromium_launch_error"),
        "playwright_version": payload.get("pip_version"),
        "pip_install_error": payload.get("pip_install_error"),
        "chromium_dir": payload.get("chromium_dir"),
        # v118.34.7 · expose the python interpreter mrpilot is using.
        # If this differs from the pip target, we know there's a
        # site-packages mismatch causing the "chromium ok, pip not"
        # paradox.
        "python_bin": payload.get("python_bin"),
        "effective_uid": payload.get("effective_uid"),
        "ts": payload.get("ts"),
        "deploy_log_tail": deploy_log_tail,
        "sentinels": sentinels,
    }


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 Mr.Pearnly 启动中...")

    # v118.35.0.28 P0 安全 self-check (体检 2026-05-21)
    # /internal/deploy 现在 fail-closed · secret 缺失会拒服务 ·
    # 启动时早期告警 · 不要等到 GitHub webhook 来才发现没配。
    import os as _os

    if not _os.environ.get("GITHUB_WEBHOOK_SECRET"):
        logger.critical(
            "⚠️ GITHUB_WEBHOOK_SECRET missing — /internal/deploy will return 503 · "
            "auto-deploy via GitHub webhook is DISABLED until env var is set"
        )

    # v0.15.1 · 不再自动创建 demo 账号 · 账号由 Supabase 管理
    # 如需恢复自动创建 · 取消下方注释:
    # try:
    #     ensure_demo_account()
    # except Exception as e:
    #     logger.error(f"启动时初始化 demo 失败: {e}")
    # v0.8.1 · 启动时清理过期历史
    try:
        cleaned = db.cleanup_expired_history(free_days=7, plus_days=90, pro_days=365)
        if cleaned > 0:
            logger.info(f"🧹 已清理 {cleaned} 条过期历史")
    except Exception as e:
        logger.warning(f"启动清理过期历史失败(不影响运行): {e}")

    # v106 · 成本追踪表初始化
    try:
        db.ensure_ocr_cost_log_table()
    except Exception as e:
        logger.warning(f"启动 ocr_cost_log 建表失败: {e}")

    # v107 · 客户实体表初始化
    try:
        db.ensure_clients_table()
    except Exception as e:
        logger.warning(f"启动 clients 建表失败: {e}")

    # B0 (2026-05-25) · workspace_clients 账套主体表(独立于买方 clients · 见 services/workspace)
    try:
        db.ensure_workspace_tables()
    except Exception as e:
        logger.warning(f"启动 workspace_clients 建表失败: {e}")

    # v118.18 · 推荐分类学习表初始化
    try:
        db.ensure_supplier_categories_table()
    except Exception as e:
        logger.warning(f"启动 supplier_categories 建表失败: {e}")

    # 批 1 改动 1 (Zihao 2026-05-19 拍板 · v118.34.33) · buyer→client 学习表
    try:
        db.ensure_buyer_to_client_table()
    except Exception as e:
        logger.warning(f"启动 buyer_to_client_memory 建表失败: {e}")

    # v118.27.5 · users.google_sub 列(Google OAuth 关联)
    try:
        db.ensure_google_sub_column()
    except Exception as e:
        logger.warning(f"启动 google_sub 列建立失败: {e}")

    # v118.28.4 · users.line_uid 列(LINE Login OAuth 关联)
    try:
        db.ensure_line_uid_column()
    except Exception as e:
        logger.warning(f"启动 line_uid 列建立失败: {e}")

    # v118.28.9 · users.password_changed_at 列(改密后旧 JWT 失效)
    try:
        db.ensure_password_changed_at_column()
    except Exception as e:
        logger.warning(f"启动 password_changed_at 列建立失败: {e}")

    # v118.27.6 · email_codes 表(注册邮箱验证码)
    try:
        db.ensure_email_codes_table()
    except Exception as e:
        logger.warning(f"启动 email_codes 建表失败: {e}")

    # v118.32.5 · gl_vat_task 表(GL vs 销项税报告 对账)
    try:
        db.ensure_gl_vat_task_table()
    except Exception as e:
        logger.warning(f"启动 gl_vat_task 建表失败: {e}")

    # v118.27.7 · 多租户改造 P0 · memberships / client_assignments / roles 三表(纯底层 · 不自动迁移)
    try:
        db.ensure_membership_tables()
    except Exception as e:
        logger.warning(f"启动 membership 建表失败: {e}")

    # v108 · 余额追踪表初始化
    try:
        db.ensure_billing_balance_table()
    except Exception as e:
        logger.warning(f"启动 billing_balance_log 建表失败: {e}")

    # v118.20.1 · 异常栏数据表初始化(exceptions + exception_whitelist)
    try:
        db.ensure_exceptions_tables()
    except Exception as e:
        logger.warning(f"启动 exceptions 建表失败: {e}")

    # v118.22.1 · 智能提醒数据表初始化(notification_rules + notification_logs)
    try:
        db.ensure_notification_tables()
    except Exception as e:
        logger.warning(f"启动 notification 建表失败: {e}")

    # v118.25 · ERP 推送自动重试 · 给 erp_push_logs 表加 retry_count / max_retries / next_retry_at 列(幂等)
    try:
        db.ensure_erp_retry_columns()
    except Exception as e:
        logger.warning(f"启动 erp_push_logs retry 列补齐失败: {e}")

    # v118.34.14 (Zihao 2026-05-19 拍板) · 把 erp_endpoints / erp_push_logs
    # 的 adapter CHECK 白名单更新到包含 'mrerp' · 之前漏写 migration 导致
    # POST /api/erp/endpoints 创建 mrerp endpoint 时 PostgreSQL 抛
    # CheckViolation → 500。这两个函数幂等 · 已包含 'mrerp' 时跳过。
    try:
        db.ensure_erp_endpoints_adapter_constraint()
    except Exception as e:
        logger.warning(f"启动 erp_endpoints adapter constraint migration 失败: {e}")
    try:
        db.ensure_erp_push_logs_adapter_constraint()
    except Exception as e:
        logger.warning(f"启动 erp_push_logs adapter constraint migration 失败: {e}")
    try:
        # ERP-2(2026-05-25):放开 erp_push_logs.status CHECK 接受 skipped_dup(防重日志落库)
        db.ensure_erp_push_logs_status_constraint()
    except Exception as e:
        logger.warning(f"启动 erp_push_logs status constraint migration 失败: {e}")

    # v118.26.2 · bank_reconcile_sessions.client_id 列(v28.1 客户分配 filter 适配)
    try:
        db.ensure_bank_recon_client_id_column()
    except Exception as e:
        logger.warning(f"启动 bank_reconcile_sessions.client_id 列补齐失败: {e}")

    # v118.27.0 · ERP 映射底座 3 张表(客户 / 科目 / 税码)
    try:
        db.ensure_erp_mapping_tables()
    except Exception as e:
        logger.warning(f"启动 erp_mapping 建表失败: {e}")

    # v118.27.4 · Xero / OAuth 通用 token 表
    try:
        db.ensure_erp_oauth_tables()
    except Exception as e:
        logger.warning(f"启动 erp_oauth 建表失败: {e}")

    # v118.32.0 · 销项税对账三张表(vat_report / reconciliation_task / reconciliation_row)
    try:
        db.ensure_vat_recon_tables()
    except Exception as e:
        logger.warning(f"启动 vat_recon 建表失败: {e}")

    # v118.32.4.10.0 · Excel 对账任务持久化表
    try:
        db.ensure_vat_recon_tasks_table()
    except Exception as e:
        logger.warning(f"启动 vat_recon_tasks 建表失败: {e}")

    # v118.33.6 · Bank Reconciliation v2 (Statement vs GL)
    try:
        db.ensure_bank_recon_v2_table()
    except Exception as e:
        logger.warning(f"启动 bank_recon_v2 建表失败: {e}")

    # P1.1 BUG-FIX-P1.1 v118.35.0.41 · 4 模块 task/row 表加 field_overrides JSONB
    # 跟 alembic/versions/002_field_overrides_4_modules.py 双跑(prod 启动兼容)
    # 铁律 #21 ✅:新 schema 函数独立 services/db_migrations/ · 不进 db.py
    try:
        from services.db_migrations.field_overrides import ensure_field_overrides_columns

        ensure_field_overrides_columns()
    except Exception as e:
        logger.warning(f"启动 field_overrides 列就绪失败 (等 alembic 002): {e}")

    # credits · 按量付费系统表结构初始化
    try:
        db.ensure_credits_tables()
    except Exception as e:
        logger.warning(f"启动 credits 建表失败: {e}")

    # v118.34.4 · MR.ERP test-connection cache flush
    # On every restart, drop any cached test-connection entries so users
    # don't see stale "stub" responses from before the v118.34.x dispatch
    # fixes. The cache is per-(user_id, endpoint_id) and TTLs at 60 s
    # anyway, so this is at most a 1-minute extra cost the first time
    # someone clicks 重新测试 right after a deploy.
    try:
        # REFACTOR-B1(2026-05-25):3 个缓存随 erp 路由搬到 erp_routes.py · 调封装函数清
        _flush_erp_caches()
        logger.info("[startup] flushed ERP test-connection caches")
    except Exception as e:
        logger.warning(f"startup cache flush failed: {e}")

    # v118.33.7 · 写入健壮版 git-deploy.sh（带回滚 + 健康检查 + 日志）
    # v118.34.6 拍板:这一段移到 _ensure_playwright_installed() 之前
    # · 保证就算 playwright 这步出问题,新 git-deploy.sh 也已经落到磁盘
    # · 这样下次部署的 deploy.sh 已经会自己 pip install + 装 chromium
    try:
        import os as _os

        _deploy_sh = "/opt/mrpilot/git-deploy.sh"
        _new_content = r"""#!/bin/bash
# ============================================================
# git-deploy.sh  v118.33.10.1
# 由 app.py 启动时自动写入 · 请勿手动修改（重启会覆盖）
# 流程：fetch → reset hard → cp static → restart → health check
# 失败时回滚到上一个 GitHub commit（不会回滚到本地旧 commit）
# ============================================================
LOG=/var/log/mrpilot-deploy.log
REPO=/opt/mrpilot
REMOTE=pearnly
BRANCH=master
HEALTH_URL=http://localhost:7860/api/health
MAX_WAIT=180  # 等待服务启动的最大秒数 (v118.34.8 拉到 3 分钟 · 兜底 pip+chromium 慢网络)

echo "======================================" >> "$LOG"
echo "$(date '+%Y-%m-%d %H:%M:%S') git-deploy start" >> "$LOG"

cd "$REPO" || { echo "cd failed" >> "$LOG"; exit 1; }

# 1. 记录 GitHub 上一个已知的好版本作为回滚目标
#    用远端追踪分支（不是本地 HEAD），避免回滚到比 GitHub 更老的本地 commit
PREV_HEAD=$(git rev-parse "$REMOTE/$BRANCH" 2>/dev/null || echo "")
echo "prev GitHub HEAD: $PREV_HEAD" >> "$LOG"

# 2. Fetch
if ! git fetch "$REMOTE" "$BRANCH" >> "$LOG" 2>&1; then
    echo "git fetch FAILED" >> "$LOG"
    exit 1
fi

NEW_HEAD=$(git rev-parse FETCH_HEAD 2>/dev/null || echo "")
echo "new HEAD:  $NEW_HEAD" >> "$LOG"

if [ "$PREV_HEAD" = "$NEW_HEAD" ]; then
    echo "already up to date — skipping restart" >> "$LOG"
    exit 0
fi

# 3. reset --hard 到最新 GitHub commit（同时移动本地 HEAD 指针）
if ! git reset --hard FETCH_HEAD >> "$LOG" 2>&1; then
    echo "git reset failed — abort" >> "$LOG"
    exit 1
fi

# 4. 复制静态资源
mkdir -p static
cp -f home.html home.js home.css login.html static/ 2>> "$LOG" || true

# 4.5. v118.34.9 · 极简版 · 只装 playwright(用 mrpilot 的 venv python
#     如果存在,否则用 system python3)· 每步 timeout 防止卡死
PY=/opt/mrpilot/venv/bin/python
if [ ! -x "$PY" ]; then PY=/usr/bin/python3; fi
echo "using python: $PY" >> "$LOG"

echo "pip install playwright..." >> "$LOG"
timeout 60 "$PY" -m pip install playwright >> "$LOG" 2>&1 || \
    timeout 60 "$PY" -m pip install playwright --break-system-packages \
        >> "$LOG" 2>&1 || \
    echo "pip install playwright non-fatal failure" >> "$LOG"

# 4.6. v118.34.9 · chromium 已装时跳过(idempotent)
echo "playwright install chromium..." >> "$LOG"
timeout 120 "$PY" -m playwright install chromium >> "$LOG" 2>&1 || \
    echo "playwright install chromium non-fatal failure" >> "$LOG"

# 4.7. v118.34.11 · 装 chromium 运行时系统依赖 (apt install libnss3 libgbm1 ...)
#     没这步 BrowserType.launch 立刻 TargetClosedError · 因为 chromium
#     二进制 ≠ chromium 能跑 · 还需要十几个 .so · install-deps 用 apt 装齐
echo "playwright install-deps chromium..." >> "$LOG"
timeout 180 "$PY" -m playwright install-deps chromium >> "$LOG" 2>&1 || \
    echo "playwright install-deps chromium non-fatal failure" >> "$LOG"

# 4.8. v118.35.0.57 · 装齐 requirements.txt 全部依赖(防新依赖漏装 · 如 xlrd 这次就漏了)
#     幂等(已装的 pip 自动跳过)· 非致命(pip 失败不挡部署)· timeout 防卡死
#     用同一个 $PY(venv 优先)· 保证装到服务真正用的 python
echo "pip install -r requirements.txt..." >> "$LOG"
if [ -f requirements.txt ]; then
    timeout 240 "$PY" -m pip install -r requirements.txt >> "$LOG" 2>&1 || \
        timeout 240 "$PY" -m pip install -r requirements.txt --break-system-packages >> "$LOG" 2>&1 || \
        echo "pip install -r requirements.txt non-fatal failure" >> "$LOG"
fi

# 4.9. v118.35.0.68 · 清 pip/playwright 解压临时残渣(铁律 #24 · 2026-05-24 血泪根因)
#     pip 装大包(torch ~2.7G)往 /tmp 解压 · 装完不清会累积撑爆硬盘 →
#     Nginx 写不下上传 body → 对账 500(mrerp 真因)。删了下次自建 · 顺带磁盘体检。
echo "cleaning /tmp/pip-* residue..." >> "$LOG"
rm -rf /tmp/pip-* >> "$LOG" 2>&1 || true
DISK_USE=$(df --output=pcent / 2>/dev/null | tail -1 | tr -dc '0-9')
echo "disk usage after cleanup: ${DISK_USE}%" >> "$LOG"
if [ "${DISK_USE:-0}" -ge 85 ]; then
    echo "WARNING: disk >= 85% after cleanup — investigate /tmp /root /var/log" >> "$LOG"
fi

# 5. 重启服务
echo "restarting mrpilot..." >> "$LOG"
systemctl restart mrpilot >> "$LOG" 2>&1

# 6. 健康检查（等服务起来）
echo "waiting for health check..." >> "$LOG"
for i in $(seq 1 $MAX_WAIT); do
    sleep 1
    HTTP=$(curl -s -o /dev/null -w "%{http_code}" "$HEALTH_URL" 2>/dev/null || echo "000")
    if [ "$HTTP" = "200" ]; then
        echo "health check OK after ${i}s (new HEAD: $NEW_HEAD)" >> "$LOG"
        exit 0
    fi
done

# 7. 服务未恢复 → 回滚到上一个 GitHub 版本（绝不回滚到 GitHub 之前的本地旧 commit）
echo "health check FAILED after ${MAX_WAIT}s — rolling back to $PREV_HEAD" >> "$LOG"
if [ -n "$PREV_HEAD" ]; then
    git reset --hard "$PREV_HEAD" >> "$LOG" 2>&1
    cp -f home.html home.js home.css login.html static/ 2>> "$LOG" || true
    systemctl restart mrpilot >> "$LOG" 2>&1
    echo "rollback done — waiting for service..." >> "$LOG"
    sleep 5
    HTTP2=$(curl -s -o /dev/null -w "%{http_code}" "$HEALTH_URL" 2>/dev/null || echo "000")
    echo "post-rollback health: $HTTP2" >> "$LOG"
fi
exit 1
"""
        with open(_deploy_sh, "w") as _f:
            _f.write(_new_content)
        _os.chmod(_deploy_sh, 0o755)
        logger.info("[v118.33.7] git-deploy.sh updated (with rollback + health check)")
    except Exception as e:
        logger.warning(f"git-deploy.sh update failed: {e}")

    # v118.34.6 · 现在再 ensure playwright。NON-BLOCKING (detached spawn)
    # · git-deploy.sh 已经写到磁盘 · 下次部署的 deploy.sh 也会自己装。
    # 之前 v118.34.5 的 sync 版本卡 lifespan > 30 s · 旧 deploy.sh
    # 健康检查超时把整个版本回滚了 · 现在恢复 detached spawn 路径。
    # v118.34.12 · 必须用 asyncio.to_thread · 否则内部 _probe_chromium_launch
    # 跑在 lifespan 的 event loop 里 · Playwright sync_api 检测到 loop 拒绝
    # start · chromium_can_launch 假阴性(实际能起,但探测炸)。
    try:
        import asyncio as _asyncio

        await _asyncio.to_thread(_ensure_playwright_installed)
    except Exception as e:
        logger.warning(
            f"[playwright-bootstrap] failed (will surface as "
            f"ERR_PLAYWRIGHT_MISSING in wizard): {e}"
        )

    # v110.7 · 启动确保 users 表有欢迎向导用的 profile 字段(幂等 · 已有字段无影响)
    try:
        _ensure_user_profile_columns()
    except Exception as e:
        logger.warning(f"启动 users profile 字段补齐失败: {e}")

    # v118.32.5.5.18 · 部署 graceful 第 3 层 · 长任务中断恢复
    # 启动时扫 3 张任务表中 status=running 的"被打断"任务 · 标 interrupted
    # 用户进对应页能看到 toast "上次更新时被打断 · 点重试"
    try:
        with db.get_cursor(commit=True) as cur:
            recovered = 0
            for tbl in ["ocr_history", "reconciliation_task", "gl_vat_task"]:
                try:
                    cur.execute(f"UPDATE {tbl} SET status='interrupted' " f"WHERE status='running'")
                    recovered += cur.rowcount or 0
                except Exception as _inner:
                    logger.warning(f"启动恢复 {tbl} 中断任务失败(表可能不存在): {_inner}")
            if recovered > 0:
                logger.info(f"🔄 重启恢复 · 共 {recovered} 个 running 任务标 interrupted")
    except Exception as e:
        logger.warning(f"启动 _recover_interrupted_tasks 失败(不影响运行): {e}")

    # v0.17 · M6 · 启动邮箱抓取定时任务(每 tick 扫到期账号)
    # v0.17.11 · HF Space 禁止 IMAP 993 出站 · 环境变量控制
    import asyncio

    email_task = None
    if os.environ.get("EMAIL_INGEST_ENABLED", "0") == "1":
        email_task = asyncio.create_task(_email_ingest_loop())
        logger.info("[email_ingest] 定时抓取已启用")
    else:
        logger.info(
            "[email_ingest] 定时抓取已禁用(HF Space 不支持 IMAP 出站 · 迁 VPS 后设 EMAIL_INGEST_ENABLED=1)"
        )

    # v118.25 · ERP 推送自动重试后台 worker(每 30 秒扫到期失败 log)
    # PEARNLY_SKIP_HEAVY_INIT=1 时不启动 · 防止 unit test 用 TestClient
    # 进 lifespan 时若再全局 patch asyncio.sleep,会把 30 秒 sleep 短路成
    # CPU 死循环 → list_logs_due_for_retry 每秒被调几万次 → stderr 缓冲爆
    # 内存(本机 OOM)。CI/生产不设这个 env,正常启动。
    erp_retry_task = None
    if os.environ.get("PEARNLY_SKIP_HEAVY_INIT", "").lower() not in ("1", "true", "yes"):
        erp_retry_task = asyncio.create_task(_erp_retry_loop())
        logger.info("[erp_retry] 自动重试后台 worker 已启动")
    else:
        logger.info("[erp_retry] 跳过启动(PEARNLY_SKIP_HEAVY_INIT=1)")

    # ADR-005 #15 · 对账异步后台工人(embedded)· 启动建表 + 起轮询任务
    # RECON_ASYNC!=1 时 start_embedded 自己跳过(可秒回滚)· PEARNLY_SKIP_HEAVY_INIT 下不起
    if os.environ.get("PEARNLY_SKIP_HEAVY_INIT", "").lower() not in ("1", "true", "yes"):
        try:
            from services.recon_jobs import store as _recon_store, worker as _recon_worker

            _recon_store.ensure_table()
            _recon_worker.start_embedded()
            # ADR-006 · 模板学习层映射表(启动自动建 · 失败自愈)
            try:
                from services.importer import template_store as _tmpl_store

                _tmpl_store.ensure_table()
            except Exception as _te:
                logger.warning(f"[importer] ensure_table 失败(不影响主服务): {_te}")
        except Exception as e:
            logger.warning(f"[recon-worker] embedded 启动失败(不影响主服务): {e}")

    logger.info("✅ Mr.Pearnly 已就绪 v0.21.0-v108 (Google 余额追踪 · 半自动校准)")
    yield
    # ADR-005 #15 · 停 embedded 工人
    try:
        from services.recon_jobs import worker as _recon_worker

        await _recon_worker.stop_embedded()
    except Exception:
        pass
    # 关闭时停定时
    if email_task is not None:
        email_task.cancel()
        try:
            await email_task
        except asyncio.CancelledError:
            pass  # 任务取消 · 正常退出
    if erp_retry_task is not None:
        erp_retry_task.cancel()
        try:
            await erp_retry_task
        except asyncio.CancelledError:
            pass  # 任务取消 · 正常退出
    logger.info("👋 Mr.Pearnly 关闭")


# v0.17 · M6 · 邮箱抓取轮询任务
# v118.25 · ERP 推送失败自动重试 worker
# 设计:每 30 秒扫一次到期任务 · 指数退避 60s/5min/30min · 共 3 次 · 用完仍失败 → 不再重试(等用户手动)
async def _erp_retry_loop():
    """每 30 秒跑一次重试 tick"""
    import asyncio

    # 启动时先等 30 秒 · 避开和其他 startup 竞争
    await asyncio.sleep(30)
    interval_sec = int(os.environ.get("ERP_RETRY_TICK_SEC", "30"))
    while True:
        try:
            await _run_erp_retry_tick()
        except Exception as e:
            logger.warning(f"[erp_retry_loop] tick 异常(继续): {e}")
        try:
            await asyncio.sleep(interval_sec)
        except asyncio.CancelledError:
            raise


async def _run_erp_retry_tick():
    """单次 tick:找到期失败 log · 重新调用 erp_push 推送 · 更新 log 状态"""
    import asyncio as _asyncio

    try:
        due = db.list_logs_due_for_retry(limit=20)
        if not due:
            return
        logger.info(f"[erp_retry] 本轮到期重试 {len(due)} 条")

        for log in due:
            try:
                # 取上下文(history + endpoint)
                history = (
                    db.get_ocr_history_detail(
                        str(log["user_id"]),
                        str(log["history_id"]),
                        tenant_id=None,
                    )
                    if log.get("history_id")
                    else None
                )
                endpoint = (
                    db.get_erp_endpoint(
                        str(log["user_id"]),
                        str(log["endpoint_id"]),
                    )
                    if log.get("endpoint_id")
                    else None
                )

                if not history or not endpoint:
                    # 关联实体已删 · 终止此 log 的重试
                    db.clear_retry_schedule(str(log["id"]))
                    logger.info(f"[erp_retry] log {log['id']} 关联记录已删 · 停止重试")
                    continue

                # 在 worker 线程里跑同步 push(避免阻塞事件循环)
                result = await _asyncio.to_thread(
                    _erp.push_to_endpoint,
                    endpoint,
                    history,
                )

                # 自增 retry_count · 更新 log 状态(直接覆盖原行 · 不写新行)
                new_count = db.increment_retry_count(str(log["id"]))
                db.update_log_status_after_retry(
                    log_id=str(log["id"]),
                    success=bool(result.get("success")),
                    http_status=result.get("http_status"),
                    response_body=result.get("response_body"),
                    error_msg=result.get("error_msg"),
                    elapsed_ms=int(result.get("elapsed_ms", 0)),
                )
                # 端点 + history 状态同步
                db.update_endpoint_stats(str(endpoint["id"]), bool(result.get("success")))
                if log.get("history_id"):
                    db.update_history_push_status(
                        str(log["history_id"]),
                        "success" if result.get("success") else "failed",
                    )

                if result.get("success"):
                    # 重试成功 · 摘出队列
                    db.clear_retry_schedule(str(log["id"]))
                    logger.info(f"[erp_retry] log {log['id']} 重试 #{new_count} 成功")
                else:
                    # 批 1 改动 3 (v118.34.33) · 用户数据错 retry 阶段也要识别 ·
                    # 一旦从技术错变成用户数据错(或本来就是)· 立刻摘队列.
                    if db.is_user_data_error(result.get("error_msg")):
                        db.clear_retry_schedule(str(log["id"]))
                        logger.info(
                            "[erp_retry] log %s 重试 #%d 命中 user-data 错 · " "停止队列 (err=%r)",
                            log["id"],
                            new_count,
                            (result.get("error_msg") or "")[:80],
                        )
                    else:
                        # 仍失败 · 看还有没有下一次
                        next_delay = db.get_erp_retry_delay_sec(new_count)
                        if next_delay is None:
                            # 用完 3 次 · 不再调度 · 等用户手动
                            db.clear_retry_schedule(str(log["id"]))
                            logger.warning(
                                f"[erp_retry] log {log['id']} 重试 {new_count} 次仍失败 · 停止"
                            )
                        else:
                            db.schedule_log_retry(str(log["id"]), next_delay)
                            logger.info(
                                f"[erp_retry] log {log['id']} 重试 #{new_count} 失败 · {next_delay}s 后再试"
                            )
            except Exception as e_inner:
                logger.warning(f"[erp_retry] 单条处理失败 log_id={log.get('id')}: {e_inner}")
                # 单条失败不影响其它
                continue
    except Exception as e:
        logger.warning(f"[erp_retry] tick 整体异常: {e}")


async def _email_ingest_loop():
    import asyncio

    # 启动时先等 60 秒避免和其他启动动作抢资源
    await asyncio.sleep(60)
    # tick 粒度固定 5 分钟(最小档)· 每账号根据自己 interval_min 判断是否到期
    interval_sec = int(os.environ.get("EMAIL_INGEST_TICK_SEC", "300"))
    while True:
        try:
            await _run_email_ingest_tick()
        except Exception as e:
            logger.warning(f"[email_ingest_loop] tick 异常(继续): {e}")
        try:
            await asyncio.sleep(interval_sec)
        except asyncio.CancelledError:
            raise


async def _run_email_ingest_tick():
    """一个 tick · 扫所有启用账号 · 按 interval_min 决定哪些到期需处理"""
    import asyncio
    from datetime import datetime, timezone, timedelta

    try:
        import email_ingest

        if not email_ingest.is_available():
            return  # 未配 EMAIL_ENCRYPTION_KEY
        accounts = db.list_enabled_email_accounts()
        if not accounts:
            return

        now = datetime.now(timezone.utc)
        due_accounts = []
        for a in accounts:
            interval = int(a.get("interval_min") or 15)
            last = a.get("last_check_at")
            # 没扫过 · 或距上次 check 超过 interval · 就到期
            if last is None:
                due_accounts.append(a)
                continue
            # 容忍 30 秒提前(避免轮询 boundary 漂移多等一轮)
            if (now - last) >= timedelta(minutes=interval) - timedelta(seconds=30):
                due_accounts.append(a)

        if not due_accounts:
            return
        logger.info(f"[email_ingest_loop] 扫 {len(accounts)} 个账号 · 到期 {len(due_accounts)} 个")

        for account in due_accounts:
            try:
                # 阻塞 IO 放到线程池 · 避免卡住 asyncio loop
                result = await asyncio.to_thread(email_ingest.run_account_ingest, account, "auto")
                db.insert_email_ingest_log(
                    account_id=account["id"],
                    user_id=account["user_id"],
                    stats=result,
                    trigger="auto",
                )
                db.update_email_account_status(
                    account["id"],
                    success=result["status"] in ("success", "partial"),
                    error_msg=result.get("error_message"),
                    fetched_any=result.get("attachments_found", 0) > 0,
                )
            except Exception as e:
                logger.warning(f"[email_ingest_loop] account={account.get('id')} 处理异常: {e}")
    except Exception as e:
        logger.warning(f"[email_ingest_loop] tick 外层异常: {e}")


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


# ============================================================
# v118.27.5.4 · 前端版本号自动读取(给 /api/version 用 · 检测新版弹横幅)
# 启动时解析 home.html 里的 ?v= 数字 · 部署后立刻反映
# ============================================================
def _read_frontend_version() -> str:
    import re

    try:
        with open("static/home.html", "r", encoding="utf-8") as _f:
            _content = _f.read()
        m = re.search(r"home\.js\?v=(\d+)", _content)
        if m:
            return m.group(1)
        m = re.search(r"home\.css\?v=(\d+)", _content)
        if m:
            return m.group(1)
    except Exception as e:
        logger.warning(f"_read_frontend_version 读取失败: {e}")
    return "0"


PEARNLY_FRONTEND_VERSION = _read_frontend_version()
logger.info(f"📌 前端版本 PEARNLY_FRONTEND_VERSION = {PEARNLY_FRONTEND_VERSION}")


# ============================================================
# v118.34.37 · 启动时清掉 static/**/*.gz 强制 nginx 动态 gzip
# ============================================================
# 根因(2026-05-20 调试发现): nginx gzip_static on 服务 pre-gzipped .gz
# 文件 · 但 deploy.sh 只 cp 源 .css/.js 不更新 .gz · 导致:
#   - curl 不带 Accept-Encoding: gzip → 拿到新源文件
#   - 浏览器带 Accept-Encoding: gzip → 拿到陈旧 .gz (mtime 跟最近源文件相差几小时)
#   - 即使 URL 加 ?v=NNN cache-bust 也没用 · nginx 静态文件忽略 query string
# 修: 每次 app 启动时删掉 static 下所有 .gz · 让 nginx 退回到 gzip on the fly
# 性能影响: 微小 (CSS/JS 文件本来就有 nginx 自身的 in-memory cache)
def _purge_stale_static_gz():
    import os as _os
    import glob as _glob

    try:
        deleted = 0
        for fp in _glob.glob("static/**/*.gz", recursive=True):
            try:
                _os.remove(fp)
                deleted += 1
            except Exception:
                pass
        if deleted:
            logger.info(
                f"🧹 启动清除 static/**/*.gz · 删了 {deleted} 个陈旧预压缩文件 · nginx 将动态 gzip 当前源文件"
            )
    except Exception as _e:
        logger.warning(f"_purge_stale_static_gz 失败: {_e}")


_purge_stale_static_gz()


# ============================================================
# Models
# ============================================================
class LoginRequest(BaseModel):
    username: str = Field(..., min_length=1, max_length=100)
    password: str = Field(..., min_length=1, max_length=200)
    # v0.17 · "记住我" · True 则 token 30 天有效 · 默认 7 天
    remember_me: bool = False
    # v109.3.2 · 兼容前端简写
    remember: Optional[bool] = None

    def is_remember(self) -> bool:
        if self.remember is not None:
            return bool(self.remember)
        return bool(self.remember_me)


class LoginResponse(BaseModel):
    token: str
    user: dict


# (UserInfo response model → me_routes.py · REFACTOR-B1)


class QuotaResponse(BaseModel):
    plan: str
    ip_used_today: Optional[int] = None
    ip_daily_limit: Optional[int] = None
    monthly_quota: Optional[int] = None
    used_this_month: Optional[int] = None
    max_pages_per_upload: int
    max_file_size_mb: int


class ExportRequest(BaseModel):
    records: List[Any]
    lang: str = Field("zh", pattern="^(zh|en|th|ja)$")
    template: str = Field("standard")


# v118.27.7 · 让 sales_detail_th 也能从单据记录批量入口用
class ExportByHistoryIdsRequest(BaseModel):
    history_ids: List[str]
    lang: str = Field("zh", pattern="^(zh|en|th|ja)$")
    template: str = Field("sales_detail_th")
    client_id: Optional[Any] = None  # 接受 int / str / null · 兼容前端


# ============================================================
# 辅助:把 DB user 转成 UserInfo
# ============================================================
def _calc_trial_days_left(user) -> Optional[float]:
    """v109.4 · 计算试用剩余天数(浮点 · 让前端做 ceil)"""
    if (user.get("plan") or "").lower() != "trial":
        return None
    exp = user.get("trial_expires_at") or user.get("expires_at")
    if not exp:
        return None
    try:
        from datetime import datetime, timezone

        if isinstance(exp, str):
            # 处理可能的字符串格式
            exp = datetime.fromisoformat(exp.replace("Z", "+00:00"))
        if exp.tzinfo is None:
            exp = exp.replace(tzinfo=timezone.utc)
        now = datetime.now(timezone.utc)
        delta = (exp - now).total_seconds() / 86400.0
        return max(0.0, delta)
    except Exception:
        return None


# v110.7 · 启动时确保 users 表有欢迎向导所需的 profile 字段(幂等)
def _ensure_user_profile_columns():
    """
    确保 users 表有 5 个 profile 字段 · 用于欢迎向导和资料完善。
    用 ADD COLUMN IF NOT EXISTS · 已有字段无影响 · 全新部署也能自动补齐。
    """
    columns = [
        ("role", "VARCHAR(32)"),
        ("monthly_volume", "VARCHAR(16)"),
        ("country", "VARCHAR(8)"),
        ("line_id", "VARCHAR(64)"),
        ("phone", "VARCHAR(32)"),
        ("active_jti", "TEXT"),  # v118.32.5.5.10 · 1 账号 1 设备 session 控制
    ]
    # v118.32.5.5.11 · 必须 commit=True · 否则 DDL 在 with 退出时回滚 · 列不会持久化
    with db.get_cursor(commit=True) as cur:
        for col, typ in columns:
            try:
                cur.execute(f"ALTER TABLE users ADD COLUMN IF NOT EXISTS {col} {typ}")
            except Exception as e:
                logger.warning(f"ALTER users add {col} 跳过: {e}")
    logger.info("✅ v110.7 users profile 字段就绪")


# (_build_user_info → me_routes.py · REFACTOR-B1)


# _plan_permissions 已抽到 route_helpers.py(REFACTOR-B1 · 2026-05-25)·
# app.py 从 route_helpers import 回来 · 13 处调用点不变。


def _check_user_quota(user: dict) -> tuple:
    """
    v0.15 · 检查用户本月配额
    v87 · 多租户支持 · 优先按 tenant_type 判断配额来源
    返回 (ok: bool, error_msg: Optional[str], quota_info: dict)

    多租户规则(v87):
    - tenant_type=admin → 超管无限
    - tenant_type=byo_api → 买断自带 key · 看 user.gemini_api_key 是否填
    - tenant_type=shared_api → 月付共用系统 key · 配额用 tenant.monthly_quota
    老规则(兜底 · 无 tenant_id 的用户):
    - 用户填了 gemini_api_key → 买断 · 不限
    - monthly_quota <= 0 → 需提示填 key
    - monthly_quota > 0 · used < quota → 可识别
    - monthly_quota > 0 · used >= quota → 本月配额用完

    v118.26.2.2 紧急修补 · 2026-05-09 · OCR P0 BUG
    BUG 真凶:v27.7 fix_orphan 给所有孤立用户建了 tenant_type='shared_api'
    但 monthly_quota=0(继承 user.monthly_quota 的 NULL/0)· 进入 tenant 分支后
    被 if t_quota <= 0 拦成 quota.need_api_key · 导致所有 trial/free/pro 用户
    OCR 全部失败。修补:有效 plan 用户已被前置 _v109_quota 检查过(ocr_recognize 入口)·
    这里直接放行 · 不再走 tenant 配额拦截。lifetime 用户保留自带 key 检查。

    v118.26.2.4 加强 · 2026-05-09 · 安全 + 员工继承
    - BUG 6 · 顶部加 banned / is_active=False 拦截 · 防被禁用账号绕过 OCR
    - BUG 7 · role=member 员工 · 用同 tenant 的 owner 的 plan 判断(跟 _build_user_info 一致)

    v118.27.5.2 紧急修补:SKIN 测试号双闸全放行
    BUG:v118.27.5 只在 auth_signup.check_ocr_quota 加白名单 · 但本函数(_check_user_quota)
    是第 2 道闸 · SKIN 的 tenant_type 仍走 byo_api 分支被 quota.need_api_key 拦
    修:本函数顶部也加 SKIN 白名单 · 跟 auth_signup 保持一致
    """
    # v118.35.0.21 · 白名单查 users.is_billing_exempt(单一数据源 + 5min cache)
    try:
        if db.is_user_billing_exempt(user.get("id")):
            return (
                True,
                None,
                {
                    "mode": "billing_exempt",
                    "monthly_quota": None,
                    "used_this_month": 0,
                    "remaining": 999999,
                },
            )
    except Exception as _wle:
        logger.warning(f"_check_user_quota whitelist lookup skip: {_wle}")
    # 老路径 fallback(防 is_billing_exempt 读取异常)
    if str(user.get("id") or "") == "468b50c1-5593-4fd6-990d-515ce8085563":
        return (
            True,
            None,
            {
                "mode": "skin_test_whitelist",
                "monthly_quota": None,
                "used_this_month": 0,
            },
        )

    # v118.26.2.4 · 安全闸 · 被禁用 / 封禁账号绝对不能 OCR
    if user.get("is_banned"):
        return (
            False,
            "account.banned",
            {
                "mode": "banned",
                "monthly_quota": 0,
                "used_this_month": 0,
            },
        )
    if user.get("is_active") is False:
        return (
            False,
            "account.inactive",
            {
                "mode": "inactive",
                "monthly_quota": 0,
                "used_this_month": 0,
            },
        )

    # v118.26.2.2 紧急放行 · 有效 plan 用户(_v109_quota 已查过试用期/月配额)
    # v118.26.2.4 · 员工 role=member 时 · 取老板 plan(继承 · 跟 _build_user_info 同步)
    user_plan = user.get("plan")
    if user.get("role") == "member" and user.get("tenant_id"):
        try:
            with db.get_cursor() as _cur:
                _cur.execute(
                    "SELECT plan FROM users WHERE tenant_id = %s AND role = 'owner' LIMIT 1",
                    (str(user["tenant_id"]),),
                )
                _row = _cur.fetchone()
                if _row:
                    _owner_plan = _row["plan"] if isinstance(_row, dict) else _row[0]
                    if _owner_plan:
                        user_plan = _owner_plan
        except Exception as _e:
            logger.warning(f"_check_user_quota: lookup owner plan failed: {_e}")

    if user.get("is_super_admin") or user_plan == "admin":
        return (
            True,
            None,
            {
                "mode": "admin",
                "monthly_quota": None,
                "used_this_month": 0,
            },
        )
    if user_plan == "lifetime":
        # lifetime 必须自带 Gemini key(员工继承时 · 看老板 key)
        _gk = user.get("gemini_api_key")
        if not _gk and user.get("role") == "member" and user.get("tenant_id"):
            try:
                with db.get_cursor() as _cur:
                    _cur.execute(
                        "SELECT gemini_api_key FROM users WHERE tenant_id = %s AND role = 'owner' LIMIT 1",
                        (str(user["tenant_id"]),),
                    )
                    _row = _cur.fetchone()
                    if _row:
                        _gk = _row["gemini_api_key"] if isinstance(_row, dict) else _row[0]
            except Exception as e:
                logger.warning(f"[user_info] 读取老板 gemini_api_key 失败: {e}")
        has_own_key = bool((_gk or "").strip())
        if has_own_key:
            return (
                True,
                None,
                {
                    "mode": "lifetime",
                    "monthly_quota": None,
                    "used_this_month": int(user.get("used_this_month") or 0),
                },
            )
        return (
            False,
            "quota.need_api_key",
            {
                "mode": "need_setup",
                "monthly_quota": 0,
                "used_this_month": 0,
            },
        )
    if user_plan in ("trial", "free", "pro", "firm", "enterprise", "monthly", "yearly"):
        return (
            True,
            None,
            {
                "mode": "v109_plan",
                "monthly_quota": None,
                "used_this_month": int(user.get("used_this_month") or 0),
            },
        )

    # === 以下为老多租户兜底(plan 字段为 NULL 或非标值的极旧用户)===
    # v87 · 多租户优先分支
    tenant_id = user.get("tenant_id")
    if tenant_id:
        try:
            tenant = db.get_tenant(str(tenant_id))
        except Exception as e:
            logger.warning(f"_check_user_quota get_tenant failed: {e}")
            tenant = None
        if tenant:
            tt = tenant.get("tenant_type")
            # 超管 · 无限
            if tt == "admin" or user.get("is_super_admin"):
                return (
                    True,
                    None,
                    {
                        "mode": "admin",
                        "monthly_quota": None,
                        "used_this_month": 0,
                    },
                )
            # 买断自带 key
            if tt == "byo_api":
                has_own_key = bool((user.get("gemini_api_key") or "").strip())
                if has_own_key:
                    return (
                        True,
                        None,
                        {
                            "mode": "lifetime",
                            "monthly_quota": None,
                            "used_this_month": int(user.get("used_this_month") or 0),
                        },
                    )
                return (
                    False,
                    "quota.need_api_key",
                    {
                        "mode": "need_setup",
                        "monthly_quota": 0,
                        "used_this_month": 0,
                    },
                )
            # 月付共用系统 key(shared_api)· 配额在 tenant 层
            if tt == "shared_api":
                t_quota = int(tenant.get("monthly_quota") or 0)
                t_used = int(tenant.get("used_this_month") or 0)
                if t_quota <= 0:
                    # 月付但管理员没配额度 · 联系管理员
                    return (
                        False,
                        "quota.need_api_key",
                        {
                            "mode": "need_setup",
                            "monthly_quota": 0,
                            "used_this_month": 0,
                        },
                    )
                if t_used >= t_quota:
                    return (
                        False,
                        "quota.exhausted",
                        {
                            "mode": "shared",
                            "monthly_quota": t_quota,
                            "used_this_month": t_used,
                        },
                    )
                return (
                    True,
                    None,
                    {
                        "mode": "shared",
                        "monthly_quota": t_quota,
                        "used_this_month": t_used,
                    },
                )

    # 老规则(兜底)· 保持向后兼容
    # === v109.3 · 新 plan 系统的用户(trial/free/pro/firm/enterprise)走新逻辑 ===
    # === v111.1 · 加 monthly/yearly/lifetime/admin 新档名 ===
    # 这些用户已经在前面被 v109.3 quota check 检查过 · 这里直接放行
    user_plan = user.get("plan")
    if user_plan in (
        "trial",
        "free",
        "pro",
        "firm",
        "enterprise",
        "monthly",
        "yearly",
        "lifetime",
        "admin",
    ):
        return (
            True,
            None,
            {
                "mode": "v109_plan",
                "monthly_quota": None,
                "used_this_month": int(user.get("used_this_month") or 0),
            },
        )

    has_own_key = bool((user.get("gemini_api_key") or "").strip())
    quota = user.get("monthly_quota")
    used = int(user.get("used_this_month") or 0)

    # 情况 1 · 自带 key(买断)· 无限制
    if has_own_key:
        return (
            True,
            None,
            {
                "mode": "lifetime",
                "monthly_quota": None,
                "used_this_month": used,
            },
        )

    # 情况 2 · 无 key · 无配额(或配额 <= 0)· 需要填 API Key
    if not quota or quota <= 0:
        return (
            False,
            "quota.need_api_key",
            {
                "mode": "need_setup",
                "monthly_quota": 0,
                "used_this_month": used,
            },
        )

    # 情况 3 · 月付 · 超额
    if used >= quota:
        return (
            False,
            "quota.exhausted",
            {
                "mode": "monthly",
                "monthly_quota": int(quota),
                "used_this_month": used,
            },
        )

    # 情况 4 · 月付 · 正常
    return (
        True,
        None,
        {
            "mode": "monthly",
            "monthly_quota": int(quota),
            "used_this_month": used,
        },
    )


# (Health & Contact 公开 meta 路由 → pages_routes.py · REFACTOR-B1)


# v118.35.0.6 · /api/plans + /api/v1/plans 已下线 · credits 系统接管(legacy/credits-system-5de6cc5 tag)


# ============================================================
# 登录
# ============================================================
@app.post("/api/login", response_model=LoginResponse)
async def login(req: LoginRequest, request: Request):
    # v109.3.2 · 登录失败次数检查(同邮箱 5 次/30 分钟)
    try:
        import db as _db

        with _db.get_cursor() as cur:
            cur.execute(
                """
                SELECT COUNT(*) AS n FROM login_failure_log
                WHERE email_or_username = %s
                  AND created_at > NOW() - INTERVAL '30 minutes'
            """,
                (req.username.lower().strip(),),
            )
            row = cur.fetchone()
            n = row.get("n") if isinstance(row, dict) else (row[0] if row else 0)
            if n and int(n) >= 5:
                raise HTTPException(429, detail="account_locked")
    except HTTPException:
        raise
    except Exception as _ex:
        # 表不存在等情况 · 不阻塞登录
        pass

    user = find_user_by_username(req.username)
    if not user:
        _record_login_failure(req.username, request)
        raise HTTPException(401, detail="auth.invalid_credentials")

    if not verify_password(req.password, user["password_hash"]):
        _record_login_failure(req.username, request)
        raise HTTPException(401, detail="auth.invalid_credentials")

    if not user.get("is_active", True):
        raise HTTPException(403, detail="auth.account_disabled")

    from datetime import datetime, timezone

    if user.get("expires_at"):
        try:
            exp = user["expires_at"]
            exp_dt = (
                exp
                if hasattr(exp, "tzinfo")
                else datetime.fromisoformat(str(exp).replace("Z", "+00:00"))
            )
            if exp_dt < datetime.now(timezone.utc):
                raise HTTPException(403, detail="auth.account_expired")
        except HTTPException:
            raise
        except Exception as e:
            logger.warning(f"[auth] 校验账户过期失败: {e}")

    # v118.11 · 员工首次登录(role=member && 还没 last_login_at)→ 返回 must_change_password 让前端弹强制改密 modal
    must_change_password = bool(
        (user.get("role") == "member")
        and (user.get("last_login_at") is None)
        and (not user.get("is_super_admin"))
    )

    update_last_login(str(user["id"]))
    # v118.11 · plan=NULL 防御兜底 · 防止 token payload 含 None 导致后续验证异常
    _safe_plan = user.get("plan") or "free"
    token = create_access_token(
        user_id=str(user["id"]),
        username=user["username"],
        plan=_safe_plan,
        tenant_id=str(user["tenant_id"]) if user.get("tenant_id") else None,
        role=user.get("role") or "owner",
        is_super_admin=bool(user.get("is_super_admin")),
        remember_me=req.is_remember(),
    )
    # 登录成功 · 清空失败记录
    try:
        import db as _db

        with _db.get_cursor() as cur:
            cur.execute(
                "DELETE FROM login_failure_log WHERE email_or_username = %s",
                (req.username.lower().strip(),),
            )
    except Exception as e:
        logger.warning(f"[login] 清理失败日志失败: {e}")

    # 返回 · 同时提供 token 和 access_token 两个键(向前兼容)
    user_info = {"id": str(user["id"]), "username": user["username"], "plan": user["plan"]}
    return JSONResponse(
        {
            "token": token,
            "access_token": token,
            "user": user_info,
            "must_change_password": must_change_password,
            "is_super_admin": bool(user.get("is_super_admin")),
        }
    )


def _record_login_failure(username: str, request: Request):
    """记录登录失败 · 用于锁定逻辑"""
    try:
        import db as _db

        ip = request.client.host if request.client else None
        ua = request.headers.get("user-agent", "")[:200]
        with _db.get_cursor() as cur:
            cur.execute(
                """
                INSERT INTO login_failure_log(email_or_username, ip, user_agent)
                VALUES (%s, %s, %s)
            """,
                (username.lower().strip(), ip, ua),
            )
    except Exception as e:
        logger.warning(f"login fail log skip: {e}")


# ============================================================
# User
# ============================================================
# (/api/me · /api/v1/me · /api/me/profile + ProfileUpdate → me_routes.py · REFACTOR-B1)


# ============================================================
# OCR
# ============================================================
@app.get("/api/ocr/quota", response_model=QuotaResponse)
async def get_quota(request: Request):
    user = get_current_user_from_request(request)
    # v118.11 · plan=NULL 防御兜底 · 同 _build_user_info
    plan = user.get("plan") or "free"
    p_perms = _plan_permissions(plan)
    monthly_quota = p_perms.get("monthly_quota")
    used_this_month = int(user.get("used_this_month") or 0) if monthly_quota is not None else None

    return QuotaResponse(
        plan=plan,
        ip_used_today=None,
        ip_daily_limit=None,
        monthly_quota=monthly_quota,
        used_this_month=used_this_month,
        max_pages_per_upload=p_perms["max_pages_per_upload"],
        max_file_size_mb=p_perms["max_file_size_mb"],
    )


@app.post("/api/ocr/recognize")
async def ocr_recognize(
    request: Request,
    file: UploadFile = File(...),
    client_id: Optional[str] = Form(None),  # v27.8.1.13a · 右上角客户切换器选中时自动归属
    # B1 相 1 (2026-05-26) · workspace 账套归属(在为哪家公司做账)· 可选 · Form 或 header
    # X-Workspace-Client-Id · 带不上 NULL · 非强制(缺失不拦上传)· 与 client_id(买方)独立。
    workspace_client_id: Optional[str] = Form(None),
):
    user = get_current_user_from_request(request)
    client_ip = get_client_ip(request)
    plan = user.get("plan", "free")

    # B1 相 1 · 解析 workspace 账套归属:优先 Form,回退 header;非数字/缺失 → None(写 NULL)。
    _ws_raw = workspace_client_id or request.headers.get("X-Workspace-Client-Id")
    _ws_client_id = int(_ws_raw) if (_ws_raw and str(_ws_raw).strip().isdigit()) else None

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
        cache_auto_pushed = False
        if _plan_permissions(plan).get("can_auto_push_erp"):
            try:
                auto_eps = db.list_erp_endpoints(str(user["id"]), auto_push_only=True)
                if auto_eps:
                    import asyncio

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

            # 批 1 改动 1 (Zihao 2026-05-19 拍板 · v118.34.33) · auto-resolve
            # client_id. 如果右上角客户切换器没选 client_id (常态) · 按
            # buyer_name + buyer_tax 匹配 Pearnly 客户:
            #   ≥0.95 → 自动 assign + 学习 · 让 auto-push 继续
            #   0.80-0.95 → 不 assign · 写 suggested_client_id 到 history.pages
            #               + 不 trigger auto-push (等用户确认)
            #   <0.80 → 不 assign · 不 trigger auto-push
            _auto_resolved_client = False
            try:
                history_existing_client = (
                    int(client_id) if (client_id and str(client_id).strip().isdigit()) else None
                )
                if not history_existing_client:
                    _buyer_name = (g_fields or {}).get("buyer_name")
                    _buyer_tax = (g_fields or {}).get("buyer_tax")
                    resolved = db.try_resolve_buyer_to_client(
                        buyer_name=_buyer_name,
                        buyer_tax=_buyer_tax,
                        user_id=str(user["id"]),
                        tenant_id=_tid(user),
                    )
                    if resolved:
                        conf = resolved.get("confidence", 0.0)
                        rcid = resolved.get("client_id")
                        if conf >= 0.95 and rcid:
                            # 自动绑 + 学习
                            db.update_history_client_id(
                                hid,
                                rcid,
                                str(user["id"]),
                                tenant_id=_tid(user),
                            )
                            db.learn_buyer_to_client(
                                _buyer_name,
                                _buyer_tax,
                                rcid,
                                str(user["id"]),
                                tenant_id=_tid(user),
                            )
                            _auto_resolved_client = True
                            logger.info(
                                "[auto-resolve] history=%s client_id=%s "
                                "name=%r conf=%.2f source=%s",
                                hid[:8],
                                rcid,
                                resolved.get("client_name"),
                                conf,
                                resolved.get("match_source"),
                            )
                        elif conf >= 0.80 and rcid:
                            # 建议归属 · 不 auto-assign · 标 suggestion
                            # 抽屉 UI 显示 "建议归属 X · 点确认"
                            logger.info(
                                "[auto-resolve] SUGGEST history=%s client_id=%s "
                                "name=%r conf=%.2f",
                                hid[:8],
                                rcid,
                                resolved.get("client_name"),
                                conf,
                            )
                            # 把 suggestion stash 到 history.pages[0].fields 让前端读
                            try:
                                _new_pages = [dict(p) for p in (g_pages_for_save or [])]
                                if _new_pages:
                                    _f = dict(_new_pages[0].get("fields") or {})
                                    _f["_suggested_client_id"] = rcid
                                    _f["_suggested_client_name"] = resolved.get("client_name")
                                    _f["_suggested_client_confidence"] = conf
                                    _new_pages[0] = {**_new_pages[0], "fields": _f}
                                    db.update_ocr_history_pages(
                                        str(user["id"]),
                                        hid,
                                        _new_pages,
                                        tenant_id=_tid(user),
                                    )
                            except Exception as _se:
                                logger.warning(f"stash suggestion failed: {_se}")
                    else:
                        logger.info(
                            "[auto-resolve] no match history=%s buyer=%r",
                            hid[:8],
                            (_buyer_name or "")[:40],
                        )
            except Exception as _are:
                logger.warning(f"auto-resolve client_id failed (history={hid[:8]}): {_are}")

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
    auto_pushed = False
    if history_ids and _plan_permissions(plan).get("can_auto_push_erp"):
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


@app.post("/api/ocr/export")
async def ocr_export(req: ExportRequest, request: Request):
    user = get_current_user_from_request(request)
    if not req.records:
        raise HTTPException(400, detail="export.empty_records")
    template_name = (req.template or "standard").strip()

    # v118.27.5.3 · 模板分发
    if template_name == "standard":
        try:
            from excel_export import build_xlsx, default_filename

            xlsx_bytes = build_xlsx(req.records, lang=req.lang)
            filename = default_filename()
        except Exception as e:
            logger.exception(f"Excel(standard)生成失败: {e}")
            raise HTTPException(500, detail="export.build_failed")
    elif template_name == "sales_detail_th":
        # 泰国销售明细模板(每商品 1 行 + Excel 公式)· 跟泰国本地销售清单习惯一致
        try:
            from excel_template_th import build_sales_detail_xlsx, sales_detail_filename

            xlsx_bytes = build_sales_detail_xlsx(req.records, lang=req.lang)
            filename = sales_detail_filename()
        except Exception as e:
            logger.exception(f"Excel(sales_detail_th)生成失败: {e}")
            raise HTTPException(500, detail="export.build_failed")
    else:
        if user["plan"] == "free" and not user.get("can_use_custom_template"):
            raise HTTPException(403, detail="export.template_locked")
        raise HTTPException(400, detail="export.template_not_supported_yet")

    return Response(
        content=xlsx_bytes,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "X-Filename": filename,
        },
    )


# ============================================================
# v118.27.7 · 单据记录批量入口走 sales_detail_th 模板
# 让我手上的 excel_template_th 也能从「单据记录批量导出」用 · 真正打通系统
# 流程:history_ids → db.get_ocr_history_detail → 合并 pages → records → excel_template_th
# ============================================================
def _merge_pages_to_fields(pages) -> dict:
    """把 history.pages(多页 OCR 结果)合并成一份 merged_fields(后端版 · 跟前端 mergeFields 等价)
    策略:同 key 谁非空用谁 · items 数组直接拼接(同张发票多页明细汇总)
    """
    if not pages or not isinstance(pages, list):
        return {}
    merged: dict = {}
    items: list = []
    for p in pages:
        if not isinstance(p, dict):
            continue
        f = p.get("fields") or {}
        if not isinstance(f, dict):
            continue
        for k, v in f.items():
            if k == "items":
                if isinstance(v, list):
                    items.extend(v)
                continue
            if v in (None, "", [], {}):
                continue
            if not merged.get(k):
                merged[k] = v
    if items:
        merged["items"] = items
    return merged


@app.post("/api/ocr/export-by-history-ids")
async def ocr_export_by_history_ids(req: ExportByHistoryIdsRequest, request: Request):
    """sales_detail_th 模板从单据记录 / 客户卡片入口走的接口
    其他模板(input_vat / standard / print)继续走 reports_router 的 batch_export
    """
    user = get_current_user_from_request(request)
    if not req.history_ids:
        raise HTTPException(400, detail="export.empty_records")
    template_name = (req.template or "sales_detail_th").strip()
    if template_name != "sales_detail_th":
        raise HTTPException(400, detail="export.template_not_supported_yet")

    user_id = str(user.get("id"))
    tenant_id = user.get("tenant_id")
    tenant_id = str(tenant_id) if tenant_id else None

    records = []
    for hid in req.history_ids:
        try:
            h = db.get_ocr_history_detail(user_id, str(hid), tenant_id)
            if not h:
                continue
            mf = _merge_pages_to_fields(h.get("pages") or [])
            # 用冗余字段回填(ocr_history 表里专门存了这些 · 比 pages 更稳)
            if h.get("invoice_no") and not mf.get("invoice_number"):
                mf["invoice_number"] = h.get("invoice_no")
            if h.get("invoice_date") and not mf.get("date"):
                mf["date"] = h.get("invoice_date")
            if h.get("seller_name") and not mf.get("seller_name"):
                mf["seller_name"] = h.get("seller_name")
            if h.get("total_amount") and not mf.get("total_amount"):
                mf["total_amount"] = h.get("total_amount")
            records.append(
                {
                    "filename": h.get("filename") or f"history-{hid}",
                    "engine": "",
                    "merged_fields": mf,
                }
            )
        except Exception as e:
            logger.warning(f"export-by-history-ids · history {hid} 拉取失败: {e}")
            continue

    if not records:
        raise HTTPException(404, detail="export.no_data")

    try:
        from excel_template_th import build_sales_detail_xlsx, sales_detail_filename

        xlsx_bytes = build_sales_detail_xlsx(records, lang=req.lang)
        filename = sales_detail_filename()
    except Exception as e:
        logger.exception(f"sales_detail_th 生成失败: {e}")
        raise HTTPException(500, detail="export.build_failed")

    return Response(
        content=xlsx_bytes,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "X-Filename": filename,
        },
    )


# ============================================================
# /api/v1/ 别名(未来升级用,当前只是路由别名)
# ============================================================
# (/api/v1/me → me_routes.py · REFACTOR-B1)


@app.get("/api/v1/ocr/quota")
async def v1_quota(request: Request):
    return await get_quota(request)


@app.post("/api/v1/ocr/recognize")
async def v1_recognize(
    request: Request,
    file: UploadFile = File(...),
    client_id: Optional[str] = Form(None),
):
    return await ocr_recognize(request, file, client_id)


@app.post("/api/v1/ocr/export")
async def v1_export(req: ExportRequest, request: Request):
    return await ocr_export(req, request)


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
import erp_push as _erp

# 上述 ERP 推送 15 路由 + _check_push_access + 6 model + _strip_endpoint_for_response
# + _fetch_listing_with_retry 已抽到 erp_routes.py(REFACTOR-B1 · 2026-05-25)·
# 顶部 from erp_routes import router as erp_router · app.include_router(erp_router)。
# ⚠️ 铁律 #10 async tripwire(局部 import asyncio as _asyncio + to_thread)随路由搬走。
# import erp_push as _erp 保留 · 供下方自动推送后台 helper(_auto_push_* · OCR hook 触发 · 非路由)复用。


# ============================================================
# v0.9 · 自动推送(识别完成后后台异步触发)
# ============================================================
async def _auto_push_history(
    user_id: str, history_id: str, endpoints: List[Dict[str, Any]], tenant_id: Optional[str] = None
):
    """
    后台异步任务 · 对 auto_push=TRUE 的端点批量推送一条历史记录
    失败不影响识别返回,只写入日志 · Plus/Pro 才会走这里
    v118.14 · tenant_id 给了 → 推送日志查询同 tenant 共享(老板能看员工触发的推送日志)
    """
    import asyncio

    # 1) 读历史详情(push_to_endpoint 要完整字段)
    history = db.get_ocr_history_detail(user_id, history_id, tenant_id=tenant_id)
    if not history:
        logger.warning(f"[AutoPush] 历史 {history_id} 不存在,跳过")
        return

    # 2) 循环推每个端点 · 用线程池避免阻塞事件循环(requests 是同步库)
    for ep in endpoints:
        try:
            # 批 2 改动 2 (v118.34.34) · 推送去重 · 同 history × endpoint
            # 已 success 过 → 静默跳过 + 写 skipped_dup log.
            existing = db.has_recent_successful_push(
                history_id,
                ep["id"],
                user_id,
            )
            if existing:
                db.insert_push_log(
                    user_id=user_id,
                    endpoint_id=ep["id"],
                    history_id=history_id,
                    invoice_no=history.get("invoice_no"),
                    seller_name=history.get("seller_name"),
                    total_amount=history.get("total_amount"),
                    status="skipped_dup",
                    http_status=200,
                    request_body={
                        "adapter": ep.get("adapter"),
                        "skipped_reason": "already_success",
                        "prior_log_id": str(existing.get("id")),
                    },
                    response_body=existing.get("response_body"),
                    error_msg=None,
                    attempt=1,
                    elapsed_ms=0,
                    trigger="auto",
                )
                logger.info(
                    "[AutoPush-dedup] skipped · history=%s endpoint=%s " "(prior=%s)",
                    history_id[:8],
                    ep["id"][:8],
                    str(existing.get("id"))[:8],
                )
                continue

            # push_to_endpoint 是同步调用(requests) · 用 run_in_executor 挪到线程
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, _erp.push_to_endpoint, ep, history)

            # 写日志
            new_log_id = db.insert_push_log(
                user_id=user_id,
                endpoint_id=ep["id"],
                history_id=history_id,
                invoice_no=history.get("invoice_no"),
                seller_name=history.get("seller_name"),
                total_amount=history.get("total_amount"),
                status="success" if result["success"] else "failed",
                http_status=result.get("http_status"),
                request_body=result.get("request_body"),
                response_body=result.get("response_body"),
                error_msg=result.get("error_msg"),
                attempt=1,
                elapsed_ms=result.get("elapsed_ms", 0),
                trigger="auto",  # 标记自动触发
            )

            db.update_endpoint_stats(ep["id"], result["success"])
            db.update_history_push_status(
                history_id,
                "success" if result["success"] else "failed",
            )

            # v118.25 · 自动推送失败 · 进入重试队列(60s 后第一次重试)
            # 批 1 改动 3 (v118.34.33) · 用户数据错跳过重试队列.
            if not result["success"] and new_log_id:
                if db.is_user_data_error(result.get("error_msg")):
                    logger.info(
                        "[AutoPush] user-data error · NOT scheduling retry · " "log=%s err=%r",
                        str(new_log_id)[:8],
                        (result.get("error_msg") or "")[:80],
                    )
                else:
                    first_delay = db.get_erp_retry_delay_sec(0)
                    if first_delay is not None:
                        db.schedule_log_retry(str(new_log_id), first_delay)
                        logger.info(
                            f"[AutoPush] 失败入重试队列 · log={new_log_id} · {first_delay}s 后第 1 次重试"
                        )

            logger.info(
                f"[AutoPush] user={user_id[:8]}.. history={history_id[:8]}.. "
                f"ep={ep.get('name')!r} success={result['success']}"
            )
        except Exception as e:
            logger.exception(f"[AutoPush] endpoint={ep.get('name')!r} 处理异常: {e}")


# ============================================================
# v27.8.1.3 · Xero 后台自动推(OCR 完成 hook 调用)
# ============================================================
async def _auto_push_xero_for_history(user_id: str, tenant_id: str, history_id: str):
    """v27.8.1.3 · 自动推 Xero(后台 · 失败只写日志不抛)"""
    import time

    if not tenant_id:
        return
    t0 = time.time()
    try:
        history = db.get_ocr_history_detail(user_id, history_id, tenant_id=tenant_id)
        if not history:
            return
        st = (history.get("status") or "").lower()
        if st in ("exception", "exception_pending", "rejected"):
            return  # 异常未放行 · 不自动推
        # 客户映射
        mappings = db.get_mrerp_mappings_bundle(tenant_id)
        cid = history.get("client_id") or 0
        contact_name = None
        for m in mappings.get("clients") or []:
            if m.get("erp_type") == "xero" and int(m.get("client_id") or 0) == int(cid):
                contact_name = (m.get("erp_code") or "").strip()
                break
        if not contact_name:
            try:
                db.insert_push_log(
                    user_id=user_id,
                    endpoint_id=None,
                    history_id=history_id,
                    invoice_no=history.get("invoice_no"),
                    seller_name=history.get("seller_name"),
                    total_amount=history.get("total_amount"),
                    status="failed",
                    http_status=400,
                    request_body={"adapter": "xero_auto", "stage": "mapping"},
                    response_body=None,
                    error_msg="no_client_mapping",
                    attempt=1,
                    elapsed_ms=int((time.time() - t0) * 1000),
                    trigger="auto",
                )
            except Exception as e:
                logger.warning(f"[xero_auto] 写 push_log(no_mapping)失败: {e}")
            return
        # 拿 token + push
        try:
            access_token, xero_org_id = _ensure_fresh_xero_token(tenant_id)
            from xero_pusher import (
                find_contact_by_name,
                build_invoice_payload,
                push_invoice,
            )

            contact = find_contact_by_name(access_token, xero_org_id, contact_name)
            if not contact:
                raise RuntimeError("contact_not_found")
            payload = build_invoice_payload(history, contact)
            result = push_invoice(access_token, xero_org_id, payload)
            ok = bool(result.get("success"))
            db.insert_push_log(
                user_id=user_id,
                endpoint_id=None,
                history_id=history_id,
                invoice_no=history.get("invoice_no"),
                seller_name=history.get("seller_name"),
                total_amount=history.get("total_amount"),
                status="success" if ok else "failed",
                http_status=result.get("http_status"),
                request_body={"adapter": "xero_auto"},
                response_body=str(result.get("invoice_id") or "")[:500],
                error_msg=(None if ok else str(result.get("error") or "")[:500]),
                attempt=1,
                elapsed_ms=int((time.time() - t0) * 1000),
                trigger="auto",
            )
            if ok:
                logger.info(f"[AutoPushXero] ok history={history_id[:8]} contact={contact_name}")
        except Exception as e:
            logger.warning(f"[AutoPushXero] failed history={history_id[:8]}: {e}")
            try:
                db.insert_push_log(
                    user_id=user_id,
                    endpoint_id=None,
                    history_id=history_id,
                    invoice_no=history.get("invoice_no"),
                    seller_name=history.get("seller_name"),
                    total_amount=history.get("total_amount"),
                    status="failed",
                    http_status=500,
                    request_body={"adapter": "xero_auto"},
                    response_body=None,
                    error_msg=str(e)[:500],
                    attempt=1,
                    elapsed_ms=int((time.time() - t0) * 1000),
                    trigger="auto",
                )
            except Exception as _le:
                logger.warning(f"[xero_auto] 写 push_log(exception)失败: {_le}")
    except Exception as e:
        logger.exception(f"[AutoPushXero] outer exception: {e}")


def _trigger_auto_push_all(user_id: str, tenant_id: Optional[str], history_id: str):
    """v27.8.1.3 · 给 OCR hook 用 · 一次性触发 webhook + Xero 两类自动推
    每类独立 task · 互不影响"""
    if not tenant_id:
        return
    import asyncio

    # Xero
    try:
        if db.get_xero_auto_push(tenant_id):
            asyncio.create_task(_auto_push_xero_for_history(user_id, tenant_id, history_id))
    except Exception as e:
        logger.warning(f"[AutoPushAll] xero schedule failed: {e}")


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


# v118.27.5.4 · 前端版本检测接口 · 前端定时轮询 · 不一致弹横幅
# v118.32.5.5.17 · 加 release_notes 4 语字段 · version-banner.js 拿来显示更新内容
# 铁律(v5.5.17 拍板):每次部署写 1-3 句 4 语更新说明 · 大白话 · 不出现 OCR/API/Gemini 技术词
# v118.35.0.28 安全脱敏 (P0-02 体检 2026-05-21):
#   公开接口只返回 version/ts/release_notes 三个公开字段
#   内部诊断 (playwright / last_500 / traceback) 挪到 /api/admin/diagnostics/runtime
@app.get("/api/version")
async def get_frontend_version():
    import time as _t

    return {
        "version": PEARNLY_FRONTEND_VERSION,
        "ts": int(_t.time()),
        "release_notes": {
            "zh": "系统已提升发票识别能力:同一页里印有多张发票时,现在会逐张完整识别,不再漏票;万一仍有未能识别的发票,会明确提示需要人工核对。顶部右上角已升级为「工作模式」切换,选定客户后本次上传会自动归属该客户;推送到外部 ERP 成功后也可直接查看并复制 ERP 单号。即日生效。",
            "th": "ระบบปรับปรุงการอ่านใบกำกับ: เมื่อมีหลายใบในหน้าเดียว ระบบจะอ่านครบทุกใบ ไม่ตกหล่น หากยังมีใบที่อ่านไม่ได้จะแจ้งให้ตรวจสอบเอง อย่างชัดเจน นอกจากนี้ปุ่มมุมขวาบนเปลี่ยนเป็น «โหมดการทำงาน» เลือกลูกค้าแล้วการอัปโหลดจะถูกจัดให้ลูกค้านั้นอัตโนมัติ และหลังส่งไป ERP สำเร็จสามารถดู/คัดลอกเลขที่เอกสาร ERP ได้ มีผลทันที",
            "en": "Invoice recognition is stronger: when one page contains several invoices, every invoice is now captured instead of dropping one; if any invoice still cannot be read, you are clearly told to review it manually. The top-right control is now a Work Mode switch — pick a client and this session's uploads are attributed to it; and after a successful push to an external ERP you can view and copy the ERP document number. Effective immediately.",
            "ja": "請求書認識を強化:1ページに複数の請求書がある場合も、取りこぼさず全件認識します。読み取れない請求書が残る場合は手動確認が必要と明確に通知します。右上は「作業モード」切り替えになり、クライアントを選ぶと今回のアップロードが自動的にそのクライアントに帰属します。外部 ERP への送信成功後は ERP 伝票番号を表示・コピーできます。即日有効。",
        },
    }


# (/reset · /terms · /privacy → pages_routes.py · REFACTOR-B1)


# ============================================================
# v118.27.5 · Google OAuth 2.0 · 仅支持已注册账号登录(自动绑定 google_sub)
# 未注册用户:跳回 /login 提示先邮箱注册(自动建账号留 v118.27.6)
# ============================================================
import time as _time
import secrets as _secrets
from urllib.parse import urlencode as _urlencode
from fastapi.responses import RedirectResponse as _RedirectResp

_GOOGLE_CLIENT_ID = os.getenv("GOOGLE_OAUTH_CLIENT_ID", "")
_GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_OAUTH_CLIENT_SECRET", "")
_GOOGLE_REDIRECT_URI = os.getenv(
    "GOOGLE_OAUTH_REDIRECT_URI", "https://pearnly.com/api/auth/google/callback"
)
_oauth_state_cache: Dict[str, float] = {}


def _gen_oauth_state() -> str:
    s = _secrets.token_urlsafe(32)
    _oauth_state_cache[s] = _time.time()
    cutoff = _time.time() - 600
    for k in list(_oauth_state_cache.keys()):
        if _oauth_state_cache[k] < cutoff:
            _oauth_state_cache.pop(k, None)
    return s


def _verify_oauth_state(s: str) -> bool:
    if not s or s not in _oauth_state_cache:
        return False
    ts = _oauth_state_cache.pop(s)
    return _time.time() - ts < 600


@app.get("/api/auth/google/start")
async def google_oauth_start():
    if not _GOOGLE_CLIENT_ID:
        raise HTTPException(status_code=503, detail="oauth_not_configured")
    state = _gen_oauth_state()
    params = {
        "client_id": _GOOGLE_CLIENT_ID,
        "redirect_uri": _GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope": "openid email profile",
        "state": state,
        "access_type": "online",
        "prompt": "select_account",
    }
    url = "https://accounts.google.com/o/oauth2/v2/auth?" + _urlencode(params)
    return _RedirectResp(url, status_code=302)


@app.get("/api/auth/google/callback")
async def google_oauth_callback(code: str = "", state: str = "", error: str = ""):
    if error:
        return _RedirectResp(f"/login?oauth_error={error}", status_code=302)
    if not _verify_oauth_state(state):
        return _RedirectResp("/login?oauth_error=invalid_state", status_code=302)
    if not code:
        return _RedirectResp("/login?oauth_error=no_code", status_code=302)
    if not _GOOGLE_CLIENT_ID or not _GOOGLE_CLIENT_SECRET:
        return _RedirectResp("/login?oauth_error=not_configured", status_code=302)

    # code → access_token → userinfo
    try:
        import httpx as _httpx

        async with _httpx.AsyncClient(timeout=15) as client:
            tr = await client.post(
                "https://oauth2.googleapis.com/token",
                data={
                    "code": code,
                    "client_id": _GOOGLE_CLIENT_ID,
                    "client_secret": _GOOGLE_CLIENT_SECRET,
                    "redirect_uri": _GOOGLE_REDIRECT_URI,
                    "grant_type": "authorization_code",
                },
            )
            if tr.status_code != 200:
                logger.error(f"[OAuth] token exchange failed {tr.status_code}: {tr.text[:300]}")
                return _RedirectResp("/login?oauth_error=token_fail", status_code=302)
            tok_data = tr.json()
            access_token = tok_data.get("access_token")
            if not access_token:
                return _RedirectResp("/login?oauth_error=no_access_token", status_code=302)
            ur = await client.get(
                "https://openidconnect.googleapis.com/v1/userinfo",
                headers={"Authorization": f"Bearer {access_token}"},
            )
            if ur.status_code != 200:
                return _RedirectResp("/login?oauth_error=userinfo_fail", status_code=302)
            uinfo = ur.json()
    except Exception as e:
        logger.error(f"[OAuth] callback fetch failed: {e}")
        return _RedirectResp("/login?oauth_error=fetch_fail", status_code=302)

    sub = uinfo.get("sub")
    email = (uinfo.get("email") or "").lower().strip()
    picture = (uinfo.get("picture") or "").strip()  # v118.27.5.3 · Google 头像 URL
    if not sub or not email:
        return _RedirectResp("/login?oauth_error=invalid_userinfo", status_code=302)

    # 1) 用 google_sub 找
    user = db.find_user_by_google_sub(sub)
    if not user:
        # 2) 用 email/username 找现有账号 · 自动绑定 google_sub(老用户首次用 Google 登录)
        existing = db.find_user_by_username(email)
        if existing:
            db.link_google_sub_to_user(str(existing["id"]), sub)
            user = db.find_user_by_username(email)
        else:
            # 3) v118.27.5.1 · 全新用户 · Google 一键注册(主流 SaaS 标准做法)
            try:
                from auth_signup import create_user_via_google_oauth

                _name = (uinfo.get("name") or "").strip() or None
                user = create_user_via_google_oauth(
                    email=email,
                    full_name=_name,
                    google_sub=sub,
                    ip=None,  # callback 这里取不到 client IP · 留空
                    ua=None,
                )
            except Exception as e:
                logger.error(f"[OAuth] google one-click signup failed: {e}")
                user = None
            if not user:
                return _RedirectResp("/login?oauth_error=signup_failed", status_code=302)

    # 颁 JWT(跟普通 login 走同一函数)
    db.update_last_login(str(user["id"]))
    # v118.27.5.3 · 同步 Google 头像(每次登录 refresh · 用户 Google 头像变了也跟随)
    if picture:
        try:
            db.update_user_avatar(str(user["id"]), picture)
        except Exception as e:
            logger.warning(f"[google_oauth] 同步用户头像失败: {e}")
    _safe_plan = user.get("plan") or "free"
    token = create_access_token(
        user_id=str(user["id"]),
        username=user["username"],
        plan=_safe_plan,
        tenant_id=str(user["tenant_id"]) if user.get("tenant_id") else None,
        role=user.get("role") or "owner",
        is_super_admin=bool(user.get("is_super_admin")),
        remember_me=True,
    )

    # 中间页 set localStorage 再跳 /home 或 /admin(callback 是 GET 不能直接 set)
    # v118.28.2 · 超管 → /admin · 普通用户 → /home
    safe_token = json.dumps(token)
    _redirect_path = "/admin" if bool(user.get("is_super_admin")) else "/home"
    return HTMLResponse(f"""<!doctype html>
<html><head><meta charset="utf-8"><title>Pearnly · Signing in...</title></head>
<body style="font-family:-apple-system,sans-serif;background:#0a0e27;color:#fff;display:flex;align-items:center;justify-content:center;height:100vh;margin:0">
<div>Signing you in...</div>
<script>
try {{ localStorage.setItem("mrpilot_token", {safe_token}); }} catch(e) {{}}
window.location.replace("{_redirect_path}");
</script>
</body></html>""")


# ============================================================
# v118.28.4 · LINE Login OAuth 2.0
# 一键登录 / 一键注册 · 跟 Google 同套机制
# email scope 需 LINE 单独审批 · 没拿到时占位 username
# ============================================================
_LINE_LOGIN_CHANNEL_ID = os.getenv("LINE_LOGIN_CHANNEL_ID", "")
_LINE_LOGIN_CHANNEL_SECRET = os.getenv("LINE_LOGIN_CHANNEL_SECRET", "")
_LINE_LOGIN_REDIRECT_URI = os.getenv(
    "LINE_LOGIN_REDIRECT_URI", "https://pearnly.com/api/auth/line/callback"
)


@app.get("/api/auth/line/start")
async def line_oauth_start():
    if not _LINE_LOGIN_CHANNEL_ID:
        raise HTTPException(status_code=503, detail="line_oauth_not_configured")
    state = _gen_oauth_state()
    params = {
        "response_type": "code",
        "client_id": _LINE_LOGIN_CHANNEL_ID,
        "redirect_uri": _LINE_LOGIN_REDIRECT_URI,
        "state": state,
        "scope": "openid profile email",  # v118.28.4.2 · email scope 已通过 · 自动拿邮箱
        "nonce": _secrets.token_urlsafe(16),
    }
    url = "https://access.line.me/oauth2/v2.1/authorize?" + _urlencode(params)
    return _RedirectResp(url, status_code=302)


@app.get("/api/auth/line/callback")
async def line_oauth_callback(code: str = "", state: str = "", error: str = ""):
    if error:
        return _RedirectResp(f"/login?oauth_error={error}", status_code=302)
    if not _verify_oauth_state(state):
        return _RedirectResp("/login?oauth_error=invalid_state", status_code=302)
    if not code:
        return _RedirectResp("/login?oauth_error=no_code", status_code=302)
    if not _LINE_LOGIN_CHANNEL_ID or not _LINE_LOGIN_CHANNEL_SECRET:
        return _RedirectResp("/login?oauth_error=line_not_configured", status_code=302)

    # code → access_token + id_token
    try:
        import httpx as _httpx

        async with _httpx.AsyncClient(timeout=15) as client:
            tr = await client.post(
                "https://api.line.me/oauth2/v2.1/token",
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                data={
                    "grant_type": "authorization_code",
                    "code": code,
                    "redirect_uri": _LINE_LOGIN_REDIRECT_URI,
                    "client_id": _LINE_LOGIN_CHANNEL_ID,
                    "client_secret": _LINE_LOGIN_CHANNEL_SECRET,
                },
            )
            if tr.status_code != 200:
                logger.error(
                    f"[LINE OAuth] token exchange failed {tr.status_code}: {tr.text[:300]}"
                )
                return _RedirectResp("/login?oauth_error=line_token_fail", status_code=302)
            tok_data = tr.json()
            id_token = tok_data.get("id_token")
            if not id_token:
                return _RedirectResp("/login?oauth_error=line_no_id_token", status_code=302)

            # 用 LINE 的 verify 端点 · 服务端验证 id_token + 拿 payload
            vr = await client.post(
                "https://api.line.me/oauth2/v2.1/verify",
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                data={
                    "id_token": id_token,
                    "client_id": _LINE_LOGIN_CHANNEL_ID,
                },
            )
            if vr.status_code != 200:
                logger.error(
                    f"[LINE OAuth] id_token verify failed {vr.status_code}: {vr.text[:300]}"
                )
                return _RedirectResp("/login?oauth_error=line_verify_fail", status_code=302)
            payload = vr.json()
    except Exception as e:
        logger.error(f"[LINE OAuth] callback fetch failed: {e}")
        return _RedirectResp("/login?oauth_error=line_fetch_fail", status_code=302)

    line_uid = payload.get("sub")
    line_name = (payload.get("name") or "").strip()
    line_picture = (payload.get("picture") or "").strip()
    line_email = (payload.get("email") or "").strip().lower()  # email scope 没批通常没这个
    if not line_uid:
        return _RedirectResp("/login?oauth_error=line_no_sub", status_code=302)

    # 1) 用 line_uid 找
    user = db.find_user_by_line_uid(line_uid)
    if not user:
        # 2) 如果有 email · 用 email 找现有账号 · 自动绑 line_uid(老用户首次用 LINE 登录)
        if line_email:
            existing = db.find_user_by_username(line_email)
            if existing:
                db.link_line_uid_to_user(str(existing["id"]), line_uid)
                user = db.find_user_by_username(line_email)
        if not user:
            # 3) 全新用户 · LINE 一键注册
            try:
                from auth_signup import create_user_via_line_oauth

                user = create_user_via_line_oauth(
                    line_uid=line_uid,
                    display_name=line_name or None,
                    email=line_email or None,
                    picture=line_picture or None,
                    ip=None,
                    ua=None,
                )
            except Exception as e:
                logger.error(f"[LINE OAuth] one-click signup failed: {e}")
                user = None
            if not user:
                return _RedirectResp("/login?oauth_error=line_signup_failed", status_code=302)

    # 颁 JWT
    db.update_last_login(str(user["id"]))
    if line_picture:
        try:
            db.update_user_avatar(str(user["id"]), line_picture)
        except Exception as e:
            logger.warning(f"[line_login] 同步用户头像失败: {e}")
    _safe_plan = user.get("plan") or "free"
    token = create_access_token(
        user_id=str(user["id"]),
        username=user["username"],
        plan=_safe_plan,
        tenant_id=str(user["tenant_id"]) if user.get("tenant_id") else None,
        role=user.get("role") or "owner",
        is_super_admin=bool(user.get("is_super_admin")),
        remember_me=True,
    )

    safe_token = json.dumps(token)
    # v118.28.2 · 超管 → /admin · 普通用户 → /home
    _redirect_path = "/admin" if bool(user.get("is_super_admin")) else "/home"
    return HTMLResponse(f"""<!doctype html>
<html><head><meta charset="utf-8"><title>Pearnly · Signing in...</title></head>
<body style="font-family:-apple-system,sans-serif;background:#0a0e27;color:#fff;display:flex;align-items:center;justify-content:center;height:100vh;margin:0">
<div>Signing you in...</div>
<script>
try {{ localStorage.setItem("mrpilot_token", {safe_token}); }} catch(e) {{}}
window.location.replace("{_redirect_path}");
</script>
</body></html>""")


# ============================================================
# v118.28.4.1 · LINE 用户补邮箱 API
# 进 /home 时前端先查 needs_email · true 则弹强制 modal
# 提交 email 时:已存在老账号 → 合并 line_uid + 删临时账号 + 颁老账号 token
#               不存在 → 把临时账号的 username/email 改成真邮箱
# ============================================================
@app.get("/api/me/needs_email")
async def me_needs_email(request: Request):
    user = get_current_user_from_request(request)
    uname = user.get("username") or ""
    needs = db.is_line_placeholder_username(uname)
    return {"needs_email": bool(needs)}


class _LinePostEmail(BaseModel):
    email: str


@app.post("/api/me/line_complete_email")
async def me_line_complete_email(payload: _LinePostEmail, request: Request):
    user = get_current_user_from_request(request)
    cur_username = user.get("username") or ""
    if not db.is_line_placeholder_username(cur_username):
        raise HTTPException(status_code=400, detail="not_a_line_temp_account")

    email_raw = (payload.email or "").strip().lower()
    if not email_raw or "@" not in email_raw or "." not in email_raw.split("@", 1)[1]:
        raise HTTPException(status_code=400, detail="email_invalid")

    cur_user_id = str(user["id"])
    line_uid = user.get("line_uid")

    # 检查该 email 是否已被其他账号占用
    existing = db.find_user_by_username(email_raw)
    if existing and str(existing["id"]) != cur_user_id:
        # 合并到老账号
        if not line_uid:
            raise HTTPException(status_code=500, detail="missing_line_uid")
        ok = db.merge_line_account_into_existing(cur_user_id, str(existing["id"]), line_uid)
        if not ok:
            raise HTTPException(status_code=500, detail="merge_failed")
        # 颁老账号 token
        merged_user = db.find_user_by_id(str(existing["id"]))
        if not merged_user:
            raise HTTPException(status_code=500, detail="target_user_lost")
        db.update_last_login(str(merged_user["id"]))
        new_token = create_access_token(
            user_id=str(merged_user["id"]),
            username=merged_user["username"],
            plan=merged_user.get("plan") or "free",
            tenant_id=str(merged_user["tenant_id"]) if merged_user.get("tenant_id") else None,
            role=merged_user.get("role") or "owner",
            is_super_admin=bool(merged_user.get("is_super_admin")),
            remember_me=True,
        )
        return {"ok": True, "merged": True, "token": new_token}
    else:
        # 直接更新临时账号
        ok = db.update_user_email_and_username(cur_user_id, email_raw)
        if not ok:
            raise HTTPException(status_code=500, detail="update_failed")
        # token 里的 username 变了 · 重发一次
        refreshed = db.find_user_by_id(cur_user_id)
        new_token = create_access_token(
            user_id=cur_user_id,
            username=refreshed["username"],
            plan=refreshed.get("plan") or "free",
            tenant_id=str(refreshed["tenant_id"]) if refreshed.get("tenant_id") else None,
            role=refreshed.get("role") or "owner",
            is_super_admin=bool(refreshed.get("is_super_admin")),
            remember_me=True,
        )
        return {"ok": True, "merged": False, "token": new_token}


# ============================================================
# v118.27.6 · SMTP 邮件 + 注册邮箱验证码
# ============================================================
import smtplib as _smtplib
import ssl as _ssl
import re as _re_v276
from email.mime.text import MIMEText as _MIMEText
from email.mime.multipart import MIMEMultipart as _MIMEMulti
from email.utils import formataddr as _formataddr
import traceback as _tb_v276


def _smtp_send_email(to_email: str, subject: str, html_body: str) -> tuple:
    """SMTP 发邮件 · 返回 (success: bool, error: str)"""
    host = os.environ.get("SMTP_HOST", "smtp.gmail.com").strip()
    try:
        port = int(os.environ.get("SMTP_PORT", "587"))
    except ValueError:
        port = 587
    user = os.environ.get("SMTP_USER", "").strip()
    pwd = os.environ.get("SMTP_PASSWORD", "").strip()
    from_addr = os.environ.get("SMTP_FROM", user).strip()
    from_name = os.environ.get("SMTP_FROM_NAME", "Pearnly").strip()

    if not host or not user or not pwd:
        return (False, "smtp_not_configured")
    try:
        msg = _MIMEMulti("alternative")
        msg["From"] = _formataddr((from_name, from_addr))
        msg["To"] = to_email
        msg["Subject"] = subject
        msg.attach(_MIMEText(html_body, "html", "utf-8"))

        ctx = _ssl.create_default_context()
        with _smtplib.SMTP(host, port, timeout=15) as s:
            s.ehlo()
            s.starttls(context=ctx)
            s.login(user, pwd)
            s.send_message(msg)
        return (True, "")
    except Exception as e:
        logger.error(f"smtp send failed: {type(e).__name__}: {e}")
        return (False, str(e)[:240])


def _build_verification_email_html(code: str, lang: str) -> tuple:
    """v118.27.6.1 · 企业级品牌邮件模板 · hero 渐变 + 大验证码 + 公司 footer · 4 语"""
    lang = (lang or "zh").lower()[:2]
    L = {
        "zh": {
            "subject": "Pearnly · 您的验证码",
            "tagline": "AI 财务副驾驶",
            "title": "您的验证码",
            "lead": "用于创建 Pearnly 账户 · 10 分钟内有效",
            "ignore": "如非本人操作 · 请忽略此邮件 · 您的账户安全无风险",
            "brand_full": "Pearnly · 泰国会计自动化平台",
            "tos": "服务条款",
            "privacy": "隐私政策",
            "copyright": "© 2026 Pearnly. All rights reserved.",
        },
        "th": {
            "subject": "Pearnly · รหัสยืนยันของคุณ",
            "tagline": "ผู้ช่วย AI ด้านบัญชี",
            "title": "รหัสยืนยันของคุณ",
            "lead": "ใช้รหัสนี้เพื่อสมัครบัญชี Pearnly · ใช้ได้ 10 นาที",
            "ignore": "หากคุณไม่ได้ทำรายการนี้ · โปรดเพิกเฉยอีเมลฉบับนี้",
            "brand_full": "Pearnly · ระบบอัตโนมัติบัญชีไทย",
            "tos": "ข้อกำหนด",
            "privacy": "นโยบายความเป็นส่วนตัว",
            "copyright": "© 2026 Pearnly · สงวนลิขสิทธิ์",
        },
        "en": {
            "subject": "Pearnly · Your verification code",
            "tagline": "Your AI accounting co-pilot",
            "title": "Your verification code",
            "lead": "Use this code to create your Pearnly account · valid for 10 minutes",
            "ignore": "If you didn't request this · please ignore this email",
            "brand_full": "Pearnly · Accounting automation for Thailand",
            "tos": "Terms",
            "privacy": "Privacy",
            "copyright": "© 2026 Pearnly. All rights reserved.",
        },
        "ja": {
            "subject": "Pearnly · 確認コード",
            "tagline": "AI 会計コパイロット",
            "title": "確認コード",
            "lead": "Pearnly アカウント作成用 · 10 分間有効",
            "ignore": "心当たりのない場合 · このメールを無視してください",
            "brand_full": "Pearnly · タイ会計自動化プラットフォーム",
            "tos": "利用規約",
            "privacy": "プライバシーポリシー",
            "copyright": "© 2026 Pearnly. All rights reserved.",
        },
    }
    tt = L.get(lang, L["zh"])
    html = f"""<!doctype html><html><body style="margin:0;padding:0;background:#f1f5f9;">
<div style="font-family:Inter,-apple-system,'PingFang SC',Sarabun,'Hiragino Sans',sans-serif;max-width:560px;margin:0 auto;padding:32px 16px;">
  <table border="0" cellpadding="0" cellspacing="0" width="100%" style="background:#fff;border-radius:16px;overflow:hidden;box-shadow:0 4px 24px rgba(15,23,42,0.08);">
    <tr><td style="background:linear-gradient(135deg,#0f172a 0%,#1e3a8a 60%,#2563eb 100%);padding:44px 40px 38px;text-align:center;">
      <table border="0" cellpadding="0" cellspacing="0" align="center"><tr>
        <td style="vertical-align:middle;padding-right:10px;">
          <div style="display:inline-block;width:36px;height:36px;background:#fff;border-radius:8px;text-align:center;line-height:36px;font-weight:800;font-size:18px;color:#1e3a8a;font-family:Inter,sans-serif;">P</div>
        </td>
        <td style="vertical-align:middle;">
          <div style="font-weight:800;font-size:24px;color:#fff;letter-spacing:-0.3px;line-height:1;">Pearnly</div>
        </td>
      </tr></table>
      <div style="margin-top:12px;font-size:12px;color:#cbd5e1;letter-spacing:1.5px;text-transform:uppercase;font-weight:600;">{tt["tagline"]}</div>
    </td></tr>
    <tr><td style="padding:44px 40px 36px;">
      <h1 style="font-size:22px;color:#0f172a;margin:0 0 10px;font-weight:700;letter-spacing:-0.2px;">{tt["title"]}</h1>
      <p style="font-size:14px;color:#64748b;line-height:1.65;margin:0 0 28px;">{tt["lead"]}</p>
      <div style="background:linear-gradient(135deg,#eff6ff 0%,#dbeafe 100%);border:1px solid #bfdbfe;border-radius:12px;padding:32px 24px;text-align:center;">
        <div style="font-size:38px;font-weight:700;letter-spacing:10px;color:#1e3a8a;font-family:'SF Mono','Roboto Mono',Consolas,monospace;line-height:1;">{code}</div>
      </div>
      <p style="font-size:13px;color:#94a3b8;line-height:1.65;margin:28px 0 0;">{tt["ignore"]}</p>
    </td></tr>
    <tr><td style="background:#f8fafc;padding:24px 40px 28px;border-top:1px solid #e2e8f0;text-align:center;">
      <div style="font-size:12px;color:#475569;margin-bottom:6px;font-weight:600;">{tt["brand_full"]}</div>
      <div style="font-size:11px;color:#94a3b8;line-height:1.7;">
        Bangkok, Thailand · <a href="https://pearnly.com" style="color:#94a3b8;text-decoration:none;">pearnly.com</a><br>
        hello@pearnly.com · LINE @059oupmg · +66 86-889-2228
      </div>
      <div style="margin-top:12px;font-size:11px;">
        <a href="https://pearnly.com/terms" style="color:#94a3b8;text-decoration:none;margin:0 8px;">{tt["tos"]}</a>
        <span style="color:#cbd5e1;">·</span>
        <a href="https://pearnly.com/privacy" style="color:#94a3b8;text-decoration:none;margin:0 8px;">{tt["privacy"]}</a>
      </div>
      <div style="font-size:10px;color:#cbd5e1;margin-top:14px;">{tt["copyright"]}</div>
    </td></tr>
  </table>
</div>
</body></html>"""
    return (tt["subject"], html)


_RE_EMAIL_V276 = _re_v276.compile(r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$")


class SendEmailCodeRequest(BaseModel):
    email: str
    purpose: str = "signup"
    lang: str = "zh"


class VerifyEmailCodeRequest(BaseModel):
    email: str
    code: str
    purpose: str = "signup"


@app.post("/api/auth/send_email_code")
def send_email_code(req: SendEmailCodeRequest, request: Request):
    """v118.27.6 · 发邮箱验证码 · 注册前必走"""
    try:
        email = (req.email or "").strip().lower()
        if not email or not _RE_EMAIL_V276.match(email):
            raise HTTPException(status_code=400, detail="email_invalid")
        if req.purpose not in ("signup",):
            raise HTTPException(status_code=400, detail="purpose_invalid")

        # 已注册则不发(防 enumerate 用 409 因为注册流程要明确告知)
        try:
            with db.get_cursor() as cur:
                cur.execute(
                    "SELECT 1 FROM users WHERE email_normalized = %s OR LOWER(email) = %s LIMIT 1",
                    (email, email),
                )
                if cur.fetchone():
                    raise HTTPException(status_code=409, detail="email_already_registered")
        except HTTPException:
            raise
        except Exception as e:
            logger.warning(f"send_email_code user check: {e}")

        # 限流 · 60s 内只能发 1 次 · 1 小时最多 5 次
        try:
            with db.get_cursor() as cur:
                cur.execute(
                    """
                    SELECT 1 FROM email_codes
                    WHERE email = %s AND purpose = %s AND sent_at > NOW() - INTERVAL '60 seconds'
                    LIMIT 1
                """,
                    (email, req.purpose),
                )
                if cur.fetchone():
                    raise HTTPException(status_code=429, detail="resend_too_fast")

                cur.execute(
                    """
                    SELECT COUNT(*) AS n FROM email_codes
                    WHERE email = %s AND purpose = %s AND sent_at > NOW() - INTERVAL '1 hour'
                """,
                    (email, req.purpose),
                )
                row = cur.fetchone()
                n = row.get("n") if isinstance(row, dict) else (row[0] if row else 0)
                if n and int(n) >= 5:
                    raise HTTPException(status_code=429, detail="hourly_limit_reached")
        except HTTPException:
            raise
        except Exception as e:
            logger.warning(f"send_email_code rate limit: {e}")

        # 6 位数字
        code = "".join([_secrets.choice("0123456789") for _ in range(6)])

        # 写 DB(旧未用 code 全部失效)
        ip = ""
        try:
            ip = (request.client.host if request.client else "")[:64]
        except Exception as e:
            logger.warning(f"[email_code] 读取客户端 IP 失败: {e}")
        try:
            with db.get_cursor(commit=True) as cur:
                cur.execute(
                    """
                    UPDATE email_codes SET used = TRUE, used_at = NOW()
                    WHERE email = %s AND purpose = %s AND used = FALSE
                """,
                    (email, req.purpose),
                )
                cur.execute(
                    """
                    INSERT INTO email_codes (email, code, purpose, expires_at, sender_ip)
                    VALUES (%s, %s, %s, NOW() + INTERVAL '10 minutes', %s)
                """,
                    (email, code, req.purpose, ip),
                )
        except Exception as e:
            logger.error(f"send_email_code db insert: {e}")
            raise HTTPException(status_code=500, detail="db_error")

        # 发邮件
        subject, html = _build_verification_email_html(code, req.lang)
        ok, err = _smtp_send_email(email, subject, html)
        if not ok:
            try:
                with db.get_cursor(commit=True) as cur:
                    cur.execute(
                        """
                        UPDATE email_codes SET used = TRUE, used_at = NOW()
                        WHERE email = %s AND code = %s AND purpose = %s
                    """,
                        (email, code, req.purpose),
                    )
            except Exception as e:
                logger.warning(f"[email_code] 标记 code 已用失败: {e}")
            logger.error(f"send_email_code smtp failed for {email}: {err}")
            raise HTTPException(status_code=502, detail="email_delivery_failed")

        logger.info(f"[v118.27.6] verification code sent to {email}")
        return {"ok": True, "ttl_seconds": 600, "resend_after": 60}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"send_email_code: {e}\n{_tb_v276.format_exc()}")
        raise HTTPException(status_code=500, detail="server_error")


@app.post("/api/auth/verify_email_code")
def verify_email_code(req: VerifyEmailCodeRequest):
    """v118.27.6 · 仅校验验证码 · 不消耗(消耗在 signup 时一并)"""
    try:
        email = (req.email or "").strip().lower()
        code = (req.code or "").strip()
        if not email or not code:
            raise HTTPException(status_code=400, detail="missing_fields")
        if not _re_v276.match(r"^\d{4,8}$", code):
            raise HTTPException(status_code=400, detail="code_invalid")

        with db.get_cursor() as cur:
            cur.execute(
                """
                SELECT id, expires_at, used FROM email_codes
                WHERE email = %s AND code = %s AND purpose = %s
                ORDER BY id DESC LIMIT 1
            """,
                (email, code, req.purpose),
            )
            row = cur.fetchone()
            if not row:
                raise HTTPException(status_code=400, detail="code_invalid")
            r = dict(row) if not isinstance(row, dict) else row
            if r.get("used"):
                raise HTTPException(status_code=400, detail="code_used")
            cur.execute("SELECT NOW() > %s AS expired", (r["expires_at"],))
            exp_row = cur.fetchone()
            expired = (
                exp_row.get("expired")
                if isinstance(exp_row, dict)
                else (exp_row[0] if exp_row else True)
            )
            if expired:
                raise HTTPException(status_code=400, detail="code_expired")
        return {"ok": True}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"verify_email_code: {e}")
        raise HTTPException(status_code=500, detail="server_error")


# (LINE 绑定 API + /api/me/lang → line_binding_routes.py · REFACTOR-B1)


# ------------------------------------------------------------
# T1 · LINE Webhook(v0.19.0 · 签名校验 + 事件分发)
# 图片 OCR 留到 T1 轮 3
# ------------------------------------------------------------


@app.post("/api/line/webhook")
async def line_webhook(request: Request):
    """
    LINE Messaging API webhook 入口。
    处理的事件:
      - follow:用户加 Bot 好友 · 回欢迎语 + 教绑定
      - unfollow:用户删 Bot · 记录不处理(LINE 不允许回复)
      - message.text:文字 · 若是 6 位数字 → 尝试绑定码消费
      - message.image:T1 轮 3 实现 OCR · 本轮提示「即将上线」
      - 其他 type:忽略
    """
    body = await request.body()
    signature = request.headers.get("x-line-signature", "")

    # 签名校验(仅在 Secret 已配置时强制)
    if not line_client.verify_signature(body, signature):
        logger.warning("[line_webhook] 签名校验失败")
        # 返回 200 避免 LINE 认为 webhook 挂掉 · 但不处理事件
        return {"status": "ignored"}

    try:
        payload = json.loads(body.decode("utf-8"))
    except Exception as e:
        logger.error(f"[line_webhook] JSON 解析失败: {e}")
        return {"status": "bad_json"}

    events = payload.get("events") or []
    for ev in events:
        try:
            await _handle_line_event(ev)
        except Exception as e:
            logger.error(f"[line_webhook] 事件处理异常: {e}")

    return {"status": "ok"}


# v118.25.4 · LINE 用户语言规范化(把 LINE 给的多种语言代码映射到我们支持的 4 语)
def _normalize_line_lang(raw_lang: str) -> str:
    """
    LINE 平台给的语言代码可能是 zh-Hant / zh-CN / zh-TW / en-US / ja-JP 等
    我们只支持 4 语:zh / en / th / ja · 主市场泰国
    完全无信息时 fallback 到 th(不是 zh)
    """
    if not raw_lang:
        return "th"
    rl = str(raw_lang).lower().replace("_", "-")
    if rl.startswith("zh"):
        return "zh"
    if rl.startswith("en"):
        return "en"
    if rl.startswith("ja"):
        return "ja"
    if rl.startswith("th"):
        return "th"
    return "th"  # 主市场 fallback


def _ev_lang(ev: dict) -> str:
    """从 LINE event 安全拿语言并规范化"""
    try:
        raw = line_client.pick_lang_from_line_event(ev) or ""
    except Exception:
        raw = ""
    return _normalize_line_lang(raw)


def _follow_lang(line_user_id: str) -> str:
    """
    follow event 平台不传 language · 主动调 Profile API 拿 · 规范化后返回
    适用于:加好友 / 解绑后重新加(此时 line_user_id 还没绑定记录)
    """
    if not line_user_id:
        return "th"
    try:
        profile = line_client.get_user_profile(line_user_id) or {}
        return _normalize_line_lang(profile.get("language") or "")
    except Exception as e:
        logger.warning(f"[line] _follow_lang profile 调用失败 · fallback th: {e}")
        return "th"


async def _handle_line_event(ev: dict):
    """单个 LINE 事件处理"""
    ev_type = ev.get("type")
    src = ev.get("source") or {}
    line_user_id = src.get("userId")
    reply_token = ev.get("replyToken")

    # follow:用户加 Bot 好友
    if ev_type == "follow":
        if reply_token:
            # v118.25.4 · LINE follow event 不传 language · 必须调 Profile API
            # 这覆盖了「解绑后重新加」场景 · 因为此时还没 line_bindings 记录
            lang = _follow_lang(line_user_id)
            line_client.reply_text(
                reply_token,
                line_client.t_line(lang, "welcome"),
            )
        return

    # unfollow:用户删 Bot
    if ev_type == "unfollow":
        logger.info(f"[line] 用户 {line_user_id} 删除了 Bot 好友")
        return

    # message
    if ev_type == "message":
        msg = ev.get("message") or {}
        msg_type = msg.get("type")

        # 文字消息:判断是否绑定码
        if msg_type == "text":
            text = (msg.get("text") or "").strip()
            # v118.25.4 · 把 ev 传过去 · 让 _handle_line_text 能拿到用户语言
            await _handle_line_text(line_user_id, reply_token, text, ev)
            return

        # 图片 / 文件消息:统一走 OCR 入口(支持 PDF / 图片 / Excel / CSV / Word / TXT)
        if msg_type in ("image", "file"):
            message_id = msg.get("id")
            filename = msg.get("fileName") if msg_type == "file" else f"line_{message_id}.jpg"
            # 检查是否绑定
            bound_user = db.get_user_by_line_user_id(line_user_id) if line_user_id else None
            if not bound_user:
                if reply_token:
                    # v118.25.4 · 用规范化后的 LINE 用户语言
                    lang = _ev_lang(ev)
                    line_client.reply_text(
                        reply_token,
                        line_client.t_line(lang, "image_not_bound"),
                    )
                return

            # v118.25.4 · 已绑定用户 · 优先用 Pearnly 网站偏好语言 · 兜底用 LINE 语言(不再写死 zh)
            lang = bound_user.get("preferred_lang") or _ev_lang(ev)

            # 立即 reply 告知"识别中"(replyToken 一分钟有效 · 必须快)
            if reply_token:
                line_client.reply_text(
                    reply_token,
                    line_client.t_ocr(lang, "processing"),
                )

            # 启后台任务跑 OCR + push 结果
            import asyncio

            asyncio.create_task(
                _handle_line_image_ocr(
                    bound_user=bound_user,
                    line_user_id=line_user_id,
                    message_id=message_id,
                    filename=filename,
                    lang=lang,
                )
            )
            return

        # 其他类型消息
        if reply_token:
            # v118.25.4 · 已绑定取用户偏好 · 未绑定用规范化 LINE 语言(不再 zh fallback)
            bound_user = db.get_user_by_line_user_id(line_user_id) if line_user_id else None
            lang = (bound_user.get("preferred_lang") if bound_user else None) or _ev_lang(ev)
            line_client.reply_text(
                reply_token,
                line_client.t_line(lang, "unsupported"),
            )
        return


async def _handle_line_text(line_user_id: str, reply_token: str, text: str, ev: dict):
    """处理 LINE 文字消息(v118.25.4 · ev 用于 fallback 拿 LINE 用户语言)"""
    if not reply_token or not line_user_id:
        return

    # v118.25.4 · 在最开头算出 ev_lang 备用 · 所有未确定身份的 fallback 都用它
    ev_lang = _ev_lang(ev)

    # 6 位数字 → 尝试当作绑定码
    if len(text) == 6 and text.isdigit():
        user_id = db.consume_line_binding_code(text)
        if not user_id:
            # v118.25.4 · 绑定码无效 · 还不知道是哪个 Pearnly 用户 · 用 LINE 语言
            line_client.reply_text(
                reply_token,
                line_client.t_line(ev_lang, "bind_invalid"),
            )
            return

        # 查 mrpilot 用户(为拿 preferred_lang)
        # v118.25.4 · 已确定身份 · 优先用网站偏好 · 兜底用 LINE 语言
        user = db.find_user_by_id(user_id)
        lang = (user.get("preferred_lang") if user else None) or ev_lang

        # 获取 LINE 用户昵称 / 头像
        profile = line_client.get_user_profile(line_user_id) or {}
        display_name = profile.get("displayName")
        picture_url = profile.get("pictureUrl")

        ok = db.create_or_update_line_binding(
            user_id=user_id,
            line_user_id=line_user_id,
            display_name=display_name,
            picture_url=picture_url,
        )
        if not ok:
            line_client.reply_text(
                reply_token,
                line_client.t_line(lang, "bind_conflict"),
            )
            return

        username = user.get("username") if user else ""
        line_client.reply_text(
            reply_token,
            line_client.t_line(
                lang,
                "bind_success",
                username=username,
                display_name=display_name or (line_user_id[:8] + "…"),
            ),
        )
        return

    # 非绑定码 · 判断是否已绑定
    bound_user = db.get_user_by_line_user_id(line_user_id)
    if not bound_user:
        # v118.25.4 · 未绑定 · 用 LINE 用户语言(之前写死 zh · 是已知简化 bug · 现在修)
        line_client.reply_text(
            reply_token,
            line_client.t_line(ev_lang, "need_bind"),
        )
    else:
        # v118.25.4 · 已绑定 · 优先用户偏好 · 兜底 LINE 语言
        lang = bound_user.get("preferred_lang") or ev_lang
        username = bound_user.get("username") or ""
        line_client.reply_text(
            reply_token,
            line_client.t_line(lang, "already_bound_hint", username=username),
        )


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
