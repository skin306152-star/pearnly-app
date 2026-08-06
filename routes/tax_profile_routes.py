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

from typing import Optional

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from core import db
from core.route_helpers import assert_owns_workspace, authorize_pearnly_ai
from services.authz.deps import check_workspace_scope, get_authz
from services.workorder import matrix, obligation_engine, profile_inference, wht_signals
from services.workorder.obligation_engine import PERIOD_RE, iso_or_none as _iso
from services.workspace import client_alias_store, tax_profile_store
from services.workspace.client_alias_store import AliasError
from services.workspace.tax_profile_store import TaxProfileError

router = APIRouter()

# 画像/义务是账套主体资料的一部分,与「管理账套主体」同权(照 workorder_routes 先例)。
_PERM = "settings.workspace.manage"

# 矩阵(C4)是工单/义务的聚合只读视图,不是画像资料本身——读侧权限走 C3 的
# tax.filing.view 细码(与 workorder_routes._C_VIEW 同码同权),不用 _PERM。
_MATRIX_PERM = "tax.filing.view"

# 别名/画像两类校验错都映射同一个 422(区分靠 detail 机器码,不靠状态码)。
_VALIDATION_ERR_STATUS = 422


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


class TaxProfileConfirm(BaseModel):
    """画像卡「确认」动作(画像卡智能判断批次):把 GET 响应里带出的推断候选转正。"""

    fields: list[str] = Field(
        ..., min_length=1, max_length=len(tax_profile_store.TRACKED_FIELD_KEYS)
    )


def _authorize(request: Request) -> tuple[dict, str]:
    """登录 + M1 闸(关→404 fail-closed)+ 动作权限。返回 (user, tenant_id)。"""
    return authorize_pearnly_ai(request, _PERM, not_found="workspace.not_found")


def _assert_owns_workspace(cur, request: Request, user: dict, tenant_id: str, ws_id: int) -> None:
    """越权/不存在一律 404(不泄漏存在性),照 workorder_routes 同名 helper。"""
    assert_owns_workspace(cur, request, user, tenant_id, ws_id, not_found="workspace.not_found")


def _obligation_codes(cur, tenant_id: str, workspace_client_id: int, period: str) -> set:
    """当期已物化的义务码集合(画像变动前后各查一次,差集就是「新增义务」)。"""
    cur.execute(
        "SELECT obligation_code FROM client_period_obligations "
        "WHERE tenant_id = %s AND workspace_client_id = %s AND period = %s",
        (tenant_id, workspace_client_id, period),
    )
    return {r["obligation_code"] for r in cur.fetchall()}


def _rematerialize_and_diff(
    cur,
    *,
    tenant_id: str,
    workspace_client_id: int,
    period: str,
    profile: dict,
    prev_codes: set,
    data_signals: Optional[dict] = None,
) -> list:
    """画像一变(手填/确认)就重算当期义务,返回新增的义务码(供前端 toast)。

    data_signals 与开单接线同源(wht_signals),两入口一致——独立只读连接扫描,绝不用
    本次写事务的游标(防交接债 #2 静默丢画像 upsert)。调用方(confirm 端点)若这次请求
    已经扫过一遍当期信号,原样传进来复用,不用为重算再扫一遍——GET/PUT 没有现成信号,
    留空走默认扫描。"""
    if data_signals is None:
        data_signals = wht_signals.scan_period_wht_signals_isolated(
            tenant_id=tenant_id, workspace_client_id=workspace_client_id, period=period
        )
    obligation_engine.rematerialize_for_profile(
        cur,
        tenant_id=tenant_id,
        workspace_client_id=workspace_client_id,
        period=period,
        profile=profile,
        data_signals=data_signals,
    )
    return sorted(_obligation_codes(cur, tenant_id, workspace_client_id, period) - prev_codes)


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


