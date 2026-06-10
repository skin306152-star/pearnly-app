# -*- coding: utf-8 -*-
"""
Pearnly · 员工管理路由模块(REFACTOR-B1 · 2026-05-25 抽出)

从 app.py 整片搬过来 · 纯搬家 · 不改业务逻辑 / URL / response shape。

覆盖 7 个 API(老板用「设置 → 团队管理」):
  GET    /api/team/employees                              · 列员工(带已分配客户数)
  GET    /api/team/employees/{employee_id}/assignments   · 拿单个员工的客户分配
  POST   /api/team/employees/{employee_id}/assignments   · 覆盖式设置客户分配(写审计)
  POST   /api/team/employees                             · 加员工(密码强度 + 查重)
  POST   /api/team/employees/{employee_id}/reset-password· 发改密链接(老板拿不到密码)
  DELETE /api/team/employees/{employee_id}               · 删员工
  PATCH  /api/team/employees/{employee_id}/active        · 启用/停用员工

依赖:
  - db.*(员工 CRUD + 客户分配 + 操作日志)
  - authz.require_perm(team.member.* 逐路由)/ _log_op / _check_password_strength(公共 helper)
  - auth.get_client_ip
  - auth_signup.send_reset_link_for_employee(函数内懒 import · 防循环)

注意:/api/admin/employees/{id}/active(超管 410 tombstone)属 admin 组 · 仍留 app.py ·
      它用到的 EmployeeToggleRequest 在本模块定义 · app.py 从这里 import 回去(非循环)。
"""

from __future__ import annotations

import logging
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from core import db
from core.auth import get_client_ip
from core.route_helpers import _check_password_strength, _log_op
from services.authz.deps import require_perm

logger = logging.getLogger("mr-pilot")
router = APIRouter()


class EmployeeAddRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, pattern="^[a-zA-Z0-9_.-]+$")
    password: str = Field(..., min_length=6, max_length=100)
    # v118.11 · 邮箱选填 · 用于员工自助忘记密码
    email: Optional[str] = Field(None, max_length=200)


class EmployeeToggleRequest(BaseModel):
    is_active: bool


# v118.28.1 · 客户分配(老板用)
class EmployeeAssignmentsRequest(BaseModel):
    client_ids: List[int] = []


# 列员工
@router.get("/api/team/employees")
async def team_list_employees(request: Request):
    owner = require_perm(request, "team.member.view")
    employees = db.list_employees(str(owner["tenant_id"]))
    # v118.28.1 · 顺手把每个员工已分配的客户数带上(团队卡片显示用)
    assignments = db.list_assignments_by_employees(str(owner["tenant_id"]))
    return {
        "employees": [
            {
                "id": str(e["id"]),
                "username": e.get("username"),
                "role": e.get("role"),
                "is_active": e.get("is_active"),
                "last_login_at": e["last_login_at"].isoformat() if e.get("last_login_at") else None,
                "created_at": e["created_at"].isoformat() if e.get("created_at") else None,
                "assigned_client_count": len(assignments.get(str(e["id"]), [])),
            }
            for e in employees
        ],
        "total": len(employees),
    }


@router.get("/api/team/employees/{employee_id}/assignments")
async def team_get_employee_assignments(employee_id: str, request: Request):
    """老板拿单个员工的客户分配列表"""
    owner = require_perm(request, "team.member.view")
    tid = str(owner.get("tenant_id") or "")
    if not tid:
        raise HTTPException(400, detail="team.no_tenant")
    # 校验员工属于本租户
    emp = db.find_user_by_id(employee_id)
    if not emp or str(emp.get("tenant_id") or "") != tid:
        raise HTTPException(404, detail="team.employee_not_found")
    all_assignments = db.list_assignments_by_employees(tid)
    return {"client_ids": all_assignments.get(str(employee_id), [])}


@router.post("/api/team/employees/{employee_id}/assignments")
async def team_set_employee_assignments(
    employee_id: str, req: EmployeeAssignmentsRequest, request: Request
):
    """老板覆盖式设置某员工的客户分配 · 写审计日志"""
    owner = require_perm(request, "team.member.scope")
    tid = str(owner.get("tenant_id") or "")
    if not tid:
        raise HTTPException(400, detail="team.no_tenant")
    emp = db.find_user_by_id(employee_id)
    if not emp or str(emp.get("tenant_id") or "") != tid:
        raise HTTPException(404, detail="team.employee_not_found")
    ok = db.set_employee_assignments(
        employee_user_id=str(employee_id),
        client_ids=req.client_ids or [],
        assigned_by=str(owner["id"]),
        tenant_id=tid,
    )
    if not ok:
        raise HTTPException(400, detail="team.assign_failed")
    # 审计日志(对齐 v118.28.6/7/8 模式)
    try:
        db.insert_operation_log(
            tenant_id=tid,
            actor_user_id=str(owner["id"]),
            actor_username=owner.get("username"),
            actor_is_super=bool(owner.get("is_super_admin")),
            action="team.set_client_assignments",
            target_type="user",
            target_id=str(employee_id),
            target_name=emp.get("username"),
            details={"client_ids": list(req.client_ids or [])},
            ip=get_client_ip(request),
            ua=request.headers.get("user-agent", ""),
        )
    except Exception as e:
        logger.warning(f"[team_assign] 写操作日志失败: {e}")
    return {"ok": True, "assigned_count": len(req.client_ids or [])}


