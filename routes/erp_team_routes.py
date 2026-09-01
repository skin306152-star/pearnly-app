"""ERP portal team management endpoints."""

from __future__ import annotations

import os
from typing import Optional

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from core import db
from core.auth import get_current_user_from_request
from core.feature_flags import erp_line_enabled_for, erp_portal_enabled_for
from core.route_helpers import _check_password_strength, _log_op
from core.workspace_context import resolve_active_workspace_id
from services.auth.entrance import require_erp_portal
from services.auth.signup_core import PLAN_CONFIG
from services.authz.deps import is_owner_role
from services.erp import team_access
from services.erp import team_members
from services.line_erp import store as line_store
from services.team.seat_usage import seat_usage

router = APIRouter(prefix="/api/erp/team", tags=["erp-team"])


class MemberCreate(BaseModel):
    account: str = Field(..., min_length=3, max_length=200)
    password: str = Field(..., min_length=6, max_length=100)
    modules: list[str] = Field(..., min_length=1, max_length=3)
    erp_system: Optional[str] = Field(None, pattern="^(mrerp|express)$")
    erp_endpoint_id: Optional[str] = None
    erp_username: Optional[str] = Field(None, max_length=200)
    erp_password: Optional[str] = Field(None, max_length=200)


class MemberUpdate(BaseModel):
    modules: list[str] = Field(..., min_length=1, max_length=3)
    is_active: bool = True


def _workspace(request: Request, tenant_id: str) -> int:
    with db.get_cursor() as cur:
        workspace_id = resolve_active_workspace_id(cur, request, tenant_id=tenant_id)
    if workspace_id is None:
        raise HTTPException(400, detail="workspace.required")
    return int(workspace_id)


def _erp_user(request: Request) -> dict:
    user = get_current_user_from_request(request)
    require_erp_portal(user)
    tenant_id = str(user.get("tenant_id") or "")
    if not user.get("is_super_admin") and not erp_portal_enabled_for(tenant_id, str(user["id"])):
        raise HTTPException(404, detail="erp_team.not_available")
    team_access.require_active_erp_user(user)
    return user


def _owner(request: Request) -> tuple[dict, str, int]:
    user = _erp_user(request)
    if not is_owner_role(request, user):
        raise HTTPException(403, detail="erp_team.owner_required")
    tenant_id = str(user["tenant_id"])
    return user, tenant_id, _workspace(request, tenant_id)


def _line_config() -> dict:
    basic_id = os.getenv("LINE_ERP_BOT_BASIC_ID", "").strip()
    friend_url = os.getenv("LINE_ERP_BOT_FRIEND_URL", "").strip()
    if basic_id and not friend_url:
        friend_url = f"https://line.me/R/ti/p/{basic_id}"
    return {"bot_basic_id": basic_id or None, "bot_friend_url": friend_url or None}


@router.get("/access")
async def erp_team_access(request: Request):
    user = _erp_user(request)
    access = team_access.access_for_user(str(user["tenant_id"]), str(user["id"]))
    return {"ok": True, "data": access}


@router.get("/members")
async def erp_team_members(request: Request):
    user, tenant_id, workspace_id = _owner(request)
    plan = PLAN_CONFIG.get(str(user.get("plan") or ""), PLAN_CONFIG["credits"])
    usage = seat_usage(tenant_id)
    return {
        "ok": True,
        "data": {
            "members": team_access.list_members(tenant_id, workspace_id),
            "seats_used": usage["used"],
            "seats_max": int(plan["seats_max"]),
            "workspace_client_id": workspace_id,
            "quota_scope": "tenant",
            "erp_endpoints": team_access.owner_endpoint_options(
                tenant_id, workspace_id, str(user["id"])
            ),
        },
    }


