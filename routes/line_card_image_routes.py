# -*- coding: utf-8 -*-
"""泰语图卡出图(公开 · LINE imagemap/图片消息按 baseUrl/{size} 取图)。

LINE 渲染 imagemap 时会请求 {baseUrl}/{width}(width ∈ 240/300/460/700/1040,无扩展名),
普通图片消息直接请求 .../1040。本路由忽略具体尺寸、统一返回 1040 母图(JPEG),LINE 自适配缩放。
公开无需登录(图本身非敏感 · 仅服务已交付的固定卡 · stem 白名单防穿越)。
"""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from services.line_binding.line_imagemap import CARD_STEMS

router = APIRouter()

_CARDS_DIR = Path(__file__).resolve().parent.parent / "static" / "line-cards"


@router.get("/api/line/card/{card}/{size}")
def get_line_card_image(card: str, size: str) -> FileResponse:
    if card not in CARD_STEMS:
        raise HTTPException(status_code=404, detail="unknown card")
    path = _CARDS_DIR / f"{card}.jpg"
    if not path.exists():
        raise HTTPException(status_code=404, detail="card image missing")
    return FileResponse(
        path=str(path),
        media_type="image/jpeg",
        headers={"Cache-Control": "public, max-age=86400"},
    )
