# -*- coding: utf-8 -*-
"""
Pearnly · 客户管理路由模块(REFACTOR-B1 · 2026-05-24 抽出)

从 app.py 整片搬过来 · 纯搬家 · 不改业务逻辑 / URL / response shape。

覆盖 5 个 API:
  GET    /api/clients                      · 列客户(员工分配过滤)
  POST   /api/clients                      · 建客户(创建者自动获得分配)
  PATCH  /api/clients/{client_id}          · 改客户
  DELETE /api/clients/{client_id}          · 删客户(级联解绑发票)
  GET    /api/clients/{client_id}/export   · 按客户导出发票 CSV(VAT 报表格式)

依赖:
  - db.*(client CRUD + ocr_history 查询)
  - auth.get_current_user_from_request
  - _tid:app.py 也有同名 helper · 这里复制一份防循环 import
    (待 B 阶段抽公共 helper 模块时再合并去重)

注意:POST /api/history/{history_id}/assign_client 用 AssignClientRequest ·
      它属 /api/history 组 · 留 app.py · 待 history_routes 抽出时一并搬。
"""

from __future__ import annotations

import csv
import io
import logging
import traceback
import urllib.parse as _up
from typing import Optional

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import Response
from pydantic import BaseModel, Field

import db
from auth import get_current_user_from_request

logger = logging.getLogger("mr-pilot")
router = APIRouter()


def _tid(user: dict) -> Optional[str]:
    """多租户共享:返回用户 tenant_id 字符串(app.py 同名 helper · 复制防循环 import)"""
    if not user:
        return None
    tid = user.get("tenant_id")
    return str(tid) if tid else None


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


@router.get("/api/clients")
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


@router.post("/api/clients")
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


@router.patch("/api/clients/{client_id}")
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


@router.delete("/api/clients/{client_id}")
async def api_delete_client(client_id: int, request: Request):
    """删除客户(级联解绑发票 · 不删发票)"""
    user = get_current_user_from_request(request)
    ok = db.delete_client(str(user["id"]), client_id, cascade_unlink=True, tenant_id=_tid(user))
    if not ok:
        raise HTTPException(404, detail="client.not_found")
    return {"ok": True}


class ClientBatchDeleteRequest(BaseModel):
    ids: list[int] = Field(..., min_length=1, max_length=500)


@router.post("/api/clients/batch-delete")
async def api_batch_delete_clients(req: ClientBatchDeleteRequest, request: Request):
    """批量删除买方客户(级联解绑发票 · 不删发票)。客户管理页批量操作用。"""
    user = get_current_user_from_request(request)
    deleted = 0
    failed: list[int] = []
    for cid in req.ids:
        try:
            ok = db.delete_client(
                str(user["id"]), int(cid), cascade_unlink=True, tenant_id=_tid(user)
            )
            if ok:
                deleted += 1
            else:
                failed.append(int(cid))
        except Exception as e:
            logger.warning(f"[client_batch_delete] id={cid} failed: {e}")
            failed.append(int(cid))
    return {"ok": True, "deleted": deleted, "failed": failed}


@router.get("/api/clients/{client_id}/export")
async def api_export_client_invoices(client_id: int, request: Request, month: Optional[str] = None):
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
                cur.execute(
                    f"""
                    SELECT h.id, h.invoice_no, h.invoice_date, h.seller_name,
                           h.total_amount, h.filename, h.created_at
                    FROM ocr_history h
                    WHERE h.client_id = %s AND {user_filter_sql}
                      AND (
                          (h.invoice_date IS NOT NULL AND TO_CHAR(h.invoice_date, 'YYYY-MM') = %s)
                          OR (h.invoice_date IS NULL AND TO_CHAR(h.created_at, 'YYYY-MM') = %s)
                      )
                    ORDER BY h.invoice_date ASC NULLS LAST, h.created_at ASC
                """,
                    (client_id, user_filter_param, month, month),
                )
            else:
                # 不过滤月份 · 全部
                cur.execute(
                    f"""
                    SELECT h.id, h.invoice_no, h.invoice_date, h.seller_name,
                           h.total_amount, h.filename, h.created_at
                    FROM ocr_history h
                    WHERE h.client_id = %s AND {user_filter_sql}
                    ORDER BY h.invoice_date ASC NULLS LAST, h.created_at ASC
                """,
                    (client_id, user_filter_param),
                )
            rows = cur.fetchall()

        logger.info(f"[client_export] client_id={client_id} month={month} rows={len(rows)}")

        # 拼 CSV(Excel 兼容)
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
            w.writerow(
                [
                    i,
                    inv_date,
                    r.get("invoice_no") or "",
                    r.get("seller_name") or "",
                    f"{amount:.2f}",
                    r.get("filename") or "",
                ]
            )
        w.writerow([])
        w.writerow(["合计", "", "", "", f"{total:.2f}"])

        client_name_safe = (client.get("name") or "client").replace("/", "_")[:50]
        # ASCII 安全的 filename(中泰文用 RFC 5987 filename* 编码)
        ascii_name = "client_export"
        encoded = _up.quote(f"{client_name_safe}_{title_month}.csv")
        return Response(
            content="﻿" + buf.getvalue(),
            media_type="text/csv; charset=utf-8",
            headers={
                "Content-Disposition": f"attachment; filename=\"{ascii_name}.csv\"; filename*=UTF-8''{encoded}"
            },
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"export_client_invoices failed: {e}\n{traceback.format_exc()}")
        raise HTTPException(500, detail=f"client.export_failed: {str(e)[:200]}")
