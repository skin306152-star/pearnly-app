from __future__ import annotations

"""
pages_routes.py · 静态页面服务 + 公开 meta 路由(health / contact)
REFACTOR-B1 · 第二十会话从 app.py 抽出 · 0 业务逻辑改 · 纯后端搬家

包含:
  页面服务(HTMLResponse / FileResponse · 全公开 · 无鉴权):
    /                   → static/login.html(no-cache)
    /login              → static/login.html(no-cache)
    /home               → static/home.html(no-cache)
    /admin              → 301 redirect → /admin/cost
    /admin/{rest:path}  → static/admin/admin.html(SPA · no-cache)
    /reset              → static/reset.html
    /terms              → static/terms.html
    /privacy            → static/privacy.html
  公开 meta:
    /api/health · /api/contact · /api/v1/health · /api/v1/contact

留在 app.py(不搬 · 故意):
    /api/version —— 铁律 #6「每次部署写 4 语 release_notes」的固定锚点;
                    且读 PEARNLY_FRONTEND_VERSION 模块全局
                    (admin_diagnostics_routes 也 lazy `import app` 读它)。
"""

import asyncio
import os

from fastapi import APIRouter
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse

router = APIRouter()


# ============================================================
# Health & Contact(公开)
# ============================================================
@router.get("/api/health")
async def health():
    # 新架构 · pipeline_v1 唯一路径 · 健康检查改为校验 GCP Service Account 就绪
    _creds = (os.environ.get("GOOGLE_APPLICATION_CREDENTIALS") or "").strip()
    if _creds and os.path.isfile(_creds):
        credentials_status = {"available": True, "path": _creds}
    elif _creds:
        credentials_status = {"available": False, "error": f"file not found: {_creds}"}
    else:
        credentials_status = {
            "available": False,
            "error": "GOOGLE_APPLICATION_CREDENTIALS env not set",
        }
    return {
        "status": "ok",
        "version": "0.18.5-v105",
        "engines": {
            "pipeline": "pipeline_v1",
            "layers": ["text_path", "vision", "flash-lite", "flash"],
            "credentials_status": credentials_status,
        },
    }


@router.get("/api/ready")
async def ready():
    # REFACTOR-WA-B4 · 真探活(铁律 #23.7)· 区别于 /api/health 永远 ok:
    #   真跑 DB SELECT 1 + 探 Gemini/SMTP/LINE 配置就绪 · 任一挂返 503。
    #   探针是 sync(psycopg2 阻塞)→ to_thread 卸载 · 不堵 event loop(铁律 #10)。
    from services.readiness.probes import run_readiness

    result = await asyncio.to_thread(run_readiness)
    status_code = 200 if result.get("ready") else 503
    return JSONResponse(content=result, status_code=status_code)


@router.get("/api/contact")
async def contact():
    return {
        "phone": os.environ.get("CONTACT_PHONE", "086-889-2228"),
        "line_id": os.environ.get("CONTACT_LINE", "@Pearnly"),
        "line_url": os.environ.get("CONTACT_LINE_URL", "https://line.me/R/ti/p/@059oupmg"),
        "email": os.environ.get("CONTACT_EMAIL", "hello@pearnly.com"),
        "address": os.environ.get("CONTACT_ADDRESS", "Bangkok, Thailand"),
    }


@router.get("/api/v1/health")
async def v1_health():
    return await health()


@router.get("/api/v1/contact")
async def v1_contact():
    return await contact()


# ============================================================
# 静态 + 根路由
# ============================================================
@router.get("/", response_class=HTMLResponse)
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


@router.get("/login", response_class=HTMLResponse)
async def login_page():
    return FileResponse(
        "static/login.html",
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0",
        },
    )


@router.get("/home", response_class=HTMLResponse)
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
@router.get("/admin", response_class=HTMLResponse)
async def admin_page():
    from fastapi.responses import RedirectResponse

    return RedirectResponse(url="/admin/cost", status_code=301)


# v118.44.0 · NAV-IA Phase 8 · Earn 超管独立 admin layout(SPA)
# 路径 /admin/cost · /admin/users · /admin/* 全部返回独立 static/admin/admin.html
# 鉴权由前端 admin.js 调 /api/me + is_super_admin 校验(非超管 → 跳 /)
# 老的 /admin URL(L4209)仍返回 home.html · 作 PEARNLY_ADMIN_MODE 老逻辑兜底
@router.get("/admin/{rest:path}", response_class=HTMLResponse)
async def admin_layout_page(rest: str):
    return FileResponse(
        "static/admin/admin.html",
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0",
        },
    )


@router.get("/reset", response_class=HTMLResponse)
async def reset_page():
    return FileResponse("static/reset.html")


@router.get("/terms", response_class=HTMLResponse)
async def terms_page():
    return FileResponse("static/terms.html")


@router.get("/privacy", response_class=HTMLResponse)
async def privacy_page():
    return FileResponse("static/privacy.html")
