# -*- coding: utf-8 -*-
"""Pearnly · Billing 路由 · 充值申请/上传凭证/历史 + 超管审核(台账)(REFACTOR-WA-B1 · R21 从 billing_routes 拆 · 0 逻辑改)
POST /api/credits/topup/{request,upload-slip} · GET /api/credits/topup/history · 超管 /api/admin/credits/topup/{requests,approve,reject}。
⚠️ 高敏(钱·台账)· 纯结构挪 handler · 0 逻辑改 · 充值审核走 services/billing。billing_routes 聚合 · app 单一 include 不变。"""

from __future__ import annotations

import logging
import mimetypes
import os

from fastapi import APIRouter, File, HTTPException, Request, UploadFile
from fastapi.responses import Response
from pydantic import BaseModel, Field

from core import db
from core.auth import get_current_user_from_request
from core.route_helpers import _require_super_admin
from services.audit import file_access as audit_file_access
from services.authz.deps import is_owner_role
from services.billing import slip_storage

logger = logging.getLogger("mr-pilot")

router = APIRouter()


def send_topup_approved_email(tenant_id, amount_thb, new_balance):
    """v118.35.0.6 · 占位 noop · v36 真接邮件再实现."""
    logger.info(
        f"[email-stub] topup_approved tenant={str(tenant_id)[:8]} amt={amount_thb} bal={new_balance}"
    )


# ============================================================
# 充值申请 · 用户端 + 管理端
# ============================================================


async def _verify_slip_with_slipok(slip_rel_path: str, expected_amount_thb: float) -> dict:
    """验证泰国转账截图. ok=None → 未配置key, 走人工审核; ok=False → 验证未通过; ok=True → 自动approve.

    slip_rel_path 是落盘相对路径("slips/123.jpg"),经 slip_storage.read_slip 解密读字节
    (落盘已加密,不能再裸 open 读密文喂外呼)。"""
    import httpx as _httpx

    api_key = os.environ.get("SLIPOK_API_KEY", "")
    branch_id = os.environ.get("SLIPOK_BRANCH_ID", "")
    if not api_key or not branch_id:
        return {"ok": None, "error": "SLIPOK_API_KEY/SLIPOK_BRANCH_ID not configured"}
    try:
        fname = os.path.basename(slip_rel_path)
        mime = (
            "image/png"
            if fname.endswith(".png")
            else "application/pdf" if fname.endswith(".pdf") else "image/jpeg"
        )
        file_data = slip_storage.read_slip(slip_rel_path)
        if file_data is None:
            return {"ok": None, "error": "slip file missing after write"}
        async with _httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                f"https://api.slipok.com/api/line/apikey/{branch_id}",
                headers={"x-authorization": api_key},
                files={"files": (fname, file_data, mime)},
                data={"log": "true"},
            )
        if resp.status_code != 200:
            logger.warning(f"SlipOK HTTP {resp.status_code}: {resp.text[:300]}")
            return {"ok": None, "error": f"SlipOK HTTP {resp.status_code}"}
        body = resp.json()
        if not body.get("success"):
            logger.warning(f"SlipOK !success: {body}")
            return {"ok": False, "error": str(body.get("message", "verification failed"))}
        d = body.get("data", {})
        verified_amount = float(d.get("amount", 0))
        sender = (d.get("sender") or {}).get("displayName", "")
        receiver = (d.get("receiver") or {}).get("displayName", "")
        transaction_id = d.get("transRef", "")
        amount_ok = abs(verified_amount - expected_amount_thb) <= 1.0
        logger.info(
            f"SlipOK result: verified={verified_amount} expected={expected_amount_thb} ok={amount_ok} ref={transaction_id}"
        )
        return {
            "ok": amount_ok,
            "verified_amount": verified_amount,
            "sender": sender,
            "receiver": receiver,
            "transaction_id": transaction_id,
            "error": (
                "" if amount_ok else f"amount {verified_amount} ≠ expected {expected_amount_thb}"
            ),
        }
    except Exception as e:
        logger.warning(f"_verify_slip_with_slipok exception: {e}")
        return {"ok": None, "error": str(e)}


class _TopupRequestBody(BaseModel):
    amount_thb: float = Field(..., gt=0, le=500000)
    payer_name: str = Field("", max_length=200)
    note: str = Field("", max_length=500)


class _AdminTopupApproveBody(BaseModel):
    actual_amount_thb: float = Field(..., gt=0)
    note: str = Field("", max_length=500)


class _AdminTopupRejectBody(BaseModel):
    note: str = Field("", max_length=500)


@router.post("/api/credits/topup/request")
async def credits_topup_request(req: _TopupRequestBody, request: Request):
    user = get_current_user_from_request(request)
    if not is_owner_role(request, user):
        raise HTTPException(403, detail="credits.owner_only")
    tenant_id = user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(400, detail="credits.no_tenant")
    with db.get_cursor(commit=True) as cur:
        cur.execute(
            """
            INSERT INTO topup_requests (tenant_id, requested_by, amount_thb, payer_name, note)
            VALUES (%s, %s, %s, %s, %s) RETURNING id
        """,
            (
                str(tenant_id),
                str(user["id"]),
                req.amount_thb,
                req.payer_name.strip(),
                req.note.strip(),
            ),
        )
        request_id = cur.fetchone()["id"]
    return {"request_id": request_id, "status": "pending"}


