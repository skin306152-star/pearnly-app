# -*- coding: utf-8 -*-
"""自动报税接口(docs/tax-filing/03 契约 · 信封同 POS)。

鉴权按权限码逐路由守门(tax.filing.view / create / approve · tax.settings.manage,
registry 已留位)。模块门控 accounting:报税吃做账账本,做账没开报税无米;registry 的
tax 码组故意不挂模块键(tenant_modules 暂无 tax 键,见 services/authz/registry.py 注),
独立 tax 开关留给前端窗口随导航一并定。套账解析 fail-closed(缺 → workspace.required)。
e-Tax 直报未接通(RD 开放度未确认)→ file(etax) 诚实返 tax.efiling_failed。
"""

from __future__ import annotations

from datetime import date
from typing import Optional

from fastapi import APIRouter, Query, Request, Response
from pydantic import BaseModel

from core import db
from core.pos_api import PosError, assert_module_enabled, ok
from core.workspace_context import default_workspace_id, read_workspace_id
from services.authz.deps import check_request_scope, require_perm_pos
from services.tax import aggregate, efiling, filings
from services.tax import anomalies as tax_anomalies
from services.tax import settings as tax_settings

router = APIRouter(prefix="/api/tax", tags=["tax"])

_LANGS = ("th", "zh", "en", "ja")


class GenerateIn(BaseModel):
    period: str


class FileIn(BaseModel):
    method: str  # etax | manual


class MarkFiledIn(BaseModel):
    receipt_no: Optional[str] = None


class SettingsIn(BaseModel):
    vat_registered: Optional[bool] = None
    branch_type: Optional[str] = None
    branch_no: Optional[str] = None
    remind_days_before: Optional[int] = None
    file_zero: Optional[bool] = None


def _auth(request: Request, code: str) -> tuple[dict, str]:
    user = require_perm_pos(request, code, err="tax.forbidden")
    tid = user.get("tenant_id")
    if not tid:
        raise PosError("tax.forbidden", 403)
    return user, str(tid)


def _resolve_ws(cur, request: Request, tenant_id: str, override: Optional[int]) -> int:
    """套账解析(同 accounting_common 范式 · tax.* 错误码命名空间)。"""
    ws = override if override is not None else read_workspace_id(request)
    if ws is not None:
        cur.execute(
            "SELECT 1 FROM workspace_clients WHERE id = %s AND tenant_id = %s",
            (int(ws), tenant_id),
        )
        if not cur.fetchone():
            raise PosError("tax.forbidden", 403)
        check_request_scope(request, int(ws), pos=True)
        return int(ws)
    ws = default_workspace_id(cur, tenant_id)
    if ws is None:
        raise PosError("workspace.required", 400)
    check_request_scope(request, ws, pos=True)
    return ws


def _gate(cur, tenant_id: str) -> None:
    assert_module_enabled(cur, tenant_id, "accounting")


def _uid(user: dict) -> Optional[str]:
    return str(user["id"]) if user and user.get("id") else None


def _prev_period() -> str:
    """报税中心默认期 = 上个月(本月要报的是上期的税)。"""
    today = date.today()
    year, month = (today.year - 1, 12) if today.month == 1 else (today.year, today.month - 1)
    return f"{year:04d}-{month:02d}"


def _taxpayer(cur, tenant_id: str, ws: int) -> dict:
    """导出文件的纳税人块 = 本套账主体资料 + 报税设置的总分公司。"""
    from services.sales import seller_profile

    seller = seller_profile.get_seller(cur, tenant_id=tenant_id, workspace_client_id=ws) or {}
    settings = tax_settings.get_settings(cur, tenant_id=tenant_id, workspace_client_id=ws)
    return {
        "name": seller.get("name"),
        "tax_id": seller.get("tax_id"),
        "branch_type": settings.get("branch_type"),
        "branch_no": settings.get("branch_no"),
    }


@router.get("/filings")
async def api_list_filings(
    request: Request,
    period: Optional[str] = Query(None),
    workspace_client_id: Optional[int] = Query(None),
):
    _, tid = _auth(request, "tax.filing.view")
    with db.get_cursor_rls(tid, commit=False) as cur:
        _gate(cur, tid)
        ws = _resolve_ws(cur, request, tid, workspace_client_id)
        cur_period = aggregate.validate_period(period or _prev_period())
        return ok(
            filings.list_filings(cur, tenant_id=tid, workspace_client_id=ws, period=cur_period)
        )


