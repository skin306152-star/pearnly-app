# -*- coding: utf-8 -*-
"""
Pearnly · 用户设置路由模块(智能归档 + 重复发票检测)(REFACTOR-B1 · 2026-05-25 抽出)

从 app.py 整片搬过来 · 纯搬家 · 不改业务逻辑 / URL / response shape。

覆盖 7 个 API:
  GET  /api/archive/settings        · 读归档命名设置(没配过返默认)
  PUT  /api/archive/settings        · 存归档命名设置
  POST /api/archive/rename-preview  · 归档命名实时预览
  GET  /api/settings/dup-check      · 读重复发票检测开关
  PUT  /api/settings/dup-check      · 存重复发票检测开关
  GET  /api/settings/erp-push-mode  · 读 ERP 自动处理方式(P1b)
  PUT  /api/settings/erp-push-mode  · 存 ERP 自动处理方式(P1b)

依赖:
  - db.*(archive settings + dup-check 开关)
  - auth.get_current_user_from_request
  - route_helpers._plan_permissions(_check_archive_* 权限闸)
  - archive 模块(DEFAULT_TEMPLATE / preview_name · 函数内懒 import)
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from core import db
from core.auth import get_current_user_from_request
from core.route_helpers import _plan_permissions

router = APIRouter()


# ─── v0.7 · 智能归档 ──────────────────────────────────────
class ArchiveSettingsPayload(BaseModel):
    name_template: List[Dict[str, Any]] = Field(default_factory=list)
    folder_strategy: str = "by_month_seller"


class ArchivePreviewRequest(BaseModel):
    merged_fields: Dict[str, Any] = Field(default_factory=dict)
    name_template: Optional[List[Dict[str, Any]]] = None


def _check_archive_access(user: dict):
    """所有 plan 都能读归档设置 · 用默认模板"""
    plan = (user or {}).get("plan", "free")
    p = _plan_permissions(plan)
    if not p.get("can_archive"):
        raise HTTPException(403, detail="archive.upgrade_required")


def _check_archive_customize(user: dict):
    """只有 Plus/Pro 能改归档模板"""
    plan = (user or {}).get("plan", "free")
    p = _plan_permissions(plan)
    if not p.get("can_customize_archive"):
        raise HTTPException(403, detail="archive.customize_plus_required")


@router.get("/api/archive/settings")
async def archive_settings_get(request: Request):
    user = get_current_user_from_request(request)
    _check_archive_access(user)
    from services.archive import archive as _archive

    s = db.get_archive_settings(str(user["id"]))
    if not s:
        # 没配过 · 返回默认
        return {
            "name_template": _archive.DEFAULT_TEMPLATE,
            "folder_strategy": _archive.DEFAULT_FOLDER_STRATEGY,
            "is_default": True,
        }
    return {
        "name_template": s.get("name_template") or _archive.DEFAULT_TEMPLATE,
        "folder_strategy": s.get("folder_strategy") or _archive.DEFAULT_FOLDER_STRATEGY,
        "is_default": False,
    }


@router.put("/api/archive/settings")
async def archive_settings_put(payload: ArchiveSettingsPayload, request: Request):
    user = get_current_user_from_request(request)
    _check_archive_customize(user)  # v0.8 · 只有 Plus/Pro 能改模板
    # 基本校验:模板不能是空的
    if not payload.name_template:
        raise HTTPException(400, detail="archive.template_empty")
    ok = db.upsert_archive_settings(
        str(user["id"]),
        payload.name_template,
        payload.folder_strategy,
    )
    if not ok:
        raise HTTPException(500, detail="archive.save_failed")
    return {"ok": True}


@router.post("/api/archive/rename-preview")
async def archive_rename_preview(payload: ArchivePreviewRequest, request: Request):
    """给配置页实时预览用:传 merged_fields + 模板 → 返回名字"""
    user = get_current_user_from_request(request)
    _check_archive_access(user)
    from services.archive import archive as _archive

    template = payload.name_template
    if not template:
        # 没传模板 · 用用户当前设置(或默认)
        s = db.get_archive_settings(str(user["id"]))
        template = (s or {}).get("name_template") or _archive.DEFAULT_TEMPLATE
    name = _archive.preview_name(payload.merged_fields or {}, template)
    return {"name": name}


# ─── v0.13 · 重复发票检测设置 ─────────────────────────────
class DupCheckSettingPayload(BaseModel):
    enabled: bool


@router.get("/api/settings/dup-check")
async def dup_check_get(request: Request):
    user = get_current_user_from_request(request)
    return {"enabled": db.get_user_dup_check_enabled(str(user["id"]))}


@router.put("/api/settings/dup-check")
async def dup_check_put(payload: DupCheckSettingPayload, request: Request):
    user = get_current_user_from_request(request)
    ok = db.set_user_dup_check_enabled(str(user["id"]), payload.enabled)
    if not ok:
        raise HTTPException(500, detail="settings.save_failed")
    return {"ok": True, "enabled": payload.enabled}


# ─── P1b · ERP 自动处理方式(账户级默认 · 上传可临时覆盖本批)───────────
#   smart    = 智能分拣(按发票卖方→账套→ERP 端点 · 默认推荐)
#   fixed    = 固定当前账套(全推 auto_push 端点 · 现行为)
#   ocr_only = 只识别不推送(完全跳过 auto-push)
class ErpPushModePayload(BaseModel):
    mode: str


@router.get("/api/settings/erp-push-mode")
async def erp_push_mode_get(request: Request):
    user = get_current_user_from_request(request)
    return {"mode": db.get_erp_push_mode(str(user["id"]))}


@router.put("/api/settings/erp-push-mode")
async def erp_push_mode_put(payload: ErpPushModePayload, request: Request):
    user = get_current_user_from_request(request)
    if payload.mode not in db.ERP_PUSH_MODES:
        raise HTTPException(400, detail="settings.invalid_mode")
    ok = db.set_erp_push_mode(str(user["id"]), payload.mode)
    if not ok:
        raise HTTPException(500, detail="settings.save_failed")
    return {"ok": True, "mode": payload.mode}
