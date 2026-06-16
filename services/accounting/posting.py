# -*- coding: utf-8 -*-
"""过账引擎(docs/accounting/02 引擎流程):取业务 → 套模板 → 解析科目 → 断言平 → 落库。

分流(状态诚实 · 绝不静默乱过):
  - 角色解析不到科目 → 待审壳(review_reason=mapping_missing,提示去配,unpost 重判)。
  - confidence < 门槛 或 auto_post 未放行(安全带③·全局/规则粒度)→ pending_review + suggested。
  - 放行且 ≥ 门槛 → auto_posted + method=auto。
幂等:同 source 已有非 void 凭证直接返回(partial UNIQUE 兜底)。
安全带②:unpost = 原凭证置 void + 同 source 重判(吃最新映射/学习记忆)。
"""

from __future__ import annotations

import logging
from datetime import date
from decimal import Decimal
from typing import Optional

from core.pos_api import PosError
from services.accounting import coa_preset, review, rules, sources
from services.accounting import settings as acct_settings
from services.accounting import store as acct_store
from services.accounting import vouchers as jv

logger = logging.getLogger("mr-pilot")


def generate_for_source(
    cur,
    *,
    tenant_id: str,
    workspace_client_id: int,
    source_type: str,
    source_id,
    created_by=None,
    context: Optional[dict] = None,
) -> Optional[dict]:
    """业务事件 → 凭证。返回凭证(已存在则原样返回)或 None(该业务不记账)。"""
    existing = jv.find_active_by_source(
        cur,
        tenant_id=tenant_id,
        workspace_client_id=workspace_client_id,
        source_type=source_type,
        source_id=source_id,
    )
    if existing:
        return dict(existing)

    coa_preset.ensure_seeded(cur, tenant_id=tenant_id, workspace_client_id=workspace_client_id)
    ctx = sources.load(
        cur,
        tenant_id=tenant_id,
        workspace_client_id=workspace_client_id,
        source_type=source_type,
        source_id=source_id,
        context=context,
    )
    if ctx is None:
        return None
    learned = review.find_learned(
        cur,
        tenant_id=tenant_id,
        workspace_client_id=workspace_client_id,
        scope_keys=ctx.get("scope_keys") or [],
    )
    if learned:
        ctx["learned"] = learned

    result = rules.build(ctx)
    if result is None:
        return None

    mappings = acct_store.resolve_mappings(
        cur, tenant_id=tenant_id, workspace_client_id=workspace_client_id
    )
    resolved, missing_roles, extra_uncertainties = _resolve_entries(result["entries"], mappings)
    uncertainties = list(result["uncertainties"]) + extra_uncertainties
    confidence = rules.compute_confidence(ctx["source_tier"], uncertainties)

    settings = acct_settings.get_settings(
        cur, tenant_id=tenant_id, workspace_client_id=workspace_client_id
    )
    header = {
        "source_type": source_type,
        "source_id": source_id,
        "source_ref": ctx.get("ref"),
        "description": result["description"],
        "human_note": result["human_note"],
        "rule_key": result["rule_key"],
        "confidence": confidence,
        "source_tier": ctx["source_tier"],
        "voucher_date": ctx["voucher_date"],
        "created_by": created_by or "system",
    }

    if missing_roles:
        # 缺映射不落行(行科目 NOT NULL):待审壳 + 提示去配,配完 unpost 重判
        header.update(
            status="pending_review",
            method="suggested",
            review_reason=f"mapping_missing:{','.join(missing_roles)}",
            total_amount=sum(
                (Decimal(str(e["amount"])) for e in result["entries"] if e["dr_cr"] == "debit"),
                Decimal("0"),
            ),
        )
        return jv.insert_voucher(
            cur,
            tenant_id=tenant_id,
            workspace_client_id=workspace_client_id,
            header=header,
            lines=[],
        )

    status, method, reason = decide_status(settings, result["rule_key"], confidence, uncertainties)
    header.update(status=status, method=method, review_reason=reason)
    return jv.insert_voucher(
        cur,
        tenant_id=tenant_id,
        workspace_client_id=workspace_client_id,
        header=header,
        lines=resolved,
    )


