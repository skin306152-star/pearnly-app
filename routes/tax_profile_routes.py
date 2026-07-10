# -*- coding: utf-8 -*-
"""客户税务画像 · 别名 · 当期义务 HTTP API(B2-e · 税务画像-方案-B1.md §6)。

三块只读+写薄壳,业务逻辑全在既有 DAL(不重写):
  services.workspace.tax_profile_store  · 画像 get/upsert + defs
  services.workspace.client_alias_store · 别名 CRUD(污染五闸已在 DAL 内)
  services.workorder.obligation_engine  · 画像×period×defs → 义务清单(纯函数)+ 物化

全组挂 feature flag `pearnly_ai_m1`(默认关,fail-closed 404),权限同「管理账套主体」
(照 workorder_routes/workspace_routes 先例:税务资料是账套主体的一部分,同权不细分)。
每条 {workspace_client_id} 路由先校验该主体属本租户 + 账套作用域,越权 404 防枚举。

义务清单是「读物化表」的薄壳,不在 GET 里现算——落库由 open_order(工单开单,见
services.workorder.api._generate_obligations_on_open)与本文件的画像 PUT 两处触发
(画像一变,当期义务立刻跟着重算,不用等下次开单才看见新画像生效)。
"""

from __future__ import annotations

import logging
import re
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from core import db
from core.auth import get_current_user_from_request
from core.feature_flags import pearnly_ai_m1_enabled_for
from core.route_helpers import _tid
from services.authz.deps import check_workspace_scope, require_perm
from services.workorder import obligation_engine
from services.workspace import client_alias_store, tax_profile_store
from services.workspace.client_alias_store import AliasError
from services.workspace.tax_profile_store import TaxProfileError

logger = logging.getLogger(__name__)

router = APIRouter()

# 画像/义务是账套主体资料的一部分,与「管理账套主体」同权(照 workorder_routes 先例)。
_PERM = "settings.workspace.manage"

_BE_YEAR_OFFSET = 543  # 佛历 = 公历 + 543(与 services/summary_import/dates.py 同口径)
_PERIOD_RE = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")

_ALIAS_ERR_STATUS = 422
_PROFILE_ERR_STATUS = 422


class TaxProfileUpdate(BaseModel):
    """部分更新(方案 §2.2 字段表 · 不含只读派生字段 vat_status/branch)。

    money 字段 vat_credit_carry 走十进制字符串进出(禁 float),照
    workorder_routes.SalesSummaryIn 先例;DAL 层 _to_decimal 再校验/转型。
    """

    sbt_status: Optional[str] = Field(None, description="none | registered | unknown")
    sbt_business_type: Optional[str] = Field(None, max_length=200)
    has_employees: Optional[str] = Field(None, description="yes | no | unknown")
    pays_individuals: Optional[str] = Field(None, description="yes | no | unknown")
    pays_juristic: Optional[str] = Field(None, description="yes | no | unknown")
    pays_foreign: Optional[str] = Field(None, description="yes | no | unknown")
    pays_interest_dividend: Optional[str] = Field(None, description="yes | no | unknown")
    has_multi_branch: Optional[bool] = None
    branch_count: Optional[int] = Field(None, ge=1, le=999)
    filing_disposition: Optional[str] = Field(None, description="active | dormant | unknown")
    efiling_enrolled: Optional[str] = Field(None, description="yes | no | unknown")
    tax_agent_authorized: Optional[bool] = None
    tax_agent_ref: Optional[str] = Field(None, max_length=200)
    vat_credit_carry: Optional[str] = Field(
        None, max_length=40, description="历史留抵(十进制字符串)"
    )


class AliasCreate(BaseModel):
    alias_raw: str = Field(..., min_length=1, max_length=200)
    alias_kind: str = Field("misc", max_length=20)
    match_mode: str = Field("exact", max_length=20)


def _authorize(request: Request) -> tuple[dict, str]:
    """登录 + M1 闸(关→404 fail-closed)+ 动作权限。返回 (user, tenant_id)。"""
    user = get_current_user_from_request(request)
    tenant_id = _tid(user)
    if not pearnly_ai_m1_enabled_for(tenant_id, str(user["id"])):
        raise HTTPException(404, detail="workspace.not_found")
    require_perm(request, _PERM)
    if not tenant_id:
        raise HTTPException(403, detail="authz.forbidden")
    return user, tenant_id


