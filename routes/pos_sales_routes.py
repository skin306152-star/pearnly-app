# -*- coding: utf-8 -*-
"""POS 收银前台路由(POS 项目 · PO-B2 · docs/pos/04 §3/§5/§6)。

薄层:鉴权(POS token 收银员 / 老板)→ 模块守门(pos)→ 账套归属 → 调 services/pos。统一信封。
收银员 token 自带 workspace_client_id;老板调需在 body/query 给 workspace_client_id。写端单事务
(get_cursor_rls commit=True)发号/扣库存/落库原子。
"""

from __future__ import annotations

import asyncio
import logging
from typing import List, Optional

from fastapi import APIRouter, Query, Request
from fastapi.responses import FileResponse, Response
from pydantic import BaseModel, Field

from core import db, pos_api
from core.pos_api import PosError, assert_module_enabled, ok, require_workspace_access
from services.imaging import image_store
from services.pos import (
    approval as approval_svc,
    catalog,
    receipt_pdf,
    refund as refund_svc,
    sale as sale_svc,
    sales_query as sq,
    upgrade as upgrade_svc,
)

router = APIRouter(prefix="/api/pos", tags=["pos-sales"])
logger = logging.getLogger("mr-pilot")

# 售出后台留档到 Google Sheet(fire-and-forget)· 持强引用防任务被 GC(asyncio 已知坑)。
_sheets_sync_tasks: set = set()


def _schedule_sheets_sync(tenant_id: str, workspace_client_id: int, sale_id: str) -> None:
    async def _run():
        try:
            from services.pos import sheets_sync

            with db.get_cursor_rls(tenant_id, commit=True) as cur:
                sheets_sync.sync_sale(
                    cur,
                    tenant_id=tenant_id,
                    workspace_client_id=workspace_client_id,
                    sale_id=sale_id,
                )
        except Exception as e:  # noqa: BLE001 — 留档失败绝不影响已完成的收银
            logger.warning("pos sheets sync task failed (sale_id=%s): %s", sale_id, e)

    task = asyncio.create_task(_run())
    _sheets_sync_tasks.add(task)
    task.add_done_callback(_sheets_sync_tasks.discard)


def _subject(request: Request) -> tuple[dict, str]:
    return pos_api.subject(request)


def _resolve_ws(user: dict, override: Optional[int]) -> int:
    return pos_api.resolve_ws(user, override)


def _read(request: Request, ws_override: Optional[int], fn, commit: bool = False):
    user, tid = _subject(request)
    ws = _resolve_ws(user, ws_override)
    with db.get_cursor_rls(tid, commit=commit) as cur:
        assert_module_enabled(cur, tid, "pos")
        require_workspace_access(cur, request, tid, ws)
        return ok(fn(cur, tid, ws, user))


def _write(request: Request, ws_override: Optional[int], fn):
    # 写事务信封收在 core.pos_api.pos_write(单一事实源)· 退货授权闸走同一执行器。
    return pos_api.pos_write(request, ws_override=ws_override, write_fn=fn)


def _created_by(user: dict) -> Optional[str]:
    return str(user["id"]) if user.get("id") else None


# ── 启动包 / 选品 ──────────────────────────────────────────────────────
@router.get("/bootstrap")
async def api_bootstrap(request: Request, workspace_client_id: Optional[int] = Query(None)):
    return _read(
        request,
        workspace_client_id,
        lambda cur, tid, ws, user: catalog.bootstrap(cur, tenant_id=tid, workspace_client_id=ws),
        commit=True,
    )


@router.get("/payment-methods")
async def api_payment_methods(request: Request, workspace_client_id: Optional[int] = Query(None)):
    """收银台轻量拉收款设置(与 bootstrap.payment 同一份 get_settings · 不投影)。

    老板在别处改收款方式后,已开着的收银台回前台用它同步(走轻量口而非重拉整包 bootstrap)。
    收银员 token 可读(同 bootstrap 鉴权),非 admin 口;返回的银行/PromptPay 是结账给顾客核对的。
    """
    from services.pos import payment_settings as pay_settings

    return _read(
        request,
        workspace_client_id,
        lambda cur, tid, ws, user: pay_settings.get_settings(
            cur, tenant_id=tid, workspace_client_id=ws
        ),
    )


