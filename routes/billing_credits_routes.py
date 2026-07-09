# -*- coding: utf-8 -*-
"""Pearnly · Billing 路由 · 余额/公司/用量(只读展示)(REFACTOR-WA-B1 · R21 从 billing_routes 拆 · 0 逻辑改)
GET /api/me/credits · /api/my-companies · POST /api/switch-company · GET /api/credits/usage-history · /api/credits/usage-report。
billing_routes 顶部 include_router 聚合 · app.py 单一 include 不变。计费计算逻辑在 services/billing/* · 本模块仅 HTTP handler。
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException, Request, Response
from pydantic import BaseModel, Field

from core import db
from core.auth import get_current_user_from_request
from services.authz.deps import is_owner_role

logger = logging.getLogger("mr-pilot")

router = APIRouter()


# ============================================================
# GET /api/me/credits · 账户余额和用量(老板 vs 员工视角)
# ============================================================
@router.get("/api/me/credits")
async def get_my_credits(request: Request, response: Response):
    """查询账户余额和用量（区分老板/员工视角）"""
    import datetime as _dt

    # 2026-05-24 · 余额是实时数据 · 禁止浏览器缓存
    # (此前缺这头 → 充值审核通过后前端轮询/刷新仍读到旧余额 0 · 用户以为没到账)
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"

    user = get_current_user_from_request(request)
    user_id = str(user.get("id", ""))
    tenant_id = user.get("tenant_id")
    is_exempt = bool(user.get("is_billing_exempt", False))
    # 老板视角看全租户余额;员工只看自己用量(批5:owner 判定读 membership)
    is_owner = is_owner_role(request, user)

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
            with db.get_cursor_rls(tenant_id=tid) as cur:
                cur.execute("SELECT balance_thb FROM tenant_credits WHERE tenant_id = %s", (tid,))
                row = cur.fetchone()
                if row:
                    # 2026-05-24 真因修复:get_cursor() 是 RealDictCursor · row[0] 抛 KeyError
                    # → 被下方 except 吞掉 → 余额永远停在默认 0 → 所有老板读自己余额都是 0
                    # (后台/my-companies 用 row["..."] 故正确显示 · 唯独这里读错)
                    balance_thb = float(row["balance_thb"])
                # 本月用量 = 按量表 + 活跃订阅本周期用量(两计数器互斥不重复计 · 见
                # services/billing/subscription.py active_sub_usage_join_sql)
                cur.execute(
                    f"""
                    SELECT
                        COALESCE(mpu.pages_used, 0) AS pages_used,
                        COALESCE(ts.pages_used_this_cycle, 0) AS sub_pages_used
                    FROM (SELECT 1) AS dummy
                    LEFT JOIN monthly_page_usage mpu
                           ON mpu.tenant_id = %s AND mpu.year_month = %s
                    {db.active_sub_usage_join_sql("ts", "%s")}
                    """,
                    (tid, year_month, tid),
                )
                row = cur.fetchone()
                if row:
                    pages_this_month = int(row["pages_used"]) + int(row.get("sub_pages_used") or 0)
        except Exception as e:
            logger.warning(f"get_my_credits owner DB: {e}")

        # 按用户拆分本月识别量（从 ocr_history 统计）
        user_breakdown = []
        try:
            with db.get_cursor_rls(tenant_id=tid) as cur:
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
            with db.get_cursor_rls(tenant_id=tid, user_id=user_id) as cur:
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
                    my_count = int(row["cnt"])  # RealDictCursor · 同 row[0] bug · 用列名
        except Exception as e:
            logger.warning(f"get_my_credits employee count: {e}")

        return {
            "has_tenant": True,
            "is_owner": False,
            "my_invoice_count": my_count,
        }


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
    is_owner = is_owner_role(request, user)
    if not is_owner:
        user_id = str(user["id"])
    per_page = min(50, max(1, per_page))
    offset = (max(1, page) - 1) * per_page
    uid_sql = "AND ct.user_id = %s::uuid" if user_id else ""
    uid_params = [user_id] if user_id else []
    try:
        with db.get_cursor_rls(tenant_id=tid, user_id=user_id or None) as cur:
            cur.execute(
                f"""
                SELECT COUNT(*) AS n FROM credit_transactions ct
                WHERE ct.tenant_id = %s::uuid AND ct.type IN ('usage','subscription') {uid_sql}
            """,
                [tid] + uid_params,
            )
            total = int(cur.fetchone()["n"])
            cur.execute(
                f"""
                SELECT
                    ct.created_at, ct.pages, ct.amount_thb AS cost_thb, ct.balance_after,
                    ct.type, ct.description,
                    u.email AS user_email, u.username AS user_name,
                    oh.filename
                FROM credit_transactions ct
                LEFT JOIN users u ON u.id = ct.user_id::uuid
                LEFT JOIN ocr_history oh
                    ON oh.user_id = ct.user_id::uuid
                    AND ct.description LIKE '%% · ' || LEFT(oh.id::text, 8)
                    -- 2026-05-24 去掉 oh.tenant_id=ct.tenant_id:ocr_history.tenant_id 现为 NULL
                    -- (insert_ocr_history 未存)· user_id + 描述里 history_id 前8位已唯一
                WHERE ct.tenant_id = %s::uuid AND ct.type IN ('usage','subscription') {uid_sql}
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
                "type": r["type"],
                "description": r["description"] or "",
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
    from services.usage import usage_report as _ur

    user = get_current_user_from_request(request)
    tid = str(user.get("tenant_id") or "")
    if not tid:
        raise HTTPException(status_code=400, detail="no_tenant")

    is_owner = is_owner_role(request, user)
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
        with db.get_cursor_rls(tenant_id=tid, user_id=user_id or None) as cur:
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
                    AND ct.description LIKE '%% · ' || LEFT(oh.id::text, 8)
                    -- 2026-05-24 去掉 oh.tenant_id=ct.tenant_id:ocr_history.tenant_id 现为 NULL
                    -- (insert_ocr_history 未存)· user_id + 描述里 history_id 前8位已唯一
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
        raise HTTPException(status_code=500, detail="build_failed")
