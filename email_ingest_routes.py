# -*- coding: utf-8 -*-
"""
Pearnly · 邮箱抓取(IMAP)路由模块(REFACTOR-B1 · 2026-05-25 抽出)

v0.17 · M6 · 邮箱抓取。从 app.py 整片搬过来 · 纯搬家 ·
不改业务逻辑 / URL / response shape。

覆盖 6 个 API:
  GET    /api/email-ingest/account  · 获取邮箱绑定(不返回密码)
  PUT    /api/email-ingest/account  · 创建/更新邮箱绑定
  DELETE /api/email-ingest/account  · 解绑(级联删日志/UID)
  POST   /api/email-ingest/test     · 测试连接(只登录 · 不保存)
  POST   /api/email-ingest/trigger  · 手动触发一次抓取(同步等 · 最长 60s)
  GET    /api/email-ingest/logs     · 最近抓取日志

依赖:
  - db.*(email account / 日志 CRUD)
  - auth.get_current_user_from_request
  - email_ingest(加密 / IMAP · 函数内懒 import · 防可选依赖在启动期炸)
"""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

import db
from auth import get_current_user_from_request

router = APIRouter()


class EmailAccountBindRequest(BaseModel):
    email_address: str = Field(..., min_length=3, max_length=200)
    imap_host: str = Field(..., min_length=3, max_length=200)
    imap_port: int = Field(993, ge=1, le=65535)
    imap_use_ssl: bool = True
    password: Optional[str] = None  # 不传 = 只改配置 · 不改密码
    folder: str = Field("INBOX", max_length=100)
    filter_subject: Optional[str] = Field(None, max_length=200)
    filter_sender: Optional[str] = Field(None, max_length=500)
    mark_as_read: bool = True
    enabled: bool = True
    interval_min: int = Field(15)  # v0.17.9 · 仅 5/15/60 三档 · db 层兜底


class EmailTestConnRequest(BaseModel):
    email_address: str = Field(..., min_length=3, max_length=200)
    imap_host: str = Field(..., min_length=3, max_length=200)
    imap_port: int = Field(993, ge=1, le=65535)
    imap_use_ssl: bool = True
    password: str = Field(..., min_length=1, max_length=500)
    folder: str = Field("INBOX", max_length=100)


@router.get("/api/email-ingest/account")
async def email_account_get(request: Request):
    """获取当前用户的邮箱绑定(不返回密码)"""
    user = get_current_user_from_request(request)
    info = db.get_email_account_safe(user["id"])
    return {"account": info, "presets": _email_presets()}


@router.put("/api/email-ingest/account")
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


@router.delete("/api/email-ingest/account")
async def email_account_unbind(request: Request):
    """解绑邮箱(同时删所有相关日志和 UID 记录 · 级联删除)"""
    user = get_current_user_from_request(request)
    ok = db.delete_email_account(user["id"])
    return {"ok": ok}


@router.post("/api/email-ingest/test")
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


@router.post("/api/email-ingest/trigger")
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


@router.get("/api/email-ingest/logs")
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
