# -*- coding: utf-8 -*-
"""
Pearnly · Billing 路由模块(EXECUTION_PLAN 阶段 5 Task 5.1 · 2026-05-22 抽出)

从 app.py L9449-10053 整片搬过来 · 纯搬家 · 不改业务逻辑 / URL / response shape。

覆盖 12 个 API:
  个人 billing(9):
    GET    /api/me/credits                          · 账户余额 + 用量(老板 vs 员工视角)
    GET    /api/my-companies                         · 当前用户隶属所有公司列表
    POST   /api/switch-company                       · 切换活动公司
    POST   /api/credits/topup/request                · 提交充值申请
    POST   /api/credits/topup/upload-slip/{rid}      · 上传转账截图(SlipOK 自动验证)
    GET    /api/credits/topup/history                · 当前公司充值申请历史
    GET    /api/credits/usage-history                · 当前公司使用流水(分页)
    GET    /api/credits/usage-report                 · 导出使用明细 PDF/XLSX

  Admin billing(3):
    GET    /api/admin/credits/topup/requests         · 超管查充值申请列表
    POST   /api/admin/credits/topup/approve/{rid}    · 超管批准充值
    POST   /api/admin/credits/topup/reject/{rid}     · 超管拒绝充值

未搬(等 Task 5.2 抽 admin 模块时一并处理):
  /api/admin/credits/{overview,tenants,daily_trend,export}(夹在 admin_monitoring 中间 · 不连续)
"""

from __future__ import annotations

import logging
import os

from fastapi import (
    APIRouter,
    File,
    HTTPException,
    Request,
    Response,
    UploadFile,
)
from pydantic import BaseModel, Field

import db
from auth import get_current_user_from_request
from route_helpers import _require_super_admin  # REFACTOR-B1 · 公共守门(2026-05-24)

logger = logging.getLogger("mr-pilot")
router = APIRouter()


def send_topup_approved_email(tenant_id, amount_thb, new_balance):
    """v118.35.0.6 · 占位 noop · v36 真接邮件再实现."""
    logger.info(
        f"[email-stub] topup_approved tenant={str(tenant_id)[:8]} amt={amount_thb} bal={new_balance}"
    )


