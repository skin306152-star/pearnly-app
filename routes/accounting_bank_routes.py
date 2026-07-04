# -*- coding: utf-8 -*-
"""银行对账接口(docs/accounting/bank-recon-mj/04 §3 · 独立 router 铁律#17)。

鉴权按权限码逐路由守门(复用 acct.entry.view/review/approve + settings.manage,01 审计:不新增码)。
套账 fail-closed(resolve_ws);模块门控 accounting;信封同 POS(acct.* 命名空间)。
解析复用 services/recon(asyncio.to_thread 不阻塞事件循环);存储/匹配走 services/accounting。
"""

from __future__ import annotations

import asyncio
import hashlib
import logging
import uuid
from typing import Optional

from fastapi import APIRouter, File, Query, Request, UploadFile
from pydantic import BaseModel

from core import db
from core.pos_api import PosError, ok
from routes.accounting_common import auth_member, gate, resolve_ws, uid
from services.accounting import bank_candidates, bank_match, bank_recon

router = APIRouter(prefix="/api/accounting/bank", tags=["accounting-bank"])
logger = logging.getLogger(__name__)

_MAX_BYTES = 20 * 1024 * 1024


class BankAccountIn(BaseModel):
    bank_code: str
    account_label: Optional[str] = None
    account_last4: Optional[str] = None
    coa_account_id: Optional[str] = None


class MatchIn(BaseModel):
    voucher_id: Optional[str] = None
    doc_ids: Optional[list[str]] = None
    new_tx: Optional[dict] = None


class HarvestIn(BaseModel):
    line_ids: list[str]


# --------------------------------------------------------------------------- #
# 账户登记
# --------------------------------------------------------------------------- #
@router.get("/accounts")
async def api_bank_accounts(request: Request, workspace_client_id: Optional[int] = Query(None)):
    _, tid = auth_member(request, "acct.entry.view")
    with db.get_cursor_rls(tid, commit=False) as cur:
        gate(cur, tid)
        ws = resolve_ws(cur, request, tid, workspace_client_id)
        return ok(
            {"accounts": bank_recon.list_bank_accounts(cur, tenant_id=tid, workspace_client_id=ws)}
        )


@router.post("/accounts")
async def api_create_bank_account(
    req: BankAccountIn, request: Request, workspace_client_id: Optional[int] = Query(None)
):
    _, tid = auth_member(request, "acct.settings.manage")
    with db.get_cursor_rls(tid, commit=True) as cur:
        gate(cur, tid)
        ws = resolve_ws(cur, request, tid, workspace_client_id)
        account = bank_recon.create_bank_account(
            cur, tenant_id=tid, workspace_client_id=ws, data=req.model_dump(exclude_none=True)
        )
        return ok({"account": account})


# --------------------------------------------------------------------------- #
# 导入(multipart;sha256 查重 → 409;解析复用 recon)
# --------------------------------------------------------------------------- #
async def _parse_statement(
    raw: bytes,
    filename: str,
    tenant_id: Optional[str] = None,
    ocr_policy_ctx: Optional[dict] = None,
):
    """复用 services/recon 解析栈(PDF→pdfplumber/Gemini;表格/图片→统一管道)· 重 CPU 进线程。"""
    from services.ocr.pipeline import IMAGE_EXTENSIONS, PDF_EXTENSIONS, TABLE_EXTENSIONS

    name_l = filename.lower()
    ext = "." + name_l.rsplit(".", 1)[-1] if "." in name_l else ""
    if ext not in (PDF_EXTENSIONS | IMAGE_EXTENSIONS | TABLE_EXTENSIONS):
        raise PosError("acct.unexpected", 422, detail="unsupported_format")
    from services.ocr import controller
    from services.ocr.contracts import OcrRequest

    return await asyncio.to_thread(
        lambda: controller.run(
            OcrRequest(
                task="bank_statement",
                file_bytes=raw,
                filename=filename,
                tenant_id=tenant_id,
                **(ocr_policy_ctx or {}),
                options={"shape": "legacy_parsed_statement"},
            )
        ).data
    )


