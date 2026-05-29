# -*- coding: utf-8 -*-
"""Pearnly · ERP 推送 / 日志 / 重试 / 批量路由(REFACTOR-WA-B1 · 2026-05-29 R18 从 erp_routes 拆出 · 0 逻辑改)

手动推送 + 推送去重 + 推送日志列表/明细/异常队列/今日统计 + 单条/批量重试 + 批量删。
⚠️ 铁律 #10:push / retry 是 async 路由调 sync Playwright(via erp_push)· 路由体保留
asyncio.to_thread。erp_routes 顶部 include_router 聚合 · app.py 单一 include 不变。
_check_push_access 走 erp_routes_access · _tid 走 route_helpers。
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

import db
import erp_push as _erp
from auth import get_current_user_from_request
from route_helpers import _tid
from erp_routes_access import _check_push_access

logger = logging.getLogger("mr-pilot")

router = APIRouter()


class ErpPushRequest(BaseModel):
    history_id: str
    endpoint_id: Optional[str] = Field(None, description="不传则用默认端点")


@router.post("/api/erp/push")
async def erp_push(req: ErpPushRequest, request: Request):
    """手动触发推送一条历史记录到指定 endpoint"""
    user = get_current_user_from_request(request)
    _check_push_access(user)

    # 1) 拿历史记录
    history = db.get_ocr_history_detail(user["id"], req.history_id, tenant_id=_tid(user))
    if not history:
        raise HTTPException(404, detail="erp.history_not_found")

    # 2) 选 endpoint
    if req.endpoint_id:
        endpoint = db.get_erp_endpoint(user["id"], req.endpoint_id)
        if not endpoint:
            raise HTTPException(404, detail="erp.endpoint_not_found")
    else:
        endpoint = db.get_default_erp_endpoint(user["id"])
        if not endpoint:
            raise HTTPException(400, detail="erp.no_default_endpoint")

    if not endpoint.get("enabled", True):
        raise HTTPException(400, detail="erp.endpoint_disabled")

    # 批 2 改动 2 (Zihao 2026-05-19 拍板 · v118.34.34) · 推送去重 check.
    # 同 history × endpoint 已经 success 过 → 写 skipped_dup log + 静默
    # 返回原成功的 bill_no. 防同张发票被自动 + 手动 + 重试反复推到 MR.ERP.
    existing = db.has_recent_successful_push(
        req.history_id,
        endpoint["id"],
        user["id"],
    )
    if existing:
        log_id = db.insert_push_log(
            user_id=user["id"],
            endpoint_id=endpoint["id"],
            history_id=req.history_id,
            invoice_no=history.get("invoice_no"),
            seller_name=history.get("seller_name"),
            total_amount=history.get("total_amount"),
            status="skipped_dup",
            http_status=200,
            request_body={
                "adapter": endpoint.get("adapter"),
                "skipped_reason": "already_success",
                "prior_log_id": str(existing.get("id")),
            },
            response_body=existing.get("response_body"),
            error_msg=None,
            attempt=1,
            elapsed_ms=0,
            trigger="manual",
        )
        logger.info(
            "[push-dedup] skipped manual push · history=%s endpoint=%s " "(prior log=%s)",
            req.history_id[:8],
            endpoint["id"][:8],
            str(existing.get("id"))[:8],
        )
        if not log_id:
            # ERP-2:防重日志没写进去(如 status CHECK 约束)· 不静默假装成功 · 显性告知
            logger.warning(
                "[push-dedup] skipped_dup log NOT persisted (insert returned None) · history=%s",
                str(req.history_id)[:8],
            )
        return {
            "ok": True,
            "log_id": log_id,
            "log_write_failed": not log_id,
            "http_status": 200,
            "skipped_dup": True,
            "prior_log_id": str(existing.get("id")),
            "endpoint_name": endpoint.get("name"),
        }

    # 3) 推送 · v118.34.10 · asyncio.to_thread keeps push_to_endpoint
    # (which may call Playwright via push_mrerp once C-1 wires it,
    # plus uses sync `requests` for webhook adapters) off the event loop.
    import asyncio as _asyncio

    result = await _asyncio.to_thread(_erp.push_to_endpoint, endpoint, history)

    # 4) 写日志 · P2-D(B8)· 「发票号已存在」= skipped_dup 中性态(不算失败)。
    final_status = db.classify_push_status(result["success"], result.get("error_msg"))
    log_id = db.insert_push_log(
        user_id=user["id"],
        endpoint_id=endpoint["id"],
        history_id=req.history_id,
        invoice_no=history.get("invoice_no"),
        seller_name=history.get("seller_name"),
        total_amount=history.get("total_amount"),
        status=final_status,
        http_status=result.get("http_status"),
        request_body=result.get("request_body"),
        response_body=result.get("response_body"),
        error_msg=result.get("error_msg"),
        attempt=1,
        elapsed_ms=result.get("elapsed_ms", 0),
    )

    # 5) 更新 endpoint 统计 + history 推送状态(skipped_dup 视为非失败)
    db.update_endpoint_stats(endpoint["id"], final_status != "failed")
    db.update_history_push_status(req.history_id, final_status)

    # v118.25 · 手动推送失败 · 也进重试队列(给用户"扔出去就不管"的体验)
    # 批 1 改动 3 (v118.34.33) · 用户数据错(ERR_NO_CLIENT 等)不入重试 ·
    # retry 没意义 + 污染队列. skipped_dup 也不入(已推送过)。
    if final_status == "failed" and log_id:
        if db.is_user_data_error(result.get("error_msg")):
            logger.info(
                "[push] user-data error · NOT scheduling retry · log=%s err=%r",
                str(log_id)[:8],
                (result.get("error_msg") or "")[:80],
            )
        else:
            first_delay = db.get_erp_retry_delay_sec(0)
            if first_delay is not None:
                db.schedule_log_retry(str(log_id), first_delay)

    return {
        "ok": result["success"] or final_status == "skipped_dup",
        "log_id": log_id,
        "status": final_status,
        "skipped_dup": final_status == "skipped_dup",
        "http_status": result.get("http_status"),
        "error_msg": result.get("error_msg"),
        "elapsed_ms": result.get("elapsed_ms"),
        "endpoint_name": endpoint.get("name"),
    }


@router.get("/api/erp/logs/{log_id}/debug-xlsx")
async def erp_log_debug_xlsx(log_id: str, request: Request):
    """v27.8.1.5 · 推送失败时下载 Pearnly 这次生成的 xlsx · 用户拖给 ERP 服务方诊断
    只有同 tenant 用户能下 · 没存 _debug_xlsx_b64 → 404"""
    user = get_current_user_from_request(request)
    tid = _tid(user)
    try:
        with db.get_cursor() as cur:
            cur.execute(
                """
                SELECT pl.id, pl.user_id, pl.history_id, pl.request_body, pl.invoice_no,
                       u.tenant_id::text AS tid
                FROM push_logs pl
                LEFT JOIN users u ON u.id = pl.user_id
                WHERE pl.id = %s LIMIT 1
            """,
                (log_id,),
            )
            row = cur.fetchone()
    except Exception as e:
        raise HTTPException(500, detail=f"db.error:{e}")
    if not row:
        raise HTTPException(404, detail="log.not_found")
    # 同 tenant 才能下
    if str(row.get("tid") or "") != str(tid or ""):
        raise HTTPException(403, detail="log.cross_tenant")
    rb = row.get("request_body") or {}
    if isinstance(rb, str):
        try:
            import json as _json

            rb = _json.loads(rb)
        except Exception:
            rb = {}
    b64 = rb.get("_debug_xlsx_b64") if isinstance(rb, dict) else None
    if not b64:
        raise HTTPException(404, detail="log.no_debug_xlsx")
    import base64 as _b64

    try:
        xlsx_bytes = _b64.b64decode(b64)
    except Exception:
        raise HTTPException(500, detail="log.decode_failed")
    from fastapi.responses import Response as _Resp

    safe_inv = (row.get("invoice_no") or "unknown").replace("/", "_").replace(" ", "_")[:40]
    fname = f"pearnly_debug_{safe_inv}_{log_id[:8]}.xlsx"
    return _Resp(
        content=xlsx_bytes,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{fname}"'},
    )


@router.get("/api/erp/history/{history_id}/push_status")
async def erp_history_push_status(history_id: str, request: Request):
    """P0-2 · 查询某张发票是否已成功推送到 ERP"""
    user = get_current_user_from_request(request)
    _check_push_access(user)
    result = db.list_push_logs(user["id"], history_id=history_id, status_filter="success", limit=1)
    items = result.get("items", [])
    if items:
        item = items[0]
        return {
            "pushed": True,
            "pushed_at": str(item["created_at"]),
            "push_log_id": str(item["id"]),
        }
    return {"pushed": False, "pushed_at": None, "push_log_id": None}


@router.get("/api/erp/logs")
async def erp_logs(
    request: Request,
    history_id: Optional[str] = None,
    endpoint_id: Optional[str] = None,
    status: Optional[str] = None,
    trigger: Optional[str] = None,
    adapter: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
):
    """批 3 改动 6 (v118.34.34) · 新增 adapter 参数 · 让前端按 ERP 类型筛日志."""
    user = get_current_user_from_request(request)
    _check_push_access(user)
    return db.list_push_logs(
        user["id"],
        history_id=history_id,
        endpoint_id=endpoint_id,
        status_filter=status,
        trigger_filter=trigger,
        adapter_filter=adapter,
        limit=min(limit, 200),
        offset=max(0, offset),
    )


@router.get("/api/erp/exceptions")
async def erp_exceptions(
    request: Request,
    q: Optional[str] = None,
    category: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
):
    """ERP 推送异常队列(Zihao 2026-05-26)· 派生自 erp_push_logs(铁律 #12 单一源)。

    每个 (history×endpoint) 最近一条仍 failed 的推送 → 一条可处理异常行:
    带 state(needs_action/retrying/failed)+ category(customer_mismatch/product_mismatch/
    no_client/verify_unavailable/other)+ 发票号/卖方/买方/已归属客户/端点名/错误码。
    支持搜索(q)+ category 过滤 + 分页。返回 {items, total, categories}。通用层 · 不写死 MR.ERP。
    """
    user = get_current_user_from_request(request)
    _check_push_access(user)
    return db.list_push_exceptions(
        user["id"], q=q, category=category, limit=min(limit, 200), offset=max(0, offset)
    )


@router.get("/api/erp/logs/{log_id}")
async def erp_log_detail(log_id: str, request: Request):
    """单条日志完整详情 · 含请求体/响应体"""
    user = get_current_user_from_request(request)
    _check_push_access(user)
    detail = db.get_push_log_detail(user["id"], log_id)
    if not detail:
        raise HTTPException(404, detail="log.not_found")
    return detail


@router.get("/api/erp/stats/today")
async def erp_stats_today(request: Request):
    """今日推送统计"""
    user = get_current_user_from_request(request)
    _check_push_access(user)
    return db.get_push_stats_today(user["id"])


@router.post("/api/erp/logs/{log_id}/retry")
async def erp_retry_push(log_id: str, request: Request):
    """一键重试失败的推送"""
    user = get_current_user_from_request(request)
    _check_push_access(user)
    log = db.get_push_log_detail(user["id"], log_id)
    if not log:
        raise HTTPException(404, detail="log.not_found")
    if log["status"] == "success":
        raise HTTPException(400, detail="log.already_success")
    if not log.get("history_id") or not log.get("endpoint_id"):
        raise HTTPException(400, detail="log.missing_refs")

    history = db.get_ocr_history_detail(user["id"], log["history_id"], tenant_id=_tid(user))
    endpoint = db.get_erp_endpoint(user["id"], log["endpoint_id"])
    if not history:
        raise HTTPException(404, detail="history.not_found")
    if not endpoint:
        raise HTTPException(404, detail="erp.endpoint_not_found")

    # v118.34.10 · asyncio.to_thread keeps push_to_endpoint off the loop.
    import asyncio as _asyncio

    result = await _asyncio.to_thread(_erp.push_to_endpoint, endpoint, history)

    # P2-A(Zihao 2026-05-27 拍板 · A3)· 重试**更新原行**(不再 INSERT 新行)·
    # 消除「旧失败行 + 新成功行」重复日志。retry_count 自增、状态原地落定。
    # P2-D(B8)· 「发票号已存在」= skipped_dup 中性态(不算失败)。
    final_status = db.classify_push_status(result["success"], result.get("error_msg"))
    db.increment_retry_count(log["id"])
    db.update_log_status_after_retry(
        log_id=log["id"],
        success=result["success"],
        http_status=result.get("http_status"),
        response_body=result.get("response_body"),
        error_msg=result.get("error_msg"),
        elapsed_ms=result.get("elapsed_ms", 0),
        request_body=result.get("request_body"),
        final_status=final_status,
    )
    # skipped_dup 视为非失败(已推送过)· 不计入端点失败数。
    db.update_endpoint_stats(endpoint["id"], final_status != "failed")
    db.update_history_push_status(log["history_id"], final_status)

    # 用户已亲自重试 · 把原 log 的自动重试队列摘掉(成功/失败/已存在都不再交给 worker)。
    if log.get("next_retry_at"):
        db.clear_retry_schedule(log["id"])

    return {
        "ok": result["success"] or final_status == "skipped_dup",
        "log_id": log["id"],
        "status": final_status,
        "http_status": result.get("http_status"),
        "error_msg": result.get("error_msg"),
        "elapsed_ms": result.get("elapsed_ms"),
    }


# v118.25.1 · 批量重推:从推送日志列表多选 → 一次性触发多条重推
class ErpBatchRetryRequest(BaseModel):
    log_ids: List[str] = Field(..., description="要重推的 log id 列表 · 上限 50")


@router.post("/api/erp/logs/batch-retry")
async def erp_batch_retry(req: ErpBatchRetryRequest, request: Request):
    """批量重推:对每个 log_id 跑一次手动重试逻辑 · 返回成功/失败计数"""
    user = get_current_user_from_request(request)
    _check_push_access(user)

    if not req.log_ids:
        raise HTTPException(400, detail="erp.batch_empty")
    if len(req.log_ids) > 50:
        raise HTTPException(400, detail={"code": "erp.batch_too_many", "max": 50})

    succeeded = 0
    failed = 0
    skipped = 0  # 已成功 / 关联实体丢失等
    details: List[Dict[str, Any]] = []

    for log_id in req.log_ids:
        try:
            log = db.get_push_log_detail(user["id"], log_id)
            if not log:
                skipped += 1
                details.append({"log_id": log_id, "result": "skipped", "reason": "not_found"})
                continue
            if log["status"] == "success":
                skipped += 1
                details.append({"log_id": log_id, "result": "skipped", "reason": "already_success"})
                continue
            if not log.get("history_id") or not log.get("endpoint_id"):
                skipped += 1
                details.append({"log_id": log_id, "result": "skipped", "reason": "missing_refs"})
                continue

            history = db.get_ocr_history_detail(user["id"], log["history_id"], tenant_id=_tid(user))
            endpoint = db.get_erp_endpoint(user["id"], log["endpoint_id"])
            if not history or not endpoint:
                skipped += 1
                details.append({"log_id": log_id, "result": "skipped", "reason": "ref_deleted"})
                continue

            # v118.34.10 · asyncio.to_thread keeps push_to_endpoint off the loop.
            import asyncio as _asyncio

            result = await _asyncio.to_thread(_erp.push_to_endpoint, endpoint, history)
            # P2-A/P2-D · 更新原行(不 INSERT 新行)+ skipped_dup 中性态。
            final_status = db.classify_push_status(result["success"], result.get("error_msg"))
            db.increment_retry_count(log["id"])
            db.update_log_status_after_retry(
                log_id=log["id"],
                success=result["success"],
                http_status=result.get("http_status"),
                response_body=result.get("response_body"),
                error_msg=result.get("error_msg"),
                elapsed_ms=result.get("elapsed_ms", 0),
                request_body=result.get("request_body"),
                final_status=final_status,
            )
            db.update_endpoint_stats(endpoint["id"], final_status != "failed")
            db.update_history_push_status(log["history_id"], final_status)
            # 跟单个手动重推一样:用户已经亲自管了 · 把原 log 的自动重试队列摘掉
            if log.get("next_retry_at"):
                db.clear_retry_schedule(log["id"])

            if final_status == "success":
                succeeded += 1
                details.append({"log_id": log_id, "result": "success"})
            elif final_status == "skipped_dup":
                # 已推送过 · 算中性跳过(不计失败 · 不红叉)
                skipped += 1
                details.append({"log_id": log_id, "result": "skipped", "reason": "already_pushed"})
            else:
                failed += 1
                details.append(
                    {"log_id": log_id, "result": "failed", "error": result.get("error_msg")}
                )
        except Exception as e:
            failed += 1
            details.append({"log_id": log_id, "result": "failed", "error": str(e)})

    return {
        "total": len(req.log_ids),
        "succeeded": succeeded,
        "failed": failed,
        "skipped": skipped,
        "details": details,
    }


class ErpBatchDeleteRequest(BaseModel):
    log_ids: List[str] = Field(..., description="要删除的 log id 列表 · 上限 200")


@router.post("/api/erp/logs/batch-delete")
async def erp_batch_delete(req: ErpBatchDeleteRequest, request: Request):
    """Bug 6 (Zihao 2026-05-19 拍板 · v118.34.23) · 批量删除推送日志.
    确认操作不可撤销 · 弹窗确认在 JS 侧 · 这里只管严格 user_id-scoped delete.
    返回 {total, deleted, skipped} · skipped = 不在该用户 scope 内的."""
    user = get_current_user_from_request(request)
    _check_push_access(user)

    if not req.log_ids:
        raise HTTPException(400, detail="erp.batch_empty")
    if len(req.log_ids) > 200:
        raise HTTPException(400, detail={"code": "erp.batch_too_many", "max": 200})

    requested = len(req.log_ids)
    deleted = db.delete_push_logs(user["id"], req.log_ids)
    return {
        "total": requested,
        "deleted": deleted,
        "skipped": max(0, requested - deleted),
    }
