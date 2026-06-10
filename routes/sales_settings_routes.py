# -*- coding: utf-8 -*-
"""租户开票设置路由(M7 · docs/16 §M7 / §N)。

GET 读默认(无行回内建默认),PUT upsert。开票向导/工作台读它预填表单,开票时按它取默认
(连号前缀/重置/起始号、审批模式、价内外/WHT/模板/语言/纸张/省纸),单据仍可覆盖。薄层:
鉴权 + 整形;存储在 services/sales/settings.py。
"""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Request
from pydantic import BaseModel, Field

from core import db
from services.authz.deps import require_perm_tid
from services.sales import settings as settings_svc

router = APIRouter(prefix="/api/sales/settings", tags=["sales-settings"])


class SettingsIn(BaseModel):
    number_prefix: Optional[str] = Field(None, max_length=20)
    number_reset: Optional[str] = Field(None, max_length=10)
    number_start: Optional[int] = Field(None, ge=1)
    approval_mode: Optional[str] = Field(None, max_length=10)
    price_includes_vat_default: Optional[bool] = None
    default_wht_rate: Optional[float] = Field(None, ge=0, le=100)
    default_template_id: Optional[str] = Field(None, max_length=40)
    default_doc_lang: Optional[str] = Field(None, max_length=8)
    default_paper: Optional[str] = Field(None, max_length=20)
    default_copies_layout: Optional[str] = Field(None, max_length=20)


def _out(s: dict) -> dict:
    return {
        "number_prefix": s.get("number_prefix"),
        "number_reset": s.get("number_reset"),
        "number_start": int(s.get("number_start") or 1),
        "approval_mode": s.get("approval_mode"),
        "price_includes_vat_default": bool(s.get("price_includes_vat_default")),
        "default_wht_rate": str(s.get("default_wht_rate")),
        "default_template_id": s.get("default_template_id"),
        "default_doc_lang": s.get("default_doc_lang"),
        "default_paper": s.get("default_paper"),
        "default_copies_layout": s.get("default_copies_layout"),
    }


@router.get("")
async def api_get_settings(request: Request):
    tid, _ = require_perm_tid(request, "sales.doc.view")
    with db.get_cursor_rls(tid) as cur:
        s = settings_svc.get_settings(cur, tenant_id=tid)
    return {"settings": _out(s)}


@router.put("")
async def api_set_settings(req: SettingsIn, request: Request):
    tid, _ = require_perm_tid(request, "sales.settings.manage")
    fields = req.model_dump() if hasattr(req, "model_dump") else req.dict()
    with db.get_cursor_rls(tid, commit=True) as cur:
        s = settings_svc.set_settings(cur, tenant_id=tid, fields=fields)
    return {"ok": True, "settings": _out(s)}
