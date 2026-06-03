# -*- coding: utf-8 -*-
"""超管用户/员工管理 · 只读查询路由(REFACTOR-WA · 从 admin_users_routes.py 按读/写域拆出)

纯搬家 · URL/method/权限/返回结构/错误码/业务逻辑 0 改 · 路由 verbatim(@router 装饰器不动)。
覆盖 6 只读路由:/api/admin/users(列)· /api/admin/employees(列)· /api/admin/users/{id}(详情)·
/api/admin/users/{id}/logs · /api/admin/users.csv · /api/admin/users/{id}/cascade-preview。
admin_users_routes.py 门面经 include_router 聚合本 router(app.include_router 不变)。
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException, Request

from core import db
from core.route_helpers import _require_super_admin

logger = logging.getLogger("mr-pilot")

router = APIRouter()


# 列出所有 owner 用户(超管)
@router.get("/api/admin/users")
async def admin_list_users(request: Request):
    """v118.12 · 仅返回客户(owner / 老数据 role NULL) · 员工走 /api/admin/employees"""
    _require_super_admin(request)
    from core import db as _db

    rows = []
    try:
        with _db.get_cursor() as cur:
            cur.execute("""
                SELECT
                    u.id           AS user_id,
                    u.username,
                    u.email,
                    COALESCE(u.company_name, t.name)   AS company_name,
                    u.tenant_id,
                    t.tenant_type,
                    t.status       AS tenant_status,
                    u.plan         AS plan,
                    t.monthly_quota AS tenant_quota,
                    t.used_this_month AS tenant_used,
                    t.subscription_expires_at,
                    u.is_active,
                    u.signup_country AS country,
                    u.last_login_at,
                    u.created_at,
                    (SELECT COUNT(*) FROM users e WHERE e.tenant_id = u.tenant_id AND e.role = 'member' AND COALESCE(e.is_active, true) = true) AS employees_count
                FROM users u
                LEFT JOIN tenants t ON t.id = u.tenant_id
                WHERE (u.role = 'owner' OR u.role IS NULL)
                  AND COALESCE(u.is_super_admin, false) = false
                ORDER BY u.created_at DESC NULLS LAST
                LIMIT 500
            """)
            db_rows = cur.fetchall()
        for r in db_rows:
            tenant_plan = r.get("plan") or "free"
            rows.append(
                {
                    "user_id": str(r["user_id"]),
                    "id": str(r["user_id"]),  # v118.12.1 · 兼容前端 u.id 字段
                    "username": r.get("username"),
                    "email": r.get("email"),
                    "company_name": r.get("company_name"),
                    "tenant_id": str(r["tenant_id"]) if r.get("tenant_id") else None,
                    "tenant_type": r.get("tenant_type"),
                    "tenant_status": r.get("tenant_status"),
                    "plan": tenant_plan,  # v118.12 · 客户列表用 user.plan(实际套餐字段)
                    "is_active": r.get("is_active"),
                    "country": r.get("country"),
                    "monthly_quota": int(r.get("tenant_quota") or 0),
                    "used_this_month": int(r.get("tenant_used") or 0),
                    "employees_count": int(r.get("employees_count") or 0),
                    "trial_expires_at": (
                        r["subscription_expires_at"].isoformat()
                        if r.get("subscription_expires_at")
                        else None
                    ),
                    "subscription_expires_at": (
                        r["subscription_expires_at"].isoformat()
                        if r.get("subscription_expires_at")
                        else None
                    ),
                    "last_login_at": (
                        r["last_login_at"].isoformat() if r.get("last_login_at") else None
                    ),
                    "created_at": r["created_at"].isoformat() if r.get("created_at") else None,
                }
            )
    except Exception as e:
        logger.error(f"admin_list_users: {e}")
        raise HTTPException(500, detail="admin.list_failed")
    return {"users": rows, "total": len(rows)}


@router.get("/api/admin/employees")
async def admin_list_employees(request: Request):
    """v118.12 · 超管查所有员工(role=member) · 显示属于哪个老板/事务所"""
    _require_super_admin(request)
    from core import db as _db

    rows = []
    try:
        with _db.get_cursor() as cur:
            cur.execute("""
                SELECT
                    e.id           AS employee_id,
                    e.username,
                    e.email,
                    e.tenant_id,
                    e.is_active,
                    e.last_login_at,
                    e.created_at,
                    t.name         AS tenant_name,
                    (SELECT plan FROM users WHERE tenant_id = t.id AND role = 'owner' LIMIT 1) AS tenant_plan,
                    o.id           AS owner_id,
                    o.username     AS owner_username,
                    o.email        AS owner_email
                FROM users e
                LEFT JOIN tenants t ON t.id = e.tenant_id
                LEFT JOIN users o   ON o.tenant_id = e.tenant_id AND o.role = 'owner'
                WHERE e.role = 'member'
                  AND COALESCE(e.is_super_admin, false) = false
                ORDER BY t.name NULLS LAST, e.created_at DESC NULLS LAST
                LIMIT 1000
            """)
            db_rows = cur.fetchall()
        for r in db_rows:
            rows.append(
                {
                    "employee_id": str(r["employee_id"]),
                    "username": r.get("username"),
                    "email": r.get("email"),
                    "tenant_id": str(r["tenant_id"]) if r.get("tenant_id") else None,
                    "tenant_name": r.get("tenant_name"),
                    "tenant_plan": r.get("tenant_plan"),
                    "owner_id": str(r["owner_id"]) if r.get("owner_id") else None,
                    "owner_username": r.get("owner_username"),
                    "owner_email": r.get("owner_email"),
                    "is_active": r.get("is_active"),
                    "last_login_at": (
                        r["last_login_at"].isoformat() if r.get("last_login_at") else None
                    ),
                    "created_at": r["created_at"].isoformat() if r.get("created_at") else None,
                }
            )
    except Exception as e:
        logger.error(f"admin_list_employees: {e}")
        raise HTTPException(500, detail="admin.list_failed")
    return {"employees": rows, "total": len(rows)}


# 用户详情(超管)· v118.12.5 · 平铺字段 + 扩展信息 · 让前端 drawer 能渲染完整
@router.get("/api/admin/users/{user_id}")
async def admin_user_detail(user_id: str, request: Request):
    _require_super_admin(request)
    user = db.find_user_by_id(user_id)
    if not user:
        raise HTTPException(404, detail="admin.user_not_found")
    tenant = db.get_tenant(str(user["tenant_id"])) if user.get("tenant_id") else None
    employees = db.list_employees(str(user["tenant_id"])) if user.get("tenant_id") else []

    # 累计 OCR · 最近识别 · 付款次数
    cumulative_ocr = 0
    last_ocr_at = None
    payment_count = 0
    last_payment_at = None
    try:
        from core import db as _db

        with _db.get_cursor() as cur:
            cur.execute(
                "SELECT COUNT(*) AS n, MAX(created_at) AS last FROM ocr_history WHERE user_id = %s",
                (user_id,),
            )
            r = cur.fetchone()
            if r:
                cumulative_ocr = int(r.get("n") or 0) if isinstance(r, dict) else int(r[0] or 0)
                last_raw = r.get("last") if isinstance(r, dict) else r[1]
                last_ocr_at = last_raw.isoformat() if last_raw else None
            try:
                cur.execute(
                    "SELECT COUNT(*) AS n, MAX(created_at) AS last FROM payment_log WHERE user_id = %s AND status = 'approved'",
                    (user_id,),
                )
                r2 = cur.fetchone()
                if r2:
                    payment_count = (
                        int(r2.get("n") or 0) if isinstance(r2, dict) else int(r2[0] or 0)
                    )
                    last_pay_raw = r2.get("last") if isinstance(r2, dict) else r2[1]
                    last_payment_at = last_pay_raw.isoformat() if last_pay_raw else None
            except Exception:
                pass  # payment_log 表可能不存在 · 静默兜底
    except Exception as _ee:
        logger.warning(f"admin_user_detail aux failed: {_ee}")

    # 2026-05-25 · credits 模式:抽屉显示公司余额/本月扣费/本月页数/累计充值(替代老套餐配额)
    credit = {}
    if user.get("tenant_id"):
        try:
            credit = db.get_tenant_credit_summary(str(user["tenant_id"]))
        except Exception as _ce:
            logger.warning(f"admin_user_detail credit summary failed: {_ce}")

    return {
        # 平铺 user 字段 · 让前端 u.email / u.phone 等直接 work
        "id": str(user["id"]),
        "user_id": str(user["id"]),
        "username": user.get("username"),
        "email": user.get("email"),
        "phone": user.get("phone"),
        "line_id": user.get("line_id"),
        "line_user_id": user.get("line_user_id"),
        "country": user.get("country") or user.get("signup_country"),
        "signup_country": user.get("signup_country"),
        "company_name": user.get("company_name") or (tenant.get("name") if tenant else None),
        "full_name": user.get("full_name"),
        "role": user.get("role"),
        "is_active": user.get("is_active"),
        "is_super_admin": bool(user.get("is_super_admin")),
        "plan": user.get("plan") or "free",
        "monthly_volume": user.get("monthly_volume"),
        "monthly_quota": int(user.get("monthly_quota") or 0),
        "used_this_month": int(user.get("used_this_month") or 0),
        "cumulative_ocr": cumulative_ocr,
        "last_ocr_at": last_ocr_at,
        "payment_count": payment_count,
        "last_payment_at": last_payment_at,
        # credits 汇总(公司级)· 抽屉「余额与计费」段用 · 取不到则为空 {}(前端隐藏该段)
        "credit": credit,
        "trial_expires_at": str(user["trial_expires_at"]) if user.get("trial_expires_at") else None,
        "expires_at": str(user["expires_at"]) if user.get("expires_at") else None,
        "last_login_at": user["last_login_at"].isoformat() if user.get("last_login_at") else None,
        "created_at": user["created_at"].isoformat() if user.get("created_at") else None,
        "signup_ip": user.get("signup_ip") or user.get("registration_ip"),
        "device_fingerprint": user.get("device_fingerprint"),
        "has_risk_signal": bool(user.get("is_suspicious") or user.get("risk_score", 0) > 0),
        # tenant 信息(嵌套)
        "tenant_id": str(user["tenant_id"]) if user.get("tenant_id") else None,
        "tenant": (
            {
                "id": str(tenant["id"]) if tenant else None,
                "name": tenant.get("name") if tenant else None,
                "tenant_type": tenant.get("tenant_type") if tenant else None,
                "status": tenant.get("status") if tenant else None,
                "monthly_quota": int(tenant.get("monthly_quota") or 0) if tenant else 0,
                "used_this_month": int(tenant.get("used_this_month") or 0) if tenant else 0,
                "notes": tenant.get("notes") if tenant else None,
            }
            if tenant
            else None
        ),
        "tenant_name": tenant.get("name") if tenant else None,
        "tenant_type": tenant.get("tenant_type") if tenant else None,
        "tenant_status": tenant.get("status") if tenant else None,
        "tenant_quota": int(tenant.get("monthly_quota") or 0) if tenant else 0,
        "tenant_used": int(tenant.get("used_this_month") or 0) if tenant else 0,
        # 员工列表(老板视角看自己的员工)
        "employees": [
            {
                "id": str(e["id"]),
                "username": e.get("username"),
                "email": e.get("email"),
                "role": e.get("role"),
                "is_active": e.get("is_active"),
                "last_login_at": e["last_login_at"].isoformat() if e.get("last_login_at") else None,
                "created_at": e["created_at"].isoformat() if e.get("created_at") else None,
            }
            for e in employees
        ],
    }


# 查某用户(tenant)的操作日志
@router.get("/api/admin/users/{user_id}/logs")
async def admin_user_logs(user_id: str, request: Request):
    _require_super_admin(request)
    user = db.find_user_by_id(user_id)
    if not user:
        raise HTTPException(404, detail="admin.user_not_found")
    logs = db.list_operation_logs(
        tenant_id=str(user["tenant_id"]) if user.get("tenant_id") else None, limit=200
    )
    return {
        "logs": [
            {
                "id": l["id"],
                "actor_username": l.get("actor_username"),
                "actor_is_super": l.get("actor_is_super"),
                "action": l.get("action"),
                "target_type": l.get("target_type"),
                "target_name": l.get("target_name"),
                "details": l.get("details"),
                "ip": l.get("ip"),
                "created_at": l["created_at"].isoformat() if l.get("created_at") else None,
            }
            for l in logs
        ],
        "total": len(logs),
    }


# v118.29.0 · 客户列表 CSV 导出(超管 · 当前 filter 全部 · 上限 5000)
@router.get("/api/admin/users.csv")
async def admin_users_csv(request: Request):
    _require_super_admin(request)
    from core import db as _db

    rows = []
    try:
        with _db.get_cursor() as cur:
            cur.execute("""
                SELECT
                    u.id           AS user_id,
                    u.username,
                    u.email,
                    COALESCE(u.company_name, t.name)   AS company_name,
                    u.tenant_id,
                    t.tenant_type,
                    t.status       AS tenant_status,
                    u.plan         AS plan,
                    t.monthly_quota AS tenant_quota,
                    t.used_this_month AS tenant_used,
                    t.subscription_expires_at,
                    u.is_active,
                    u.signup_country AS country,
                    u.last_login_at,
                    u.created_at,
                    (SELECT COUNT(*) FROM users e WHERE e.tenant_id = u.tenant_id AND e.role = 'member' AND COALESCE(e.is_active, true) = true) AS employees_count
                FROM users u
                LEFT JOIN tenants t ON t.id = u.tenant_id
                WHERE (u.role = 'owner' OR u.role IS NULL)
                  AND COALESCE(u.is_super_admin, false) = false
                ORDER BY u.created_at DESC NULLS LAST
                LIMIT 5000
            """)
            rows = cur.fetchall()
    except Exception as e:
        logger.error(f"admin_users_csv: {e}")
        raise HTTPException(500, detail="admin.csv_failed")

    import csv as _csv
    from io import StringIO as _StringIO

    buf = _StringIO()
    buf.write("\ufeff")
    w = _csv.writer(buf)
    w.writerow(
        [
            "created_at",
            "username",
            "email",
            "company_name",
            "country",
            "plan",
            "tenant_status",
            "is_active",
            "monthly_quota",
            "used_this_month",
            "employees_count",
            "subscription_expires_at",
            "last_login_at",
            "tenant_id",
        ]
    )
    for r in rows:
        w.writerow(
            [
                r["created_at"].isoformat() if r.get("created_at") else "",
                r.get("username") or "",
                r.get("email") or "",
                r.get("company_name") or "",
                r.get("country") or "",
                r.get("plan") or "free",
                r.get("tenant_status") or "",
                "1" if r.get("is_active") else "0",
                int(r.get("tenant_quota") or 0),
                int(r.get("tenant_used") or 0),
                int(r.get("employees_count") or 0),
                (
                    r["subscription_expires_at"].isoformat()
                    if r.get("subscription_expires_at")
                    else ""
                ),
                r["last_login_at"].isoformat() if r.get("last_login_at") else "",
                str(r["tenant_id"]) if r.get("tenant_id") else "",
            ]
        )
    from fastapi.responses import Response as _Resp

    return _Resp(
        content=buf.getvalue(),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="pearnly_users.csv"'},
    )


@router.get("/api/admin/users/{user_id}/cascade-preview")
async def admin_cascade_preview(user_id: str, request: Request):
    """超管查看删除老板的影响范围(给前端 modal 显示)"""
    _require_super_admin(request)
    info = db.preview_owner_cascade(user_id)
    if not info:
        raise HTTPException(404, detail="admin.user_not_found_or_not_owner")
    return info
