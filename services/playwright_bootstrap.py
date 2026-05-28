# -*- coding: utf-8 -*-
"""
Pearnly · Playwright 启动自举 / 诊断模块 (REFACTOR-WA-B1 · 2026-05-29 从 app.py 抽出)

纯搬家 · 0 逻辑改 · app.py lifespan 调 ensure_playwright_installed() ·
admin_diagnostics_routes /api/admin/diagnostics/runtime 调 read_playwright_status()。

3 个函数(原 app.py L162-480 · 私有下划线名去掉 · 成为本模块公开 API):
  · probe_chromium_launch()     — 真启动 chromium 探活 · 永不 raise · 返 {"ok": bool, ...}
  · ensure_playwright_installed() — 启动期快查 + 缺件后台 detached 装 + 自 restart
  · read_playwright_status()    — 读 /tmp 状态快照 + 实时 re-probe · 给 /api/version 暴露
"""

import logging

logger = logging.getLogger("mr-pilot")


def probe_chromium_launch():
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


def ensure_playwright_installed():
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
        launch_result = probe_chromium_launch()
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


def read_playwright_status():
    """Read the status snapshot written by ensure_playwright_installed.
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
