# -*- coding: utf-8 -*-
"""
Pearnly · Admin Diagnostics / Internal Deploy 路由模块
(EXECUTION_PLAN 阶段 5 Task 5.2 · 2026-05-22 抽出)

从 app.py L5438-5678 整片搬过来 · 纯搬家 · URL / response shape 0 改动。

覆盖 5 个 route handler:
  GET    /api/admin/diagnostics/runtime    · 超管诊断(playwright/last_500/version)
  POST   /internal/deploy                   · GitHub webhook 自动部署
  GET    /internal/deploy/manual            · 浏览器手动触发部署
  GET    /internal/deploy/log               · 查看部署日志 tail
  GET    /internal/install-playwright       · 部署 Playwright + chromium
  POST   /internal/install-playwright       · 同上 · POST 别名

抽出 1 个 helper(EXECUTION_PLAN Task 5.2 "统一 secret 校验"):
  _require_internal_token(token)  · 3 个 /internal/* 路由共用 · 比对 GITHUB_WEBHOOK_SECRET
  (POST /internal/deploy 用 HMAC 签名 · 不是 token · 不走这个 helper)

循环 import 解法:
  /api/admin/diagnostics/runtime 依赖 app.py 的全局 _last_500_event(mutable dict ·
  被全局 exception handler 实时写入)+ PEARNLY_FRONTEND_VERSION + _read_playwright_status·
  本文件顶层 NOT import app · handler 内部运行时 import(此时 app module init 完成)。
"""

from __future__ import annotations

import logging
import os
from typing import Any, Dict

from fastapi import APIRouter, HTTPException, Request

from auth import get_current_user_from_request

logger = logging.getLogger("mr-pilot")
router = APIRouter()


# ============================================================
# 局部 helper · 跟 billing_routes.py 同款(8 行 super-admin 守门 · 复制不抽公共)
# ============================================================
def _require_super_admin(request: Request) -> Dict[str, Any]:
    """超级管理员守门员 · 非超管 403"""
    from fastapi import status
    user = get_current_user_from_request(request)
    if not user.get("is_super_admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="admin.not_super_admin",
        )
    return user


# ============================================================
# 统一 internal/* token 校验(EXECUTION_PLAN Task 5.2 拍板)
# 原来 3 个 /internal/* 路由都重复 4 行内联 check · 抽 1 个 helper
# (POST /internal/deploy 用 HMAC 签名 · 不走这个)
# ============================================================
def _require_internal_token(token: str) -> None:
    """比对 token == GITHUB_WEBHOOK_SECRET env · 不等就 403"""
    secret = os.environ.get("GITHUB_WEBHOOK_SECRET", "")
    if not secret or token != secret:
        raise HTTPException(status_code=403, detail="Invalid token")


# ── 超管诊断接口 (v118.35.0.28 · 体检 P0-02 2026-05-21) ───────────────────
# 这里收纳所有原先暴露在 /api/version 的内部诊断字段:
#   · playwright 状态 (安装情况 / 浏览器路径 / chromium probe)
#   · last_500 (最近一次未捕获 500 的 path/method/exc_type/traceback)
#   · 前端 cache_bust 等运行时状态
# 仅超管能访问 · 普通用户 403 · 未登录 401
# 体检 P0-03 让全局异常 handler 不再返回 traceback · 运维要看根因走这里
@router.get("/api/admin/diagnostics/runtime")
async def admin_diagnostics_runtime(request: Request):
    _require_super_admin(request)
    import time as _t
    # Lazy import 解循环 import:app.py 也 import 本模块 · 顶层不能 import app
    # 此时(handler 执行时)app module 已经完成 init · 全局变量都已就绪
    import app as _app
    return {
        "ok": True,
        "ts": int(_t.time()),
        "version": _app.PEARNLY_FRONTEND_VERSION,
        "playwright": _app._read_playwright_status(),
        "last_500": _app._read_last_500(),
    }


# ── GitHub Webhook 自动部署 (v118.41.133 · 2026-05-17) ──────────────────────
# Claude 每次 git push → GitHub → 触发这个接口 → 服务器自动 pull + restart
# 无需 SSH · 彻底绕开 fail2ban 问题
@router.post("/internal/deploy")
async def github_deploy_webhook(request: Request):
    """
    GitHub Webhook → 触发 git-deploy.sh
    关键修复：先发响应，再用 detached subprocess 执行部署脚本。
    这样 systemctl restart 不会在发送响应前就把自己杀掉。

    v118.35.0.28 安全修(P0 体检 2026-05-21) · fail-closed:
    GITHUB_WEBHOOK_SECRET 缺失时直接 503 拒服务 · 不再降级成无鉴权 ·
    避免运维忘记配 secret 时被任意人触发 git pull + restart。
    """
    import hmac as _hmac, hashlib as _hashlib, subprocess as _subprocess, os as _os
    body = await request.body()
    secret = _os.environ.get("GITHUB_WEBHOOK_SECRET", "")
    if not secret:
        logger.error("[git-deploy] GITHUB_WEBHOOK_SECRET not configured · refusing webhook")
        raise HTTPException(status_code=503, detail="webhook secret not configured")
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


@router.get("/internal/deploy/manual")
async def manual_deploy_trigger(token: str = ""):
    """
    备用手动部署触发器（webhook 失败时使用）。
    访问：https://pearnly.com/internal/deploy/manual?token=<GITHUB_WEBHOOK_SECRET>
    无需 SSH，浏览器直接触发。
    """
    _require_internal_token(token)
    import subprocess as _subprocess
    logger.info("[git-deploy] manual trigger")
    _subprocess.Popen(
        ["bash", "-c", "sleep 1 && bash /opt/mrpilot/git-deploy.sh >> /var/log/mrpilot-deploy.log 2>&1"],
        close_fds=True,
        start_new_session=True,
    )
    return {"ok": True, "status": "manual deploy scheduled", "log": "/var/log/mrpilot-deploy.log"}


@router.get("/internal/deploy/log")
async def deploy_log(token: str = "", lines: int = 50):
    """查看最近部署日志。"""
    _require_internal_token(token)
    import subprocess as _subprocess
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
@router.get("/internal/install-playwright")
@router.post("/internal/install-playwright")
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
    _require_internal_token(token)
    import subprocess as _subprocess
    import shutil as _shutil

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