@router.get("/api/workspace/clients/{workspace_client_id}/tax-profile")
async def get_tax_profile(workspace_client_id: int, request: Request):
    """画像 + 派生字段(vat_status/branch join 自 workspace_clients,不重复存)。

    省一次独立归属查询:get_profile 的底查询本就 FROM workspace_clients WHERE
    tenant_id=%s AND id=%s,None 天然等价于「主体不属本租户/不存在」,不用先跑一遍
    _assert_owns_workspace 的 SELECT 1 再查一遍画像。
    """
    user, tenant_id = _authorize(request)
    with db.get_cursor() as cur:
        profile = tax_profile_store.get_profile(
            cur, tenant_id=tenant_id, workspace_client_id=workspace_client_id
        )
    if profile is None:
        raise HTTPException(404, detail="workspace.not_found")
    check_workspace_scope(request, user, workspace_client_id)

    # 诚实推断(画像卡智能判断批次):每次 GET 现算,不落库、不加定时任务——只有
    # pays_individuals/pays_juristic 两项有数据源(services.workorder.wht_signals),
    # 现算的候选合并进 field_meta[field].proposal 这一次响应,用户点确认才真正落库。
    period = obligation_engine.current_be_period()
    data_signals = wht_signals.scan_period_wht_signals_isolated(
        tenant_id=tenant_id, workspace_client_id=workspace_client_id, period=period
    )
    proposals = profile_inference.compute_proposals(
        profile=profile,
        field_meta=profile.get("field_meta") or {},
        data_signals=data_signals,
        period=period,
    )
    serialized = _serialize_profile(profile)
    serialized["field_meta"] = profile_inference.merge_proposals_into_field_meta(
        serialized.get("field_meta") or {}, proposals
    )
    # completeness 给档案页完整度条 + 客户目录 0% CTA(前端消费此值,不再手抄字段表)。
    return {
        "profile": serialized,
        "completeness": matrix.profile_completeness(profile),
    }


@router.put("/api/workspace/clients/{workspace_client_id}/tax-profile")
async def put_tax_profile(workspace_client_id: int, req: TaxProfileUpdate, request: Request):
    """upsert(部分字段,手填即确认);保存后对当期重物化义务清单,返回新增义务码
    (画像卡确认后 toast「当期义务已重算:+新增项」消费此值)。"""
    user, tenant_id = _authorize(request)
    payload = req.model_dump(exclude_none=True)
    added: list = []
    with db.get_cursor(commit=True) as cur:
        _assert_owns_workspace(cur, request, user, tenant_id, workspace_client_id)
        period = obligation_engine.current_be_period()
        prev_codes = _obligation_codes(cur, tenant_id, workspace_client_id, period)
        try:
            tax_profile_store.upsert_profile(
                cur,
                tenant_id=tenant_id,
                workspace_client_id=workspace_client_id,
                updated_by=f"user:{user['id']}",
                **payload,
            )
        except TaxProfileError as e:
            raise HTTPException(_VALIDATION_ERR_STATUS, detail=e.code) from e
        profile = tax_profile_store.get_profile(
            cur, tenant_id=tenant_id, workspace_client_id=workspace_client_id
        )
        if profile is not None:
            added = _rematerialize_and_diff(
                cur,
                tenant_id=tenant_id,
                workspace_client_id=workspace_client_id,
                period=period,
                profile=profile,
                prev_codes=prev_codes,
            )
    if profile is None:
        raise HTTPException(404, detail="workspace.not_found")
    return {"profile": _serialize_profile(profile), "added_obligations": added}


