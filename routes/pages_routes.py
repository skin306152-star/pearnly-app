from __future__ import annotations

"""
pages_routes.py · 静态页面服务 + 公开 meta 路由(health / contact)
REFACTOR-B1 · 第二十会话从 app.py 抽出 · 0 业务逻辑改 · 纯后端搬家

包含:
  页面服务(HTMLResponse / FileResponse · 全公开 · 无鉴权):
    /                   → static/landing/portal.dc.html(品牌门户 · no-cache · 脸0 2026-07-10)
    /login              → static/dist/login.html(原登录页 · no-cache)
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

# 页面外壳统一 no-cache(防浏览器缓存旧壳 → 内部 ?v= bump 失效拿不到新版)。
# 所有返回 HTML 页面入口的路由共用这一份,别再内联复制。
_NO_CACHE = {
    "Cache-Control": "no-cache, no-store, must-revalidate",
    "Pragma": "no-cache",
    "Expires": "0",
}


# ============================================================
# Health & Contact(公开)
# ============================================================
@router.get("/api/health")
async def health():
    # 新架构 · pipeline_v1 唯一路径 · 健康检查改为校验 GCP Service Account 就绪。
    # 只对外暴露就绪布尔:凭证文件路径属敏感信息,免鉴权端点不得回显(安全评估 2026-07-07 M1)。
    _creds = (os.environ.get("GOOGLE_APPLICATION_CREDENTIALS") or "").strip()
    credentials_status = {"available": bool(_creds and os.path.isfile(_creds))}
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
        "line_id": os.environ.get("CONTACT_LINE", "@pearnly"),
        "line_url": os.environ.get("CONTACT_LINE_URL", "https://line.me/R/ti/p/@pearnly"),
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
    # 脸0(2026-07-10)· / = 品牌门户(4 产品分流)· 原登录页挪 /login · 门户自托管在 static/landing/ 直发不进 dist · no-cache。
    return FileResponse("static/landing/portal.dc.html", headers=_NO_CACHE)


@router.get("/login", response_class=HTMLResponse)
async def login_page():
    return FileResponse("static/dist/login.html", headers=_NO_CACHE)


@router.get("/home", response_class=HTMLResponse)
async def home():
    # v118.27.5.4 · 强制 no-cache · 防 CDN/浏览器误缓存导致用户拿不到新版
    return FileResponse("static/dist/home.html", headers=_NO_CACHE)


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
    return FileResponse("static/admin/admin.html", headers=_NO_CACHE)


# POS 收银前台 SPA(PS-5 迁址 · 2026-07-10)· 收银台新家在 /cashier(与老板后台 /pos 分家,
# 消除混淆)· 独立 plain-script SPA(参考 admin layout)。/cashier · /cashier/{rest:path} 全返回
# static/pos/pos.html;鉴权由前端 pos.js 落地(PIN 登录 + 收银员 token)。老径 /pos 改作老板后台
# 登录页(见下,带老设备接回 /cashier 的 guard);老收银设备装的旧 PWA(scope /pos + cache-first
# service worker)继续吐缓存老壳照常收银,零感知。
def _cashier_page() -> FileResponse:
    return FileResponse("static/dist/pos.html", headers=_NO_CACHE)


@router.get("/pos-sw.js")
async def pos_service_worker():
    # 老收银设备的 service worker(scope /pos)· 字节保持不动 → 旧 PWA 不触发更新、继续缓存老壳。
    # no-cache:SW 字节若变更要即时被浏览器拾取。新收银台走 /cashier-sw.js(scope /cashier)。
    return FileResponse(
        "static/pos/pos-sw.js", media_type="application/javascript", headers=_NO_CACHE
    )


@router.get("/cashier-sw.js")
async def cashier_service_worker():
    # 收银台新家的 Service Worker:从根路径出 → 可注册 scope=/cashier(控 /cashier 导航、离线重开壳)。
    # 与 /pos-sw.js 各自独立作用域,互不影响(老设备的 /pos 旧 SW 原样保留)。
    return FileResponse(
        "static/pos/cashier-sw.js", media_type="application/javascript", headers=_NO_CACHE
    )


@router.get("/cashier", response_class=HTMLResponse)
async def cashier_page():
    return _cashier_page()


@router.get("/cashier/{rest:path}", response_class=HTMLResponse)
async def cashier_layout_page(rest: str):
    return _cashier_page()


# 管理控制台 SPA(权限批3 · 2026-06-10)· 照 /cashier 套路:独立 static/console 自含,
# 登录态前端鉴权(can(team.member.view) 不过 → 403 人话页)。紫色主题只作用 /console。
@router.get("/console", response_class=HTMLResponse)
async def console_page():
    return FileResponse("static/dist/console.html", headers=_NO_CACHE)


@router.get("/console/{rest:path}", response_class=HTMLResponse)
async def console_layout_page(rest: str):
    return FileResponse("static/dist/console.html", headers=_NO_CACHE)


# 邀请接受公开页(无登录态 · token 在路径上由前端 JS 读取)
@router.get("/invite/{token}", response_class=HTMLResponse)
async def invite_page(token: str):
    return FileResponse("static/dist/invite.html", headers=_NO_CACHE)


# Pearnly AI SPA(M1-W2)· 照 /console 先例:友好路由指向打包壳,鉴权/闸判定在前端
# ai.js 里跑(闸关/未登录 → 整页跳 /home,见 ai.js boot() 注释)。
@router.get("/ai", response_class=HTMLResponse)
async def ai_page():
    return FileResponse("static/dist/ai.html", headers=_NO_CACHE)


@router.get("/ai/{rest:path}", response_class=HTMLResponse)
async def ai_layout_page(rest: str):
    return FileResponse("static/dist/ai.html", headers=_NO_CACHE)


# POS 老板后台专属登录页(PS-5 · 主域路径 /pos · pos.pearnly.com 子域方案已废弃)。
# 只有邮箱+密码,无 Google/LINE/注册。页头 guard:本机存过收银台绑定凭据(pos_store_token)→
# 即跳 /cashier;否则渲染老板登录页。收银台 SPA 迁至 /cashier(见上)。不碰根路由 `/`(脸 0 门户在改)。
def _pos_owner_login() -> HTMLResponse:
    from routes.pos_login_page import POS_LOGIN_HTML

    return HTMLResponse(POS_LOGIN_HTML, headers=_NO_CACHE)


@router.get("/pos", response_class=HTMLResponse)
async def pos_owner_login_page():
    return _pos_owner_login()


@router.get("/pos/{rest:path}", response_class=HTMLResponse)
async def pos_owner_login_layout(rest: str):
    return _pos_owner_login()


# Earn 超管后台专属登录页(主域路径 /earn · 2026-07-10 Zihao 拍板)。只有账号+密码,
# 登录后前端打 /api/me 复核 is_super_admin(与 admin.js 鉴权同一事实源),非超管不落 token。
# admin.js 无登录态/鉴权失败统一甩回本页。内联 HTML 原因同 reset_page。
@router.get("/earn", response_class=HTMLResponse)
async def earn_login_page():
    from routes.earn_login_page import EARN_LOGIN_HTML

    return HTMLResponse(EARN_LOGIN_HTML, headers=_NO_CACHE)


@router.get("/reset", response_class=HTMLResponse)
async def reset_page():
    # 内联 HTML(非 static 文件)· 见 routes/reset_page.py 头注:webhook 不拾取新增 static 根文件
    from routes.reset_page import RESET_PAGE_HTML

    return HTMLResponse(RESET_PAGE_HTML, headers=_NO_CACHE)


@router.get("/terms", response_class=HTMLResponse)
async def terms_page():
    return FileResponse("static/terms.html", headers=_NO_CACHE)


@router.get("/privacy", response_class=HTMLResponse)
async def privacy_page():
    return FileResponse("static/privacy.html", headers=_NO_CACHE)
