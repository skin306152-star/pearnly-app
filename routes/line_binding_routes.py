from __future__ import annotations

"""
line_binding_routes.py · LINE 账号绑定 + 用户偏好语言路由
REFACTOR-B1 · 第二十会话从 app.py 抽出 · 0 业务逻辑改 · 纯后端搬家

包含 4 路由 + 3 model(全自包含 · 每个路由只调一个 db.* 函数 + get_current_user_from_request):
    POST   /api/line/binding-code  → LineBindingCodeResponse · db.generate_line_binding_code
    GET    /api/line/binding       → LineBindingInfo · db.get_line_binding_by_user
    DELETE /api/line/binding       → db.unbind_line_by_user
    POST   /api/me/lang            → UpdateLangRequest · db.update_user_preferred_lang
                                     (用户偏好语言 · 用于 LINE Bot / 邮件等非网页场景回复)

留在 app.py(不搬 · 故意):/api/line/webhook(LINE 事件分发 · 勿碰)·
    /api/me/needs_email · /api/me/line_complete_email(与 OAuth/邮箱验证码流程纠缠)。
"""

import os
from typing import Optional

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from core import db
from core.auth import get_current_user_from_request

router = APIRouter()


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


@router.post("/api/line/binding-code", response_model=LineBindingCodeResponse)
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


@router.get("/api/line/binding", response_model=LineBindingInfo)
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


@router.delete("/api/line/binding")
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


@router.post("/api/me/lang")
async def update_my_lang(req: UpdateLangRequest, request: Request):
    """同步用户偏好语言到 DB · 前端每次切语言时调用"""
    user = get_current_user_from_request(request)
    ok = db.update_user_preferred_lang(user["id"], req.lang)
    if not ok:
        raise HTTPException(status_code=400, detail="不支持的语言或更新失败")
    return {"success": True, "lang": req.lang}
