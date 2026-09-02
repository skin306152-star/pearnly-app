# -*- coding: utf-8 -*-

from __future__ import annotations

import logging
from typing import Any, List, Optional

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import Response
from pydantic import BaseModel, Field

from core import db
from core import thai_date
from core import workspace_context as wc
from services.audit import file_access as audit_file_access
from services.ocr import pdf_storage
from services.ocr.pdf_utils import render_page_png_bytes
from core.db import (
    commit_staged_ocr_history,
    delete_ocr_history_with_pdf_paths,
    get_history_pdf_info,
    get_ocr_history_detail,
    list_ocr_history,
    update_ocr_history_pages,
)
from core.auth import get_current_user_from_request
from routes.history_assign_routes import router as _assign_router
from core.route_helpers import _check_history_access, _tid, content_disposition
from services.exceptions.exception_checks import _async_run_exception_checks, _parse_money
from services.erp import team_access
from services.intake_bridge import convert as convert_svc, erp_confirmation_access
from services.intake_bridge import mutable_history_access
from services.ocr_history.posting_manual import (
    _ITEM_TYPE_VALUES,
    _PAYMENT_VALUES,
    backflow_supplier_profile,
    update_history_posting_manual,
)

logger = logging.getLogger("mr-pilot")

router = APIRouter()
# 归属类端点(assign_workspace / assign_client)拆到 history_assign_routes,挂同一棵树
# 让 app.py 零改动;单向依赖(此处 import 它,它不 import 此处)不成环。
router.include_router(_assign_router)


class HistoryUpdateRequest(BaseModel):
    pages: List[Any] = Field(..., description="完整 pages 数组(会计修改后的)")


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
    limit = max(1, min(int(limit), 100))
    offset = max(0, int(offset))
    src = source if source in ("upload", "line", "email") else None
    sts = status if status in ("confirmed", "pending", "failed") else None
    return list_ocr_history(
        user_id=str(user["id"]),
        retention_days=retention,
        keyword=keyword.strip() if keyword else None,
        limit=limit,
        offset=offset,
        tenant_id=team_access.tenant_record_scope(request, user),
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
        tenant_id=team_access.tenant_record_scope(request, user),
    )
    if not detail:
        raise HTTPException(404, detail="history.not_found")
    return detail


class OcrCommitRequest(BaseModel):
    ids: List[str] = Field(..., min_length=1, max_length=500, description="待落库的草稿记录 id")


@router.post("/api/ocr/commit")
async def ocr_commit(req: OcrCommitRequest, request: Request):
    """录入第4步完成:把本人草稿落进识别记录;F1共享确认必须已有匹配正式单据。"""
    user = get_current_user_from_request(request)
    _check_history_access(user)
    tenant_id = _tid(user)
    team_access.assert_owned_histories(request, user, req.ids)
    guarded = erp_confirmation_access.commit_shared_confirmation(request, user, tenant_id, req.ids)
    if guarded is not None:
        return {"ok": True, "committed": guarded}
    if user.get("entry") == "erp":
        with db.get_cursor_rls(tenant_id=tenant_id, user_id=str(user["id"])) as cur:
            unconverted = convert_svc.unconverted_owned_history_ids(
                cur,
                tenant_id=tenant_id,
                user_id=str(user["id"]),
                history_ids=req.ids,
            )
        if unconverted:
            raise HTTPException(
                409,
                detail={
                    "code": "erp.formal_document_required",
                    "history_ids": unconverted,
                },
            )
    n = commit_staged_ocr_history(
        str(user["id"]), list(req.ids), tenant_id=team_access.tenant_record_scope(request, user)
    )
    return {"ok": True, "committed": n}


class OcrConvertRequest(BaseModel):
    history_ids: List[str] = Field(..., min_length=1, max_length=500)
    workspace_client_id: int


@router.post("/api/ocr/convert-documents")
async def ocr_convert_documents(req: OcrConvertRequest, request: Request):
    """Convert histories; shared confirmation groups by persisted workspace."""
    user = get_current_user_from_request(request)
    _check_history_access(user)
    erp_confirmation_access.require_formal_conversion_entry(user)
    tenant_id = _tid(user)
    team_access.assert_owned_histories(request, user, req.history_ids)
    shared_confirmation = erp_confirmation_access.is_shared_confirmation_context(user, tenant_id)
    cursor_args = {"tenant_id": tenant_id, "user_id": str(user["id"]), "commit": True}
    if not shared_confirmation:
        cursor_args["workspace_client_id"] = req.workspace_client_id
    with db.get_cursor_rls(**cursor_args) as cur:
        confirmation = erp_confirmation_access.guard_confirmation(
            cur,
            request,
            user,
            tenant_id,
            req.workspace_client_id,
            req.history_ids,
            shared_context=shared_confirmation,
        )
        if user.get("entry") == "erp":
            invalid = convert_svc.validate_erp_histories(
                cur, tenant_id=tenant_id, history_ids=req.history_ids
            )
            if invalid:
                raise HTTPException(
                    409,
                    detail={"code": "erp.declaration_required", "histories": invalid},
                )
        result = convert_svc.convert_histories(
            cur, tenant_id=tenant_id, user_id=str(user["id"]), history_ids=req.history_ids
        )
        if user.get("entry") == "erp":
            resolved_ids = {str(row.get("history_id")) for row in result.get("converted") or []}
            resolved_ids.update(
                str(row.get("history_id"))
                for row in result.get("skipped") or []
                if row.get("reason") == "already_converted"
            )
            if resolved_ids:
                erp_confirmation_access.finish_resolved_histories(
                    cur,
                    confirmation,
                    tenant_id,
                    str(user["id"]),
                    req.workspace_client_id,
                    resolved_ids,
                )
    return result