def _assert_owns_workspace(cur, request: Request, user: dict, tenant_id: str, ws_id: int) -> None:
    """越权/不存在一律 404(不泄漏存在性),照 workorder_routes 同名 helper。"""
    cur.execute(
        "SELECT 1 FROM workspace_clients WHERE id = %s AND tenant_id = %s",
        (ws_id, tenant_id),
    )
    if not cur.fetchone():
        raise HTTPException(404, detail="workspace.not_found")
    check_workspace_scope(request, user, ws_id)


def _current_be_period() -> str:
    """当前公历月 → 佛历「YYYY-MM」,给「画像保存后重物化当期义务」定「当期」用。"""
    today = datetime.now(timezone.utc).date()
    return f"{today.year + _BE_YEAR_OFFSET:04d}-{today.month:02d}"


def _serialize_profile(profile: dict) -> dict:
    """Decimal → 十进制字符串(禁 float 精度丢失)、datetime → ISO,其余原样透传。"""
    out = dict(profile)
    for key in ("vat_credit_carry", "confidence"):
        if out.get(key) is not None:
            out[key] = str(out[key])
    for key in ("updated_at", "created_at"):
        if out.get(key) is not None:
            out[key] = out[key].isoformat()
    return out


def _regenerate_current_period_obligations(
    cur, *, tenant_id: str, workspace_client_id: int, profile: dict
) -> None:
    """画像一变,当期义务立刻重算物化(不用等下次开单)。义务清单是供料层,失败不挡画像保存。"""
    try:
        period = _current_be_period()
        defs = tax_profile_store.load_active_defs(cur)
        obligations = obligation_engine.generate_obligations(
            profile=profile, period=period, data_signals=None, defs=defs
        )
        obligation_engine.materialize_obligations(
            cur,
            tenant_id=tenant_id,
            workspace_client_id=workspace_client_id,
            work_order_id=None,
            period=period,
            obligations=obligations,
        )
    except Exception:
        logger.exception(
            "obligation_engine re-materialize failed on profile save (tenant=%s, client=%s)",
            tenant_id,
            workspace_client_id,
        )


@router.get("/api/workspace/clients/{workspace_client_id}/tax-profile")
async def get_tax_profile(workspace_client_id: int, request: Request):
    """画像 + 派生字段(vat_status/branch join 自 workspace_clients,不重复存)。"""
    user, tenant_id = _authorize(request)
    with db.get_cursor() as cur:
        _assert_owns_workspace(cur, request, user, tenant_id, workspace_client_id)
        profile = tax_profile_store.get_profile(
            cur, tenant_id=tenant_id, workspace_client_id=workspace_client_id
        )
    if profile is None:
        raise HTTPException(404, detail="workspace.not_found")
    return {"profile": _serialize_profile(profile)}


@router.put("/api/workspace/clients/{workspace_client_id}/tax-profile")
async def put_tax_profile(workspace_client_id: int, req: TaxProfileUpdate, request: Request):
    """upsert(部分字段);保存后对当期(今日所在佛历月)重物化义务清单。"""
    user, tenant_id = _authorize(request)
    payload = req.model_dump(exclude_none=True)
    with db.get_cursor(commit=True) as cur:
        _assert_owns_workspace(cur, request, user, tenant_id, workspace_client_id)
        try:
            tax_profile_store.upsert_profile(
                cur,
                tenant_id=tenant_id,
                workspace_client_id=workspace_client_id,
                updated_by=f"user:{user['id']}",
                **payload,
            )
        except TaxProfileError as e:
            raise HTTPException(_PROFILE_ERR_STATUS, detail=e.code) from e
        profile = tax_profile_store.get_profile(
            cur, tenant_id=tenant_id, workspace_client_id=workspace_client_id
        )
        if profile is not None:
            _regenerate_current_period_obligations(
                cur, tenant_id=tenant_id, workspace_client_id=workspace_client_id, profile=profile
            )
    if profile is None:
        raise HTTPException(404, detail="workspace.not_found")
    return {"profile": _serialize_profile(profile)}