@router.post("/api/credits/topup/upload-slip/{request_id}")
async def credits_topup_upload_slip(
    request_id: int, request: Request, file: UploadFile = File(...)
):
    user = get_current_user_from_request(request)
    uid = str(user.get("id", ""))
    tid = str(user.get("tenant_id") or "")
    with db.get_cursor() as cur:
        cur.execute(
            "SELECT tenant_id, status, amount_thb FROM topup_requests WHERE id = %s", (request_id,)
        )
        row = cur.fetchone()
    if not row:
        raise HTTPException(404, detail="topup.not_found")
    if str(row["tenant_id"]) != tid:
        raise HTTPException(403, detail="topup.forbidden")
    if row["status"] != "pending":
        raise HTTPException(400, detail="topup.already_reviewed")
    expected_amount = float(row["amount_thb"])
    content = await file.read()
    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(413, detail="topup.file_too_large")
    fname = (file.filename or "slip.jpg").lower()
    ext = ".png" if fname.endswith(".png") else ".pdf" if fname.endswith(".pdf") else ".jpg"
    slip_filename = f"{request_id}{ext}"
    slip_rel = f"slips/{slip_filename}"
    slip_storage.write_slip(slip_rel, content)
    with db.get_cursor(commit=True) as cur:
        cur.execute(
            "UPDATE topup_requests SET slip_path = %s WHERE id = %s",
            (slip_rel, request_id),
        )
    # ── SlipOK 自动验证 ──────────────────────────────────────────
    slipok = await _verify_slip_with_slipok(slip_rel, expected_amount)
    if slipok.get("ok") is True:
        verified_amount = slipok["verified_amount"]
        ref = slipok.get("transaction_id", "")
        try:
            with db.get_cursor(commit=True) as cur:
                cur.execute(
                    """UPDATE topup_requests SET status='approved', reviewed_at=NOW(),
                    review_note=%s, amount_thb=%s WHERE id=%s""",
                    (f"SlipOK auto-approved · ref={ref}", verified_amount, request_id),
                )
                # 余额+台账走 canonical 记账口(不手写 UPDATE 余额 · 铁律 #26)。
                new_balance = float(
                    db.grant_credits(
                        cur,
                        tenant_id=tid,
                        user_id=uid,
                        amount_thb=verified_amount,
                        txn_type="topup",
                        description=f"SlipOK自动充值 · #{request_id} · ref={ref}",
                    )
                )
            logger.info(
                f"[topup] SlipOK auto-approved #{request_id} ฿{verified_amount} tenant={tid[:8]}"
            )
            return {
                "ok": True,
                "auto_approved": True,
                "balance_thb": new_balance,
                "slip_path": slip_rel,
            }
        except Exception as e:
            logger.error(f"SlipOK auto-approve DB error: {e}")
            # Fall through to manual review
    # ── 人工审核 (no key, ok=False, or auto-approve DB error) ────
    return {"ok": True, "auto_approved": False, "slip_path": f"slips/{slip_filename}"}


@router.get("/api/credits/topup/history")
async def credits_topup_history(request: Request):
    user = get_current_user_from_request(request)
    tid = str(user.get("tenant_id") or "")
    if not tid:
        return []
    with db.get_cursor() as cur:
        cur.execute(
            """
            SELECT id, amount_thb, payer_name, note, status, slip_path,
                   review_note, created_at, reviewed_at
            FROM topup_requests WHERE tenant_id = %s
            ORDER BY created_at DESC LIMIT 20
        """,
            (tid,),
        )
        rows = cur.fetchall()
    return [
        {
            "id": r["id"],
            "amount_thb": float(r["amount_thb"]),
            "payer_name": r["payer_name"] or "",
            "note": r["note"] or "",
            "status": r["status"],
            "slip_path": r["slip_path"],
            "review_note": r["review_note"] or "",
            "created_at": r["created_at"].isoformat() if r["created_at"] else None,
            "reviewed_at": r["reviewed_at"].isoformat() if r["reviewed_at"] else None,
        }
        for r in rows
    ]