@router.get("/products")
async def api_products(
    request: Request,
    workspace_client_id: Optional[int] = Query(None),
    q: Optional[str] = None,
    category: Optional[str] = None,
):
    return _read(
        request,
        workspace_client_id,
        lambda cur, tid, ws, user: catalog.list_products(
            cur, tenant_id=tid, workspace_client_id=ws, q=q, category=category
        ),
    )


@router.get("/products/image/{name}")
async def api_product_image(name: str, request: Request):
    """商品图取图(收银台用)。POS token 取不到 /api/uploads(那条只认登录用户),
    故走本路由:从 token 拿 tenant → 沙盒内回流本租户图片(uuid 文件名 + 沙盒路径双保险)。"""
    _user, tid = _subject(request)
    path = image_store.local_path(tid, name)
    if not path:
        raise PosError("pos.not_found", 404)
    ext = path.suffix.lstrip(".").lower()
    return FileResponse(
        str(path),
        media_type=image_store.media_type_for(ext),
        headers={"Cache-Control": "public, max-age=31536000, immutable"},
    )


@router.get("/products/by-barcode")
async def api_by_barcode(
    request: Request, code: str = Query(...), workspace_client_id: Optional[int] = Query(None)
):
    return _read(
        request,
        workspace_client_id,
        lambda cur, tid, ws, user: catalog.product_by_barcode(
            cur, tenant_id=tid, workspace_client_id=ws, code=code
        ),
    )


# ── 小票 ──────────────────────────────────────────────────────────────
class SaleLine(BaseModel):
    product_id: str
    sell_unit: Optional[str] = None
    qty: float = Field(..., gt=0)
    unit_price: float = Field(..., ge=0)
    line_discount: float = Field(0, ge=0)
    batch_id: Optional[str] = None


class HeaderDiscount(BaseModel):
    type: str = "none"
    value: float = 0


class Payment(BaseModel):
    method: str
    amount: float
    ref: Optional[str] = None


class CreateSaleRequest(BaseModel):
    workspace_client_id: Optional[int] = None
    client_uuid: Optional[str] = None
    shift_id: Optional[str] = None
    terminal_id: Optional[int] = None
    doc_kind: str = "receipt"
    member_client_id: Optional[int] = None
    price_includes_vat: bool = False
    lines: List[SaleLine] = Field(..., min_length=1)
    header_discount: Optional[HeaderDiscount] = None
    payments: List[Payment] = Field(default_factory=list)
    sold_at: Optional[str] = None
    # PC-1a:折扣超限/改价时,收银员在授权窗填店长收银员身份 + PIN 覆盖(flag 关时忽略)。
    approval: Optional[approval_svc.ManagerApproval] = None


def _dump(m) -> dict:
    return m.model_dump() if hasattr(m, "model_dump") else m.dict()


@router.post("/sales")
async def api_create_sale(req: CreateSaleRequest, request: Request):
    payload = _dump(req)
    user, tid = _subject(request)
    ws = _resolve_ws(user, req.workspace_client_id)
    with db.get_cursor_rls(tid, commit=True) as cur:
        assert_module_enabled(cur, tid, "pos")
        require_workspace_access(cur, request, tid, ws)
        result = sale_svc.create_sale(
            cur,
            tenant_id=tid,
            workspace_client_id=ws,
            payload={**payload, "cashier_id": user.get("cashier_id")},
            created_by=_created_by(user),
            operator=user,
        )
    # 只对本次真新建的单留档(client_uuid 命中去重的重放不重复追加,天然幂等)。
    if not result.get("deduped"):
        _schedule_sheets_sync(tid, ws, result["sale"]["id"])
    return ok(result)


class SyncRequest(BaseModel):
    workspace_client_id: Optional[int] = None
    sales: List[dict] = Field(..., min_length=1, max_length=500)


