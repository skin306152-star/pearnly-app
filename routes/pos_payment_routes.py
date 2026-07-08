# -*- coding: utf-8 -*-
"""POS 收款设置路由(老板后台 · 主程序 · docs/pos UI 13-收款设置)。

薄层:owner(收银员不可改收款配置 → 403)→ 模块守门(pos)→ 账套归属 → 调
services/pos/payment_settings。统一 POS 信封。写端单事务。按账套 workspace_client_id 隔离。
"""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Query, Request
from pydantic import BaseModel, Field

from core import db
from core.pos_api import PosError, assert_module_enabled, ok, require_workspace
from services.authz.deps import require_perm_pos
from services.pos import payment_settings as svc

router = APIRouter(prefix="/api/pos/admin", tags=["pos-payment"])


def _owner_ctx(request: Request, ws_override: Optional[int]) -> tuple[str, int]:
    user = require_perm_pos(request, "pos.admin.manage")  # 收款配置=老板动作,收银员 403
    tid = user.get("tenant_id")
    if not tid:
        raise PosError("pos.forbidden", 403)
    ws = user.get("workspace_client_id") or ws_override
    if ws is None:
        raise PosError("pos.forbidden", 403)
    return str(tid), int(ws)


class PaymentSettings(BaseModel):
    workspace_client_id: Optional[int] = None
    promptpay_enabled: bool = True
    card_enabled: bool = True
    service_charge_rate: float = Field(0, ge=0, le=100)
    price_includes_vat: bool = True
    promptpay_id: str = ""
    bank_transfer_enabled: bool = False
    bank_name: str = ""
    bank_account_no: str = ""
    bank_account_name: str = ""


@router.get("/payment-settings")
async def api_get_payment_settings(
    request: Request, workspace_client_id: Optional[int] = Query(None)
):
    tid, ws = _owner_ctx(request, workspace_client_id)
    with db.get_cursor_rls(tid, commit=False) as cur:
        assert_module_enabled(cur, tid, "pos")
        require_workspace(cur, tid, ws)
        return ok(svc.get_settings(cur, tenant_id=tid, workspace_client_id=ws))


@router.put("/payment-settings")
async def api_save_payment_settings(req: PaymentSettings, request: Request):
    tid, ws = _owner_ctx(request, req.workspace_client_id)
    with db.get_cursor_rls(tid, commit=True) as cur:
        assert_module_enabled(cur, tid, "pos")
        require_workspace(cur, tid, ws)
        return ok(
            svc.save_settings(
                cur,
                tenant_id=tid,
                workspace_client_id=ws,
                promptpay_enabled=req.promptpay_enabled,
                card_enabled=req.card_enabled,
                service_charge_rate=req.service_charge_rate,
                price_includes_vat=req.price_includes_vat,
                promptpay_id=req.promptpay_id,
                bank_transfer_enabled=req.bank_transfer_enabled,
                bank_name=req.bank_name,
                bank_account_no=req.bank_account_no,
                bank_account_name=req.bank_account_name,
            )
        )
