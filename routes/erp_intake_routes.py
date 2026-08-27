"""ERP 商户 staged OCR 草稿动作。"""

from __future__ import annotations

from typing import List

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from core.auth import get_current_user_from_request
from core import db
from core.feature_flags import erp_portal_enabled_for
from core.route_helpers import _tid
from services.auth.entrance import ERP, require_erp_portal
from services.ocr import pdf_storage
from services.ocr_history.staged import discard_staged_ocr_history_with_pdf_paths

router = APIRouter()


def _authorize(request: Request) -> dict:
    """草稿动作仅接受 ERP 邀请会话；超管保留任意门。"""
    user = get_current_user_from_request(request)
    require_erp_portal(user)
    if user.get("is_super_admin"):
        return user
    if user.get("entry") != ERP:
        raise HTTPException(403, detail="authz.entrance_scope")
    tenant_id = str(user["tenant_id"]) if user.get("tenant_id") else None
    user_id = str(user["id"]) if user.get("id") else None
    if not erp_portal_enabled_for(tenant_id, user_id):
        raise HTTPException(404, detail="erp.not_found")
    return user


class ErpDiscardRequest(BaseModel):
    history_ids: List[str] = Field(..., min_length=1, max_length=500)


@router.post("/api/erp/intake/discard")
async def erp_discard_staged(req: ErpDiscardRequest, request: Request):
    """只丢弃调用者仍为 staged 且尚未转换的 OCR 草稿。"""
    user = _authorize(request)
    deleted, paths = discard_staged_ocr_history_with_pdf_paths(
        str(user["id"]), list(req.history_ids), tenant_id=_tid(user)
    )
    for path in set(paths):
        try:
            with db.get_cursor_rls(bypass=True) as cur:
                cur.execute(
                    "SELECT 1 FROM ocr_history WHERE pdf_storage_path = %s LIMIT 1", (path,)
                )
                still_used = cur.fetchone() is not None
            if not still_used:
                pdf_storage.delete_pdf(path)
        except Exception:
            # 数据库删除已经提交；孤立留底可由后续维护任务清理。
            continue
    return {"ok": True, "discarded": deleted, "skipped": max(0, len(req.history_ids) - deleted)}