@router.post("/sales/sync")
async def api_sync_sales(req: SyncRequest, request: Request):
    """离线批量补传:逐张 client_uuid 幂等,部分失败不卡其余(失败项带错误码供端上重试)。"""
    return _write(
        request,
        req.workspace_client_id,
        lambda cur, tid, ws, user: sale_svc.sync_sales(
            cur,
            tenant_id=tid,
            workspace_client_id=ws,
            items=req.sales,
            cashier_id=user.get("cashier_id"),
            created_by=_created_by(user),
            operator=user,
        ),
    )


@router.get("/sales/by-receipt")
async def api_sale_by_receipt(
    request: Request, no: str = Query(...), workspace_client_id: Optional[int] = Query(None)
):
    return _read(
        request,
        workspace_client_id,
        lambda cur, tid, ws, user: sale_svc.get_sale_by_receipt(
            cur, tenant_id=tid, workspace_client_id=ws, receipt_no=no
        ),
    )


@router.get("/sales/today")
async def api_sales_today(request: Request, workspace_client_id: Optional[int] = Query(None)):
    """收银台今日已完成交易(退货/作废入口 · 收银员 token 可读 · 限当前账套)。

    路由须排在 /sales/{sale_id} 之前,否则 "today" 会被当成 sale_id 匹配。
    """
    return _read(
        request,
        workspace_client_id,
        lambda cur, tid, ws, user: sq.list_today(cur, tenant_id=tid, workspace_client_id=ws),
    )


@router.get("/sales/{sale_id}")
async def api_get_sale(
    sale_id: str, request: Request, workspace_client_id: Optional[int] = Query(None)
):
    return _read(
        request,
        workspace_client_id,
        lambda cur, tid, ws, user: sale_svc.get_sale_detail(
            cur, tenant_id=tid, workspace_client_id=ws, sale_id=sale_id
        ),
    )


class RefundLine(BaseModel):
    sale_line_id: str
    qty: float = Field(..., gt=0)


class RefundPayment(BaseModel):
    method: str
    amount: float = Field(..., gt=0)


class RefundRequest(BaseModel):
    workspace_client_id: Optional[int] = None
    client_uuid: Optional[str] = None
    lines: List[RefundLine] = Field(..., min_length=1)
    refund_method: str = "cash"
    # 原路拆退:混合支付原单按各方式拆退款(现金退现金/刷卡退刷卡)。不给则走 refund_method 单笔。
    refund_payments: Optional[List[RefundPayment]] = None
    approval: Optional[approval_svc.ManagerApproval] = None


class VoidRequest(BaseModel):
    workspace_client_id: Optional[int] = None
    approval: Optional[approval_svc.ManagerApproval] = None


@router.post("/sales/{sale_id}/refund")
async def api_refund(sale_id: str, req: RefundRequest, request: Request):
    return approval_svc.execute_gated_write(
        request,
        ws_override=req.workspace_client_id,
        approval=_dump(req.approval) if req.approval else None,
        write_fn=lambda cur, tid, ws, user: refund_svc.refund(
            cur,
            tenant_id=tid,
            workspace_client_id=ws,
            original_sale_id=sale_id,
            lines=[_dump(line) for line in req.lines],
            refund_method=req.refund_method,
            refund_payments=(
                [_dump(p) for p in req.refund_payments] if req.refund_payments else None
            ),
            client_uuid=req.client_uuid,
            cashier_id=user.get("cashier_id"),
            created_by=_created_by(user),
        ),
        action="pos.refund.approved",
        sale_id_of=lambda r: r["refund_sale"]["id"],
        audit_details={"original_sale_id": sale_id, "method": req.refund_method},
    )


@router.post("/sales/{sale_id}/void")
async def api_void(sale_id: str, request: Request, req: Optional[VoidRequest] = None):
    req = req or VoidRequest()
    return approval_svc.execute_gated_write(
        request,
        ws_override=req.workspace_client_id,
        approval=_dump(req.approval) if req.approval else None,
        write_fn=lambda cur, tid, ws, user: sale_svc.void_sale(
            cur,
            tenant_id=tid,
            workspace_client_id=ws,
            sale_id=sale_id,
            created_by=_created_by(user),
            operator=user,
        ),
        action="pos.void.approved",
        sale_id_of=lambda _r: sale_id,
    )