def decide_status(settings: dict, rule_key: str, confidence, uncertainties: list):
    """安全带③分流(纯函数):auto_post 放行(全局或规则粒度)且 ≥ 门槛 → 自动过账;
    否则 pending_review + method=suggested(建议模式/低置信都走这,绝不静默乱过)。"""
    allowed = acct_settings.auto_post_allowed(settings, rule_key)
    threshold = Decimal(str(settings["auto_post_threshold"]))
    if allowed and Decimal(str(confidence)) >= threshold:
        return "auto_posted", "auto", None
    if uncertainties:
        reason = uncertainties[0]
    elif not allowed:
        reason = "suggest_mode"
    else:
        reason = "below_threshold"
    return "pending_review", "suggested", reason


def _resolve_entries(entries: list, mappings: dict):
    """角色 → 真科目。费用类别角色缺映射回落 expense_default(+扣分);核心角色缺=待审。"""
    resolved, missing, extra = [], [], []
    for e in entries:
        account_id = e.get("account_id")
        if account_id is None:
            role = e["role"]
            account_id = mappings.get(role)
            if account_id is None and role.startswith("expense:"):
                account_id = mappings.get("expense_default")
                if account_id is not None and "category_unmapped" not in extra:
                    extra.append("category_unmapped")
            if account_id is None:
                missing.append(role)
                continue
        resolved.append(
            {
                "account_id": account_id,
                "dr_cr": e["dr_cr"],
                "amount": Decimal(str(e["amount"])),
                "memo": e.get("memo"),
            }
        )
    return resolved, missing, extra


def unpost_voucher(
    cur, *, tenant_id: str, workspace_client_id: int, voucher_id, created_by=None
) -> Optional[dict]:
    """安全带②一键撤销重做:原凭证置 void → 同 source 重新跑引擎(吃最新映射/记忆)。

    返回重判后的新凭证;源单已不可记账(如被作废)→ None(只撤不重生)。
    """
    voucher = jv.get_voucher(
        cur, tenant_id=tenant_id, workspace_client_id=workspace_client_id, voucher_id=voucher_id
    )
    if voucher is None:
        raise PosError("acct.unexpected", 404, detail="voucher_not_found")
    if voucher["status"] == "void":
        raise PosError("acct.not_pending", 409, detail="already_void")
    _assert_period_open(cur, tenant_id, workspace_client_id, voucher["period"])

    jv.set_status(
        cur,
        tenant_id=tenant_id,
        workspace_client_id=workspace_client_id,
        voucher_id=voucher_id,
        status="void",
    )
    if not voucher["source_id"] or voucher["source_type"] == "manual":
        return None
    context = None
    if voucher["source_type"] == "payment":
        # 付款事件无独立业务行,从被撤凭证反推事件参数
        context = {
            "amount": voucher["total_debit"],
            "direction": "in" if voucher["rule_key"] == "R6" else "out",
            "ref": voucher["source_ref"],
            "voucher_date": voucher["voucher_date"],
        }
    return generate_for_source(
        cur,
        tenant_id=tenant_id,
        workspace_client_id=workspace_client_id,
        source_type=voucher["source_type"],
        source_id=voucher["source_id"],
        created_by=created_by,
        context=context,
    )


def void_voucher(cur, *, tenant_id: str, workspace_client_id: int, voucher_id) -> dict:
    voucher = jv.get_voucher(
        cur, tenant_id=tenant_id, workspace_client_id=workspace_client_id, voucher_id=voucher_id
    )
    if voucher is None:
        raise PosError("acct.unexpected", 404, detail="voucher_not_found")
    if voucher["status"] == "void":
        return voucher
    _assert_period_open(cur, tenant_id, workspace_client_id, voucher["period"])
    jv.set_status(
        cur,
        tenant_id=tenant_id,
        workspace_client_id=workspace_client_id,
        voucher_id=voucher_id,
        status="void",
    )
    return {**voucher, "status": "void"}