@router.get("/api/workspace/clients/{workspace_client_id}/aliases")
async def list_client_aliases(
    workspace_client_id: int, request: Request, include_inactive: bool = False
):
    user, tenant_id = _authorize(request)
    with db.get_cursor() as cur:
        _assert_owns_workspace(cur, request, user, tenant_id, workspace_client_id)
        aliases = client_alias_store.list_aliases(
            cur,
            tenant_id=tenant_id,
            workspace_client_id=workspace_client_id,
            active_only=not include_inactive,
        )
    return {"aliases": aliases, "count": len(aliases)}


@router.post("/api/workspace/clients/{workspace_client_id}/aliases")
async def create_client_alias(workspace_client_id: int, req: AliasCreate, request: Request):
    """新增别名。source 固定 human_confirmed(方向锚唯一消费的可信来源,方案 §4.6 闸3)。"""
    user, tenant_id = _authorize(request)
    with db.get_cursor(commit=True) as cur:
        _assert_owns_workspace(cur, request, user, tenant_id, workspace_client_id)
        try:
            alias_id = client_alias_store.add_alias(
                cur,
                tenant_id=tenant_id,
                workspace_client_id=workspace_client_id,
                alias_raw=req.alias_raw,
                alias_kind=req.alias_kind,
                match_mode=req.match_mode,
                source="human_confirmed",
            )
        except AliasError as e:
            raise HTTPException(_ALIAS_ERR_STATUS, detail=e.code) from e
    if alias_id is None:
        raise HTTPException(_ALIAS_ERR_STATUS, detail="alias.empty")
    return {"ok": True, "id": alias_id}


@router.post("/api/workspace/clients/{workspace_client_id}/aliases/{alias_id}/deactivate")
async def deactivate_client_alias(workspace_client_id: int, alias_id: int, request: Request):
    """软删。先校验该别名确属这个客户(URL 路径与资源一致),防跨客户 id 枚举误删。"""
    user, tenant_id = _authorize(request)
    with db.get_cursor(commit=True) as cur:
        _assert_owns_workspace(cur, request, user, tenant_id, workspace_client_id)
        cur.execute(
            "SELECT 1 FROM client_name_aliases "
            "WHERE tenant_id = %s AND id = %s AND workspace_client_id = %s",
            (tenant_id, alias_id, workspace_client_id),
        )
        if not cur.fetchone():
            raise HTTPException(404, detail="alias.not_found")
        ok = client_alias_store.deactivate_alias(cur, tenant_id=tenant_id, alias_id=alias_id)
    if not ok:
        raise HTTPException(404, detail="alias.not_found")
    return {"ok": True}


@router.get("/api/workspace/clients/{workspace_client_id}/obligations")
async def list_client_obligations(
    workspace_client_id: int, request: Request, period: Optional[str] = None
):
    """当期义务清单(读物化表 client_period_obligations,不现算)。period 缺省=当前佛历月。

    JOIN tax_obligation_defs 带出 display_names(四语义务名),前端按当前语言取键,
    不必在前端另抄一份义务码→名称的映射表。
    """
    user, tenant_id = _authorize(request)
    resolved_period = period or _current_be_period()
    if not _PERIOD_RE.match(resolved_period):
        raise HTTPException(422, detail="obligation.invalid_period")
    with db.get_cursor() as cur:
        _assert_owns_workspace(cur, request, user, tenant_id, workspace_client_id)
        cur.execute(
            """
            SELECT o.obligation_code, o.status, o.trigger_source, o.due_paper, o.due_efiling,
                   o.updated_at, d.display_names
            FROM client_period_obligations o
            LEFT JOIN tax_obligation_defs d ON d.obligation_code = o.obligation_code
            WHERE o.tenant_id = %s AND o.workspace_client_id = %s AND o.period = %s
            ORDER BY o.due_efiling NULLS LAST, o.obligation_code
            """,
            (tenant_id, workspace_client_id, resolved_period),
        )
        rows = [dict(r) for r in cur.fetchall()]
    for row in rows:
        for key in ("due_paper", "due_efiling", "updated_at"):
            if row.get(key) is not None:
                row[key] = row[key].isoformat()
    return {"period": resolved_period, "obligations": rows}