class FullInvoiceBuyer(BaseModel):
    party_type: str = "company"
    name: Optional[str] = None
    tax_id: Optional[str] = None
    branch_type: Optional[str] = None
    branch_no: Optional[str] = None
    address: Optional[str] = None


class FullInvoiceRequest(BaseModel):
    workspace_client_id: Optional[int] = None
    buyer: Optional[FullInvoiceBuyer] = None


@router.post("/sales/{sale_id}/full-tax-invoice")
async def api_full_tax_invoice(sale_id: str, req: FullInvoiceRequest, request: Request):
    """小票升级正式税票:落 sales_documents(合规连号/冻结/不可改)+ 回填 full_invoice_id。"""
    buyer = _dump(req.buyer) if req.buyer else None
    return _write(
        request,
        req.workspace_client_id,
        lambda cur, tid, ws, user: upgrade_svc.upgrade_to_full_tax_invoice(
            cur,
            tenant_id=tid,
            workspace_client_id=ws,
            sale_id=sale_id,
            buyer=buyer,
            created_by=_created_by(user),
        ),
    )


def _promptpay_qr_result(cur, tenant_id, workspace_client_id, amount) -> dict:
    """按账套 promptpay_id + 金额出 PromptPay 码(payload+PNG)。未配 ID → 422。两个 QR 端点共用。"""
    import base64

    from services.sales.promptpay import build_payload, build_qr_png

    cur.execute(
        "SELECT promptpay_id FROM workspace_clients WHERE tenant_id = %s AND id = %s",
        (tenant_id, workspace_client_id),
    )
    row = cur.fetchone()
    ppid = row["promptpay_id"] if row else None
    if not ppid:
        raise PosError("pos.line_invalid", 422, detail="no_promptpay_id")
    return {
        "qr_payload": build_payload(ppid, amount),
        "png_base64": base64.b64encode(build_qr_png(ppid, amount)).decode("ascii"),
        "amount": f"{amount:.2f}",
    }


@router.get("/sales/{sale_id}/promptpay-qr")
async def api_promptpay_qr(
    sale_id: str, request: Request, workspace_client_id: Optional[int] = Query(None)
):
    from services.pos import sales_store

    def _fn(cur, tid, ws, user):
        sale = sales_store.get_sale(cur, tenant_id=tid, workspace_client_id=ws, sale_id=sale_id)
        if not sale:
            raise PosError("pos.product_not_found", 404)
        return _promptpay_qr_result(cur, tid, ws, sale["grand_total"])

    return _read(request, workspace_client_id, _fn)


@router.get("/promptpay-qr")
async def api_promptpay_qr_presale(
    request: Request,
    amount: float = Query(..., ge=0),
    workspace_client_id: Optional[int] = Query(None),
):
    """收款前先出码:按账套配的 PromptPay ID + 待收金额生成二维码(无需先建单)。

    收银员可调(_read)。未配 ID → 422,收银端提示去「收款设置」填。
    """
    from decimal import Decimal

    def _fn(cur, tid, ws, user):
        return _promptpay_qr_result(cur, tid, ws, Decimal(str(amount)).quantize(Decimal("0.01")))

    return _read(request, workspace_client_id, _fn)


@router.get("/sales/{sale_id}/receipt-pdf")
async def api_receipt_pdf(
    sale_id: str,
    request: Request,
    workspace_client_id: Optional[int] = Query(None),
    width: int = Query(80),
):
    user, tid = _subject(request)
    ws = _resolve_ws(user, workspace_client_id)
    with db.get_cursor_rls(tid) as cur:
        assert_module_enabled(cur, tid, "pos")
        require_workspace_access(cur, request, tid, ws)
        pdf = receipt_pdf.build_receipt_pdf(
            cur, tenant_id=tid, workspace_client_id=ws, sale_id=sale_id, width_mm=width
        )
    return Response(content=pdf, media_type="application/pdf")
