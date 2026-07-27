# -*- coding: utf-8 -*-
"""管家月结产线四问(B4 第二步 · 只读薄封装,零新 SQL、零直接写库)。

会计每天在工作台上问的就这四句,以前只能自己点页面翻:
  due_soon           「这期还有哪些没交、几号截止」 services.workorder.matrix.fetch_rows
                     + obligation_engine.defer_optional(= 矩阵页 / 义务清单端点同一份原料)
  review_queue       「有什么等我审的」             services.workorder.review.review_queue
                     (= /api/workorder/review-queue)
  tax_numbers        「这家这期该交多少」           services.workorder.api.order_detail['numbers']
  bank_recon_status  「银行对账差多少没对上」       services.workorder.api.order_detail['bank_recon']

数字一律取自既有投影,本模块不算账也不重排口径 —— 对话里说的数与人手点开工单看到的必须
逐位相同。钱走 tool_scope.money(decimal 两位字符串,不过 float)。

作用域、客户名接地、工单详情取法(client_order)共用 tool_scope:allowed_client_ids 是请求侧算好的账套快照,被分派成员
在对话里也只看得见分到的账套(worker 没有请求可算,绝不在这里放宽)。
"""

from __future__ import annotations

from datetime import date
from typing import Any, Optional

from services.agent.contracts import ToolResult
from services.steward import tool_scope
from services.steward.registry import ToolContext

# 逾期/临近的分界:泰国月度税表(ภ.พ.30 次月 15 日、ภ.ง.ด. 次月 7 日)从截止前一周开始催
# 才来得及补料,再早会天天满屏"快到期"而失去信号意义。
DUE_SOON_DAYS = 7

_SEVERITIES = ("crit", "warn")

# order_detail['numbers'] 里的钱字段(compute 步落的 R1/R2 认列结果)。全所税额表答的是同一批
# 数字,字段集因此住在 tool_scope 一份。period 也在同一个投影里但不是钱,单独取。
_MONEY_KEYS = tool_scope.TAX_MONEY_KEYS

_RECON_LISTS = ("auto_matched", "review", "missing_invoice", "unmatched_invoice")


def _iso(value: Any) -> Optional[str]:
    return value.isoformat() if hasattr(value, "isoformat") else (value or None)


def _days_left(due: Optional[date], today: date) -> Optional[int]:
    return (due - today).days if isinstance(due, date) else None


def due_soon(ctx: ToolContext, args: dict) -> ToolResult:
    """本期还没交完的义务 + 截止日(近→远)。

    口径三条,与矩阵页同源:①从未物化过义务的客户格子不算「欠交」(状态未知不冒充已知);
    ②status=nil 的义务本来就不用交;③工单已冻结(archive)= 这期已交付,不再催。
    截止日经 defer_optional 现算法定顺延(遇周末/泰国政府假日逐日推),裸日期不直接示人 ——
    会计照裸日期赶工会白加一天班。
    """
    from services.workorder import matrix, obligation_engine

    period = tool_scope.period_or_current(args.get("period"))
    with tool_scope.cursor() as cur:
        rows = matrix.fetch_rows(cur, tenant_id=ctx.tenant_id, period=period)

    pending = []
    for r in rows:
        if not tool_scope.in_scope(ctx, r["client_id"]):
            continue
        status = r.get("obligation_status")
        if status is None or status == obligation_engine.STATUS_NIL:
            continue
        badge = matrix.badge(status, r.get("order_status"))
        if badge == matrix.BADGE_FROZEN:
            continue
        # 纸质截止日是保守基准(e-Filing 只会更晚),拿它排序与倒计时;两个日期都如实带出去。
        paper = obligation_engine.defer_optional(r.get("due_paper"))
        efiling = obligation_engine.defer_optional(r.get("due_efiling"))
        anchor = paper or efiling
        pending.append(
            {
                "client_id": int(r["client_id"]),
                "client_name": r.get("client_name") or "",
                "obligation_code": r.get("obligation_code") or "",
                "badge": badge,
                "due": _iso(anchor),
                "due_efiling": _iso(efiling),
                "days_left": _days_left(anchor, ctx.today),
                "_sort": anchor or date.max,
            }
        )
    pending.sort(key=lambda x: (x["_sort"], x["client_name"]))
    for row in pending:
        row.pop("_sort")
    counted = [r["days_left"] for r in pending if r["days_left"] is not None]
    return ToolResult(
        ok=True,
        data={
            "period": period,
            "today": ctx.today.isoformat(),
            "window_days": DUE_SOON_DAYS,
            "total": len(pending),
            "overdue": sum(1 for d in counted if d < 0),
            "due_soon": sum(1 for d in counted if 0 <= d <= DUE_SOON_DAYS),
            "no_due_date": len(pending) - len(counted),
            "rows": pending[: tool_scope.LIST_LIMIT],
        },
    )


