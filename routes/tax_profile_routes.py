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
from services.workorder import obligation_engine, wht_signals
from services.workorder.engine import (
    STATUS_ARCHIVE,
    STATUS_COLLECTING,
    STATUS_REVIEW,
    STATUS_RUNNING,
    STATUS_STUCK,
)
from services.workorder.obligation_engine import PERIOD_RE
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

# 矩阵格子徽章(C4 · UI-Canon-v4 §1 四色族:good=顺畅/完结,warn=缺料/催,
# crit=等人判/卡点,sage=AI 在做)。stuck 与 review 两个引擎态合并成同一个「待审」
# 徽章——矩阵一次 JOIN 喂全租户全客户,不能像工单详情那样逐单读 events 分辨 stuck
# 是缺料还是等人判(那是 N+1),两态对矩阵使用者都是"要人看"这一层意思,故不细分。
_BADGE_NO_NEED = "no_need"
_BADGE_PENDING_ORDER = "pending_order"
_BADGE_MISSING_MATERIALS = "missing_materials"
_BADGE_IN_PROGRESS = "in_progress"
_BADGE_PENDING_REVIEW = "pending_review"
_BADGE_FROZEN = "frozen"
_BADGE_NOT_EVALUATED = "not_evaluated"


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
    return authorize_pearnly_ai(request, _PERM, not_found="workspace.not_found")


def _assert_owns_workspace(cur, request: Request, user: dict, tenant_id: str, ws_id: int) -> None:
    """越权/不存在一律 404(不泄漏存在性),照 workorder_routes 同名 helper。"""
    assert_owns_workspace(cur, request, user, tenant_id, ws_id, not_found="workspace.not_found")


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
            raise HTTPException(_VALIDATION_ERR_STATUS, detail=e.code) from e
        profile = tax_profile_store.get_profile(
            cur, tenant_id=tenant_id, workspace_client_id=workspace_client_id
        )
        if profile is not None:
            period = obligation_engine.current_be_period()
            # 画像一变即重算当期义务;WHT 信号与开单接线同源(wht_signals),两入口一致。
            # 独立只读连接扫描——绝不用本 PUT 的写游标(防交接债 #2 静默丢画像 upsert)。
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
        for key in ("due_paper", "due_efiling", "updated_at"):
            if row.get(key) is not None:
                row[key] = row[key].isoformat()
    return {"period": resolved_period, "obligations": rows}


# 客户目录(EN-clients · 2026-07-13)「画像完整度」= 这 6 个默认落 unknown 的画像字段
# 里已被人工确认几个,0..1。挂在矩阵响应上(同一 LEFT JOIN,零额外往返),不是画像表单
# FIELD_DEFS 全集——sbt_status/filing_disposition 默认值本身就是"已答"(none/active),
# 计入分母只会让每个新客户显得比实际更"完整",故只数真正默认 unknown 的字段。
_COMPLETENESS_FIELDS = (
    "p_has_employees",
    "p_pays_individuals",
    "p_pays_juristic",
    "p_pays_foreign",
    "p_pays_interest_dividend",
    "p_efiling_enrolled",
)


def _profile_completeness(row: dict) -> float:
    """0..1,round 到 2 位。行里没有画像列(旧调用点/测试 fixture 没带)一律按全 unknown
    算,不假装完整——client_tax_profiles 缺档时 COALESCE 已在 SQL 层退到 'unknown'。"""
    answered = sum(1 for f in _COMPLETENESS_FIELDS if row.get(f, "unknown") != "unknown")
    return round(answered / len(_COMPLETENESS_FIELDS), 2)


def _matrix_badge(obligation_status: Optional[str], order_status: Optional[str]) -> str:
    """(obligation_status, order_status) → 矩阵格子徽章(纯函数,零 I/O,见常量顶注)。

    order_status 词汇一律 import engine.STATUS_*(单一事实源,C4-R1:首版手打
    "archived"/"signed" 两个臆造词,真冻结单 status=archive 落 fallthrough 错标
    「未评估」——测试也用同一套错词自证自洽,教训=状态字符串必须来自权威常量)。
    """
    if obligation_status is None:
        return _BADGE_NOT_EVALUATED  # 该期从未物化过义务(未存过画像/未开过单)
    if obligation_status == obligation_engine.STATUS_NIL:
        return _BADGE_NO_NEED
    if order_status is None:
        return _BADGE_PENDING_ORDER
    if order_status == STATUS_COLLECTING:
        return _BADGE_MISSING_MATERIALS
    if order_status == STATUS_RUNNING:
        return _BADGE_IN_PROGRESS
    if order_status in (STATUS_STUCK, STATUS_REVIEW):
        return _BADGE_PENDING_REVIEW
    if order_status == STATUS_ARCHIVE:
        return _BADGE_FROZEN
    return _BADGE_NOT_EVALUATED  # 未知未来态:诚实降级,不冒充已知徽章