def _derive_dates_from_printed(pages: Optional[List[dict]]) -> Optional[str]:
    """按票面日期(date_raw)重算库里的公历 date。返回认不出的那串票面值(供闸拦下)。

    会计改的是票面那一串 —— 泰国票面印佛历,人看什么就填什么,换算在这里发生一次,
    界面上不出现公历。date_raw 为空(旧记录/文字层来源)则沿用既有 date 不动。
    """
    for p in pages or []:
        if not isinstance(p, dict):
            continue
        fields = p.get("fields")
        if not isinstance(fields, dict):
            continue
        printed = fields.get("date_raw")
        if not str(printed or "").strip():
            # 无票面原文可依据时,守住底线:date 仍不许是佛历年
            if thai_date.buddhist_year_of(fields.get("date")):
                return str(fields.get("date"))
            continue
        derived = thai_date.gregorian_from_printed(printed)
        if not derived:
            return str(printed)
        fields["date"] = derived
    return None


@router.put("/api/history/{record_id}")
async def history_update(record_id: str, req: HistoryUpdateRequest, request: Request):
    user = get_current_user_from_request(request)
    _check_history_access(user)
    if not req.pages:
        raise HTTPException(400, detail="history.empty_pages")
    bad_printed = _derive_dates_from_printed(req.pages)
    if bad_printed:
        raise HTTPException(400, detail="history.date_unreadable")
    tenant_id = _tid(user)
    ok = mutable_history_access.update_history_pages(request, user, tenant_id, record_id, req.pages)
    if ok is None:
        scope_tenant_id = team_access.tenant_record_scope(request, user)
        ok = update_ocr_history_pages(
            str(user["id"]), record_id, req.pages, tenant_id=scope_tenant_id
        )
    if not ok:
        raise HTTPException(404, detail="history.not_found")
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
    rechecked = False
    try:
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
            detail_now = get_ocr_history_detail(
                str(user["id"]),
                record_id,
                tenant_id=team_access.tenant_record_scope(request, user),
            )
            confidence = (detail_now or {}).get("confidence")
            db.delete_pending_exceptions_by_history(
                record_id, tenant_id=_tid(user), user_id=str(user["id"])
            )
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


class HistoryPostingRequest(BaseModel):
    payment: Optional[str] = None  # "cash" | "credit" | null(缺省键=不动 · null=删键恢复自动)
    item_type: Optional[str] = None  # "goods" | "expense" | null


_POSTING_PAYMENT_VALUES = _PAYMENT_VALUES | {None}
_POSTING_ITEM_TYPE_VALUES = _ITEM_TYPE_VALUES | {None}


@router.patch("/api/history/{record_id}/posting")
async def history_update_posting(record_id: str, req: HistoryPostingRequest, request: Request):
    """F5 人工裁决:复核屏改现/赊、货/费(payment_verdict/choose_doc_type 最高优先级判据)。

    回流(F4 · L2)在 posting_manual.backflow_supplier_profile:失败只 warning,不挡本次保存。
    """
    user = get_current_user_from_request(request)
    _check_history_access(user)
    tenant_id = _tid(user)
    changed = req.model_dump(exclude_unset=True)
    if not changed:
        return {"ok": True}
    # 值域闸在路由层:传错字 → 422,不许被 DAL 静默当"清除人工裁决"(DAL 的宽容 pop 语义=删键)。
    if "payment" in changed and changed["payment"] not in _POSTING_PAYMENT_VALUES:
        raise HTTPException(422, detail="history.posting_payment_invalid")
    if "item_type" in changed and changed["item_type"] not in _POSTING_ITEM_TYPE_VALUES:
        raise HTTPException(422, detail="history.posting_item_type_invalid")
    result = mutable_history_access.update_history_posting(
        request, user, tenant_id, record_id, changed
    )
    if result is None:
        scope_tenant_id = team_access.tenant_record_scope(request, user)
        result = update_history_posting_manual(
            str(user["id"]), record_id, scope_tenant_id, **changed
        )
    if not result.ok:
        raise HTTPException(404, detail="history.not_found")
    backflow_supplier_profile(
        record_id=record_id,
        tenant_id=tenant_id,
        payment=changed.get("payment"),
        item_type=changed.get("item_type"),
        workspace_client_id=result.workspace_client_id,
        seller_tax=result.seller_tax,
    )
    return {"ok": True}