@router.get("/api/admin/credits/topup/requests")
async def admin_topup_list(request: Request, status: str = "pending"):
    _require_super_admin(request)
    where = "" if status == "all" else "WHERE tr.status = %s"
    params = () if status == "all" else (status,)
    with db.get_cursor() as cur:
        cur.execute(
            f"""
            SELECT tr.id, tr.amount_thb, tr.payer_name, tr.note,
                   tr.status, tr.slip_path, tr.review_note,
                   tr.created_at, tr.reviewed_at,
                   u.username, u.email, t.name AS tenant_name
            FROM topup_requests tr
            LEFT JOIN users u ON u.id = tr.requested_by
            LEFT JOIN tenants t ON t.id = tr.tenant_id
            {where}
            ORDER BY tr.created_at DESC LIMIT 100
        """,
            params,
        )
        rows = cur.fetchall()
    return [
        {
            "id": r["id"],
            "amount_thb": float(r["amount_thb"]),
            "payer_name": r["payer_name"] or "",
            "note": r["note"] or "",
            "status": r["status"],
            "slip_path": r["slip_path"] or "",
            "review_note": r["review_note"] or "",
            "created_at": r["created_at"].isoformat() if r["created_at"] else None,
            "reviewed_at": r["reviewed_at"].isoformat() if r["reviewed_at"] else None,
            "username": r["username"] or "",
            "email": r["email"] or "",
            "tenant_name": r["tenant_name"] or "",
        }
        for r in rows
    ]


@router.post("/api/admin/credits/topup/approve/{request_id}")
async def admin_topup_approve(request_id: int, body: _AdminTopupApproveBody, request: Request):
    _require_super_admin(request)
    admin_user = get_current_user_from_request(request)
    admin_id = str(admin_user["id"])
    with db.get_cursor(commit=True) as cur:
        cur.execute(
            "SELECT tenant_id, status FROM topup_requests WHERE id = %s FOR UPDATE", (request_id,)
        )
        row = cur.fetchone()
        if not row:
            raise HTTPException(404, detail="topup.not_found")
        if row["status"] != "pending":
            raise HTTPException(400, detail="topup.already_reviewed")
        tid = str(row["tenant_id"])
        amt = body.actual_amount_thb
        cur.execute(
            """UPDATE topup_requests SET status='approved', reviewed_by=%s,
            reviewed_at=NOW(), review_note=%s, amount_thb=%s WHERE id=%s""",
            (admin_id, body.note, amt, request_id),
        )
        # 余额+台账走 canonical 记账口(不手写 UPDATE 余额 · 铁律 #26)。
        new_balance = float(
            db.grant_credits(
                cur,
                tenant_id=tid,
                user_id=admin_id,
                amount_thb=amt,
                txn_type="topup",
                description=f"充值审核通过 · 申请#{request_id}",
            )
        )
    # Task 5 · 通知 tenant owner(失败不影响主流程)
    try:
        send_topup_approved_email(tid, amt, new_balance)
    except Exception as _e:
        logger.warning(f"[email] topup_approved trigger skipped: {_e}")
    return {"ok": True, "new_balance": new_balance}


@router.post("/api/admin/credits/topup/reject/{request_id}")
async def admin_topup_reject(request_id: int, body: _AdminTopupRejectBody, request: Request):
    _require_super_admin(request)
    admin_user = get_current_user_from_request(request)
    admin_id = str(admin_user["id"])
    with db.get_cursor(commit=True) as cur:
        cur.execute("SELECT status FROM topup_requests WHERE id = %s", (request_id,))
        row = cur.fetchone()
        if not row:
            raise HTTPException(404, detail="topup.not_found")
        if row["status"] != "pending":
            raise HTTPException(400, detail="topup.already_reviewed")
        cur.execute(
            """UPDATE topup_requests SET status='rejected', reviewed_by=%s,
            reviewed_at=NOW(), review_note=%s WHERE id=%s""",
            (admin_id, body.note, request_id),
        )
    return {"ok": True}


@router.get("/api/admin/credits/topup/slip/{request_id}")
async def admin_topup_slip(request_id: int, request: Request):
    """充值截图取件(超管审核台专用,鉴权对齐同组 admin_topup_list/approve/reject)。

    老 `/static/slips/...` URL 已随 2026-06-03 目录重组 404(且形态无鉴权),本端点是唯一
    在场取件口:落盘经 slip_storage 加密收口,取件经 read_slip 解密,零裸文件暴露。"""
    admin = _require_super_admin(request)
    with db.get_cursor() as cur:
        cur.execute("SELECT tenant_id, slip_path FROM topup_requests WHERE id = %s", (request_id,))
        row = cur.fetchone()
    if not row or not row.get("slip_path"):
        raise HTTPException(404, detail="topup.slip_not_found")
    data = slip_storage.read_slip(row["slip_path"])
    if data is None:
        raise HTTPException(404, detail="topup.slip_not_found")
    media_type = mimetypes.guess_type(row["slip_path"])[0] or "application/octet-stream"
    # tenant_id 记被查看资料所属的客户租户(非超管自身租户——超管本不挂靠任何租户);
    # actor 字段才是这次操作的人(admin)。
    audit_file_access.log_file_access(
        request,
        action=audit_file_access.SLIP_VIEWED,
        tenant_id=str(row["tenant_id"]) if row.get("tenant_id") else None,
        actor_user_id=str(admin["id"]) if admin.get("id") else None,
        actor_username=admin.get("username"),
        actor_is_super=True,
        target_type="topup_request",
        target_id=str(request_id),
        details={"kind": "slip", "ref": row["slip_path"]},
    )
    return Response(content=data, media_type=media_type)