@router.post("/import")
async def api_bank_import(
    request: Request,
    file: UploadFile = File(...),
    workspace_client_id: Optional[int] = Query(None),
):
    user, tid = auth_member(request, "acct.entry.review")
    raw = await file.read()
    if not raw or len(raw) < 50:
        raise PosError("acct.unexpected", 422, detail="empty_file")
    if len(raw) > _MAX_BYTES:
        raise PosError("acct.unexpected", 413, detail="file_too_large")
    sha256 = hashlib.sha256(raw).hexdigest()

    with db.get_cursor_rls(tid, commit=False) as cur:
        gate(cur, tid)
        ws = resolve_ws(cur, request, tid, workspace_client_id)
        if bank_recon.file_already_imported(
            cur, tenant_id=tid, workspace_client_id=ws, sha256=sha256
        ):
            raise PosError("acct.bank.duplicate_file", 409)
    _ocr_policy_ctx = {}
    try:
        from services.ocr.entrypoints import policy_context_from_billing

        _ocr_policy_ctx = policy_context_from_billing(
            db.get_billing_status_combined(str(user["id"]), tid)
        )
    except Exception as e:  # noqa: BLE001
        logger.warning(f"[acct.bank.ocr_policy] billing lookup skipped: {e}")

    try:
        parsed = await _parse_statement(
            raw,
            file.filename or "statement",
            tenant_id=tid,
            ocr_policy_ctx=_ocr_policy_ctx,
        )
    except PosError:
        raise
    except Exception:
        # 坏文件 → 422 人话不扣费(Pillow/pdf 先例),不 500
        raise PosError("acct.unexpected", 422, detail="parse_failed")
    if not parsed.transactions:
        raise PosError("acct.unexpected", 422, detail="no_transactions")

    txs = [
        {
            "tx_date": t.tx_date,
            "amount": t.amount,
            "direction": t.direction,
            "description": t.description,
            "ref_no": t.ref_no,
        }
        for t in parsed.transactions
    ]
    batch_id = str(uuid.uuid4())
    with db.get_cursor_rls(tid, commit=True) as cur:
        gate(cur, tid)
        ws = resolve_ws(cur, request, tid, workspace_client_id)
        account = _resolve_import_account(cur, tid, ws, parsed)
        result = bank_recon.insert_lines(
            cur,
            tenant_id=tid,
            workspace_client_id=ws,
            bank_account_id=account["id"],
            batch_id=batch_id,
            sha256=sha256,
            transactions=txs,
            closing_balance=parsed.closing_balance,
            closing_date=parsed.period_end,
        )
    db.insert_operation_log(
        tid,
        uid(user),
        (user or {}).get("username"),
        False,
        "bank.import",
        target_type="bank_account",
        target_id=account["id"],
        details={"inserted": result["inserted"], "skipped": result["skipped"], "ws": ws},
    )
    return ok(
        {
            "bank_account_id": account["id"],
            "bank_code": parsed.bank_code,
            "parsed": len(parsed.transactions),
            "inserted": result["inserted"],
            "skipped": result["skipped"],
            "opening_balance": parsed.opening_balance,
            "closing_balance": parsed.closing_balance,
        }
    )


def _resolve_import_account(cur, tid, ws, parsed) -> dict:
    """按 bank_code+last4 找已登记账户;无则自动登记(回落 bank 角色科目)。"""
    for acc in bank_recon.list_bank_accounts(cur, tenant_id=tid, workspace_client_id=ws):
        if acc["bank_code"] == (parsed.bank_code or "").upper() and (
            acc["account_last4"] or None
        ) == (parsed.account_last4 or None):
            return acc
    return bank_recon.create_bank_account(
        cur,
        tenant_id=tid,
        workspace_client_id=ws,
        data={
            "bank_code": parsed.bank_code or "OTHER",
            "account_last4": parsed.account_last4,
            "account_label": parsed.account_last4 and f"****{parsed.account_last4}",
        },
    )


# --------------------------------------------------------------------------- #
# 概览 / 列表
# --------------------------------------------------------------------------- #
@router.get("/summary")
async def api_bank_summary(request: Request, workspace_client_id: Optional[int] = Query(None)):
    _, tid = auth_member(request, "acct.entry.view")
    with db.get_cursor_rls(tid, commit=False) as cur:
        gate(cur, tid)
        ws = resolve_ws(cur, request, tid, workspace_client_id)
        return ok({"summary": bank_recon.summary(cur, tenant_id=tid, workspace_client_id=ws)})


@router.get("/lines")
async def api_bank_lines(
    request: Request,
    account: Optional[str] = Query(None),
    period: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    limit: int = Query(200),
    offset: int = Query(0),
    workspace_client_id: Optional[int] = Query(None),
):
    _, tid = auth_member(request, "acct.entry.view")
    with db.get_cursor_rls(tid, commit=False) as cur:
        gate(cur, tid)
        ws = resolve_ws(cur, request, tid, workspace_client_id)
        items = bank_recon.list_lines(
            cur,
            tenant_id=tid,
            workspace_client_id=ws,
            bank_account_id=account,
            period=period,
            status=status,
            limit=limit,
            offset=offset,
        )
        return ok({"count": len(items), "items": items})