@router.get("/api/tax-profile/matrix")
async def get_tax_profile_matrix(request: Request, period: Optional[str] = None):
    """事务所矩阵(C4):客户行 × 当期义务列,一次 JOIN 喂全矩阵,严禁循环查询。

    列集合 = 该租户该期实际物化过的 obligation_code(client_period_obligations 里
    没有行的客户/期不会凭空长出列——诚实反映"先保存一次画像或开一次单才有义务"的
    既有语义,见 obligation_engine 顶注);没有任何物化记录的客户仍出现在矩阵里,
    各格子标「未评估」而非编造一个已知徽章。

    客户目录(EN-clients)复用本端点当数据源:tax_id + profile_completeness 挂在同一
    LEFT JOIN 里一次带出(client_tax_profiles 与 workspace_clients 是 1:1,不会像
    obligation 那样按期/按义务码炸出多行),零额外查询。
    """
    user, tenant_id = authorize_pearnly_ai(request, _MATRIX_PERM, not_found="workorder.not_found")
    resolved_period = period or obligation_engine.current_be_period()
    if not PERIOD_RE.match(resolved_period):
        raise HTTPException(422, detail="obligation.invalid_period")

    with db.get_cursor() as cur:
        cur.execute(
            """
            SELECT wc.id AS client_id, wc.name AS client_name, wc.tax_id AS client_tax_id,
                   o.obligation_code, o.status AS obligation_status,
                   o.due_paper, o.due_efiling, o.work_order_id,
                   wo.status AS order_status, d.display_names,
                   COALESCE(p.has_employees, 'unknown') AS p_has_employees,
                   COALESCE(p.pays_individuals, 'unknown') AS p_pays_individuals,
                   COALESCE(p.pays_juristic, 'unknown') AS p_pays_juristic,
                   COALESCE(p.pays_foreign, 'unknown') AS p_pays_foreign,
                   COALESCE(p.pays_interest_dividend, 'unknown') AS p_pays_interest_dividend,
                   COALESCE(p.efiling_enrolled, 'unknown') AS p_efiling_enrolled
            FROM workspace_clients wc
            LEFT JOIN client_period_obligations o
                ON o.tenant_id = wc.tenant_id
               AND o.workspace_client_id = wc.id
               AND o.period = %s
            LEFT JOIN work_orders wo ON wo.id = o.work_order_id
            LEFT JOIN tax_obligation_defs d ON d.obligation_code = o.obligation_code
            LEFT JOIN client_tax_profiles p
                ON p.tenant_id = wc.tenant_id AND p.workspace_client_id = wc.id
            WHERE wc.tenant_id = %s AND wc.is_active = TRUE
            ORDER BY wc.name, o.obligation_code
            """,
            (resolved_period, tenant_id),
        )
        rows = [dict(r) for r in cur.fetchall()]

    # 作用域收窄(照 workspace_routes.list_workspace_clients 先例):被分派成员只看
    # 分配给自己的账套主体;超管/scope_mode='all' 零开销直接放行。
    authz = get_authz(request, user)
    if not user.get("is_super_admin") and authz.scope_mode == "assigned":
        allowed = authz.workspace_ids or frozenset()
        rows = [r for r in rows if int(r["client_id"]) in allowed]

    clients: dict[int, dict] = {}
    client_has_order: dict[int, bool] = {}
    codes: set[str] = set()
    labels: dict[str, dict] = {}
    cells: list[dict] = []
    for r in rows:
        cid = int(r["client_id"])
        clients.setdefault(
            cid,
            {
                "id": cid,
                "name": r["client_name"],
                "tax_id": r.get("client_tax_id"),
                "profile_completeness": _profile_completeness(r),
            },
        )
        client_has_order.setdefault(cid, False)
        code = r["obligation_code"]
        if code is None:
            continue
        codes.add(code)
        if code not in labels and r.get("display_names"):
            labels[code] = r["display_names"]
        if r["work_order_id"]:
            client_has_order[cid] = True
        cells.append(
            {
                "client_id": cid,
                "obligation_code": code,
                "obligation_status": r["obligation_status"],
                "order_status": r["order_status"],
                "work_order_id": str(r["work_order_id"]) if r["work_order_id"] else None,
                "due_paper": r["due_paper"].isoformat() if r["due_paper"] else None,
                "due_efiling": r["due_efiling"].isoformat() if r["due_efiling"] else None,
                "badge": _matrix_badge(r["obligation_status"], r["order_status"]),
            }
        )

    out_clients = []
    for cid, c in clients.items():
        c["missing_order"] = not client_has_order.get(cid, False)
        out_clients.append(c)
    out_clients.sort(key=lambda c: c["name"])

    return {
        "period": resolved_period,
        "clients": out_clients,
        "obligation_codes": sorted(codes),
        "obligation_labels": labels,
        "cells": cells,
    }
