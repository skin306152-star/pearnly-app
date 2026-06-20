# -*- coding: utf-8 -*-
"""
Pearnly · OCR 历史记录 API 路由模块(REFACTOR-B1 · 2026-05-25 抽出 · 步骤 B)

历史列表 / 详情 / 编辑(重对账 hook)/ 删除 / PDF 下载 / 批量删除 + v1 别名 ·
10 路由。从 app.py 整片搬过来 · 纯搬家 · URL/method/权限/返回结构/错误码 0 改。

前置:OCR 异常检测链已在步骤 A 搬到 exception_checks.py(history PUT 编辑后重跑
规则用 _async_run_exception_checks / _parse_money · 此处 import)。

依赖:
  - db.*(get_cursor)+ list_ocr_history / get_ocr_history_detail / update_ocr_history_pages /
    delete_ocr_history_with_pdf_paths / get_history_pdf_info(从 db import)
  - pdf_storage(PDF 留底删除 / 取绝对路径)
  - auth.get_current_user_from_request
  - route_helpers._tid / _plan_permissions(_check_history_access 用)
  - exception_checks._async_run_exception_checks / _parse_money(history PUT 重跑规则)
"""

from __future__ import annotations

import logging
from typing import Any, List, Optional

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from core import db
from core import workspace_context as wc
from services.ocr import pdf_storage
from core.db import (
    delete_ocr_history_with_pdf_paths,
    get_history_pdf_info,
    get_ocr_history_detail,
    list_ocr_history,
    update_ocr_history_pages,
)
from core.auth import get_current_user_from_request
from core.route_helpers import _plan_permissions, _tid
from services.exceptions.exception_checks import _async_run_exception_checks, _parse_money

logger = logging.getLogger("mr-pilot")

router = APIRouter()


class HistoryUpdateRequest(BaseModel):
    pages: List[Any] = Field(..., description="完整 pages 数组(会计修改后的)")


def _check_history_access(user: dict):
    """v0.8 · 所有 plan 都能看历史,保留天数不同"""
    plan = (user or {}).get("plan", "free")
    p = _plan_permissions(plan)
    if not p.get("can_view_history"):
        raise HTTPException(403, detail="history.upgrade_required")
    return int(p.get("history_retention_days", 7))


@router.get("/api/history")
async def history_list(
    request: Request,
    keyword: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    client_id: Optional[int] = None,
    source: Optional[str] = None,
    status: Optional[str] = None,
):
    user = get_current_user_from_request(request)
    retention = _check_history_access(user)
    # 安全限制
    limit = max(1, min(int(limit), 100))
    offset = max(0, int(offset))
    # 白名单收敛(防注入到派生 SQL 分支)
    src = source if source in ("upload", "line", "email") else None
    sts = status if status in ("confirmed", "pending", "failed") else None
    return list_ocr_history(
        user_id=str(user["id"]),
        retention_days=retention,
        keyword=keyword.strip() if keyword else None,
        limit=limit,
        offset=offset,
        tenant_id=_tid(user),
        client_id=client_id,  # v118.28.0 · 顶栏客户切换器过滤
        source_filter=src,
        status_filter=sts,
        restrict_client_ids=db.get_visible_client_ids_for_user(user),  # v118.28.1 · 员工分配
        workspace_client_id=wc.active_workspace_for_request(
            request, _tid(user)
        ),  # PO-4 · 套账硬边界
    )


@router.get("/api/history/{record_id}")
async def history_detail(record_id: str, request: Request):
    user = get_current_user_from_request(request)
    _check_history_access(user)
    detail = get_ocr_history_detail(
        str(user["id"]),
        record_id,
        tenant_id=_tid(user),
        workspace_client_id=wc.active_workspace_for_request(
            request, _tid(user)
        ),  # PO-4 · 套账硬边界
    )
    if not detail:
        raise HTTPException(404, detail="history.not_found")
    return detail