# 加员工
@router.post("/api/team/employees")
async def team_add_employee(req: EmployeeAddRequest, request: Request):
    owner = require_perm(request, "team.member.invite")
    # v118.11 · 密码强度校验
    pw_err = _check_password_strength(req.password)
    if pw_err:
        raise HTTPException(400, detail=pw_err)
    # 提前查是否已存在
    existing = db.find_user_by_username(req.username)
    if existing:
        raise HTTPException(409, detail="team.username_exists")
    # v118.11 · 邮箱也要查重(如果填了)
    if req.email:
        try:
            from core import db as _db

            with _db.get_cursor() as cur:
                cur.execute(
                    "SELECT id FROM users WHERE LOWER(email) = LOWER(%s) LIMIT 1", (req.email,)
                )
                if cur.fetchone():
                    raise HTTPException(409, detail="team.email_exists")
        except HTTPException:
            raise
        except Exception as _ex:
            logger.warning(f"email check skip: {_ex}")
    new_id = db.add_employee(
        tenant_id=str(owner["tenant_id"]),
        username=req.username,
        password=req.password,
        invited_by=str(owner["id"]),
    )
    if not new_id:
        raise HTTPException(400, detail="team.create_failed")
    # v118.11 · 员工创建后写入 email(如果提供)
    if req.email:
        try:
            from core import db as _db

            with _db.get_cursor(commit=True) as cur:
                cur.execute(
                    "UPDATE users SET email = %s WHERE id = %s", (req.email.strip().lower(), new_id)
                )
        except Exception as _ex:
            logger.warning(f"set employee email failed: {_ex}")
    _log_op(request, owner, "employee.add", "employee", new_id, req.username, {})
    return {"ok": True, "id": new_id}


# v118.11 · 重置员工密码 · 系统生成强随机临时密码 · 一次性返回给老板
@router.post("/api/team/employees/{employee_id}/reset-password")
async def team_reset_employee_password(employee_id: str, request: Request):
    """v118.28.7 · 老板给员工发改密链接 · 老板永远拿不到密码
    员工没邮箱也没 LINE 关联 → 拒绝 · 提示先补邮箱(对齐大厂)"""
    owner = require_perm(request, "team.member.toggle")
    target = db.find_user_by_id(employee_id)
    if not target:
        raise HTTPException(404, detail="team.employee_not_found")
    if str(target.get("tenant_id") or "") != str(owner["tenant_id"]):
        if not owner.get("is_super_admin"):
            raise HTTPException(403, detail="team.not_in_your_tenant")
    if target.get("role") == "owner" or target.get("is_super_admin"):
        raise HTTPException(400, detail="team.cannot_reset_owner")

    from services.auth.auth_signup import send_reset_link_for_employee

    host = request.headers.get("host", "pearnly.com")
    res = send_reset_link_for_employee(
        user_id=employee_id,
        request_host=host,
        actor_username=owner.get("username"),
    )

    if res.get("error") == "no_channel":
        # 员工既无邮箱也无 LINE 关联 · 拒绝重置 · 让老板先帮员工补邮箱
        _log_op(
            request,
            owner,
            "employee.password_reset_blocked_no_channel",
            "employee",
            employee_id,
            target.get("username"),
            {},
        )
        raise HTTPException(400, detail="team.reset_no_channel")

    if not res.get("ok"):
        _log_op(
            request,
            owner,
            "employee.password_reset_link_failed",
            "employee",
            employee_id,
            target.get("username"),
            {"error": res.get("error")},
        )
        raise HTTPException(500, detail="team.reset_link_send_failed")

    _log_op(
        request,
        owner,
        "employee.password_reset_link_sent",
        "employee",
        employee_id,
        target.get("username"),
        {"channel": res.get("channel")},
    )
    return {
        "ok": True,
        "channel": res.get("channel"),  # line / email
        "message": "reset_link_sent",
    }


# 删员工
@router.delete("/api/team/employees/{employee_id}")
async def team_remove_employee(employee_id: str, request: Request):
    owner = require_perm(request, "team.member.remove")
    # 记下员工 username 再删
    target = db.find_user_by_id(employee_id)
    target_name = target.get("username") if target else None
    ok = db.remove_employee(str(owner["tenant_id"]), employee_id)
    if not ok:
        raise HTTPException(404, detail="team.employee_not_found")
    _log_op(request, owner, "employee.remove", "employee", employee_id, target_name, {})
    return {"ok": True}


# 启用/停用员工
@router.patch("/api/team/employees/{employee_id}/active")
async def team_toggle_employee(employee_id: str, req: EmployeeToggleRequest, request: Request):
    owner = require_perm(request, "team.member.toggle")
    target = db.find_user_by_id(employee_id)
    target_name = target.get("username") if target else None
    ok = db.toggle_employee_active(str(owner["tenant_id"]), employee_id, req.is_active)
    if not ok:
        raise HTTPException(404, detail="team.employee_not_found")
    _log_op(
        request,
        owner,
        "employee.toggle",
        "employee",
        employee_id,
        target_name,
        {"is_active": req.is_active},
    )
    return {"ok": True}