@router.post("/members")
async def erp_team_member_create(req: MemberCreate, request: Request):
    user, tenant_id, workspace_id = _owner(request)
    password_error = _check_password_strength(req.password)
    if password_error:
        raise HTTPException(400, detail=password_error)
    plan = PLAN_CONFIG.get(str(user.get("plan") or ""), PLAN_CONFIG["credits"])
    if seat_usage(tenant_id)["used"] >= int(plan["seats_max"]):
        raise HTTPException(422, detail="team.seat_limit")
    erp_config = None
    if req.erp_system == "mrerp" and not req.erp_endpoint_id:
        username = (req.erp_username or "").strip()
        password = req.erp_password or ""
        if not username or not password:
            raise HTTPException(422, detail="erp_team.mrerp_credentials_required")
        try:
            from core.kms_helper import encrypt_str

            erp_config = {
                "system_url": "https://www.mrerp4sme.com",
                "username_enc": encrypt_str(username),
                "password_enc": encrypt_str(password),
                "client_ids": [],
            }
        except Exception as exc:
            raise HTTPException(500, detail="erp.encrypt_failed") from exc
    result = team_members.create_member(
        tenant_id=tenant_id,
        workspace_client_id=workspace_id,
        invited_by=str(user["id"]),
        account=req.account.strip(),
        password=req.password,
        modules=req.modules,
        erp_system=req.erp_system,
        erp_config=erp_config,
        erp_endpoint_id=req.erp_endpoint_id,
    )
    if result.get("error"):
        raise HTTPException(422, detail=result["error"])
    _log_op(
        request,
        user,
        "erp_team.member_create",
        "user",
        result["user_id"],
        result["username"],
        {"modules": list(team_access.normalize_modules(req.modules)), "erp_system": req.erp_system},
    )
    line = None
    if erp_line_enabled_for(tenant_id, result["user_id"]):
        line = line_store.new_code(tenant_id, result["user_id"], workspace_id)
        line.update(_line_config())
    return {"ok": True, "data": {**result, "line": line}}


@router.patch("/members/{user_id}")
async def erp_team_member_update(user_id: str, req: MemberUpdate, request: Request):
    user, tenant_id, workspace_id = _owner(request)
    if not team_members.member_exists(tenant_id, workspace_id, user_id):
        raise HTTPException(404, detail="team.member_not_found")
    result = team_members.update_member(
        tenant_id=tenant_id,
        actor_id=str(user["id"]),
        user_id=user_id,
        modules=req.modules,
        is_active=req.is_active,
    )
    if result.get("error"):
        raise HTTPException(422, detail=result["error"])
    _log_op(
        request,
        user,
        "erp_team.member_update",
        "user",
        user_id,
        None,
        {"modules": result["modules"], "is_active": result["is_active"]},
    )
    return {"ok": True, "data": result}


@router.post("/members/{user_id}/line-code")
async def erp_team_member_line_code(user_id: str, request: Request):
    _, tenant_id, workspace_id = _owner(request)
    if not team_members.member_exists(tenant_id, workspace_id, user_id):
        raise HTTPException(404, detail="team.member_not_found")
    if not erp_line_enabled_for(tenant_id, user_id):
        raise HTTPException(403, detail="line_erp.not_invited")
    data = line_store.new_code(tenant_id, user_id, workspace_id)
    data.update(_line_config())
    return {"ok": True, "data": data}


@router.get("/members/{user_id}/line-binding")
async def erp_team_member_line_binding(user_id: str, request: Request):
    _, tenant_id, workspace_id = _owner(request)
    if not team_members.member_exists(tenant_id, workspace_id, user_id):
        raise HTTPException(404, detail="team.member_not_found")
    binding = line_store.get_binding_by_user(user_id)
    if binding and str(binding.get("tenant_id")) != tenant_id:
        binding = None
    return {
        "ok": True,
        "data": {
            "bound": bool(binding),
            "display_name": (binding or {}).get("display_name"),
            "bound_at": (binding or {}).get("bound_at"),
        },
    }


@router.delete("/members/{user_id}/line-binding")
async def erp_team_member_line_unbind(user_id: str, request: Request):
    user, tenant_id, workspace_id = _owner(request)
    if not team_members.member_exists(tenant_id, workspace_id, user_id):
        raise HTTPException(404, detail="team.member_not_found")
    line_store.unbind_by_user(user_id)
    _log_op(request, user, "erp_team.line_unbind", "user", user_id, None, {})
    return {"ok": True, "data": {"bound": False}}