@router.post("/api/workspace/clients/{workspace_client_id}/tax-profile/confirm")
async def confirm_tax_profile_fields(
    workspace_client_id: int, req: TaxProfileConfirm, request: Request
):
    """把 GET 响应里带出的推断候选(field_meta[field].proposal)转正。

    每个字段用「这一刻重新现算」的候选核对(不信任前端回传的旧候选)——两次请求之间
    数据可能已经变了(同事又过账了一张票),候选跟不上就诚实报 409,不假装还是原来
    那份候选;成功转正的字段与 PUT 同款返回新增义务码,前端同一套 toast 逻辑复用。
    """
    user, tenant_id = _authorize(request)
    added: list = []
    with db.get_cursor(commit=True) as cur:
        _assert_owns_workspace(cur, request, user, tenant_id, workspace_client_id)
        profile = tax_profile_store.get_profile(
            cur, tenant_id=tenant_id, workspace_client_id=workspace_client_id
        )
        if profile is None:
            raise HTTPException(404, detail="workspace.not_found")
        period = obligation_engine.current_be_period()
        data_signals = wht_signals.scan_period_wht_signals_isolated(
            tenant_id=tenant_id, workspace_client_id=workspace_client_id, period=period
        )
        live_proposals = profile_inference.compute_proposals(
            profile=profile,
            field_meta=profile.get("field_meta") or {},
            data_signals=data_signals,
            period=period,
        )
        to_confirm = {}
        for field in req.fields:
            if field not in live_proposals:
                raise HTTPException(409, detail="tax_profile.proposal_stale")
            to_confirm[field] = live_proposals[field]
        prev_codes = _obligation_codes(cur, tenant_id, workspace_client_id, period)
        tax_profile_store.confirm_field_proposals(
            cur,
            tenant_id=tenant_id,
            workspace_client_id=workspace_client_id,
            updated_by=f"user:{user['id']}",
            proposals=to_confirm,
        )
        profile = tax_profile_store.get_profile(
            cur, tenant_id=tenant_id, workspace_client_id=workspace_client_id
        )
        if profile is not None:
            added = _rematerialize_and_diff(
                cur,
                tenant_id=tenant_id,
                workspace_client_id=workspace_client_id,
                period=period,
                profile=profile,
                prev_codes=prev_codes,
                data_signals=data_signals,  # 这次请求已经扫过一遍,不重复扫描
            )
    if profile is None:
        raise HTTPException(404, detail="workspace.not_found")
    return {"profile": _serialize_profile(profile), "added_obligations": added}


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
            raise HTTPException(_VALIDATION_ERR_STATUS, detail=e.code) from e
    if alias_id is None:
        raise HTTPException(_VALIDATION_ERR_STATUS, detail="alias.empty")
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
    resolved_period = period or obligation_engine.current_be_period()
    if not PERIOD_RE.match(resolved_period):
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
        # 顺延(G3 · MC2-B 件2)在裸日期基础上现算,原始日先留原样再顺延——两个事实都
        # 序列化出去(读侧如实展示,别只留顺延日糊掉规则见 obligation_engine 顶注)。
        row["due_paper_deferred"] = _iso(obligation_engine.defer_optional(row.get("due_paper")))
        row["due_efiling_deferred"] = _iso(obligation_engine.defer_optional(row.get("due_efiling")))
        for key in ("due_paper", "due_efiling", "updated_at"):
            if row.get(key) is not None:
                row[key] = row[key].isoformat()
    return {"period": resolved_period, "obligations": rows}


@router.get("/api/tax-profile/matrix")
async def get_tax_profile_matrix(request: Request, period: Optional[str] = None):
    """事务所矩阵(C4):客户行 × 当期义务列,一次 JOIN 喂全矩阵,严禁循环查询。

    聚合本体在 services.workorder.matrix(B2-M1 下沉):智能管家的 matrix_overview 工具
    读同一份矩阵,SQL 只此一处,对话查到的与人手点开看到的同源。本层只剩鉴权 + 期间归一
    + 作用域收窄(依赖 HTTP 权限快照,留在路由)。

    客户目录(EN-clients)复用本端点当数据源:tax_id + profile_completeness 挂在同一
    LEFT JOIN 里一次带出(client_tax_profiles 与 workspace_clients 是 1:1,不会像
    obligation 那样按期/按义务码炸出多行),零额外查询。
    """
    user, tenant_id = authorize_pearnly_ai(request, _MATRIX_PERM, not_found="workorder.not_found")
    resolved_period = period or obligation_engine.current_be_period()
    if not PERIOD_RE.match(resolved_period):
        raise HTTPException(422, detail="obligation.invalid_period")

    with db.get_cursor() as cur:
        rows = matrix.fetch_rows(cur, tenant_id=tenant_id, period=resolved_period)

    # 作用域收窄(照 workspace_routes.list_workspace_clients 先例):被分派成员只看
    # 分配给自己的账套主体;超管/scope_mode='all' 零开销直接放行。
    authz = get_authz(request, user)
    if not user.get("is_super_admin") and authz.scope_mode == "assigned":
        allowed = authz.workspace_ids or frozenset()
        rows = [r for r in rows if int(r["client_id"]) in allowed]

    return matrix.build(rows, period=resolved_period)