# ============================================================
# GET /api/me/credits · 账户余额和用量(老板 vs 员工视角)
# ============================================================
@router.get("/api/me/credits")
async def get_my_credits(request: Request):
    """查询账户余额和用量（区分老板/员工视角）"""
    import datetime as _dt

    user = get_current_user_from_request(request)
    user_id = str(user.get("id", ""))
    tenant_id = user.get("tenant_id")
    is_exempt = bool(user.get("is_billing_exempt", False))
    # 老板 = 自己注册（invited_by IS NULL）；员工 = 被老板邀请创建
    is_owner = user.get("invited_by") is None

    if not tenant_id:
        return {"has_tenant": False, "is_owner": is_owner}

    tid = str(tenant_id)
    # Task 6A · Asia/Bangkok 时区(UTC+7)· 与 deduct_company_credits 锚点一致
    _bkk = _dt.timezone(_dt.timedelta(hours=7))
    year_month = _dt.datetime.now(_bkk).strftime("%Y-%m")

    if is_owner:
        balance_thb = 0.0
        pages_this_month = 0
        try:
            with db.get_cursor() as cur:
                cur.execute("SELECT balance_thb FROM tenant_credits WHERE tenant_id = %s", (tid,))
                row = cur.fetchone()
                if row:
                    balance_thb = float(row[0])
                cur.execute(
                    "SELECT pages_used FROM monthly_page_usage WHERE tenant_id = %s AND year_month = %s",
                    (tid, year_month),
                )
                row = cur.fetchone()
                if row:
                    pages_this_month = int(row[0])
        except Exception as e:
            logger.warning(f"get_my_credits owner DB: {e}")

        # 按用户拆分本月识别量（从 ocr_history 统计）
        user_breakdown = []
        try:
            with db.get_cursor() as cur:
                cur.execute(
                    """
                    SELECT h.user_id::text,
                           COALESCE(u.username, split_part(u.email, '@', 1)) AS name,
                           COUNT(*) AS invoice_count
                    FROM ocr_history h
                    LEFT JOIN users u ON u.id::text = h.user_id::text
                    WHERE h.user_id::text IN (
                        SELECT id::text FROM users WHERE tenant_id = %s
                    )
                      AND DATE_TRUNC('month', h.created_at) = DATE_TRUNC('month', CURRENT_DATE)
                    GROUP BY h.user_id, u.username, u.email
                    ORDER BY invoice_count DESC
                    LIMIT 10
                """,
                    (tid,),
                )
                rows = cur.fetchall()
                user_breakdown = [
                    {"name": r["name"], "count": int(r["invoice_count"])} for r in rows
                ]
        except Exception as e:
            logger.warning(f"get_my_credits breakdown: {e}")

        return {
            "has_tenant": True,
            "is_owner": True,
            "is_billing_exempt": is_exempt,
            "balance_thb": balance_thb,
            "pages_this_month": pages_this_month,
            "tier_threshold": 200,
            "current_rate": 0.75 if pages_this_month >= 200 else 1.5,
            "user_breakdown": user_breakdown,
        }
    else:
        # 员工：只返回自己本月发票数，不暴露任何余额/金额信息
        my_count = 0
        try:
            with db.get_cursor() as cur:
                cur.execute(
                    """
                    SELECT COUNT(*) AS cnt
                    FROM ocr_history
                    WHERE user_id::text = %s
                      AND DATE_TRUNC('month', created_at) = DATE_TRUNC('month', CURRENT_DATE)
                """,
                    (user_id,),
                )
                row = cur.fetchone()
                if row:
                    my_count = int(row[0])
        except Exception as e:
            logger.warning(f"get_my_credits employee count: {e}")

        return {
            "has_tenant": True,
            "is_owner": False,
            "my_invoice_count": my_count,
        }


# ============================================================
# 充值申请 · 用户端 + 管理端
# ============================================================


async def _verify_slip_with_slipok(slip_abs_path: str, expected_amount_thb: float) -> dict:
    """验证泰国转账截图. ok=None → 未配置key, 走人工审核; ok=False → 验证未通过; ok=True → 自动approve."""
    import httpx as _httpx

    api_key = os.environ.get("SLIPOK_API_KEY", "")
    branch_id = os.environ.get("SLIPOK_BRANCH_ID", "")
    if not api_key or not branch_id:
        return {"ok": None, "error": "SLIPOK_API_KEY/SLIPOK_BRANCH_ID not configured"}
    try:
        fname = os.path.basename(slip_abs_path)
        mime = (
            "image/png"
            if fname.endswith(".png")
            else "application/pdf" if fname.endswith(".pdf") else "image/jpeg"
        )
        with open(slip_abs_path, "rb") as f:
            file_data = f.read()
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


# ============================================================
# Multi-company (Task 3 · 不动 JWT · 用 users.active_tenant_id)
# ============================================================


class _SwitchCompanyBody(BaseModel):
    tenant_id: str = Field(..., min_length=8)


@router.get("/api/my-companies")
async def my_companies(request: Request):
    """返回当前用户隶属的所有公司列表 · 含 balance(仅 admin 角色可见) + 月用量"""
    user = get_current_user_from_request(request)
    user_id = str(user.get("id", ""))
    if not user_id:
        raise HTTPException(401, detail="auth.required")

    items = db.list_user_companies(user_id)

    # 取 active_tenant_id(若未设置则降级到 tenant_id)
    active_tid = None
    try:
        with db.get_cursor() as cur:
            cur.execute(
                "SELECT active_tenant_id, tenant_id FROM users WHERE id = %s::uuid", (user_id,)
            )
            row = cur.fetchone()
            if row:
                active_tid = str(row.get("active_tenant_id") or row.get("tenant_id") or "")
    except Exception as _e:
        logger.warning(f"my_companies active_tid lookup failed: {_e}")

    # admin 才看 balance · member 屏蔽 balance 字段(置 None)
    out = []
    for it in items:
        is_admin = it.get("role") == "admin"
        out.append(
            {
                "tenant_id": it["tenant_id"],
                "name": it["name"],
                "role": it["role"],
                "balance_thb": (it["balance_thb"] if is_admin else None),
                "pages_this_month": it["pages_this_month"],
                "is_active_tenant": (it["tenant_id"] == active_tid),
            }
        )
    return {"companies": out, "active_tenant_id": active_tid}


