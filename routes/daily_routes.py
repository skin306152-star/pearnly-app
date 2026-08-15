# -*- coding: utf-8 -*-
"""Daily 周记账 API(邀请制 · 每用户独立租户隔离)。

面向受邀用户的个人收入/支出记录应用(pearnly.com/daily · 泰文界面 · 按周/月统计)。
数据表 daily_entries 按 tenant_id 隔离(RLS 第二道防线 · 见 services/daily/schema),
每受邀用户一个独立租户(create_owner_user 建号即建租户)。

守卫:无权限码,与 /api/dms 同款本地判 —— require_entrance_api(daily_finance 邀请闸
+ entrance_api_scope 入口作用域),闸关一律 404 不泄漏功能存在。

端点:
  GET    /api/daily/session            门禁探针(壳 boot 用 · 无业务副作用)
  GET    /api/daily/entries?month=…   月内全部记录(前端本地汇总周/月指标)
  POST   /api/daily/entries            新建一条收入/支出
  DELETE /api/daily/entries/{id}       删除(仅限本租户行)
"""

from __future__ import annotations

import logging
import re
from datetime import date
from decimal import Decimal
from typing import Literal

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from core import db
from core.auth import get_current_user_from_request
from core.feature_flags import daily_enabled_for, entrance_api_scope_enabled_for
from services.auth.entrance import DAILY, require_entrance_api
from services.daily import store

logger = logging.getLogger(__name__)

router = APIRouter()

_MONTH_RE = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")
_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


class EntryCreate(BaseModel):
    date: str
    kind: Literal["income", "expense"]
    title: str = Field(..., min_length=1, max_length=100)
    amount: Decimal = Field(..., gt=0, max_digits=12, decimal_places=2)


def _authorize(request: Request):
    """Daily 入口守卫(四端点统一)· 薄壳委托 entrance.require_entrance_api 通用无码守卫。

    三个消费面按本模块名传入(patch 落本模块全局才生效):daily_finance 邀请闸 +
    entrance_api_scope 入口作用域 + 无 plan 推送闸。
    """
    user = get_current_user_from_request(request)
    return require_entrance_api(
        user,
        gate_fn=daily_enabled_for,
        scope_fn=entrance_api_scope_enabled_for,
        entry=DAILY,
        not_found_detail="daily.not_found",
    )


def _tid(user: dict) -> str:
    """调用方租户 id;无租户(异常账号)显式 403,不让 RLS 静默空表吞掉。"""
    tid = user.get("tenant_id")
    if not tid:
        raise HTTPException(403, detail="daily.no_tenant")
    return str(tid)


def _valid_date(value: str) -> str:
    if not _DATE_RE.match(value):
        raise HTTPException(422, detail="daily.bad_date")
    try:
        date.fromisoformat(value)
    except ValueError:
        raise HTTPException(422, detail="daily.bad_date")
    return value


@router.get("/api/daily/session")
async def daily_session(request: Request):
    """门禁探针:只跑 _authorize,不碰业务数据。200=放行,401/403/404 由守卫天然给出。"""
    _authorize(request)
    return {"ok": True}


@router.get("/api/daily/entries")
async def daily_entries(request: Request, month: str):
    user = _authorize(request)
    if not _MONTH_RE.match(month):
        raise HTTPException(422, detail="daily.bad_month")
    tid = _tid(user)
    with db.get_cursor_rls(tenant_id=tid, commit=False) as cur:
        rows = store.list_entries(cur, tid, month)
    return {"entries": rows}


@router.get("/api/daily/export")
async def daily_export(request: Request):
    """全量导出(JSON 备份 · 前端导出按钮用)。与列表同款租户隔离。"""
    user = _authorize(request)
    tid = _tid(user)
    with db.get_cursor_rls(tenant_id=tid, commit=False) as cur:
        rows = store.list_all_entries(cur, tid)
    return {"entries": rows}


@router.post("/api/daily/entries")
async def daily_entry_create(body: EntryCreate, request: Request):
    user = _authorize(request)
    _valid_date(body.date)
    tid = _tid(user)
    with db.get_cursor_rls(tenant_id=tid, commit=True) as cur:
        row = store.insert_entry(cur, tid, body.date, body.kind, body.title.strip(), body.amount)
    if not row:
        raise HTTPException(422, detail="daily.create_failed")
    return row


@router.delete("/api/daily/entries/{entry_id}")
async def daily_entry_delete(entry_id: str, request: Request):
    user = _authorize(request)
    tid = _tid(user)
    with db.get_cursor_rls(tenant_id=tid, commit=True) as cur:
        deleted = store.delete_entry(cur, tid, entry_id)
    if not deleted:
        raise HTTPException(404, detail="daily.entry_not_found")
    return {"ok": True}
