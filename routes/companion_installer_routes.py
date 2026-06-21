# -*- coding: utf-8 -*-
"""小助手安装包下载(登录鉴权 · GET /api/companion/installer)。

setup.exe 部署在 static/companion/PearnlyCompanion-Setup.exe。登录用户在集成页点
「下载小助手」→ FE 带 Bearer fetch 此路由 → 返回 exe。未登录 401。文件缺失 404(尚未发布)。
"""

import os

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import FileResponse

from core.auth import get_current_user_from_request

router = APIRouter()

_INSTALLER = os.path.join("static", "companion", "PearnlyCompanion-Setup.exe")


@router.get("/api/companion/installer")
async def download_companion_installer(request: Request):
    """下载小助手安装包(登录鉴权)。"""
    get_current_user_from_request(request)
    if not os.path.exists(_INSTALLER):
        raise HTTPException(404, detail="companion.installer_not_ready")
    return FileResponse(
        _INSTALLER,
        media_type="application/octet-stream",
        filename="PearnlyCompanion-Setup.exe",
    )
