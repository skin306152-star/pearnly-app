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
from fastapi.responses import Response
from pydantic import BaseModel, Field

from core import db
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
from core.route_helpers import _plan_permissions, _tid, content_disposition
from services.exceptions.exception_checks import _async_run_exception_checks, _parse_money
from services.ocr_history.posting_manual import (
    _ITEM_TYPE_VALUES,
    _PAYMENT_VALUES,
    backflow_supplier_profile,
    update_history_posting_manual,
)

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
    # 单条按主键查复核:授权按归属(user_id + tenant)· 不叠加活跃套账软过滤。
    # 套账过滤是列表的视图收窄,异常单据的 workspace_client_id 常被打成发票对手方
    # 而非活跃套账,叠加后会把列表里能看到的票挡成 404(与 page.png 同口径)。
    detail = get_ocr_history_detail(
        str(user["id"]),
        record_id,
        tenant_id=_tid(user),
    )
    if not detail:
        raise HTTPException(404, detail="history.not_found")
    return detail


class OcrCommitRequest(BaseModel):
    ids: List[str] = Field(..., min_length=1, max_length=500, description="待落库的草稿记录 id")


@router.post("/api/ocr/commit")
async def ocr_commit(req: OcrCommitRequest, request: Request):
    """录入第4步完成(无论仅完成 / 导出 / 推送)→ 把草稿记录落进识别记录(staged→FALSE)。

    幂等:已落库 / 非本人的 id 跳过,只翻仍属本人的草稿。前端任一终态动作都调,确保必落库。
    """
    user = get_current_user_from_request(request)
    _check_history_access(user)
    n = commit_staged_ocr_history(str(user["id"]), list(req.ids), tenant_id=_tid(user))
    return {"ok": True, "committed": n}


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
    result = update_history_posting_manual(str(user["id"]), record_id, tenant_id, **changed)
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
        tenant_id=_tid(user),
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
    """复核时边看原票边改字段:把留底 PDF 的指定页渲成 PNG 供前端图查看器。

    授权按归属(user_id + tenant)· 不叠加活跃套账过滤:复核中的原图是用户刚上传、
    自己拥有的记录的视觉辅助;记录的 workspace_client_id 常被打成发票对手方(买/卖方)
    而非活跃套账,套用列表用的套账软过滤会把刚上传的票挡成 404。归属校验已足够,
    且用户切套账本就能看到自己全部记录。
    """
    user = get_current_user_from_request(request)
    _check_history_access(user)
    info = get_history_pdf_info(
        str(user["id"]),
        record_id,
        tenant_id=_tid(user),
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
    deleted, pdf_paths = delete_ocr_history_with_pdf_paths(uid, list(req.ids), tenant_id=_tid(user))
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


class AssignClientRequest(BaseModel):
    client_id: Optional[int] = None  # None 表示移除归属


class AssignWorkspaceRequest(BaseModel):
    workspace_client_id: int = Field(..., description="目标套账 id(必须指定,不许清空归属)")


@router.post("/api/history/{history_id}/assign_workspace")
async def api_assign_workspace(history_id: str, req: AssignWorkspaceRequest, request: Request):
    """把识别记录改归属到另一个套账(税号路由再准也有例外:代付/税号印错的票)。

    只许挪到本租户的套账;不提供清空(NULL 会让 Express 方向判定失锚,见 persist 注释)。
    """
    user = get_current_user_from_request(request)
    _check_history_access(user)
    _tenant = _tid(user)
    if not _tenant:
        raise HTTPException(400, detail="workspace.required")
    from core.workspace_context import assert_workspace_in_tenant

    with db.get_cursor() as cur:
        assert_workspace_in_tenant(
            cur, tenant_id=_tenant, workspace_client_id=int(req.workspace_client_id)
        )
    ok = db.update_history_workspace_client_id(
        history_id, int(req.workspace_client_id), str(user["id"]), tenant_id=_tenant
    )
    if not ok:
        raise HTTPException(400, detail="history.assign_workspace_failed")
    return {"ok": True, "workspace_client_id": int(req.workspace_client_id)}


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