@router.post("/filings/generate")
async def api_generate_filings(
    req: GenerateIn, request: Request, workspace_client_id: Optional[int] = Query(None)
):
    """手动生成/重算本期全部草稿(close-period 挂点之外的入口)。"""
    _, tid = _auth(request, "tax.filing.create")
    with db.get_cursor_rls(tid, commit=True) as cur:
        _gate(cur, tid)
        ws = _resolve_ws(cur, request, tid, workspace_client_id)
        period = aggregate.validate_period(req.period)
        items = filings.generate_filings(cur, tenant_id=tid, workspace_client_id=ws, period=period)
        return ok({"items": items})


@router.get("/filings/{filing_id}")
async def api_get_filing(
    filing_id: str, request: Request, workspace_client_id: Optional[int] = Query(None)
):
    _, tid = _auth(request, "tax.filing.view")
    with db.get_cursor_rls(tid, commit=False) as cur:
        _gate(cur, tid)
        ws = _resolve_ws(cur, request, tid, workspace_client_id)
        filing = filings.require_filing(
            cur, tenant_id=tid, workspace_client_id=ws, filing_id=filing_id
        )
        return ok({"filing": filing})


@router.post("/filings/{filing_id}/recompute")
async def api_recompute_filing(
    filing_id: str, request: Request, workspace_client_id: Optional[int] = Query(None)
):
    _, tid = _auth(request, "tax.filing.create")
    with db.get_cursor_rls(tid, commit=True) as cur:
        _gate(cur, tid)
        ws = _resolve_ws(cur, request, tid, workspace_client_id)
        filing = filings.recompute(cur, tenant_id=tid, workspace_client_id=ws, filing_id=filing_id)
        return ok({"filing": filing})


@router.post("/filings/{filing_id}/check")
async def api_check_filing(
    filing_id: str, request: Request, workspace_client_id: Optional[int] = Query(None)
):
    """报前体检(按当下数据·不动库)。hard 异常在前端拦提交按钮。"""
    _, tid = _auth(request, "tax.filing.view")
    with db.get_cursor_rls(tid, commit=False) as cur:
        _gate(cur, tid)
        ws = _resolve_ws(cur, request, tid, workspace_client_id)
        filing = filings.require_filing(
            cur, tenant_id=tid, workspace_client_id=ws, filing_id=filing_id
        )
        checked = filings.fresh_anomalies(cur, tenant_id=tid, workspace_client_id=ws, filing=filing)
        return ok({"anomalies": checked, "fileable": not tax_anomalies.has_hard(checked)})


@router.post("/filings/{filing_id}/file")
async def api_file_filing(
    filing_id: str,
    req: FileIn,
    request: Request,
    workspace_client_id: Optional[int] = Query(None),
):
    """提交(不可逆·前端二次确认后调)。etax=直报(未接通诚实失败);manual=置已报+返导出包。"""
    user, tid = _auth(request, "tax.filing.approve")
    if req.method not in ("etax", "manual"):
        raise PosError("tax.unexpected", 422, detail="bad_method")
    with db.get_cursor_rls(tid, commit=True) as cur:
        _gate(cur, tid)
        ws = _resolve_ws(cur, request, tid, workspace_client_id)
        if req.method == "etax":
            filing = filings.require_filing(
                cur, tenant_id=tid, workspace_client_id=ws, filing_id=filing_id
            )
            filings.assert_fileable(cur, tenant_id=tid, workspace_client_id=ws, filing=filing)
            settings = tax_settings.get_settings(cur, tenant_id=tid, workspace_client_id=ws)
            efiling.submit_etax(filing, settings)  # 未接通 → tax.efiling_failed
        filing = filings.mark_filed(
            cur,
            tenant_id=tid,
            workspace_client_id=ws,
            filing_id=filing_id,
            method="manual_export",
            filed_by=_uid(user),
        )
        export_url = f"/api/tax/filings/{filing_id}/export?fmt=zip"
        return ok({"filing": filing, "export_url": export_url})


