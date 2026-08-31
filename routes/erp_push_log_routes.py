# -*- coding: utf-8 -*-
"""ERP 手动推送、日志、重试与批量操作路由。"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from core import db
from services.erp import erp_push as _erp
from services.intake_bridge import convert as convert_svc
from core.auth import get_current_user_from_request
from core.route_helpers import _tid
from routes.erp_routes_access import _check_push_access
from services.auth.entrance import DMS, require_erp_portal
from services.erp import team_access
from core import workspace_context as wc

logger = logging.getLogger("mr-pilot")

router = APIRouter()


class ErpPushRequest(BaseModel):
    history_id: str
    endpoint_id: Optional[str] = Field(None, description="不传则用默认端点")
    posting_kind: Optional[str] = Field(None, description="stock | service · Express 库存过账开关")


@router.post("/api/erp/push")
async def erp_push(req: ErpPushRequest, request: Request):
    """手动触发推送一条历史记录到指定 endpoint"""
    user = get_current_user_from_request(request)
    require_erp_portal(user)
    _check_push_access(user)
    creator_scope = team_access.record_creator_scope(request, user)
    assigned_endpoint = team_access.assigned_endpoint_for_request(user, req.endpoint_id)
    effective_endpoint_id = (
        str(assigned_endpoint["id"]) if assigned_endpoint is not None else req.endpoint_id
    )
    member_history = None
    if creator_scope:
        member_history = db.get_ocr_history_detail(user["id"], req.history_id)
        if not member_history:
            raise HTTPException(404, detail="erp.history_not_found")

    from services.erp.shared_express_push import maybe_reserve_manual_push

    managed = await maybe_reserve_manual_push(
        user=user,
        request=request,
        history_id=req.history_id,
        endpoint_id=effective_endpoint_id,
        posting_kind=req.posting_kind,
    )
    if managed is not None:
        return managed

    # 1) 拿历史记录
    history = member_history or db.get_ocr_history_detail(
        user["id"], req.history_id, tenant_id=_tid(user)
    )
    if not history:
        raise HTTPException(404, detail="erp.history_not_found")
    # ERP 产品只允许推送用户已经确认并生成正式采购/销售单的历史。Cowork 的既有推送
    # 工作流保持原样；这里按会话入口收窄，避免直接调用 API 绕过 ERP 复核确认。
    if user.get("entry") == "erp" and not convert_svc.history_is_converted(
        tenant_id=_tid(user), history_id=req.history_id
    ):
        raise HTTPException(409, detail="erp.history_not_converted")

    # 2) 选 endpoint
    if effective_endpoint_id:
        endpoint = assigned_endpoint or db.get_erp_endpoint(user["id"], effective_endpoint_id)
        if not endpoint:
            raise HTTPException(404, detail="erp.endpoint_not_found")
    else:
        endpoint = assigned_endpoint or db.get_default_erp_endpoint(user["id"])
        if not endpoint:
            raise HTTPException(400, detail="erp.no_default_endpoint")

    if not endpoint.get("enabled", True):
        raise HTTPException(400, detail="erp.endpoint_disabled")

    # 同 history × endpoint 已 success 过就返回旧结果，防自动/手动/重试重复入账。
    existing = db.has_recent_successful_push(
        req.history_id,
        endpoint["id"],
        user["id"],
    )
    if existing:
        log_args = {
            "endpoint_id": str(endpoint["id"]),
            "history_id": req.history_id,
            "invoice_no": history.get("invoice_no"),
            "seller_name": history.get("seller_name"),
            "total_amount": history.get("total_amount"),
            "status": "skipped_dup",
            "http_status": 200,
            "request_body": {
                "adapter": endpoint.get("adapter"),
                "skipped_reason": "already_success",
                "prior_log_id": str(existing.get("id")),
            },
            "response_body": existing.get("response_body"),
            "error_msg": None,
            "attempt": 1,
            "elapsed_ms": 0,
            "trigger": "manual",
        }
        log_id = (
            team_access.insert_assigned_push_log(user=user, **log_args)
            if assigned_endpoint
            else db.insert_push_log(user_id=user["id"], **log_args)
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

    # 3) 推送 · 同步 adapter 必须离开事件循环。
    import asyncio as _asyncio

    result = await _asyncio.to_thread(
        _erp.push_to_endpoint, endpoint, history, posting_kind=req.posting_kind
    )

    # 4) 写日志 · P2-D(B8)· 「发票号已存在」= skipped_dup 中性态(不算失败)。
    final_status = db.classify_push_status(result["success"], result.get("error_msg"))
    log_args = {
        "endpoint_id": str(endpoint["id"]),
        "history_id": req.history_id,
        "invoice_no": history.get("invoice_no"),
        "seller_name": history.get("seller_name"),
        "total_amount": history.get("total_amount"),
        "status": final_status,
        "http_status": result.get("http_status"),
        "request_body": result.get("request_body"),
        "response_body": result.get("response_body"),
        "error_msg": result.get("error_msg"),
        "attempt": 1,
        "elapsed_ms": result.get("elapsed_ms", 0),
    }
    log_id = (
        team_access.insert_assigned_push_log(user=user, **log_args)
        if assigned_endpoint
        else db.insert_push_log(user_id=user["id"], **log_args)
    )

    # 5) 更新 endpoint 统计 + history 推送状态(口径见 _counts_as_endpoint_success)。
    db.update_endpoint_stats(endpoint["id"], db.counts_as_endpoint_success(final_status))
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


@router.get("/api/erp/history/{history_id}/push_status")
async def erp_history_push_status(history_id: str, request: Request):
    """P0-2 · 查询某张发票是否已成功推送到 ERP"""
    user = get_current_user_from_request(request)
    require_erp_portal(user)
    _check_push_access(user)
    result = db.list_push_logs(
        user["id"],
        history_id=history_id,
        status_filter="success",
        limit=1,
        tenant_id=team_access.tenant_record_scope(request, user),
    )
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
    keyword: Optional[str] = None,
    push_type: Optional[str] = None,
    exclude_push_type: Optional[str] = None,
):
    """批 3 改动 6 (v118.34.34) · 新增 adapter 参数 · 让前端按 ERP 类型筛日志.
    + 草稿对齐:keyword 搜索(单据号/卖方)· push_type 业务类型(全部业务下拉)。
    + exclude_push_type:主站推送日志排身份证订车行(DMS 已搬独立入口 /dms)· 后端剔除
      让 total 诚实(前端不再 .filter 造成「共 N 条」虚高)。/dms 记录页走 adapter=mrerp_dms
      仍能看到 id_card 行,故不能全局硬剔——只在调用方显式传参时排除。"""
    user = get_current_user_from_request(request)
    require_erp_portal(
        user, also_allowed=(DMS,)
    )  # /dms 记录页(entry='dms')读本租户推送日志 → 窄 allowlist
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
        keyword=keyword.strip() if keyword else None,
        push_type=push_type if push_type in ("id_card", "invoice") else None,
        exclude_push_type=(
            exclude_push_type if exclude_push_type in ("id_card", "invoice") else None
        ),
        tenant_id=team_access.tenant_record_scope(request, user),
        workspace_client_id=wc.active_workspace_for_request(request, _tid(user)),
    )


@router.get("/api/erp/logs/{log_id}")
async def erp_log_detail(log_id: str, request: Request):
    """单条日志完整详情 · 含请求体/响应体"""
    user = get_current_user_from_request(request)
    require_erp_portal(user)
    _check_push_access(user)
    detail = db.get_push_log_detail(
        user["id"], log_id, tenant_id=team_access.tenant_record_scope(request, user)
    )
    if not detail:
        raise HTTPException(404, detail="log.not_found")
    return detail


@router.get("/api/erp/stats/today")
async def erp_stats_today(request: Request):
    """今日推送统计 · 同日志列表按当前套账隔离(active_workspace_for_request 解析)。"""
    user = get_current_user_from_request(request)
    require_erp_portal(user)
    _check_push_access(user)
    return db.get_push_stats_today(
        user["id"],
        tenant_id=team_access.tenant_record_scope(request, user),
        workspace_client_id=wc.active_workspace_for_request(request, _tid(user)),
    )


@router.post("/api/erp/logs/{log_id}/retry")
async def erp_retry_push(log_id: str, request: Request):
    """一键重试失败的推送"""
    user = get_current_user_from_request(request)
    require_erp_portal(user)
    _check_push_access(user)
    tenant_scope = team_access.tenant_record_scope(request, user)
    log = db.get_push_log_detail(user["id"], log_id, tenant_id=tenant_scope)
    if not log:
        raise HTTPException(404, detail="log.not_found")
    if log["status"] == "success":
        raise HTTPException(400, detail="log.already_success")
    if not log.get("history_id") or not log.get("endpoint_id"):
        raise HTTPException(400, detail="log.missing_refs")

    history = db.get_ocr_history_detail(user["id"], log["history_id"], tenant_id=tenant_scope)
    endpoint = team_access.assigned_endpoint_for_request(user, log["endpoint_id"])
    endpoint = endpoint or db.get_erp_endpoint(user["id"], log["endpoint_id"])
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
    db.update_endpoint_stats(endpoint["id"], db.counts_as_endpoint_success(final_status))
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
    require_erp_portal(user)
    _check_push_access(user)

    if not req.log_ids:
        raise HTTPException(400, detail="erp.batch_empty")
    if len(req.log_ids) > 50:
        raise HTTPException(400, detail={"code": "erp.batch_too_many", "max": 50})

    succeeded = 0
    failed = 0
    skipped = 0  # 已成功 / 关联实体丢失等
    details: List[Dict[str, Any]] = []
    tid = _tid(user)
    tenant_scope = team_access.tenant_record_scope(request, user)

    for log_id in req.log_ids:
        try:
            log = db.get_push_log_detail(user["id"], log_id, tenant_id=tenant_scope)
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

            history = db.get_ocr_history_detail(
                user["id"], log["history_id"], tenant_id=tenant_scope
            )
            endpoint = team_access.assigned_endpoint_for_request(user, log["endpoint_id"])
            endpoint = endpoint or db.get_erp_endpoint(user["id"], log["endpoint_id"])
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
            db.update_endpoint_stats(endpoint["id"], db.counts_as_endpoint_success(final_status))
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
    require_erp_portal(user)
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