@router.put("/api/history/{record_id}")
async def history_update(record_id: str, req: HistoryUpdateRequest, request: Request):
    user = get_current_user_from_request(request)
    _check_history_access(user)
    if not req.pages:
        raise HTTPException(400, detail="history.empty_pages")
    ok = update_ocr_history_pages(str(user["id"]), record_id, req.pages, tenant_id=_tid(user))
    if not ok:
        raise HTTPException(404, detail="history.not_found")
    # v118.18 · 推荐分类「学习」· 用户改了 category 就记忆「seller → category」
    try:
        for p in req.pages or []:
            if p.get("is_duplicate") or p.get("is_copy"):
                continue
            f = p.get("fields") or {}
            seller = (f.get("seller_name") or "").strip()
            cat = (f.get("category") or "").strip()
            if seller and cat:
                db.upsert_supplier_category(
                    seller_name=seller,
                    category=cat,
                    user_id=str(user["id"]),
                    tenant_id=_tid(user),
                )
            break  # 只学主页 · 多页发票其他页是副本不学
    except Exception as _ue:
        logger.warning(f"upsert supplier_category 失败(已忽略): {_ue}")
    # v118.21.3 · 字段改完后重跑规则 · 让异常自动消失或更新
    rechecked = False
    try:
        # 取主页字段(跟 OCR 时的 hook 输入一致)
        primary = None
        for p in req.pages or []:
            if p.get("is_duplicate") or p.get("is_copy"):
                continue
            primary = p
            break
        if primary:
            f = primary.get("fields") or {}
            seller_name = (f.get("seller_name") or "").strip() or None
            invoice_no = (f.get("invoice_number") or f.get("invoice_no") or "").strip() or None
            total_amount = _parse_money(f.get("total_amount"))
            # 取 history 的当前 confidence(更新 pages 不会影响 confidence · 复用现值)
            detail_now = get_ocr_history_detail(str(user["id"]), record_id, tenant_id=_tid(user))
            confidence = (detail_now or {}).get("confidence")
            # 1. 删该 history 下所有 pending 异常
            db.delete_pending_exceptions_by_history(
                record_id, tenant_id=_tid(user), user_id=str(user["id"])
            )
            # 2. 同步重跑规则(duplicate 不重检 · 因为依赖 OCR 时的指纹比对 · 此处保留为 None)
            await _async_run_exception_checks(
                history_id=record_id,
                user_id=str(user["id"]),
                tenant_id=_tid(user),
                seller_name=seller_name,
                invoice_no=invoice_no,
                total_amount=total_amount,
                confidence=confidence,
                duplicate=None,
                fields=f,
            )
            rechecked = True
    except Exception as _re:
        logger.warning(f"history_update rechek hook failed (id={record_id}): {_re}")
    return {"ok": True, "rechecked": rechecked}


@router.delete("/api/history/{record_id}")
async def history_delete(record_id: str, request: Request):
    user = get_current_user_from_request(request)
    _check_history_access(user)
    # v114 · 删除时同步清掉留底的 PDF 文件
    deleted, pdf_paths = delete_ocr_history_with_pdf_paths(
        str(user["id"]), [record_id], tenant_id=_tid(user)
    )
    if deleted == 0:
        raise HTTPException(404, detail="history.not_found")
    # v114 · 检查这个 PDF 是否还被其他记录引用(多发票拆分场景共享同一 PDF)· 没人引用才真正删
    for p in pdf_paths:
        try:
            still_used = False
            from core.db import get_cursor

            with get_cursor() as cur:
                cur.execute("SELECT 1 FROM ocr_history WHERE pdf_storage_path = %s LIMIT 1", (p,))
                still_used = cur.fetchone() is not None
            if not still_used:
                pdf_storage.delete_pdf(p)
        except Exception as e:
            logger.warning(f"清理 PDF 文件失败(已忽略): {e}")
    return {"ok": True}


# v114 · PDF 留底下载接口 · 用户可下载自己识别过的原 PDF
@router.get("/api/history/{record_id}/pdf")
async def history_pdf_download(record_id: str, request: Request):
    from fastapi.responses import FileResponse

    user = get_current_user_from_request(request)
    _check_history_access(user)
    info = get_history_pdf_info(
        str(user["id"]),
        record_id,
        tenant_id=_tid(user),
        workspace_client_id=wc.active_workspace_for_request(
            request, _tid(user)
        ),  # PO-4 · 套账硬边界
    )
    if not info:
        raise HTTPException(404, detail="history.pdf_not_found")
    abs_path = pdf_storage.get_pdf_abs_path(info["pdf_storage_path"])
    if not abs_path or not abs_path.exists():
        raise HTTPException(404, detail="history.pdf_missing")
    fn = info.get("filename") or "invoice.pdf"
    if not fn.lower().endswith(".pdf"):
        fn = fn + ".pdf"
    return FileResponse(
        path=str(abs_path),
        media_type="application/pdf",
        filename=fn,
    )


