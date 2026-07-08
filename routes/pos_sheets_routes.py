# -*- coding: utf-8 -*-
"""POS Google Sheet 留档设置路由(老板后台 · 主程序 · docs/pos UI 14-Google Sheet)。

薄层:owner(收银员不可改 → 403)→ 模块守门(pos)→ 账套归属 → 调 services/pos/sheets_sync。
Google 连接状态借读 export.google_store(与采购导出共用同一份凭据,见 google_oauth_routes
的 return_to=pos)——本文件不重复实现 OAuth,只管"目标表"配置。统一 POS 信封。
"""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Query, Request
from pydantic import BaseModel

from core import db
from core.pos_api import PosError, assert_module_enabled, ok, require_workspace
from services.authz.deps import require_perm_pos
from services.export import google_store
from services.pos import sheets_sync as svc

router = APIRouter(prefix="/api/pos/admin", tags=["pos-sheets"])


def _owner_ctx(request: Request, ws_override: Optional[int]) -> tuple[str, int]:
    user = require_perm_pos(request, "pos.admin.manage")  # 收款配置=老板动作,收银员 403
    tid = user.get("tenant_id")
    if not tid:
        raise PosError("pos.forbidden", 403)
    ws = user.get("workspace_client_id") or ws_override
    if ws is None:
        raise PosError("pos.forbidden", 403)
    return str(tid), int(ws)


class SheetsSettings(BaseModel):
    workspace_client_id: Optional[int] = None
    enabled: bool = False
    lang: str = "th"


@router.get("/sheets-settings")
async def api_get_sheets_settings(
    request: Request, workspace_client_id: Optional[int] = Query(None)
):
    tid, ws = _owner_ctx(request, workspace_client_id)
    with db.get_cursor_rls(tid, commit=False) as cur:
        assert_module_enabled(cur, tid, "pos")
        require_workspace(cur, tid, ws)
        cred = google_store.get_credential(cur, tenant_id=tid, workspace_client_id=ws)
        settings = svc.get_settings(cur, tenant_id=tid, workspace_client_id=ws)
    return ok(
        {
            **settings,
            "connected": bool(cred),
            "email": (cred or {}).get("google_email") or "",
            "sheet_url": svc.sheet_url(settings["spreadsheet_id"]),
        }
    )


@router.put("/sheets-settings")
async def api_save_sheets_settings(req: SheetsSettings, request: Request):
    tid, ws = _owner_ctx(request, req.workspace_client_id)
    with db.get_cursor_rls(tid, commit=True) as cur:
        assert_module_enabled(cur, tid, "pos")
        require_workspace(cur, tid, ws)
        settings = (
            svc.ensure_target_sheet(cur, tenant_id=tid, workspace_client_id=ws, lang=req.lang)
            if req.enabled
            else svc.set_enabled(cur, tenant_id=tid, workspace_client_id=ws, enabled=False)
        )
        return ok({**settings, "sheet_url": svc.sheet_url(settings["spreadsheet_id"])})
