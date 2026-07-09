# -*- coding: utf-8 -*-
"""compute 步:算应缴税额(任务包 §5 步 5)。

纯编排:取 reconcile 的结果(同进程从 ctx.data,续跑场景从事件流回放 reconcile 的
step_done——照 reconcile.py 自身"事件流是断点续跑恢复源"的范式)→ 应缴 = 销项税 −
进项税(Decimal,负数即留抵,如实表达不 clamp)→ 与上期同口径数字比一眼(M0 只记录
不拦,没有上期就诚实记 no_prior_period)。本步不重算票面/汇总的任何金额,只做一次
减法——重算是 classify/reconcile 上游的事。
"""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Optional

from services.workorder import evidence
from services.workorder.engine import StepContext, StepResult

_STEP_RECONCILE = "reconcile"
_DELIVERABLE_PP30 = "pp30_draft"
_DEFAULT_INTENT = "monthly_vat"

# reconcile step_done payload 里必须齐的四个数字(§5 步 4 契约),缺一即不可算税。
_RECONCILE_KEYS = (
    "input_vat_total",
    "purchase_amount_total",
    "sales_amount_total",
    "output_vat_total",
)


def run(ctx: StepContext) -> StepResult:
    reconcile_numbers = _reconcile_numbers(ctx)
    missing = [k for k in _RECONCILE_KEYS if not reconcile_numbers.get(k)]
    if missing:
        return StepResult.needs([f"reconcile:{k}" for k in missing])

    output_vat = Decimal(reconcile_numbers["output_vat_total"])
    input_vat = Decimal(reconcile_numbers["input_vat_total"])
    tax_due = output_vat - input_vat  # 负数=留抵,诚实表达

    work_order = ctx.store.get_work_order(
        ctx.cur, tenant_id=ctx.tenant_id, work_order_id=ctx.work_order_id
    )
    period = (work_order or {}).get("period")

    return StepResult.ok(
        tax_due=str(tax_due),
        sales_amount=reconcile_numbers["sales_amount_total"],
        output_vat=reconcile_numbers["output_vat_total"],
        purchase_amount=reconcile_numbers["purchase_amount_total"],
        input_vat=reconcile_numbers["input_vat_total"],
        period=period,
        prior_period_check=_prior_period_check(ctx, work_order, tax_due),
    )


def _reconcile_numbers(ctx: StepContext) -> dict:
    """取 reconcile 的四个金额。同进程直接读 ctx.data;续跑 ctx.data 为空时从事件流回放
    reconcile 最后一条 step_done——两条路径最终读到的都是 reconcile 落库时的原值。"""
    if all(ctx.data.get(k) for k in _RECONCILE_KEYS):
        return {k: ctx.data[k] for k in _RECONCILE_KEYS}
    events = ctx.store.list_events(
        ctx.cur, tenant_id=ctx.tenant_id, work_order_id=ctx.work_order_id
    )
    payload = evidence.replay_step_done(events, _STEP_RECONCILE) or {}
    return {k: payload.get(k) for k in _RECONCILE_KEYS}


def _shift_period(period: str) -> Optional[str]:
    """期间格式「佛历年-月」(如 2569-05)取上一期;1 月的上一期是去年 12 月。"""
    try:
        year_s, month_s = period.split("-")
        year, month = int(year_s), int(month_s)
    except (ValueError, AttributeError):
        return None
    if month == 1:
        year, month = year - 1, 12
    else:
        month -= 1
    return f"{year:04d}-{month:02d}"


def _prior_period_check(ctx: StepContext, work_order: Optional[dict], tax_due: Decimal) -> dict:
    """与上期同口径数字比一眼。M0 只记录不拦——没查到上期就诚实记 no_prior_period,
    不推断、不报错。"""
    period = (work_order or {}).get("period")
    prior_period = _shift_period(period) if period else None
    if not prior_period:
        return {"status": "no_prior_period"}

    prior_id = _resolve_prior_work_order_id(
        ctx,
        workspace_client_id=(work_order or {}).get("workspace_client_id"),
        period=prior_period,
        intent=(work_order or {}).get("intent") or _DEFAULT_INTENT,
    )
    if not prior_id:
        return {"status": "no_prior_period"}

    prior_numbers = _prior_pp30_numbers(ctx, prior_id)
    prior_tax_due = _to_decimal(prior_numbers.get("tax_due")) if prior_numbers else None
    if prior_tax_due is None:
        return {"status": "no_prior_period"}

    return {
        "status": "compared",
        "prior_period": prior_period,
        "prior_tax_due": str(prior_tax_due),
        "delta": str(tax_due - prior_tax_due),
    }


def _prior_pp30_numbers(ctx: StepContext, prior_work_order_id: str) -> Optional[dict]:
    deliverables = ctx.store.list_deliverables(
        ctx.cur, tenant_id=ctx.tenant_id, work_order_id=prior_work_order_id
    )
    prior_pp30 = next((d for d in deliverables if d.get("kind") == _DELIVERABLE_PP30), None)
    return (prior_pp30 or {}).get("numbers")


def _to_decimal(v) -> Optional[Decimal]:
    if v is None:
        return None
    try:
        return Decimal(str(v))
    except InvalidOperation:
        return None


def _default_resolve_prior_work_order_id(
    ctx: StepContext, *, workspace_client_id, period: str, intent: str
) -> Optional[str]:
    """真实现:只读查上期工单 id。store.py 没有「按 period 查找」的口子(它只给
    open_work_order 这种幂等开单——拿来当查询会在无上期时意外新建一张空单),
    这里用事务游标发一条参数化只读 SELECT,不新增/不绕过 store 的写路径。"""
    if not workspace_client_id:
        return None
    ctx.cur.execute(
        "SELECT id FROM work_orders WHERE tenant_id = %s AND workspace_client_id = %s "
        "AND period = %s AND intent = %s",
        (ctx.tenant_id, workspace_client_id, period, intent),
    )
    row = ctx.cur.fetchone()
    if not row:
        return None
    return row["id"] if isinstance(row, dict) else row[0]


# 注入点:模块级绑定,测试用 compute._resolve_prior_work_order_id = fake 替换。
_resolve_prior_work_order_id = _default_resolve_prior_work_order_id