@router.post("/api/switch-company")
async def switch_company(body: _SwitchCompanyBody, request: Request):
    """切换当前活动公司 · 校验归属后更新 users.active_tenant_id"""
    user = get_current_user_from_request(request)
    user_id = str(user.get("id", ""))
    if not user_id:
        raise HTTPException(401, detail="auth.required")
    ok = db.set_user_active_tenant(user_id, body.tenant_id)
    if not ok:
        raise HTTPException(403, detail="company.not_member")
    return {"ok": True, "active_tenant_id": body.tenant_id}


@router.post("/api/credits/topup/request")
async def credits_topup_request(req: _TopupRequestBody, request: Request):
    user = get_current_user_from_request(request)
    if user.get("invited_by") is not None:
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
    slips_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static", "slips")
    os.makedirs(slips_dir, exist_ok=True)
    fname = (file.filename or "slip.jpg").lower()
    ext = ".png" if fname.endswith(".png") else ".pdf" if fname.endswith(".pdf") else ".jpg"
    slip_filename = f"{request_id}{ext}"
    slip_abs = os.path.join(slips_dir, slip_filename)
    with open(slip_abs, "wb") as fp:
        fp.write(content)
    with db.get_cursor(commit=True) as cur:
        cur.execute(
            "UPDATE topup_requests SET slip_path = %s WHERE id = %s",
            (f"slips/{slip_filename}", request_id),
        )
    # ── SlipOK 自动验证 ──────────────────────────────────────────
    slipok = await _verify_slip_with_slipok(slip_abs, expected_amount)
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
                cur.execute(
                    """INSERT INTO tenant_credits (tenant_id, balance_thb) VALUES (%s, %s)
                    ON CONFLICT (tenant_id) DO UPDATE
                    SET balance_thb = tenant_credits.balance_thb + %s, updated_at = NOW()
                    RETURNING balance_thb""",
                    (tid, verified_amount, verified_amount),
                )
                new_balance = float(cur.fetchone()["balance_thb"])
                cur.execute(
                    """INSERT INTO credit_transactions
                    (tenant_id, user_id, type, amount_thb, balance_after, description)
                    VALUES (%s::uuid, %s::uuid, 'topup', %s, %s, %s)""",
                    (
                        tid,
                        uid,
                        verified_amount,
                        new_balance,
                        f"SlipOK自动充值 · #{request_id} · ref={ref}",
                    ),
                )
            logger.info(
                f"[topup] SlipOK auto-approved #{request_id} ฿{verified_amount} tenant={tid[:8]}"
            )
            return {
                "ok": True,
                "auto_approved": True,
                "balance_thb": new_balance,
                "slip_path": f"slips/{slip_filename}",
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


@router.get("/api/credits/usage-history")
async def credits_usage_history(
    request: Request, page: int = 1, per_page: int = 20, user_id: str = None
):
    user = get_current_user_from_request(request)
    tid = str(user.get("tenant_id") or "")
    if not tid:
        return {
            "rows": [],
            "total": 0,
            "page": page,
            "per_page": per_page,
            "is_owner": False,
            "members": [],
        }
    is_owner = user.get("invited_by") is None
    if not is_owner:
        user_id = str(user["id"])
    per_page = min(50, max(1, per_page))
    offset = (max(1, page) - 1) * per_page
    uid_sql = "AND ct.user_id = %s::uuid" if user_id else ""
    uid_params = [user_id] if user_id else []
    try:
        with db.get_cursor() as cur:
            cur.execute(
                f"""
                SELECT COUNT(*) AS n FROM credit_transactions ct
                WHERE ct.tenant_id = %s::uuid AND ct.type = 'usage' {uid_sql}
            """,
                [tid] + uid_params,
            )
            total = int(cur.fetchone()["n"])
            cur.execute(
                f"""
                SELECT
                    ct.created_at, ct.pages, ct.amount_thb AS cost_thb, ct.balance_after,
                    u.email AS user_email, u.username AS user_name,
                    oh.filename
                FROM credit_transactions ct
                LEFT JOIN users u ON u.id = ct.user_id::uuid
                LEFT JOIN ocr_history oh
                    ON oh.user_id = ct.user_id::uuid
                    AND oh.tenant_id = ct.tenant_id::uuid
                    AND ct.description LIKE '%% · ' || LEFT(oh.id::text, 8)
                WHERE ct.tenant_id = %s::uuid AND ct.type = 'usage' {uid_sql}
                ORDER BY ct.created_at DESC
                LIMIT %s OFFSET %s
            """,
                [tid] + uid_params + [per_page, offset],
            )
            rows = cur.fetchall()
    except Exception as e:
        logger.warning(f"credits_usage_history: {e}")
        return {
            "rows": [],
            "total": 0,
            "page": page,
            "per_page": per_page,
            "is_owner": is_owner,
            "members": [],
        }
    members = []
    if is_owner:
        try:
            with db.get_cursor() as cur:
                cur.execute(
                    """
                    SELECT id, email, username FROM users
                    WHERE tenant_id = %s::uuid AND is_active = TRUE ORDER BY email
                """,
                    (tid,),
                )
                members = [
                    {"id": str(r["id"]), "email": r["email"] or "", "username": r["username"] or ""}
                    for r in cur.fetchall()
                ]
        except Exception:
            pass
    return {
        "is_owner": is_owner,
        "rows": [
            {
                "date": r["created_at"].isoformat() if r["created_at"] else None,
                "user_email": r["user_email"] or "",
                "user_name": r["user_name"] or "",
                "filename": r["filename"] or "",
                "pages": int(r["pages"] or 0),
                "cost_thb": float(r["cost_thb"] or 0),
                "balance_after": (
                    float(r["balance_after"]) if r["balance_after"] is not None else None
                ),
            }
            for r in rows
        ],
        "total": total,
        "page": page,
        "per_page": per_page,
        "members": members,
    }


@router.get("/api/credits/usage-report")
async def credits_usage_report(
    request: Request,
    start_date: str = None,
    end_date: str = None,
    format: str = "pdf",
    user_id: str = None,
    lang: str = "zh",
):
    """导出使用明细报告 · PDF/XLSX · 按用户分组."""
    import datetime as _dt
    import usage_report as _ur

    user = get_current_user_from_request(request)
    tid = str(user.get("tenant_id") or "")
    if not tid:
        raise HTTPException(status_code=400, detail="no_tenant")

    is_owner = user.get("invited_by") is None
    if not is_owner:
        user_id = str(user["id"])  # 员工只能导出自己

    today = _dt.date.today()
    try:
        if start_date:
            sd = _dt.date.fromisoformat(start_date)
        else:
            sd = today.replace(day=1)
        if end_date:
            ed = _dt.date.fromisoformat(end_date)
        else:
            ed = today
    except Exception:
        raise HTTPException(status_code=400, detail="invalid_date")

    if ed < sd:
        raise HTTPException(status_code=400, detail="end_before_start")

    fmt = (format or "pdf").lower()
    if fmt not in ("pdf", "xlsx"):
        raise HTTPException(status_code=400, detail="invalid_format")
    if lang not in ("zh", "en", "th", "ja"):
        lang = "zh"

    ed_exclusive = ed + _dt.timedelta(days=1)

    uid_sql = ""
    uid_params: list = []
    if user_id:
        uid_sql = "AND ct.user_id = %s::uuid"
        uid_params = [user_id]

    rows: list = []
    company = ""
    try:
        with db.get_cursor() as cur:
            cur.execute("SELECT name FROM tenants WHERE id = %s::uuid", (tid,))
            trow = cur.fetchone()
            if trow:
                company = trow.get("name") or ""
            cur.execute(
                f"""
                SELECT
                    ct.user_id::text AS user_id,
                    ct.created_at,
                    ct.pages,
                    ct.amount_thb AS cost_thb,
                    u.email AS user_email,
                    u.username AS user_name,
                    oh.filename
                FROM credit_transactions ct
                LEFT JOIN users u ON u.id = ct.user_id::uuid
                LEFT JOIN ocr_history oh
                    ON oh.user_id = ct.user_id::uuid
                    AND oh.tenant_id = ct.tenant_id::uuid
                    AND ct.description LIKE '%% · ' || LEFT(oh.id::text, 8)
                WHERE ct.tenant_id = %s::uuid
                  AND ct.type = 'usage'
                  AND ct.created_at >= %s
                  AND ct.created_at < %s
                  {uid_sql}
                ORDER BY u.email NULLS LAST, ct.created_at ASC
            """,
                [tid, sd, ed_exclusive] + uid_params,
            )
            for r in cur.fetchall():
                rows.append(
                    {
                        "user_id": r["user_id"],
                        "date": r["created_at"].isoformat() if r["created_at"] else None,
                        "pages": int(r["pages"] or 0),
                        "cost_thb": float(r["cost_thb"] or 0),
                        "user_email": r["user_email"] or "",
                        "user_name": r["user_name"] or "",
                        "filename": r["filename"] or "",
                    }
                )
    except HTTPException:
        raise
    except Exception as e:
        logger.warning(f"credits_usage_report query: {e}")
        raise HTTPException(status_code=500, detail="query_failed")

    safe_tenant = (
        "".join(ch for ch in (company or "tenant") if ch.isalnum() or ch in "-_")[:24] or "tenant"
    )
    fname_stem = f"pearnly_usage_{safe_tenant}_{sd.strftime('%Y%m%d')}_{ed.strftime('%Y%m%d')}"

    try:
        if fmt == "pdf":
            data = _ur.build_pdf(
                lang=lang,
                company=company or "—",
                start_date=sd.isoformat(),
                end_date=ed.isoformat(),
                rows=rows,
            )
            return Response(
                content=data,
                media_type="application/pdf",
                headers={"Content-Disposition": f'attachment; filename="{fname_stem}.pdf"'},
            )
        else:
            data = _ur.build_xlsx(
                lang=lang,
                company=company or "—",
                start_date=sd.isoformat(),
                end_date=ed.isoformat(),
                rows=rows,
            )
            return Response(
                content=data,
                media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                headers={"Content-Disposition": f'attachment; filename="{fname_stem}.xlsx"'},
            )
    except Exception as e:
        logger.error(f"credits_usage_report build {fmt}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"build_failed: {e}")


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
        cur.execute(
            """INSERT INTO tenant_credits (tenant_id, balance_thb) VALUES (%s, %s)
            ON CONFLICT (tenant_id) DO UPDATE
            SET balance_thb = tenant_credits.balance_thb + %s, updated_at = NOW()
            RETURNING balance_thb""",
            (tid, amt, amt),
        )
        new_balance = float(cur.fetchone()["balance_thb"])
        cur.execute(
            """INSERT INTO credit_transactions
            (tenant_id, user_id, type, amount_thb, balance_after, description)
            VALUES (%s, %s, 'topup', %s, %s, %s)""",
            (tid, admin_id, amt, new_balance, f"充值审核通过 · 申请#{request_id}"),
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