def review_queue(ctx: ToolContext, args: dict) -> ToolResult:
    """待审队列(工单 × flagged 分组)。与 /api/workorder/review-queue 同一个读模型。

    severity 只认 crit/warn —— 认不出的词一律当没筛(不拿编造的严重度去查库),并在返回里
    如实标 severity=None,答复因此说得出"没筛"还是"只看严重的"。
    """
    from core.feature_flags import pearnly_ai_sod_enabled_for
    from services.workorder import review

    client_name = (args.get("client_name") or "").strip()
    client = None
    if client_name:
        client, err = tool_scope.resolve_client(ctx, client_name)
        if err:
            return err
    severity = args.get("severity") if args.get("severity") in _SEVERITIES else None
    period = args.get("period") or None  # 队列跨期有意义(上期没审完的还在里面),不默认当期
    with tool_scope.cursor() as cur:
        queue = review.review_queue(
            cur,
            tenant_id=ctx.tenant_id,
            period=period,
            client_id=client["id"] if client else None,
            severity=severity,
            actor=f"user:{ctx.user_id}",
            sod_enforced=pearnly_ai_sod_enabled_for(ctx.tenant_id),
        )
    orders = [
        o
        for c in queue.get("clients") or []
        for o in c.get("orders") or []
        if tool_scope.in_scope(ctx, c["workspace_client_id"])
    ]
    return ToolResult(
        ok=True,
        data={
            "period": period,
            "severity": severity,
            "client_name": client["name"] if client else "",
            "client_count": len({o["workspace_client_id"] for o in orders}),
            "order_count": len(orders),
            "flagged_count": sum(o.get("flagged_total") or 0 for o in orders),
            "rows": [
                {
                    "client_name": o.get("client_name") or "",
                    "period": o.get("period") or "",
                    "status": o.get("status") or "",
                    "flagged": o.get("flagged_total") or 0,
                    "severity": o.get("top_severity") or "",
                    "due": o.get("next_due_efiling") or o.get("next_due_paper") or "",
                }
                for o in orders[: tool_scope.LIST_LIMIT]
            ],
        },
    )


def tax_numbers(ctx: ToolContext, args: dict) -> ToolResult:
    """某家某期的销项/进项/应交税额(order_detail['numbers'] = compute 步认列结果)。

    引擎还没跑到 compute 就没有 numbers —— 此时诚实报 has_numbers=False,绝不用 0 充数:
    「应交 0 บาท」和「还没算出来」在会计眼里是两件完全不同的事。
    """
    client, period, detail, err = tool_scope.client_order(ctx, args)
    if err:
        return err
    numbers = (detail or {}).get("numbers") or {}
    data = {
        "client_id": client["id"],
        "client_name": client["name"],
        "period": period,
        "has_order": bool(detail),
        "has_numbers": bool(numbers),
        "status": (detail or {}).get("status") or "",
        "current_step": (detail or {}).get("current_step") or "",
    }
    data.update(
        {k: tool_scope.money(numbers[k]) for k in _MONEY_KEYS if numbers.get(k) is not None}
    )
    return ToolResult(ok=True, data=data)


def bank_recon_status(ctx: ToolContext, args: dict) -> ToolResult:
    """某家某期的银行对账进度(order_detail['bank_recon'] = R3 四清单投影)。

    四清单:自动匹配 / 待人审 / 缺票(有流水无票)/ 未达(有票无流水),外加两张清单的
    金额合计与净差。闸关、没收到银行流水、还没跑到 reconcile 一律 has_recon=False —— 投影
    本身在这些情形给 None,这里照实转述,不拼一份"全 0 已对平"的假象。
    """
    client, period, detail, err = tool_scope.client_order(ctx, args)
    if err:
        return err
    recon = (detail or {}).get("bank_recon") or None
    data = {
        "client_id": client["id"],
        "client_name": client["name"],
        "period": period,
        "has_order": bool(detail),
        "has_recon": bool(recon),
        "status": (detail or {}).get("status") or "",
    }
    if recon:
        diff = recon.get("diff") or {}
        data.update({k: tool_scope.recon_count(recon, k) for k in _RECON_LISTS})
        data.update(
            {
                "missing_invoice_total": tool_scope.money(diff.get("missing_invoice_total")),
                "unmatched_invoice_total": tool_scope.money(diff.get("unmatched_invoice_total")),
                "net": tool_scope.money(diff.get("net")),
                # 只列缺票清单:这是唯一需要人去要票的一张,另外三张要么已对上、要么在
                # 对账界面里逐笔裁(对话里摆出来也没法处理)。行形状 = 流水视图原样。
                "rows": [
                    {
                        "tx_date": tx.get("tx_date") or "",
                        "amount": tx.get("amount") or "",
                        "description": tx.get("description") or "",
                    }
                    for tx in (recon.get("missing_invoice") or [])[: tool_scope.LIST_LIMIT]
                ],
            }
        )
    return ToolResult(ok=True, data=data)
