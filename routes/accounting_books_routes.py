# -*- coding: utf-8 -*-
"""出账本 / 报税材料 / 月末结账接口(docs/accounting/03 §5 · 屏4)。

独立 router(同 /api/accounting 前缀):accounting_routes 承载凭证/审/配置,本文件承载
月末出口。读 = 成员;PDF/打包 = acct.ledger.export;结账 = acct.entry.approve(不可逆档)。
format=json 给屏4预览,format=pdf 直接下载;export-package 返 zip。
"""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Query, Request, Response
from pydantic import BaseModel

from core import db
from core.pos_api import PosError, ok
from routes.accounting_common import auth_member, auth_owner, gate, resolve_ws, uid
from services.accounting import books, books_pdf, closing
from services.tax import hooks as tax_hooks

router = APIRouter(prefix="/api/accounting", tags=["accounting-books"])

_BOOK_FN = {
    "gl": books.general_ledger,
    "subsidiary": books.subsidiary_ledger,
    "trial_balance": books.trial_balance,
}
_TAX_FN = {"vat": books.vat_report, "wht": books.wht_report}

_LANGS = ("th", "zh", "en", "ja")


class ClosePeriodIn(BaseModel):
    period: str


def _lang(lang: Optional[str]) -> str:
    return lang if lang in _LANGS else "th"


def _report(request, *, fn, kind, period, workspace_client_id, fmt, lang, perm):
    _, tid = auth_member(request, perm)
    with db.get_cursor_rls(tid, commit=False) as cur:
        gate(cur, tid)
        ws = resolve_ws(cur, request, tid, workspace_client_id)
        payload = fn(cur, tenant_id=tid, workspace_client_id=ws, period=period)
    if fmt == "pdf":
        pdf = books_pdf.render(kind, payload, lang=_lang(lang))
        return Response(
            content=pdf,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="{kind}_{payload["period"]}.pdf"'
            },
        )
    return ok(payload)


@router.get("/books")
async def api_books(
    request: Request,
    period: str = Query(...),
    kind: str = Query(...),
    format: str = Query("json"),
    lang: Optional[str] = Query(None),
    workspace_client_id: Optional[int] = Query(None),
):
    fn = _BOOK_FN.get(kind)
    if fn is None:
        raise PosError("acct.unexpected", 422, detail="bad_kind")
    perm = "acct.ledger.export" if format == "pdf" else "acct.entry.view"
    return _report(
        request,
        fn=fn,
        kind=kind,
        period=period,
        workspace_client_id=workspace_client_id,
        fmt=format,
        lang=lang,
        perm=perm,
    )


@router.get("/tax-reports")
async def api_tax_reports(
    request: Request,
    period: str = Query(...),
    kind: str = Query(...),
    format: str = Query("json"),
    lang: Optional[str] = Query(None),
    workspace_client_id: Optional[int] = Query(None),
):
    fn = _TAX_FN.get(kind)
    if fn is None:
        raise PosError("acct.unexpected", 422, detail="bad_kind")
    perm = "acct.ledger.export" if format == "pdf" else "acct.entry.view"
    return _report(
        request,
        fn=fn,
        kind=kind,
        period=period,
        workspace_client_id=workspace_client_id,
        fmt=format,
        lang=lang,
        perm=perm,
    )


@router.get("/financials")
async def api_financials(
    request: Request,
    period: str = Query(...),
    format: str = Query("json"),
    lang: Optional[str] = Query(None),
    workspace_client_id: Optional[int] = Query(None),
):
    perm = "acct.ledger.export" if format == "pdf" else "acct.entry.view"
    return _report(
        request,
        fn=books.financials,
        kind="financials",
        period=period,
        workspace_client_id=workspace_client_id,
        fmt=format,
        lang=lang,
        perm=perm,
    )


@router.post("/close-period")
async def api_close_period(
    req: ClosePeriodIn,
    request: Request,
    workspace_client_id: Optional[int] = Query(None),
):
    user, tid = auth_owner(request, "acct.entry.approve")
    with db.get_cursor_rls(tid, commit=True) as cur:
        gate(cur, tid)
        ws = resolve_ws(cur, request, tid, workspace_client_id)
        result = closing.close_period(
            cur, tenant_id=tid, workspace_client_id=ws, period=req.period, closed_by=uid(user)
        )
        # 报税挂点(docs/tax-filing/04 seam):结账完成 → 本期税表草稿。SAVEPOINT 隔离,
        # 失败吞不挡结账,兜底=报税中心手动重算。
        tax_hooks.enqueue_generate(
            cur, tenant_id=tid, workspace_client_id=ws, period=result["closed"]
        )
    return ok(result)


@router.get("/export-package")
async def api_export_package(
    request: Request,
    period: str = Query(...),
    lang: Optional[str] = Query(None),
    workspace_client_id: Optional[int] = Query(None),
):
    _, tid = auth_member(request, "acct.ledger.export")
    period = closing.validate_period(period)
    with db.get_cursor_rls(tid, commit=False) as cur:
        gate(cur, tid)
        ws = resolve_ws(cur, request, tid, workspace_client_id)
        payloads = {
            "gl": books.general_ledger(cur, tenant_id=tid, workspace_client_id=ws, period=period),
            "subsidiary": books.subsidiary_ledger(
                cur, tenant_id=tid, workspace_client_id=ws, period=period
            ),
            "trial_balance": books.trial_balance(
                cur, tenant_id=tid, workspace_client_id=ws, period=period
            ),
            "vat": books.vat_report(cur, tenant_id=tid, workspace_client_id=ws, period=period),
            "wht": books.wht_report(cur, tenant_id=tid, workspace_client_id=ws, period=period),
            "financials": books.financials(
                cur, tenant_id=tid, workspace_client_id=ws, period=period
            ),
        }
    data = books_pdf.export_package(payloads, period=period, lang=_lang(lang))
    return Response(
        content=data,
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="pearnly_books_{period}.zip"'},
    )