# v0.16 · 批量删除历史记录
class HistoryBatchDeleteRequest(BaseModel):
    ids: List[str] = Field(..., min_length=1, max_length=500)


@router.post("/api/history/batch-delete")
async def history_batch_delete(req: HistoryBatchDeleteRequest, request: Request):
    user = get_current_user_from_request(request)
    _check_history_access(user)
    uid = str(user["id"])
    # v114 · 一次性删除 + 拿到所有要清理的 PDF 路径
    deleted, pdf_paths = delete_ocr_history_with_pdf_paths(uid, list(req.ids), tenant_id=_tid(user))
    failed = max(0, len(req.ids) - deleted)
    # v114 · 检查每个 PDF 是否还被其他记录引用 · 没人引用才物理删
    if pdf_paths:
        try:
            from core.db import get_cursor

            for p in set(pdf_paths):
                try:
                    with get_cursor() as cur:
                        cur.execute(
                            "SELECT 1 FROM ocr_history WHERE pdf_storage_path = %s LIMIT 1", (p,)
                        )
                        still_used = cur.fetchone() is not None
                    if not still_used:
                        pdf_storage.delete_pdf(p)
                except Exception as e:
                    logger.warning(f"[batch-delete] 清理 PDF 失败 {p}: {e}")
        except Exception as e:
            logger.warning(f"[batch-delete] 清理 PDF 阶段失败(已忽略): {e}")
    return {"ok": True, "deleted": deleted, "failed": failed}


# v1 别名
@router.get("/api/v1/history")
async def v1_history_list(
    request: Request, keyword: Optional[str] = None, limit: int = 50, offset: int = 0
):
    return await history_list(request, keyword, limit, offset)


@router.get("/api/v1/history/{record_id}")
async def v1_history_detail(record_id: str, request: Request):
    return await history_detail(record_id, request)


@router.put("/api/v1/history/{record_id}")
async def v1_history_update(record_id: str, req: HistoryUpdateRequest, request: Request):
    return await history_update(record_id, req, request)


@router.delete("/api/v1/history/{record_id}")
async def v1_history_delete(record_id: str, request: Request):
    return await history_delete(record_id, request)


class AssignClientRequest(BaseModel):
    client_id: Optional[int] = None  # None 表示移除归属


@router.post("/api/history/{history_id}/assign_client")
async def api_assign_client(history_id: str, req: AssignClientRequest, request: Request):
    """把发票归属到客户 · client_id=null 表示取消归属"""
    user = get_current_user_from_request(request)
    # v118.28.1 · 员工:校验 client_id 在 visible_ids 内 · 否则 403(防员工把发票归到他不能看的客户)
    if req.client_id is not None:
        visible = db.get_visible_client_ids_for_user(user)
        if visible is not None and int(req.client_id) not in set(visible):
            raise HTTPException(403, detail="client.no_access")
    ok = db.assign_invoice_to_client(
        str(user["id"]), history_id, req.client_id, tenant_id=_tid(user)
    )
    if not ok:
        raise HTTPException(400, detail="client.assign_failed")

    # 批 1 改动 1 (Zihao 2026-05-19 拍板 · v118.34.33) · 用户手动 assign 时 ·
    # 把 buyer_name + buyer_tax → client_id 的关系学进 buyer_to_client_memory ·
    # 下次 OCR 出同 buyer 就 auto-resolve · 不用每次手动选.
    if req.client_id is not None:
        try:
            h = db.get_ocr_history_detail(
                str(user["id"]),
                history_id,
                tenant_id=_tid(user),
            )
            if h:
                _pages = h.get("pages") or []
                _primary = next(
                    (
                        p
                        for p in _pages
                        if isinstance(p, dict)
                        and not p.get("is_duplicate")
                        and not p.get("is_copy")
                    ),
                    _pages[0] if _pages else {},
                )
                _f = (_primary or {}).get("fields") or {}
                _buyer_name = _f.get("buyer_name") or ""
                _buyer_tax = _f.get("buyer_tax") or ""
                if _buyer_name:
                    db.learn_buyer_to_client(
                        _buyer_name,
                        _buyer_tax,
                        int(req.client_id),
                        str(user["id"]),
                        tenant_id=_tid(user),
                    )
                    logger.info(
                        "[assign_client] learned buyer→client: %r → %s",
                        _buyer_name[:40],
                        req.client_id,
                    )
        except Exception as e:
            logger.warning(f"learn buyer→client failed (history={history_id[:8]}): {e}")

    return {"ok": True}