@router.get("/lines/{line_id}/candidates")
async def api_bank_candidates(
    line_id: str, request: Request, workspace_client_id: Optional[int] = Query(None)
):
    _, tid = auth_member(request, "acct.entry.review")
    with db.get_cursor_rls(tid, commit=False) as cur:
        gate(cur, tid)
        ws = resolve_ws(cur, request, tid, workspace_client_id)
        line = bank_recon.get_line(cur, tenant_id=tid, workspace_client_id=ws, line_id=line_id)
        if line is None:
            raise PosError("acct.unexpected", 404, detail="line_not_found")
        cands = bank_candidates.candidates_for_line(
            cur, tenant_id=tid, workspace_client_id=ws, line=line
        )
        return ok({"candidates": cands})


# --------------------------------------------------------------------------- #
# 匹配动作
# --------------------------------------------------------------------------- #
@router.post("/lines/{line_id}/match")
async def api_bank_match(
    line_id: str,
    req: MatchIn,
    request: Request,
    workspace_client_id: Optional[int] = Query(None),
):
    user, tid = auth_member(request, "acct.entry.review")
    with db.get_cursor_rls(tid, commit=True) as cur:
        gate(cur, tid)
        ws = resolve_ws(cur, request, tid, workspace_client_id)
        res = bank_match.match_line(
            cur,
            tenant_id=tid,
            workspace_client_id=ws,
            line_id=line_id,
            body=req.model_dump(exclude_none=True),
            created_by=uid(user),
        )
        return ok(res)


@router.post("/lines/{line_id}/unmatch")
async def api_bank_unmatch(
    line_id: str, request: Request, workspace_client_id: Optional[int] = Query(None)
):
    user, tid = auth_member(request, "acct.entry.approve")
    with db.get_cursor_rls(tid, commit=True) as cur:
        gate(cur, tid)
        ws = resolve_ws(cur, request, tid, workspace_client_id)
        line = bank_match.unmatch_line(
            cur, tenant_id=tid, workspace_client_id=ws, line_id=line_id, created_by=uid(user)
        )
    db.insert_operation_log(
        tid,
        uid(user),
        (user or {}).get("username"),
        False,
        "bank.unmatch",
        target_type="bank_line",
        target_id=line_id,
        details={"ws": ws},
    )
    return ok({"line": line})


@router.post("/lines/{line_id}/exclude")
async def api_bank_exclude(
    line_id: str, request: Request, workspace_client_id: Optional[int] = Query(None)
):
    _, tid = auth_member(request, "acct.entry.review")
    with db.get_cursor_rls(tid, commit=True) as cur:
        gate(cur, tid)
        ws = resolve_ws(cur, request, tid, workspace_client_id)
        line = bank_match.set_excluded(
            cur, tenant_id=tid, workspace_client_id=ws, line_id=line_id, excluded=True
        )
        return ok({"line": line})


@router.post("/lines/{line_id}/restore")
async def api_bank_restore(
    line_id: str, request: Request, workspace_client_id: Optional[int] = Query(None)
):
    _, tid = auth_member(request, "acct.entry.review")
    with db.get_cursor_rls(tid, commit=True) as cur:
        gate(cur, tid)
        ws = resolve_ws(cur, request, tid, workspace_client_id)
        line = bank_match.set_excluded(
            cur, tenant_id=tid, workspace_client_id=ws, line_id=line_id, excluded=False
        )
        return ok({"line": line})


@router.post("/harvest")
async def api_bank_harvest(
    req: HarvestIn, request: Request, workspace_client_id: Optional[int] = Query(None)
):
    user, tid = auth_member(request, "acct.entry.review")
    with db.get_cursor_rls(tid, commit=True) as cur:
        gate(cur, tid)
        ws = resolve_ws(cur, request, tid, workspace_client_id)
        results = bank_match.harvest(
            cur,
            tenant_id=tid,
            workspace_client_id=ws,
            line_ids=req.line_ids,
            created_by=uid(user),
        )
    matched = sum(1 for r in results if r.get("matched"))
    db.insert_operation_log(
        tid,
        uid(user),
        (user or {}).get("username"),
        False,
        "bank.harvest",
        target_type="bank",
        details={"matched": matched, "total": len(results), "ws": ws},
    )
    return ok({"results": results, "matched": matched, "total": len(results)})