@router.delete("/api/history/{record_id}")
async def history_delete(record_id: str, request: Request):
    user = get_current_user_from_request(request)
    _check_history_access(user)
    tenant_id = _tid(user)
    guarded = mutable_history_access.delete_histories(request, user, tenant_id, [record_id])
    if guarded is None:
        scope_tenant_id = team_access.tenant_record_scope(request, user)
        guarded = delete_ocr_history_with_pdf_paths(
            str(user["id"]), [record_id], tenant_id=scope_tenant_id
        )
    deleted, pdf_paths = guarded
    if deleted == 0:
        raise HTTPException(404, detail="history.not_found")
    # v114 · 检查这个 PDF 是否还被其他记录引用(多发票拆分场景共享同一 PDF)· 没人引用才真正删
    for p in pdf_paths:
        try:
            still_used = False
            from core.db import get_cursor_rls

            # 跨用户 PDF 引用计数(多发票共享同一 PDF)· 故意不按 RLS 收窄 → bypass。
            with get_cursor_rls(bypass=True) as cur:
                cur.execute("SELECT 1 FROM ocr_history WHERE pdf_storage_path = %s LIMIT 1", (p,))
                still_used = cur.fetchone() is not None
            if not still_used:
                pdf_storage.delete_pdf(p)
        except Exception as e:
            logger.warning(f"清理 PDF 文件失败(已忽略): {e}")
    return {"ok": True}


def _log_pdf_view(request: Request, user: dict, record_id: str, kind: str, **extra) -> None:
    """留底 PDF/页图取件审计(两端点共用,收敛重复调用样板)。"""
    audit_file_access.log_user_file_access(
        request,
        user,
        audit_file_access.OCR_PDF_VIEWED,
        target_type="ocr_history",
        target_id=record_id,
        details={"kind": kind, **extra},
    )


# v114 · PDF 留底下载接口 · 用户可下载自己识别过的原 PDF
@router.get("/api/history/{record_id}/pdf")
async def history_pdf_download(record_id: str, request: Request):
    user = get_current_user_from_request(request)
    _check_history_access(user)
    # 同 page.png · 单条复核按归属授权 · 不叠加活跃套账软过滤(否则对手方票 404)
    info = get_history_pdf_info(
        str(user["id"]),
        record_id,
        tenant_id=team_access.tenant_record_scope(request, user),
    )
    if not info:
        raise HTTPException(404, detail="history.pdf_not_found")
    # 落盘密文经 pdf_storage.read_bytes 解回明文再出流(FileResponse 会直吐密文,故换 Response)。
    data = pdf_storage.read_bytes(info["pdf_storage_path"])
    if data is None:
        raise HTTPException(404, detail="history.pdf_missing")
    fn = info.get("filename") or "invoice.pdf"
    if not fn.lower().endswith(".pdf"):
        fn = fn + ".pdf"
    _log_pdf_view(request, user, record_id, "pdf")
    return Response(
        content=data,
        media_type="application/pdf",
        headers={"Content-Disposition": content_disposition(fn, "invoice.pdf")},
    )


@router.get("/api/history/{record_id}/page/{page}.png")
async def history_page_png(record_id: str, page: int, request: Request):
    user = get_current_user_from_request(request)
    _check_history_access(user)
    info = get_history_pdf_info(
        str(user["id"]),
        record_id,
        tenant_id=team_access.tenant_record_scope(request, user),
    )
    if not info:
        raise HTTPException(404, detail="history.pdf_not_found")
    # 先解密再从字节渲染(留底加密后不能把密文路径直喂 fitz)。
    data = pdf_storage.read_bytes(info["pdf_storage_path"])
    if data is None:
        raise HTTPException(404, detail="history.pdf_missing")
    rendered = render_page_png_bytes(data, page=page)
    if rendered is None:
        raise HTTPException(422, detail="history.render_failed")
    png, total_pages = rendered
    _log_pdf_view(request, user, record_id, "page_png", page=page)
    return Response(
        content=png,
        media_type="image/png",
        headers={
            "Cache-Control": "private, max-age=300",
            "X-Page-Count": str(total_pages),  # 多页 PDF → 前端翻页看每张
        },
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
    tenant_id = _tid(user)
    guarded = mutable_history_access.delete_histories(request, user, tenant_id, list(req.ids))
    if guarded is None:
        scope_tenant_id = team_access.tenant_record_scope(request, user)
        guarded = delete_ocr_history_with_pdf_paths(uid, list(req.ids), tenant_id=scope_tenant_id)
    deleted, pdf_paths = guarded
    failed = max(0, len(req.ids) - deleted)
    # v114 · 检查每个 PDF 是否还被其他记录引用 · 没人引用才物理删
    if pdf_paths:
        try:
            from core.db import get_cursor_rls

            for p in set(pdf_paths):
                try:
                    # 跨用户 PDF 引用计数 · 故意不按 RLS 收窄 → bypass。
                    with get_cursor_rls(bypass=True) as cur:
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