def reverse_voucher(
    cur, *, tenant_id: str, workspace_client_id: int, voucher_id, created_by=None
) -> dict:
    """红冲(docs/purchasing/04):已结/已申报期凭证不可改 → 在【当前开放期间】插一张反向凭证
    (借贷对调)冲销,原凭证留原期不动(合规:不篡改已报历史)。

    当前期也已结(无开放期可落)→ acct.no_open_period(409·诚实拦)。反向凭证 source_type 加
    `_reversal` 后缀(避 uq_jv_source 撞仍 posted 的原单);原凭证无行(待审壳)→ 原样返回不冲。
    """
    voucher = jv.get_voucher(
        cur, tenant_id=tenant_id, workspace_client_id=workspace_client_id, voucher_id=voucher_id
    )
    if voucher is None:
        raise PosError("acct.unexpected", 404, detail="voucher_not_found")
    if voucher["status"] == "void":
        return voucher
    lines = voucher.get("lines") or []
    if not lines:
        return voucher

    today = date.today()
    period = today.strftime("%Y-%m")
    settings = acct_settings.get_settings(
        cur, tenant_id=tenant_id, workspace_client_id=workspace_client_id
    )
    if acct_settings.is_period_closed(settings, period):
        raise PosError("acct.no_open_period", 409, detail="current_period_closed")

    reversed_lines = [
        {
            "account_id": ln["account_id"],
            "dr_cr": "credit" if ln["dr_cr"] == "debit" else "debit",
            "amount": ln["amount"],
            "memo": ln.get("memo"),
        }
        for ln in lines
    ]
    ref = voucher.get("source_ref") or voucher.get("voucher_no")
    header = {
        "source_type": f"{voucher['source_type']}_reversal",
        "source_id": voucher.get("source_id"),
        "source_ref": voucher.get("source_ref"),
        "description": f"红冲 {ref}",
        "human_note": f"红冲 {ref}:原单在已结/已申报期,按原票反向冲销,落当期。",
        "rule_key": "reversal",
        "confidence": 1,
        "source_tier": "manual",
        "voucher_date": today,
        "status": "auto_posted",
        "method": "auto",
        "review_reason": None,
        "created_by": created_by or "system",
    }
    return jv.insert_voucher(
        cur,
        tenant_id=tenant_id,
        workspace_client_id=workspace_client_id,
        header=header,
        lines=reversed_lines,
    )


def create_manual_voucher(
    cur,
    *,
    tenant_id: str,
    workspace_client_id: int,
    voucher_date,
    description,
    lines: list,
    created_by=None,
    draft: bool = False,
) -> dict:
    """手工凭证:借贷自填,断言平。draft=True → 存草稿(pending_review,进待审列表,可逐笔审过账);
    否则直接 posted(人录的 = method manual)。已结期间日期拦截(acct.period_closed)。"""
    _assert_period_open(cur, tenant_id, workspace_client_id, voucher_date.strftime("%Y-%m"))
    coa_preset.ensure_seeded(cur, tenant_id=tenant_id, workspace_client_id=workspace_client_id)
    for ln in lines:
        acct = acct_store.get_account(
            cur,
            tenant_id=tenant_id,
            workspace_client_id=workspace_client_id,
            account_id=ln.get("account_id"),
        )
        if acct is None:
            raise PosError("acct.mapping_missing", 422, detail="account_not_found")
    header = {
        "source_type": "manual",
        "source_id": None,
        "description": description,
        "human_note": description,
        "rule_key": "manual",
        "confidence": 100,
        "source_tier": "manual",
        "method": "manual",
        "status": "pending_review" if draft else "posted",
        "review_reason": "manual_draft" if draft else None,
        "voucher_date": voucher_date,
        "created_by": created_by or "manual",
    }
    return jv.insert_voucher(
        cur,
        tenant_id=tenant_id,
        workspace_client_id=workspace_client_id,
        header=header,
        lines=lines,
    )


def _assert_period_open(cur, tenant_id: str, workspace_client_id: int, period: str) -> None:
    settings = acct_settings.get_settings(
        cur, tenant_id=tenant_id, workspace_client_id=workspace_client_id
    )
    if acct_settings.is_period_closed(settings, period):
        raise PosError("acct.period_closed", 409)