@router.post("/filings/{filing_id}/mark-filed")
async def api_mark_filed(
    filing_id: str,
    req: MarkFiledIn,
    request: Request,
    workspace_client_id: Optional[int] = Query(None),
):
    """手报完回填回执号(已 filed 只补回执;未 filed 走完整安全带置 filed)。"""
    user, tid = _auth(request, "tax.filing.approve")
    with db.get_cursor_rls(tid, commit=True) as cur:
        _gate(cur, tid)
        ws = _resolve_ws(cur, request, tid, workspace_client_id)
        filing = filings.require_filing(
            cur, tenant_id=tid, workspace_client_id=ws, filing_id=filing_id
        )
        if filing["status"] == "filed":
            if req.receipt_no:
                cur.execute(
                    "UPDATE tax_filings SET receipt_no = %s, updated_at = now() "
                    "WHERE tenant_id = %s AND workspace_client_id = %s AND id = %s",
                    (req.receipt_no, tid, ws, filing_id),
                )
                filing = filings.require_filing(
                    cur, tenant_id=tid, workspace_client_id=ws, filing_id=filing_id
                )
        else:
            filing = filings.mark_filed(
                cur,
                tenant_id=tid,
                workspace_client_id=ws,
                filing_id=filing_id,
                method="manual_export",
                receipt_no=req.receipt_no,
                filed_by=_uid(user),
            )
        return ok({"filing": filing})


@router.get("/filings/{filing_id}/export")
async def api_export_filing(
    filing_id: str,
    request: Request,
    fmt: str = Query("pdf"),
    lang: Optional[str] = Query(None),
    workspace_client_id: Optional[int] = Query(None),
):
    _, tid = _auth(request, "tax.filing.view")
    if fmt not in efiling.EXPORT_FORMATS:
        raise PosError("tax.unexpected", 422, detail="bad_fmt")
    lang = lang if lang in _LANGS else "th"
    with db.get_cursor_rls(tid, commit=False) as cur:
        _gate(cur, tid)
        ws = _resolve_ws(cur, request, tid, workspace_client_id)
        filing = filings.require_filing(
            cur, tenant_id=tid, workspace_client_id=ws, filing_id=filing_id
        )
        taxpayer = _taxpayer(cur, tid, ws)
    name = f"{filing['kind']}_{filing['period']}"
    if fmt == "pdf":
        content, media, ext = efiling.export_pdf(filing, lang=lang), "application/pdf", "pdf"
    elif fmt == "xml":
        content, media, ext = (
            efiling.export_xml(filing, taxpayer=taxpayer),
            "application/xml",
            "xml",
        )
    else:
        content, media, ext = (
            efiling.export_bundle(filing, lang=lang, taxpayer=taxpayer),
            "application/zip",
            "zip",
        )
    return Response(
        content=content,
        media_type=media,
        headers={"Content-Disposition": f'attachment; filename="{name}.{ext}"'},
    )


@router.post("/wht-certs/{line_id}/issue")
async def api_issue_wht_cert(
    line_id: str, request: Request, workspace_client_id: Optional[int] = Query(None)
):
    """补开/关联扣缴凭证:凭证本体复用进项生成链路(render_wht_cert 按需渲染)。"""
    _, tid = _auth(request, "tax.filing.create")
    with db.get_cursor_rls(tid, commit=True) as cur:
        _gate(cur, tid)
        ws = _resolve_ws(cur, request, tid, workspace_client_id)
        doc_id = filings.require_line_source(
            cur, tenant_id=tid, workspace_client_id=ws, line_id=line_id
        )
        from services.purchase import documents as purchase_documents

        att = purchase_documents.record_generated(
            cur, tenant_id=tid, workspace_client_id=ws, doc_id=doc_id, kind="wht_cert"
        )
        line = filings.set_line_cert(
            cur, tenant_id=tid, workspace_client_id=ws, line_id=line_id, cert_url=att["url"]
        )
        return ok({"line": line})


@router.get("/settings")
async def api_get_settings(request: Request, workspace_client_id: Optional[int] = Query(None)):
    _, tid = _auth(request, "tax.filing.view")
    with db.get_cursor_rls(tid, commit=False) as cur:
        _gate(cur, tid)
        ws = _resolve_ws(cur, request, tid, workspace_client_id)
        return ok(
            {"settings": tax_settings.get_settings(cur, tenant_id=tid, workspace_client_id=ws)}
        )


@router.put("/settings")
async def api_update_settings(
    req: SettingsIn, request: Request, workspace_client_id: Optional[int] = Query(None)
):
    _, tid = _auth(request, "tax.settings.manage")
    with db.get_cursor_rls(tid, commit=True) as cur:
        _gate(cur, tid)
        ws = _resolve_ws(cur, request, tid, workspace_client_id)
        settings = tax_settings.update_settings(
            cur, tenant_id=tid, workspace_client_id=ws, data=req.model_dump(exclude_unset=True)
        )
        return ok({"settings": settings})
