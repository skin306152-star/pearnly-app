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

from fastapi import FastAPI, Request, HTTPException, status, UploadFile, File, Form
from fastapi.responses import HTMLResponse, FileResponse, Response, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

import db  # v0.6.4 修复:新增 ERP 路由用到了 db.xxx 命名空间
try:
    import line_client  # T1 · LINE Bot(v0.19.0)
except ImportError:
    line_client = None  # line_client.py 不在 pearnly 仓库 · 文件需单独部署到服务器
from db import (
    ensure_demo_account,
    find_user_by_username,
    update_last_login,
    get_ip_usage_today,
    increment_ip_usage,
    increment_user_monthly_usage,
    insert_ocr_history,
    list_ocr_history,
    get_ocr_history_detail,
    update_ocr_history_pages,
    delete_ocr_history,
    delete_ocr_history_with_pdf_paths,  # v114 · PDF 留底
    get_history_pdf_info,                # v114
    find_ocr_by_hash,
    # T1 · LINE Bot(v0.19.0)
    generate_line_binding_code,
    get_line_binding_by_user,
    unbind_line_by_user,
    update_user_preferred_lang,
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
from vat_excel_routes import router as vat_excel_router  # v118.32.4.9.5 · Excel 公式对账内测

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


# v118.34.13 (Zihao 2026-05-19 拍板) · 最近 500 错误的现场摘要 ·
# 通过 /api/version 直接读 · 用户不用 SSH 看 journalctl 也能拿到根因。
# 内容控制在 1500 字符内,堆栈尾巴优先(异常点附近)。
_last_500_event: Dict[str, Any] = {}


def _record_500(*, path: str = "", method: str = "", detail: str = ""):
    """Capture the current traceback (if any) + request context into the
    module-level snapshot that /api/version surfaces. Safe to call from
    anywhere — uses sys.exc_info() to grab the active traceback, falls
    back to a synthetic message when no exception is in flight."""
    import sys as _sys
    import time as _t
    import traceback as _tb
    tb_str = ""
    exc_type = ""
    try:
        et, ev, etb = _sys.exc_info()
        if et is not None and ev is not None:
            exc_type = et.__name__
            tb_str = "".join(_tb.format_exception(et, ev, etb))
    except Exception:
        pass
    if not tb_str and detail:
        tb_str = f"(no traceback) {detail}"
    # Trim to last 1500 chars — the tail is where the actual error is.
    _last_500_event.clear()
    _last_500_event.update({
        "ts": int(_t.time()),
        "path": str(path or "")[:200],
        "method": str(method or "")[:10],
        "detail": str(detail or "")[:200],
        "exc_type": exc_type,
        "traceback": (tb_str or "")[-1500:],
    })


def _read_last_500() -> Dict[str, Any]:
    """Snapshot copy of the last captured 500 event."""
    if not _last_500_event:
        return {}
    return dict(_last_500_event)

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
            pip_version = getattr(
                importlib.import_module("playwright"), "__version__", None
            )
        except Exception:
            pip_version = None
    except ImportError:
        pip_importable = False

    # ── Quick probe: chromium binary on disk? ──
    cache_root = (
        _os.environ.get("PLAYWRIGHT_BROWSERS_PATH")
        or _os.path.expanduser("~/.cache/ms-playwright")
    )
    chromium_installed = False
    chromium_dir = None
    try:
        if _os.path.isdir(cache_root):
            for name in _os.listdir(cache_root):
                if name.startswith("chromium") and _os.path.isdir(
                    _os.path.join(cache_root, name)
                ):
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
                "spawning install-deps in background", launch_result.get("error"),
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
            close_fds=True, start_new_session=True,
            stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
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
        cache_root = (
            _os.environ.get("PLAYWRIGHT_BROWSERS_PATH")
            or _os.path.expanduser("~/.cache/ms-playwright")
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
        _endpoint_test_cache.clear()
        _endpoint_customers_cache.clear()
        _endpoint_products_cache.clear()
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
        with open(_deploy_sh, 'w') as _f:
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
        logger.warning(f"[playwright-bootstrap] failed (will surface as "
                       f"ERR_PLAYWRIGHT_MISSING in wizard): {e}")

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
            for tbl in ['ocr_history', 'reconciliation_task', 'gl_vat_task']:
                try:
                    cur.execute(
                        f"UPDATE {tbl} SET status='interrupted' "
                        f"WHERE status='running'"
                    )
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
        logger.info("[email_ingest] 定时抓取已禁用(HF Space 不支持 IMAP 出站 · 迁 VPS 后设 EMAIL_INGEST_ENABLED=1)")

    # v118.25 · ERP 推送自动重试后台 worker(每 30 秒扫到期失败 log)
    erp_retry_task = asyncio.create_task(_erp_retry_loop())
    logger.info("[erp_retry] 自动重试后台 worker 已启动")

    logger.info(f"✅ Mr.Pearnly 已就绪 v0.21.0-v108 (Google 余额追踪 · 半自动校准)")
    yield
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
                history = db.get_ocr_history_detail(
                    str(log["user_id"]), str(log["history_id"]),
                    tenant_id=None,
                ) if log.get("history_id") else None
                endpoint = db.get_erp_endpoint(
                    str(log["user_id"]), str(log["endpoint_id"]),
                ) if log.get("endpoint_id") else None

                if not history or not endpoint:
                    # 关联实体已删 · 终止此 log 的重试
                    db.clear_retry_schedule(str(log["id"]))
                    logger.info(f"[erp_retry] log {log['id']} 关联记录已删 · 停止重试")
                    continue

                # 在 worker 线程里跑同步 push(避免阻塞事件循环)
                result = await _asyncio.to_thread(
                    _erp.push_to_endpoint, endpoint, history,
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
                            "[erp_retry] log %s 重试 #%d 命中 user-data 错 · "
                            "停止队列 (err=%r)",
                            log["id"], new_count,
                            (result.get("error_msg") or "")[:80],
                        )
                    else:
                        # 仍失败 · 看还有没有下一次
                        next_delay = db.get_erp_retry_delay_sec(new_count)
                        if next_delay is None:
                            # 用完 3 次 · 不再调度 · 等用户手动
                            db.clear_retry_schedule(str(log["id"]))
                            logger.warning(f"[erp_retry] log {log['id']} 重试 {new_count} 次仍失败 · 停止")
                        else:
                            db.schedule_log_retry(str(log["id"]), next_delay)
                            logger.info(f"[erp_retry] log {log['id']} 重试 #{new_count} 失败 · {next_delay}s 后再试")
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
                result = await asyncio.to_thread(
                    email_ingest.run_account_ingest, account, "auto"
                )
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
app.include_router(recon_router)   # v118.32.0 · 销项税对账
app.include_router(vat_excel_router)  # v118.32.4.9.5 · Excel 公式对账内测(skin306152 only)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# v118.34.13 (Zihao 2026-05-19 拍板) · catch-all exception handler so
# any uncaught exception writes a traceback snapshot into _last_500_event
# before propagating. HTTPException(500, ...) raised explicitly bypasses
# this (FastAPI handles it before this hook fires), so routes that raise
# 500 must also call _record_500 manually — see erp_endpoints_create.
@app.exception_handler(Exception)
async def _capture_unhandled_500(request: Request, exc: Exception):
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
        request.method, request.url.path, type(exc).__name__,
    )
    return JSONResponse(
        status_code=500,
        content={
            "detail": f"{type(exc).__name__}: {str(exc)[:200]}",
            "diag_url": "/api/version (see playwright.last_500_traceback)",
        },
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
    import os as _os, glob as _glob
    try:
        deleted = 0
        for fp in _glob.glob("static/**/*.gz", recursive=True):
            try:
                _os.remove(fp)
                deleted += 1
            except Exception:
                pass
        if deleted:
            logger.info(f"🧹 启动清除 static/**/*.gz · 删了 {deleted} 个陈旧预压缩文件 · nginx 将动态 gzip 当前源文件")
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


class UserInfo(BaseModel):
    # v118.35.0.15 · credits 全站统一后 · 所有老 plan/quota 字段改 Optional ·
    # _build_user_info() 已不再返回 plan/monthly_quota/trial_expires_at/
    # plan_expires_at/plan_days_left/tenant_quota/tenant_used 8 字段(v0.11) ·
    # 这里也跟着改成 Optional · 避免 Pydantic ResponseValidationError 500 ·
    # 配额改由 credits 系统(/api/me/credits)接管
    id: str
    username: str
    # v0.15.5 · 明确账号类型(monthly / lifetime / lifetime_pending)· 前端显隐判断用
    account_type: str = "monthly"
    used_this_month: int = 0
    # IP 限流(v0.8 废弃,仅兼容旧前端)
    ip_used_today: Optional[int] = None
    ip_daily_limit: Optional[int] = None
    # 精细化权限(全开 · credits 模型不再区分套餐)
    can_edit_fields: bool = True
    can_verify_tax: bool = True
    can_use_gemini: bool = True
    can_use_typhoon: bool = True
    can_use_custom_template: bool = True
    can_view_history: bool = True
    can_push_erp: bool = True
    can_manage_api_keys: bool = False
    # v0.15 · 买断标识
    has_own_gemini_key: bool = False
    # v0.8
    rd_daily_limit: Optional[int] = None
    can_extract_items: bool = True
    can_auto_push_erp: bool = False
    endpoints_limit: int = 1
    can_archive: bool = True
    can_customize_archive: bool = False
    zip_batch_limit: int = 10
    can_use_email_ingest: bool = False
    can_use_folder_watch: bool = False
    can_use_smart_alert: bool = False
    # 兼容旧字段(不再使用但前端可能仍引用)
    can_use_automation: bool = False
    # 配额(全部默认 0)
    typhoon_quota_monthly: int = 0
    typhoon_used_this_month: int = 0
    history_retention_days: int = 365
    custom_template_limit: int = 0
    # v22 · 多租户
    tenant_id: Optional[str] = None
    tenant_name: Optional[str] = None
    tenant_type: Optional[str] = None          # shared_api / byo_api / admin
    tenant_status: Optional[str] = None        # active / warning / suspended / frozen
    role: Optional[str] = None                 # owner / member
    is_super_admin: bool = False
    # v118.8.4 · 公司名 + 真实姓名(注册时填的) · 顶栏归属感用
    company_name: Optional[str] = None
    full_name: Optional[str] = None
    # v118.27.6 · Google 头像 URL(OAuth 注册同步)
    avatar_url: Optional[str] = None
    # v110.7 · 欢迎向导 profile 字段
    monthly_volume: Optional[str] = None
    country: Optional[str] = None
    line_id: Optional[str] = None
    phone: Optional[str] = None
    line_verified: bool = False
    profile_filled: bool = True
    # v118.11 · 员工首次登录强制改密
    must_change_password: bool = False
    # v118.35.0.11 · credits 新加 4 字段
    email: Optional[str] = None
    invited_by: Optional[str] = None
    is_billing_exempt: bool = False
    active_tenant_id: Optional[str] = None
    # === 老字段全部 Optional · _build_user_info 已不返回 · credits 系统接管 ===
    plan: Optional[str] = None                 # v0.11 删 · 仅保 Optional 兼容老前端
    monthly_quota: Optional[int] = None        # v0.11 删
    effective_plan: Optional[str] = None       # v0.11 删
    plan_expires_at: Optional[str] = None      # v0.11 删
    plan_days_left: Optional[int] = None       # v0.11 删
    trial_expires_at: Optional[str] = None     # v0.11 删
    trial_days_left: Optional[float] = None    # v0.11 删
    tenant_quota: Optional[int] = None         # v0.11 删
    tenant_used: Optional[int] = None          # v0.11 删
    expires_at: Optional[str] = None           # v0.11 删


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


def _build_user_info(user, ip_used=None, ip_limit=None) -> dict:
    # v118.35.0.11 · credits 统一后 · 老 plan / effective_plan / monthly_quota /
    # plan_expires_at / plan_days_left / trial_expires_at / tenant_quota /
    # tenant_used 字段全部从返回值删除 · 不再做员工继承老板 plan 的 DB 查询 ·
    # 不再算 plan_days_left / trial_days_left 这些套餐到期天数.
    # 配额改由 credits 系统(tenant_credits.balance_thb + monthly_page_usage)
    # 接管 · 前端读 /api/me/credits 拿余额和本月用量 · 设置页只显示用户名 +
    # 计费方式(按使用量计费)+ 价格说明小字.
    role = user.get("role") or "owner"
    is_super = bool(user.get("is_super_admin"))

    # v22 · 多租户:查用户所属租户(显示 tenant_name + tenant_type 给顶栏用)
    tenant_info = None
    if user.get("tenant_id"):
        try:
            tenant_info = db.get_tenant(str(user["tenant_id"]))
        except Exception as _te:
            logger.warning(f"_build_user_info: get_tenant failed: {_te}")
            tenant_info = None

    p_perms = _plan_permissions(None)

    # 自带 key 标识(设置页 API Key 输入框显隐用 · 跟 plan 解耦)
    has_own_key = bool((user.get("gemini_api_key") or "").strip())
    account_type = "lifetime" if has_own_key else "monthly"

    return {
        "id": str(user["id"]),
        "username": user["username"],
        "email": user.get("email") or None,
        "invited_by": user.get("invited_by"),
        "is_billing_exempt": bool(user.get("is_billing_exempt", False)),
        "active_tenant_id": str(user["active_tenant_id"]) if user.get("active_tenant_id") else None,
        "account_type": account_type,     # v0.15.5 · 明确的账号类型 · 供前端显示判断
        "used_this_month": int(user.get("used_this_month", 0) or 0),
        "ip_used_today": ip_used,
        "ip_daily_limit": ip_limit,
        # 基础能力
        "can_edit_fields": p_perms["can_edit_fields"],
        "can_verify_tax": p_perms["can_verify_tax"],
        "rd_daily_limit": p_perms.get("rd_daily_limit"),
        "can_extract_items": p_perms.get("can_extract_items", True),
        # 引擎
        "can_use_gemini": True,
        "can_use_typhoon": True,
        # 历史
        "can_view_history": p_perms["can_view_history"],
        "history_retention_days": p_perms["history_retention_days"],
        # ERP
        "can_push_erp": p_perms["can_push_erp"],
        "can_auto_push_erp": p_perms["can_auto_push_erp"],
        "endpoints_limit": p_perms["endpoints_limit"],
        # 归档
        "can_archive": p_perms["can_archive"],
        "can_customize_archive": p_perms["can_customize_archive"],
        "zip_batch_limit": p_perms["zip_batch_limit"],
        # 自动化
        "can_use_email_ingest": p_perms.get("can_use_email_ingest", False),
        "can_use_folder_watch": p_perms.get("can_use_folder_watch", False),
        "can_use_smart_alert": p_perms.get("can_use_smart_alert", False),
        # 次级
        "can_use_custom_template": p_perms.get("can_use_custom_template", False),
        "custom_template_limit": p_perms.get("custom_template_limit", 0),
        "typhoon_quota_monthly": p_perms.get("typhoon_quota_monthly", 0) or 0,
        "typhoon_used_this_month": user.get("typhoon_used_this_month", 0) or 0,
        "can_manage_api_keys": p_perms.get("can_manage_api_keys", False),
        # v118.35.0.11 · 删除 expires_at / plan_expires_at / plan_days_left /
        #               trial_expires_at / trial_days_left / tenant_quota /
        #               tenant_used · credits 系统接管 · 前端读 /api/me/credits
        "line_verified": bool(user.get("line_user_id") or user.get("line_verified_at")),
        # v0.15 · 新增:买断标识(前端根据此决定显示 API Key 输入框)
        "has_own_gemini_key": has_own_key,
        # v22 · 多租户:供前端显示租户信息 + 判断超管
        "tenant_id": str(user["tenant_id"]) if user.get("tenant_id") else None,
        "tenant_name": tenant_info.get("name") if tenant_info else None,
        "tenant_type": tenant_info.get("tenant_type") if tenant_info else None,
        "tenant_status": tenant_info.get("status") if tenant_info else None,
        "role": role,
        "is_super_admin": is_super,
        # v118.8.4 · 公司名 + 真实姓名(注册时填的) · 顶栏归属感 + 设置页显示
        # v118.12 · 员工的 company_name 应继承自 tenant(他不该自己有公司)
        "company_name": (tenant_info.get("name") if tenant_info else None) or user.get("company_name") or None,
        "full_name": user.get("full_name") or None,
        # v118.27.6 · Google 头像 URL(OAuth 注册时同步)
        "avatar_url": user.get("avatar_url") or None,
        # v110.7 · 欢迎向导用 · 暴露原始 profile 字段(role 已在上方 · 此处 raw 用于判断"是否填过")
        "monthly_volume": user.get("monthly_volume") or None,
        "country": user.get("country") or None,
        "line_id": user.get("line_id") or None,
        "phone": user.get("phone") or None,
        # v118.12.5 · onboarding wizard 暂时下架(没真实现个性化推荐 · 弹了也是噪音)
        # 永远返回 true · 前端 wizard 不弹 · 后续要恢复直接改回判断逻辑
        "profile_filled": True,
    }


def _plan_permissions(plan: str = None) -> dict:
    """
    v0.15 · 彻底扁平化 · 不再有套餐概念
    所有用户功能完全一样 · 配额由 user.monthly_quota 单独控制
    plan 参数保留仅为兼容 · 忽略其值 · 永远返回全开权限
    """
    return {
        # 这里的 monthly_quota 是 "权限层默认值" · 实际配额以 user.monthly_quota 为准
        # 下游代码应读 user.monthly_quota · 而不是 perms["monthly_quota"]
        "monthly_quota": None,                # 权限层不限 · 实际配额看 user
        "max_pages_per_upload": 50,
        "max_file_size_mb": 100,
        "can_edit_fields": True,
        "can_verify_tax": True,
        "rd_daily_limit": None,
        "can_extract_items": True,
        "can_view_history": True,
        "history_retention_days": 365,
        "can_push_erp": True,
        "can_auto_push_erp": True,
        "endpoints_limit": -1,
        "can_archive": True,
        "can_customize_archive": True,
        "zip_batch_limit": -1,
        "can_use_email_ingest": True,
        "can_use_folder_watch": True,
        "can_use_smart_alert": True,
        "can_use_custom_template": True,
        "custom_template_limit": -1,
        "typhoon_quota_monthly": 500,
        "can_manage_api_keys": True,
        "can_auto_classify": True,
        "can_duplicate_detect": True,
        "can_ai_query": True,
        "can_voucher_draft": True,
    }


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
    # v118.35.0.20 · 白名单改查 users.is_billing_exempt(取代硬编码 user_id)
    # 跟 auth_signup.check_ocr_quota 一致 · 单一数据源
    try:
        if db.is_user_billing_exempt(user.get("id")):
            return True, None, {
                "mode": "billing_exempt",
                "monthly_quota": None,
                "used_this_month": 0,
                "remaining": 999999,
            }
    except Exception as _wle:
        logger.warning(f"_check_user_quota whitelist lookup skip: {_wle}")
    # 老路径兼容(防 is_billing_exempt 字段读取异常时回退)
    if str(user.get("id") or "") == "468b50c1-5593-4fd6-990d-515ce8085563":
        return True, None, {
            "mode": "skin_test_whitelist",
            "monthly_quota": None,
            "used_this_month": 0,
        }

    # v118.26.2.4 · 安全闸 · 被禁用 / 封禁账号绝对不能 OCR
    if user.get("is_banned"):
        return False, "account.banned", {
            "mode": "banned",
            "monthly_quota": 0,
            "used_this_month": 0,
        }
    if user.get("is_active") is False:
        return False, "account.inactive", {
            "mode": "inactive",
            "monthly_quota": 0,
            "used_this_month": 0,
        }

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
                    _owner_plan = (_row["plan"] if isinstance(_row, dict) else _row[0])
                    if _owner_plan:
                        user_plan = _owner_plan
        except Exception as _e:
            logger.warning(f"_check_user_quota: lookup owner plan failed: {_e}")

    if user.get("is_super_admin") or user_plan == "admin":
        return True, None, {
            "mode": "admin",
            "monthly_quota": None,
            "used_this_month": 0,
        }
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
                        _gk = (_row["gemini_api_key"] if isinstance(_row, dict) else _row[0])
            except Exception as e:
                logger.warning(f"[user_info] 读取老板 gemini_api_key 失败: {e}")
        has_own_key = bool((_gk or "").strip())
        if has_own_key:
            return True, None, {
                "mode": "lifetime",
                "monthly_quota": None,
                "used_this_month": int(user.get("used_this_month") or 0),
            }
        return False, "quota.need_api_key", {
            "mode": "need_setup",
            "monthly_quota": 0,
            "used_this_month": 0,
        }
    if user_plan in ("trial", "free", "pro", "firm", "enterprise",
                     "monthly", "yearly"):
        return True, None, {
            "mode": "v109_plan",
            "monthly_quota": None,
            "used_this_month": int(user.get("used_this_month") or 0),
        }

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
                return True, None, {
                    "mode": "admin",
                    "monthly_quota": None,
                    "used_this_month": 0,
                }
            # 买断自带 key
            if tt == "byo_api":
                has_own_key = bool((user.get("gemini_api_key") or "").strip())
                if has_own_key:
                    return True, None, {
                        "mode": "lifetime",
                        "monthly_quota": None,
                        "used_this_month": int(user.get("used_this_month") or 0),
                    }
                return False, "quota.need_api_key", {
                    "mode": "need_setup",
                    "monthly_quota": 0,
                    "used_this_month": 0,
                }
            # 月付共用系统 key(shared_api)· 配额在 tenant 层
            if tt == "shared_api":
                t_quota = int(tenant.get("monthly_quota") or 0)
                t_used = int(tenant.get("used_this_month") or 0)
                if t_quota <= 0:
                    # 月付但管理员没配额度 · 联系管理员
                    return False, "quota.need_api_key", {
                        "mode": "need_setup",
                        "monthly_quota": 0,
                        "used_this_month": 0,
                    }
                if t_used >= t_quota:
                    return False, "quota.exhausted", {
                        "mode": "shared",
                        "monthly_quota": t_quota,
                        "used_this_month": t_used,
                    }
                return True, None, {
                    "mode": "shared",
                    "monthly_quota": t_quota,
                    "used_this_month": t_used,
                }

    # 老规则(兜底)· 保持向后兼容
    # === v109.3 · 新 plan 系统的用户(trial/free/pro/firm/enterprise)走新逻辑 ===
    # === v111.1 · 加 monthly/yearly/lifetime/admin 新档名 ===
    # 这些用户已经在前面被 v109.3 quota check 检查过 · 这里直接放行
    user_plan = user.get("plan")
    if user_plan in ("trial", "free", "pro", "firm", "enterprise",
                     "monthly", "yearly", "lifetime", "admin"):
        return True, None, {
            "mode": "v109_plan",
            "monthly_quota": None,
            "used_this_month": int(user.get("used_this_month") or 0),
        }

    has_own_key = bool((user.get("gemini_api_key") or "").strip())
    quota = user.get("monthly_quota")
    used = int(user.get("used_this_month") or 0)

    # 情况 1 · 自带 key(买断)· 无限制
    if has_own_key:
        return True, None, {
            "mode": "lifetime",
            "monthly_quota": None,
            "used_this_month": used,
        }

    # 情况 2 · 无 key · 无配额(或配额 <= 0)· 需要填 API Key
    if not quota or quota <= 0:
        return False, "quota.need_api_key", {
            "mode": "need_setup",
            "monthly_quota": 0,
            "used_this_month": used,
        }

    # 情况 3 · 月付 · 超额
    if used >= quota:
        return False, "quota.exhausted", {
            "mode": "monthly",
            "monthly_quota": int(quota),
            "used_this_month": used,
        }

    # 情况 4 · 月付 · 正常
    return True, None, {
        "mode": "monthly",
        "monthly_quota": int(quota),
        "used_this_month": used,
    }


# ============================================================
# Health & Contact
# ============================================================
@app.get("/api/health")
async def health():
    # 新架构 · pipeline_v1 唯一路径 · 健康检查改为校验 GCP Service Account 就绪
    _creds = (os.environ.get("GOOGLE_APPLICATION_CREDENTIALS") or "").strip()
    if _creds and os.path.isfile(_creds):
        credentials_status = {"available": True, "path": _creds}
    elif _creds:
        credentials_status = {"available": False, "error": f"file not found: {_creds}"}
    else:
        credentials_status = {"available": False, "error": "GOOGLE_APPLICATION_CREDENTIALS env not set"}
    return {
        "status": "ok",
        "version": "0.18.5-v105",
        "engines": {
            "pipeline": "pipeline_v1",
            "layers": ["text_path", "vision", "flash-lite", "flash"],
            "credentials_status": credentials_status,
        },
    }


@app.get("/api/contact")
async def contact():
    return {
        "phone": os.environ.get("CONTACT_PHONE", "086-889-2228"),
        "line_id": os.environ.get("CONTACT_LINE", "@Pearnly"),
        "line_url": os.environ.get("CONTACT_LINE_URL", "https://line.me/R/ti/p/@059oupmg"),
        "email": os.environ.get("CONTACT_EMAIL", "hello@pearnly.com"),
        "address": os.environ.get("CONTACT_ADDRESS", "Bangkok, Thailand"),
    }


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
            cur.execute("""
                SELECT COUNT(*) AS n FROM login_failure_log
                WHERE email_or_username = %s
                  AND created_at > NOW() - INTERVAL '30 minutes'
            """, (req.username.lower().strip(),))
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
            exp_dt = exp if hasattr(exp, "tzinfo") else datetime.fromisoformat(
                str(exp).replace("Z", "+00:00")
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
    return JSONResponse({
        "token": token,
        "access_token": token,
        "user": user_info,
        "must_change_password": must_change_password,
        "is_super_admin": bool(user.get("is_super_admin")),
    })


def _record_login_failure(username: str, request: Request):
    """记录登录失败 · 用于锁定逻辑"""
    try:
        import db as _db
        ip = request.client.host if request.client else None
        ua = request.headers.get("user-agent", "")[:200]
        with _db.get_cursor() as cur:
            cur.execute("""
                INSERT INTO login_failure_log(email_or_username, ip, user_agent)
                VALUES (%s, %s, %s)
            """, (username.lower().strip(), ip, ua))
    except Exception as e:
        logger.warning(f"login fail log skip: {e}")


# ============================================================
# User
# ============================================================
@app.get("/api/me", response_model=UserInfo)
async def get_me(request: Request):
    user = get_current_user_from_request(request)
    return _build_user_info(user, None, None)


# v110.7 · 用户完善资料 endpoint(欢迎向导 + 设置页共用)
class ProfileUpdate(BaseModel):
    role: Optional[str] = None
    monthly_volume: Optional[str] = None
    country: Optional[str] = None
    line_id: Optional[str] = None
    phone: Optional[str] = None
    # v118.10 · 让用户在设置页能补全姓名 / 公司名(注册时已变成选填)
    full_name: Optional[str] = None
    company_name: Optional[str] = None


@app.put("/api/me/profile")
async def update_me_profile(payload: ProfileUpdate, request: Request):
    """
    v110.7 · 更新当前用户的 profile 字段
    所有字段可选 · 只更新 payload 中明确提供的字段(None 表示不动)
    空字符串 / 仅空白 · 视为清空(写入 NULL)
    v118.10 · 新增 full_name + company_name(让设置页能补全)
    """
    user = get_current_user_from_request(request)

    fields = []
    values = []

    def _add(col, raw, max_len, transform=None):
        # raw 是 None 表示"不更新此字段"; 空字符串表示"清空"
        if raw is None:
            return
        v = (raw or "").strip()
        if transform:
            v = transform(v)
        v = v[:max_len] if v else ""
        fields.append(f"{col} = %s")
        values.append(v if v else None)

    _add("role", payload.role, 32)
    _add("monthly_volume", payload.monthly_volume, 16)
    _add("country", payload.country, 8, transform=lambda s: s.upper())
    _add("line_id", payload.line_id, 64, transform=lambda s: s.lstrip("@"))
    _add("phone", payload.phone, 32)
    # v118.10 · 新增字段
    _add("full_name", payload.full_name, 64)
    _add("company_name", payload.company_name, 200)

    if not fields:
        return {"ok": True, "updated": 0}

    values.append(user["id"])
    sql = f"UPDATE users SET {', '.join(fields)} WHERE id = %s"

    try:
        with db.get_cursor() as cur:
            cur.execute(sql, tuple(values))
    except Exception as e:
        logger.error(f"v110.7 update profile failed for user {user.get('id')}: {e}")
        raise HTTPException(500, detail={"code": "profile.update_failed", "msg": str(e)})

    return {"ok": True, "updated": len(fields)}


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
):
    user = get_current_user_from_request(request)
    client_ip = get_client_ip(request)
    plan = user.get("plan", "free")

    # 1. 基本校验 (2026-05-21 multi-format refactor: PDF + image + Excel + CSV + Word)
    from services.ocr.pipeline import (
        PDF_EXTENSIONS, IMAGE_EXTENSIONS, TABLE_EXTENSIONS,
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
            raise HTTPException(400, detail={
                "code": "ocr.too_many_pages",
                "max": max_pages, "actual": page_count,
            })
    else:
        page_count = 1  # images / single-CSV / single-DOCX count as 1 page

    # 4. 配额检查 · v0.15 · 新双轨:自带 key → 不限 · 否则扣 user.monthly_quota
    # === v109.3 · 新套餐配额检查(防薅 + 真实计量) ===
    try:
        from auth_signup import check_ocr_quota as _v109_quota
        _q = _v109_quota(str(user.get("id")))
        if not _q.get("allowed"):
            reason = _q.get("reason", "quota_exceeded")
            raise HTTPException(status_code=429, detail={
                "code": f"v109.{reason}",
                "used": _q.get("used"), "limit": _q.get("limit"), "plan": _q.get("plan"),
                "needs_line_verify": reason == "needs_line_verify",
            })
    except HTTPException:
        raise
    except Exception as _v109e:
        logger.warning(f"v109 quota check skip: {_v109e}")

    ok, err_code, quota_info = _check_user_quota(user)
    if not ok:
        if err_code == "quota.need_api_key":
            # 买断账号未填 key
            raise HTTPException(403, detail={
                "code": "quota.need_api_key",
            })
        elif err_code == "quota.exhausted":
            raise HTTPException(429, detail={
                "code": "ocr.monthly_limit_exceeded",
                "limit": quota_info["monthly_quota"],
                "used": quota_info["used_this_month"],
                "remaining": 0,
                "requested": page_count,
            })
        else:
            raise HTTPException(429, detail={"code": err_code or "quota.unknown"})

    # 如果是月付用户 · 并且本次识别会超额 · 也要拒绝
    if quota_info["mode"] == "monthly":
        mq = quota_info["monthly_quota"]
        um = quota_info["used_this_month"]
        if um + page_count > mq:
            raise HTTPException(429, detail={
                "code": "ocr.monthly_limit_exceeded",
                "limit": mq,
                "used": um,
                "remaining": max(0, mq - um),
                "requested": page_count,
            })

    monthly_quota = quota_info.get("monthly_quota")  # 兼容下游(None=不限)
    used_today = None
    used_month = quota_info.get("used_this_month")

    # v118.35.0.20 · Credits 余额前置检查(填上 cherry-pick v36 留的 TODO)
    # 业务: 没钱就不让 OCR · 白名单 is_billing_exempt 自动跳过
    # 估算成本仅供用户提示 · 不预扣 · 实际扣费在 OCR 完成后
    try:
        _billing = db.get_billing_status(str(user.get("id")), _tid(user))
        if not _billing.get("allowed") and not _billing.get("is_exempt"):
            # 估算本次成本(让用户知道需要充多少)
            if _ext in PDF_EXTENSIONS:
                _est_cost = float(db.estimate_pdf_cost_thb(_tid(user), page_count))
            else:
                _chars = db._excel_char_count_estimate(content, file.filename or "")
                _est_cost = float(db.estimate_excel_cost_thb(_chars))
            raise HTTPException(402, detail={
                "code": "insufficient_balance",
                "balance": _billing.get("balance_thb", 0.0),
                "estimated_cost": _est_cost,
                "pages_used_this_month": _billing.get("pages_used_this_month", 0),
            })
    except HTTPException:
        raise
    except Exception as _be:
        logger.warning(f"[credits] billing pre-check skip(error tolerated): {_be}")

    # 4.5. 文件指纹缓存 · v0.8 改:所有 plan 都启用(按 user_id 隔离,不跨用户)
    # v92 · 缓存窗口从 24h 扩到 30 天(默认) · 月末复核上月票也能命中 · 省 Gemini 配额
    import hashlib
    file_hash = hashlib.sha256(content).hexdigest()
    cached = find_ocr_by_hash(str(user["id"]), file_hash, tenant_id=_tid(user))
    if cached:
        logger.info(f"  🎯 命中文件缓存 (hash={file_hash[:12]}..., 省额度)")

        # v0.9 · 缓存命中也触发自动推送(用户的期待是"每次上传就推送")
        cache_auto_pushed = False
        if _plan_permissions(plan).get("can_auto_push_erp"):
            try:
                auto_eps = db.list_erp_endpoints(str(user["id"]), auto_push_only=True)
                if auto_eps:
                    import asyncio
                    asyncio.create_task(_auto_push_history(str(user["id"]), cached["id"], auto_eps, tenant_id=_tid(user)))
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
            _primary = next((p for p in _cached_pages if not p.get("is_duplicate") and not p.get("is_copy")), None)
            _primary = _primary or (_cached_pages[0] if _cached_pages else None)
            _cf = (_primary or {}).get("fields") or {}
            _exc_total_c = None
            _raw_t_c = _cf.get("total_amount")
            if _raw_t_c:
                try:
                    _exc_total_c = float(str(_raw_t_c).replace(",", "").strip())
                except Exception as e:
                    logger.warning(f"[cache_hit] total_amount 解析失败: {e}")
            _asyncio_exc_c.create_task(_async_run_exception_checks(
                history_id=str(cached["id"]),
                user_id=str(user["id"]),
                tenant_id=_tid(user),
                seller_name=_cf.get("seller_name"),
                invoice_no=_cf.get("invoice_number"),
                total_amount=_exc_total_c,
                confidence=cached.get("confidence"),
                duplicate=None,  # 缓存命中说明 hash 全等 · 由专门的 duplicate 路径处理(本身已是同张)
                fields=_cf,
            ))
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
            _pipe_res = _pipeline_run_table(content, filename=file.filename or "upload", api_key=api_key)
            chain_info = ["pipeline_v1_table"]
        result = pipeline_result_to_legacy_dict(_pipe_res)
        _pipeline_cost_thb = float(_pipe_res.estimated_cost_thb)
        logger.info(
            f"🆕 pipeline_v1 · file={file.filename} · ext={_ext} · pages={_pipe_res.page_count} "
            f"· cost=฿{_pipeline_cost_thb:.4f} · elapsed={_pipe_res.elapsed_ms}ms"
        )

        # v118.35.0.20 · Credits 真扣费 · OCR 成功才扣 · 豁免账号自动跳过
        # PDF 按页扣 · Excel/Word/CSV 按字符扣
        try:
            if _ext in PDF_EXTENSIONS:
                _charge = db.charge_ocr(
                    user_id=str(user.get("id")), tenant_id=_tid(user),
                    kind="pdf", units=int(_pipe_res.page_count or page_count),
                    description=f"OCR PDF · {file.filename}",
                )
            else:
                # Excel/CSV/Word · 按字符计费 · _excel_char_count_estimate 计字符数
                _chars = db._excel_char_count_estimate(content, file.filename or "")
                _charge = db.charge_ocr(
                    user_id=str(user.get("id")), tenant_id=_tid(user),
                    kind="excel", units=int(_chars),
                    description=f"OCR Excel · {file.filename} · {_chars} chars",
                )
            if _charge.get("ok"):
                logger.info(f"💳 charged ฿{_charge.get('charged_thb', 0):.2f} · bal_after=฿{_charge.get('balance_after')}")
            else:
                logger.warning(f"💳 charge_ocr FAIL: {_charge.get('error')}")
        except Exception as _ce:
            logger.warning(f"💳 charge_ocr exception(silent): {_ce}")
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
        if f.get("invoice_number"): s += 1
        if f.get("date"): s += 1
        if f.get("total_amount"): s += 1
        if f.get("seller_name") or f.get("seller_tax"): s += 1
        if f.get("buyer_name") or f.get("buyer_tax"): s += 1
        items = f.get("items") or []
        if items: s += 2
        # v118.20.4.2 · 文本路径补偿:subtotal + vat 双有 → 等价 items(发票结构完整)
        elif f.get("subtotal") and f.get("vat"): s += 2
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
        invoice_groups = [{
            "invoice_fields": {},
            "source_pages": result["pages"],
            "page_indices": list(range(1, result["page_count"] + 1)),
        }]

    invoice_count = len(invoice_groups)
    source_pdf_id = str(_uuid.uuid4()) if invoice_count > 1 else None

    # 取用户归档模板(一次查询复用)
    try:
        template = db.get_archive_template(str(user["id"])) or _archive.DEFAULT_TEMPLATE
    except Exception:
        template = _archive.DEFAULT_TEMPLATE

    history_ids = []
    duplicate_warnings = []         # v0.13 · 收集所有发票的重复警告
    primary_history_id = None       # 第一张发票的 history_id · 兼容老前端字段
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
                    duplicate_warnings.append({
                        "invoice_index": idx,           # 第几张
                        "invoice_total": invoice_count, # 共几张
                        "level": dup["level"],          # exact / likely
                        "matched_fields": dup["matched_fields"],
                        "match": dup["match"],
                        "current": {
                            "invoice_no": inv_no,
                            "invoice_date": date_iso,
                            "seller_name": seller,
                            "total_amount": total_f,
                        },
                    })
                    logger.info(f"⚠️ 检测到重复发票 (idx={idx} · {dup['level']} · 匹配于历史 {dup['match']['id']})")
            except Exception as e:
                logger.warning(f"重复检测失败(已忽略): {e}")

        # v92 · Bug 1 第 1 层防御 · 识别成功才带 file_hash · 防止空结果污染缓存
        _gf = g_fields or {}
        _has_inv = bool(str(_gf.get("invoice_number") or "").strip())
        _has_amt = _gf.get("total_amount") is not None and bool(str(_gf.get("total_amount")).strip())
        _has_seller = bool(str(_gf.get("seller_name") or "").strip())
        _recognized_ok = _has_inv or _has_amt or _has_seller
        _cache_hash = file_hash if (idx == 1 and _recognized_ok) else None
        if idx == 1 and not _recognized_ok:
            logger.warning(f"⚠️ 识别失败(关键字段全空) · file_hash 不入缓存 · file={file.filename}")

        hid = insert_ocr_history(
            user_id=str(user["id"]),
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
            client_id=(int(client_id) if (client_id and str(client_id).strip().isdigit()) else None),
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
                    int(client_id) if (client_id and str(client_id).strip().isdigit())
                    else None
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
                                hid, rcid, str(user["id"]),
                                tenant_id=_tid(user),
                            )
                            db.learn_buyer_to_client(
                                _buyer_name, _buyer_tax, rcid,
                                str(user["id"]), tenant_id=_tid(user),
                            )
                            _auto_resolved_client = True
                            logger.info(
                                "[auto-resolve] history=%s client_id=%s "
                                "name=%r conf=%.2f source=%s",
                                hid[:8], rcid, resolved.get("client_name"),
                                conf, resolved.get("match_source"),
                            )
                        elif conf >= 0.80 and rcid:
                            # 建议归属 · 不 auto-assign · 标 suggestion
                            # 抽屉 UI 显示 "建议归属 X · 点确认"
                            logger.info(
                                "[auto-resolve] SUGGEST history=%s client_id=%s "
                                "name=%r conf=%.2f",
                                hid[:8], rcid, resolved.get("client_name"), conf,
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
                                        str(user["id"]), hid, _new_pages,
                                        tenant_id=_tid(user),
                                    )
                            except Exception as _se:
                                logger.warning(f"stash suggestion failed: {_se}")
                    else:
                        logger.info(
                            "[auto-resolve] no match history=%s buyer=%r",
                            hid[:8], (_buyer_name or "")[:40],
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
                _asyncio_exc.create_task(_async_run_exception_checks(
                    history_id=str(hid),
                    user_id=str(user["id"]),
                    tenant_id=_tid(user),
                    seller_name=(g_fields or {}).get("seller_name"),
                    invoice_no=(g_fields or {}).get("invoice_number"),
                    total_amount=_exc_total,
                    confidence=confidence,
                    duplicate=_dup_for_idx,
                    fields=g_fields or {},  # v118.20.1.5 · 全字段 · 给自洽性规则用
                ))
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
                        str(user["id"]), hid, tenant_id=_tid(user),
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
                                str(user["id"]), hid, auto_eps,
                                tenant_id=_tid(user),
                            ),
                        )
                    auto_pushed = True
                    logger.info(
                        "🚀 自动推送已入队 · %d/%d 张发票 × %d 端点 "
                        "(没归属的发票跳过)",
                        len(pushable_ids), len(history_ids), len(auto_eps),
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
        logger.info(f"💰 成本记录 · {total_pages} 页 · in={total_input_tokens} out={total_output_tokens} · ≈THB {cost_thb:.4f}")
    except Exception as _cost_err:
        logger.warning(f"成本记录写入失败(不影响识别): {_cost_err}")

    return {
        "filename": file.filename,
        "page_count": result["page_count"],
        "elapsed_ms": result["elapsed_ms"],
        "engine": result["engine"],
        "pages": result["pages"],
        "confidence": confidence,
        "history_id": primary_history_id,        # 兼容老前端
        "history_ids": history_ids,              # v0.11 · 全部 id 列表
        "invoice_count": invoice_count,          # v0.11 · 识别出几张发票
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
            "used_this_month": new_month_used if new_month_used is not None else int(user.get("used_this_month") or 0),
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
            records.append({
                "filename": h.get("filename") or f"history-{hid}",
                "engine": "",
                "merged_fields": mf,
            })
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
@app.get("/api/v1/me")
async def v1_me(request: Request):
    return await get_me(request)


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


@app.get("/api/v1/health")
async def v1_health():
    return await health()


@app.get("/api/v1/contact")
async def v1_contact():
    return await contact()


# ============================================================
# 第 5 批 · 历史记录路由(Plus/Pro · Free 禁用)
# ============================================================

class HistoryUpdateRequest(BaseModel):
    pages: List[Any] = Field(..., description="完整 pages 数组(会计修改后的)")


# ============================================================
# v118.20.1 · 异常栏(Exceptions)· 阶段 1 · 数据底座 + 3 类零成本规则
#   - confidence_low:OCR 置信度非 high(对应低/中)
#   - duplicate:与历史发票重复(复用 check_duplicate_invoice 结果)
#   - amount_missing:关键字段缺失(总金额 + 发票号都为空)
# v118.20.1.5 · 阶段 1.5 · 加自洽性规则(数据真实性的根)
#   - math_mismatch:未税 + 税额 ≠ 总额(±1฿ 容差)
#   - tax_id_format_invalid:卖方税号不是 13 位纯数字(泰国 RD 标准)
# ============================================================

# 规则码 · 集中常量(后续阶段 4 加 tax_invalid / large_amount 在这里追加)
EXC_RULE_CONFIDENCE_LOW    = "confidence_low"
EXC_RULE_DUPLICATE         = "duplicate"
EXC_RULE_AMOUNT_MISSING    = "amount_missing"
EXC_RULE_MATH_MISMATCH     = "math_mismatch"
EXC_RULE_TAX_ID_FORMAT     = "tax_id_format_invalid"


def _parse_money(raw) -> Optional[float]:
    """容错解析金额字符串 → float · 解析失败返回 None"""
    if raw is None:
        return None
    try:
        s = str(raw).replace(",", "").replace("฿", "").replace("THB", "").strip()
        if not s:
            return None
        return float(s)
    except Exception:
        return None


def _is_valid_thai_tax_id(tax_id: Optional[str]) -> bool:
    """泰国 RD 税号:13 位纯数字 · 其它一律不合规"""
    if not tax_id:
        return False
    s = str(tax_id).strip().replace("-", "").replace(" ", "")
    return len(s) == 13 and s.isdigit()


async def _async_run_exception_checks(history_id: str, user_id: str,
                                       tenant_id: Optional[str],
                                       seller_name: Optional[str],
                                       invoice_no: Optional[str],
                                       total_amount: Optional[float],
                                       confidence: Optional[str],
                                       duplicate: Optional[Dict[str, Any]],
                                       fields: Optional[Dict[str, Any]] = None):
    """OCR 完成后异步跑规则 · 任何失败都吞掉 · 绝不影响主流程"""
    try:
        fields = fields or {}
        # v118.22.0.5/6 · 诊断 log(降级 debug · 排查时改 debug→info 临时开)
        logger.debug(
            f"[exception] hook IN hid={history_id} conf={confidence!r} "
            f"sub={fields.get('subtotal')!r} vat={fields.get('vat')!r} "
            f"total={total_amount!r} stax={fields.get('seller_tax')!r} "
            f"all_keys={list(fields.keys())}"
        )
        # v118.22.1.1 · 收集本次写入的 high severity 异常 · 函数末尾触发智能提醒
        _high_inserted: List[str] = []  # 元素是 rule_code
        # ── Rule 1 · confidence_low(非 high 即拦)
        # v118.22.0.6 · 修暗坑:conf=None / 空串 时前端显示「请复核」但 hook 原本跳过 · 现在也拦
        if (not confidence) or confidence != "high":
            if not db.is_exception_whitelisted(user_id, tenant_id, seller_name, EXC_RULE_CONFIDENCE_LOW):
                _sev_1 = "medium" if confidence == "medium" else "high"
                _ex_id_1 = db.insert_exception(
                    user_id=user_id, tenant_id=tenant_id, history_id=history_id,
                    rule_code=EXC_RULE_CONFIDENCE_LOW,
                    severity=_sev_1,
                    seller_name=seller_name, invoice_no=invoice_no, total_amount=total_amount,
                    detail={"confidence": confidence},
                )
                if _ex_id_1 and _sev_1 == "high":
                    _high_inserted.append(EXC_RULE_CONFIDENCE_LOW)
        # ── Rule 2 · duplicate(已检测过 · 直接复用)
        if duplicate:
            if not db.is_exception_whitelisted(user_id, tenant_id, seller_name, EXC_RULE_DUPLICATE):
                _sev_2 = "high" if duplicate.get("level") == "exact" else "medium"
                _ex_id_2 = db.insert_exception(
                    user_id=user_id, tenant_id=tenant_id, history_id=history_id,
                    rule_code=EXC_RULE_DUPLICATE,
                    severity=_sev_2,
                    seller_name=seller_name, invoice_no=invoice_no, total_amount=total_amount,
                    detail={
                        "level": duplicate.get("level"),
                        "matched_fields": duplicate.get("matched_fields"),
                        "match_id": (duplicate.get("match") or {}).get("id"),
                        "match_filename": (duplicate.get("match") or {}).get("filename"),
                        "match_invoice_no": (duplicate.get("match") or {}).get("invoice_no"),
                    },
                )
                if _ex_id_2 and _sev_2 == "high":
                    _high_inserted.append(EXC_RULE_DUPLICATE)
        # ── Rule 3 · amount_missing(总金额 + 发票号 都为空 → 严重异常)
        _no_amount = (total_amount is None)
        _no_invno = (not invoice_no or not str(invoice_no).strip())
        if _no_amount and _no_invno:
            if not db.is_exception_whitelisted(user_id, tenant_id, seller_name, EXC_RULE_AMOUNT_MISSING):
                _ex_id_3 = db.insert_exception(
                    user_id=user_id, tenant_id=tenant_id, history_id=history_id,
                    rule_code=EXC_RULE_AMOUNT_MISSING, severity="high",
                    seller_name=seller_name, invoice_no=None, total_amount=None,
                    detail={"missing": ["total_amount", "invoice_no"]},
                )
                if _ex_id_3:
                    _high_inserted.append(EXC_RULE_AMOUNT_MISSING)
        # ── Rule 4 · math_mismatch(自洽性 · 未税 + 税额 ≠ 总额 → 假数据嫌疑)
        _sub  = _parse_money(fields.get("subtotal"))
        _vat  = _parse_money(fields.get("vat"))
        if _sub is not None and _vat is not None and total_amount is not None:
            _expected = round(_sub + _vat, 2)
            _diff = abs(_expected - total_amount)
            if _diff > 1.0:  # ±1฿ 舍入容差
                if not db.is_exception_whitelisted(user_id, tenant_id, seller_name, EXC_RULE_MATH_MISMATCH):
                    _ex_id_4 = db.insert_exception(
                        user_id=user_id, tenant_id=tenant_id, history_id=history_id,
                        rule_code=EXC_RULE_MATH_MISMATCH,
                        severity="high",  # 数学不自洽 = OCR 数据可能编的 · 高危
                        seller_name=seller_name, invoice_no=invoice_no, total_amount=total_amount,
                        detail={
                            "subtotal": _sub, "vat": _vat,
                            "total_actual": total_amount,
                            "total_expected": _expected,
                            "diff": round(_diff, 2),
                        },
                    )
                    if _ex_id_4:
                        _high_inserted.append(EXC_RULE_MATH_MISMATCH)
        # ── Rule 5 · tax_id_format_invalid(卖方税号不是 13 位 → OCR 读错 / 假票)
        _stax = fields.get("seller_tax")
        if _stax and not _is_valid_thai_tax_id(_stax):
            if not db.is_exception_whitelisted(user_id, tenant_id, seller_name, EXC_RULE_TAX_ID_FORMAT):
                _clean = str(_stax).strip().replace("-", "").replace(" ", "")
                db.insert_exception(
                    user_id=user_id, tenant_id=tenant_id, history_id=history_id,
                    rule_code=EXC_RULE_TAX_ID_FORMAT, severity="medium",
                    seller_name=seller_name, invoice_no=invoice_no, total_amount=total_amount,
                    detail={
                        "tax_id_raw": _stax,
                        "tax_id_normalized": _clean,
                        "expected": "13 digits",
                        "actual_length": len(_clean),
                    },
                )
                # severity 是 medium · 不进 _high_inserted
        # v118.22.1.1 · 智能提醒触发(异步 fire-and-forget · 失败吞)
        try:
            import asyncio as _asyncio_notif
            for _hi_rule in _high_inserted:
                _asyncio_notif.create_task(_notify_exception_high(
                    user_id=user_id, tenant_id=tenant_id, history_id=history_id,
                    rule_code=_hi_rule, seller_name=seller_name,
                    invoice_no=invoice_no, total_amount=total_amount,
                ))
            # 大额发票通知触发(独立于异常 · 只要 total 非空就检查)
            if total_amount is not None:
                _asyncio_notif.create_task(_notify_large_invoice(
                    user_id=user_id, tenant_id=tenant_id, history_id=history_id,
                    seller_name=seller_name, invoice_no=invoice_no,
                    total_amount=total_amount,
                ))
        except Exception as _ne:
            logger.warning(f"notify trigger enqueue failed (hid={history_id}): {_ne}")
    except Exception as e:
        logger.warning(f"_async_run_exception_checks failed (hid={history_id}): {e}")


# v118.22.1.1 · 智能提醒触发 helper · 异步 fire-and-forget
# 调用方:_async_run_exception_checks 在 hook 末尾分别 create_task

# 内置模板代码常量(对应 line_client.NOTIFICATION_TEMPLATES)
NOTIF_TEMPLATE_EXCEPTION_HIGH = "exception_high"
NOTIF_TEMPLATE_LARGE_INVOICE  = "large_invoice"
NOTIF_TEMPLATE_WHITELIST = {NOTIF_TEMPLATE_EXCEPTION_HIGH, NOTIF_TEMPLATE_LARGE_INVOICE}


def _format_thb(amount: Optional[float]) -> str:
    """统一金额格式化 · 中文 / 英文 / 通用 · 千分位 + 2 位小数"""
    if amount is None:
        return "-"
    try:
        return f"฿ {float(amount):,.2f}"
    except Exception:
        return str(amount)


def _user_lang_safe(user_id: str) -> str:
    """取用户首选语言 · v118.25.3 · 默认 th(主市场泰国 · 之前 fallback 中文是 bug)"""
    try:
        u = db.find_user_by_id(user_id) or {}
        return (u.get("preferred_lang") or "th")
    except Exception:
        return "th"


def _rule_belongs_to(rule: dict, target_user_id: str, target_tenant_id: Optional[str]) -> bool:
    """判断一条规则是否归属指定 user/tenant
    tenant 模式:同 tenant_id 即同租户共享
    个人模式:rule_user == target_user 且 rule_tenant 为空
    """
    r_tenant = rule.get("tenant_id")
    if target_tenant_id:
        return r_tenant is not None and str(r_tenant) == str(target_tenant_id)
    return (str(rule.get("user_id") or "") == str(target_user_id)) and (r_tenant is None)


async def _notify_exception_high(user_id: str, tenant_id: Optional[str],
                                 history_id: str, rule_code: str,
                                 seller_name: Optional[str],
                                 invoice_no: Optional[str],
                                 total_amount: Optional[float]):
    """异常 high 触发 · 给该 user/tenant 所有启用 exception_high 规则推 LINE"""
    try:
        rules = db.list_active_notification_rules_by_template(NOTIF_TEMPLATE_EXCEPTION_HIGH)
        for r in rules:
            if not _rule_belongs_to(r, user_id, tenant_id):
                continue
            r_user = str(r.get("user_id") or "")
            r_tenant = r.get("tenant_id")
            binding = db.get_line_binding_by_user(r_user)
            if not binding or not binding.get("line_user_id"):
                db.log_notification(
                    user_id=r_user, tenant_id=r_tenant,
                    rule_id=r["id"], template_code=NOTIF_TEMPLATE_EXCEPTION_HIGH,
                    event_type="exception_high", event_ref=str(history_id),
                    line_user_id=None, status="failed", error="line_not_bound",
                )
                continue
            line_uid = binding["line_user_id"]
            lang = _user_lang_safe(r_user)
            rule_label = line_client.t_notify(lang, f"rule_label_{rule_code}")
            text = line_client.render_notification(lang, "exception_high", {
                "seller": seller_name or "-",
                "invoice_no": invoice_no or "-",
                "rule_label": rule_label,
                "amount": _format_thb(total_amount),
                "url": "https://pearnly.com",
            })
            ok = line_client.push_text(line_uid, text)
            db.log_notification(
                user_id=r_user, tenant_id=r_tenant,
                rule_id=r["id"], template_code=NOTIF_TEMPLATE_EXCEPTION_HIGH,
                event_type="exception_high", event_ref=str(history_id),
                line_user_id=line_uid,
                status="sent" if ok else "failed",
                error=None if ok else "line_push_failed",
            )
    except Exception as e:
        logger.warning(f"_notify_exception_high failed (hid={history_id}): {e}")


async def _notify_large_invoice(user_id: str, tenant_id: Optional[str],
                                history_id: str,
                                seller_name: Optional[str],
                                invoice_no: Optional[str],
                                total_amount: Optional[float]):
    """大额发票触发 · 比对该 user/tenant 所有启用 large_invoice 规则的阈值"""
    if total_amount is None:
        return
    try:
        rules = db.list_active_notification_rules_by_template(NOTIF_TEMPLATE_LARGE_INVOICE)
        for r in rules:
            if not _rule_belongs_to(r, user_id, tenant_id):
                continue
            params = r.get("params") or {}
            try:
                threshold = float(params.get("threshold") or 0)
            except Exception:
                threshold = 0.0
            if threshold <= 0 or float(total_amount) < threshold:
                continue
            r_user = str(r.get("user_id") or "")
            r_tenant = r.get("tenant_id")
            binding = db.get_line_binding_by_user(r_user)
            if not binding or not binding.get("line_user_id"):
                db.log_notification(
                    user_id=r_user, tenant_id=r_tenant,
                    rule_id=r["id"], template_code=NOTIF_TEMPLATE_LARGE_INVOICE,
                    event_type="large_invoice", event_ref=str(history_id),
                    line_user_id=None, status="failed", error="line_not_bound",
                )
                continue
            line_uid = binding["line_user_id"]
            lang = _user_lang_safe(r_user)
            text = line_client.render_notification(lang, "large_invoice", {
                "seller": seller_name or "-",
                "invoice_no": invoice_no or "-",
                "amount": _format_thb(total_amount),
                "threshold": _format_thb(threshold),
                "url": "https://pearnly.com",
            })
            ok = line_client.push_text(line_uid, text)
            db.log_notification(
                user_id=r_user, tenant_id=r_tenant,
                rule_id=r["id"], template_code=NOTIF_TEMPLATE_LARGE_INVOICE,
                event_type="large_invoice", event_ref=str(history_id),
                line_user_id=line_uid,
                status="sent" if ok else "failed",
                error=None if ok else "line_push_failed",
            )
    except Exception as e:
        logger.warning(f"_notify_large_invoice failed (hid={history_id}): {e}")


# ─── API 端点 ───────────────────────────────────────────

class ExceptionResolvePayload(BaseModel):
    # 可选字段:仅当 ignore_rule=True 时 · 把 (seller, rule) 加入白名单
    ignore_rule: bool = False


@app.get("/api/exceptions/list")
async def api_list_exceptions(request: Request,
                               status: str = "pending",
                               rule_code: Optional[str] = None,
                               client_id: Optional[int] = None,
                               limit: int = 100, offset: int = 0):
    """列异常(同 tenant 共享视图)· status=all 看全部 · client_id 给了只看该客户"""
    user = get_current_user_from_request(request)
    items = db.list_exceptions(
        user_id=str(user["id"]),
        tenant_id=_tid(user),
        status=status, rule_code=rule_code,
        client_id=client_id,
        limit=min(int(limit), 500), offset=max(int(offset), 0),
        restrict_client_ids=db.get_visible_client_ids_for_user(user),  # v118.28.1 · 员工分配
    )
    return {"items": items, "count": len(items)}


@app.get("/api/exceptions/stats")
async def api_exceptions_stats(request: Request, client_id: Optional[int] = None,
                                status: Optional[str] = "pending"):
    """顶部 KPI + 筛选 chip 的数字 · 同 tenant 共享 · 可按 client 收口
    status:控制 chip 计数(by_rule)归属哪个状态 · 顶部 KPI 整体计数不受影响
    """
    user = get_current_user_from_request(request)
    by_rule_status = status if status in ("pending", "resolved", "ignored") else "pending"
    stats = db.count_exceptions_by_status_and_rule(
        str(user["id"]), tenant_id=_tid(user), client_id=client_id,
        by_rule_status=by_rule_status,
    )
    stats["learned_rules"] = db.count_whitelist_rules(str(user["id"]), tenant_id=_tid(user))
    return stats


@app.get("/api/exceptions/{exception_id}")
async def api_get_exception(exception_id: int, request: Request):
    """单条异常详情(给抽屉用)"""
    user = get_current_user_from_request(request)
    ex = db.get_exception(str(user["id"]), int(exception_id), tenant_id=_tid(user))
    if not ex:
        raise HTTPException(404, detail="exception.not_found")
    return ex


@app.post("/api/exceptions/{exception_id}/resolve")
async def api_resolve_exception(exception_id: int, request: Request):
    """会计「✓ 确认放行」· 标记为 resolved · 不写白名单"""
    user = get_current_user_from_request(request)
    ok = db.resolve_exception(str(user["id"]), int(exception_id),
                              tenant_id=_tid(user), new_status="resolved")
    if not ok:
        raise HTTPException(404, detail="exception.not_found")
    return {"ok": True}


@app.post("/api/exceptions/{exception_id}/ignore")
async def api_ignore_exception(exception_id: int, request: Request):
    """会计「⊘ 忽略此类」· 标 ignored + 把 (seller, rule) 写入白名单 · 下次同类不拦"""
    user = get_current_user_from_request(request)
    ex = db.get_exception(str(user["id"]), int(exception_id), tenant_id=_tid(user))
    if not ex:
        raise HTTPException(404, detail="exception.not_found")
    # 1. 标 ignored
    db.resolve_exception(str(user["id"]), int(exception_id),
                         tenant_id=_tid(user), new_status="ignored")
    # 2. 写白名单(供应商名 + 规则码 · 缺供应商时只标 ignored 不写白名单)
    seller = ex.get("seller_name")
    rule_code = ex.get("rule_code")
    wl_added = False
    if seller and rule_code:
        wl_added = db.add_exception_whitelist(
            str(user["id"]), _tid(user), seller, rule_code
        )
    return {"ok": True, "whitelist_added": wl_added}


# v118.20.5 · P0-3 · 批量复核(全部放行 / 全部忽略此类)
@app.post("/api/exceptions/batch")
async def api_batch_exceptions(request: Request):
    """批量处理异常 · body: { ids: [int], action: "resolve"|"ignore" }
    返回:{ ok, processed, ids_done, whitelist_added }
    - resolve:批量标 resolved · 不写白名单
    - ignore:批量标 ignored · 同时按 (seller, rule) 去重写白名单(缺 seller 的仅 ignored)
    """
    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(400, detail="invalid_json")
    ids = payload.get("ids") or []
    action = payload.get("action") or ""
    if action not in ("resolve", "ignore"):
        raise HTTPException(400, detail="invalid_action")
    if not isinstance(ids, list) or not ids:
        raise HTTPException(400, detail="empty_ids")
    if len(ids) > 500:
        raise HTTPException(400, detail="too_many")
    user = get_current_user_from_request(request)
    new_status = "resolved" if action == "resolve" else "ignored"
    res = db.batch_resolve_exceptions(
        user_id=str(user["id"]),
        exception_ids=ids,
        tenant_id=_tid(user),
        new_status=new_status,
    )
    # ignored → 写白名单(去重在 db 已做 · 这里仅插入)
    wl_added = 0
    if action == "ignore":
        for seller, rc in (res.get("whitelist_pairs") or []):
            if db.add_exception_whitelist(str(user["id"]), _tid(user), seller, rc):
                wl_added += 1
    return {
        "ok": True,
        "processed": int(res.get("processed", 0)),
        "ids_done": res.get("ids_done", []),
        "whitelist_added": wl_added,
    }


# v118.21.2 · 学习规则面板 · 列表 + 删除(撤销学过的白名单)
@app.get("/api/exception-whitelist")
async def api_list_exception_whitelist(request: Request):
    """列出当前 user/tenant 学过的白名单"""
    user = get_current_user_from_request(request)
    items = db.list_exception_whitelist(str(user["id"]), tenant_id=_tid(user))
    return {"items": items, "count": len(items)}


@app.delete("/api/exception-whitelist/{wl_id}")
async def api_delete_exception_whitelist(wl_id: int, request: Request):
    """删除一条白名单(撤销学习)"""
    user = get_current_user_from_request(request)
    ok = db.delete_exception_whitelist(str(user["id"]), int(wl_id), tenant_id=_tid(user))
    if not ok:
        raise HTTPException(404, detail="whitelist.not_found")
    return {"ok": True}


def _tid(user: dict) -> Optional[str]:
    """v118.14 · 多租户共享:返回用户的 tenant_id 字符串(用于 db 函数过滤同 tenant 数据)
    给 list_ocr_history / get_ocr_history_detail / find_ocr_by_hash 等的 tenant_id 参数使用
    传了 → 同 tenant 所有成员共享数据(老板看员工的发票)
    没传 / NULL → fallback 单 user 老逻辑(向前兼容)
    """
    if not user:
        return None
    tid = user.get("tenant_id")
    return str(tid) if tid else None


def _check_history_access(user: dict):
    """v0.8 · 所有 plan 都能看历史,保留天数不同"""
    plan = (user or {}).get("plan", "free")
    p = _plan_permissions(plan)
    if not p.get("can_view_history"):
        raise HTTPException(403, detail="history.upgrade_required")
    return int(p.get("history_retention_days", 7))


@app.get("/api/history")
async def history_list(
    request: Request,
    keyword: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    client_id: Optional[int] = None,
):
    user = get_current_user_from_request(request)
    retention = _check_history_access(user)
    # 安全限制
    limit = max(1, min(int(limit), 100))
    offset = max(0, int(offset))
    return list_ocr_history(
        user_id=str(user["id"]),
        retention_days=retention,
        keyword=keyword.strip() if keyword else None,
        limit=limit,
        offset=offset,
        tenant_id=_tid(user),
        client_id=client_id,  # v118.28.0 · 顶栏客户切换器过滤
        restrict_client_ids=db.get_visible_client_ids_for_user(user),  # v118.28.1 · 员工分配
    )


@app.get("/api/history/{record_id}")
async def history_detail(record_id: str, request: Request):
    user = get_current_user_from_request(request)
    _check_history_access(user)
    detail = get_ocr_history_detail(str(user["id"]), record_id, tenant_id=_tid(user))
    if not detail:
        raise HTTPException(404, detail="history.not_found")
    return detail


@app.put("/api/history/{record_id}")
async def history_update(record_id: str, req: HistoryUpdateRequest, request: Request):
    user = get_current_user_from_request(request)
    _check_history_access(user)
    if not req.pages:
        raise HTTPException(400, detail="history.empty_pages")
    ok = update_ocr_history_pages(str(user["id"]), record_id, req.pages, tenant_id=_tid(user))
    if not ok:
        raise HTTPException(404, detail="history.not_found")
    # v118.18 · 推荐分类「学习」· 用户改了 category 就记忆「seller → category」
    try:
        for p in req.pages or []:
            if p.get("is_duplicate") or p.get("is_copy"):
                continue
            f = p.get("fields") or {}
            seller = (f.get("seller_name") or "").strip()
            cat = (f.get("category") or "").strip()
            if seller and cat:
                db.upsert_supplier_category(
                    seller_name=seller, category=cat,
                    user_id=str(user["id"]), tenant_id=_tid(user),
                )
            break  # 只学主页 · 多页发票其他页是副本不学
    except Exception as _ue:
        logger.warning(f"upsert supplier_category 失败(已忽略): {_ue}")
    # v118.21.3 · 字段改完后重跑规则 · 让异常自动消失或更新
    rechecked = False
    try:
        # 取主页字段(跟 OCR 时的 hook 输入一致)
        primary = None
        for p in req.pages or []:
            if p.get("is_duplicate") or p.get("is_copy"):
                continue
            primary = p
            break
        if primary:
            f = primary.get("fields") or {}
            seller_name = (f.get("seller_name") or "").strip() or None
            invoice_no = (f.get("invoice_number") or f.get("invoice_no") or "").strip() or None
            total_amount = _parse_money(f.get("total_amount"))
            # 取 history 的当前 confidence(更新 pages 不会影响 confidence · 复用现值)
            detail_now = get_ocr_history_detail(str(user["id"]), record_id, tenant_id=_tid(user))
            confidence = (detail_now or {}).get("confidence")
            # 1. 删该 history 下所有 pending 异常
            db.delete_pending_exceptions_by_history(record_id, tenant_id=_tid(user), user_id=str(user["id"]))
            # 2. 同步重跑规则(duplicate 不重检 · 因为依赖 OCR 时的指纹比对 · 此处保留为 None)
            await _async_run_exception_checks(
                history_id=record_id,
                user_id=str(user["id"]),
                tenant_id=_tid(user),
                seller_name=seller_name,
                invoice_no=invoice_no,
                total_amount=total_amount,
                confidence=confidence,
                duplicate=None,
                fields=f,
            )
            rechecked = True
    except Exception as _re:
        logger.warning(f"history_update rechek hook failed (id={record_id}): {_re}")
    return {"ok": True, "rechecked": rechecked}


@app.delete("/api/history/{record_id}")
async def history_delete(record_id: str, request: Request):
    user = get_current_user_from_request(request)
    _check_history_access(user)
    # v114 · 删除时同步清掉留底的 PDF 文件
    deleted, pdf_paths = delete_ocr_history_with_pdf_paths(str(user["id"]), [record_id], tenant_id=_tid(user))
    if deleted == 0:
        raise HTTPException(404, detail="history.not_found")
    # v114 · 检查这个 PDF 是否还被其他记录引用(多发票拆分场景共享同一 PDF)· 没人引用才真正删
    for p in pdf_paths:
        try:
            still_used = False
            from db import get_cursor
            with get_cursor() as cur:
                cur.execute("SELECT 1 FROM ocr_history WHERE pdf_storage_path = %s LIMIT 1", (p,))
                still_used = cur.fetchone() is not None
            if not still_used:
                pdf_storage.delete_pdf(p)
        except Exception as e:
            logger.warning(f"清理 PDF 文件失败(已忽略): {e}")
    return {"ok": True}


# v114 · PDF 留底下载接口 · 用户可下载自己识别过的原 PDF
@app.get("/api/history/{record_id}/pdf")
async def history_pdf_download(record_id: str, request: Request):
    from fastapi.responses import FileResponse
    user = get_current_user_from_request(request)
    _check_history_access(user)
    info = get_history_pdf_info(str(user["id"]), record_id, tenant_id=_tid(user))
    if not info:
        raise HTTPException(404, detail="history.pdf_not_found")
    abs_path = pdf_storage.get_pdf_abs_path(info["pdf_storage_path"])
    if not abs_path or not abs_path.exists():
        raise HTTPException(404, detail="history.pdf_missing")
    fn = info.get("filename") or "invoice.pdf"
    if not fn.lower().endswith(".pdf"):
        fn = fn + ".pdf"
    return FileResponse(
        path=str(abs_path),
        media_type="application/pdf",
        filename=fn,
    )


# v0.16 · 批量删除历史记录
class HistoryBatchDeleteRequest(BaseModel):
    ids: List[str] = Field(..., min_length=1, max_length=500)


@app.post("/api/history/batch-delete")
async def history_batch_delete(req: HistoryBatchDeleteRequest, request: Request):
    user = get_current_user_from_request(request)
    _check_history_access(user)
    uid = str(user["id"])
    # v114 · 一次性删除 + 拿到所有要清理的 PDF 路径
    deleted, pdf_paths = delete_ocr_history_with_pdf_paths(uid, list(req.ids), tenant_id=_tid(user))
    failed = max(0, len(req.ids) - deleted)
    # v114 · 检查每个 PDF 是否还被其他记录引用 · 没人引用才物理删
    if pdf_paths:
        try:
            from db import get_cursor
            for p in set(pdf_paths):
                try:
                    with get_cursor() as cur:
                        cur.execute("SELECT 1 FROM ocr_history WHERE pdf_storage_path = %s LIMIT 1", (p,))
                        still_used = cur.fetchone() is not None
                    if not still_used:
                        pdf_storage.delete_pdf(p)
                except Exception as e:
                    logger.warning(f"[batch-delete] 清理 PDF 失败 {p}: {e}")
        except Exception as e:
            logger.warning(f"[batch-delete] 清理 PDF 阶段失败(已忽略): {e}")
    return {"ok": True, "deleted": deleted, "failed": failed}


# v1 别名
@app.get("/api/v1/history")
async def v1_history_list(request: Request, keyword: Optional[str] = None, limit: int = 50, offset: int = 0):
    return await history_list(request, keyword, limit, offset)


@app.get("/api/v1/history/{record_id}")
async def v1_history_detail(record_id: str, request: Request):
    return await history_detail(record_id, request)


@app.put("/api/v1/history/{record_id}")
async def v1_history_update(record_id: str, req: HistoryUpdateRequest, request: Request):
    return await history_update(record_id, req, request)


@app.delete("/api/v1/history/{record_id}")
async def v1_history_delete(record_id: str, request: Request):
    return await history_delete(record_id, request)


# ============================================================
# 第 6.0 批 · ERP 推送(支柱 3)
# ============================================================
import erp_push as _erp


def _check_push_access(user: dict):
    """所有 plan 都可用 ERP 推送(v0.8)· Free 有数量限制,无自动推"""
    plan = (user or {}).get("plan", "free")
    p = _plan_permissions(plan)
    if not p.get("can_push_erp"):
        raise HTTPException(403, detail="erp.upgrade_required")


class ErpEndpointCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=80)
    adapter: str = Field(..., description="webhook | mr_erp | flowaccount")
    config: Dict[str, Any] = Field(default_factory=dict, description="适配器配置:url/token/...")
    is_default: bool = False
    auto_push: bool = False


class ErpEndpointUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=80)
    config: Optional[Dict[str, Any]] = None
    is_default: Optional[bool] = None
    auto_push: Optional[bool] = None
    enabled: Optional[bool] = None


class ErpTestConnectionRequest(BaseModel):
    adapter: str
    config: Dict[str, Any] = Field(default_factory=dict)


def _strip_endpoint_for_response(ep: Dict[str, Any]) -> Dict[str, Any]:
    """返回前端时,把 token / 加密凭据 字段隐藏,避免泄漏"""
    out = dict(ep)
    cfg = dict(out.get("config") or {})
    if "token" in cfg and cfg["token"]:
        t = str(cfg["token"])
        cfg["token"] = (t[:4] + "***" + t[-4:]) if len(t) > 10 else "***"
        cfg["_token_set"] = True
    # P1-B / C-1 · MR.ERP endpoints store Fernet-encrypted creds. The
    # UI must never see them — replace with sentinel flags so the
    # wizard knows credentials are present without exposing the values.
    for sensitive in ("username_enc", "password_enc"):
        if sensitive in cfg and cfg[sensitive]:
            cfg[sensitive] = "***"
            cfg[f"_{sensitive}_set"] = True
    out["config"] = cfg
    return out


@app.get("/api/erp/endpoints")
async def erp_endpoints_list(request: Request):
    user = get_current_user_from_request(request)
    _check_push_access(user)
    items = db.list_erp_endpoints(user["id"])
    return {"items": [_strip_endpoint_for_response(it) for it in items]}


@app.post("/api/erp/endpoints")
async def erp_endpoints_create(req: ErpEndpointCreate, request: Request):
    """v118.34.13 (Zihao 2026-05-19 拍板) · 加 try/except + 500 现场记录 +
    mrerp 凭据先 Fernet 加密再存盘。之前 wizard 把 plaintext 塞进
    username_enc/password_enc 字段名(假签名)· DB 存的是明文 ·
    回头 test-connection 解密就 InvalidToken。现在路由识别 mrerp ·
    走 kms_helper.encrypt_str 转 ciphertext 再落地。"""
    user = get_current_user_from_request(request)
    _check_push_access(user)
    p = _plan_permissions(user.get("plan", "free"))

    try:
        # v0.8 · 数量限制
        ep_limit = p.get("endpoints_limit", 1)
        if ep_limit != -1:
            existing = db.list_erp_endpoints(user["id"])
            if len(existing) >= ep_limit:
                raise HTTPException(403, detail={
                    "code": "erp.endpoint_limit_reached",
                    "limit": ep_limit,
                })

        # v0.8 · 自动推送权限
        if req.auto_push and not p.get("can_auto_push_erp"):
            raise HTTPException(403, detail="erp.auto_push_plus_required")

        if req.adapter not in _erp.ADAPTER_REGISTRY:
            raise HTTPException(400, detail="erp.unknown_adapter")

        # Bug 1 (Zihao 2026-05-19 拍板 · v118.34.22) · 拒绝没绑客户的 mrerp endpoint
        # 落库 · 否则推送时 ERR_NO_CLIENT 一连串失败. 前端 wizard Step 1 也加了
        # 一道闸 · 这里是双保险(API 直接打过来 / 老 wizard 残留状态).
        config = dict(req.config or {})
        if req.adapter == "mrerp":
            client_ids = config.get("client_ids") or []
            if not isinstance(client_ids, list) or not client_ids:
                raise HTTPException(
                    400,
                    detail={
                        "code": "erp.endpoint_no_clients",
                        "message_zh": "这个 ERP 连接还没绑任何 Pearnly 客户 · 请在向导第 1 步至少选 1 个客户",
                        "message_en": "No Pearnly clients linked to this ERP connection · pick at least one in wizard Step 1",
                    },
                )

        # v118.34.13 · 加密 mrerp 凭据再落地 · wizard 发的是 plaintext。
        # 即使字段名叫 _enc · 不加密就 None-op 解密会炸。
        if req.adapter == "mrerp":
            try:
                from kms_helper import encrypt_str, is_encrypted
                for fld in ("username_enc", "password_enc"):
                    v = config.get(fld)
                    if v and isinstance(v, str) and not is_encrypted(v):
                        config[fld] = encrypt_str(v)
            except ImportError as e:
                # kms_helper 不可用(env 缺 KMS_KEY)· 记录并报清晰错误,
                # 别让 500 给用户看一片空白。
                _record_500(
                    path="/api/erp/endpoints", method="POST",
                    detail=f"kms_helper unavailable: {e}",
                )
                raise HTTPException(
                    500,
                    detail="erp.kms_key_missing · server KMS_KEY env not set",
                )
            except Exception as e:
                _record_500(
                    path="/api/erp/endpoints", method="POST",
                    detail=f"encrypt failed: {type(e).__name__}: {e}",
                )
                raise HTTPException(
                    500, detail=f"erp.encrypt_failed: {type(e).__name__}",
                )

        new_id = db.create_erp_endpoint(
            user["id"], req.name, req.adapter, config,
            is_default=req.is_default, auto_push=req.auto_push,
        )
        if not new_id:
            # db.create_erp_endpoint swallowed the underlying DB error
            # and returned None. Pull the last DB-side error out of the
            # module global if available, otherwise mark as opaque.
            last = getattr(db, "_last_create_endpoint_error", None) or "unknown"
            _record_500(
                path="/api/erp/endpoints", method="POST",
                detail=f"db.create_erp_endpoint returned None · {last}",
            )
            raise HTTPException(
                500,
                detail=f"erp.create_failed · {str(last)[:200]}",
            )
        ep = db.get_erp_endpoint(user["id"], new_id)
        return _strip_endpoint_for_response(ep) if ep else {"id": new_id}
    except HTTPException:
        raise
    except Exception as e:
        # Last-resort capture so /api/version's last_500_traceback
        # shows the real stack instead of opaque "create_failed".
        _record_500(
            path="/api/erp/endpoints", method="POST",
            detail=f"{type(e).__name__}: {str(e)[:200]}",
        )
        logger.exception("[erp_endpoints_create] unhandled error")
        raise HTTPException(500, detail=f"erp.create_failed: {type(e).__name__}: {str(e)[:200]}")


@app.patch("/api/erp/endpoints/{endpoint_id}")
async def erp_endpoints_update(endpoint_id: str, req: ErpEndpointUpdate, request: Request):
    """P-3 (Zihao 2026-05-19 拍板 · v118.34.21) · PATCH 路由现在镜像 POST
    路由的 Fernet 加密逻辑:wizard 编辑已有 endpoint 重新输入密码时,JS 把
    新密码塞进 username_enc/password_enc 字段名(假签名)· 这条路径之前不
    走加密 → DB 落明文 → test-connection 解密 InvalidToken → ERR_CRED_DECRYPT.

    现在:如果目标 endpoint adapter=='mrerp' 且 PATCH config 携带
    username_enc/password_enc · 用 kms_helper.is_encrypted 判断是不是真
    ciphertext;明文就 encrypt_str 转一次再 update。已是 ciphertext
    (gAAAAA*)的不动 · 防止 double-encrypt。"""
    user = get_current_user_from_request(request)
    _check_push_access(user)
    # 如果 config 里 token 是 "***" 占位符,说明用户没改 token,要保留旧值
    fields = {k: v for k, v in req.dict(exclude_unset=True).items() if v is not None}

    # 先查目标 endpoint 的 adapter · PATCH 不带 adapter · 必须从已有数据看
    existing_ep = db.get_erp_endpoint(user["id"], endpoint_id)
    target_adapter = (existing_ep.get("adapter") or "").strip().lower() if existing_ep else ""

    if "config" in fields:
        new_cfg = dict(fields["config"] or {})
        token = str(new_cfg.get("token", ""))
        if token and ("***" in token or token == ""):
            if existing_ep:
                old_token = (existing_ep.get("config") or {}).get("token", "")
                if old_token:
                    new_cfg["token"] = old_token
        # 清掉前端塞的标记字段
        new_cfg.pop("_token_set", None)
        new_cfg.pop("_username_enc_set", None)
        new_cfg.pop("_password_enc_set", None)

        # Bug 1 (v118.34.22) · 镜像 POST 的 client_ids 验证 · PATCH 改 client_ids
        # 为空也得拦下 · 否则用户误删可能 silent regression 全推送失败.
        if target_adapter == "mrerp" and "client_ids" in new_cfg:
            cids = new_cfg.get("client_ids") or []
            if not isinstance(cids, list) or not cids:
                raise HTTPException(
                    400,
                    detail={
                        "code": "erp.endpoint_no_clients",
                        "message_zh": "这个 ERP 连接不能没有 Pearnly 客户 · 至少留 1 个",
                        "message_en": "ERP connection must have at least one Pearnly client",
                    },
                )

        # P-3 · MR.ERP 加密镜像 POST 路由 (v118.34.13 一致)
        if target_adapter == "mrerp":
            try:
                from kms_helper import encrypt_str, is_encrypted
                for fld in ("username_enc", "password_enc"):
                    v = new_cfg.get(fld)
                    if v and isinstance(v, str) and not is_encrypted(v):
                        new_cfg[fld] = encrypt_str(v)
            except ImportError as e:
                _record_500(
                    path=f"/api/erp/endpoints/{endpoint_id}", method="PATCH",
                    detail=f"kms_helper unavailable: {e}",
                )
                raise HTTPException(
                    500,
                    detail="erp.kms_key_missing · server KMS_KEY env not set",
                )
            except Exception as e:
                _record_500(
                    path=f"/api/erp/endpoints/{endpoint_id}", method="PATCH",
                    detail=f"encrypt failed: {type(e).__name__}: {e}",
                )
                raise HTTPException(
                    500, detail=f"erp.encrypt_failed: {type(e).__name__}",
                )

        fields["config"] = new_cfg

    # v0.8 · auto_push 权限
    if fields.get("auto_push"):
        p = _plan_permissions(user.get("plan", "free"))
        if not p.get("can_auto_push_erp"):
            raise HTTPException(403, detail="erp.auto_push_plus_required")

    ok = db.update_erp_endpoint(user["id"], endpoint_id, **fields)
    if not ok:
        raise HTTPException(404, detail="erp.endpoint_not_found")
    ep = db.get_erp_endpoint(user["id"], endpoint_id)
    return _strip_endpoint_for_response(ep) if ep else {"ok": True}


@app.delete("/api/erp/endpoints/{endpoint_id}")
async def erp_endpoints_delete(endpoint_id: str, request: Request):
    user = get_current_user_from_request(request)
    _check_push_access(user)
    ok = db.delete_erp_endpoint(user["id"], endpoint_id)
    if not ok:
        raise HTTPException(404, detail="erp.endpoint_not_found")
    return {"ok": True}


@app.post("/api/erp/test-connection")
async def erp_test_connection(req: ErpTestConnectionRequest, request: Request):
    """前端「测试连接」按钮 · 不写日志、不改任何状态

    v118.34.1 (Zihao 2026-05-19 拍板) · mrerp 必须直接走 MRERPAdapter.login
    + select_company,不能掉进 ADAPTER_REGISTRY → push_mrerp stub。
    v118.34.2 (2026-05-19) · 加路由级 try/except 兜底 + 接受 wizard 发的
    plaintext `{username, password}`(以前只接受 `{username_enc,
    password_enc}` 容易碰到的 ImportError 上浮成 500)。"""
    user = get_current_user_from_request(request)
    _check_push_access(user)
    if req.adapter not in _erp.ADAPTER_REGISTRY:
        raise HTTPException(400, detail="erp.unknown_adapter")
    cfg = dict(req.config or {})
    cfg.pop("_token_set", None)

    # mrerp: real login + company-picker scrape (rich shape with
    # ok / companies / error_friendly). Wizard JS already understands
    # this shape. test_mrerp_endpoint is contracted to NEVER raise but
    # the route still wraps the call so a bug in the helper can't
    # surface as a 500 to the UI — we'd rather render a friendly bar.
    #
    # v118.34.10 (Zihao 2026-05-19 拍板) · MUST use asyncio.to_thread:
    # MRERPAdapter uses Playwright's sync_api which explicitly refuses
    # to start when there's a running asyncio loop. FastAPI handlers
    # ARE the running loop, so a direct call raises
    # "Playwright Sync API inside the asyncio loop". to_thread offloads
    # to a worker thread (no running loop there), letting Playwright
    # initialise cleanly. Same applies to every other route in this
    # file that touches MRERPAdapter.
    import asyncio as _asyncio
    if req.adapter == "mrerp":
        try:
            return await _asyncio.to_thread(_erp.test_mrerp_endpoint, cfg)
        except Exception as e:
            logger.exception("erp_test_connection mrerp helper raised")
            return {
                "ok": False,
                "elapsed_ms": 0,
                "companies": [],
                "error_code": "ERR_UNEXPECTED",
                "error_friendly": {
                    "zh": f"服务器内部错误:{type(e).__name__}",
                    "en": f"Internal server error: {type(e).__name__}",
                    "th": f"ข้อผิดพลาดของเซิร์ฟเวอร์: {type(e).__name__}",
                    "zh_TW": f"伺服器內部錯誤:{type(e).__name__}",
                },
                "raw_error": f"{type(e).__name__}: {str(e)[:300]}",
            }

    # Other adapters: legacy ping. Keep the historical shape so
    # webhook / flowaccount UIs aren't broken. push_webhook uses
    # `requests.post` which is also sync I/O — to_thread either way.
    return await _asyncio.to_thread(_erp.test_endpoint_connection, req.adapter, cfg)


# C-1 (Zihao 2026-05-18 拍板) · 60-second TTL cache for per-endpoint
# health checks. Drives MRERPAdapter.login + select_company at most
# once per 60s per (user_id, endpoint_id); the wizard / cards UI hits
# this aggressively, so the cache keeps MR.ERP traffic sane.
from services.erp._master_data_cache import TTLCache as _EndpointTestCache  # noqa: E402
_endpoint_test_cache = _EndpointTestCache(max_size=512, ttl_seconds=60.0)
# 问题 2 (Zihao 2026-05-19 拍板 · v118.34.24) · 客户/商品 listing 缓存 TTL
# 60s → 600s (10 分钟). 同一 tenant 10 分钟内 listing 基本不变 · 频繁拉
# 是性能杀手 + MR.ERP 压力源. wizard 重新打开会刷一次 (refresh=1)
# 也能用 refresh=1 query param 强制 bypass.
# Task 1 (Zihao 2026-05-18 拍板) — separate cache for the customers /
# products dropdown listings used by the wizard's Step 3.
_endpoint_customers_cache = _EndpointTestCache(max_size=512, ttl_seconds=600.0)
# Task 2 Phase 5 (Zihao 2026-05-18 拍板) — same TTL for product listing.
_endpoint_products_cache = _EndpointTestCache(max_size=512, ttl_seconds=600.0)


@app.post("/api/erp/endpoints/{endpoint_id}/test-connection")
async def erp_endpoint_test_connection(
    endpoint_id: str,
    request: Request,
    refresh: bool = False,
):
    """Per-endpoint health check. Loads the stored endpoint (with its
    Fernet-encrypted credentials), runs adapter-specific verification
    (MR.ERP: login + select_company + scrape companies dropdown), and
    returns a structured result the wizard / cards UI can render.

    Caches by (user_id, endpoint_id) for 60s. Pass `?refresh=1` to
    bypass the cache (used by the explicit "重新测试" button).

    Returns 200 with `{ok: bool, ...}` either way — the UI uses `ok`
    to decide the pill colour. Auth / not-found responses still HTTP
    error normally so the UI can show a generic toast.
    """
    user = get_current_user_from_request(request)
    _check_push_access(user)
    ep = db.get_erp_endpoint(user["id"], endpoint_id)
    if not ep:
        raise HTTPException(404, detail="erp.endpoint_not_found")

    cache_key = (str(user["id"]), str(endpoint_id))
    if not refresh:
        cached = _endpoint_test_cache.get(cache_key)
        if cached is not None:
            return {**cached, "cached": True}

    adapter = (ep.get("adapter") or "").strip().lower()
    config = ep.get("config") or {}
    # v118.34.2 (2026-05-19) · try/except wrapper mirrors the legacy
    # route so even a bug in test_mrerp_endpoint can't surface as a 500.
    # v118.34.10 · asyncio.to_thread keeps Playwright's sync API off
    # the FastAPI event loop (refuses to start otherwise).
    import asyncio as _asyncio
    try:
        if adapter == "mrerp":
            result = await _asyncio.to_thread(_erp.test_mrerp_endpoint, config)
        else:
            # webhook / flowaccount / etc — defer to the existing ping test.
            legacy = await _asyncio.to_thread(_erp.test_endpoint_connection, adapter, config)
            result = {
                "ok": bool(legacy.get("success")),
                "elapsed_ms": legacy.get("elapsed_ms", 0),
                "http_status": legacy.get("http_status"),
                "raw_error": legacy.get("error_msg"),
                "companies": [],
                "error_code": None if legacy.get("success") else "ERR_TECHNICAL",
                "error_friendly": None,
            }
    except Exception as e:
        logger.exception("erp_endpoint_test_connection helper raised")
        result = {
            "ok": False,
            "elapsed_ms": 0,
            "companies": [],
            "error_code": "ERR_UNEXPECTED",
            "error_friendly": {
                "zh": f"服务器内部错误:{type(e).__name__}",
                "en": f"Internal server error: {type(e).__name__}",
                "th": f"ข้อผิดพลาดของเซิร์ฟเวอร์: {type(e).__name__}",
                "zh_TW": f"伺服器內部錯誤:{type(e).__name__}",
            },
            "raw_error": f"{type(e).__name__}: {str(e)[:300]}",
        }

    from datetime import datetime as _dt
    result["last_tested_at"] = _dt.utcnow().isoformat() + "Z"
    result["cached"] = False
    _endpoint_test_cache.set(cache_key, result)
    return result


async def _fetch_listing_with_retry(
    fetch_fn,
    config: dict,
    *,
    listing_kind: str,
    max_attempts: int = 2,
    delay_seconds: float = 2.0,
) -> dict:
    """A3 (Zihao 2026-05-19 拍板) · transient-aware retry wrapper for
    /endpoints/:id/customers and /endpoints/:id/products.

    Retries up to `max_attempts` times with `delay_seconds` between
    attempts when the underlying fetch reports a transient error
    (ERR_TECHNICAL / ERR_UNEXPECTED / network exception from
    asyncio.to_thread). Non-transient errors (ERR_AUTH /
    ERR_CRED_DECRYPT / ERR_BUSINESS / ERR_NO_CREDS) break out of the
    loop immediately — those don't get better by retrying.

    Always returns a dict matching the underlying fetch's response
    shape; never raises.
    """
    import asyncio as _asyncio
    transient_codes = {"ERR_TECHNICAL", "ERR_UNEXPECTED", "ERR_NETWORK"}
    result: dict = {}
    for attempt in range(1, max_attempts + 1):
        if attempt > 1:
            await _asyncio.sleep(delay_seconds)
            logger.info(
                "[listing-retry] %s attempt %d/%d after %.1fs delay",
                listing_kind, attempt, max_attempts, delay_seconds,
            )
        try:
            result = await _asyncio.to_thread(fetch_fn, config)
        except Exception as e:
            logger.exception(
                "[listing-retry] %s attempt %d raised", listing_kind, attempt,
            )
            result = {
                "ok": False,
                listing_kind: [],
                "error_code": "ERR_UNEXPECTED",
                "error_friendly": {
                    "zh": f"服务器内部错误:{type(e).__name__}",
                    "en": f"Internal server error: {type(e).__name__}",
                    "th": f"ข้อผิดพลาดของเซิร์ฟเวอร์: {type(e).__name__}",
                    "zh_TW": f"伺服器內部錯誤:{type(e).__name__}",
                },
                "raw_error": f"{type(e).__name__}: {str(e)[:300]}",
            }
        # Bug 2 (Zihao 2026-05-19 拍板 · v118.34.22) · 每次结果都打可观察 log ·
        # 包含失败截图路径(如果有). 让 journalctl/api/version 一眼看到 retry
        # 链路: 第几次 / 是否成功 / 截图 / 错误码.
        ok_flag = result.get("ok")
        code = result.get("error_code")
        raw = str(result.get("raw_error") or "")
        import re as _re
        shot_match = _re.search(r"screenshot=(\S+\.png)", raw, _re.IGNORECASE)
        shot_path = shot_match.group(1) if shot_match else None
        logger.info(
            "[listing-retry] %s attempt %d → ok=%s code=%s screenshot=%s",
            listing_kind, attempt, ok_flag, code, shot_path or "-",
        )
        if ok_flag:
            return result
        # Non-transient: bail out · the retry won't help.
        if code not in transient_codes:
            logger.info(
                "[listing-retry] %s attempt %d code=%s non-transient · bail out",
                listing_kind, attempt, code,
            )
            return result
        # Transient: loop will retry (unless we just exhausted attempts).
    # All retries exhausted; surface the last result.
    return result


@app.get("/api/erp/endpoints/{endpoint_id}/customers")
async def erp_endpoint_customers(
    endpoint_id: str,
    request: Request,
    refresh: bool = False,
):
    """Task 1 (Zihao 2026-05-18 拍板) · Fetch the MR.ERP customer
    listing for an endpoint so the wizard's Step-3 seed dropdown can
    show real options.

    Returns 200 with `{ok, customers: [{code, name, type_name, prefix}]}`
    or `{ok: false, error_code, error_friendly, raw_error}` on
    auth/network failure so the UI can degrade gracefully (fall back
    to a free-text input).

    Cached 60s per (user_id, endpoint_id). Pass `?refresh=1` to force.
    Only available for `adapter='mrerp'` endpoints.
    """
    user = get_current_user_from_request(request)
    _check_push_access(user)
    ep = db.get_erp_endpoint(user["id"], endpoint_id)
    if not ep:
        raise HTTPException(404, detail="erp.endpoint_not_found")

    adapter = (ep.get("adapter") or "").strip().lower()
    if adapter != "mrerp":
        # Other adapters don't have a sensible customer-listing
        # equivalent; surface 200 with empty list so the wizard can
        # render gracefully.
        return {
            "ok": False, "customers": [],
            "error_code": "ERR_ADAPTER_NO_CUSTOMERS",
            "error_friendly": {
                "zh": "此适配器没有客户列表接口",
                "en": "This adapter does not expose a customer listing",
                "th": "อะแดปเตอร์นี้ไม่มี API รายชื่อลูกค้า",
                "zh_TW": "此適配器沒有客戶列表介面",
            },
            "elapsed_ms": 0,
        }

    cache_key = (str(user["id"]), str(endpoint_id), "customers")
    if not refresh:
        cached = _endpoint_customers_cache.get(cache_key)
        if cached is not None:
            return {**cached, "cached": True}

    # A3 (Zihao 2026-05-19 拍板) · route-level retry + don't-cache-failures
    # for transient listing flakes.
    # Layered with the _fetch_listing's own wait_for_selector + reload
    # (handles slow renders) and gives one full retry cycle if a whole
    # nav round-trip times out (e.g. mid-deploy MR.ERP 5xx).
    result = await _fetch_listing_with_retry(
        _erp.list_mrerp_customers,
        ep.get("config") or {},
        listing_kind="customers",
    )
    from datetime import datetime as _dt
    result["last_fetched_at"] = _dt.utcnow().isoformat() + "Z"
    result["cached"] = False
    # Only cache success — sticky failure was the user-reported "first
    # click works, second click says '无法拉取客户列表'" bug.
    if result.get("ok"):
        _endpoint_customers_cache.set(cache_key, result)
    return result


@app.get("/api/erp/endpoints/{endpoint_id}/products")
async def erp_endpoint_products(
    endpoint_id: str,
    request: Request,
    refresh: bool = False,
):
    """Task 2 Phase 5 (Zihao 2026-05-18 拍板) · Fetch the MR.ERP
    product listing for an endpoint so the wizard's Step-3 seed-product
    dropdown can show real options. Mirrors the customers route + cache."""
    user = get_current_user_from_request(request)
    _check_push_access(user)
    ep = db.get_erp_endpoint(user["id"], endpoint_id)
    if not ep:
        raise HTTPException(404, detail="erp.endpoint_not_found")

    adapter = (ep.get("adapter") or "").strip().lower()
    if adapter != "mrerp":
        return {
            "ok": False, "products": [],
            "error_code": "ERR_ADAPTER_NO_PRODUCTS",
            "error_friendly": {
                "zh": "此适配器没有商品列表接口",
                "en": "This adapter does not expose a product listing",
                "th": "อะแดปเตอร์นี้ไม่มี API รายการสินค้า",
                "zh_TW": "此適配器沒有商品列表介面",
            },
            "elapsed_ms": 0,
        }

    cache_key = (str(user["id"]), str(endpoint_id), "products")
    if not refresh:
        cached = _endpoint_products_cache.get(cache_key)
        if cached is not None:
            return {**cached, "cached": True}

    # A3 (Zihao 2026-05-19 拍板) · route-level retry + don't-cache-failures
    # · mirror of customer listing route.
    result = await _fetch_listing_with_retry(
        _erp.list_mrerp_products,
        ep.get("config") or {},
        listing_kind="products",
    )
    from datetime import datetime as _dt
    result["last_fetched_at"] = _dt.utcnow().isoformat() + "Z"
    result["cached"] = False
    if result.get("ok"):
        _endpoint_products_cache.set(cache_key, result)
    return result


class ErpPushRequest(BaseModel):
    history_id: str
    endpoint_id: Optional[str] = Field(None, description="不传则用默认端点")


@app.post("/api/erp/push")
async def erp_push(req: ErpPushRequest, request: Request):
    """手动触发推送一条历史记录到指定 endpoint"""
    user = get_current_user_from_request(request)
    _check_push_access(user)

    # 1) 拿历史记录
    history = db.get_ocr_history_detail(user["id"], req.history_id, tenant_id=_tid(user))
    if not history:
        raise HTTPException(404, detail="erp.history_not_found")

    # 2) 选 endpoint
    if req.endpoint_id:
        endpoint = db.get_erp_endpoint(user["id"], req.endpoint_id)
        if not endpoint:
            raise HTTPException(404, detail="erp.endpoint_not_found")
    else:
        endpoint = db.get_default_erp_endpoint(user["id"])
        if not endpoint:
            raise HTTPException(400, detail="erp.no_default_endpoint")

    if not endpoint.get("enabled", True):
        raise HTTPException(400, detail="erp.endpoint_disabled")

    # 批 2 改动 2 (Zihao 2026-05-19 拍板 · v118.34.34) · 推送去重 check.
    # 同 history × endpoint 已经 success 过 → 写 skipped_dup log + 静默
    # 返回原成功的 bill_no. 防同张发票被自动 + 手动 + 重试反复推到 MR.ERP.
    existing = db.has_recent_successful_push(
        req.history_id, endpoint["id"], user["id"],
    )
    if existing:
        log_id = db.insert_push_log(
            user_id=user["id"],
            endpoint_id=endpoint["id"],
            history_id=req.history_id,
            invoice_no=history.get("invoice_no"),
            seller_name=history.get("seller_name"),
            total_amount=history.get("total_amount"),
            status="skipped_dup",
            http_status=200,
            request_body={"adapter": endpoint.get("adapter"),
                          "skipped_reason": "already_success",
                          "prior_log_id": str(existing.get("id"))},
            response_body=existing.get("response_body"),
            error_msg=None,
            attempt=1,
            elapsed_ms=0,
            trigger="manual",
        )
        logger.info(
            "[push-dedup] skipped manual push · history=%s endpoint=%s "
            "(prior log=%s)",
            req.history_id[:8], endpoint["id"][:8],
            str(existing.get("id"))[:8],
        )
        return {
            "ok": True,
            "log_id": log_id,
            "http_status": 200,
            "skipped_dup": True,
            "prior_log_id": str(existing.get("id")),
            "endpoint_name": endpoint.get("name"),
        }

    # 3) 推送 · v118.34.10 · asyncio.to_thread keeps push_to_endpoint
    # (which may call Playwright via push_mrerp once C-1 wires it,
    # plus uses sync `requests` for webhook adapters) off the event loop.
    import asyncio as _asyncio
    result = await _asyncio.to_thread(_erp.push_to_endpoint, endpoint, history)

    # 4) 写日志
    log_id = db.insert_push_log(
        user_id=user["id"],
        endpoint_id=endpoint["id"],
        history_id=req.history_id,
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
    )

    # 5) 更新 endpoint 统计 + history 推送状态
    db.update_endpoint_stats(endpoint["id"], result["success"])
    db.update_history_push_status(req.history_id,
                                  "success" if result["success"] else "failed")

    # v118.25 · 手动推送失败 · 也进重试队列(给用户"扔出去就不管"的体验)
    # 批 1 改动 3 (v118.34.33) · 用户数据错(ERR_NO_CLIENT 等)不入重试 ·
    # retry 没意义 + 污染队列.
    if not result["success"] and log_id:
        if db.is_user_data_error(result.get("error_msg")):
            logger.info(
                "[push] user-data error · NOT scheduling retry · log=%s err=%r",
                str(log_id)[:8], (result.get("error_msg") or "")[:80],
            )
        else:
            first_delay = db.get_erp_retry_delay_sec(0)
            if first_delay is not None:
                db.schedule_log_retry(str(log_id), first_delay)

    return {
        "ok": result["success"],
        "log_id": log_id,
        "http_status": result.get("http_status"),
        "error_msg": result.get("error_msg"),
        "elapsed_ms": result.get("elapsed_ms"),
        "endpoint_name": endpoint.get("name"),
    }


# ============================================================
# v0.9 · 自动推送(识别完成后后台异步触发)
# ============================================================
async def _auto_push_history(user_id: str, history_id: str, endpoints: List[Dict[str, Any]], tenant_id: Optional[str] = None):
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
                history_id, ep["id"], user_id,
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
                    request_body={"adapter": ep.get("adapter"),
                                  "skipped_reason": "already_success",
                                  "prior_log_id": str(existing.get("id"))},
                    response_body=existing.get("response_body"),
                    error_msg=None,
                    attempt=1,
                    elapsed_ms=0,
                    trigger="auto",
                )
                logger.info(
                    "[AutoPush-dedup] skipped · history=%s endpoint=%s "
                    "(prior=%s)",
                    history_id[:8], ep["id"][:8],
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
                trigger="auto",   # 标记自动触发
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
                        "[AutoPush] user-data error · NOT scheduling retry · "
                        "log=%s err=%r", str(new_log_id)[:8],
                        (result.get("error_msg") or "")[:80],
                    )
                else:
                    first_delay = db.get_erp_retry_delay_sec(0)
                    if first_delay is not None:
                        db.schedule_log_retry(str(new_log_id), first_delay)
                        logger.info(f"[AutoPush] 失败入重试队列 · log={new_log_id} · {first_delay}s 后第 1 次重试")

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
        for m in (mappings.get("clients") or []):
            if m.get("erp_type") == "xero" and int(m.get("client_id") or 0) == int(cid):
                contact_name = (m.get("erp_code") or "").strip()
                break
        if not contact_name:
            try:
                db.insert_push_log(
                    user_id=user_id, endpoint_id=None, history_id=history_id,
                    invoice_no=history.get("invoice_no"),
                    seller_name=history.get("seller_name"),
                    total_amount=history.get("total_amount"),
                    status="failed", http_status=400,
                    request_body={"adapter": "xero_auto", "stage": "mapping"},
                    response_body=None, error_msg="no_client_mapping",
                    attempt=1, elapsed_ms=int((time.time() - t0) * 1000),
                    trigger="auto",
                )
            except Exception as e:
                logger.warning(f"[xero_auto] 写 push_log(no_mapping)失败: {e}")
            return
        # 拿 token + push
        try:
            access_token, xero_org_id = _ensure_fresh_xero_token(tenant_id)
            from xero_pusher import (
                find_contact_by_name, build_invoice_payload,
                push_invoice, parse_xero_error,
            )
            contact = find_contact_by_name(access_token, xero_org_id, contact_name)
            if not contact:
                raise RuntimeError("contact_not_found")
            payload = build_invoice_payload(history, contact)
            result = push_invoice(access_token, xero_org_id, payload)
            ok = bool(result.get("success"))
            db.insert_push_log(
                user_id=user_id, endpoint_id=None, history_id=history_id,
                invoice_no=history.get("invoice_no"),
                seller_name=history.get("seller_name"),
                total_amount=history.get("total_amount"),
                status="success" if ok else "failed",
                http_status=result.get("http_status"),
                request_body={"adapter": "xero_auto"},
                response_body=str(result.get("invoice_id") or "")[:500],
                error_msg=(None if ok else str(result.get("error") or "")[:500]),
                attempt=1, elapsed_ms=int((time.time() - t0) * 1000),
                trigger="auto",
            )
            if ok:
                logger.info(f"[AutoPushXero] ok history={history_id[:8]} contact={contact_name}")
        except Exception as e:
            logger.warning(f"[AutoPushXero] failed history={history_id[:8]}: {e}")
            try:
                db.insert_push_log(
                    user_id=user_id, endpoint_id=None, history_id=history_id,
                    invoice_no=history.get("invoice_no"),
                    seller_name=history.get("seller_name"),
                    total_amount=history.get("total_amount"),
                    status="failed", http_status=500,
                    request_body={"adapter": "xero_auto"},
                    response_body=None, error_msg=str(e)[:500],
                    attempt=1, elapsed_ms=int((time.time() - t0) * 1000),
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


@app.get("/api/erp/logs/{log_id}/debug-xlsx")
async def erp_log_debug_xlsx(log_id: str, request: Request):
    """v27.8.1.5 · 推送失败时下载 Pearnly 这次生成的 xlsx · 用户拖给 ERP 服务方诊断
    只有同 tenant 用户能下 · 没存 _debug_xlsx_b64 → 404"""
    user = get_current_user_from_request(request)
    tid = _tid(user)
    try:
        with db.get_cursor() as cur:
            cur.execute("""
                SELECT pl.id, pl.user_id, pl.history_id, pl.request_body, pl.invoice_no,
                       u.tenant_id::text AS tid
                FROM push_logs pl
                LEFT JOIN users u ON u.id = pl.user_id
                WHERE pl.id = %s LIMIT 1
            """, (log_id,))
            row = cur.fetchone()
    except Exception as e:
        raise HTTPException(500, detail=f"db.error:{e}")
    if not row:
        raise HTTPException(404, detail="log.not_found")
    # 同 tenant 才能下
    if str(row.get("tid") or "") != str(tid or ""):
        raise HTTPException(403, detail="log.cross_tenant")
    rb = row.get("request_body") or {}
    if isinstance(rb, str):
        try:
            import json as _json
            rb = _json.loads(rb)
        except Exception:
            rb = {}
    b64 = rb.get("_debug_xlsx_b64") if isinstance(rb, dict) else None
    if not b64:
        raise HTTPException(404, detail="log.no_debug_xlsx")
    import base64 as _b64
    try:
        xlsx_bytes = _b64.b64decode(b64)
    except Exception:
        raise HTTPException(500, detail="log.decode_failed")
    from fastapi.responses import Response as _Resp
    safe_inv = (row.get("invoice_no") or "unknown").replace("/", "_").replace(" ", "_")[:40]
    fname = f"pearnly_debug_{safe_inv}_{log_id[:8]}.xlsx"
    return _Resp(
        content=xlsx_bytes,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{fname}"'},
    )


@app.get("/api/erp/history/{history_id}/push_status")
async def erp_history_push_status(history_id: str, request: Request):
    """P0-2 · 查询某张发票是否已成功推送到 ERP"""
    user = get_current_user_from_request(request)
    _check_push_access(user)
    result = db.list_push_logs(user["id"], history_id=history_id, status_filter="success", limit=1)
    items = result.get("items", [])
    if items:
        item = items[0]
        return {"pushed": True, "pushed_at": str(item["created_at"]), "push_log_id": str(item["id"])}
    return {"pushed": False, "pushed_at": None, "push_log_id": None}


@app.get("/api/erp/logs")
async def erp_logs(request: Request,
                   history_id: Optional[str] = None,
                   endpoint_id: Optional[str] = None,
                   status: Optional[str] = None,
                   trigger: Optional[str] = None,
                   adapter: Optional[str] = None,
                   limit: int = 50, offset: int = 0):
    """批 3 改动 6 (v118.34.34) · 新增 adapter 参数 · 让前端按 ERP 类型筛日志."""
    user = get_current_user_from_request(request)
    _check_push_access(user)
    return db.list_push_logs(
        user["id"], history_id=history_id, endpoint_id=endpoint_id,
        status_filter=status, trigger_filter=trigger,
        adapter_filter=adapter,
        limit=min(limit, 200), offset=max(0, offset),
    )


@app.get("/api/erp/logs/{log_id}")
async def erp_log_detail(log_id: str, request: Request):
    """单条日志完整详情 · 含请求体/响应体"""
    user = get_current_user_from_request(request)
    _check_push_access(user)
    detail = db.get_push_log_detail(user["id"], log_id)
    if not detail:
        raise HTTPException(404, detail="log.not_found")
    return detail


@app.get("/api/erp/stats/today")
async def erp_stats_today(request: Request):
    """今日推送统计"""
    user = get_current_user_from_request(request)
    _check_push_access(user)
    return db.get_push_stats_today(user["id"])


# ============================================================
# v0.17 · M6 · 邮箱抓取
# ============================================================
class EmailAccountBindRequest(BaseModel):
    email_address: str = Field(..., min_length=3, max_length=200)
    imap_host: str = Field(..., min_length=3, max_length=200)
    imap_port: int = Field(993, ge=1, le=65535)
    imap_use_ssl: bool = True
    password: Optional[str] = None         # 不传 = 只改配置 · 不改密码
    folder: str = Field("INBOX", max_length=100)
    filter_subject: Optional[str] = Field(None, max_length=200)
    filter_sender: Optional[str] = Field(None, max_length=500)
    mark_as_read: bool = True
    enabled: bool = True
    interval_min: int = Field(15)          # v0.17.9 · 仅 5/15/60 三档 · db 层兜底


class EmailTestConnRequest(BaseModel):
    email_address: str = Field(..., min_length=3, max_length=200)
    imap_host: str = Field(..., min_length=3, max_length=200)
    imap_port: int = Field(993, ge=1, le=65535)
    imap_use_ssl: bool = True
    password: str = Field(..., min_length=1, max_length=500)
    folder: str = Field("INBOX", max_length=100)


@app.get("/api/email-ingest/account")
async def email_account_get(request: Request):
    """获取当前用户的邮箱绑定(不返回密码)"""
    user = get_current_user_from_request(request)
    info = db.get_email_account_safe(user["id"])
    return {"account": info, "presets": _email_presets()}


@app.put("/api/email-ingest/account")
async def email_account_bind(req: EmailAccountBindRequest, request: Request):
    """创建或更新邮箱绑定"""
    user = get_current_user_from_request(request)
    import email_ingest
    if not email_ingest.is_available():
        raise HTTPException(503, detail="email.encryption_not_configured")

    password_enc = None
    if req.password:
        password_enc = email_ingest.encrypt_password(req.password)

    account_id = db.upsert_email_account(
        user_id=str(user["id"]),
        email_address=req.email_address.strip(),
        imap_host=req.imap_host.strip(),
        imap_port=req.imap_port,
        imap_use_ssl=req.imap_use_ssl,
        password_enc=password_enc,
        folder=req.folder.strip() or "INBOX",
        filter_subject=(req.filter_subject or "").strip() or None,
        filter_sender=(req.filter_sender or "").strip() or None,
        mark_as_read=req.mark_as_read,
        enabled=req.enabled,
        interval_min=req.interval_min,
    )
    if not account_id:
        raise HTTPException(500, detail="email.save_failed")
    info = db.get_email_account_safe(user["id"])
    return {"ok": True, "account": info}


@app.delete("/api/email-ingest/account")
async def email_account_unbind(request: Request):
    """解绑邮箱(同时删所有相关日志和 UID 记录 · 级联删除)"""
    user = get_current_user_from_request(request)
    ok = db.delete_email_account(user["id"])
    return {"ok": ok}


@app.post("/api/email-ingest/test")
async def email_account_test(req: EmailTestConnRequest, request: Request):
    """测试邮箱连接(只登录 · 不保存)"""
    user = get_current_user_from_request(request)  # 仅用于鉴权
    import email_ingest
    import asyncio
    # IMAP 是阻塞 IO · 扔线程池
    result = await asyncio.to_thread(
        email_ingest.test_connection,
        req.email_address.strip(),
        req.password,
        req.imap_host.strip(),
        req.imap_port,
        req.imap_use_ssl,
        req.folder.strip() or "INBOX",
    )
    return result


@app.post("/api/email-ingest/trigger")
async def email_account_trigger(request: Request):
    """手动触发一次抓取 · 同步等结果(最长 30 秒)"""
    user = get_current_user_from_request(request)
    account = db.get_email_account(user["id"])
    if not account:
        raise HTTPException(404, detail="email.no_account")
    if not account.get("enabled"):
        raise HTTPException(400, detail="email.disabled")

    import email_ingest
    import asyncio
    if not email_ingest.is_available():
        raise HTTPException(503, detail="email.encryption_not_configured")
    try:
        result = await asyncio.wait_for(
            asyncio.to_thread(email_ingest.run_account_ingest, account, "manual"),
            timeout=60.0,
        )
    except asyncio.TimeoutError:
        raise HTTPException(504, detail="email.timeout")

    # 写日志 + 更新账号状态
    db.insert_email_ingest_log(
        account_id=account["id"],
        user_id=str(user["id"]),
        stats=result,
        trigger="manual",
    )
    db.update_email_account_status(
        account["id"],
        success=result["status"] in ("success", "partial"),
        error_msg=result.get("error_message"),
        fetched_any=result.get("attachments_found", 0) > 0,
    )
    return result


@app.get("/api/email-ingest/logs")
async def email_ingest_logs(request: Request, limit: int = 20):
    """最近抓取日志"""
    user = get_current_user_from_request(request)
    limit = max(1, min(int(limit), 100))
    return db.list_email_ingest_logs(user["id"], limit)


def _email_presets():
    """返回常用邮箱预设 · 不暴露任何敏感信息"""
    try:
        import email_ingest
        return email_ingest.IMAP_PRESETS
    except Exception:
        return {}


# ============================================================
# v0.18 · M10 · 银行对账 API
# ============================================================

@app.post("/api/bank-recon/upload")
async def bank_recon_upload(request: Request, file: UploadFile = File(...)):
    """
    上传银行对账单 PDF · 同步解析 · 返回 session_id
    - 不做匹配(用户下一步手动触发,方便分步)
    - 失败返回 4xx 明确错误码
    """
    user = get_current_user_from_request(request)
    filename = file.filename or "statement.pdf"
    # 2026-05-21 multi-format refactor: bank statement upload supports
    # PDF / image / Excel / CSV / Word. PDF goes through bank_recon_v2's
    # existing parser; tabular formats go through the unified pipeline
    # with document_type=bank_statement.
    from services.ocr.pipeline import (
        PDF_EXTENSIONS, IMAGE_EXTENSIONS, TABLE_EXTENSIONS,
    )
    _bank_all_exts = PDF_EXTENSIONS | IMAGE_EXTENSIONS | TABLE_EXTENSIONS
    _bank_fname_l = filename.lower()
    _bank_ext = "." + _bank_fname_l.rsplit(".", 1)[-1] if "." in _bank_fname_l else ""
    if _bank_ext not in _bank_all_exts:
        raise HTTPException(400, detail="bank_recon.unsupported_format")

    pdf_bytes = await file.read()
    if not pdf_bytes or len(pdf_bytes) < 50:
        raise HTTPException(400, detail="bank_recon.empty_file")
    if len(pdf_bytes) > 20 * 1024 * 1024:
        raise HTTPException(413, detail="bank_recon.file_too_large")

    import bank_recon_v2 as br
    import asyncio

    try:
        if _bank_ext in PDF_EXTENSIONS:
            # Existing flow: pdfplumber → Gemini fallback (handles scan + text PDFs)
            parsed = await asyncio.to_thread(br.parse_statement_pdf, pdf_bytes, filename)
        else:
            # New flow: route through unified pipeline with explicit document_type
            # so Excel/CSV/Word bank statements bypass OCR and the GL/Bank
            # validators reject mis-sourced amounts (e.g. 6091).
            from services.ocr.pipeline import (
                run_on_image_bytes as _bank_run_image,
                run_on_table_bytes as _bank_run_table,
            )
            from services.ocr.legacy_adapter import pipeline_result_to_legacy_dict
            if _bank_ext in IMAGE_EXTENSIONS:
                _pipe_res = await asyncio.to_thread(
                    _bank_run_image, pdf_bytes, document_type="bank_statement"
                )
            else:  # TABLE_EXTENSIONS
                _pipe_res = await asyncio.to_thread(
                    _bank_run_table, pdf_bytes, filename, None, None, "bank_statement"
                )
            _legacy = pipeline_result_to_legacy_dict(_pipe_res)
            parsed = br.parsed_from_pipeline_legacy(_legacy, filename)
    except Exception as e:
        logger.exception("[bank_recon] 解析异常")
        raise HTTPException(500, detail=f"bank_recon.parse_exception:{str(e)[:100]}")

    session_id = db.create_bank_recon_session(
        user_id=str(user["id"]),
        bank_code=parsed.bank_code,
        filename=filename,
        pages=parsed.pages,
    )
    if not session_id:
        raise HTTPException(500, detail="bank_recon.create_session_failed")

    if parsed.parse_method == "gemini_vision_pending":
        # 轮 2 未接通 vision · 标记 "scanned not supported yet"
        db.mark_recon_parse_failed(session_id,
            "扫描件暂未支持 · 请上传带文字层的 PDF")
        return {
            "session_id": session_id,
            "bank_code":  parsed.bank_code,
            "parse_status": "parse_failed",
            "tx_count":   0,
            "error":      "scanned_pdf_not_yet",
        }

    if not parsed.transactions:
        db.mark_recon_parse_failed(session_id,
            "没有解析到任何流水 · 可能格式不支持 · 请反馈给我们")
        return {
            "session_id": session_id,
            "bank_code":  parsed.bank_code,
            "parse_status": "parse_failed",
            "tx_count":   0,
            "error":      "no_transactions_parsed",
        }

    ok = db.save_bank_recon_parse(session_id, parsed.as_dict())
    if not ok:
        db.mark_recon_parse_failed(session_id, "落库失败")
        raise HTTPException(500, detail="bank_recon.save_failed")

    return {
        "session_id":       session_id,
        "bank_code":        parsed.bank_code,
        "account_last4":    parsed.account_last4,
        "period_start":     parsed.period_start,
        "period_end":       parsed.period_end,
        "opening_balance":  parsed.opening_balance,
        "closing_balance":  parsed.closing_balance,
        "total_inflow":     parsed.total_inflow,
        "total_outflow":    parsed.total_outflow,
        "tx_count":         len(parsed.transactions),
        "parse_status":     "parsed",
    }


@app.get("/api/bank-recon/sessions")
async def bank_recon_list_sessions(request: Request, limit: int = 30):
    """最近对账会话列表
    v118.26.2 · 接 client_assignments filter(v28.1 铁律 · 员工只看分到的客户的对账)
    """
    user = get_current_user_from_request(request)
    limit = max(1, min(int(limit), 100))
    restrict = db.get_visible_client_ids_for_user(user)
    return db.list_bank_recon_sessions(user["id"], limit,
                                        restrict_client_ids=restrict)


# v118.26.0 · 对账中心首页统计 · 当月概览
@app.get("/api/bank-recon/stats")
async def bank_recon_stats(request: Request):
    """
    对账中心顶级菜单首页用 · 当月银行对账概览
    返回:
      pending  - 待对账(系统已推荐但人没确认 · suggested 状态)
      matched  - 已完成(matched 状态)
      unmatched - 未匹配(unmatched · 找不到候选)
      total_sessions - 当月会话总数(=0 时前端显示空态)
      last_activity_at - 最近一次操作时间(iso 字符串 · null 表示无)
    时区按 Asia/Bangkok 算「当月」
    """
    user = get_current_user_from_request(request)
    return db.get_bank_recon_stats(user["id"])


@app.get("/api/bank-recon/sessions/{session_id}")
async def bank_recon_session_detail(session_id: str, request: Request,
                                     filter: str = "all"):
    """会话详情 · 含流水列表 · 可按 match_status 过滤"""
    user = get_current_user_from_request(request)
    session = db.get_bank_recon_session(user["id"], session_id)
    if not session:
        raise HTTPException(404, detail="bank_recon.session_not_found")

    match_filter = filter if filter in ("matched", "suggested", "unmatched") else None
    txs = db.list_bank_recon_transactions(session_id, user["id"],
                                            match_filter=match_filter, limit=2000)
    return {"session": session, "transactions": txs}


@app.delete("/api/bank-recon/sessions/{session_id}")
async def bank_recon_delete_session(session_id: str, request: Request):
    """删除对账会话(级联删流水和候选)"""
    user = get_current_user_from_request(request)
    ok = db.delete_bank_recon_session(user["id"], session_id)
    if not ok:
        raise HTTPException(404, detail="bank_recon.session_not_found")
    return {"ok": True}


@app.post("/api/bank-recon/sessions/{session_id}/match")
async def bank_recon_run_match(session_id: str, request: Request):
    """触发匹配算法 · 同步等结果(最长 60 秒)"""
    user = get_current_user_from_request(request)
    session = db.get_bank_recon_session(user["id"], session_id)
    if not session:
        raise HTTPException(404, detail="bank_recon.session_not_found")
    if session.get("parse_status") != "parsed":
        raise HTTPException(400, detail="bank_recon.not_parsed")

    import bank_recon_v2 as br
    import asyncio
    try:
        stats = await asyncio.wait_for(
            asyncio.to_thread(br.run_matching_for_session,
                               session_id, str(user["id"])),
            timeout=60.0,
        )
    except asyncio.TimeoutError:
        raise HTTPException(504, detail="bank_recon.match_timeout")

    return stats


@app.post("/api/bank-recon/tx/{tx_id}/override")
async def bank_recon_tx_override(tx_id: str, request: Request):
    """用户手动指派匹配 · body: {history_id?, status}"""
    user = get_current_user_from_request(request)
    body = await request.json()
    status = (body.get("status") or "").strip()
    history_id = body.get("history_id")
    if status not in ("matched", "unmatched", "ignored"):
        raise HTTPException(400, detail="bank_recon.invalid_status")
    ok = db.override_tx_match(tx_id, str(user["id"]),
                               history_id if status == "matched" else None,
                               status)
    if not ok:
        raise HTTPException(404, detail="bank_recon.tx_not_found")
    return {"ok": True}


# v118.26.2 · 拉一条流水的候选发票列表(JOIN 拿发票字段 · 给候选抽屉用)
@app.get("/api/bank-recon/tx/{tx_id}/candidates")
async def bank_recon_tx_candidates(tx_id: str, request: Request):
    """
    返回这条流水「跑过匹配后」落库的全部候选(已按 score 降序 · 最多 5 个)
    每项含发票字段(invoice_no / vendor / amount_total / invoice_date / filename)
    没跑过匹配的流水返回空数组 · 前端显示「请先点开始匹配」
    """
    user = get_current_user_from_request(request)
    return {"candidates": db.get_tx_candidates(tx_id, str(user["id"]))}


# v118.26.2 · 给一份银行对账 session 绑客户(老板分客户给员工 → 流水进 client filter)
@app.patch("/api/bank-recon/sessions/{session_id}/client")
async def bank_recon_set_session_client(session_id: str, request: Request):
    """body: {client_id: int|null}
    鉴权:session 必须属于 user 且 client_id 必须在 visible 范围内(防越权)
    """
    user = get_current_user_from_request(request)
    body = await request.json()
    cid = body.get("client_id")
    # 校验客户在 visible 范围
    if cid is not None:
        try:
            cid = int(cid)
        except (ValueError, TypeError):
            raise HTTPException(400, detail="bank_recon.invalid_client_id")
        visible = db.get_visible_client_ids_for_user(user)
        if visible is not None and cid not in visible:
            raise HTTPException(403, detail="client.no_access")
    ok = db.update_bank_recon_session_client(str(user["id"]), session_id, cid)
    if not ok:
        raise HTTPException(404, detail="bank_recon.session_not_found")
    return {"ok": True, "client_id": cid}


# v118.26.2 · 测试中心专用 · 一键插入 mock 银行对账数据
#   仅 skin OAuth 测试白名单可调 · 前端按钮也只对 skin 显示
#   场景:v118.26.4 才做 Excel/CSV 解析 · 此前对账 UI 没数据可测
_TEST_USER_IDS = {
    "468b50c1-5593-4fd6-990d-515ce8085563",  # skin306152@gmail.com
}

@app.post("/api/bank-recon/_dev/seed")
async def bank_recon_dev_seed(request: Request):
    """skin 白名单 · 插一份 KBANK mock session(8 条流水)· 用于演示对账 UI"""
    user = get_current_user_from_request(request)
    uid = str(user["id"])
    if uid not in _TEST_USER_IDS:
        raise HTTPException(403, detail="bank_recon.dev_not_allowed")
    result = db.seed_bank_recon_test_data(uid)
    if not result.get("ok"):
        raise HTTPException(500, detail=f"bank_recon.seed_failed:{result.get('error','')[:80]}")
    return result


@app.post("/api/bank-recon/_dev/clear")
async def bank_recon_dev_clear(request: Request):
    """skin 白名单 · 清掉所有 _MOCK_ session"""
    user = get_current_user_from_request(request)
    uid = str(user["id"])
    if uid not in _TEST_USER_IDS:
        raise HTTPException(403, detail="bank_recon.dev_not_allowed")
    n = db.clear_bank_recon_test_data(uid)
    return {"ok": True, "deleted": n}


@app.post("/api/erp/logs/{log_id}/retry")
async def erp_retry_push(log_id: str, request: Request):
    """一键重试失败的推送"""
    user = get_current_user_from_request(request)
    _check_push_access(user)
    log = db.get_push_log_detail(user["id"], log_id)
    if not log:
        raise HTTPException(404, detail="log.not_found")
    if log["status"] == "success":
        raise HTTPException(400, detail="log.already_success")
    if not log.get("history_id") or not log.get("endpoint_id"):
        raise HTTPException(400, detail="log.missing_refs")

    history = db.get_ocr_history_detail(user["id"], log["history_id"], tenant_id=_tid(user))
    endpoint = db.get_erp_endpoint(user["id"], log["endpoint_id"])
    if not history:
        raise HTTPException(404, detail="history.not_found")
    if not endpoint:
        raise HTTPException(404, detail="erp.endpoint_not_found")

    # v118.34.10 · asyncio.to_thread keeps push_to_endpoint off the loop.
    import asyncio as _asyncio
    result = await _asyncio.to_thread(_erp.push_to_endpoint, endpoint, history)

    # 写新一条日志(attempt 递增)
    new_log_id = db.insert_push_log(
        user_id=user["id"],
        endpoint_id=endpoint["id"],
        history_id=log["history_id"],
        invoice_no=history.get("invoice_no"),
        seller_name=history.get("seller_name"),
        total_amount=history.get("total_amount"),
        status="success" if result["success"] else "failed",
        http_status=result.get("http_status"),
        request_body=result.get("request_body"),
        response_body=result.get("response_body"),
        error_msg=result.get("error_msg"),
        attempt=(log.get("attempt") or 1) + 1,
        elapsed_ms=result.get("elapsed_ms", 0),
        trigger="retry",
    )
    db.update_endpoint_stats(endpoint["id"], result["success"])
    db.update_history_push_status(log["history_id"],
                                  "success" if result["success"] else "failed")

    # v118.25 · 手动重试结果同步到原 log 的 retry 状态
    # 成功 → 清队列(终止自动重试)· 失败 → 也清队列(用户已经手动管了 · 不再交给 worker)
    if log.get("next_retry_at"):
        db.clear_retry_schedule(log["id"])

    return {
        "ok": result["success"],
        "log_id": new_log_id,
        "http_status": result.get("http_status"),
        "error_msg": result.get("error_msg"),
        "elapsed_ms": result.get("elapsed_ms"),
    }


# v118.25.1 · 批量重推:从推送日志列表多选 → 一次性触发多条重推
class ErpBatchRetryRequest(BaseModel):
    log_ids: List[str] = Field(..., description="要重推的 log id 列表 · 上限 50")


@app.post("/api/erp/logs/batch-retry")
async def erp_batch_retry(req: ErpBatchRetryRequest, request: Request):
    """批量重推:对每个 log_id 跑一次手动重试逻辑 · 返回成功/失败计数"""
    user = get_current_user_from_request(request)
    _check_push_access(user)

    if not req.log_ids:
        raise HTTPException(400, detail="erp.batch_empty")
    if len(req.log_ids) > 50:
        raise HTTPException(400, detail={"code": "erp.batch_too_many", "max": 50})

    succeeded = 0
    failed = 0
    skipped = 0  # 已成功 / 关联实体丢失等
    details: List[Dict[str, Any]] = []

    for log_id in req.log_ids:
        try:
            log = db.get_push_log_detail(user["id"], log_id)
            if not log:
                skipped += 1
                details.append({"log_id": log_id, "result": "skipped", "reason": "not_found"})
                continue
            if log["status"] == "success":
                skipped += 1
                details.append({"log_id": log_id, "result": "skipped", "reason": "already_success"})
                continue
            if not log.get("history_id") or not log.get("endpoint_id"):
                skipped += 1
                details.append({"log_id": log_id, "result": "skipped", "reason": "missing_refs"})
                continue

            history = db.get_ocr_history_detail(user["id"], log["history_id"], tenant_id=_tid(user))
            endpoint = db.get_erp_endpoint(user["id"], log["endpoint_id"])
            if not history or not endpoint:
                skipped += 1
                details.append({"log_id": log_id, "result": "skipped", "reason": "ref_deleted"})
                continue

            # v118.34.10 · asyncio.to_thread keeps push_to_endpoint off the loop.
            import asyncio as _asyncio
            result = await _asyncio.to_thread(_erp.push_to_endpoint, endpoint, history)
            db.insert_push_log(
                user_id=user["id"],
                endpoint_id=endpoint["id"],
                history_id=log["history_id"],
                invoice_no=history.get("invoice_no"),
                seller_name=history.get("seller_name"),
                total_amount=history.get("total_amount"),
                status="success" if result["success"] else "failed",
                http_status=result.get("http_status"),
                request_body=result.get("request_body"),
                response_body=result.get("response_body"),
                error_msg=result.get("error_msg"),
                attempt=(log.get("attempt") or 1) + 1,
                elapsed_ms=result.get("elapsed_ms", 0),
                trigger="retry",
            )
            db.update_endpoint_stats(endpoint["id"], result["success"])
            db.update_history_push_status(log["history_id"],
                                          "success" if result["success"] else "failed")
            # 跟单个手动重推一样:用户已经亲自管了 · 把原 log 的自动重试队列摘掉
            if log.get("next_retry_at"):
                db.clear_retry_schedule(log["id"])

            if result["success"]:
                succeeded += 1
                details.append({"log_id": log_id, "result": "success"})
            else:
                failed += 1
                details.append({"log_id": log_id, "result": "failed",
                                "error": result.get("error_msg")})
        except Exception as e:
            failed += 1
            details.append({"log_id": log_id, "result": "failed", "error": str(e)})

    return {
        "total": len(req.log_ids),
        "succeeded": succeeded,
        "failed": failed,
        "skipped": skipped,
        "details": details,
    }


class ErpBatchDeleteRequest(BaseModel):
    log_ids: List[str] = Field(..., description="要删除的 log id 列表 · 上限 200")


@app.post("/api/erp/logs/batch-delete")
async def erp_batch_delete(req: ErpBatchDeleteRequest, request: Request):
    """Bug 6 (Zihao 2026-05-19 拍板 · v118.34.23) · 批量删除推送日志.
    确认操作不可撤销 · 弹窗确认在 JS 侧 · 这里只管严格 user_id-scoped delete.
    返回 {total, deleted, skipped} · skipped = 不在该用户 scope 内的."""
    user = get_current_user_from_request(request)
    _check_push_access(user)

    if not req.log_ids:
        raise HTTPException(400, detail="erp.batch_empty")
    if len(req.log_ids) > 200:
        raise HTTPException(400, detail={"code": "erp.batch_too_many", "max": 200})

    requested = len(req.log_ids)
    deleted = db.delete_push_logs(user["id"], req.log_ids)
    return {
        "total": requested,
        "deleted": deleted,
        "skipped": max(0, requested - deleted),
    }


# ============================================================
# 第 5.1 批 · 泰国 RD 税务 API(校验 + 同步)
# ============================================================

class RdQueryRequest(BaseModel):
    tax_id: str = Field(..., description="13 位税号")
    branch: Optional[int] = Field(0, description="分支号 · 默认 0(总部)")


def _check_rd_access(user: dict):
    """v0.8 · 所有 plan 可用 · Free 有日限"""
    plan = (user or {}).get("plan", "free")
    p = _plan_permissions(plan)
    if not p.get("can_verify_tax"):
        raise HTTPException(403, detail="rd.upgrade_required")

    daily_limit = p.get("rd_daily_limit")
    if daily_limit is None:
        return  # 无限

    # 当日用量(从 Redis/内存都没有,直接查 DB 简表)
    used = db.get_rd_daily_usage(str(user["id"]))
    if used >= daily_limit:
        raise HTTPException(429, detail={
            "code": "rd.daily_limit_reached",
            "limit": daily_limit,
            "used": used,
        })


@app.post("/api/rd/verify")
async def rd_verify(req: RdQueryRequest, request: Request):
    """校验税号是否真实存在(快 · TIN Service)"""
    user = get_current_user_from_request(request)
    _check_rd_access(user)
    from rd_api import verify_tin
    result = verify_tin(req.tax_id)
    # v0.8.1 · 只计成功的查询,失败不算日限
    if (result or {}).get("valid"):
        db.increment_rd_daily_usage(str(user["id"]))
    return result


@app.post("/api/rd/lookup")
async def rd_lookup(req: RdQueryRequest, request: Request):
    """查公司全信息(VAT Service · 17 字段 · 用于一键同步)"""
    user = get_current_user_from_request(request)
    _check_rd_access(user)
    from rd_api import lookup_vat
    result = lookup_vat(req.tax_id, req.branch or 0)
    # v0.8.1 · 只计查到公司信息的请求
    if (result or {}).get("found") or (result or {}).get("name"):
        db.increment_rd_daily_usage(str(user["id"]))
    return result


# v1 别名
@app.post("/api/v1/rd/verify")
async def v1_rd_verify(req: RdQueryRequest, request: Request):
    return await rd_verify(req, request)


@app.post("/api/v1/rd/lookup")
async def v1_rd_lookup(req: RdQueryRequest, request: Request):
    return await rd_lookup(req, request)


# ============================================================
# v0.7 · 智能归档
# ============================================================
class ArchiveSettingsPayload(BaseModel):
    name_template: List[Dict[str, Any]] = Field(default_factory=list)
    folder_strategy: str = "by_month_seller"


class ArchivePreviewRequest(BaseModel):
    merged_fields: Dict[str, Any] = Field(default_factory=dict)
    name_template: Optional[List[Dict[str, Any]]] = None


def _check_archive_access(user: dict):
    """所有 plan 都能读归档设置 · 用默认模板"""
    plan = (user or {}).get("plan", "free")
    p = _plan_permissions(plan)
    if not p.get("can_archive"):
        raise HTTPException(403, detail="archive.upgrade_required")


def _check_archive_customize(user: dict):
    """只有 Plus/Pro 能改归档模板"""
    plan = (user or {}).get("plan", "free")
    p = _plan_permissions(plan)
    if not p.get("can_customize_archive"):
        raise HTTPException(403, detail="archive.customize_plus_required")


@app.get("/api/archive/settings")
async def archive_settings_get(request: Request):
    user = get_current_user_from_request(request)
    _check_archive_access(user)
    import archive as _archive
    s = db.get_archive_settings(str(user["id"]))
    if not s:
        # 没配过 · 返回默认
        return {
            "name_template": _archive.DEFAULT_TEMPLATE,
            "folder_strategy": _archive.DEFAULT_FOLDER_STRATEGY,
            "is_default": True,
        }
    return {
        "name_template": s.get("name_template") or _archive.DEFAULT_TEMPLATE,
        "folder_strategy": s.get("folder_strategy") or _archive.DEFAULT_FOLDER_STRATEGY,
        "is_default": False,
    }


@app.put("/api/archive/settings")
async def archive_settings_put(payload: ArchiveSettingsPayload, request: Request):
    user = get_current_user_from_request(request)
    _check_archive_customize(user)   # v0.8 · 只有 Plus/Pro 能改模板
    # 基本校验:模板不能是空的
    if not payload.name_template:
        raise HTTPException(400, detail="archive.template_empty")
    ok = db.upsert_archive_settings(
        str(user["id"]),
        payload.name_template,
        payload.folder_strategy,
    )
    if not ok:
        raise HTTPException(500, detail="archive.save_failed")
    return {"ok": True}


# ============================================================
# v0.13 · 重复发票检测设置
# ============================================================
class DupCheckSettingPayload(BaseModel):
    enabled: bool


@app.get("/api/settings/dup-check")
async def dup_check_get(request: Request):
    user = get_current_user_from_request(request)
    return {"enabled": db.get_user_dup_check_enabled(str(user["id"]))}


@app.put("/api/settings/dup-check")
async def dup_check_put(payload: DupCheckSettingPayload, request: Request):
    user = get_current_user_from_request(request)
    ok = db.set_user_dup_check_enabled(str(user["id"]), payload.enabled)
    if not ok:
        raise HTTPException(500, detail="settings.save_failed")
    return {"ok": True, "enabled": payload.enabled}


# ============================================================
# v0.15 · 用户自带 Gemini API Key
# 设计:
#   GET  · 读遮罩信息(安全)
#   PUT  · 保存 key
#   POST /test · 用 key 做一次最小调用验证有效
# v118.35.0.16 · /api/settings/gemini-key GET/PUT/POST routes 永久下线 · credits 系统不需要用户自带 key


@app.post("/api/archive/rename-preview")
async def archive_rename_preview(payload: ArchivePreviewRequest, request: Request):
    """给配置页实时预览用:传 merged_fields + 模板 → 返回名字"""
    user = get_current_user_from_request(request)
    _check_archive_access(user)
    import archive as _archive
    template = payload.name_template
    if not template:
        # 没传模板 · 用用户当前设置(或默认)
        s = db.get_archive_settings(str(user["id"]))
        template = (s or {}).get("name_template") or _archive.DEFAULT_TEMPLATE
    name = _archive.preview_name(payload.merged_fields or {}, template)
    return {"name": name}


# ============================================================
# 静态 + 根路由
# ============================================================
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/", response_class=HTMLResponse)
async def root():
    # v118.44.0.3 · login.html 也加 no-cache · 防浏览器 cache 老 login.html 让超管跳转逻辑失效
    return FileResponse(
        "static/login.html",
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0",
        },
    )


@app.get("/login", response_class=HTMLResponse)
async def login_page():
    return FileResponse(
        "static/login.html",
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0",
        },
    )


@app.get("/home", response_class=HTMLResponse)
async def home():
    # v118.27.5.4 · 强制 no-cache · 防 CDN/浏览器误缓存导致用户拿不到新版
    return FileResponse(
        "static/home.html",
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0",
        },
    )


# v118.44.0.1 · NAV-IA Phase 8 hotfix · 老 /admin 永久重定向到 /admin/cost
# 解决:老浏览器 cache 里的 home.js 仍跳 /admin · 导致 Earn 进入老 PEARNLY_ADMIN_MODE 视图(home.html 红 banner)
# 修法:无论老新代码,/admin 都被 server 端 301 引导到 /admin/cost(新 admin SPA)
@app.get("/admin", response_class=HTMLResponse)
async def admin_page():
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/admin/cost", status_code=301)


# v118.44.0 · NAV-IA Phase 8 · Earn 超管独立 admin layout(SPA)
# 路径 /admin/cost · /admin/users · /admin/* 全部返回独立 static/admin/admin.html
# 鉴权由前端 admin.js 调 /api/me + is_super_admin 校验(非超管 → 跳 /)
# 老的 /admin URL(L4209)仍返回 home.html · 作 PEARNLY_ADMIN_MODE 老逻辑兜底
@app.get("/admin/{rest:path}", response_class=HTMLResponse)
async def admin_layout_page(rest: str):
    return FileResponse(
        "static/admin/admin.html",
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0",
        },
    )


# v118.27.5.4 · 前端版本检测接口 · 前端定时轮询 · 不一致弹横幅
# v118.32.5.5.17 · 加 release_notes 4 语字段 · version-banner.js 拿来显示更新内容
# 铁律(v5.5.17 拍板):每次部署写 1-3 句 4 语更新说明 · 大白话 · 不出现 OCR/API/Gemini 技术词
@app.get("/api/version")
async def get_frontend_version():
    import time as _t
    # v118.34.5 · diagnostic state for the MR.ERP Playwright pipeline.
    # Lets the user verify in-browser whether the auto-installer landed
    # without needing SSH access. Cheap to compute (one stat() per call).
    # v118.34.13 · also surfaces the last captured 500 traceback so the
    # operator can read the actual stack from the browser instead of
    # journalctl.
    return {
        "version": PEARNLY_FRONTEND_VERSION,
        "ts": int(_t.time()),
        "playwright": _read_playwright_status(),
        "last_500": _read_last_500(),
        "release_notes": {
            "zh": "v118.35.0.20 · 计费系统真正打通 · 没钱不让识别:\n• 之前的大漏洞:新注册账户余额 0 也能无限识别 · 因为后台只有月页数检查 · 没接钱包余额检查 · 也没扣费代码 · 等于免费送 · 今天补齐\n• 价格规则按你定的:PDF 前 200 张 ฿1.50/张 · 第 201 张起 ฿0.75/张 · Excel/Word/CSV 不走 AI 直接按字符 · 50 字符 = 1 satang(฿0.01)\n• 余额 0 上传时弹『余额不足 · 当前 ฿0 · 本次约需 ฿X · 点击充值』· 不是干巴巴的英文报错 · 4 语都翻好\n• 充值输入超过 ฿500,000 上限时不再露 pydantic 报错 · 改成『充值金额超过单次上限』· 4 语\n• 白名单两个邮箱(skin306152 + mrerp)通过数据库 is_billing_exempt 字段管理 · 不再硬编码 user_id · 单一数据源\n• 3 个 OCR 入口全部接入:发票识别 / 销项税对账 / 银行对账",
            "th": "v118.35.0.20 · ระบบคิดเงินเชื่อมเสร็จสมบูรณ์ · ไม่มีเงินใช้ OCR ไม่ได้:\n• บั๊กเก่า: ผู้ใช้ใหม่ยอด 0 บาทใช้ OCR ฟรีไม่จำกัด · เพราะตรวจสอบแค่โควต้ารายเดือน · ไม่ได้เชื่อมกระเป๋าเงินกับโค้ดหักเงิน · วันนี้แก้แล้ว\n• ราคาตามที่ตกลง: PDF 200 แผ่นแรก ฿1.50/แผ่น · แผ่นที่ 201 ขึ้นไป ฿0.75/แผ่น · Excel/Word/CSV ไม่ผ่าน AI คิดตามตัวอักษร · 50 ตัวอักษร = 1 สตางค์\n• อัปโหลดตอนยอด 0 จะแสดง 'ยอดเงินไม่พอ · ปัจจุบัน ฿0 · ต้องการ ~฿X · แตะเพื่อเติมเงิน' · 4 ภาษา\n• กรอกจำนวนเงินเติมเกิน ฿500,000 ไม่ขึ้นข้อความ pydantic แล้ว · เปลี่ยนเป็น 'จำนวนเงินเกินวงเงินสูงสุดต่อครั้ง' · 4 ภาษา\n• Whitelist 2 อีเมล (skin306152 + mrerp) ใช้ฟิลด์ is_billing_exempt ใน DB จัดการ · ไม่ฮาร์ดโค้ด user_id อีกต่อไป\n• เชื่อม 3 จุดอัปโหลดทั้งหมด: OCR ใบกำกับ / ศูนย์กระทบยอดภาษีขาย / ศูนย์กระทบยอดธนาคาร",
            "en": "v118.35.0.20 · Credits billing fully wired · no balance = no OCR:\n• Critical bug fixed: new accounts at ฿0 could use OCR unlimited because only monthly page check existed · wallet check + deduction code were missing · effectively free · plugged today\n• Pricing per your spec: PDF first 200 pages ฿1.50/page · 201+ at ฿0.75/page · Excel/Word/CSV skip AI · charged by character · 50 chars = 1 satang (฿0.01)\n• Upload with ฿0 balance now shows 'Insufficient balance · current ฿0 · need ~฿X · tap to top up' · 4 langs\n• Topup over ฿500,000 cap no longer shows raw pydantic error · changed to 'Amount exceeds single-topup cap' · 4 langs\n• 2 whitelist emails (skin306152 + mrerp) now managed via users.is_billing_exempt DB field · no more hardcoded user_id · single source of truth\n• Wired all 3 OCR entry points: invoice OCR / VAT recon / bank recon",
            "ja": "v118.35.0.20 · クレジット課金システム完全接続 · 残高なしで OCR 不可:\n• 致命バグ修正: 新規ユーザー残高 0 でも無制限 OCR · 月間ページチェックのみで残高チェック + 課金コードが未実装 · 実質無料 · 本日修正\n• 価格仕様: PDF 最初の 200 枚 ฿1.50/枚 · 201 枚以降 ฿0.75/枚 · Excel/Word/CSV は AI 不要 · 文字数課金 · 50 文字 = 1 サタン (฿0.01)\n• 残高 0 でアップロード時『残高不足 · 現在 ฿0 · 今回必要 ~฿X · タップでチャージ』表示 · 4 言語\n• チャージ ฿500,000 超過時 pydantic エラー非表示 · 『1 回の上限を超えています』に変更 · 4 言語\n• ホワイトリスト 2 アドレス (skin306152 + mrerp) は users.is_billing_exempt DB フィールドで管理 · user_id ハードコード廃止\n• 3 つの OCR エントリーポイント全接続: 請求書 OCR / VAT 対照 / 銀行対照",
            "th": "v118.35.0.19 · แก้บั๊กอัปโหลด Statement Excel + เปลี่ยนข้อความ error เป็นภาษาคน:\n• ตอนอัปโหลด Excel statement ระบบจะลอง 'อ่านตรง' ก่อน (ฟรี+ทันที) · อ่านหัวคอลัมน์ไม่ออกค่อย fallback ไป AI · รองรับหัวภาษาไทย/อังกฤษ/จีนอัตโนมัติ\n• ตารางสถานะการอ่านไฟล์ในศูนย์กระทบยอด · ข้อความ error แดงๆ เปลี่ยนจาก 'Gemini returned invalid JSON' เป็น 'หาคอลัมน์หัวตารางไม่เจอ · ตรวจสอบไฟล์มีวันที่/จำนวนเงิน/ยอดคงเหลือ' · ครบ 4 ภาษา",
            "en": "v118.35.0.19 · Bank statement Excel fix + plain-language reconciliation errors:\n• When users upload bank-statement Excel files, the system now tries direct-read first (free + instant), falling back to AI only when headers can't be detected (previously forced through AI and hit token limits) · Auto-detects Chinese/English/Thai headers\n• Reconciliation 'File Parse Status' table now shows plain-language errors like 'Cannot detect column headers · ensure date/amount/balance columns exist' instead of 'Gemini returned invalid JSON' (4 langs)",
            "ja": "v118.35.0.19 · 銀行明細 Excel 修正 + 対照失敗メッセージを平易な表現に:\n• ユーザーが銀行明細 Excel をアップロードする際、まず『直接読取』(無料+即時)を試行 · ヘッダー認識できない場合のみ AI にフォールバック(従来は強制 AI でトークン制限超過) · 中/英/タイ語ヘッダー自動認識\n• 対照センターの『ファイル解析状態』表のエラー表示を『Gemini returned invalid JSON』から『列ヘッダーが認識できません · 日付/金額/残高列を確認してください』へ · 4 言語対応",
            "release_notes_archived_v34_39": "v118.34.39 · 设置弹窗滚动彻底修好 · 用户 DevTools 诊断抓出真正 bug:\n• 用户在 zoom 142% / viewport 659px 时测出: modal max-height 是 560px (正确) 但 layout + side-nav 被 align-items:stretch + flex:1 撑成 611px (内容高度) · 超出 modal 90px · 被 modal overflow:hidden 切掉 · '联系我们' 永远看不到\n• 根因: 之前靠 min-height:0 + flex shrink chain 让 flex item 缩到父容器 · 实际 flex 默认 min-height:auto 导致 item 至少跟内容一样高 · 我的 min-height:0 没起到预期作用\n• 修: 放弃 flex stretch 推力 · 直接给 side-nav 设 max-height: calc(min(85vh, 100vh - 64px) - 80px) · 用 calc 卡死最大高 · 不再依赖 flex chain · 现在 overflow-y:scroll 必然触发\n• cache-bust v=11834938 → 11834939\n\n累积 fix 包含: 对账中心 78 条 4 语术语统一 · Excel sheet 名 รายละเอียดบัญชี → รายละเอียดSTATEMENT · ERP 集成页布局 · 设置弹窗响应式 + 滚动条 · Xero/MR.ERP 卡同高 · nginx pre-gzipped 陈旧 .gz 自动清除",
            "release_notes_archived_v34_33": "v118.34.33 · 批 1 · OCR 自动归属客户 + 不 retry 用户数据错 + 日志加客户/ERP 列:\n• 改动 1 OCR 完自动 resolve client_id:按 buyer_name + buyer_tax 匹配 Pearnly 客户表(税号 0.98 / 完全名 0.95 / substring 0.80-0.90 / 学习记忆 1.0)· ≥0.95 自动绑 + 学习下次 · 0.80-0.95 标 suggested_client_id · <0.80 不绑 · 没归属的发票直接不入 auto-push 队列(不再炸 ERR_NO_CLIENT)\n• 改动 3 retry 区分用户数据错:USER_DATA_ERROR_CODES (NO_CLIENT/NO_CUSTOMER_MAPPING/NO_INVOICE_NO/DATE_FUTURE/DUPLICATE_INVOICE 等) + 泰文 raw 模式 · 这类错不进重试队列 · retry worker 命中也立刻摘队列\n• 改动 5 日志列表加 Pearnly 客户列:LEFT JOIN clients · UI 显示 client_name · 未归属灰色「未归属」+ tip\n• 改动 8 顺便做 ERP 列:LEFT JOIN erp_endpoints · 显示 endpoint.name(用户起的)\n• 新 db 表 buyer_to_client_memory · 用户在抽屉 assign 时学习 buyer→client · 下次 OCR 自动归属",
            "release_notes_archived_v34_28": "v118.34.28 · 死链修:derive_mrerp_invoice_no seq 不再写死 001:\n• 根因:第一笔 push 成功 → bill_no SI690519-001 · 第二笔 push (同一天) MR.ERP 报「เลขที่ดังกล่าวมีอยู่ในระบบแล้ว(已存在)」· 因为 derive_mrerp_invoice_no seq 写死 \"001\" · 同一天所有 push 都 derive YYMMDD-001 撞\n• 之前的 docstring 写「序号取 history.id 末 3 位 hex 转 dec mod 1000」但代码写错成 hardcode \"001\" · 注释和实现不一致\n• 修:按 docstring 真实现 · 用 history.id 末 6 位 hex 转 dec mod 999 + 1 (避开 000)· 同一 history 重传幂等 · 不同 history 序号不同\n• 测试: 5 个 uuid → 5 个不同 seq (460/272/732/705/078) · 同 uuid 两次 → 同 seq (441/441) · 幂等保证\n\n现在可以并发推多笔 · 不会撞 invoice_no",
            "release_notes_archived_v34_27": "v118.34.27 · listing 拉不到不再阻断 push · fail-soft 走 auto-create:\n• 根因:TEST2019 stkmas listing 在 30s × 3 retries 都拉不出来(MR.ERP 服务端慢或 #showdata p selector 不命中)· 之前 listing fetch 在 lookup() 里 raise · 整个 push fail\n• 修:mrerp_customer_sync.lookup + mrerp_product_sync.lookup 把 _fetch_listing() try/catch MRERPTechnicalError · 失败时 log warning + return None · 让 lookup_or_create 走 L4 auto-create (创建路径 stkmas/allform.php 不依赖 allview.php listing)\n• 效果:listing 拉不到 → L1 DB mapping 没命中 → L2/L3 listing 路径 fail-soft return None → L4 自动建用 seed 模板 · push 继续\n• 跟之前 v34.26 sync 吞 MRERPTechnicalError 是互补:v34.26 在 sync 顶层吞 · v34.27 在 lookup 里 fail-soft 让 lookup_or_create 能继续走 L4\n\n这是 stkmas listing 慢的兜底方案 · 自动建客户/商品全链路通",
            "release_notes_archived_v34_26": "v118.34.26 · 修 3 个生产卡点 (a/b/c):\n• 问题 a sync listing timeout 让整批 push 炸:adapter._sync_master_data 现在也 catch MRERPTechnicalError(之前只 catch MRERPBusinessError)· listing fetch 超时不再炸整批 · 让 validate_history_for_sales_credit 后面 ERR_NO_CUSTOMER_MAPPING preflight 早返友好错给用户。customer + product 两侧同步\n• 问题 b ERR_NO_CUSTOMER_MAPPING friendly 改 action-oriented:旧「该客户未配置 MR.ERP 客户码映射」→ 新「这个客户在 MR.ERP 里还没对应客户码 · 请打开 MR.ERP 连接向导选「种子客户」(开自动建) · 或去 ERP 设置手动加映射」4 语都改\n• 问题 c wizard 客户列表一直 loading:_fetchSeedCustomers + _fetchSeedProducts 加 AbortController 60s client-side timeout · 后端 worst case 90s 会卡 wizard · 客户端 60s 兜底超时 → fail-over 显示 input + 「⚠ 无法拉取」hint。\n\n刷浏览器:wizard 编辑 mrerp 看客户列表 60s 内会回(成功或失败)· 不再无限 loading",
            "release_notes_archived_v34_25": "v118.34.25 · 修 4 个生产体验问题 (A/B/C/D):\n• 问题 A 推送 listing 超时 + 文案改:1) home.js humanizeError 去掉 大于 10s 老数字 · 加 listing fetch 专门翻译「拉取 MR.ERP 客户/商品列表超时 · 已重试 3 次仍不通」2) adapter._sync_master_data 加 guard:history.client_id 是 0/null 时 · 跳过 customer + product sync(让 preflight ERR_NO_CLIENT 早返 · 不浪费 90s+ listing 拉取)\n• 问题 B wizard 商品下拉 + 警告并存:success path 显式 hide inputEl + fbHintEl · customer + product 镜像 · 防 race / 上次 fallback 残留\n• 问题 C 批量删除视觉反馈:删除后立即从 DOM 移除被删 row + 立即 hide batch bar · 500ms 后再 reload 拉新数据(用户先看到「消失了」再自动接显示剩余 log)\n• 问题 D 全选含 success:canSelect 从「仅 failed 终态」改成「非 retrying-in-progress」· success log 也能选(批量删除清历史)· 批量重试 server 已 skip success 不会重复推 · selectableIds 同步\n\n试一下:1) wizard 编辑 mrerp 看商品下拉 (P26050011 应该正确选中 + 没警告) 2) 推送日志全选应该包括成功的 row 3) 删除完应该看到 row 立即消失",
            "release_notes_archived_v34_24": "v118.34.24 · 修 3 个生产体验问题:\n• 问题 1 重复发票 friendly 文案改人话:旧「该发票号已存在于 MR.ERP」→ 新「这张发票之前已经推送过 MR.ERP 了 · 不能重复推 · 如需更新请去 MR.ERP 后台直接编辑这张单据」· 4 语都改 · เลขที่เอกสารซ้ำ + เลขที่ดังกล่าวมีอยู่ในระบบแล้ว 两条都改\n• 问题 2 product listing fetch 超时加固:wait_for_selector 10s → 30s · retry 2 → 3 次 · 间隔 5s · cache TTL 60s → 600s(10 分钟)· customer side 镜像 · 减少对 MR.ERP 压力 + 大 tenant listing 慢也能拿到\n• 问题 3 推送日志加表头全选 checkbox:第一列加全选 box · 点了 → 当前 filter 下所有失败终态行勾选 · 半选状态 indeterminate · 跟现有「批量重推」「批量删除」联动 · 列标签(时间/状态/触发/发票号/卖家/HTTP/耗时)4 语都补\n\n刷浏览器 · 推送日志页表头应该有全选 box · listing 拉取应该更稳定",
            "release_notes_archived_v34_23": "v118.34.23 · 修 Bug 5/6/8 + 加批量删除:\n• Bug 8 product-create 跳 login.php(生产真问题):MR.ERP PHP session 偶尔在 customer-sync 跑完进 stkmas 模块时被服务端无声 invalidate · 修:detect page.url 落在 login.php · 自动 re-login + select_company + 重 goto 一次 · 仍失败抛 ERR_TECHNICAL 带清晰消息 · customer side 镜像同样修\n• Bug 5 批量重推:加直接 addEventListener 绑定到 btn-erp-batch-retry/delete/clear · 不依赖 document 事件委托 · 加 console.info trace · 防 IIFE 没接管的边界情况 · 兜底 2s/5s 重试 binding\n• Bug 6 加批量删除:推送日志页加「批量删除」按钮(红色 ghost)· 弹确认「确定删除 N 条?不可撤销」(danger 模式)· 新路由 POST /api/erp/logs/batch-delete · db.delete_push_logs 严格 user_id scope · 4 语 i18n 全补\n• Bug 7 推送按钮下拉:既有 _pushOne + _renderDropdown 已支持多 endpoint · 视觉小调下个版本\n\n刷浏览器:1) 配 mrerp 推一张能 trigger 商品 auto-create 的发票 · 看是否能完成 2) 推送日志页选几条 · 点批量删除 · 看是否真删",
            "release_notes_archived_v34_22": "v118.34.22 · 修 4 个生产 UI bug (Bug 1-4):\n• Bug 1 ERR_NO_CLIENT 全栈防护:wizard Step 1 至少选 1 客户才能 Next(前端 toast 警告)· POST/PATCH endpoint 后端校验 client_ids 空 → 400 friendly · ERR_NO_CLIENT 友好文案从「未指定 Pearnly 客户(client_id 缺失)」改成「这张发票还没分配 Pearnly 客户 · 请先在发票详情里指定客户」4 语都改\n• Bug 2 seed 下拉默认值 + listing retry log:wizard 渲染下拉时 selectedValue=endpoint.config.seed_xxx · 不在 listing 时合成 option 标「(已保存 · 当前列表暂未显示)」· 不 fallback 到 listing[0]。app.py _fetch_listing_with_retry 每次结果都打 log 包含 ok/code/screenshot 路径\n• Bug 3 抽屉「看推送日志」link CSS 修:原来 text-align:right 偶尔被内容撑过 viewport → 按钮跑出。改 flex left-align + 蓝色高亮卡片 · 不依赖 right-edge 浮动\n• Bug 4 删集成卡片右下「看推送日志」link:入口收敛 · 用户点「配置」进 ERP 抽屉 → 抽屉里点「看推送日志 →」· 或直接点集成主页顶部「推送日志」tab\n\nBug 5-8 (批量重试/批量删除/推送下拉/product-create session) 下个版本继续",
            "release_notes_archived_v34_21": "v118.34.21 · 收尾 2 个老 bug (P-3 + P-4):\n• P-3:PATCH /api/erp/endpoints/:id 之前不加密 mrerp 凭据 · wizard 编辑老 endpoint 重新输密码 → 落库明文 → 下次 test-connection InvalidToken → ERR_CRED_DECRYPT. 现在 PATCH 也走 kms_helper.encrypt_str · 跟 POST 路由对齐 · 已加密的 ciphertext 不 double-encrypt.\n• P-4:wizard 测试连接失败后端把截图路径塞在 raw_error 一坨密集文本里用户看不见. 现在 JS 正则抽 screenshot=(\\S+\\.png) · 单独显示成「失败截图存到了:{path} · 发给客服可以加快排查」橙色高亮条 · 4 语都补.\n• 加守门测试 PatchEndpointEncryptionContractTests 2 条:plaintext 触发加密 · 已加密的不 double-encrypt.\n\n配过 mrerp 的话 · 试一次「编辑」改密码 · 改完应该还能正常测试连接.",
            "en_archived_v34_28": "v118.34.28 · Critical fix: derive_mrerp_invoice_no seq no longer hardcoded 001:\n• Root cause: first push succeeded (bill SI690519-001), but the second push (same day) failed with MR.ERP responding 'invoice number already exists' because derive_mrerp_invoice_no hardcoded seq='001'. Every same-day push derived YYMMDD-001 and collided.\n• The docstring said 'seq = history.id last 3 hex bytes mod 1000' but the implementation was a hardcoded literal — comment and code drifted.\n• Fix: match the docstring intent. Use history.id last 6 hex chars → int mod 999 + 1 (avoid 000). Same history → same seq (idempotent for retries); different histories → different seqs.\n• Unit-tested: 5 random uuids → 5 distinct seqs (460/272/732/705/078); same uuid twice → same seq (441/441) — idempotency preserved.\n\nMulti-push on the same day now works without invoice_no collisions.",
            "en_archived_v34_27": "v118.34.27 · listing fail no longer blocks push · fail-soft to auto-create:\n• Root cause: on TEST2019, stkmas listing fetch fails after 30s × 3 retries (MR.ERP slow or #showdata p selector miss). Previously _fetch_listing raised inside lookup() and killed the whole push.\n• Fix: mrerp_customer_sync.lookup + mrerp_product_sync.lookup now try/catch MRERPTechnicalError around _fetch_listing(); on fail, log warning + return None so lookup_or_create falls through to L4 auto-create (creation path stkmas/allform.php doesn't depend on listing page allview.php).\n• Effect: listing fetch fails → L1 DB mapping miss → L2/L3 fail-soft return None → L4 auto-creates using the seed template, push proceeds.\n• Complementary to v34.26 which catches MRERPTechnicalError at sync top-level; v34.27 fails soft at the lookup level so lookup_or_create can still go L4.\n\nThis is the safety net for when stkmas listing is slow / unscrapable. Customer/product auto-create chain stays operational.",
            "en_archived_v34_26": "v118.34.26 · 3 production blockers fixed (a/b/c):\n• Issue a sync listing timeout no longer crashes the whole batch push: adapter._sync_master_data now also catches MRERPTechnicalError (previously only MRERPBusinessError). When listing fetch times out, sync swallow+continue and validate_history_for_sales_credit returns ERR_NO_CUSTOMER_MAPPING quickly with a friendly message. Mirrored on customer + product sides.\n• Issue b ERR_NO_CUSTOMER_MAPPING friendly rewritten with action: old 'No MR.ERP customer mapping configured for this client' → new 'This client has no matching MR.ERP customer code · open the MR.ERP wizard and pick a seed customer (enables auto-create), or go to ERP settings to add the mapping manually' (4 langs).\n• Issue c wizard customer listing stuck loading forever: _fetchSeedCustomers + _fetchSeedProducts now use AbortController with 60s client-side timeout (backend worst case is 90s; client 60s safety cap). On timeout, the wizard falls back to text input + warning instead of an infinite spinner.\n\nRefresh and open the MR.ERP wizard edit dialog: the customer/product dropdown should return within 60s (success or fail-over), never infinite loading.",
            "en_archived_v34_25": "v118.34.25 · 4 production-experience fixes (A/B/C/D):\n• Issue A push listing timeout + wording: (1) home.js humanizeError drops the stale greater-than-10s number and adds a dedicated translation for listing-fetch failures: 'Fetching MR.ERP customer/product list timed out, already retried 3 times, MR.ERP may be slow, try again later'. (2) adapter._sync_master_data adds a guard: when history.client_id is 0/null, skip customer + product sync entirely (let the preflight return ERR_NO_CLIENT immediately instead of burning 90s+ on listing fetches).\n• Issue B wizard product dropdown + warning showing together: success path now explicitly hides inputEl + fbHintEl (customer + product mirror). Prevents race / stale fallback state from leaking through.\n• Issue C batch-delete visual feedback: deleted rows are now removed from DOM immediately and the batch bar hides right away; the list reloads 500ms later (user sees rows disappeared first, then remaining logs auto-fill).\n• Issue D select-all now includes success rows: canSelect changed from failed-final only to not-retrying-in-progress. Success logs can be selected (for batch-delete to clean history); batch-retry server-side already skips success rows automatically. selectableIds in the header checkbox computation also updated.\n\nTo verify: (1) open the MR.ERP wizard edit dialog, the product dropdown should be selected correctly (P26050011) with NO warning. (2) On the push logs tab, select-all should include success rows. (3) Batch-delete should show rows disappearing immediately.",
            "en_archived_v34_24": "v118.34.24 · 3 production-experience fixes:\n• Issue 1 duplicate-invoice friendly wording rewritten in plain language: old 'This invoice number already exists in MR.ERP' → new 'This invoice was already pushed to MR.ERP previously · duplicates aren't allowed · to update, open MR.ERP and edit the bill directly' (4 langs; both Thai variants เลขที่เอกสารซ้ำ + เลขที่ดังกล่าวมีอยู่ในระบบแล้ว updated).\n• Issue 2 product listing fetch hardening: wait_for_selector 10s → 30s, retries 2 → 3 with 5s back-off between, route cache TTL 60s → 600s (10 min). Mirrored on customer side. Reduces pressure on MR.ERP and tolerates slow listings on larger tenants.\n• Issue 3 push-logs header select-all checkbox: a new column-1 checkbox in the header row toggles all selectable rows (failed-final only) under the current filter; partial state renders as indeterminate; column labels (Time/Status/Trigger/Invoice/Seller/HTTP/Elapsed) translated to 4 langs.\n\nRefresh the page: the push-logs tab should show a select-all checkbox in the header, and listing fetches should be more reliable.",
            "en_archived_v34_23": "v118.34.23 · Bug 5/6/8 fixes + batch-delete:\n• Bug 8 product-create bouncing to login.php (production blocker): MR.ERP PHP session occasionally got invalidated server-side after the customer-sync phase completed, when nav'ing into the stkmas module. Fix: detect page.url landing on login.php after the goto, auto re-login + select_company + retry the goto once; if still bounced, raise ERR_TECHNICAL with a clear 'session refresh did not recover' message. Mirrored on the customer side.\n• Bug 5 batch-retry no-response: added direct addEventListener bindings on btn-erp-batch-retry/delete/clear (no longer solely relying on document-level event delegation). Added console.info traces and 2s/5s re-binding as a safety net for edge cases where the IIFE didn't take over.\n• Bug 6 batch-delete added: new red ghost button beside batch-retry, confirm dialog ('Delete N? Cannot be undone' in danger mode), new POST /api/erp/logs/batch-delete route, db.delete_push_logs with strict user_id scope, 4-lang i18n.\n• Bug 7 push button dropdown: existing _pushOne + _renderDropdown infrastructure already supports multi-endpoint; visual polish deferred to next version.\n\nRefresh and: (1) push an invoice that triggers product auto-create and check it completes; (2) on the push logs tab, select rows and click batch-delete to confirm real deletion.",
            "en_archived_v34_22": "v118.34.22 · 4 production UI bugs fixed (Bug 1-4):\n• Bug 1 ERR_NO_CLIENT full-stack guard: wizard Step 1 now requires ≥1 client before Next (frontend toast warn). POST/PATCH endpoint backend validator rejects empty client_ids → 400 friendly. ERR_NO_CLIENT friendly message rewritten from technical 'client_id missing' to action-oriented 'this invoice has no Pearnly client assigned · open the invoice details and pick a client first' in 4 langs.\n• Bug 2 seed dropdown default + listing retry log: wizard renders dropdown with selectedValue=endpoint.config.seed_xxx; if the saved code isn't in the current listing page, synthesize an option labelled 'saved · not on current listing page' rather than fallback-selecting listing[0]. app.py _fetch_listing_with_retry now logs ok/code/screenshot path on every attempt.\n• Bug 3 drawer 'View push log' link CSS fix: original text-align:right occasionally let the button overflow the 480px drawer width → user couldn't see it. Switched to flex left-align with a blue-highlighted card; no longer depends on right-edge flow.\n• Bug 4 removed the right-side 'View push log' link from the integrations card. Entry path collapsed: click '配置' → ERP drawer → click 'View push log →' inside the drawer · or click the integrations page top tab 'Push Log' directly.\n\nBug 5-8 (batch retry / batch delete / push button dropdown / product-create session) to follow in the next version.",
            "en_archived_v34_21": "v118.34.21 · Closing out P-3 + P-4 from STATE.md:\n• P-3: PATCH /api/erp/endpoints/:id previously skipped mrerp credential encryption · wizard editing an existing endpoint with a fresh password would store plaintext under username_enc/password_enc · next test-connection's decrypt threw InvalidToken → ERR_CRED_DECRYPT. PATCH now mirrors POST's kms_helper.encrypt_str logic; already-encrypted ciphertext is NOT double-encrypted.\n• P-4: wizard test-connection failures left the screenshot path buried inside a dense raw_error blob. The JS now regex-extracts `screenshot=(\\S+\\.png)` and surfaces it on its own orange-bordered line: 'Failure screenshot saved at: {path} · send this to support'. 4-lang complete.\n• Added PatchEndpointEncryptionContractTests with 2 guards: plaintext triggers encryption · already-encrypted ciphertext is preserved.\n\nIf you have an MR.ERP endpoint, try editing it and changing the password — test-connection should keep working afterward.",
            "th_archived_v34_21": "v118.34.21 · ปิดงาน 2 บัก P-3 + P-4:\n• P-3: PATCH /api/erp/endpoints/:id เดิมไม่เข้ารหัสข้อมูลรับรอง mrerp · เมื่อแก้ไข endpoint แล้วใส่รหัสผ่านใหม่ → เก็บ plaintext ใน DB → ครั้งถัดไป test-connection ถอดรหัสไม่ผ่าน → ERR_CRED_DECRYPT. ตอนนี้ PATCH ก็ใช้ kms_helper.encrypt_str เหมือน POST · ciphertext ที่เข้ารหัสแล้วไม่ encrypt ซ้ำ.\n• P-4: ตอนทดสอบเชื่อมต่อล้มเหลว backend แอบใส่ path สกรีนช็อตอยู่ใน raw_error ก้อนใหญ่ ผู้ใช้มองไม่เห็น · ตอนนี้ JS regex ดึง screenshot=(\\S+\\.png) ออกมาโชว์เป็นแถบสีส้ม 'บันทึกภาพข้อผิดพลาดที่: {path} · ส่งให้ทีมซัพพอร์ตเพื่อช่วยตรวจสอบ' · 4 ภาษาครบ.\n• เพิ่ม PatchEndpointEncryptionContractTests 2 ตัว: plaintext กระตุ้นการเข้ารหัส · ที่เข้ารหัสแล้วไม่ double-encrypt.\n\nถ้ามี endpoint mrerp อยู่แล้ว ลองคลิก 'แก้ไข' เปลี่ยนรหัสผ่าน · หลังบันทึก test-connection ควรใช้ได้ปกติ",
            "ja_archived_v34_21": "v118.34.21 · STATE.md の P-3 + P-4 を回収:\n• P-3: PATCH /api/erp/endpoints/:id は mrerp 認証情報の暗号化をスキップしていた · ウィザードで既存 endpoint のパスワードを再入力すると平文が DB に保存 → 次回 test-connection 復号で InvalidToken → ERR_CRED_DECRYPT. PATCH も kms_helper.encrypt_str を通すように修正 · POST と一致 · 既に暗号化された ciphertext は再暗号化しない.\n• P-4: ウィザードの接続テスト失敗時、screenshot パスが raw_error の塊に埋もれてユーザーが見えなかった · JS で正規表現 `screenshot=(\\S+\\.png)` を抽出し、別行の橙色強調枠で「エラースクショ保存先: {path} · サポートに送ると調査が早まります」と表示 · 4 言語対応.\n• PatchEndpointEncryptionContractTests を 2 件追加: plaintext が暗号化される · 暗号化済みは double-encrypt しない.\n\nMR.ERP endpoint があれば「編集」でパスワード変更 → test-connection が継続して動くはず."
        }
    }


# ── GitHub Webhook 自动部署 (v118.41.133 · 2026-05-17) ──────────────────────
# Claude 每次 git push → GitHub → 触发这个接口 → 服务器自动 pull + restart
# 无需 SSH · 彻底绕开 fail2ban 问题
@app.post("/internal/deploy")
async def github_deploy_webhook(request: Request):
    """
    GitHub Webhook → 触发 git-deploy.sh
    关键修复：先发响应，再用 detached subprocess 执行部署脚本。
    这样 systemctl restart 不会在发送响应前就把自己杀掉。
    """
    import hmac as _hmac, hashlib as _hashlib, subprocess as _subprocess, os as _os
    body = await request.body()
    secret = _os.environ.get("GITHUB_WEBHOOK_SECRET", "")
    if secret:
        sig = request.headers.get("X-Hub-Signature-256", "")
        expected = "sha256=" + _hmac.new(secret.encode(), body, _hashlib.sha256).hexdigest()
        if not _hmac.compare_digest(sig, expected):
            logger.warning("[git-deploy] HMAC mismatch — ignored")
            raise HTTPException(status_code=403, detail="Invalid webhook signature")

    logger.info("[git-deploy] webhook received · launching detached deploy in 3 s")

    # ── 关键：用 start_new_session=True 开新会话 ──────────────────────
    # 父进程（mrpilot）被 systemctl restart 杀掉后，子进程仍然存活，
    # 能完成 git pull + cp + systemctl restart 整个流程。
    _subprocess.Popen(
        ["bash", "-c", "sleep 3 && bash /opt/mrpilot/git-deploy.sh >> /var/log/mrpilot-deploy.log 2>&1"],
        close_fds=True,
        start_new_session=True,   # 脱离父进程组，父死子不死
    )
    return {"ok": True, "status": "deploy scheduled in 3 s"}


@app.get("/internal/deploy/manual")
async def manual_deploy_trigger(token: str = ""):
    """
    备用手动部署触发器（webhook 失败时使用）。
    访问：https://pearnly.com/internal/deploy/manual?token=<GITHUB_WEBHOOK_SECRET>
    无需 SSH，浏览器直接触发。
    """
    import subprocess as _subprocess, os as _os
    secret = _os.environ.get("GITHUB_WEBHOOK_SECRET", "")
    if not secret or token != secret:
        raise HTTPException(status_code=403, detail="Invalid token")
    logger.info("[git-deploy] manual trigger")
    _subprocess.Popen(
        ["bash", "-c", "sleep 1 && bash /opt/mrpilot/git-deploy.sh >> /var/log/mrpilot-deploy.log 2>&1"],
        close_fds=True,
        start_new_session=True,
    )
    return {"ok": True, "status": "manual deploy scheduled", "log": "/var/log/mrpilot-deploy.log"}


@app.get("/internal/deploy/log")
async def deploy_log(token: str = "", lines: int = 50):
    """查看最近部署日志。"""
    import subprocess as _subprocess, os as _os
    secret = _os.environ.get("GITHUB_WEBHOOK_SECRET", "")
    if not secret or token != secret:
        raise HTTPException(status_code=403, detail="Invalid token")
    try:
        result = _subprocess.run(
            ["tail", f"-{lines}", "/var/log/mrpilot-deploy.log"],
            capture_output=True, text=True, timeout=5
        )
        return {"ok": True, "log": result.stdout}
    except Exception as e:
        return {"ok": False, "error": str(e)}


# ── Playwright admin installer (v118.34.3 · 2026-05-19) ─────────────────────
# Background: git-deploy.sh on the server runs `git pull + systemctl restart`
# but does NOT run `pip install -r requirements.txt`. The MR.ERP integration
# needs Playwright + chromium binary; without them, /api/erp/test-connection
# for mrerp returns ERR_PLAYWRIGHT_MISSING (the friendly fallback added in
# v118.34.2).
#
# This endpoint installs both in one shot and schedules a restart so the
# new module is picked up by the long-running uvicorn process. Auth uses
# the same GITHUB_WEBHOOK_SECRET as the deploy webhook.
#
# Idempotent: pip skips already-installed packages, playwright skips
# already-downloaded browsers. Safe to retry.
@app.get("/internal/install-playwright")
@app.post("/internal/install-playwright")
async def install_playwright(token: str = "", with_deps: bool = False, restart: bool = True):
    """One-shot installer for Playwright + chromium on the production host.

    Query params:
        token       Required. Same value as GITHUB_WEBHOOK_SECRET env.
        with_deps   If true, runs `playwright install chromium --with-deps`
                    (requires root + apt). Default false; usually not
                    needed if the host already has libgbm/libnss/etc.
        restart     If true (default), schedule mrpilot systemctl restart
                    after install succeeds so uvicorn picks up the new
                    module. The restart is detached/delayed 3 s, mirroring
                    /internal/deploy so the response can land first.

    Returns a JSON envelope with per-step stdout/stderr so the operator
    can diff "what worked" vs "what failed" in the browser. NEVER raises
    — failure modes are part of the response, not the HTTP status.
    """
    import subprocess as _subprocess
    import os as _os
    import shutil as _shutil
    secret = _os.environ.get("GITHUB_WEBHOOK_SECRET", "")
    if not secret or token != secret:
        raise HTTPException(status_code=403, detail="Invalid token")

    log_lines = []

    def _log(prefix, completed):
        # CompletedProcess → string block we can render to the user.
        log_lines.append(f"\n--- {prefix} (exit={completed.returncode}) ---")
        if completed.stdout:
            log_lines.append(completed.stdout.strip())
        if completed.stderr:
            log_lines.append("STDERR: " + completed.stderr.strip())

    try:
        # ── 1. pip install playwright ──
        pip_bin = _shutil.which("pip3") or _shutil.which("pip") or "pip3"
        # `--break-system-packages` mirrors deploy.sh's pattern; required on
        # PEP-668 protected hosts (Ubuntu 23.04+ system Python).
        pip_cmd = [pip_bin, "install", "playwright", "--break-system-packages"]
        log_lines.append(f"$ {' '.join(pip_cmd)}")
        r1 = _subprocess.run(pip_cmd, capture_output=True, text=True, timeout=300)
        _log("pip install playwright", r1)
        if r1.returncode != 0:
            return {
                "ok": False, "step": "pip_install",
                "hint": "pip install failed — check stderr above. May need sudo or pip path fix.",
                "log": "\n".join(log_lines),
            }

        # ── 2. download chromium ──
        # We use `python3 -m playwright install` (vs `playwright` CLI) so we
        # use the exact interpreter that mrpilot runs as, ensuring the
        # browser ends up where Python will find it.
        py_bin = _shutil.which("python3") or "python3"
        browser_cmd = [py_bin, "-m", "playwright", "install", "chromium"]
        if with_deps:
            browser_cmd.append("--with-deps")
        log_lines.append(f"\n$ {' '.join(browser_cmd)}")
        # Browser download is ~140MB; allow up to 10 min on slow links.
        r2 = _subprocess.run(browser_cmd, capture_output=True, text=True, timeout=600)
        _log("playwright install chromium", r2)
        if r2.returncode != 0:
            return {
                "ok": False, "step": "browser_install",
                "hint": (
                    "Browser download failed. If you see 'missing libgbm/libnss',"
                    " re-run this URL with &with_deps=true to install system libs."
                ),
                "log": "\n".join(log_lines),
            }

        # ── 3. verify import works (in a clean subprocess) ──
        verify_cmd = [
            py_bin, "-c",
            "from playwright.sync_api import sync_playwright; "
            "print('IMPORT_OK · version', sync_playwright.__module__)"
        ]
        log_lines.append(f"\n$ {' '.join(verify_cmd)}")
        r3 = _subprocess.run(verify_cmd, capture_output=True, text=True, timeout=15)
        _log("verify import", r3)
        import_ok = "IMPORT_OK" in (r3.stdout or "")

        if not import_ok:
            return {
                "ok": False, "step": "verify",
                "hint": "pip + browser installed but import still fails. Check that "
                        "mrpilot's Python interpreter matches the one that ran pip.",
                "log": "\n".join(log_lines),
            }

        # ── 4. schedule restart so the running uvicorn picks up the new module ──
        next_step_url = None
        if restart:
            log_lines.append("\n--- scheduling mrpilot restart in 3 s ---")
            _subprocess.Popen(
                ["bash", "-c",
                 "sleep 3 && systemctl restart mrpilot "
                 ">> /var/log/mrpilot-deploy.log 2>&1"],
                close_fds=True, start_new_session=True,
            )
        else:
            next_step_url = (
                "https://pearnly.com/internal/deploy/manual?token=<your-secret>"
            )

        return {
            "ok": True, "step": "complete",
            "restart_scheduled": bool(restart),
            "next_step": (
                "Wait ~10 s for the restart, then click 「测试连接」in the wizard. "
                "If you still see ERR_PLAYWRIGHT_MISSING, retry with &with_deps=true."
                if restart else f"Trigger restart manually: {next_step_url}"
            ),
            "log": "\n".join(log_lines),
        }

    except _subprocess.TimeoutExpired as e:
        return {
            "ok": False, "step": "timeout",
            "hint": f"Step timed out after {e.timeout}s. Re-run; pip/playwright "
                    f"resume partial downloads.",
            "log": "\n".join(log_lines),
        }
    except Exception as e:
        logger.exception("install_playwright endpoint failure")
        return {
            "ok": False, "step": "exception",
            "log": "\n".join(log_lines) + f"\n\nEXCEPTION: {type(e).__name__}: {e}",
        }


@app.get("/reset", response_class=HTMLResponse)
async def reset_page():
    return FileResponse("static/reset.html")


@app.get("/terms", response_class=HTMLResponse)
async def terms_page():
    return FileResponse("static/terms.html")


@app.get("/privacy", response_class=HTMLResponse)
async def privacy_page():
    return FileResponse("static/privacy.html")


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
_GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_OAUTH_REDIRECT_URI", "https://pearnly.com/api/auth/google/callback")
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
            tr = await client.post("https://oauth2.googleapis.com/token", data={
                "code": code,
                "client_id": _GOOGLE_CLIENT_ID,
                "client_secret": _GOOGLE_CLIENT_SECRET,
                "redirect_uri": _GOOGLE_REDIRECT_URI,
                "grant_type": "authorization_code",
            })
            if tr.status_code != 200:
                logger.error(f"[OAuth] token exchange failed {tr.status_code}: {tr.text[:300]}")
                return _RedirectResp("/login?oauth_error=token_fail", status_code=302)
            tok_data = tr.json()
            access_token = tok_data.get("access_token")
            if not access_token:
                return _RedirectResp("/login?oauth_error=no_access_token", status_code=302)
            ur = await client.get(
                "https://openidconnect.googleapis.com/v1/userinfo",
                headers={"Authorization": f"Bearer {access_token}"}
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
    return HTMLResponse(f'''<!doctype html>
<html><head><meta charset="utf-8"><title>Pearnly · Signing in...</title></head>
<body style="font-family:-apple-system,sans-serif;background:#0a0e27;color:#fff;display:flex;align-items:center;justify-content:center;height:100vh;margin:0">
<div>Signing you in...</div>
<script>
try {{ localStorage.setItem("mrpilot_token", {safe_token}); }} catch(e) {{}}
window.location.replace("{_redirect_path}");
</script>
</body></html>''')


# ============================================================
# v118.28.4 · LINE Login OAuth 2.0
# 一键登录 / 一键注册 · 跟 Google 同套机制
# email scope 需 LINE 单独审批 · 没拿到时占位 username
# ============================================================
_LINE_LOGIN_CHANNEL_ID = os.getenv("LINE_LOGIN_CHANNEL_ID", "")
_LINE_LOGIN_CHANNEL_SECRET = os.getenv("LINE_LOGIN_CHANNEL_SECRET", "")
_LINE_LOGIN_REDIRECT_URI = os.getenv("LINE_LOGIN_REDIRECT_URI", "https://pearnly.com/api/auth/line/callback")


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
                }
            )
            if tr.status_code != 200:
                logger.error(f"[LINE OAuth] token exchange failed {tr.status_code}: {tr.text[:300]}")
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
                }
            )
            if vr.status_code != 200:
                logger.error(f"[LINE OAuth] id_token verify failed {vr.status_code}: {vr.text[:300]}")
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
    return HTMLResponse(f'''<!doctype html>
<html><head><meta charset="utf-8"><title>Pearnly · Signing in...</title></head>
<body style="font-family:-apple-system,sans-serif;background:#0a0e27;color:#fff;display:flex;align-items:center;justify-content:center;height:100vh;margin:0">
<div>Signing you in...</div>
<script>
try {{ localStorage.setItem("mrpilot_token", {safe_token}); }} catch(e) {{}}
window.location.replace("{_redirect_path}");
</script>
</body></html>''')


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
    from auth_signup import normalize_email as _norm_email
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
            "tos": "服务条款", "privacy": "隐私政策",
            "copyright": "© 2026 Pearnly. All rights reserved.",
        },
        "th": {
            "subject": "Pearnly · รหัสยืนยันของคุณ",
            "tagline": "ผู้ช่วย AI ด้านบัญชี",
            "title": "รหัสยืนยันของคุณ",
            "lead": "ใช้รหัสนี้เพื่อสมัครบัญชี Pearnly · ใช้ได้ 10 นาที",
            "ignore": "หากคุณไม่ได้ทำรายการนี้ · โปรดเพิกเฉยอีเมลฉบับนี้",
            "brand_full": "Pearnly · ระบบอัตโนมัติบัญชีไทย",
            "tos": "ข้อกำหนด", "privacy": "นโยบายความเป็นส่วนตัว",
            "copyright": "© 2026 Pearnly · สงวนลิขสิทธิ์",
        },
        "en": {
            "subject": "Pearnly · Your verification code",
            "tagline": "Your AI accounting co-pilot",
            "title": "Your verification code",
            "lead": "Use this code to create your Pearnly account · valid for 10 minutes",
            "ignore": "If you didn't request this · please ignore this email",
            "brand_full": "Pearnly · Accounting automation for Thailand",
            "tos": "Terms", "privacy": "Privacy",
            "copyright": "© 2026 Pearnly. All rights reserved.",
        },
        "ja": {
            "subject": "Pearnly · 確認コード",
            "tagline": "AI 会計コパイロット",
            "title": "確認コード",
            "lead": "Pearnly アカウント作成用 · 10 分間有効",
            "ignore": "心当たりのない場合 · このメールを無視してください",
            "brand_full": "Pearnly · タイ会計自動化プラットフォーム",
            "tos": "利用規約", "privacy": "プライバシーポリシー",
            "copyright": "© 2026 Pearnly. All rights reserved.",
        },
    }
    tt = L.get(lang, L["zh"])
    html = f'''<!doctype html><html><body style="margin:0;padding:0;background:#f1f5f9;">
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
</body></html>'''
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
                    (email, email)
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
                cur.execute("""
                    SELECT 1 FROM email_codes
                    WHERE email = %s AND purpose = %s AND sent_at > NOW() - INTERVAL '60 seconds'
                    LIMIT 1
                """, (email, req.purpose))
                if cur.fetchone():
                    raise HTTPException(status_code=429, detail="resend_too_fast")

                cur.execute("""
                    SELECT COUNT(*) AS n FROM email_codes
                    WHERE email = %s AND purpose = %s AND sent_at > NOW() - INTERVAL '1 hour'
                """, (email, req.purpose))
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
                cur.execute("""
                    UPDATE email_codes SET used = TRUE, used_at = NOW()
                    WHERE email = %s AND purpose = %s AND used = FALSE
                """, (email, req.purpose))
                cur.execute("""
                    INSERT INTO email_codes (email, code, purpose, expires_at, sender_ip)
                    VALUES (%s, %s, %s, NOW() + INTERVAL '10 minutes', %s)
                """, (email, code, req.purpose, ip))
        except Exception as e:
            logger.error(f"send_email_code db insert: {e}")
            raise HTTPException(status_code=500, detail="db_error")

        # 发邮件
        subject, html = _build_verification_email_html(code, req.lang)
        ok, err = _smtp_send_email(email, subject, html)
        if not ok:
            try:
                with db.get_cursor(commit=True) as cur:
                    cur.execute("""
                        UPDATE email_codes SET used = TRUE, used_at = NOW()
                        WHERE email = %s AND code = %s AND purpose = %s
                    """, (email, code, req.purpose))
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
            cur.execute("""
                SELECT id, expires_at, used FROM email_codes
                WHERE email = %s AND code = %s AND purpose = %s
                ORDER BY id DESC LIMIT 1
            """, (email, code, req.purpose))
            row = cur.fetchone()
            if not row:
                raise HTTPException(status_code=400, detail="code_invalid")
            r = dict(row) if not isinstance(row, dict) else row
            if r.get("used"):
                raise HTTPException(status_code=400, detail="code_used")
            cur.execute("SELECT NOW() > %s AS expired", (r["expires_at"],))
            exp_row = cur.fetchone()
            expired = exp_row.get("expired") if isinstance(exp_row, dict) else (exp_row[0] if exp_row else True)
            if expired:
                raise HTTPException(status_code=400, detail="code_expired")
        return {"ok": True}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"verify_email_code: {e}")
        raise HTTPException(status_code=500, detail="server_error")


# ============================================================
# T1 · LINE Bot · 绑定 API(v0.19.0)
# ============================================================

class LineBindingCodeResponse(BaseModel):
    code: str = Field(..., description="6 位绑定码")
    expires_at: str = Field(..., description="过期时间 ISO")
    bot_friend_url: Optional[str] = Field(None, description="Bot 加好友 URL(若配了)")
    bot_basic_id: Optional[str] = Field(None, description="Bot 显示 ID · 如 @mrpilot")


class LineBindingInfo(BaseModel):
    bound: bool
    line_display_name: Optional[str] = None
    line_picture_url: Optional[str] = None
    bound_at: Optional[str] = None
    last_active_at: Optional[str] = None


@app.post("/api/line/binding-code", response_model=LineBindingCodeResponse)
async def create_line_binding_code(request: Request):
    """
    生成 6 位 LINE 绑定码 · 10 分钟有效。
    前端流程:
      1. 用户点「绑定 LINE」按钮
      2. 调此接口拿 code
      3. 页面显示:「请扫 QR 加 Bot 好友 · 发送这串数字:123456」
    """
    user = get_current_user_from_request(request)

    result = db.generate_line_binding_code(user["id"], ttl_minutes=10)
    if not result:
        raise HTTPException(status_code=500, detail="生成绑定码失败 · 请稍后重试")

    return LineBindingCodeResponse(
        code=result["code"],
        expires_at=result["expires_at"],
        bot_friend_url=os.environ.get("LINE_BOT_FRIEND_URL") or None,
        bot_basic_id=os.environ.get("LINE_BOT_BASIC_ID") or None,
    )


@app.get("/api/line/binding", response_model=LineBindingInfo)
async def get_line_binding_info(request: Request):
    """查当前用户的 LINE 绑定状态(前端轮询判断是否已绑完)"""
    user = get_current_user_from_request(request)
    b = db.get_line_binding_by_user(user["id"])
    if not b:
        return LineBindingInfo(bound=False)
    return LineBindingInfo(
        bound=True,
        line_display_name=b.get("line_display_name"),
        line_picture_url=b.get("line_picture_url"),
        bound_at=b["bound_at"].isoformat() if b.get("bound_at") else None,
        last_active_at=b["last_active_at"].isoformat() if b.get("last_active_at") else None,
    )


@app.delete("/api/line/binding")
async def delete_line_binding(request: Request):
    """解绑 LINE"""
    user = get_current_user_from_request(request)
    ok = db.unbind_line_by_user(user["id"])
    if not ok:
        raise HTTPException(status_code=500, detail="解绑失败")
    return {"success": True}


# ------------------------------------------------------------
# T1 · 用户偏好语言(v0.19.0)
# 用于 LINE Bot / 邮件等非网页场景回复
# ------------------------------------------------------------

class UpdateLangRequest(BaseModel):
    lang: str = Field(..., description="zh / en / th / ja")


@app.post("/api/me/lang")
async def update_my_lang(req: UpdateLangRequest, request: Request):
    """同步用户偏好语言到 DB · 前端每次切语言时调用"""
    user = get_current_user_from_request(request)
    ok = db.update_user_preferred_lang(user["id"], req.lang)
    if not ok:
        raise HTTPException(status_code=400, detail="不支持的语言或更新失败")
    return {"success": True, "lang": req.lang}


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

        # 图片消息:v0.19 T1 轮 3 · OCR 闭环
        if msg_type == "image":
            message_id = msg.get("id")
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
            asyncio.create_task(_handle_line_image_ocr(
                bound_user=bound_user,
                line_user_id=line_user_id,
                message_id=message_id,
                lang=lang,
            ))
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
                lang, "bind_success",
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

async def _handle_line_image_ocr(bound_user: dict, line_user_id: str,
                                   message_id: str, lang: str):
    """
    异步处理 LINE 图片消息:
      1. 下载图片
      2. 包装成 PDF 喂 OCR(复用 gemini 引擎)
      3. 插入 ocr_history(source='line_bot')
      4. 扣配额
      5. push 结果给用户
    """
    try:
        # 1. 下载
        img_bytes = line_client.download_message_content(message_id)
        if not img_bytes:
            line_client.push_text(line_user_id, line_client.t_ocr(lang, "err_download"))
            return

        # 2. 权限 / 配额检查(复用网页逻辑)
        user_fresh = db.find_user_by_id(bound_user["id"])
        if not user_fresh:
            line_client.push_text(line_user_id, line_client.t_ocr(lang, "err_plan"))
            return

        # 所有账号都走 Gemini · 区别只在 key 归属(月付共用 / 买断自带)和配额
        ok, err_code, quota_info = _check_user_quota(user_fresh)
        if not ok:
            if err_code in ("quota.exhausted", "ocr.monthly_limit_exceeded"):
                line_client.push_text(line_user_id, line_client.t_ocr(lang, "err_quota"))
            elif err_code == "quota.need_api_key":
                # 买断账号没填 key
                line_client.push_text(line_user_id, line_client.t_ocr(lang, "err_need_key"))
            else:
                line_client.push_text(line_user_id, line_client.t_ocr(lang, "err_quota"))
            return

        # 月付用户:本次 1 页 · 预先检查是否超额
        if quota_info.get("mode") == "monthly":
            mq = quota_info.get("monthly_quota") or 0
            um = quota_info.get("used_this_month") or 0
            if um + 1 > mq:
                line_client.push_text(line_user_id, line_client.t_ocr(lang, "err_quota"))
                return

        # 3. 图片 → PDF
        pdf_bytes = line_client.image_to_pdf_bytes(img_bytes)
        if not pdf_bytes:
            line_client.push_text(line_user_id, line_client.t_ocr(lang, "err_ocr"))
            return

        # 3.5 · 文件指纹缓存查找(v118.22.0.3 · 与网页入口对齐)
        # LINE 同图重传 / 用户传过的票再发 → 命中则跳 Gemini · 省配额
        import hashlib as _hashlib_l
        file_hash = _hashlib_l.sha256(pdf_bytes).hexdigest()
        cached = find_ocr_by_hash(
            str(user_fresh["id"]),
            file_hash,
            tenant_id=str(user_fresh.get("tenant_id")) if user_fresh.get("tenant_id") else None,
        )
        if cached:
            logger.info(f"[line_ocr] 命中文件缓存 (hash={file_hash[:12]}...) hid={cached['id']}")
            # 跑异常 hook(同网页缓存命中分支 · 不重复扣配额)
            try:
                import asyncio as _asyncio_exc_lc
                _cached_pages = cached.get("pages") or []
                _primary = next((p for p in _cached_pages if not p.get("is_duplicate") and not p.get("is_copy")), None)
                _primary = _primary or (_cached_pages[0] if _cached_pages else None)
                _cf = (_primary or {}).get("fields") or {}
                _exc_total_c = None
                _raw_t_c = _cf.get("total_amount")
                if _raw_t_c:
                    try:
                        _exc_total_c = float(str(_raw_t_c).replace(",", "").strip())
                    except Exception as e:
                        logger.warning(f"[line_cache] total_amount 解析失败: {e}")
                _asyncio_exc_lc.create_task(_async_run_exception_checks(
                    history_id=str(cached["id"]),
                    user_id=str(user_fresh["id"]),
                    tenant_id=str(user_fresh.get("tenant_id")) if user_fresh.get("tenant_id") else None,
                    seller_name=_cf.get("seller_name"),
                    invoice_no=_cf.get("invoice_number"),
                    total_amount=_exc_total_c,
                    confidence=cached.get("confidence"),
                    duplicate=None,
                    fields=_cf,
                ))
                logger.info(f"  🛡  [LINE Cache] 异常检测已入队 · hid={cached['id']}")
            except Exception as _e_lc:
                logger.warning(f"[line_ocr] 缓存异常检测入队失败: {_e_lc}")
            # 推 cached 结果给用户(模拟 OCR 完成)
            reply_txt = line_client.format_ocr_result_for_line(
                lang, cached.get("pages") or [], invoice_count=len(cached.get("pages") or [])
            )
            line_client.push_text(line_user_id, reply_txt)
            return

        # 4. OCR · 新 pipeline 唯一路径
        own_key = (user_fresh.get("gemini_api_key")
                   or user_fresh.get("custom_gemini_api_key") or "").strip()
        api_key = own_key or None
        # 检查 API key 可用性(用户自带或系统默认)
        if not api_key and not os.environ.get("GEMINI_API_KEY", "").strip():
            line_client.push_text(line_user_id, line_client.t_ocr(lang, "err_plan"))
            return

        try:
            from services.ocr.pipeline import run_on_pdf_bytes as _pipeline_run
            from services.ocr.legacy_adapter import pipeline_result_to_legacy_dict
            _pipe_res = _pipeline_run(pdf_bytes, max_pages=1, api_key=api_key)
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

        # 5. 写 history(source='line_bot')
        # file_hash 已在 3.5 计算(v118.22.0.3)
        try:
            hid = insert_ocr_history(
                user_id=str(user_fresh["id"]),
                filename=f"line_{message_id}.pdf",
                page_count=len(pages),
                pages=pages,
                confidence=result.get("confidence") or "unknown",
                elapsed_ms=result.get("elapsed_ms") or 0,
                file_size_kb=len(pdf_bytes) // 1024,
                file_hash=file_hash,
                source="line_bot",
                source_ref=line_user_id,
            )
        except Exception as e:
            logger.warning(f"[line_ocr] 写 history 失败(不影响回复): {e}")
            hid = None

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
                _asyncio_exc_l.create_task(_async_run_exception_checks(
                    history_id=str(hid),
                    user_id=str(user_fresh["id"]),
                    tenant_id=str(user_fresh.get("tenant_id")) if user_fresh.get("tenant_id") else None,
                    seller_name=_f.get("seller_name"),
                    invoice_no=_f.get("invoice_number"),
                    total_amount=_exc_total,
                    confidence=result.get("confidence"),
                    duplicate=_dup,
                    fields=_f,
                ))
                logger.info(f"  🛡  [LINE] 异常检测已入队 · hid={hid} · dup={'有' if _dup else '无'}")
            except Exception as _e:
                logger.warning(f"[line_ocr] 异常检测入队失败(不影响推送): {_e}")

        # 6. 扣配额(月付)· v87 多租户支持
        qm = quota_info.get("mode")
        if qm == "shared" and user_fresh.get("tenant_id"):
            try:
                db.increment_tenant_monthly_usage(str(user_fresh["tenant_id"]), n=1)
            except Exception as e:
                logger.warning(f"[line_ocr] 扣租户配额失败: {e}")
        elif qm == "monthly":
            try:
                increment_user_monthly_usage(str(user_fresh["id"]), n=1)
            except Exception as e:
                logger.warning(f"[line_ocr] 扣配额失败: {e}")

        # 7. 推送识别结果
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

def _require_super_admin(request: Request) -> Dict[str, Any]:
    """超级管理员守门员 · 非超管 403"""
    user = get_current_user_from_request(request)
    if not user.get("is_super_admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="admin.not_super_admin",
        )
    return user


# ============================================================
# v118.27.7 · 多租户改造 P0 · 数据迁移路由(仅超管)
# 流程:
#   1. POST /api/admin/migration/dry_run  · 试运行 · 只统计不写库 · 看输出 OK 才执行
#   2. POST /api/admin/migration/execute  · 真执行 · 写 memberships
# 失败可回滚:DELETE FROM memberships;(memberships 表空 = 系统自动 fallback 到老 user.tenant_id)
# ============================================================

@app.post("/api/admin/migration/dry_run")
async def admin_migration_dry_run(request: Request):
    """v27.7 · 试运行多租户迁移 · 只统计不写库
    返回结构化 JSON · 给超管 admin 看 · 检查无误才调 /execute
    """
    _require_super_admin(request)
    result = db.migrate_to_membership_model(dry_run=True)
    return result


@app.post("/api/admin/migration/execute")
async def admin_migration_execute(request: Request):
    """v27.7 · 真执行多租户迁移 · 写 memberships
    幂等:已迁移的用户 ON CONFLICT DO NOTHING · 重复调安全
    回滚:DELETE FROM memberships · 系统会 fallback 到老 user.tenant_id
    """
    _require_super_admin(request)
    result = db.migrate_to_membership_model(dry_run=False)
    return result


# ============================================================
# v118.27.7.1 · 孤立用户(tenant_id IS NULL)盘点 + 修复路由(仅超管)
# ============================================================

@app.get("/api/admin/migration/orphan_list")
async def admin_orphan_list(request: Request):
    """v27.7.1 · 列出所有孤立用户(tenant_id IS NULL)+ 每人数据量统计"""
    _require_super_admin(request)
    return {"items": db.list_orphan_users()}


@app.post("/api/admin/migration/fix_orphans")
async def admin_fix_orphans(request: Request, dry_run: bool = True):
    """v27.7.1 · 给孤立用户每人建独立 tenant + 同步写 membership
    Query 参数:?dry_run=true(默认 · 只看不改)/ ?dry_run=false(真执行)
    单用户独立事务 · 失败不影响其他
    """
    _require_super_admin(request)
    return db.fix_orphan_users(dry_run=bool(dry_run))


# ============================================================
# v118.27.8.0 · RLS 行级安全(P1 试点)· 仅超管
# ============================================================

@app.get("/api/admin/rls/status")
async def admin_rls_status(request: Request):
    """v27.8.0 · 看 RLS 总开关 + clients 表当前 RLS 状态 + 现存 policy"""
    _require_super_admin(request)
    return db.get_clients_rls_status()


@app.post("/api/admin/rls/run_tests")
async def admin_rls_run_tests(request: Request):
    """v27.8.0 · 跑 RLS 穿透测试 · 5 条
    流程:临时启用 clients 表 RLS → 跑 5 条测试 → 关闭恢复
    全部通过 → RLS 基础设施 OK · v27.8.1 才永久启用
    """
    _require_super_admin(request)
    return db.run_rls_isolation_tests()


@app.post("/api/admin/migration/backfill_tenant_ids")
async def admin_backfill_tenant_ids(request: Request, dry_run: bool = True):
    """v27.8.1 · 自动扫所有 (user_id, tenant_id) 双列表 · 按用户回填 tenant_id
    Query 参数:?dry_run=true(默认 · 只看)/ ?dry_run=false(真执行)
    """
    _require_super_admin(request)
    return db.backfill_tenant_ids(dry_run=bool(dry_run))


class AdminCreateTenantRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    tenant_type: str = Field("shared_api", pattern="^(shared_api|byo_api|admin)$")
    monthly_quota: int = 100
    notes: Optional[str] = None


class AdminUpdateTenantQuotaRequest(BaseModel):
    monthly_quota: int = Field(..., ge=0)


class AdminUpdateTenantStatusRequest(BaseModel):
    status: str = Field(..., pattern="^(active|warning|suspended|frozen)$")


@app.get("/api/admin/tenants")
async def admin_list_tenants(request: Request):
    """列出所有租户 · 仅超管"""
    _require_super_admin(request)
    tenants = db.list_all_tenants(limit=500)
    # 序列化
    result = []
    for t in tenants:
        result.append({
            "id": str(t["id"]),
            "name": t.get("name"),
            "display_name": t.get("display_name"),
            "tenant_type": t.get("tenant_type"),
            "status": t.get("status"),
            "monthly_quota": int(t.get("monthly_quota") or 0),
            "used_this_month": int(t.get("used_this_month") or 0),
            "member_count": int(t.get("actual_member_count") or 0),
            "ocr_this_month": int(t.get("ocr_this_month") or 0),
            "last_active_at": t["last_active_at"].isoformat() if t.get("last_active_at") else None,
            "subscription_expires_at": t["subscription_expires_at"].isoformat() if t.get("subscription_expires_at") else None,
            "notes": t.get("notes"),
            "created_at": t["created_at"].isoformat() if t.get("created_at") else None,
        })
    return {"tenants": result, "total": len(result)}


# ============================================================
# v106 · 管理员成本追踪面板 · 4 个路由 · 仅 super_admin 可访问
# ============================================================

@app.get("/api/admin/cost/overview")
async def admin_cost_overview(request: Request):
    """成本面板 · 顶部 KPI(今日/本月/总计 + 引擎占比)"""
    _require_super_admin(request)
    return db.get_cost_overview()


# v107.3 · 诊断接口 · 直接 SELECT 5 条最新记录看是否有数据
@app.get("/api/admin/cost/debug")
async def admin_cost_debug(request: Request):
    """成本追踪诊断 · 仅 super admin · 用于排查为什么前端看不到数据"""
    _require_super_admin(request)
    try:
        with db.get_cursor() as cur:
            # 1. 表是否存在 + 总条数
            cur.execute("""
                SELECT COUNT(*) AS total,
                       MIN(created_at) AS earliest,
                       MAX(created_at) AS latest,
                       SUM(cost_thb) AS sum_cost,
                       SUM(pages) AS sum_pages
                FROM ocr_cost_log
            """)
            stats = dict(cur.fetchone() or {})
            # 2. 最近 5 条
            cur.execute("""
                SELECT id, user_id::text, engine, pages, input_tokens, output_tokens,
                       cost_thb, created_at, created_at::date AS day_only,
                       CURRENT_DATE AS db_today, NOW() AS db_now
                FROM ocr_cost_log
                ORDER BY created_at DESC
                LIMIT 5
            """)
            recent = [dict(r) for r in cur.fetchall()]
            # 3. PostgreSQL 时区设置
            cur.execute("SHOW timezone")
            tz = cur.fetchone()
        # 序列化(datetime → str)
        from datetime import datetime as _dt
        def _ser(v):
            if isinstance(v, _dt):
                return v.isoformat()
            try:
                # date 类型
                return str(v)
            except:
                return v
        return {
            "table_stats": {k: _ser(v) for k, v in stats.items()},
            "postgres_timezone": dict(tz) if tz else {},
            "recent_5": [{k: _ser(v) for k, v in r.items()} for r in recent],
        }
    except Exception as e:
        import traceback
        return {"error": str(e), "traceback": traceback.format_exc()}


@app.get("/api/admin/cost/by_user")
async def admin_cost_by_user(request: Request, limit: int = 50):
    """按用户分组 · 找烧钱多的"""
    _require_super_admin(request)
    rows = db.get_cost_by_user(limit=limit)
    return {
        "users": [
            {
                "user_id": str(r.get("user_id")),
                "username": r.get("username") or "(已删)",
                "plan": r.get("plan") or "",
                "today_cost_thb": float(r.get("today_cost") or 0),
                "month_cost_thb": float(r.get("month_cost") or 0),
                "total_cost_thb": float(r.get("total_cost") or 0),
                "total_pages": int(r.get("total_pages") or 0),
                "total_invoices": int(r.get("total_invoices") or 0),
                "last_used_at": r["last_used_at"].isoformat() if r.get("last_used_at") else None,
            }
            for r in rows
        ],
    }


@app.get("/api/admin/cost/daily_trend")
async def admin_cost_daily_trend(request: Request, days: int = 30):
    """每天趋势 · 默认最近 30 天"""
    _require_super_admin(request)
    days = max(1, min(int(days), 365))
    return {"days": db.get_cost_daily_trend(days=days)}


@app.get("/api/admin/cost/export")
async def admin_cost_export(request: Request, days: int = 30):
    """导出 CSV · 最近 N 天每条成本记录"""
    _require_super_admin(request)
    days = max(1, min(int(days), 365))
    try:
        with db.get_cursor() as cur:
            cur.execute("""
                SELECT c.created_at, u.username, c.engine, c.pages,
                       c.input_tokens, c.output_tokens, c.cost_thb, c.elapsed_ms
                FROM ocr_cost_log c
                LEFT JOIN users u ON u.id = c.user_id
                WHERE c.created_at >= NOW() - INTERVAL '%s days'
                ORDER BY c.created_at DESC
            """ % days)
            rows = cur.fetchall()
        # 拼 CSV
        import io
        import csv
        buf = io.StringIO()
        w = csv.writer(buf)
        w.writerow(["时间", "用户", "引擎", "页数", "输入Token", "输出Token", "成本THB", "耗时ms"])
        for r in rows:
            w.writerow([
                r["created_at"].strftime("%Y-%m-%d %H:%M:%S") if r["created_at"] else "",
                r.get("username") or "(已删)",
                r.get("engine") or "",
                int(r.get("pages") or 0),
                int(r.get("input_tokens") or 0),
                int(r.get("output_tokens") or 0),
                f"{float(r.get('cost_thb') or 0):.4f}",
                int(r.get("elapsed_ms") or 0),
            ])
        from fastapi.responses import Response
        return Response(
            content="\ufeff" + buf.getvalue(),  # BOM 让 Excel 正确识别中文
            media_type="text/csv; charset=utf-8",
            headers={"Content-Disposition": f'attachment; filename="cost_log_{days}d.csv"'},
        )
    except Exception as e:
        logger.error(f"admin_cost_export failed: {e}")
        raise HTTPException(500, detail="admin.export_failed")


# ============================================================
# v108 · Google AI Studio 余额追踪 · 3 个 API 路由
# 半自动 · 管理员每周更新真实余额 · 系统自动校准
# ============================================================

class BalanceUpdateRequest(BaseModel):
    real_balance_thb: float = Field(..., ge=0, le=10_000_000)
    notes: Optional[str] = Field(None, max_length=500)
    calibration_factor: Optional[float] = Field(None, ge=0.5, le=2.0)


@app.get("/api/admin/billing/balance")
async def admin_get_balance(request: Request):
    """获取最新余额 + 估算 vs 真实对比 + 当前校准系数"""
    _require_super_admin(request)
    summary = db.get_balance_summary()
    # 拿当月估算总消耗(对照用)
    try:
        with db.get_cursor() as cur:
            cur.execute("""
                SELECT COALESCE(SUM(cost_thb), 0) AS month_estimated
                FROM ocr_cost_log
                WHERE date_trunc('month', created_at) = date_trunc('month', NOW())
            """)
            summary["month_estimated_thb"] = float(cur.fetchone()["month_estimated"] or 0)
    except Exception:
        summary["month_estimated_thb"] = 0
    # Google 跳转链接(直达 Billing)
    summary["google_billing_url"] = "https://aistudio.google.com/app/billing"
    return summary


@app.post("/api/admin/billing/balance")
async def admin_update_balance(req: BalanceUpdateRequest, request: Request):
    """管理员手动更新真实余额 · 系统自动算校准系数"""
    _require_super_admin(request)
    user = get_current_user_from_request(request)
    payload = req.model_dump() if hasattr(req, "model_dump") else req.dict()
    new_id = db.add_balance_log(
        real_balance=payload["real_balance_thb"],
        user_id=str(user["id"]),
        notes=payload.get("notes"),
        calibration_override=payload.get("calibration_factor"),
    )
    if not new_id:
        raise HTTPException(500, detail="billing.update_failed")
    summary = db.get_balance_summary()
    return {"ok": True, "id": new_id, "summary": summary}


@app.get("/api/admin/billing/history")
async def admin_balance_history(request: Request, limit: int = 20):
    """余额更新历史 · 看每次更新校准趋势"""
    _require_super_admin(request)
    try:
        with db.get_cursor() as cur:
            cur.execute("""
                SELECT id, real_balance_thb, estimated_used_since_last,
                       real_used_since_last, calibration_factor, notes, created_at
                FROM billing_balance_log
                ORDER BY created_at DESC
                LIMIT %s
            """, (max(1, min(int(limit), 100)),))
            rows = cur.fetchall()
        return {
            "history": [
                {
                    "id": int(r["id"]),
                    "real_balance_thb": float(r["real_balance_thb"]),
                    "estimated_used_since_last": float(r.get("estimated_used_since_last") or 0),
                    "real_used_since_last": float(r.get("real_used_since_last") or 0),
                    "calibration_factor": float(r.get("calibration_factor") or 1.0),
                    "notes": r.get("notes"),
                    "created_at": r["created_at"].isoformat(),
                }
                for r in rows
            ]
        }
    except Exception as e:
        logger.error(f"balance_history failed: {e}")
        raise HTTPException(500, detail="billing.history_failed")


# ============================================================
# v107 · 客户(Client)实体 API · 6 个路由
# 多客户事务所核心 · 用户登录后看自己的客户
# ============================================================

class ClientCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    short_name: Optional[str] = Field(None, max_length=80)
    tax_id: Optional[str] = Field(None, max_length=20)
    address: Optional[str] = Field(None, max_length=500)
    contact_person: Optional[str] = Field(None, max_length=100)
    contact_phone: Optional[str] = Field(None, max_length=50)
    contact_email: Optional[str] = Field(None, max_length=200)
    notes: Optional[str] = Field(None, max_length=1000)
    color: Optional[str] = Field(None, max_length=20)


class ClientUpdateRequest(BaseModel):
    name: Optional[str] = Field(None, max_length=200)
    short_name: Optional[str] = Field(None, max_length=80)
    tax_id: Optional[str] = Field(None, max_length=20)
    address: Optional[str] = Field(None, max_length=500)
    contact_person: Optional[str] = Field(None, max_length=100)
    contact_phone: Optional[str] = Field(None, max_length=50)
    contact_email: Optional[str] = Field(None, max_length=200)
    notes: Optional[str] = Field(None, max_length=1000)
    color: Optional[str] = Field(None, max_length=20)
    is_active: Optional[bool] = None


class AssignClientRequest(BaseModel):
    client_id: Optional[int] = None  # None 表示移除归属


def _serialize_client(c: dict) -> dict:
    """序列化客户 · 处理 datetime 等"""
    return {
        "id": int(c["id"]),
        "name": c.get("name"),
        "short_name": c.get("short_name"),
        "tax_id": c.get("tax_id"),
        "address": c.get("address"),
        "contact_person": c.get("contact_person"),
        "contact_phone": c.get("contact_phone"),
        "contact_email": c.get("contact_email"),
        "notes": c.get("notes"),
        "color": c.get("color") or "#3b82f6",
        "is_active": bool(c.get("is_active")),
        "invoice_count": int(c.get("invoice_count") or 0),
        "total_amount": float(c.get("total_amount") or 0),
        "last_invoice_at": c["last_invoice_at"].isoformat() if c.get("last_invoice_at") else None,
        "created_at": c["created_at"].isoformat() if c.get("created_at") else None,
    }


@app.get("/api/clients")
async def api_list_clients(request: Request, include_inactive: bool = False):
    """列出当前用户的所有客户"""
    user = get_current_user_from_request(request)
    rows = db.list_clients(str(user["id"]), include_inactive=include_inactive, tenant_id=_tid(user))
    # v118.28.1 · 员工分配过滤
    visible = db.get_visible_client_ids_for_user(user)
    if visible is not None:
        visible_set = set(visible)
        rows = [r for r in rows if int(r.get("id", 0)) in visible_set]
    return {"clients": [_serialize_client(r) for r in rows]}


@app.post("/api/clients")
async def api_create_client(req: ClientCreateRequest, request: Request):
    """创建新客户"""
    user = get_current_user_from_request(request)
    # v107.1 · 兼容 Pydantic v1/v2
    payload = req.model_dump() if hasattr(req, "model_dump") else req.dict()
    new_id = db.create_client(
        user_id=str(user["id"]),
        tenant_id=str(user.get("tenant_id")) if user.get("tenant_id") else None,
        **payload,
    )
    if not new_id:
        raise HTTPException(400, detail="client.create_failed")
    # v118.28.1 · 创建者自动获得分配(让员工身份创建客户后能看到)
    try:
        db.auto_assign_client_to_creator(str(user["id"]), int(new_id))
    except Exception as e:
        logger.warning(f"[client_create] auto_assign 失败: {e}")
    client = db.get_client(str(user["id"]), new_id, tenant_id=_tid(user))
    return {"ok": True, "client": _serialize_client(client) if client else {"id": new_id}}


@app.patch("/api/clients/{client_id}")
async def api_update_client(client_id: int, req: ClientUpdateRequest, request: Request):
    """更新客户信息"""
    user = get_current_user_from_request(request)
    # v107.1 · 兼容 Pydantic v1/v2
    raw = req.model_dump() if hasattr(req, "model_dump") else req.dict()
    payload = {k: v for k, v in raw.items() if v is not None}
    if not payload:
        raise HTTPException(400, detail="client.no_changes")
    ok = db.update_client(str(user["id"]), client_id, tenant_id=_tid(user), **payload)
    if not ok:
        raise HTTPException(404, detail="client.not_found")
    client = db.get_client(str(user["id"]), client_id, tenant_id=_tid(user))
    return {"ok": True, "client": _serialize_client(client) if client else None}


@app.delete("/api/clients/{client_id}")
async def api_delete_client(client_id: int, request: Request):
    """删除客户(级联解绑发票 · 不删发票)"""
    user = get_current_user_from_request(request)
    ok = db.delete_client(str(user["id"]), client_id, cascade_unlink=True, tenant_id=_tid(user))
    if not ok:
        raise HTTPException(404, detail="client.not_found")
    return {"ok": True}


@app.post("/api/history/{history_id}/assign_client")
async def api_assign_client(history_id: str, req: AssignClientRequest, request: Request):
    """把发票归属到客户 · client_id=null 表示取消归属"""
    user = get_current_user_from_request(request)
    # v118.28.1 · 员工:校验 client_id 在 visible_ids 内 · 否则 403(防员工把发票归到他不能看的客户)
    if req.client_id is not None:
        visible = db.get_visible_client_ids_for_user(user)
        if visible is not None and int(req.client_id) not in set(visible):
            raise HTTPException(403, detail="client.no_access")
    ok = db.assign_invoice_to_client(str(user["id"]), history_id, req.client_id, tenant_id=_tid(user))
    if not ok:
        raise HTTPException(400, detail="client.assign_failed")

    # 批 1 改动 1 (Zihao 2026-05-19 拍板 · v118.34.33) · 用户手动 assign 时 ·
    # 把 buyer_name + buyer_tax → client_id 的关系学进 buyer_to_client_memory ·
    # 下次 OCR 出同 buyer 就 auto-resolve · 不用每次手动选.
    if req.client_id is not None:
        try:
            h = db.get_ocr_history_detail(
                str(user["id"]), history_id, tenant_id=_tid(user),
            )
            if h:
                _pages = h.get("pages") or []
                _primary = next(
                    (p for p in _pages
                     if isinstance(p, dict)
                     and not p.get("is_duplicate")
                     and not p.get("is_copy")),
                    _pages[0] if _pages else {},
                )
                _f = (_primary or {}).get("fields") or {}
                _buyer_name = _f.get("buyer_name") or ""
                _buyer_tax = _f.get("buyer_tax") or ""
                if _buyer_name:
                    db.learn_buyer_to_client(
                        _buyer_name, _buyer_tax, int(req.client_id),
                        str(user["id"]), tenant_id=_tid(user),
                    )
                    logger.info(
                        "[assign_client] learned buyer→client: %r → %s",
                        _buyer_name[:40], req.client_id,
                    )
        except Exception as e:
            logger.warning(f"learn buyer→client failed (history={history_id[:8]}): {e}")

    return {"ok": True}


@app.get("/api/clients/{client_id}/export")
async def api_export_client_invoices(client_id: int, request: Request,
                                       month: Optional[str] = None):
    """按客户导出发票 Excel(VAT 报表格式)
    month 格式 · YYYY-MM(默认本月)· 不带 month 参数则导出全部
    v108.3 · 防御性加固 + 详细日志
    """
    user = get_current_user_from_request(request)
    # 验证客户属于该用户/tenant
    client = db.get_client(str(user["id"]), client_id, tenant_id=_tid(user))
    if not client:
        raise HTTPException(404, detail="client.not_found")
    
    # 月份过滤 · 空 / "all" 表示全部
    if month and month.lower() == "all":
        month = None
    if not month:
        # 默认导出最近 90 天(更宽容 · 而不是仅本月)
        month = None
    
    try:
        # v118.15 · tenant 共享:同 tenant 内任意成员对该客户识别的发票都算
        tid = _tid(user)
        if tid:
            user_filter_sql = "h.user_id IN (SELECT id FROM users WHERE tenant_id = %s)"
            user_filter_param = tid
        else:
            user_filter_sql = "h.user_id = %s"
            user_filter_param = str(user["id"])
        with db.get_cursor() as cur:
            if month:
                # 按月份过滤 · 同时兼容 invoice_date 为 NULL 的情况(用 created_at fallback)
                cur.execute(f"""
                    SELECT h.id, h.invoice_no, h.invoice_date, h.seller_name, 
                           h.total_amount, h.filename, h.created_at
                    FROM ocr_history h
                    WHERE h.client_id = %s AND {user_filter_sql}
                      AND (
                          (h.invoice_date IS NOT NULL AND TO_CHAR(h.invoice_date, 'YYYY-MM') = %s)
                          OR (h.invoice_date IS NULL AND TO_CHAR(h.created_at, 'YYYY-MM') = %s)
                      )
                    ORDER BY h.invoice_date ASC NULLS LAST, h.created_at ASC
                """, (client_id, user_filter_param, month, month))
            else:
                # 不过滤月份 · 全部
                cur.execute(f"""
                    SELECT h.id, h.invoice_no, h.invoice_date, h.seller_name, 
                           h.total_amount, h.filename, h.created_at
                    FROM ocr_history h
                    WHERE h.client_id = %s AND {user_filter_sql}
                    ORDER BY h.invoice_date ASC NULLS LAST, h.created_at ASC
                """, (client_id, user_filter_param))
            rows = cur.fetchall()
        
        logger.info(f"[client_export] client_id={client_id} month={month} rows={len(rows)}")
        
        # 拼 CSV(Excel 兼容)
        import io, csv
        buf = io.StringIO()
        w = csv.writer(buf)
        title_month = month or "All"
        w.writerow([f"客户:{client.get('name', '')} · 月份:{title_month}"])
        w.writerow([f"税号:{client.get('tax_id') or '—'} · 共 {len(rows)} 张"])
        w.writerow([])
        w.writerow(["序号", "发票日期", "发票号", "卖方", "金额(THB)", "文件名"])
        total = 0.0
        for i, r in enumerate(rows, 1):
            try:
                amount = float(r["total_amount"]) if r.get("total_amount") is not None else 0.0
            except Exception:
                amount = 0.0
            total += amount
            # invoice_date 是 date 对象时 strftime · 是字符串/None 时直接用
            inv_date = ""
            if r.get("invoice_date"):
                try:
                    inv_date = r["invoice_date"].strftime("%Y-%m-%d")
                except AttributeError:
                    inv_date = str(r["invoice_date"])[:10]
            w.writerow([
                i,
                inv_date,
                r.get("invoice_no") or "",
                r.get("seller_name") or "",
                f"{amount:.2f}",
                r.get("filename") or "",
            ])
        w.writerow([])
        w.writerow(["合计", "", "", "", f"{total:.2f}"])
        from fastapi.responses import Response
        client_name_safe = (client.get("name") or "client").replace("/", "_")[:50]
        # ASCII 安全的 filename(中泰文用 RFC 5987 filename* 编码)
        import urllib.parse as _up
        ascii_name = "client_export"
        encoded = _up.quote(f"{client_name_safe}_{title_month}.csv")
        return Response(
            content="\ufeff" + buf.getvalue(),
            media_type="text/csv; charset=utf-8",
            headers={
                "Content-Disposition": f"attachment; filename=\"{ascii_name}.csv\"; filename*=UTF-8''{encoded}"
            },
        )
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        logger.error(f"export_client_invoices failed: {e}\n{traceback.format_exc()}")
        raise HTTPException(500, detail=f"client.export_failed: {str(e)[:200]}")


@app.post("/api/admin/tenants")
async def admin_create_tenant(req: AdminCreateTenantRequest, request: Request):
    """创建新租户 · 仅超管"""
    _require_super_admin(request)
    tenant_id = db.create_tenant(
        name=req.name,
        tenant_type=req.tenant_type,
        monthly_quota=req.monthly_quota,
        notes=req.notes,
    )
    if not tenant_id:
        raise HTTPException(500, detail="admin.create_tenant_failed")
    return {"ok": True, "tenant_id": tenant_id}


@app.patch("/api/admin/tenants/{tenant_id}/quota")
async def admin_update_tenant_quota(tenant_id: str, req: AdminUpdateTenantQuotaRequest, request: Request):
    """改租户限额 · 仅超管"""
    _require_super_admin(request)
    ok = db.update_tenant_quota(tenant_id, req.monthly_quota)
    if not ok:
        raise HTTPException(404, detail="admin.tenant_not_found")
    return {"ok": True}


@app.patch("/api/admin/tenants/{tenant_id}/status")
async def admin_update_tenant_status(tenant_id: str, req: AdminUpdateTenantStatusRequest, request: Request):
    """改租户状态 · 仅超管"""
    _require_super_admin(request)
    ok = db.update_tenant_status(tenant_id, req.status)
    if not ok:
        raise HTTPException(404, detail="admin.tenant_not_found")
    return {"ok": True}


@app.get("/api/admin/tenants/{tenant_id}/summary")
async def admin_tenant_summary(tenant_id: str, request: Request):
    """租户运营概况 · 仅超管"""
    _require_super_admin(request)
    tenant = db.get_tenant(tenant_id)
    if not tenant:
        raise HTTPException(404, detail="admin.tenant_not_found")
    summary = db.get_tenant_usage_summary(tenant_id)
    members = db.list_tenant_members(tenant_id)
    return {
        "tenant": {
            "id": str(tenant["id"]),
            "name": tenant.get("name"),
            "tenant_type": tenant.get("tenant_type"),
            "status": tenant.get("status"),
            "monthly_quota": int(tenant.get("monthly_quota") or 0),
            "notes": tenant.get("notes"),
        },
        "summary": summary,
        "members": [
            {
                "id": str(m["id"]),
                "username": m.get("username"),
                "email": m.get("email"),
                "role": m.get("role"),
                "is_active": m.get("is_active"),
                "is_super_admin": m.get("is_super_admin"),
                "last_login_at": m["last_login_at"].isoformat() if m.get("last_login_at") else None,
                "created_at": m["created_at"].isoformat() if m.get("created_at") else None,
            }
            for m in members
        ],
    }


@app.get("/api/me/tenant-usage")
async def get_my_tenant_usage(request: Request):
    """
    当前登录用户查看自己租户的本月用量(给限额仪表盘用)
    所有用户都能调 · 只查自己的租户
    """
    user = get_current_user_from_request(request)
    tenant_id = user.get("tenant_id")
    if not tenant_id:
        # 没挂租户 · 返回空
        return {"has_tenant": False}
    summary = db.get_tenant_usage_summary(str(tenant_id))
    tenant = db.get_tenant(str(tenant_id))
    return {
        "has_tenant": True,
        "tenant_name": tenant.get("name") if tenant else None,
        "tenant_type": tenant.get("tenant_type") if tenant else None,
        "tenant_status": tenant.get("status") if tenant else None,
        "quota": summary["quota"],
        "user_count": summary["user_count"],
        "ocr_this_month": summary["ocr_this_month"],
    }


# ============================================================
# v23 · 用户管理(超管)· 员工管理(老板)· 操作日志
# ============================================================

class AdminCreateUserRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, pattern="^[a-zA-Z0-9_.-]+$")
    password: str = Field(..., min_length=6, max_length=100)
    company_name: str = Field(..., min_length=1, max_length=200)
    tenant_type: str = Field("shared_api", pattern="^(shared_api|byo_api)$")
    monthly_quota: int = Field(100, ge=0)
    notes: Optional[str] = None


class AdminVerifyPasswordRequest(BaseModel):
    password: str


class AdminDeleteUserRequest(BaseModel):
    password: str  # 超管自己的密码确认
    confirm_username: str  # 要删除用户的用户名(再次核对)


class AdminResetPasswordRequest(BaseModel):
    new_password: str = Field(..., min_length=6, max_length=100)


class EmployeeAddRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, pattern="^[a-zA-Z0-9_.-]+$")
    password: str = Field(..., min_length=6, max_length=100)
    # v118.11 · 邮箱选填 · 用于员工自助忘记密码
    email: Optional[str] = Field(None, max_length=200)


class EmployeeToggleRequest(BaseModel):
    is_active: bool


def _log_op(request: Request, user, action, target_type=None, target_id=None, target_name=None, details=None):
    """记操作日志的便捷函数"""
    try:
        db.insert_operation_log(
            tenant_id=str(user["tenant_id"]) if user.get("tenant_id") else None,
            actor_user_id=str(user["id"]),
            actor_username=user.get("username"),
            actor_is_super=bool(user.get("is_super_admin")),
            action=action,
            target_type=target_type,
            target_id=target_id,
            target_name=target_name,
            details=details,
            ip=_get_client_ip(request),
            ua=request.headers.get("User-Agent", "")[:300],
        )
    except Exception as e:
        logger.warning(f"_log_op failed: {e}")


def _get_client_ip(request):
    xff = request.headers.get("X-Forwarded-For", "")
    if xff:
        return xff.split(",")[0].strip()
    return request.client.host if request.client else None


# 列出所有 owner 用户(超管)
@app.get("/api/admin/users")
async def admin_list_users(request: Request):
    """v118.12 · 仅返回客户(owner / 老数据 role NULL) · 员工走 /api/admin/employees"""
    _require_super_admin(request)
    import db as _db
    rows = []
    try:
        with _db.get_cursor() as cur:
            cur.execute("""
                SELECT
                    u.id           AS user_id,
                    u.username,
                    u.email,
                    COALESCE(u.company_name, t.name)   AS company_name,
                    u.tenant_id,
                    t.tenant_type,
                    t.status       AS tenant_status,
                    u.plan         AS plan,
                    t.monthly_quota AS tenant_quota,
                    t.used_this_month AS tenant_used,
                    t.subscription_expires_at,
                    u.is_active,
                    u.signup_country AS country,
                    u.last_login_at,
                    u.created_at,
                    (SELECT COUNT(*) FROM users e WHERE e.tenant_id = u.tenant_id AND e.role = 'member' AND COALESCE(e.is_active, true) = true) AS employees_count
                FROM users u
                LEFT JOIN tenants t ON t.id = u.tenant_id
                WHERE (u.role = 'owner' OR u.role IS NULL)
                  AND COALESCE(u.is_super_admin, false) = false
                ORDER BY u.created_at DESC NULLS LAST
                LIMIT 500
            """)
            db_rows = cur.fetchall()
        for r in db_rows:
            tenant_plan = r.get("plan") or "free"
            rows.append({
                "user_id": str(r["user_id"]),
                "id": str(r["user_id"]),                      # v118.12.1 · 兼容前端 u.id 字段
                "username": r.get("username"),
                "email": r.get("email"),
                "company_name": r.get("company_name"),
                "tenant_id": str(r["tenant_id"]) if r.get("tenant_id") else None,
                "tenant_type": r.get("tenant_type"),
                "tenant_status": r.get("tenant_status"),
                "plan": tenant_plan,                          # v118.12 · 客户列表用 user.plan(实际套餐字段)
                "is_active": r.get("is_active"),
                "country": r.get("country"),
                "monthly_quota": int(r.get("tenant_quota") or 0),
                "used_this_month": int(r.get("tenant_used") or 0),
                "employees_count": int(r.get("employees_count") or 0),
                "trial_expires_at": r["subscription_expires_at"].isoformat() if r.get("subscription_expires_at") else None,
                "subscription_expires_at": r["subscription_expires_at"].isoformat() if r.get("subscription_expires_at") else None,
                "last_login_at": r["last_login_at"].isoformat() if r.get("last_login_at") else None,
                "created_at": r["created_at"].isoformat() if r.get("created_at") else None,
            })
    except Exception as e:
        logger.error(f"admin_list_users: {e}")
        raise HTTPException(500, detail="admin.list_failed")
    return {"users": rows, "total": len(rows)}


@app.get("/api/admin/employees")
async def admin_list_employees(request: Request):
    """v118.12 · 超管查所有员工(role=member) · 显示属于哪个老板/事务所"""
    _require_super_admin(request)
    import db as _db
    rows = []
    try:
        with _db.get_cursor() as cur:
            cur.execute("""
                SELECT
                    e.id           AS employee_id,
                    e.username,
                    e.email,
                    e.tenant_id,
                    e.is_active,
                    e.last_login_at,
                    e.created_at,
                    t.name         AS tenant_name,
                    (SELECT plan FROM users WHERE tenant_id = t.id AND role = 'owner' LIMIT 1) AS tenant_plan,
                    o.id           AS owner_id,
                    o.username     AS owner_username,
                    o.email        AS owner_email
                FROM users e
                LEFT JOIN tenants t ON t.id = e.tenant_id
                LEFT JOIN users o   ON o.tenant_id = e.tenant_id AND o.role = 'owner'
                WHERE e.role = 'member'
                  AND COALESCE(e.is_super_admin, false) = false
                ORDER BY t.name NULLS LAST, e.created_at DESC NULLS LAST
                LIMIT 1000
            """)
            db_rows = cur.fetchall()
        for r in db_rows:
            rows.append({
                "employee_id": str(r["employee_id"]),
                "username": r.get("username"),
                "email": r.get("email"),
                "tenant_id": str(r["tenant_id"]) if r.get("tenant_id") else None,
                "tenant_name": r.get("tenant_name"),
                "tenant_plan": r.get("tenant_plan"),
                "owner_id": str(r["owner_id"]) if r.get("owner_id") else None,
                "owner_username": r.get("owner_username"),
                "owner_email": r.get("owner_email"),
                "is_active": r.get("is_active"),
                "last_login_at": r["last_login_at"].isoformat() if r.get("last_login_at") else None,
                "created_at": r["created_at"].isoformat() if r.get("created_at") else None,
            })
    except Exception as e:
        logger.error(f"admin_list_employees: {e}")
        raise HTTPException(500, detail="admin.list_failed")
    return {"employees": rows, "total": len(rows)}


# 创建用户(超管)· 同时建 tenant + owner
@app.post("/api/admin/users")
async def admin_create_user(req: AdminCreateUserRequest, request: Request):
    admin = _require_super_admin(request)
    result = db.create_owner_user(
        username=req.username,
        password=req.password,
        company_name=req.company_name,
        tenant_type=req.tenant_type,
        monthly_quota=req.monthly_quota,
        notes=req.notes,
    )
    if not result.get("ok"):
        err = result.get("error", "create_failed")
        if err == "username_exists":
            raise HTTPException(409, detail="admin.username_exists")
        raise HTTPException(400, detail="admin.create_failed")
    _log_op(request, admin, "user.create", "user", result["user_id"], req.username,
            {"company_name": req.company_name, "tenant_type": req.tenant_type, "quota": req.monthly_quota})
    return {"ok": True, "user_id": result["user_id"], "tenant_id": result["tenant_id"]}


# 用户详情(超管)· v118.12.5 · 平铺字段 + 扩展信息 · 让前端 drawer 能渲染完整
@app.get("/api/admin/users/{user_id}")
async def admin_user_detail(user_id: str, request: Request):
    _require_super_admin(request)
    user = db.find_user_by_id(user_id)
    if not user:
        raise HTTPException(404, detail="admin.user_not_found")
    tenant = db.get_tenant(str(user["tenant_id"])) if user.get("tenant_id") else None
    employees = db.list_employees(str(user["tenant_id"])) if user.get("tenant_id") else []

    # 累计 OCR · 最近识别 · 付款次数
    cumulative_ocr = 0
    last_ocr_at = None
    payment_count = 0
    last_payment_at = None
    try:
        import db as _db
        with _db.get_cursor() as cur:
            cur.execute("SELECT COUNT(*) AS n, MAX(created_at) AS last FROM ocr_history WHERE user_id = %s", (user_id,))
            r = cur.fetchone()
            if r:
                cumulative_ocr = int(r.get("n") or 0) if isinstance(r, dict) else int(r[0] or 0)
                last_raw = r.get("last") if isinstance(r, dict) else r[1]
                last_ocr_at = last_raw.isoformat() if last_raw else None
            try:
                cur.execute("SELECT COUNT(*) AS n, MAX(created_at) AS last FROM payment_log WHERE user_id = %s AND status = 'approved'", (user_id,))
                r2 = cur.fetchone()
                if r2:
                    payment_count = int(r2.get("n") or 0) if isinstance(r2, dict) else int(r2[0] or 0)
                    last_pay_raw = r2.get("last") if isinstance(r2, dict) else r2[1]
                    last_payment_at = last_pay_raw.isoformat() if last_pay_raw else None
            except Exception:
                pass  # payment_log 表可能不存在 · 静默兜底
    except Exception as _ee:
        logger.warning(f"admin_user_detail aux failed: {_ee}")

    return {
        # 平铺 user 字段 · 让前端 u.email / u.phone 等直接 work
        "id": str(user["id"]),
        "user_id": str(user["id"]),
        "username": user.get("username"),
        "email": user.get("email"),
        "phone": user.get("phone"),
        "line_id": user.get("line_id"),
        "line_user_id": user.get("line_user_id"),
        "country": user.get("country") or user.get("signup_country"),
        "signup_country": user.get("signup_country"),
        "company_name": user.get("company_name") or (tenant.get("name") if tenant else None),
        "full_name": user.get("full_name"),
        "role": user.get("role"),
        "is_active": user.get("is_active"),
        "is_super_admin": bool(user.get("is_super_admin")),
        "plan": user.get("plan") or "free",
        "monthly_volume": user.get("monthly_volume"),
        "monthly_quota": int(user.get("monthly_quota") or 0),
        "used_this_month": int(user.get("used_this_month") or 0),
        "cumulative_ocr": cumulative_ocr,
        "last_ocr_at": last_ocr_at,
        "payment_count": payment_count,
        "last_payment_at": last_payment_at,
        "trial_expires_at": str(user["trial_expires_at"]) if user.get("trial_expires_at") else None,
        "expires_at": str(user["expires_at"]) if user.get("expires_at") else None,
        "last_login_at": user["last_login_at"].isoformat() if user.get("last_login_at") else None,
        "created_at": user["created_at"].isoformat() if user.get("created_at") else None,
        "signup_ip": user.get("signup_ip") or user.get("registration_ip"),
        "device_fingerprint": user.get("device_fingerprint"),
        "has_risk_signal": bool(user.get("is_suspicious") or user.get("risk_score", 0) > 0),
        # tenant 信息(嵌套)
        "tenant_id": str(user["tenant_id"]) if user.get("tenant_id") else None,
        "tenant": {
            "id": str(tenant["id"]) if tenant else None,
            "name": tenant.get("name") if tenant else None,
            "tenant_type": tenant.get("tenant_type") if tenant else None,
            "status": tenant.get("status") if tenant else None,
            "monthly_quota": int(tenant.get("monthly_quota") or 0) if tenant else 0,
            "used_this_month": int(tenant.get("used_this_month") or 0) if tenant else 0,
            "notes": tenant.get("notes") if tenant else None,
        } if tenant else None,
        "tenant_name": tenant.get("name") if tenant else None,
        "tenant_type": tenant.get("tenant_type") if tenant else None,
        "tenant_status": tenant.get("status") if tenant else None,
        "tenant_quota": int(tenant.get("monthly_quota") or 0) if tenant else 0,
        "tenant_used": int(tenant.get("used_this_month") or 0) if tenant else 0,
        # 员工列表(老板视角看自己的员工)
        "employees": [
            {
                "id": str(e["id"]),
                "username": e.get("username"),
                "email": e.get("email"),
                "role": e.get("role"),
                "is_active": e.get("is_active"),
                "last_login_at": e["last_login_at"].isoformat() if e.get("last_login_at") else None,
                "created_at": e["created_at"].isoformat() if e.get("created_at") else None,
            } for e in employees
        ],
    }


# 改配额(超管)· tenant_id 路径可从用户详情得到 · 但这里简化 · 按 user_id
@app.patch("/api/admin/users/{user_id}/quota")
async def admin_update_user_quota(user_id: str, req: AdminUpdateTenantQuotaRequest, request: Request):
    admin = _require_super_admin(request)
    user = db.find_user_by_id(user_id)
    if not user or not user.get("tenant_id"):
        raise HTTPException(404, detail="admin.user_not_found")
    ok = db.update_tenant_quota(str(user["tenant_id"]), req.monthly_quota)
    if not ok:
        raise HTTPException(500, detail="admin.update_failed")
    _log_op(request, admin, "user.update_quota", "user", user_id, user.get("username"),
            {"new_quota": req.monthly_quota})
    return {"ok": True}


# 改状态(超管)
@app.patch("/api/admin/users/{user_id}/status")
async def admin_update_user_status(user_id: str, req: AdminUpdateTenantStatusRequest, request: Request):
    admin = _require_super_admin(request)
    user = db.find_user_by_id(user_id)
    if not user or not user.get("tenant_id"):
        raise HTTPException(404, detail="admin.user_not_found")
    ok = db.update_tenant_status(str(user["tenant_id"]), req.status)
    if not ok:
        raise HTTPException(500, detail="admin.update_failed")
    _log_op(request, admin, "user.update_status", "user", user_id, user.get("username"),
            {"new_status": req.status})
    return {"ok": True}


# 删除用户(超管)· 级联删所有数据 · 要求密码确认
@app.post("/api/admin/users/{user_id}/delete")
async def admin_delete_user(user_id: str, req: AdminDeleteUserRequest, request: Request):
    admin = _require_super_admin(request)

    # 1. 验证超管密码
    if not db.verify_user_password(str(admin["id"]), req.password):
        raise HTTPException(403, detail="admin.wrong_password")

    # 2. 确认用户名匹配
    user = db.find_user_by_id(user_id)
    if not user:
        raise HTTPException(404, detail="admin.user_not_found")
    if user.get("username") != req.confirm_username:
        raise HTTPException(400, detail="admin.username_mismatch")
    if user.get("is_super_admin"):
        raise HTTPException(400, detail="admin.cant_delete_super")

    # 3. 级联删
    ok = db.delete_owner_user_cascade(user_id)
    if not ok:
        raise HTTPException(500, detail="admin.delete_failed")
    _log_op(request, admin, "user.delete", "user", user_id, user.get("username"),
            {"company_name": user.get("company_name")})
    return {"ok": True}


# 重置密码(超管)
@app.post("/api/admin/users/{user_id}/reset-password")
async def admin_reset_user_password(user_id: str, request: Request):
    """v118.28.7 · 砍 · 大厂惯例(Xero/QuickBooks/Stripe)超管不碰客户密码
       客户忘密码请走登录页「忘记密码」自助 · 邮箱也丢了走身份验证申诉(人工流程)"""
    _require_super_admin(request)
    raise HTTPException(410, detail="admin.password_reset_removed")


# 查某用户(tenant)的操作日志
@app.get("/api/admin/users/{user_id}/logs")
async def admin_user_logs(user_id: str, request: Request):
    _require_super_admin(request)
    user = db.find_user_by_id(user_id)
    if not user:
        raise HTTPException(404, detail="admin.user_not_found")
    logs = db.list_operation_logs(tenant_id=str(user["tenant_id"]) if user.get("tenant_id") else None, limit=200)
    return {
        "logs": [
            {
                "id": l["id"],
                "actor_username": l.get("actor_username"),
                "actor_is_super": l.get("actor_is_super"),
                "action": l.get("action"),
                "target_type": l.get("target_type"),
                "target_name": l.get("target_name"),
                "details": l.get("details"),
                "ip": l.get("ip"),
                "created_at": l["created_at"].isoformat() if l.get("created_at") else None,
            } for l in logs
        ],
        "total": len(logs),
    }


# 全局操作日志(超管)
@app.get("/api/admin/logs")
async def admin_global_logs(
    request: Request,
    page: int = 1,
    per_page: int = 50,
    q: str = "",
    action: str = "",
    date_from: str = "",
    date_to: str = "",
):
    """v118.29.0 · 分页 + 搜索 + 时间过滤"""
    _require_super_admin(request)
    res = db.list_operation_logs_paged(
        tenant_id=None,
        page=page, per_page=per_page,
        q=q or None, action=action or None,
        date_from=date_from or None, date_to=date_to or None,
    )
    return {
        "logs": [
            {
                "id": l["id"],
                "tenant_id": str(l["tenant_id"]) if l.get("tenant_id") else None,
                "actor_username": l.get("actor_username"),
                "actor_is_super": l.get("actor_is_super"),
                "action": l.get("action"),
                "target_type": l.get("target_type"),
                "target_name": l.get("target_name"),
                "details": l.get("details"),
                "ip": l.get("ip"),
                "created_at": l["created_at"].isoformat() if l.get("created_at") else None,
            } for l in res["rows"]
        ],
        "total": res["total"],
        "page": res["page"],
        "per_page": res["per_page"],
    }


# v118.29.0 · 操作日志 CSV 导出(超管 · 当前 filter 全部 · 上限 5000)
@app.get("/api/admin/logs.csv")
async def admin_logs_csv(
    request: Request,
    q: str = "",
    action: str = "",
    date_from: str = "",
    date_to: str = "",
):
    _require_super_admin(request)
    res = db.list_operation_logs_paged(
        tenant_id=None,
        q=q or None, action=action or None,
        date_from=date_from or None, date_to=date_to or None,
        limit_all=5000,
    )
    import csv as _csv
    from io import StringIO as _StringIO
    buf = _StringIO()
    buf.write("\ufeff")  # BOM · Excel 中文不乱码
    w = _csv.writer(buf)
    w.writerow(["created_at", "actor_username", "actor_is_super", "action", "target_type", "target_name", "tenant_id", "ip", "details"])
    for l in res["rows"]:
        w.writerow([
            l["created_at"].isoformat() if l.get("created_at") else "",
            l.get("actor_username") or "",
            "1" if l.get("actor_is_super") else "0",
            l.get("action") or "",
            l.get("target_type") or "",
            l.get("target_name") or "",
            str(l["tenant_id"]) if l.get("tenant_id") else "",
            l.get("ip") or "",
            json.dumps(l.get("details"), ensure_ascii=False) if l.get("details") else "",
        ])
    from fastapi.responses import Response as _Resp
    return _Resp(
        content=buf.getvalue(),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="pearnly_logs.csv"'}
    )


# ============================================================
# v118.28.8 · 客户老板查 Pearnly 访问日志(对齐 Xero/QuickBooks Audit log)
# 仅返回 actor_is_super=true 的操作 · 让客户能审计 Pearnly 内部员工的访问
# ============================================================
@app.get("/api/me/access_log")
async def me_access_log(
    request: Request,
    page: int = 1,
    per_page: int = 50,
    q: str = "",
):
    user = get_current_user_from_request(request)
    # 只 owner / super admin 可看
    role = user.get("role") or "owner"
    if role != "owner" and not user.get("is_super_admin"):
        raise HTTPException(403, detail="me.access_log_owner_only")
    tenant_id = str(user["tenant_id"]) if user.get("tenant_id") else None
    if not tenant_id:
        return {"logs": [], "total": 0, "page": 1, "per_page": per_page}

    res = db.list_operation_logs_paged(
        tenant_id=tenant_id,
        page=page, per_page=per_page,
        q=q or None,
        actor_is_super=True,  # 关键 · 只看 Pearnly 超管的操作
    )
    return {
        "logs": [
            {
                "id": l["id"],
                "actor_username": l.get("actor_username"),
                "action": l.get("action"),
                "target_type": l.get("target_type"),
                "target_name": l.get("target_name"),
                "details": l.get("details"),
                "ip": l.get("ip"),
                "created_at": l["created_at"].isoformat() if l.get("created_at") else None,
            } for l in res["rows"]
        ],
        "total": res["total"],
        "page": res["page"],
        "per_page": res["per_page"],
    }


@app.get("/api/me/access_log.csv")
async def me_access_log_csv(request: Request, q: str = ""):
    user = get_current_user_from_request(request)
    role = user.get("role") or "owner"
    if role != "owner" and not user.get("is_super_admin"):
        raise HTTPException(403, detail="me.access_log_owner_only")
    tenant_id = str(user["tenant_id"]) if user.get("tenant_id") else None
    if not tenant_id:
        from fastapi.responses import Response as _Resp
        return _Resp(content="\ufeff", media_type="text/csv; charset=utf-8")

    res = db.list_operation_logs_paged(
        tenant_id=tenant_id,
        q=q or None,
        actor_is_super=True,
        limit_all=5000,
    )
    import csv as _csv
    from io import StringIO as _StringIO
    buf = _StringIO()
    buf.write("\ufeff")
    w = _csv.writer(buf)
    w.writerow(["created_at", "actor_username", "action", "target_type", "target_name", "ip", "details"])
    for l in res["rows"]:
        w.writerow([
            l["created_at"].isoformat() if l.get("created_at") else "",
            l.get("actor_username") or "",
            l.get("action") or "",
            l.get("target_type") or "",
            l.get("target_name") or "",
            l.get("ip") or "",
            json.dumps(l.get("details"), ensure_ascii=False) if l.get("details") else "",
        ])
    from fastapi.responses import Response as _Resp
    return _Resp(
        content=buf.getvalue(),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="pearnly_access_log.csv"'}
    )


# v118.29.0 · 客户列表 CSV 导出(超管 · 当前 filter 全部 · 上限 5000)
@app.get("/api/admin/users.csv")
async def admin_users_csv(request: Request):
    _require_super_admin(request)
    import db as _db
    rows = []
    try:
        with _db.get_cursor() as cur:
            cur.execute("""
                SELECT
                    u.id           AS user_id,
                    u.username,
                    u.email,
                    COALESCE(u.company_name, t.name)   AS company_name,
                    u.tenant_id,
                    t.tenant_type,
                    t.status       AS tenant_status,
                    u.plan         AS plan,
                    t.monthly_quota AS tenant_quota,
                    t.used_this_month AS tenant_used,
                    t.subscription_expires_at,
                    u.is_active,
                    u.signup_country AS country,
                    u.last_login_at,
                    u.created_at,
                    (SELECT COUNT(*) FROM users e WHERE e.tenant_id = u.tenant_id AND e.role = 'member' AND COALESCE(e.is_active, true) = true) AS employees_count
                FROM users u
                LEFT JOIN tenants t ON t.id = u.tenant_id
                WHERE (u.role = 'owner' OR u.role IS NULL)
                  AND COALESCE(u.is_super_admin, false) = false
                ORDER BY u.created_at DESC NULLS LAST
                LIMIT 5000
            """)
            rows = cur.fetchall()
    except Exception as e:
        logger.error(f"admin_users_csv: {e}")
        raise HTTPException(500, detail="admin.csv_failed")

    import csv as _csv
    from io import StringIO as _StringIO
    buf = _StringIO()
    buf.write("\ufeff")
    w = _csv.writer(buf)
    w.writerow(["created_at", "username", "email", "company_name", "country", "plan",
                "tenant_status", "is_active", "monthly_quota", "used_this_month",
                "employees_count", "subscription_expires_at", "last_login_at", "tenant_id"])
    for r in rows:
        w.writerow([
            r["created_at"].isoformat() if r.get("created_at") else "",
            r.get("username") or "",
            r.get("email") or "",
            r.get("company_name") or "",
            r.get("country") or "",
            r.get("plan") or "free",
            r.get("tenant_status") or "",
            "1" if r.get("is_active") else "0",
            int(r.get("tenant_quota") or 0),
            int(r.get("tenant_used") or 0),
            int(r.get("employees_count") or 0),
            r["subscription_expires_at"].isoformat() if r.get("subscription_expires_at") else "",
            r["last_login_at"].isoformat() if r.get("last_login_at") else "",
            str(r["tenant_id"]) if r.get("tenant_id") else "",
        ])
    from fastapi.responses import Response as _Resp
    return _Resp(
        content=buf.getvalue(),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="pearnly_users.csv"'}
    )


# ============================================================
# 员工管理(老板用)
# ============================================================

# v118.11 · 弱密码黑名单 + 强度校验(共享给员工创建/重置/首登改密)
_WEAK_PASSWORDS = {
    "111111", "112233", "121212", "123123", "123321", "123456", "1234567",
    "12345678", "123456789", "1234567890", "131313", "147258", "159753",
    "654321", "666666", "888888", "987654", "abc123", "abcd1234", "admin",
    "admin123", "iloveyou", "letmein", "monkey", "password", "password1",
    "password123", "qazwsx", "qwerty", "qwerty123", "qwertyuiop", "welcome",
    "zxcvbnm",
}


def _check_password_strength(password: str) -> Optional[str]:
    """
    返回 None 表示通过 · 返回错误 code 表示拒绝
    code: pwd.too_short / pwd.too_weak_numeric / pwd.too_weak_common / pwd.too_weak
    """
    if not password or len(password) < 8:
        return "pwd.too_short"
    if password.lower() in _WEAK_PASSWORDS:
        return "pwd.too_weak_common"
    if password.isdigit():
        return "pwd.too_weak_numeric"
    has_letter = any(c.isalpha() for c in password)
    has_digit = any(c.isdigit() for c in password)
    if not (has_letter and has_digit):
        return "pwd.too_weak"
    return None


def _require_owner_or_super(request: Request) -> Dict[str, Any]:
    """老板或超管
    v118.26.2.4 · BUG 4 修补:新注册老板 tenant_id=NULL · 加员工时被拒
    懒建模式:首次需要 tenant 时自动建一个 + 回填 user.tenant_id · 不影响新签名 API
    """
    user = get_current_user_from_request(request)
    if user.get("is_super_admin"):
        return user
    if user.get("role") != "owner":
        raise HTTPException(403, detail="team.only_owner_or_super")
    if not user.get("tenant_id"):
        # v118.26.2.4 · 懒建 tenant · 只在首次需要时
        try:
            tenant_name = (user.get("company_name")
                           or user.get("full_name")
                           or user.get("username")
                           or f"user_{str(user['id'])[:8]}")[:100]
            new_tid = db.create_tenant(
                name=tenant_name,
                owner_user_id=str(user["id"]),
                tenant_type="shared_api",
                monthly_quota=100,
                notes="auto-created on first owner action",
            )
            if new_tid:
                with db.get_cursor(commit=True) as _cur:
                    _cur.execute(
                        "UPDATE users SET tenant_id = %s WHERE id = %s AND tenant_id IS NULL",
                        (new_tid, str(user["id"])),
                    )
                user["tenant_id"] = new_tid
                logger.info(f"[v118.26.2.4 lazy-tenant] +tenant {new_tid[:8]}.. for user {user.get('username')!r}")
        except Exception as _e:
            logger.error(f"_require_owner_or_super lazy-tenant fail: {_e}")
            raise HTTPException(500, detail="team.tenant_create_failed")
        if not user.get("tenant_id"):
            raise HTTPException(400, detail="team.no_tenant")
    return user


# 列员工
@app.get("/api/team/employees")
async def team_list_employees(request: Request):
    owner = _require_owner_or_super(request)
    employees = db.list_employees(str(owner["tenant_id"]))
    # v118.28.1 · 顺手把每个员工已分配的客户数带上(团队卡片显示用)
    assignments = db.list_assignments_by_employees(str(owner["tenant_id"]))
    return {
        "employees": [
            {
                "id": str(e["id"]),
                "username": e.get("username"),
                "role": e.get("role"),
                "is_active": e.get("is_active"),
                "last_login_at": e["last_login_at"].isoformat() if e.get("last_login_at") else None,
                "created_at": e["created_at"].isoformat() if e.get("created_at") else None,
                "assigned_client_count": len(assignments.get(str(e["id"]), [])),
            } for e in employees
        ],
        "total": len(employees),
    }


# v118.28.1 · 客户分配(老板用)
class EmployeeAssignmentsRequest(BaseModel):
    client_ids: List[int] = []


@app.get("/api/team/employees/{employee_id}/assignments")
async def team_get_employee_assignments(employee_id: str, request: Request):
    """老板拿单个员工的客户分配列表"""
    owner = _require_owner_or_super(request)
    tid = str(owner.get("tenant_id") or "")
    if not tid:
        raise HTTPException(400, detail="team.no_tenant")
    # 校验员工属于本租户
    emp = db.find_user_by_id(employee_id)
    if not emp or str(emp.get("tenant_id") or "") != tid:
        raise HTTPException(404, detail="team.employee_not_found")
    all_assignments = db.list_assignments_by_employees(tid)
    return {"client_ids": all_assignments.get(str(employee_id), [])}


@app.post("/api/team/employees/{employee_id}/assignments")
async def team_set_employee_assignments(employee_id: str,
                                          req: EmployeeAssignmentsRequest,
                                          request: Request):
    """老板覆盖式设置某员工的客户分配 · 写审计日志"""
    owner = _require_owner_or_super(request)
    tid = str(owner.get("tenant_id") or "")
    if not tid:
        raise HTTPException(400, detail="team.no_tenant")
    emp = db.find_user_by_id(employee_id)
    if not emp or str(emp.get("tenant_id") or "") != tid:
        raise HTTPException(404, detail="team.employee_not_found")
    ok = db.set_employee_assignments(
        employee_user_id=str(employee_id),
        client_ids=req.client_ids or [],
        assigned_by=str(owner["id"]),
        tenant_id=tid,
    )
    if not ok:
        raise HTTPException(400, detail="team.assign_failed")
    # 审计日志(对齐 v118.28.6/7/8 模式)
    try:
        db.insert_operation_log(
            tenant_id=tid,
            actor_user_id=str(owner["id"]),
            actor_username=owner.get("username"),
            actor_is_super=bool(owner.get("is_super_admin")),
            action="team.set_client_assignments",
            target_type="user",
            target_id=str(employee_id),
            target_name=emp.get("username"),
            details={"client_ids": list(req.client_ids or [])},
            ip=get_client_ip(request),
            ua=request.headers.get("user-agent", ""),
        )
    except Exception as e:
        logger.warning(f"[team_assign] 写操作日志失败: {e}")
    return {"ok": True, "assigned_count": len(req.client_ids or [])}


# 加员工
@app.post("/api/team/employees")
async def team_add_employee(req: EmployeeAddRequest, request: Request):
    owner = _require_owner_or_super(request)
    # v118.11 · 密码强度校验
    pw_err = _check_password_strength(req.password)
    if pw_err:
        raise HTTPException(400, detail=pw_err)
    # 提前查是否已存在
    existing = db.find_user_by_username(req.username)
    if existing:
        raise HTTPException(409, detail="team.username_exists")
    # v118.11 · 邮箱也要查重(如果填了)
    if req.email:
        try:
            import db as _db
            with _db.get_cursor() as cur:
                cur.execute("SELECT id FROM users WHERE LOWER(email) = LOWER(%s) LIMIT 1", (req.email,))
                if cur.fetchone():
                    raise HTTPException(409, detail="team.email_exists")
        except HTTPException:
            raise
        except Exception as _ex:
            logger.warning(f"email check skip: {_ex}")
    new_id = db.add_employee(
        tenant_id=str(owner["tenant_id"]),
        username=req.username,
        password=req.password,
        invited_by=str(owner["id"]),
    )
    if not new_id:
        raise HTTPException(400, detail="team.create_failed")
    # v118.11 · 员工创建后写入 email(如果提供)
    if req.email:
        try:
            import db as _db
            with _db.get_cursor(commit=True) as cur:
                cur.execute("UPDATE users SET email = %s WHERE id = %s",
                            (req.email.strip().lower(), new_id))
        except Exception as _ex:
            logger.warning(f"set employee email failed: {_ex}")
    _log_op(request, owner, "employee.add", "employee", new_id, req.username, {})
    return {"ok": True, "id": new_id}


# v118.11 · 重置员工密码 · 系统生成强随机临时密码 · 一次性返回给老板
@app.post("/api/team/employees/{employee_id}/reset-password")
async def team_reset_employee_password(employee_id: str, request: Request):
    """v118.28.7 · 老板给员工发改密链接 · 老板永远拿不到密码
       员工没邮箱也没 LINE 关联 → 拒绝 · 提示先补邮箱(对齐大厂)"""
    owner = _require_owner_or_super(request)
    target = db.find_user_by_id(employee_id)
    if not target:
        raise HTTPException(404, detail="team.employee_not_found")
    if str(target.get("tenant_id") or "") != str(owner["tenant_id"]):
        if not owner.get("is_super_admin"):
            raise HTTPException(403, detail="team.not_in_your_tenant")
    if target.get("role") == "owner" or target.get("is_super_admin"):
        raise HTTPException(400, detail="team.cannot_reset_owner")

    from auth_signup import send_reset_link_for_employee
    host = request.headers.get("host", "pearnly.com")
    res = send_reset_link_for_employee(
        user_id=employee_id,
        request_host=host,
        actor_username=owner.get("username"),
    )

    if res.get("error") == "no_channel":
        # 员工既无邮箱也无 LINE 关联 · 拒绝重置 · 让老板先帮员工补邮箱
        _log_op(request, owner, "employee.password_reset_blocked_no_channel", "employee",
                employee_id, target.get("username"), {})
        raise HTTPException(400, detail="team.reset_no_channel")

    if not res.get("ok"):
        _log_op(request, owner, "employee.password_reset_link_failed", "employee",
                employee_id, target.get("username"), {"error": res.get("error")})
        raise HTTPException(500, detail="team.reset_link_send_failed")

    _log_op(request, owner, "employee.password_reset_link_sent", "employee",
            employee_id, target.get("username"), {"channel": res.get("channel")})
    return {
        "ok": True,
        "channel": res.get("channel"),  # line / email
        "message": "reset_link_sent",
    }


# 删员工
@app.delete("/api/team/employees/{employee_id}")
async def team_remove_employee(employee_id: str, request: Request):
    owner = _require_owner_or_super(request)
    # 记下员工 username 再删
    target = db.find_user_by_id(employee_id)
    target_name = target.get("username") if target else None
    ok = db.remove_employee(str(owner["tenant_id"]), employee_id)
    if not ok:
        raise HTTPException(404, detail="team.employee_not_found")
    _log_op(request, owner, "employee.remove", "employee", employee_id, target_name, {})
    return {"ok": True}


# 启用/停用员工
@app.patch("/api/team/employees/{employee_id}/active")
async def team_toggle_employee(employee_id: str, req: EmployeeToggleRequest, request: Request):
    owner = _require_owner_or_super(request)
    target = db.find_user_by_id(employee_id)
    target_name = target.get("username") if target else None
    ok = db.toggle_employee_active(str(owner["tenant_id"]), employee_id, req.is_active)
    if not ok:
        raise HTTPException(404, detail="team.employee_not_found")
    _log_op(request, owner, "employee.toggle", "employee", employee_id, target_name,
            {"is_active": req.is_active})
    return {"ok": True}


# ============================================================
# v118.13 · 超管员工操作接口(配合「用户管理 → 员工 tab」)
# 跟老板的 /api/team/employees/{id}/xxx 不同的是:超管不依赖 owner.tenant_id 过滤
# 数据走同一张表 (users WHERE role='member') · 操作后老板的「设置 → 团队管理」也立刻看到
# ============================================================

@app.patch("/api/admin/employees/{employee_id}/active")
async def admin_toggle_employee_active(employee_id: str, req: EmployeeToggleRequest, request: Request):
    """v118.28.6 · 砍 · 行业惯例(Xero/QuickBooks/Stripe)超管不直接管客户员工 · 由所属老板自行操作"""
    _require_super_admin(request)
    raise HTTPException(410, detail="admin.employee_action_removed")


@app.post("/api/admin/employees/{employee_id}/reset-password")
async def admin_reset_employee_password(employee_id: str, request: Request):
    """v118.28.6 · 砍 · 见上"""
    _require_super_admin(request)
    raise HTTPException(410, detail="admin.employee_action_removed")


@app.delete("/api/admin/employees/{employee_id}")
async def admin_remove_employee(employee_id: str, request: Request):
    """v118.28.6 · 砍 · 见上"""
    _require_super_admin(request)
    raise HTTPException(410, detail="admin.employee_action_removed")




# ============================================================
# v118.16 · 超管级联删除老板账号 · 影响范围预查 + 双重确认
# ============================================================

@app.get("/api/admin/users/{user_id}/cascade-preview")
async def admin_cascade_preview(user_id: str, request: Request):
    """超管查看删除老板的影响范围(给前端 modal 显示)"""
    _require_super_admin(request)
    info = db.preview_owner_cascade(user_id)
    if not info:
        raise HTTPException(404, detail="admin.user_not_found_or_not_owner")
    return info


class CascadeDeleteRequest(BaseModel):
    confirm_username: str = Field(..., min_length=1, max_length=200)
    confirm_password: str = Field(..., min_length=1, max_length=200)


@app.post("/api/admin/users/{user_id}/cascade-delete")
async def admin_cascade_delete(user_id: str, req: CascadeDeleteRequest, request: Request):
    """超管级联删除老板 + 整个 tenant + 所有员工 + 所有数据
    需要双重确认:超管自己的主密码 + 输入要删客户的用户名
    """
    admin = _require_super_admin(request)
    # 1) 拿目标 owner
    target = db.find_user_by_id(user_id)
    if not target:
        raise HTTPException(404, detail="admin.user_not_found")
    # v118.16.1 · 兼容老用户 role IS NULL(对齐 admin_list_users 筛选规则)
    target_role = target.get("role")
    if target_role and target_role != "owner":
        raise HTTPException(400, detail="admin.not_an_owner")
    # 2) 防自删
    if str(target["id"]) == str(admin["id"]):
        raise HTTPException(400, detail="admin.cannot_delete_self")
    # 3) 验证用户名(防误删)
    if (target.get("username") or "").strip() != req.confirm_username.strip():
        raise HTTPException(400, detail="admin.username_mismatch")
    # 4) 验证超管自己的密码
    if not db.verify_user_password(str(admin["id"]), req.confirm_password):
        raise HTTPException(403, detail="admin.password_invalid")
    # 5) 取影响范围(写入操作日志)
    preview = db.preview_owner_cascade(user_id) or {}
    target_name = target.get("username")
    # 6) 级联删
    ok = db.delete_owner_user_cascade(user_id)
    if not ok:
        raise HTTPException(500, detail="admin.cascade_delete_failed")
    # 7) 操作日志(deletion 之后写 · 因为 tenant_id 已删)
    _log_op(request, admin, "admin.user.cascade_delete", "user", user_id, target_name,
            {"counts": preview.get("counts", {}), "tenant_id": (preview.get("tenant") or {}).get("id")})
    return {"ok": True, "deleted_username": target_name}


# ============================================================
# v118.18 · 推荐分类(supplier_categories)前端 API
# ============================================================

@app.get("/api/categories")
async def api_list_used_categories(request: Request):
    """列出当前 tenant/user 用过的所有 category(给前端 datalist 自动补全 + 统计)"""
    user = get_current_user_from_request(request)
    tid = _tid(user)
    cats = db.list_used_categories(user_id=str(user["id"]), tenant_id=tid, limit=30)
    n_mappings = db.count_supplier_mappings(user_id=str(user["id"]), tenant_id=tid)
    return {"categories": cats, "supplier_count": n_mappings}



# ============================================================
# v118.22.1 · 智能提醒(Notifications)· 数据底座 + 测试发送
# 触发 hook 接入留 v118.22.1.1 做(异常 hook + 大额 hook)
# ============================================================
# 模板常量已在 v118.22.1.1 helper 段(本文件 1900 多行处)统一声明


class NotificationRuleCreate(BaseModel):
    name: str
    template_code: str
    params: Optional[Dict[str, Any]] = None
    enabled: bool = True


class NotificationRuleUpdate(BaseModel):
    name: Optional[str] = None
    params: Optional[Dict[str, Any]] = None
    enabled: Optional[bool] = None


def _validate_template_params(template_code: str, params: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """模板特定参数校验 · 失败 raise HTTPException 400"""
    p = dict(params or {})
    if template_code == NOTIF_TEMPLATE_LARGE_INVOICE:
        thr = p.get("threshold")
        try:
            thr_f = float(thr) if thr is not None else 0.0
        except Exception:
            raise HTTPException(400, detail="notification.threshold_invalid")
        if thr_f <= 0:
            raise HTTPException(400, detail="notification.threshold_required")
        p["threshold"] = thr_f
    # exception_high 暂无必填参数
    return p


@app.get("/api/notifications/rules")
async def api_notif_list_rules(request: Request):
    """列规则 · 同 tenant 共享视图"""
    user = get_current_user_from_request(request)
    rules = db.list_notification_rules(str(user["id"]), tenant_id=_tid(user))
    return {"items": rules, "count": len(rules)}


@app.post("/api/notifications/rules")
async def api_notif_create_rule(req: NotificationRuleCreate, request: Request):
    """新建规则 · 必须选内置模板之一"""
    user = get_current_user_from_request(request)
    name = (req.name or "").strip()
    if not name:
        raise HTTPException(400, detail="notification.name_required")
    if len(name) > 100:
        raise HTTPException(400, detail="notification.name_too_long")
    if req.template_code not in NOTIF_TEMPLATE_WHITELIST:
        raise HTTPException(400, detail="notification.template_invalid")
    params = _validate_template_params(req.template_code, req.params)
    rule_id = db.create_notification_rule(
        user_id=str(user["id"]), tenant_id=_tid(user),
        name=name, template_code=req.template_code,
        params=params, enabled=req.enabled,
    )
    if not rule_id:
        raise HTTPException(500, detail="notification.create_failed")
    return {"ok": True, "id": rule_id}


@app.patch("/api/notifications/rules/{rule_id}")
async def api_notif_update_rule(rule_id: int, req: NotificationRuleUpdate, request: Request):
    """改规则 · 任一字段非 None 即更新"""
    user = get_current_user_from_request(request)
    rule = db.get_notification_rule(rule_id, str(user["id"]), tenant_id=_tid(user))
    if not rule:
        raise HTTPException(404, detail="notification.not_found")
    name_new = None
    if req.name is not None:
        name_new = req.name.strip()
        if not name_new:
            raise HTTPException(400, detail="notification.name_required")
        if len(name_new) > 100:
            raise HTTPException(400, detail="notification.name_too_long")
    params_new = None
    if req.params is not None:
        params_new = _validate_template_params(rule["template_code"], req.params)
    ok = db.update_notification_rule(
        rule_id=rule_id, user_id=str(user["id"]), tenant_id=_tid(user),
        name=name_new, params=params_new, enabled=req.enabled,
    )
    if not ok:
        raise HTTPException(500, detail="notification.update_failed")
    return {"ok": True}


@app.delete("/api/notifications/rules/{rule_id}")
async def api_notif_delete_rule(rule_id: int, request: Request):
    """删规则 · logs 里的 rule_id 置空保留发送历史"""
    user = get_current_user_from_request(request)
    rule = db.get_notification_rule(rule_id, str(user["id"]), tenant_id=_tid(user))
    if not rule:
        raise HTTPException(404, detail="notification.not_found")
    ok = db.delete_notification_rule(rule_id, str(user["id"]), tenant_id=_tid(user))
    if not ok:
        raise HTTPException(500, detail="notification.delete_failed")
    return {"ok": True}


@app.post("/api/notifications/rules/{rule_id}/test")
async def api_notif_test_send(rule_id: int, request: Request):
    """测试发送 · 渲染 test_send 模板 + 推到当前用户绑定的 LINE"""
    user = get_current_user_from_request(request)
    rule = db.get_notification_rule(rule_id, str(user["id"]), tenant_id=_tid(user))
    if not rule:
        raise HTTPException(404, detail="notification.not_found")
    binding = db.get_line_binding_by_user(str(user["id"]))
    if not binding or not binding.get("line_user_id"):
        raise HTTPException(400, detail="notification.line_not_bound")
    line_user_id = binding["line_user_id"]
    # v118.25.4 · fallback 改 th(主市场泰国)而非 zh
    lang = (user.get("preferred_lang") or "th")
    text = line_client.render_notification(lang, "test_send", {
        "rule_name": rule.get("name") or "-",
    })
    ok = line_client.push_text(line_user_id, text)
    db.log_notification(
        user_id=str(user["id"]), tenant_id=_tid(user),
        rule_id=rule_id, template_code=rule.get("template_code") or "test_send",
        event_type="test_send", event_ref=None,
        line_user_id=line_user_id,
        status="sent" if ok else "failed",
        error=None if ok else "line_push_failed",
    )
    if not ok:
        raise HTTPException(502, detail="notification.line_push_failed")
    return {"ok": True}


@app.get("/api/notifications/logs")
async def api_notif_list_logs(request: Request, limit: int = 50):
    """列发送日志 · 同 tenant 共享 · 默认最近 50"""
    user = get_current_user_from_request(request)
    logs = db.list_notification_logs(
        str(user["id"]), tenant_id=_tid(user),
        limit=min(int(limit), 200),
    )
    return {"items": logs, "count": len(logs)}


# ============================================================
# v118.27.0 · ERP 映射底座(客户 / 科目 / 税码 3 个 sub-tab)
# ============================================================
# 权限:
#   - 客户映射:接 client_assignments filter(员工只看自己客户)· GET 全员可调
#   - 科目/税码映射:tenant 共享 · GET 全员可调
#   - POST/DELETE 全部要 _require_owner_or_super(老板/超管才能改)
# ============================================================

# ─── 客户映射 ────────────────────────────────────────────
@app.get("/api/erp/mappings/clients")
async def erp_map_list_clients(request: Request):
    user = get_current_user_from_request(request)
    tid = _tid(user)
    if not tid:
        return {"items": []}
    visible = db.get_visible_client_ids_for_user(user)
    rows = db.list_erp_client_mappings(tid, restrict_client_ids=visible)
    return {"items": rows, "count": len(rows)}


@app.post("/api/erp/mappings/clients")
async def erp_map_upsert_client(request: Request):
    owner = _require_owner_or_super(request)
    body = await request.json()
    cid = body.get("client_id")
    erp_type = body.get("erp_type")
    erp_code = body.get("erp_code")
    notes = body.get("notes") or ""
    if not cid or not erp_type or not erp_code:
        raise HTTPException(400, detail="erp_map.missing_fields")
    new_id = db.upsert_erp_client_mapping(
        str(owner["tenant_id"]), int(cid), erp_type, erp_code, notes, str(owner["id"])
    )
    if not new_id:
        raise HTTPException(400, detail="erp_map.upsert_failed")
    return {"ok": True, "id": new_id}


@app.delete("/api/erp/mappings/clients/{mapping_id}")
async def erp_map_delete_client(mapping_id: str, request: Request):
    owner = _require_owner_or_super(request)
    ok = db.delete_erp_client_mapping(str(owner["tenant_id"]), mapping_id)
    if not ok:
        raise HTTPException(404, detail="erp_map.not_found")
    return {"ok": True}


# ─── 科目映射 ────────────────────────────────────────────
@app.get("/api/erp/mappings/accounts")
async def erp_map_list_accounts(request: Request):
    user = get_current_user_from_request(request)
    tid = _tid(user)
    if not tid:
        return {"items": []}
    rows = db.list_erp_account_mappings(tid)
    return {"items": rows, "count": len(rows)}


@app.post("/api/erp/mappings/accounts")
async def erp_map_upsert_account(request: Request):
    owner = _require_owner_or_super(request)
    body = await request.json()
    erp_type = body.get("erp_type")
    cat = body.get("pearnly_category")
    code = body.get("erp_code")
    name = body.get("erp_name") or ""
    notes = body.get("notes") or ""
    if not erp_type or not cat or not code:
        raise HTTPException(400, detail="erp_map.missing_fields")
    new_id = db.upsert_erp_account_mapping(
        str(owner["tenant_id"]), erp_type, cat, code, name, notes, str(owner["id"])
    )
    if not new_id:
        raise HTTPException(400, detail="erp_map.upsert_failed")
    return {"ok": True, "id": new_id}


@app.delete("/api/erp/mappings/accounts/{mapping_id}")
async def erp_map_delete_account(mapping_id: str, request: Request):
    owner = _require_owner_or_super(request)
    ok = db.delete_erp_account_mapping(str(owner["tenant_id"]), mapping_id)
    if not ok:
        raise HTTPException(404, detail="erp_map.not_found")
    return {"ok": True}


# ─── 税码映射 ────────────────────────────────────────────
@app.get("/api/erp/mappings/taxes")
async def erp_map_list_taxes(request: Request):
    user = get_current_user_from_request(request)
    tid = _tid(user)
    if not tid:
        return {"items": []}
    rows = db.list_erp_tax_mappings(tid)
    return {"items": rows, "count": len(rows)}


@app.post("/api/erp/mappings/taxes")
async def erp_map_upsert_tax(request: Request):
    owner = _require_owner_or_super(request)
    body = await request.json()
    erp_type = body.get("erp_type")
    kind = body.get("pearnly_tax_kind")
    code = body.get("erp_code")
    notes = body.get("notes") or ""
    if not erp_type or not kind or not code:
        raise HTTPException(400, detail="erp_map.missing_fields")
    new_id = db.upsert_erp_tax_mapping(
        str(owner["tenant_id"]), erp_type, kind, code, notes, str(owner["id"])
    )
    if not new_id:
        raise HTTPException(400, detail="erp_map.upsert_failed")
    return {"ok": True, "id": new_id}


@app.delete("/api/erp/mappings/taxes/{mapping_id}")
async def erp_map_delete_tax(mapping_id: str, request: Request):
    owner = _require_owner_or_super(request)
    ok = db.delete_erp_tax_mapping(str(owner["tenant_id"]), mapping_id)
    if not ok:
        raise HTTPException(404, detail="erp_map.not_found")
    return {"ok": True}


# ─── 商品映射 CRUD ──────────────────────────────────────────

class ErpProductMappingReq(BaseModel):
    erp_type:  str
    item_name: str
    erp_code:  str
    erp_name:  Optional[str] = None
    notes:     Optional[str] = None


@app.get("/api/erp/mappings/products")
async def list_mappings_products(request: Request, erp_type: str = ""):
    """列商品映射 · 可选 erp_type 过滤 · 默认列全部"""
    user = get_current_user_from_request(request)
    tid = _tid(user)
    if not tid:
        raise HTTPException(400, detail="no_tenant")
    role = (user.get("role") or "owner").lower()
    if role != "owner" and not user.get("is_super_admin"):
        raise HTTPException(403, detail="owner_only")
    rows = db.list_erp_product_mappings(tid, erp_type=(erp_type.strip() or None))
    out = []
    for r in rows:
        out.append({
            "id":         str(r.get("id")) if r.get("id") else None,
            "erp_type":   r.get("erp_type"),
            "item_name":  r.get("item_name"),
            "erp_code":   r.get("erp_code"),
            "erp_name":   r.get("erp_name"),
            "notes":      r.get("notes"),
            "created_at": r.get("created_at").isoformat() if r.get("created_at") else None,
            "updated_at": r.get("updated_at").isoformat() if r.get("updated_at") else None,
        })
    return {"ok": True, "items": out, "total": len(out)}


@app.post("/api/erp/mappings/products")
async def upsert_mapping_product(req: ErpProductMappingReq, request: Request):
    """加/改商品映射"""
    user = get_current_user_from_request(request)
    tid = _tid(user)
    if not tid:
        raise HTTPException(400, detail="no_tenant")
    role = (user.get("role") or "owner").lower()
    if role != "owner" and not user.get("is_super_admin"):
        raise HTTPException(403, detail="owner_only")
    mid = db.upsert_erp_product_mapping(
        tenant_id=tid,
        erp_type=req.erp_type,
        item_name=req.item_name,
        erp_code=req.erp_code,
        erp_name=req.erp_name,
        notes=req.notes,
        user_id=str(user["id"]),
    )
    if not mid:
        raise HTTPException(400, detail="upsert_failed")
    return {"ok": True, "id": mid}


@app.delete("/api/erp/mappings/products/{mapping_id}")
async def delete_mapping_product(mapping_id: str, request: Request):
    user = get_current_user_from_request(request)
    tid = _tid(user)
    if not tid:
        raise HTTPException(400, detail="no_tenant")
    role = (user.get("role") or "owner").lower()
    if role != "owner" and not user.get("is_super_admin"):
        raise HTTPException(403, detail="owner_only")
    ok = db.delete_erp_product_mapping(tid, mapping_id)
    return {"ok": bool(ok)}


# ============================================================
# v118.27.5 · 统一连接器聚合 · 抽屉「1 个推送按钮」用
# ============================================================
@app.get("/api/erp/connectors/status")
async def erp_connectors_status(request: Request):
    """
    统一返回当前用户/租户所有「已配置的 ERP 连接器」 · 不管它走的是
    OAuth API(Xero) / 老 webhook endpoints 表(自定义/flowaccount)
    
    返回:
    {
      connectors: [
        { id, type, name, method, status, push_endpoint, ... }
      ]
    }
    
    method:
      - "api"      → 直接 fetch(后端推送 · 完成即结束)
      - "download" → fetch + 浏览器下载 .xlsx
      - "webhook"  → 走老 /api/erp/push 接口(endpoint_id 必填)
    """
    user = get_current_user_from_request(request)
    tid = _tid(user)
    connectors: List[Dict[str, Any]] = []

    # 1. Xero(OAuth · v118.27.4)
    try:
        if tid:
            xero_tokens = db.list_oauth_tokens(tid, "xero") or []
            if xero_tokens:
                default_token = next((tk for tk in xero_tokens if tk.get("is_default")), xero_tokens[0])
                connectors.append({
                    "id": "xero",
                    "type": "xero",
                    "name": "Xero",
                    "method": "api",
                    "status": "connected",
                    "is_default": False,
                    "push_endpoint": "/api/erp/xero/push/{history_id}",
                    "meta": {
                        "organisation_count": len(xero_tokens),
                        "default_org": (default_token or {}).get("organisation_name"),
                    },
                })
    except Exception as e:
        logger.warning(f"connectors_status xero failed: {e}")

    # 2. erp_endpoints 表(老 webhook + flowaccount + 任何 adapter)
    try:
        endpoints = db.list_erp_endpoints(str(user["id"])) or []
        for ep in endpoints:
            if not ep.get("enabled", True):
                continue
            adapter = ep.get("adapter") or "webhook"
            connectors.append({
                "id": f"endpoint_{ep['id']}",
                "type": adapter,
                "endpoint_id": str(ep["id"]),
                "name": ep.get("name") or "Webhook",
                "method": "webhook",
                "status": "connected",
                "is_default": bool(ep.get("is_default")),
                "push_endpoint": "/api/erp/push",
                "meta": {
                    "auto_push": bool(ep.get("auto_push")),
                },
            })
    except Exception as e:
        logger.warning(f"connectors_status endpoints failed: {e}")

    return {"connectors": connectors}


# ============================================================
# v118.27.4 · Xero 适配器(OAuth 2.0 Web app · ACCREC 销售推送)
# ============================================================
# 5 接口:auth/start · auth/callback · select_org · disconnect · status · push
# 复用 v118.27.0 的 3 张映射表(erp_type='xero')
# ============================================================

@app.get("/api/erp/xero/auth/start")
async def xero_auth_start(request: Request):
    """
    老板点「连接 Xero」→ 后端生成 state · 存 db · 返回 redirect URL
    前端拿到 URL 后用 window.location 跳转
    """
    owner = _require_owner_or_super(request)
    try:
        from xero_pusher import is_configured, build_auth_url, gen_state
    except ImportError:
        raise HTTPException(500, detail="xero.module_missing")
    if not is_configured():
        raise HTTPException(500, detail="xero.not_configured")
    state = gen_state()
    if not db.save_oauth_state(state, str(owner["tenant_id"]), str(owner["id"]), "xero"):
        raise HTTPException(500, detail="xero.state_save_failed")
    return {"redirect_url": build_auth_url(state)}


@app.get("/api/erp/xero/auth/callback")
async def xero_auth_callback(request: Request, code: str = "", state: str = "",
                              error: str = "", error_description: str = ""):
    """
    Xero 重定向回来 · 用 code 换 token · 拿 organisations · 存 db
    完成后 302 redirect 用户回前端 hash 路由 + 提示
    """
    from fastapi.responses import RedirectResponse
    base = (os.environ.get("PEARNLY_BASE_URL") or "https://pearnly.com").rstrip("/")
    fail_url = f"{base}/#automation?xero=err"

    if error:
        logger.warning(f"xero callback error: {error} · {error_description[:200]}")
        return RedirectResponse(url=f"{base}/#automation?xero=err&reason={error}", status_code=302)

    if not code or not state:
        return RedirectResponse(url=fail_url, status_code=302)

    consumed = db.consume_oauth_state(state)
    if not consumed or consumed.get('erp_type') != 'xero':
        return RedirectResponse(url=fail_url + "&reason=bad_state", status_code=302)

    try:
        from xero_pusher import (
            exchange_code_for_token, list_organisations, compute_expires_at,
        )
    except ImportError:
        return RedirectResponse(url=fail_url + "&reason=module", status_code=302)

    tok = exchange_code_for_token(code)
    if not tok or not tok.get("access_token") or not tok.get("refresh_token"):
        return RedirectResponse(url=fail_url + "&reason=token_exchange", status_code=302)

    orgs = list_organisations(tok["access_token"])
    if not orgs:
        return RedirectResponse(url=fail_url + "&reason=no_org", status_code=302)

    expires_at = compute_expires_at(tok.get("expires_in", 1800))
    saved = 0
    for i, o in enumerate(orgs):
        org_id = o.get("tenantId") or o.get("id")
        org_name = o.get("tenantName") or "Xero Org"
        if not org_id:
            continue
        ok = db.upsert_oauth_token(
            tenant_id=consumed['tenant_id'], erp_type="xero",
            organisation_id=str(org_id), organisation_name=org_name,
            access_token=tok["access_token"], refresh_token=tok["refresh_token"],
            expires_at=expires_at, scope=tok.get("scope") or "",
            is_default=(i == 0),  # 第 1 个先设默认 · 用户回去可改
            user_id=consumed['user_id'],
        )
        if ok:
            saved += 1

    if not saved:
        return RedirectResponse(url=fail_url + "&reason=db_save", status_code=302)

    # 成功 · 跳回自动化 ERP 对接 · 触发前端刷新连接卡片
    return RedirectResponse(url=f"{base}/#automation?xero=ok&n={saved}", status_code=302)


@app.get("/api/erp/xero/status")
async def xero_status(request: Request):
    """前端拉取连接状态 · 渲染连接卡片"""
    user = get_current_user_from_request(request)
    tid = _tid(user)
    try:
        from xero_pusher import is_configured
    except ImportError:
        return {"configured": False, "connected": False}
    out = {
        "configured": bool(is_configured()),
        "connected": False,
        "organisations": [],
        "default_org_id": None,
        "auto_push": False,  # v27.8.1.3
    }
    if not tid:
        return out
    rows = db.list_oauth_tokens(tid, "xero")
    if rows:
        out["connected"] = True
        out["organisations"] = [{
            "id": str(r["id"]),
            "organisation_id": r["organisation_id"],
            "organisation_name": r["organisation_name"],
            "is_default": bool(r["is_default"]),
            "expires_at": r["expires_at"].isoformat() if r["expires_at"] else None,
        } for r in rows]
        for r in rows:
            if r["is_default"]:
                out["default_org_id"] = r["organisation_id"]
                break
        out["auto_push"] = db.get_xero_auto_push(tid)
    return out


@app.post("/api/erp/xero/auto-push")
async def xero_set_auto_push(request: Request):
    """v27.8.1.3 · 切换 Xero 识别完自动推送(老板权限)"""
    owner = _require_owner_or_super(request)
    body = await request.json()
    on = bool(body.get("on"))
    if not db.set_xero_auto_push(str(owner["tenant_id"]), on):
        raise HTTPException(500, detail="xero.toggle_failed")
    return {"ok": True, "auto_push": on}


@app.post("/api/erp/xero/select_org")
async def xero_select_org(request: Request):
    """切换默认 organisation"""
    owner = _require_owner_or_super(request)
    body = await request.json()
    token_id = body.get("token_id")
    if not token_id:
        raise HTTPException(400, detail="xero.missing_token_id")
    ok = db.set_default_oauth_token(str(owner["tenant_id"]), "xero", str(token_id))
    if not ok:
        raise HTTPException(404, detail="xero.token_not_found")
    return {"ok": True}


@app.post("/api/erp/xero/disconnect")
async def xero_disconnect(request: Request):
    """断开 Xero 连接 · 删 tenant 在 Xero 的所有 token"""
    owner = _require_owner_or_super(request)
    n = db.delete_oauth_tokens(str(owner["tenant_id"]), "xero")
    return {"ok": True, "deleted": n}


def _ensure_fresh_xero_token(tenant_id):
    """拿默认 token · 过期就 refresh · 失败抛 HTTPException
    返回 (access_token, organisation_id)
    """
    from xero_pusher import refresh_access_token, compute_expires_at
    tok = db.get_default_oauth_token(tenant_id, "xero")
    if not tok:
        raise HTTPException(400, detail="xero.err_not_connected")
    # 过期判断
    exp = tok.get("expires_at")
    need_refresh = False
    if exp:
        try:
            from datetime import datetime, timezone
            now = datetime.now(timezone.utc)
            if exp.tzinfo is None:
                exp = exp.replace(tzinfo=timezone.utc)
            need_refresh = (exp <= now)
        except Exception:
            need_refresh = True
    if need_refresh:
        new = refresh_access_token(tok["refresh_token"])
        if not new or not new.get("access_token"):
            raise HTTPException(401, detail="xero.err_token_expired")
        new_exp = compute_expires_at(new.get("expires_in", 1800))
        db.update_oauth_access_token(
            token_id=str(tok["id"]),
            access_token=new["access_token"],
            refresh_token=new.get("refresh_token") or tok["refresh_token"],
            expires_at=new_exp,
        )
        return new["access_token"], tok["organisation_id"]
    return tok["access_token"], tok["organisation_id"]


@app.post("/api/erp/xero/push/{history_id}")
async def xero_push(history_id: str, request: Request):
    """单张 OCR history → Xero ACCREC Invoice(DRAFT 状态)"""
    import time
    t0 = time.time()
    user = get_current_user_from_request(request)
    tid = _tid(user)

    history = db.get_ocr_history_detail(str(user["id"]), history_id, tenant_id=tid)
    if not history:
        raise HTTPException(404, detail="xero.err_history_not_found")

    if not tid:
        raise HTTPException(400, detail="xero.err_not_connected")

    # 异常未放行
    st = (history.get("status") or "").lower()
    if st in ("exception", "exception_pending", "rejected"):
        raise HTTPException(400, detail="xero.err_exception_unresolved")

    # 客户映射
    mappings = db.get_mrerp_mappings_bundle(tid)  # 通用 3 表映射拼装
    cid = history.get("client_id") or 0
    contact_name = None
    for m in (mappings.get("clients") or []):
        if m.get("erp_type") == "xero" and int(m.get("client_id") or 0) == int(cid):
            contact_name = (m.get("erp_code") or "").strip()
            break
    if not contact_name:
        raise HTTPException(400, detail="xero.err_no_client_mapping")

    # 拿 token + refresh
    access_token, xero_org_id = _ensure_fresh_xero_token(tid)

    # 找 contact
    try:
        from xero_pusher import (
            find_contact_by_name, build_invoice_payload, push_invoice,
            parse_xero_error,
        )
    except ImportError:
        raise HTTPException(500, detail="xero.module_missing")

    contact = find_contact_by_name(access_token, xero_org_id, contact_name)
    if not contact or not contact.get("ContactID"):
        # 写失败日志
        try:
            db.insert_push_log(
                user_id=str(user["id"]), endpoint_id=None, history_id=history_id,
                invoice_no=history.get("invoice_no"),
                seller_name=history.get("seller_name"),
                total_amount=history.get("total_amount"),
                status="failed", http_status=400,
                request_body={"adapter": "xero", "stage": "find_contact", "name": contact_name},
                response_body=None, error_msg="contact_not_found",
                attempt=1, elapsed_ms=int((time.time() - t0) * 1000),
                trigger="manual",
            )
        except Exception as e:
            logger.warning(f"[xero_manual] 写 push_log(no_contact)失败: {e}")
        raise HTTPException(400, detail="xero.err_contact_not_found")

    # 拼 payload + 推
    payload = build_invoice_payload(history, mappings, contact)
    ok, body = push_invoice(access_token, xero_org_id, payload)

    if ok:
        invoice_id = ""
        try:
            invs = body.get("Invoices") or []
            if invs:
                invoice_id = invs[0].get("InvoiceID", "")
        except Exception as e:
            logger.warning(f"[xero_manual] 解析 InvoiceID 失败: {e}")
        try:
            db.insert_push_log(
                user_id=str(user["id"]), endpoint_id=None, history_id=history_id,
                invoice_no=history.get("invoice_no"),
                seller_name=history.get("seller_name"),
                total_amount=history.get("total_amount"),
                status="success", http_status=200,
                request_body={"adapter": "xero", "stage": "push_invoice"},
                response_body=str(invoice_id)[:200],
                error_msg=None, attempt=1,
                elapsed_ms=int((time.time() - t0) * 1000),
                trigger="manual",
            )
        except Exception as e:
            logger.warning(f"[xero_manual] 写 push_log(ok)失败: {e}")
        return {"ok": True, "invoice_id": invoice_id, "organisation_id": xero_org_id}

    # 失败 · 解析错误码
    http_st = body.get("http_status") if isinstance(body, dict) else None
    err_code = parse_xero_error(http_st or 400, body.get("body") if isinstance(body, dict) else {})
    try:
        db.insert_push_log(
            user_id=str(user["id"]), endpoint_id=None, history_id=history_id,
            invoice_no=history.get("invoice_no"),
            seller_name=history.get("seller_name"),
            total_amount=history.get("total_amount"),
            status="failed", http_status=http_st or 400,
            request_body={"adapter": "xero", "stage": "push_invoice"},
            response_body=str(body)[:500],
            error_msg=err_code, attempt=1,
            elapsed_ms=int((time.time() - t0) * 1000),
            trigger="manual",
        )
    except Exception as e:
        logger.warning(f"[xero_manual] 写 push_log(fail)失败: {e}")
    raise HTTPException(http_st or 400, detail=f"xero.{err_code.lower()}")




# ============================================================
# v118.35.0.6 · credits 后端 11 接口 + multi-company 切换 + topup 审核
# 从 legacy/credits-system-5de6cc5 cherry-pick surgery (D1 方案 · 只接
# 后端 · 前端 home.js/home.html/home.css 不动 · 充值 UI 暂缺 v36 补)
# ============================================================

def send_topup_approved_email(tenant_id, amount_thb, new_balance):
    """v118.35.0.6 · 占位 noop · v36 真接邮件再实现."""
    logger.info(f"[email-stub] topup_approved tenant={str(tenant_id)[:8]} amt={amount_thb} bal={new_balance}")


@app.get("/api/me/credits")
async def get_my_credits(request: Request):
    """查询账户余额和用量（区分老板/员工视角）"""
    import datetime as _dt
    user = get_current_user_from_request(request)
    user_id = str(user.get("id", ""))
    tenant_id = user.get("tenant_id")
    is_exempt = bool(user.get("is_billing_exempt", False))
    # 老板 = 自己注册（invited_by IS NULL）；员工 = 被老板邀请创建
    is_owner = user.get("invited_by") is None

    if not tenant_id:
        return {"has_tenant": False, "is_owner": is_owner}

    tid = str(tenant_id)
    # Task 6A · Asia/Bangkok 时区(UTC+7)· 与 deduct_company_credits 锚点一致
    _bkk = _dt.timezone(_dt.timedelta(hours=7))
    year_month = _dt.datetime.now(_bkk).strftime("%Y-%m")

    if is_owner:
        balance_thb = 0.0
        pages_this_month = 0
        try:
            with db.get_cursor() as cur:
                cur.execute("SELECT balance_thb FROM tenant_credits WHERE tenant_id = %s", (tid,))
                row = cur.fetchone()
                if row:
                    balance_thb = float(row[0])
                cur.execute(
                    "SELECT pages_used FROM monthly_page_usage WHERE tenant_id = %s AND year_month = %s",
                    (tid, year_month),
                )
                row = cur.fetchone()
                if row:
                    pages_this_month = int(row[0])
        except Exception as e:
            logger.warning(f"get_my_credits owner DB: {e}")

        # 按用户拆分本月识别量（从 ocr_history 统计）
        user_breakdown = []
        try:
            with db.get_cursor() as cur:
                cur.execute("""
                    SELECT h.user_id::text,
                           COALESCE(u.username, split_part(u.email, '@', 1)) AS name,
                           COUNT(*) AS invoice_count
                    FROM ocr_history h
                    LEFT JOIN users u ON u.id::text = h.user_id::text
                    WHERE h.user_id::text IN (
                        SELECT id::text FROM users WHERE tenant_id = %s
                    )
                      AND DATE_TRUNC('month', h.created_at) = DATE_TRUNC('month', CURRENT_DATE)
                    GROUP BY h.user_id, u.username, u.email
                    ORDER BY invoice_count DESC
                    LIMIT 10
                """, (tid,))
                rows = cur.fetchall()
                user_breakdown = [
                    {"name": r["name"], "count": int(r["invoice_count"])}
                    for r in rows
                ]
        except Exception as e:
            logger.warning(f"get_my_credits breakdown: {e}")

        return {
            "has_tenant": True,
            "is_owner": True,
            "is_billing_exempt": is_exempt,
            "balance_thb": balance_thb,
            "pages_this_month": pages_this_month,
            "tier_threshold": 200,
            "current_rate": 0.75 if pages_this_month >= 200 else 1.5,
            "user_breakdown": user_breakdown,
        }
    else:
        # 员工：只返回自己本月发票数，不暴露任何余额/金额信息
        my_count = 0
        try:
            with db.get_cursor() as cur:
                cur.execute("""
                    SELECT COUNT(*) AS cnt
                    FROM ocr_history
                    WHERE user_id::text = %s
                      AND DATE_TRUNC('month', created_at) = DATE_TRUNC('month', CURRENT_DATE)
                """, (user_id,))
                row = cur.fetchone()
                if row:
                    my_count = int(row[0])
        except Exception as e:
            logger.warning(f"get_my_credits employee count: {e}")

        return {
            "has_tenant": True,
            "is_owner": False,
            "my_invoice_count": my_count,
        }


# ============================================================
# 充值申请 · 用户端 + 管理端
# ============================================================

async def _verify_slip_with_slipok(slip_abs_path: str, expected_amount_thb: float) -> dict:
    """验证泰国转账截图. ok=None → 未配置key, 走人工审核; ok=False → 验证未通过; ok=True → 自动approve."""
    import httpx as _httpx
    api_key = os.environ.get("SLIPOK_API_KEY", "")
    branch_id = os.environ.get("SLIPOK_BRANCH_ID", "")
    if not api_key or not branch_id:
        return {"ok": None, "error": "SLIPOK_API_KEY/SLIPOK_BRANCH_ID not configured"}
    try:
        fname = os.path.basename(slip_abs_path)
        mime = "image/png" if fname.endswith(".png") else "application/pdf" if fname.endswith(".pdf") else "image/jpeg"
        with open(slip_abs_path, "rb") as f:
            file_data = f.read()
        async with _httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                f"https://api.slipok.com/api/line/apikey/{branch_id}",
                headers={"x-authorization": api_key},
                files={"files": (fname, file_data, mime)},
                data={"log": "true"},
            )
        if resp.status_code != 200:
            logger.warning(f"SlipOK HTTP {resp.status_code}: {resp.text[:300]}")
            return {"ok": None, "error": f"SlipOK HTTP {resp.status_code}"}
        body = resp.json()
        if not body.get("success"):
            logger.warning(f"SlipOK !success: {body}")
            return {"ok": False, "error": str(body.get("message", "verification failed"))}
        d = body.get("data", {})
        verified_amount = float(d.get("amount", 0))
        sender = (d.get("sender") or {}).get("displayName", "")
        receiver = (d.get("receiver") or {}).get("displayName", "")
        transaction_id = d.get("transRef", "")
        amount_ok = abs(verified_amount - expected_amount_thb) <= 1.0
        logger.info(f"SlipOK result: verified={verified_amount} expected={expected_amount_thb} ok={amount_ok} ref={transaction_id}")
        return {
            "ok": amount_ok,
            "verified_amount": verified_amount,
            "sender": sender,
            "receiver": receiver,
            "transaction_id": transaction_id,
            "error": "" if amount_ok else f"amount {verified_amount} ≠ expected {expected_amount_thb}",
        }
    except Exception as e:
        logger.warning(f"_verify_slip_with_slipok exception: {e}")
        return {"ok": None, "error": str(e)}


class _TopupRequestBody(BaseModel):
    amount_thb: float = Field(..., gt=0, le=500000)
    payer_name: str = Field("", max_length=200)
    note: str = Field("", max_length=500)

class _AdminTopupApproveBody(BaseModel):
    actual_amount_thb: float = Field(..., gt=0)
    note: str = Field("", max_length=500)

class _AdminTopupRejectBody(BaseModel):
    note: str = Field("", max_length=500)


# ============================================================
# Multi-company (Task 3 · 不动 JWT · 用 users.active_tenant_id)
# ============================================================

class _SwitchCompanyBody(BaseModel):
    tenant_id: str = Field(..., min_length=8)


@app.get("/api/my-companies")
async def my_companies(request: Request):
    """返回当前用户隶属的所有公司列表 · 含 balance(仅 admin 角色可见) + 月用量"""
    user = get_current_user_from_request(request)
    user_id = str(user.get("id", ""))
    if not user_id:
        raise HTTPException(401, detail="auth.required")

    items = db.list_user_companies(user_id)

    # 取 active_tenant_id(若未设置则降级到 tenant_id)
    active_tid = None
    try:
        with db.get_cursor() as cur:
            cur.execute(
                "SELECT active_tenant_id, tenant_id FROM users WHERE id = %s::uuid",
                (user_id,)
            )
            row = cur.fetchone()
            if row:
                active_tid = str(row.get("active_tenant_id") or row.get("tenant_id") or "")
    except Exception as _e:
        logger.warning(f"my_companies active_tid lookup failed: {_e}")

    # admin 才看 balance · member 屏蔽 balance 字段(置 None)
    out = []
    for it in items:
        is_admin = (it.get("role") == "admin")
        out.append({
            "tenant_id": it["tenant_id"],
            "name": it["name"],
            "role": it["role"],
            "balance_thb": (it["balance_thb"] if is_admin else None),
            "pages_this_month": it["pages_this_month"],
            "is_active_tenant": (it["tenant_id"] == active_tid),
        })
    return {"companies": out, "active_tenant_id": active_tid}


@app.post("/api/switch-company")
async def switch_company(body: _SwitchCompanyBody, request: Request):
    """切换当前活动公司 · 校验归属后更新 users.active_tenant_id"""
    user = get_current_user_from_request(request)
    user_id = str(user.get("id", ""))
    if not user_id:
        raise HTTPException(401, detail="auth.required")
    ok = db.set_user_active_tenant(user_id, body.tenant_id)
    if not ok:
        raise HTTPException(403, detail="company.not_member")
    return {"ok": True, "active_tenant_id": body.tenant_id}


@app.post("/api/credits/topup/request")
async def credits_topup_request(req: _TopupRequestBody, request: Request):
    user = get_current_user_from_request(request)
    if user.get("invited_by") is not None:
        raise HTTPException(403, detail="credits.owner_only")
    tenant_id = user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(400, detail="credits.no_tenant")
    with db.get_cursor(commit=True) as cur:
        cur.execute("""
            INSERT INTO topup_requests (tenant_id, requested_by, amount_thb, payer_name, note)
            VALUES (%s, %s, %s, %s, %s) RETURNING id
        """, (str(tenant_id), str(user["id"]), req.amount_thb,
              req.payer_name.strip(), req.note.strip()))
        request_id = cur.fetchone()["id"]
    return {"request_id": request_id, "status": "pending"}


@app.post("/api/credits/topup/upload-slip/{request_id}")
async def credits_topup_upload_slip(request_id: int, request: Request, file: UploadFile = File(...)):
    user = get_current_user_from_request(request)
    uid = str(user.get("id", ""))
    tid = str(user.get("tenant_id") or "")
    with db.get_cursor() as cur:
        cur.execute("SELECT tenant_id, status, amount_thb FROM topup_requests WHERE id = %s", (request_id,))
        row = cur.fetchone()
    if not row:
        raise HTTPException(404, detail="topup.not_found")
    if str(row["tenant_id"]) != tid:
        raise HTTPException(403, detail="topup.forbidden")
    if row["status"] != "pending":
        raise HTTPException(400, detail="topup.already_reviewed")
    expected_amount = float(row["amount_thb"])
    content = await file.read()
    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(413, detail="topup.file_too_large")
    slips_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static", "slips")
    os.makedirs(slips_dir, exist_ok=True)
    fname = (file.filename or "slip.jpg").lower()
    ext = ".png" if fname.endswith(".png") else ".pdf" if fname.endswith(".pdf") else ".jpg"
    slip_filename = f"{request_id}{ext}"
    slip_abs = os.path.join(slips_dir, slip_filename)
    with open(slip_abs, "wb") as fp:
        fp.write(content)
    with db.get_cursor(commit=True) as cur:
        cur.execute("UPDATE topup_requests SET slip_path = %s WHERE id = %s",
                    (f"slips/{slip_filename}", request_id))
    # ── SlipOK 自动验证 ──────────────────────────────────────────
    slipok = await _verify_slip_with_slipok(slip_abs, expected_amount)
    if slipok.get("ok") is True:
        verified_amount = slipok["verified_amount"]
        ref = slipok.get("transaction_id", "")
        try:
            with db.get_cursor(commit=True) as cur:
                cur.execute("""UPDATE topup_requests SET status='approved', reviewed_at=NOW(),
                    review_note=%s, amount_thb=%s WHERE id=%s""",
                    (f"SlipOK auto-approved · ref={ref}", verified_amount, request_id))
                cur.execute("""INSERT INTO tenant_credits (tenant_id, balance_thb) VALUES (%s, %s)
                    ON CONFLICT (tenant_id) DO UPDATE
                    SET balance_thb = tenant_credits.balance_thb + %s, updated_at = NOW()
                    RETURNING balance_thb""", (tid, verified_amount, verified_amount))
                new_balance = float(cur.fetchone()["balance_thb"])
                cur.execute("""INSERT INTO credit_transactions
                    (tenant_id, user_id, type, amount_thb, balance_after, description)
                    VALUES (%s::uuid, %s::uuid, 'topup', %s, %s, %s)""",
                    (tid, uid, verified_amount, new_balance,
                     f"SlipOK自动充值 · #{request_id} · ref={ref}"))
            logger.info(f"[topup] SlipOK auto-approved #{request_id} ฿{verified_amount} tenant={tid[:8]}")
            return {"ok": True, "auto_approved": True, "balance_thb": new_balance,
                    "slip_path": f"slips/{slip_filename}"}
        except Exception as e:
            logger.error(f"SlipOK auto-approve DB error: {e}")
            # Fall through to manual review
    # ── 人工审核 (no key, ok=False, or auto-approve DB error) ────
    return {"ok": True, "auto_approved": False, "slip_path": f"slips/{slip_filename}"}


@app.get("/api/credits/topup/history")
async def credits_topup_history(request: Request):
    user = get_current_user_from_request(request)
    tid = str(user.get("tenant_id") or "")
    if not tid:
        return []
    with db.get_cursor() as cur:
        cur.execute("""
            SELECT id, amount_thb, payer_name, note, status, slip_path,
                   review_note, created_at, reviewed_at
            FROM topup_requests WHERE tenant_id = %s
            ORDER BY created_at DESC LIMIT 20
        """, (tid,))
        rows = cur.fetchall()
    return [
        {"id": r["id"], "amount_thb": float(r["amount_thb"]),
         "payer_name": r["payer_name"] or "", "note": r["note"] or "",
         "status": r["status"], "slip_path": r["slip_path"],
         "review_note": r["review_note"] or "",
         "created_at": r["created_at"].isoformat() if r["created_at"] else None,
         "reviewed_at": r["reviewed_at"].isoformat() if r["reviewed_at"] else None}
        for r in rows
    ]


@app.get("/api/credits/usage-history")
async def credits_usage_history(request: Request, page: int = 1, per_page: int = 20, user_id: str = None):
    user = get_current_user_from_request(request)
    tid = str(user.get("tenant_id") or "")
    if not tid:
        return {"rows": [], "total": 0, "page": page, "per_page": per_page, "is_owner": False, "members": []}
    is_owner = user.get("invited_by") is None
    if not is_owner:
        user_id = str(user["id"])
    per_page = min(50, max(1, per_page))
    offset = (max(1, page) - 1) * per_page
    uid_sql = "AND ct.user_id = %s::uuid" if user_id else ""
    uid_params = [user_id] if user_id else []
    try:
        with db.get_cursor() as cur:
            cur.execute(f"""
                SELECT COUNT(*) AS n FROM credit_transactions ct
                WHERE ct.tenant_id = %s::uuid AND ct.type = 'usage' {uid_sql}
            """, [tid] + uid_params)
            total = int(cur.fetchone()["n"])
            cur.execute(f"""
                SELECT
                    ct.created_at, ct.pages, ct.amount_thb AS cost_thb, ct.balance_after,
                    u.email AS user_email, u.username AS user_name,
                    oh.filename
                FROM credit_transactions ct
                LEFT JOIN users u ON u.id = ct.user_id::uuid
                LEFT JOIN ocr_history oh
                    ON oh.user_id = ct.user_id::uuid
                    AND oh.tenant_id = ct.tenant_id::uuid
                    AND ct.description LIKE '%% · ' || LEFT(oh.id::text, 8)
                WHERE ct.tenant_id = %s::uuid AND ct.type = 'usage' {uid_sql}
                ORDER BY ct.created_at DESC
                LIMIT %s OFFSET %s
            """, [tid] + uid_params + [per_page, offset])
            rows = cur.fetchall()
    except Exception as e:
        logger.warning(f"credits_usage_history: {e}")
        return {"rows": [], "total": 0, "page": page, "per_page": per_page, "is_owner": is_owner, "members": []}
    members = []
    if is_owner:
        try:
            with db.get_cursor() as cur:
                cur.execute("""
                    SELECT id, email, username FROM users
                    WHERE tenant_id = %s::uuid AND is_active = TRUE ORDER BY email
                """, (tid,))
                members = [{"id": str(r["id"]), "email": r["email"] or "", "username": r["username"] or ""} for r in cur.fetchall()]
        except Exception:
            pass
    return {
        "is_owner": is_owner,
        "rows": [{
            "date": r["created_at"].isoformat() if r["created_at"] else None,
            "user_email": r["user_email"] or "",
            "user_name": r["user_name"] or "",
            "filename": r["filename"] or "",
            "pages": int(r["pages"] or 0),
            "cost_thb": float(r["cost_thb"] or 0),
            "balance_after": float(r["balance_after"]) if r["balance_after"] is not None else None,
        } for r in rows],
        "total": total,
        "page": page,
        "per_page": per_page,
        "members": members,
    }


@app.get("/api/credits/usage-report")
async def credits_usage_report(
    request: Request,
    start_date: str = None,
    end_date: str = None,
    format: str = "pdf",
    user_id: str = None,
    lang: str = "zh",
):
    """导出使用明细报告 · PDF/XLSX · 按用户分组."""
    import datetime as _dt
    import usage_report as _ur

    user = get_current_user_from_request(request)
    tid = str(user.get("tenant_id") or "")
    if not tid:
        raise HTTPException(status_code=400, detail="no_tenant")

    is_owner = user.get("invited_by") is None
    if not is_owner:
        user_id = str(user["id"])  # 员工只能导出自己

    today = _dt.date.today()
    try:
        if start_date:
            sd = _dt.date.fromisoformat(start_date)
        else:
            sd = today.replace(day=1)
        if end_date:
            ed = _dt.date.fromisoformat(end_date)
        else:
            ed = today
    except Exception:
        raise HTTPException(status_code=400, detail="invalid_date")

    if ed < sd:
        raise HTTPException(status_code=400, detail="end_before_start")

    fmt = (format or "pdf").lower()
    if fmt not in ("pdf", "xlsx"):
        raise HTTPException(status_code=400, detail="invalid_format")
    if lang not in ("zh", "en", "th", "ja"):
        lang = "zh"

    ed_exclusive = ed + _dt.timedelta(days=1)

    uid_sql = ""
    uid_params: list = []
    if user_id:
        uid_sql = "AND ct.user_id = %s::uuid"
        uid_params = [user_id]

    rows: list = []
    company = ""
    try:
        with db.get_cursor() as cur:
            cur.execute("SELECT name FROM tenants WHERE id = %s::uuid", (tid,))
            trow = cur.fetchone()
            if trow:
                company = trow.get("name") or ""
            cur.execute(f"""
                SELECT
                    ct.user_id::text AS user_id,
                    ct.created_at,
                    ct.pages,
                    ct.amount_thb AS cost_thb,
                    u.email AS user_email,
                    u.username AS user_name,
                    oh.filename
                FROM credit_transactions ct
                LEFT JOIN users u ON u.id = ct.user_id::uuid
                LEFT JOIN ocr_history oh
                    ON oh.user_id = ct.user_id::uuid
                    AND oh.tenant_id = ct.tenant_id::uuid
                    AND ct.description LIKE '%% · ' || LEFT(oh.id::text, 8)
                WHERE ct.tenant_id = %s::uuid
                  AND ct.type = 'usage'
                  AND ct.created_at >= %s
                  AND ct.created_at < %s
                  {uid_sql}
                ORDER BY u.email NULLS LAST, ct.created_at ASC
            """, [tid, sd, ed_exclusive] + uid_params)
            for r in cur.fetchall():
                rows.append({
                    "user_id": r["user_id"],
                    "date": r["created_at"].isoformat() if r["created_at"] else None,
                    "pages": int(r["pages"] or 0),
                    "cost_thb": float(r["cost_thb"] or 0),
                    "user_email": r["user_email"] or "",
                    "user_name": r["user_name"] or "",
                    "filename": r["filename"] or "",
                })
    except HTTPException:
        raise
    except Exception as e:
        logger.warning(f"credits_usage_report query: {e}")
        raise HTTPException(status_code=500, detail="query_failed")

    safe_tenant = "".join(ch for ch in (company or "tenant") if ch.isalnum() or ch in "-_")[:24] or "tenant"
    fname_stem = f"pearnly_usage_{safe_tenant}_{sd.strftime('%Y%m%d')}_{ed.strftime('%Y%m%d')}"

    try:
        if fmt == "pdf":
            data = _ur.build_pdf(
                lang=lang, company=company or "—",
                start_date=sd.isoformat(), end_date=ed.isoformat(), rows=rows,
            )
            return Response(
                content=data, media_type="application/pdf",
                headers={"Content-Disposition": f'attachment; filename="{fname_stem}.pdf"'},
            )
        else:
            data = _ur.build_xlsx(
                lang=lang, company=company or "—",
                start_date=sd.isoformat(), end_date=ed.isoformat(), rows=rows,
            )
            return Response(
                content=data,
                media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                headers={"Content-Disposition": f'attachment; filename="{fname_stem}.xlsx"'},
            )
    except Exception as e:
        logger.error(f"credits_usage_report build {fmt}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"build_failed: {e}")


@app.get("/api/admin/credits/topup/requests")
async def admin_topup_list(request: Request, status: str = "pending"):
    _require_super_admin(request)
    where = "" if status == "all" else "WHERE tr.status = %s"
    params = () if status == "all" else (status,)
    with db.get_cursor() as cur:
        cur.execute(f"""
            SELECT tr.id, tr.amount_thb, tr.payer_name, tr.note,
                   tr.status, tr.slip_path, tr.review_note,
                   tr.created_at, tr.reviewed_at,
                   u.username, u.email, t.name AS tenant_name
            FROM topup_requests tr
            LEFT JOIN users u ON u.id = tr.requested_by
            LEFT JOIN tenants t ON t.id = tr.tenant_id
            {where}
            ORDER BY tr.created_at DESC LIMIT 100
        """, params)
        rows = cur.fetchall()
    return [
        {"id": r["id"], "amount_thb": float(r["amount_thb"]),
         "payer_name": r["payer_name"] or "", "note": r["note"] or "",
         "status": r["status"], "slip_path": r["slip_path"] or "",
         "review_note": r["review_note"] or "",
         "created_at": r["created_at"].isoformat() if r["created_at"] else None,
         "reviewed_at": r["reviewed_at"].isoformat() if r["reviewed_at"] else None,
         "username": r["username"] or "", "email": r["email"] or "",
         "tenant_name": r["tenant_name"] or ""}
        for r in rows
    ]


@app.post("/api/admin/credits/topup/approve/{request_id}")
async def admin_topup_approve(request_id: int, body: _AdminTopupApproveBody, request: Request):
    _require_super_admin(request)
    admin_user = get_current_user_from_request(request)
    admin_id = str(admin_user["id"])
    with db.get_cursor(commit=True) as cur:
        cur.execute(
            "SELECT tenant_id, status FROM topup_requests WHERE id = %s FOR UPDATE",
            (request_id,))
        row = cur.fetchone()
        if not row:
            raise HTTPException(404, detail="topup.not_found")
        if row["status"] != "pending":
            raise HTTPException(400, detail="topup.already_reviewed")
        tid = str(row["tenant_id"])
        amt = body.actual_amount_thb
        cur.execute("""UPDATE topup_requests SET status='approved', reviewed_by=%s,
            reviewed_at=NOW(), review_note=%s, amount_thb=%s WHERE id=%s""",
            (admin_id, body.note, amt, request_id))
        cur.execute("""INSERT INTO tenant_credits (tenant_id, balance_thb) VALUES (%s, %s)
            ON CONFLICT (tenant_id) DO UPDATE
            SET balance_thb = tenant_credits.balance_thb + %s, updated_at = NOW()
            RETURNING balance_thb""", (tid, amt, amt))
        new_balance = float(cur.fetchone()["balance_thb"])
        cur.execute("""INSERT INTO credit_transactions
            (tenant_id, user_id, type, amount_thb, balance_after, description)
            VALUES (%s, %s, 'topup', %s, %s, %s)""",
            (tid, admin_id, amt, new_balance, f"充值审核通过 · 申请#{request_id}"))
    # Task 5 · 通知 tenant owner(失败不影响主流程)
    try:
        send_topup_approved_email(tid, amt, new_balance)
    except Exception as _e:
        logger.warning(f"[email] topup_approved trigger skipped: {_e}")
    return {"ok": True, "new_balance": new_balance}


@app.post("/api/admin/credits/topup/reject/{request_id}")
async def admin_topup_reject(request_id: int, body: _AdminTopupRejectBody, request: Request):
    _require_super_admin(request)
    admin_user = get_current_user_from_request(request)
    admin_id = str(admin_user["id"])
    with db.get_cursor(commit=True) as cur:
        cur.execute("SELECT status FROM topup_requests WHERE id = %s", (request_id,))
        row = cur.fetchone()
        if not row:
            raise HTTPException(404, detail="topup.not_found")
        if row["status"] != "pending":
            raise HTTPException(400, detail="topup.already_reviewed")
        cur.execute("""UPDATE topup_requests SET status='rejected', reviewed_by=%s,
            reviewed_at=NOW(), review_note=%s WHERE id=%s""",
            (admin_id, body.note, request_id))
    return {"ok": True}




if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=int(os.environ.get("PORT", "7860")), reload=True)
